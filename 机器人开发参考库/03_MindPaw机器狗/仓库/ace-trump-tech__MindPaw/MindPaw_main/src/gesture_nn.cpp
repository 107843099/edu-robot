//----------------------------------------------
// 轻量手势识别实现
// int8 量化 MLP 推理引擎 + 特征提取
//----------------------------------------------
#include "gesture_nn.h"
#include <string.h>

// ==================== 模型权重 (占位) ====================
// 重要: 使用前请运行 tools/distill_gesture.py 生成真实权重
// 当前权重为初始化占位值，能保证分类流程但准确率未经训练

// Layer 1: 38×16 (608 int8)
const int8_t GestureNN::_w1[FEATURE_DIM * HIDDEN1_DIM] = {
    // 为简化演示，设置为小随机值模式
    // 完整训练请运行蒸馏管线
    12, -8,  3,  15, -5,  7,  -12, 9,   5,  -3,  11, -7,  4,  -14, 6,   -2,
    8,  -11, 2,  13,  -6,  10, -15, 1,   14, -4,  9,  -8,  3,   12, -13, 7,
    -5, 16, -10, 4,  -2,  8,  -12, 6,   11, -3,  15, -7,  1,  -14, 5,   -9,
    // ... 重复模式填充剩余 560 个元素
    // 实际使用时应由蒸馏脚本生成
};
// Bias 1: 16 int8
const int8_t GestureNN::_b1[HIDDEN1_DIM] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

// Layer 2: 16×8 (128 int8)
const int8_t GestureNN::_w2[HIDDEN1_DIM * HIDDEN2_DIM] = {
    5, -3,  8,  -6,  2,  -9,  4,  -1,
    7, -4,  1,  -8,  6,  -2,  9,  -5,
    // ... 重复
};

// Bias 2: 8 int8
const int8_t GestureNN::_b2[HIDDEN2_DIM] = {0, 0, 0, 0, 0, 0, 0, 0};

// Layer 3: 8×5 (40 int8)
const int8_t GestureNN::_w3[HIDDEN2_DIM * OUTPUT_DIM] = {
    3, -1,  5,  -2,  4,  -3,  2,  -4,
    1, -5,  6,  -1,  3,  -2,  5,  -4,
    2, -3,  4,  -5,  1,  -6,  3,  -2,
    5, -1,  4,  -3,  2,  -5,  1,  -4,
    3, -2,  6,  -1,  5,  -3,  4,  -2,
};

// Bias 3: 5 int8
const int8_t GestureNN::_b3[OUTPUT_DIM] = {0, 0, 0, 0, 0};

// ==================== 构造函数 ====================
GestureNN::GestureNN() {
    _debug = false;
}

// ==================== int8 全连接层 + ReLU ====================
void GestureNN::_fcRelu(const int8_t* input, const int8_t* weight, const int8_t* bias,
                         uint8_t inputDim, uint8_t outputDim, int8_t* output) {
    for (uint8_t o = 0; o < outputDim; o++) {
        int32_t sum = 0;
        for (uint8_t i = 0; i < inputDim; i++) {
            sum += (int32_t)input[i] * (int32_t)weight[o * inputDim + i];
        }
        sum += (int32_t)bias[o];
        // 缩放 (8 位量化: 除以 64)
        sum >>= 6;
        // ReLU: max(0, x)
        if (sum < 0) sum = 0;
        if (sum > 127) sum = 127;
        output[o] = (int8_t)sum;
    }
}

// ==================== int8 全连接层 (无激活) ====================
void GestureNN::_fc(const int8_t* input, const int8_t* weight, const int8_t* bias,
                    uint8_t inputDim, uint8_t outputDim, int8_t* output) {
    for (uint8_t o = 0; o < outputDim; o++) {
        int32_t sum = 0;
        for (uint8_t i = 0; i < inputDim; i++) {
            sum += (int32_t)input[i] * (int32_t)weight[o * inputDim + i];
        }
        sum += (int32_t)bias[o];
        sum >>= 6;  // 量化缩放
        if (sum < -128) sum = -128;
        if (sum > 127) sum = 127;
        output[o] = (int8_t)sum;
    }
}

// ==================== 32-bin 强度直方图 ====================
void GestureNN::_computeHistogram(const uint8_t* grayBuffer, uint8_t* histOut) {
    // 清零
    memset(histOut, 0, 32);

    // 遍历 40×30 = 1200 个像素
    for (int i = 0; i < 1200; i++) {
        uint8_t val = grayBuffer[i];
        uint8_t bin = val >> 3;  // 256/32 = 8, val/8 = bin
        if (bin >= 32) bin = 31;
        if (histOut[bin] < 255) histOut[bin]++;  // 防溢出
    }

    if (_debug) {
        Serial.print("GESTURE_NN: Histogram bins: ");
        for (int b = 0; b < 32; b++) {
            Serial.print(histOut[b]);
            if (b < 31) Serial.print(",");
        }
        Serial.println();
    }
}

// ==================== 6-bin 空间分布 ====================
void GestureNN::_computeSpatial(const uint8_t* grayBuffer, uint8_t* spatialOut) {
    // 将 40×30 图像分为 3×2 网格 (行: 0-13, 14-27, 28-39; 列: 0-19, 20-39)
    const int gridRows = 3, gridCols = 2;
    int rowStep = 40 / gridRows;   // ~13
    int colStep = 30 / gridCols;   // 15

    memset(spatialOut, 0, gridRows * gridCols);

    for (int gr = 0; gr < gridRows; gr++) {
        for (int gc = 0; gc < gridCols; gc++) {
            uint32_t sum = 0;
            uint32_t count = 0;
            for (int r = gr * rowStep; r < (gr+1) * rowStep && r < 40; r++) {
                for (int c = gc * colStep; c < (gc+1) * colStep && c < 30; c++) {
                    sum += grayBuffer[r * 30 + c];  // 每行30列
                    count++;
                }
            }
            if (count > 0) {
                spatialOut[gr * gridCols + gc] = (uint8_t)(sum / count);
            }
        }
    }

    if (_debug) {
        Serial.printf("GESTURE_NN: Spatial [%d,%d,%d,%d,%d,%d]\n",
                     spatialOut[0], spatialOut[1], spatialOut[2],
                     spatialOut[3], spatialOut[4], spatialOut[5]);
    }
}

// ==================== 特征提取 ====================
void GestureNN::extractFeatures(const uint8_t* grayBuffer, uint8_t* featuresOut) {
    _computeHistogram(grayBuffer, featuresOut);       // 前 32 维
    _computeSpatial(grayBuffer, featuresOut + 32);    // 后 6 维
}

// ==================== 推理 (完整帧) ====================
GestureNNResult GestureNN::classify(const uint8_t* grayBuffer) {
    GestureNNResult result;
    result.gesture = GESTURE_NONE;
    result.confidence = 0.0f;

    // 1. 提取特征
    extractFeatures(grayBuffer, result.feature);

    // 2. 特征中心化 (uint8 → int8, 减去128)
    int8_t centered[FEATURE_DIM];
    for (uint8_t i = 0; i < FEATURE_DIM; i++) {
        centered[i] = (int8_t)((int)result.feature[i] - 128);
    }

    // 3. MLP 前向传播
    int8_t h1[HIDDEN1_DIM];
    int8_t h2[HIDDEN2_DIM];
    int8_t output[OUTPUT_DIM];

    _fcRelu(centered, _w1, _b1, FEATURE_DIM, HIDDEN1_DIM, h1);
    _fcRelu(h1, _w2, _b2, HIDDEN1_DIM, HIDDEN2_DIM, h2);
    _fc(h2, _w3, _b3, HIDDEN2_DIM, OUTPUT_DIM, output);

    // 4. ArgMax 找到最大值索引
    int8_t maxVal = output[0];
    uint8_t maxIdx = 0;
    for (uint8_t i = 1; i < OUTPUT_DIM; i++) {
        if (output[i] > maxVal) {
            maxVal = output[i];
            maxIdx = i;
        }
    }

    // 计算置信度 (softmax 近似: 最大值 / 总和)
    int32_t sumExp = 0;
    for (uint8_t i = 0; i < OUTPUT_DIM; i++) {
        // 简单偏移使值非负
        int32_t shifted = (int32_t)output[i] + 128;
        if (shifted < 0) shifted = 0;
        sumExp += shifted;
    }
    int32_t maxExp = (int32_t)maxVal + 128;
    if (maxExp < 0) maxExp = 0;

    result.confidence = (sumExp > 0) ? ((float)maxExp / (float)sumExp) : 0.0f;

    // 只有当置信度 > 阈值时才输出有效分类
    if (result.confidence > 0.25f) {
        result.gesture = (GestureClass)maxIdx;
    } else {
        result.gesture = GESTURE_NONE;
    }

    if (_debug) {
        Serial.printf("GESTURE_NN: Class=%d conf=%.2f outputs=[%d,%d,%d,%d,%d]\n",
                     result.gesture, result.confidence,
                     output[0], output[1], output[2], output[3], output[4]);
    }

    return result;
}

// ==================== 流式推理 (通过回调逐行读取) ====================
GestureNNResult GestureNN::classifyStream(int imageWidth, int imageHeight,
                                           RowReader rowReader) {
    if (!rowReader) {
        GestureNNResult empty = {GESTURE_NONE, 0.0f, {0}};
        return empty;
    }

    // 下采样到 40×30
    const int targetW = 40;
    const int targetH = 30;
    uint8_t grayBuffer[1200];  // 40×30

    int stepX = imageWidth / targetW;
    int stepY = imageHeight / targetH;
    if (stepX < 1) stepX = 1;
    if (stepY < 1) stepY = 1;

    // 逐行读取并下采样
    uint8_t rowBuf[imageWidth < 320 ? 320 : imageWidth];
    for (int ty = 0; ty < targetH; ty++) {
        int sy = ty * stepY;
        if (sy >= imageHeight) sy = imageHeight - 1;
        rowReader(sy, rowBuf, imageWidth);

        for (int tx = 0; tx < targetW; tx++) {
            int sx = tx * stepX;
            if (sx >= imageWidth) sx = imageWidth - 1;
            grayBuffer[ty * targetW + tx] = rowBuf[sx];
        }
    }

    return classify(grayBuffer);
}

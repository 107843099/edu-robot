//----------------------------------------------
// 轻量手势识别 — 知识蒸馏 MLP 推理引擎
//
// 端侧特征: 38维 (32-bin 强度直方图 + 6-bin 空间分布)
// 模型: int8 量化 MLP: 38 → 16 (ReLU) → 8 (ReLU) → 5 (ArgMax)
// 权重: ~1.1KB, 从开源模型蒸馏 + 量化得到
//
// 训练管线 (PC 端, tools/distill_gesture.py):
//   开源手势数据 → Teacher(RF/MLP) → Student MLP → int8 → C header
//----------------------------------------------
#ifndef GESTURE_NN_H
#define GESTURE_NN_H

#include <Arduino.h>

// ==================== 手势分类 ====================
enum GestureClass : uint8_t {
    GESTURE_NONE  = 0,  // 无手势
    GESTURE_WAVE  = 1,  // 挥手
    GESTURE_PALM  = 2,  // 伸掌/停止
    GESTURE_FIST  = 3,  // 握拳
    GESTURE_POINT = 4,  // 指点
};

// ==================== 特征维度 ====================
#define FEATURE_DIM  38   // 32 (直方图) + 6 (空间分布)
#define HIDDEN1_DIM  16
#define HIDDEN2_DIM  8
#define OUTPUT_DIM   5

// ==================== 推理结果 ====================
struct GestureNNResult {
    GestureClass gesture;   // 分类结果
    float confidence;       // 置信度 [0, 1]
    uint8_t feature[FEATURE_DIM]; // 特征向量 (调试用)
};

// ==================== 手势推理引擎 ====================
class GestureNN {
public:
    GestureNN();

    // 从 40×30 灰度图缓冲区进行推理
    // grayBuffer: 40行 × 30列的灰度值 [0,255]
    GestureNNResult classify(const uint8_t* grayBuffer);

    // 从逐行扫描模式推理 (流式特征提取，无需完整帧)
    // imageWidth, imageHeight: 完整图像尺寸
    // rowCallback: 用户提供获取指定行灰度数据的函数
    typedef void (*RowReader)(int y, uint8_t* rowOut, int width);
    GestureNNResult classifyStream(int imageWidth, int imageHeight, RowReader rowReader);

    // 获取特征提取结果 (不分类)
    void extractFeatures(const uint8_t* grayBuffer, uint8_t* featuresOut);

    // 模型是否已加载权重 (始终返回 true，权重编译在代码中)
    bool isLoaded() const { return true; }

    // 设置调试
    void setDebug(bool debug) { _debug = debug; }

private:
    bool _debug;

    // ---------- 量化模型权重 (int8) ----------
    // 通过 tools/distill_gesture.py 蒸馏+量化生成
    // 占位权重 — 使用前请运行蒸馏管线生成真实权重
    static const int8_t _w1[FEATURE_DIM * HIDDEN1_DIM];
    static const int8_t _b1[HIDDEN1_DIM];
    static const int8_t _w2[HIDDEN1_DIM * HIDDEN2_DIM];
    static const int8_t _b2[HIDDEN2_DIM];
    static const int8_t _w3[HIDDEN2_DIM * OUTPUT_DIM];
    static const int8_t _b3[OUTPUT_DIM];

    // ---------- 内部方法 ----------
    // 计算 32-bin 强度直方图
    void _computeHistogram(const uint8_t* grayBuffer, uint8_t* histOut);

    // 计算 6-bin 空间分布 (3×2 网格平均亮度)
    void _computeSpatial(const uint8_t* grayBuffer, uint8_t* spatialOut);

    // int8 全连接层: output = weight·input + bias, 再 ReLU
    static void _fcRelu(const int8_t* input, const int8_t* weight, const int8_t* bias,
                        uint8_t inputDim, uint8_t outputDim, int8_t* output);

    // int8 全连接层: output = weight·input + bias (无激活)
    static void _fc(const int8_t* input, const int8_t* weight, const int8_t* bias,
                    uint8_t inputDim, uint8_t outputDim, int8_t* output);
};

#endif // GESTURE_NN_H

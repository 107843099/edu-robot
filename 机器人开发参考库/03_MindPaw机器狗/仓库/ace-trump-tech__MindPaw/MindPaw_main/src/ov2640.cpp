//----------------------------------------------
// OV2640 摄像头模块实现
// 使用 ArduCAM Mini 捕获 BMP 帧并提取灰度缓冲
//----------------------------------------------
#include "ov2640.h"

// ==================== 构造函数 ====================
OV2640_Camera::OV2640_Camera(uint8_t csPin) : _cs(csPin) {
    _cam = nullptr;
    _available = false;
    _debug = false;
    _lastCaptureMs = 0;
    _intervalMs = 500;
}

// ==================== 初始化摄像头 ====================
bool OV2640_Camera::initCamera() {
    uint8_t vid, pid;
    _cam->wrSensorReg8_8(0xFF, 0x01);
    delay(10);
    _cam->rdSensorReg8_8(0x0A, &vid);
    _cam->rdSensorReg8_8(0x0B, &pid);

    if (_debug) {
        Serial.printf("OV2640: VID=0x%02X PID=0x%02X\n", vid, pid);
    }

    // 初始化为 JPEG 模式 (后续 captureGrayscale 切换到 BMP)
    _cam->set_format(JPEG);
    _cam->InitCAM();
    delay(100);

    // 设置 QQVGA 分辨率
    _cam->OV2640_set_JPEG_size(OV2640_160x120);
    delay(50);

    // 关闭特殊效果
    _cam->OV2640_set_Special_effects(Normal);
    delay(50);

    if (_debug) Serial.println("OV2640: Camera initialized");
    return true;
}

bool OV2640_Camera::begin() {
    if (_debug) Serial.println("OV2640: Initializing...");

    pinMode(_cs, OUTPUT);
    digitalWrite(_cs, HIGH);
    delay(10);

    _cam = new ArduCAM(OV2640, _cs);
    if (!_cam) {
        if (_debug) Serial.println("OV2640: Failed to create ArduCAM instance");
        return false;
    }

    // 检查 SPI 通信
    _cam->write_reg(0x07, 0x80);
    delay(10);
    _cam->write_reg(0x07, 0x00);
    delay(10);

    if (!initCamera()) {
        if (_debug) Serial.println("OV2640: Camera init failed");
        delete _cam;
        _cam = nullptr;
        return false;
    }

    _available = true;
    if (_debug) Serial.println("OV2640: Ready");
    return true;
}

// ==================== 捕获原始帧 ====================
bool OV2640_Camera::captureRawFrame() {
    if (!_available || !_cam) return false;

    _cam->flush_fifo();
    _cam->clear_fifo_flag();
    _cam->start_capture();

    unsigned long timeout = millis() + 3000;
    while (!_cam->get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK)) {
        if (millis() > timeout) {
            if (_debug) Serial.println("OV2640: Capture timeout");
            return false;
        }
        delay(2);
    }

    return true;
}

// ==================== 读取 FIFO 字 (2 字节) ====================
uint16_t OV2640_Camera::readFifoWord() {
    uint8_t high = _cam->read_fifo();
    uint8_t low  = _cam->read_fifo();
    return ((uint16_t)high << 8) | low;
}

// ==================== RGB565 采样到灰度缓冲 ====================
void OV2640_Camera::sampleToGrayscale(uint8_t* buffer, int srcW, int srcH,
                                        int dstW, int dstH) {
    int stepX = srcW / dstW;  // e.g., 160/40 = 4
    int stepY = srcH / dstH;  // 120/30 = 4
    int bytesPerRow = srcW * 2;  // RGB565: 2 bytes/pixel

    // Burst 模式读取 FIFO
    _cam->CS_LOW();
    _cam->set_fifo_burst();

    for (int dy = 0; dy < dstH; dy++) {
        int srcY = dy * stepY;
        // 跳过未采样行的全部像素
        for (int skipRow = 0; skipRow < stepY; skipRow++) {
            for (int dx = 0; dx < dstW; dx++) {
                if (skipRow == 0) {
                    // 需要采样此行
                    int srcX = dx * stepX * 2;  // ×2 for RGB565 bytes
                    // 跳过未采样列
                    for (int skipCol = 0; skipCol < stepX; skipCol++) {
                        uint16_t pixel = readFifoWord();  // 读取 RGB565
                        if (skipCol == 0 && skipRow == 0) {
                            // 转换到灰度: Y = (R*77 + G*150 + B*29) >> 8
                            uint8_t r = (pixel >> 11) & 0x1F;  // 5 bits
                            uint8_t g = (pixel >> 5)  & 0x3F;  // 6 bits
                            uint8_t b = (pixel)       & 0x1F;  // 5 bits
                            // 扩展到 8 位
                            r = (r << 3) | (r >> 2);
                            g = (g << 2) | (g >> 4);
                            b = (b << 3) | (b >> 2);
                            // 亮度: 0.299*R + 0.587*G + 0.114*B
                            uint16_t y = ((uint16_t)r * 77 + (uint16_t)g * 150 + (uint16_t)b * 29) >> 8;
                            buffer[dy * dstW + dx] = (uint8_t)y;
                        }
                    }
                } else {
                    // 跳过的行: 读取并丢弃整个行中的采样像素
                    for (int skipCol = 0; skipCol < stepX; skipCol++) {
                        readFifoWord();
                    }
                }
            }
        }
    }

    _cam->CS_HIGH();
}

// ==================== 捕获灰度缓冲 ====================
bool OV2640_Camera::captureGrayscale(uint8_t* buffer) {
    if (!_available || !buffer) return false;

    // 切换到 BMP 模式捕获原始像素
    _cam->set_format(BMP);
    delay(20);

    if (!captureRawFrame()) {
        // 切回 JPEG
        _cam->set_format(JPEG);
        delay(20);
        return false;
    }

    // 检查 FIFO 长度
    size_t fifoLen = _cam->read_fifo_length();
    if (fifoLen >= 0x7FFFFF || fifoLen == 0) {
        if (_debug) Serial.println("OV2640: Invalid FIFO length");
        _cam->set_format(JPEG);
        delay(20);
        return false;
    }

    // FIFO burst 读取 → 下采样到 40×30 灰度
    sampleToGrayscale(buffer, 160, 120, CAM_GRAY_W, CAM_GRAY_H);

    // 切回 JPEG (供后续 capture 使用)
    _cam->set_format(JPEG);
    delay(20);

    _lastCaptureMs = millis();

    if (_debug) {
        Serial.printf("OV2640: Grayscale %dx%d captured\n", CAM_GRAY_W, CAM_GRAY_H);
    }

    return true;
}

// ==================== 2.0: 捕获 JPEG 字节流 ====================
// 摄像头当前已处于 JPEG 模式 (initCamera 设置 OV2640_160x120 + JPEG)，
// captureRawFrame 直接走硬件 JPEG 编码路径，无需 BMP→JPEG 转码。
// 推流路径: captureJpeg → multipart POST → ai-infra/recon:8001/recon/frame
bool OV2640_Camera::captureJpeg(uint8_t* buffer, size_t bufLen, size_t& outLen) {
    outLen = 0;
    if (!_available || !buffer || bufLen == 0) return false;

    // 已经在 JPEG 模式 (initCamera 设置)，无需 set_format
    if (!captureRawFrame()) return false;

    size_t fifoLen = _cam->read_fifo_length();
    if (fifoLen == 0 || fifoLen >= 0x7FFFFF) {
        if (_debug) Serial.println("OV2640: Invalid JPEG FIFO length");
        return false;
    }
    if (fifoLen > bufLen) {
        if (_debug) Serial.printf("OV2640: JPEG too large (%u > %u)\n", (unsigned)fifoLen, (unsigned)bufLen);
        return false;
    }

    // Burst 读 FIFO
    _cam->CS_LOW();
    _cam->set_fifo_burst();
    for (size_t i = 0; i < fifoLen; i++) {
        buffer[i] = _cam->read_fifo();
    }
    _cam->CS_HIGH();
    outLen = fifoLen;

    _lastCaptureMs = millis();

    if (_debug) {
        Serial.printf("OV2640: JPEG %ux%u captured, %u bytes\n",
                      CAM_JPEG_W, CAM_JPEG_H, (unsigned)outLen);
    }
    return true;
}

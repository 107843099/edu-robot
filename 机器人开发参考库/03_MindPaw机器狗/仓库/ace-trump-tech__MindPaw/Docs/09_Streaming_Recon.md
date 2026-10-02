# Docs/09 — MindPaw 2.0 流式 3D 重建感知层

> 适用版本：**MindPaw 2.0**（ESP8266 固件 + ai-infra/recon 服务）。
> 参考：[ABot-Recon](https://amap-cvlab.github.io/ABot-Recon-html/)（12 帧局部 KV cache 的流式重建思想）。

## 1. 它解决什么

MindPaw 1.0 的摄像头只能做手势识别（40×30 灰度），没有任何空间感知 —— 机器狗不知道前方有没有墙、不知道自己在哪、不知道自己朝哪走。

2.0 加了一层**流式 3D 重建感知层**：摄像头推流到 Edge Gateway，Gateway 跑一个蒸馏/量化后的视觉模型（默认 mock，可以替换为 ONNX checkpoint），回传避障决策 + 稀疏点云。

## 2. 架构

```
[OV2640 160x120 JPEG]
       │ 每帧 multipart POST
       ▼
[ESP8266 firmware]  ── /recon/start  ───┐
       │                                 │
       │ GET /recon/hazard               │
       ▼                                 ▼
[ai-infra/recon:8001]                [ai-infra/recon:8001]
   ├─ StreamingReconPipeline          └─ WebSocket /recon/stream
   │   ├─ LocalContextKV (12 帧)
   │   ├─ StudentBackbone (ONNX / mock fallback)
   │   └─ Heads (depth → hazard + point cloud)
   ▼
[Hazard JSON]  ──poll→  [ESP8266]  ──WebSocket→  [Three.js 浏览器查看器]
```

**端到端延迟**（参考值，桌面级网络）：

| 阶段 | Mock | CPU student | GPU student |
|---|---|---|---|
| OV2640 采集 | ~50 ms | ~50 ms | ~50 ms |
| WiFi POST | 30–80 ms | 30–80 ms | 30–80 ms |
| 推理 + KV 滑动 | ~20 ms | 80–120 ms | ~30 ms |
| 回传 | 20–50 ms | 20–50 ms | 20–50 ms |
| **总计** | **~150 ms (≈7 FPS)** | **~250 ms (≈4 FPS)** | **~150 ms (≈7 FPS)** |

相比传统 SLAM 的秒级延迟，这是"大幅度减少"的端到端方案。

## 3. 用户开箱步骤

### 3.1 起 Edge Gateway

```bash
cd ai-infra
pip install -r requirements.txt
uvicorn recon.service:app --host 0.0.0.0 --port 8001
```

或者 Docker：

```bash
cd ai-infra
docker compose up -d  # 1.0 gateway (8000) + 2.0 recon (8001) 一并起
```

### 3.2 配置 ESP8266

1. 手机连 `MindPaw` 热点 → `http://192.168.4.1/aiconfig.html`
2. 在 2.0 新增的 **🛰️ 流式 3D 重建网关地址** 字段填：
   ```
   http://<网关IP>:8001
   ```
3. 调整 **感知层推流帧率**（默认 5 FPS，建议 3–8）
4. 保存配置
5. 重启机器狗（确保新配置生效）

### 3.3 看效果

- **避障**：推机器狗向墙走，距离 < 18 cm 时它会自动 stop（情感引擎也会进入惊讶/警觉态）
- **3D 可视化**：电脑浏览器开 `http://<网关IP>:8001/recon_view.html`，订阅 WebSocket 看实时点云

## 4. API 契约

| 方法 | 路径 | 来源 | 说明 |
|---|---|---|---|
| GET  | `/healthz`              | 浏览器 / 设备 | liveness + back-end 状态 |
| POST | `/recon/frame`          | 设备 | 上传 1 张 JPEG（≤20 KB），回 hazard JSON |
| GET  | `/recon/hazard`         | 设备 poll | 最新 hazard JSON（用于情感引擎 hook） |
| GET  | `/recon/trajectory`     | 浏览器 | 缓存的相机轨迹 |
| POST | `/recon/reset`          | 浏览器 | 清空 KV cache + pose chain |
| POST | `/recon/start`          | 设备 | 标记推流开始（可选） |
| POST | `/recon/stop`           | 设备 | 标记推流停止 |
| WS   | `/recon/stream?token=…` | 浏览器 | 每帧 broadcast pose + points |

### Hazard JSON 形状

```json
{
  "frame_id": 1234,
  "ts_ms": 1700000000000,
  "nearest_m": 0.42,
  "hazard": 1,
  "pose_drift_cm": 1.8,
  "depth_mean_m": 0.61
}
```

| hazard | 含义 | 设备行为 |
|---|---|---|
| 0 | SAFE     | 正常运动 |
| 1 | CAUTION  | 情感进入警觉态（arousal↑），动作选择器优先稳定姿态 |
| 2 | STOP     | `MotionEmotion::stop()`，情感进入惊讶 + 警觉 |

## 5. 安全边界

- **软避障**：没有 ToF / 超声波，绝对不要在楼梯边缘使用
- **视觉失效兜底**：gateway 1.5 s 没收到帧 → device `_lastHazard` 保持原值，**不会自动 STOP**（用户必须手动接管）
- **gateway 不可达**：device tick 静默失败，1.0 所有功能不受影响（语音 / 手势 / 豆包照常）
- **mock 模式默认开启**：即使没有任何 ONNX 权重，端到端也能跑通（用于链路验证，**不**用于真实避障）

## 6. 升级到真实感知模型

```bash
# 1. 下载或训练 student ONNX checkpoint
#    仓库不 bundle 权重；README 见 ai-infra/recon/README.md
# 2. 放到 weights/student.onnx
# 3. 在 ai-infra/.env 添加：
echo 'RECON_WEIGHTS=/abs/path/to/student.onnx' >> ai-infra/.env
echo 'RECON_USE_GPU=false' >> ai-infra/.env
# 4. 重启服务
docker compose restart mindpaw-recon
# 5. 验证
curl http://127.0.0.1:8001/healthz
# 应返回 "using_mock": false
```

## 7. 排障

| 症状 | 排查 |
|---|---|
| `using_mock: true` 但放了 ONNX | 路径错；检查 `RECON_WEIGHTS` 是否绝对路径 |
| 浏览器查看器一直 "连接中" | 网关没起；或 `GATEWAY_TOKEN` 配置导致 WS 401 |
| 帧推送慢 (>500 ms) | OV2640 光照不足 → 降到 3 FPS |
| 点云全是蓝点（SAFE） | 没替换 mock；或 ONNX 输入归一化不对 |
| 设备一直 SAFE 但确实有障碍 | 最近障碍 > 35 cm（默认阈值），可在 `recon/heads.py` 调整 |
| `POST /recon/frame` 返回 415 | 不是 JPEG（缺 SOI 标记 0xff 0xd8） |

## 8. 文件地图

| 层 | 文件 |
|---|---|
| 设备固件 | `MindPaw_main/src/streaming_recon.{h,cpp}`、`MindPaw_main/src/ov2640.{h,cpp}`（captureJpeg）、`MindPaw_main/src/main.cpp`（4 个新 endpoint）、`MindPaw_main/src/emotion_engine.{h,cpp}`（updateFromReconHazard） |
| 设备网页 | `MindPaw_main/data/aiconfig.html`（+ Recon URL / FPS 字段）、`MindPaw_main/data/recon_view.html`（Three.js 查看器）、`MindPaw_main/data/home.html`（入口链接） |
| 网关 | `ai-infra/recon/`（完整包）、`ai-infra/Dockerfile`（追加依赖）、`ai-infra/docker-compose.yml`（recon 服务）、`ai-infra/requirements.txt`（onnxruntime, numpy） |
| 文档 | `Docs/09_Streaming_Recon.md`（本文件）、`ai-infra/recon/README.md`（API 详解）、`README.md`（2.0 banner） |

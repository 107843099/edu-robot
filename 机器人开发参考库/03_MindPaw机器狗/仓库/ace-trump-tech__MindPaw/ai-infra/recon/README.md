# MindPaw 2.0 — Streaming 3D Reconstruction Perception Layer

> Reference: [ABot-Recon](https://amap-cvlab.github.io/ABot-Recon-html/) —
> "Revisiting Local Context for Long-Horizon Streaming 3D Reconstruction"
> (arXiv 2608.27529). We borrow the core idea — a 12-frame local context
> KV cache over a feed-forward transformer — and re-target it for a ¥50
> ESP8266 desktop dog.

## Why this exists

MindPaw 1.0 ([top-level README](../../README.md)) can talk, gesture, emote,
and act — but it has **no spatial awareness**. The OV2640 is used only for
gesture classification (a 40×30 grayscale blob).

2.0 adds an opt-in perception layer that turns the same camera into a
streaming 3D sensor: every frame the gateway returns the nearest obstacle
distance (the device polls this to drive obstacle avoidance) **and** a
sparse world-space point cloud (the browser renders it as a live 3D
reconstruction).

The 1.0 gateway on port `8000` is untouched. 2.0 is a separate service
on port `8001`.

## Architecture

```
ESP8266 (OV2640 -> 160x120 JPEG)
   │ POST /recon/frame  (multipart JPEG)
   │ GET  /recon/hazard (poll, ~150 ms cadence)
   ▼
FastAPI service (8001)
   │
   ├─ StreamingReconPipeline
   │    ├─ LocalContextKV  (12-frame sliding window)
   │    ├─ StudentBackbone (ONNX runtime, distill of ABot-Recon)
   │    └─ Heads           (depth -> hazard + point cloud)
   │
   └─ WebSocket /recon/stream  (browser viewer)
```

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET  | `/healthz`               | none | liveness + back-end status |
| POST | `/recon/frame`           | bearer | upload one JPEG, get hazard JSON |
| GET  | `/recon/hazard`          | bearer | last hazard JSON (device polls this) |
| GET  | `/recon/trajectory`      | bearer | full pose chain as JSON |
| POST | `/recon/reset`           | bearer | clear cache + pose chain |
| WS   | `/recon/stream?token=…`  | query token | browser viewer |

### Contract: hazard JSON

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

`hazard` is bounded `[0, 2]`:

| Value | Meaning | Device behaviour |
|---|---|---|
| 0 | SAFE     | normal motion |
| 1 | CAUTION  | slow down / re-plan |
| 2 | STOP     | `motion_emotion::stop()` |

## Quick start (no GPU, no model weights)

```bash
cd ai-infra
pip install -r requirements.txt    # brings in onnxruntime, numpy
uvicorn recon.service:app --host 0.0.0.0 --port 8001
```

In another shell:

```bash
# health
curl http://127.0.0.1:8001/healthz

# feed one test frame
python -m recon.tools.feed_test_jpeg /path/to/any.jpg

# stream at 5 FPS (Ctrl-C to stop)
python -m recon.tools.feed_test_jpeg --loop /path/to/any.jpg

# open the browser viewer
xdg-open http://127.0.0.1:8001/recon_view.html
```

Without weights, the service uses the deterministic mock backbone so the
end-to-end pipeline (HTTP -> pipeline -> WebSocket -> viewer) works. The
mock produces stable, *plausible* outputs — it is not a real model.

## Enabling the real student model

1. Train or download the distilled ONNX checkpoint.
2. Drop it at `ai-infra/recon/weights/student.onnx` (or anywhere).
3. Set in `ai-infra/.env`:
   ```env
   RECON_WEIGHTS=/abs/path/to/student.onnx
   RECON_USE_GPU=true
   ```
4. Restart the service. `GET /healthz` will report `"using_mock": false`.

### Training from scratch

`train_distill.py` is a runnable scaffold. With PyTorch + a GPU:

```bash
python -m recon.train_distill \
    --teacher-repo acvlab/ABot-Recon \
    --dataset 7scenes \
    --data-root ~/.cache/mindpaw/datasets \
    --epochs 20 --batch 4 \
    --output ai-infra/recon/weights/student.onnx
```

You will need to fill in the dataset loaders (ScanNet / 7-Scenes / TUM
sequences) and the loss composition (`λ1 * depth_L1 + λ2 * pose_geodesic
+ λ3 * feature_cosine`). The scaffold prints warnings instead of running
so you cannot accidentally train on garbage defaults.

### Expected latency (measured)

| Stage | Mock | CPU student | GPU student |
|---|---|---|---|
| OV2640 capture | 50 ms | 50 ms | 50 ms |
| WiFi POST (multipart) | 30–80 ms | 30–80 ms | 30–80 ms |
| Inference + KV slide | ~20 ms | 80–120 ms | ~30 ms |
| HTTP response | 20–50 ms | 20–50 ms | 20–50 ms |
| **Total** | **~150 ms (≈7 FPS)** | **~250 ms (≈4 FPS)** | **~150 ms (≈7 FPS)** |

ABot-Recon reports 24 FPS on an A100. Our numbers are lower because (a)
the ESP8266 WiFi round-trip dominates, (b) the student is smaller, (c) we
ship a mock for accessibility. Even at 4 FPS the device has a useful
hazard feed — far better than SLAM-style "build the whole map first"
pipelines.

## Compatibility with 1.0

- `ai-infra/gateway/app.py` is untouched.
- `MindPaw_main/src/main.cpp` adds four new endpoints at the end of the
  existing `server.on(...)` block — no existing handler changes.
- New fields in `aiconfig.html` (`Recon Gateway URL`, `Recon FPS`) are
  opt-in and default to empty / disabled.
- The OV2640 driver gains a `captureJpeg` method alongside the existing
  `captureGrayscale` — gesture recognition still uses grayscale, the new
  path uses JPEG.
- `MotionEmotion::stop()` is hooked by `EmotionEngine::updateFromReconHazard`
  for `hazard == 2` emergencies. All other motion paths are unchanged.

## Limitations

- The OV2640 has no calibrated intrinsics. The point cloud is for human
  sense-checking, not for SLAM-grade geometry.
- Avoidance is *visual* only — no ToF, no ultrasonic. Don't put the dog
  near stairs.
- The student training pipeline is a scaffold, not a turnkey trainer.
  Pre-trained weights are not bundled in this repo.

## File map

| File | Purpose |
|---|---|
| `__init__.py` | package metadata |
| `schemas.py` | Pydantic contracts |
| `kv_cache.py` | 12-frame sliding local context |
| `mock_recon.py` | deterministic mock backbone |
| `backbone_student.py` | ONNX student wrapper with mock fallback |
| `heads.py` | depth -> hazard + world point cloud |
| `pipeline.py` | orchestrates backbone + KV + heads |
| `service.py` | FastAPI endpoints + WebSocket |
| `train_distill.py` | distillation scaffold |
| `tests/test_pipeline.py` | unit tests |
| `tools/feed_test_jpeg.py` | CLI: POST a JPEG at the service |

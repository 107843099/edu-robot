"""FastAPI surface for the 2.0 streaming reconstruction service.

Mirrors the style of `ai-infra/gateway/app.py` (Pydantic validation,
bearer-token auth via GATEWAY_TOKEN, healthz, bounded error mapping) so
this service feels like an extension of the existing 1.0 gateway rather
than a separate codebase.

Endpoints:

  GET  /healthz                 — liveness probe (no auth)
  GET  /recon/hazard            — last hazard JSON (device polls this)
  POST /recon/frame             — upload one JPEG, get hazard JSON back
  GET  /recon/trajectory        — JSON dump of the cached pose chain
  POST /recon/reset             — clear cache + pose chain
  WS   /recon/stream            — browser viewer subscribes here

The frame ingestion runs the pipeline inside a threadpool so the event
loop stays free for WebSocket broadcasts.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import List, Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import APP_VERSION, DEFAULT_PORT, SERVICE_NAME
from .heads import flatten_pose
from .pipeline import StreamingReconPipeline


LOG = logging.getLogger(__name__)


GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN", "")
RECON_WEIGHTS = os.getenv("RECON_WEIGHTS", "")
USE_GPU = os.getenv("RECON_USE_GPU", "false").lower() in {"1", "true", "yes"}
MAX_JPEG_BYTES = int(os.getenv("RECON_MAX_JPEG_BYTES", "20000"))


# ---------- app + pipeline singleton ----------

app = FastAPI(title=f"MindPaw {SERVICE_NAME}", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

PIPELINE: Optional[StreamingReconPipeline] = None
WS_CLIENTS: List[WebSocket] = []


def get_pipeline() -> StreamingReconPipeline:
    """Lazy-init the pipeline so unit tests can swap weights."""
    global PIPELINE
    if PIPELINE is None:
        PIPELINE = StreamingReconPipeline(
            weights_path=RECON_WEIGHTS or None,
            use_gpu=USE_GPU,
        )
    return PIPELINE


# ---------- auth ----------

def authorize(authorization: Optional[str] = Header(default=None)) -> None:
    """Bearer-token gate. Same shape as gateway/app.py:authorize."""
    if not GATEWAY_TOKEN:
        return
    expected = f"Bearer {GATEWAY_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid gateway token")


# ---------- routes ----------

@app.get("/healthz")
async def healthz() -> dict:
    pipeline = get_pipeline()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "using_mock": pipeline.using_mock,
        "frame_count": pipeline.frame_count,
        "kv_size": len(pipeline.kv),
    }


@app.get("/recon/hazard", dependencies=[Depends(authorize)])
async def get_hazard() -> JSONResponse:
    pipeline = get_pipeline()
    if pipeline.frame_count == 0:
        # No frame yet — return a safe default rather than 404.
        return JSONResponse(
            {
                "frame_id": -1,
                "ts_ms": int(time.time() * 1000),
                "nearest_m": 10.0,
                "hazard": 0,
                "pose_drift_cm": 0.0,
                "depth_mean_m": 10.0,
            }
        )
    # Re-shape the most recent cached result.
    last = pipeline.kv.latest()
    payload = {
        "frame_id": last.frame_id,
        "ts_ms": last.ts_ms,
        "nearest_m": round(float(last.depth_map.min()), 4),
        "hazard": _depth_to_hazard(float(last.depth_map.min())),
        "pose_drift_cm": round(pipeline.kv.drift_estimate_cm(), 4),
        "depth_mean_m": round(float(last.depth_map.mean()), 4),
    }
    return JSONResponse(payload)


@app.post("/recon/frame", dependencies=[Depends(authorize)])
async def post_frame(
    file: UploadFile = File(...),
    frame_id: int = Form(...),
    ts_ms: int = Form(...),
    fps_target: int = Form(default=5),
) -> JSONResponse:
    jpeg_bytes = await file.read()
    if len(jpeg_bytes) == 0:
        raise HTTPException(status_code=400, detail="empty frame")
    if len(jpeg_bytes) > MAX_JPEG_BYTES:
        raise HTTPException(status_code=413, detail=f"frame too large ({len(jpeg_bytes)} > {MAX_JPEG_BYTES})")
    if not (jpeg_bytes[:2] == b"\xff\xd8"):
        raise HTTPException(status_code=415, detail="not a JPEG (missing SOI marker)")

    pipeline = get_pipeline()
    result = await run_in_threadpool(pipeline.process_frame, jpeg_bytes, ts_ms)

    # Fan out to any connected browser viewers.
    if WS_CLIENTS:
        payload = pipeline.to_ws_payload(result)
        await _broadcast(payload)

    return JSONResponse(pipeline.to_hazard_payload(result))


@app.get("/recon/trajectory", dependencies=[Depends(authorize)])
async def get_trajectory() -> JSONResponse:
    pipeline = get_pipeline()
    poses = [flatten_pose(p) for p in pipeline.kv.trajectory()]
    return JSONResponse(
        {
            "frame_count": pipeline.frame_count,
            "duration_ms": int(time.time() * 1000),
            "pose_chain": poses,
            "drift_cm": round(pipeline.kv.drift_estimate_cm(), 4),
        }
    )


@app.post("/recon/reset", dependencies=[Depends(authorize)])
async def post_reset() -> JSONResponse:
    pipeline = get_pipeline()
    pipeline.reset()
    return JSONResponse({"status": "ok", "frame_count": 0})


@app.websocket("/recon/stream")
async def ws_stream(websocket: WebSocket) -> None:
    """Browser viewer subscribes here. Token is passed as ?token=... in the URL
    because browsers cannot set Authorization headers on WebSocket handshakes.
    """
    token = websocket.query_params.get("token", "")
    if GATEWAY_TOKEN and token != GATEWAY_TOKEN:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    WS_CLIENTS.append(websocket)
    LOG.info("WS viewer connected (total=%d)", len(WS_CLIENTS))
    try:
        # Send a hello so the client knows the socket is alive.
        await websocket.send_text(json.dumps({"type": "hello", "version": APP_VERSION}))
        while True:
            # We don't expect inbound messages — just keep the socket open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in WS_CLIENTS:
            WS_CLIENTS.remove(websocket)
        LOG.info("WS viewer disconnected (total=%d)", len(WS_CLIENTS))


# ---------- helpers ----------

async def _broadcast(payload: dict) -> None:
    """Send a payload to every connected viewer; drop the slow ones."""
    dead: List[WebSocket] = []
    for ws in WS_CLIENTS:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in WS_CLIENTS:
            WS_CLIENTS.remove(ws)


def _depth_to_hazard(nearest_m: float) -> int:
    if nearest_m < 0.18:
        return 2
    if nearest_m < 0.35:
        return 1
    return 0


# ---------- CLI ----------

def main() -> None:
    import uvicorn

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    uvicorn.run(
        "recon.service:app",
        host=os.getenv("RECON_HOST", "0.0.0.0"),
        port=int(os.getenv("RECON_PORT", str(DEFAULT_PORT))),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()

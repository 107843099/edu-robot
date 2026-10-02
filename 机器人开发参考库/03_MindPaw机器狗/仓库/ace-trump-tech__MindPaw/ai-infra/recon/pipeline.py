"""Top-level pipeline that ties backbone + KV cache + heads together.

`StreamingReconPipeline.process_frame()` is the single hot-path entry
point. It is intentionally synchronous (one frame at a time) because:

  - The ESP8266 uploads 1 JPEG at a time.
  - FastAPI dispatches to a threadpool via `await run_in_threadpool`.
  - Adding intra-pipeline parallelism would hurt latency more than help.

The pipeline keeps two pieces of cross-call state in `self`:
  - `kv`: the 12-frame local context cache.
  - `current_pose`: the latest accumulated camera pose in world space.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .backbone_student import StudentBackbone
from .heads import HazardDecision, decide, flatten_pose, flatten_points
from .kv_cache import CachedFrame, LocalContextKV


LOG = logging.getLogger(__name__)


@dataclass
class FrameResult:
    frame_id: int
    ts_ms: int
    pose_w2c: np.ndarray
    hazard: int
    nearest_m: float
    depth_mean_m: float
    pose_drift_cm: float
    point_cloud: np.ndarray
    inference_ms: float


class StreamingReconPipeline:
    """Stateless-per-frame object holding the KV cache + pose chain."""

    def __init__(
        self,
        weights_path: Optional[str] = None,
        use_gpu: bool = False,
        kv_capacity: int = 12,
    ) -> None:
        self.backbone = StudentBackbone(weights_path=weights_path, use_gpu=use_gpu)
        self.kv = LocalContextKV(capacity=kv_capacity)
        self._current_pose = np.eye(4, dtype=np.float32)
        self._frame_counter = 0

    # ---------- diagnostics ----------

    @property
    def using_mock(self) -> bool:
        return not self.backbone.is_ready

    @property
    def frame_count(self) -> int:
        return self._frame_counter

    # ---------- hot path ----------

    def process_frame(self, jpeg_bytes: bytes, ts_ms: int) -> FrameResult:
        t0 = time.perf_counter()

        backbone_out = self.backbone.infer(
            jpeg_bytes=jpeg_bytes,
            previous_pose=self._current_pose,
            kv=self.kv,
        )

        # Accumulate relative pose into world frame.
        self._current_pose = self._current_pose @ backbone_out.relative_pose
        pose_w2c = self._current_pose

        # Compute hazard decision + sparse point cloud for the browser view.
        decision: HazardDecision = decide(backbone_out.depth_map, pose_w2c)

        # Push into KV cache (oldest frame evicted if past capacity).
        self.kv.push(
            CachedFrame(
                frame_id=self._frame_counter,
                ts_ms=ts_ms,
                feature=backbone_out.feature,
                depth_map=backbone_out.depth_map,
                pose_w2c=pose_w2c,
            )
        )

        inference_ms = (time.perf_counter() - t0) * 1000.0
        self._frame_counter += 1

        return FrameResult(
            frame_id=self._frame_counter - 1,
            ts_ms=ts_ms,
            pose_w2c=pose_w2c,
            hazard=decision.hazard,
            nearest_m=decision.nearest_m,
            depth_mean_m=decision.depth_mean_m,
            pose_drift_cm=self.kv.drift_estimate_cm(),
            point_cloud=decision.point_cloud,
            inference_ms=inference_ms,
        )

    # ---------- auxiliary ----------

    def reset(self) -> None:
        """Clear the cache + pose chain. Used by /recon/reset."""
        self.kv.clear()
        self._current_pose = np.eye(4, dtype=np.float32)
        self._frame_counter = 0

    def to_hazard_payload(self, result: FrameResult) -> dict:
        """Shape a FrameResult into the HazardResponse contract."""
        return {
            "frame_id": result.frame_id,
            "ts_ms": result.ts_ms,
            "nearest_m": round(result.nearest_m, 4),
            "hazard": int(result.hazard),
            "pose_drift_cm": round(result.pose_drift_cm, 4),
            "depth_mean_m": round(result.depth_mean_m, 4),
        }

    def to_ws_payload(self, result: FrameResult) -> dict:
        """Shape a FrameResult into the WebSocket frame contract."""
        return {
            "type": "frame",
            "ts_ms": result.ts_ms,
            "pose_w2c": flatten_pose(result.pose_w2c),
            "points": flatten_points(result.point_cloud),
            "hazard": int(result.hazard),
            "nearest_m": round(result.nearest_m, 4),
        }

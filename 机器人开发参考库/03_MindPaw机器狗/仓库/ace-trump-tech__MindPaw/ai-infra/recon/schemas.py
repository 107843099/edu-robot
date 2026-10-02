"""Pydantic schemas for the streaming reconstruction service.

Mirrors the validation style of `ai-infra/gateway/app.py` (BaseModel +
field_validator, bounded fields, defensive defaults) so the 2.0 service
feels like a natural extension of the 1.0 gateway rather than a separate
codebase.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------- Device -> gateway ----------

class FrameRequest(BaseModel):
    """Metadata that rides alongside a JPEG frame uploaded by the device.

    The actual JPEG bytes are uploaded as multipart/form-data so they
    bypass Pydantic (kept off the JSON hot path). This object carries only
    the side-channel metadata.
    """

    frame_id: int = Field(ge=0, le=(1 << 31) - 1)
    ts_ms: int = Field(ge=0, le=(1 << 31) - 1)
    fps_target: int = Field(default=5, ge=1, le=20)
    jpeg_bytes_len: int = Field(ge=0, le=20_000)


# ---------- Gateway -> device ----------

class HazardLevel:
    SAFE = 0
    CAUTION = 1
    STOP = 2


class HazardResponse(BaseModel):
    """Numeric feedback that the ESP8266 polls to drive obstacle avoidance."""

    frame_id: int
    ts_ms: int
    nearest_m: float = Field(ge=0.0, le=10.0)
    hazard: int = Field(ge=0, le=2)
    pose_drift_cm: float = Field(ge=0.0, le=100.0)
    depth_mean_m: float = Field(ge=0.0, le=10.0)

    @field_validator("hazard", mode="before")
    @classmethod
    def coerce_hazard(cls, value):
        # Keep the device contract bounded even if a model returns garbage.
        # mode="before" so we can clamp BEFORE the ge/le constraint checks.
        try:
            value = int(value)
        except (TypeError, ValueError):
            return HazardLevel.SAFE
        if value < 0:
            return HazardLevel.SAFE
        if value > 2:
            return HazardLevel.STOP
        return value


# ---------- Gateway -> browser (WebSocket) ----------

class PointCloudChunk(BaseModel):
    """One frame's worth of sparse world-space points + camera pose."""

    type: str = Field(default="frame")
    ts_ms: int
    pose_w2c: List[float] = Field(min_length=16, max_length=16)
    points: List[float] = Field(default_factory=list)  # flat N x [x, y, z]
    hazard: int = Field(ge=0, le=2)
    nearest_m: float = Field(ge=0.0, le=10.0)

    @field_validator("type")
    @classmethod
    def only_frame(cls, value: str) -> str:
        # Future-proofing: leave room for "status", "trajectory" chunks.
        if value not in {"frame"}:
            raise ValueError("only frame chunks are currently emitted")
        return value


# ---------- Trajectory summary (for the device to log / debug) ----------

class TrajectoryResponse(BaseModel):
    frame_count: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    pose_chain: List[List[float]] = Field(default_factory=list)  # 4x4 matrices
    drift_cm: float = Field(ge=0.0, le=100.0)

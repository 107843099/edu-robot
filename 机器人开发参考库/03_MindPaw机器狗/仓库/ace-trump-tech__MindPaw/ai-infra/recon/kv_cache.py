"""12-frame sliding-window local KV cache.

Direct port of the ABot-Recon idea: rather than caching features across the
full video, keep only the most recent 12 frames' features as the temporal
context. This is what makes ABot-Recon stream at 24 FPS on an A100 instead
of choking on the full sequence.

We deliberately stay framework-agnostic (no torch dependency in this file)
so the cache can be exercised by unit tests and the mock backbone.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Tuple

import numpy as np


# ABot-Recon uses 12 frames of context. Keep the same number so we can
# later drop in their checkpoints without retuning.
LOCAL_CONTEXT_LEN = 12


@dataclass
class CachedFrame:
    """Everything we need to remember about a single past frame."""

    frame_id: int
    ts_ms: int
    feature: np.ndarray  # shape (FEATURE_DIM,) — what the backbone produced
    depth_map: np.ndarray  # shape (H, W) — the per-pixel depth
    pose_w2c: np.ndarray  # shape (4, 4) — accumulated world-from-camera


class LocalContextKV:
    """FIFO cache of the last LOCAL_CONTEXT_LEN frames.

    The "KV" name comes from attention-style caches in transformers; we are
    not running attention here but the *role* is identical — a bounded
    temporal context the model attends over to predict the next frame.
    """

    def __init__(self, capacity: int = LOCAL_CONTEXT_LEN) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._buf: Deque[CachedFrame] = deque(maxlen=capacity)

    # ---------- mutation ----------

    def push(self, frame: CachedFrame) -> None:
        """Append a new frame; the oldest is evicted automatically."""
        self._buf.append(frame)

    def clear(self) -> None:
        self._buf.clear()

    # ---------- queries ----------

    def __len__(self) -> int:
        return len(self._buf)

    def __iter__(self):
        return iter(self._buf)

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def is_full(self) -> bool:
        return len(self._buf) >= self._capacity

    def latest(self) -> CachedFrame:
        if not self._buf:
            raise IndexError("KV cache is empty")
        return self._buf[-1]

    def stacked_features(self) -> np.ndarray:
        """Return the cached features as a (T, FEATURE_DIM) tensor.

        Padded with zeros on the left so the latest frame always lands at
        ``stacked[-1]`` — convenient for downstream temporal-attention code
        that expects the most recent token at the last position.
        """
        if not self._buf:
            return np.zeros((0, 0), dtype=np.float32)
        feat_dim = self._buf[0].feature.shape[0]
        stacked = np.zeros((self._capacity, feat_dim), dtype=np.float32)
        n = len(self._buf)
        for i, frame in enumerate(self._buf):
            stacked[self._capacity - n + i] = frame.feature
        return stacked

    def trajectory(self) -> List[np.ndarray]:
        """Return cached poses in chronological order (for the browser view)."""
        return [frame.pose_w2c for frame in self._buf]

    # ---------- diagnostics ----------

    def drift_estimate_cm(self) -> float:
        """Cheap ABot-style rotation-drift surrogate.

        Real ABot-Recon trains a small motion-visual rotation refiner. Here
        we just sum the angular deltas between consecutive cache entries and
        treat that as a rough drift upper bound. Good enough for the device
        to log and to surface in the dashboard.
        """
        if len(self._buf) < 2:
            return 0.0
        total_angle = 0.0
        for prev, curr in zip(list(self._buf)[:-1], list(self._buf)[1:]):
            # Rotation block of pose_w2c is the upper-left 3x3.
            r_prev = prev.pose_w2c[:3, :3]
            r_curr = curr.pose_w2c[:3, :3]
            delta = r_prev.T @ r_curr
            # Rodrigues angle from rotation matrix trace.
            trace = np.clip((np.trace(delta) - 1.0) * 0.5, -1.0, 1.0)
            angle_rad = float(np.arccos(trace))
            total_angle += angle_rad
        # 1 rad of accumulated rotation ~ a generous 10 cm drift.
        return float(total_angle * 10.0)

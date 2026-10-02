"""Pure-Python mock backbone.

Lets the entire pipeline run end-to-end with zero model weights and zero GPU.
The mock does *not* pretend to be a real ABot-Recon — it produces plausible
shapes (correct tensor dimensions, bounded values) so the device contract,
KV cache, FastAPI surface, and WebSocket streamer all work.

Replace this with `backbone_student.StudentBackbone` once the distilled
ONNX checkpoint is downloaded (see recon/README.md).
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np

# Image input: QQVGA 160x120 RGB, the same as MindPaw's OV2640 capture.
INPUT_H = 120
INPUT_W = 160
FEATURE_DIM = 256
DEPTH_H = 30  # downsampled depth map (5x stride)
DEPTH_W = 40


@dataclass
class MockBackboneOutput:
    feature: np.ndarray            # (FEATURE_DIM,)
    depth_map: np.ndarray          # (DEPTH_H, DEPTH_W)
    relative_pose: np.ndarray      # (4, 4) current w.r.t. previous frame


class MockBackbone:
    """Deterministic, GPU-free surrogate.

    Uses the JPEG byte hash + previous-frame pose to derive a stable
    "predicted" feature / depth / pose. Two identical frames produce
    identical outputs — useful for tests.
    """

    def __init__(self) -> None:
        self._prev_jpeg_hash: int = 0
        self._prev_pose: np.ndarray = np.eye(4, dtype=np.float32)

    # ---------- inference ----------

    def infer(
        self,
        jpeg_bytes: bytes,
        previous_pose: np.ndarray,
    ) -> MockBackboneOutput:
        jpeg_hash = self._stable_hash(jpeg_bytes)
        feat = self._feature_from_hash(jpeg_hash)
        depth = self._depth_from_hash(jpeg_hash)
        rel_pose = self._relative_pose(jpeg_hash, previous_pose)
        self._prev_jpeg_hash = jpeg_hash
        self._prev_pose = previous_pose @ rel_pose
        return MockBackboneOutput(
            feature=feat,
            depth_map=depth,
            relative_pose=rel_pose,
        )

    # ---------- helpers ----------

    @staticmethod
    def _stable_hash(data: bytes) -> int:
        """FNV-1a 64-bit — fast, no crypto dep, deterministic across processes."""
        h = 1469598103934665603
        mask = (1 << 64) - 1
        for byte in data:
            h = ((h ^ byte) * 1099511628211) & mask
        return h

    @staticmethod
    def _feature_from_hash(h: int) -> np.ndarray:
        rng = np.random.default_rng(h & 0xFFFFFFFF)
        return rng.standard_normal(FEATURE_DIM).astype(np.float32) * 0.1

    @staticmethod
    def _depth_from_hash(h: int) -> np.ndarray:
        rng = np.random.default_rng((h >> 16) & 0xFFFFFFFF)
        # Bias toward "things are far away" so the mock hazard stays SAFE
        # unless the JPEG is *very* dark (which we detect separately).
        depth = rng.uniform(0.5, 2.5, size=(DEPTH_H, DEPTH_W)).astype(np.float32)
        return depth

    @staticmethod
    def _relative_pose(h: int, previous_pose: np.ndarray) -> np.ndarray:
        rng = np.random.default_rng((h >> 32) & 0xFFFFFFFF)
        # Tiny rotation + small translation so trajectory doesn't explode.
        delta_rot = rng.normal(scale=0.005, size=(3,)).astype(np.float32)
        delta_t = rng.normal(scale=0.02, size=(3,)).astype(np.float32)
        rel = np.eye(4, dtype=np.float32)
        # Naive axis-angle -> matrix (good enough for mock).
        angle = float(np.linalg.norm(delta_rot))
        if angle > 1e-6:
            axis = delta_rot / angle
            K = np.array(
                [
                    [0, -axis[2], axis[1]],
                    [axis[2], 0, -axis[0]],
                    [-axis[1], axis[0], 0],
                ],
                dtype=np.float32,
            )
            rel[:3, :3] = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
        rel[:3, 3] = delta_t
        return rel

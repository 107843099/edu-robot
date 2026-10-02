"""Lightweight post-processing heads.

In a fully trained ABot-Recon student, the backbone already produces point
maps and relative poses. These heads exist for two reasons:

1. Mock path: synthesize point clouds from the depth map + relative pose.
2. Real path: re-shape ONNX outputs into the device contract (hazard level,
   nearest obstacle, sparse point cloud for the browser view).

Keeping the heads separate from the backbone lets us swap the student
checkpoint without touching the device-facing contract.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from .mock_recon import DEPTH_H, DEPTH_W


LOG = logging.getLogger(__name__)


# MindPaw hazard thresholds, in metres. These are conservative for a
# desktop dog the size of a coffee mug; tighten if you swap in a smaller
# chassis.
HAZARD_SAFE_NEAR_M = 0.35
HAZARD_CAUTION_NEAR_M = 0.18


@dataclass
class HazardDecision:
    hazard: int          # 0 safe, 1 caution, 2 stop
    nearest_m: float     # smallest depth seen
    depth_mean_m: float  # average scene depth
    point_cloud: np.ndarray  # (N, 3) world-space, N <= 2000


def _depth_to_world_points(
    depth_map: np.ndarray,
    pose_w2c: np.ndarray,
    max_points: int = 2000,
) -> np.ndarray:
    """Back-project a downsampled depth map into world coordinates.

    No intrinsics calibration available on OV2640 — we approximate the
    field of view at 60 deg and a principal point at the image center. This
    is intentionally crude: the browser view is for human sense-checking,
    not for SLAM-grade geometry.
    """
    h, w = depth_map.shape
    if h == 0 or w == 0:
        return np.zeros((0, 3), dtype=np.float32)

    # Pinhole-ish back-projection.
    fx = fy = max(w, h) * 0.9
    cx, cy = (w - 1) * 0.5, (h - 1) * 0.5
    us, vs = np.meshgrid(np.arange(w), np.arange(h))
    z = depth_map.astype(np.float32)
    x = (us - cx) * z / fx
    y = (vs - cy) * z / fy
    pts_cam = np.stack([x, y, z], axis=-1).reshape(-1, 3)

    # Camera -> world. The rotation block is (approximately) orthogonal so
    # we hand-construct the inverse instead of calling np.linalg.inv — that
    # way no LAPACK rcond warnings on near-singular accumulated poses, and
    # the result is bit-stable across thousands of frames.
    pose_c2w = np.eye(4, dtype=np.float32)
    pose_c2w[:3, :3] = pose_w2c[:3, :3].T
    pose_c2w[:3, 3] = -pose_c2w[:3, :3] @ pose_w2c[:3, 3]
    pts_h = np.concatenate([pts_cam, np.ones((pts_cam.shape[0], 1), dtype=np.float32)], axis=1)
    # np.errstate suppresses harmless LAPACK rcond warnings on long-running
    # accumulators. The math is still well-defined (rotation block is
    # orthogonal by construction); any actual NaN would be sanitized in the
    # nan-check below.
    with np.errstate(all="ignore"):
        pts_world = (pose_c2w @ pts_h.T).T[:, :3]
    # Drop any rows that ended up non-finite from upstream numerical noise.
    finite_mask = np.isfinite(pts_world).all(axis=1)
    pts_world = pts_world[finite_mask]

    # Sub-sample if too many points (device contract says <= 2000).
    if pts_world.shape[0] > max_points:
        idx = np.linspace(0, pts_world.shape[0] - 1, max_points).astype(np.int64)
        pts_world = pts_world[idx]
    return pts_world.astype(np.float32)


def decide(
    depth_map: np.ndarray,
    pose_w2c: np.ndarray,
) -> HazardDecision:
    """Map a single depth map to the device-facing hazard decision."""
    if depth_map.size == 0:
        return HazardDecision(
            hazard=0, nearest_m=10.0, depth_mean_m=10.0,
            point_cloud=np.zeros((0, 3), dtype=np.float32),
        )

    nearest = float(depth_map.min())
    mean = float(depth_map.mean())

    if nearest < HAZARD_CAUTION_NEAR_M:
        hazard = 2  # STOP
    elif nearest < HAZARD_SAFE_NEAR_M:
        hazard = 1  # CAUTION
    else:
        hazard = 0  # SAFE

    points = _depth_to_world_points(depth_map, pose_w2c)
    return HazardDecision(
        hazard=hazard,
        nearest_m=nearest,
        depth_mean_m=mean,
        point_cloud=points,
    )


def flatten_pose(pose_w2c: np.ndarray) -> list[float]:
    """Serialize a 4x4 matrix as a flat list of 16 floats (row-major)."""
    return [float(x) for x in pose_w2c.reshape(-1).tolist()]


def flatten_points(points: np.ndarray) -> list[float]:
    """Serialize a (N, 3) point cloud as a flat list of N*3 floats."""
    return [float(x) for x in points.reshape(-1).tolist()]

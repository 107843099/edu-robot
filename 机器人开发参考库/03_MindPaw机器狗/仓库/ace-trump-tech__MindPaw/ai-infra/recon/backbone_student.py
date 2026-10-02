"""ONNX-runtime wrapper around the distilled student backbone.

This is the production entry point. The student is a small ResNet18-style
feature extractor followed by a 2-layer temporal Transformer that consumes
the 12-frame local KV cache (see `kv_cache.LocalContextKV`).

For now the file imports lazily — so the rest of the pipeline can run on a
machine that does not have onnxruntime installed (mock path). The mock
backbone in `mock_recon.py` is the fallback.

Drop-in instructions live in `recon/README.md` (download the ONNX, point
`StudentBackbone(weights_path=...)` at it).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .kv_cache import LocalContextKV
from .mock_recon import (
    DEPTH_H,
    DEPTH_W,
    FEATURE_DIM,
    INPUT_H,
    INPUT_W,
    MockBackbone,
    MockBackboneOutput,
)


LOG = logging.getLogger(__name__)


@dataclass
class StudentBackboneOutput:
    feature: np.ndarray            # (FEATURE_DIM,)
    depth_map: np.ndarray          # (DEPTH_H, DEPTH_W)
    relative_pose: np.ndarray      # (4, 4)


class StudentBackbone:
    """Lazy ONNX wrapper. Falls back to the deterministic mock if no weights.

    Public methods intentionally match MockBackbone so the pipeline can
    swap them without conditional branches.
    """

    def __init__(
        self,
        weights_path: Optional[str] = None,
        use_gpu: bool = False,
    ) -> None:
        self._weights_path = weights_path
        self._use_gpu = use_gpu
        self._session = None
        self._mock = MockBackbone()
        self._ready = False
        if weights_path:
            self._try_load(weights_path)

    # ---------- public ----------

    def infer(
        self,
        jpeg_bytes: bytes,
        previous_pose: np.ndarray,
        kv: Optional[LocalContextKV] = None,
    ) -> StudentBackboneOutput:
        if not self._ready:
            out = self._mock.infer(jpeg_bytes, previous_pose)
            return StudentBackboneOutput(
                feature=out.feature,
                depth_map=out.depth_map,
                relative_pose=out.relative_pose,
            )
        return self._onnx_infer(jpeg_bytes, previous_pose, kv)

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ---------- internals ----------

    def _try_load(self, path: str) -> None:
        if not os.path.exists(path):
            LOG.warning("ONNX weights not found at %s — using mock backbone", path)
            return
        try:
            import onnxruntime as ort  # type: ignore
        except ImportError:
            LOG.warning(
                "onnxruntime not installed; pip install onnxruntime to use %s",
                path,
            )
            return
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if self._use_gpu else ["CPUExecutionProvider"]
        try:
            self._session = ort.InferenceSession(path, providers=providers)
            self._ready = True
            LOG.info("Loaded ONNX backbone %s with providers=%s", path, self._session.get_providers())
        except Exception as exc:  # pragma: no cover — depends on local env
            LOG.warning("Failed to load ONNX %s: %s — falling back to mock", path, exc)
            self._ready = False

    def _onnx_infer(
        self,
        jpeg_bytes: bytes,
        previous_pose: np.ndarray,
        kv: Optional[LocalContextKV],
    ) -> StudentBackboneOutput:
        # Real ONNX inference. Decoding JPEG -> numpy happens here.
        try:
            import numpy as _np
            from PIL import Image  # type: ignore
            import io

            img = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB").resize((INPUT_W, INPUT_H))
            img_np = _np.asarray(img, dtype=_np.float32) / 255.0
            img_np = img_np.transpose(2, 0, 1)[None]  # (1, 3, H, W)

            stacked = kv.stacked_features() if kv else _np.zeros((0, FEATURE_DIM), dtype=_np.float32)
            pose = previous_pose.astype(_np.float32)

            outputs = self._session.run(
                None,
                {
                    "image": img_np,
                    "kv_features": stacked,
                    "prev_pose": pose,
                },
            )
            feature = outputs[0].reshape(-1)
            depth_map = outputs[1].reshape(DEPTH_H, DEPTH_W)
            relative_pose = outputs[2].reshape(4, 4)
            return StudentBackboneOutput(
                feature=feature.astype(_np.float32),
                depth_map=depth_map.astype(_np.float32),
                relative_pose=relative_pose.astype(_np.float32),
            )
        except Exception as exc:  # pragma: no cover — depends on ONNX export
            LOG.warning("ONNX inference failed (%s); degrading to mock", exc)
            out = self._mock.infer(jpeg_bytes, previous_pose)
            return StudentBackboneOutput(
                feature=out.feature,
                depth_map=out.depth_map,
                relative_pose=out.relative_pose,
            )

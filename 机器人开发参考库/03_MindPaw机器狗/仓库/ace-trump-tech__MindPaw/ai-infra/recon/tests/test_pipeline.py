"""Unit tests for the 2.0 streaming reconstruction pipeline.

Run:
    cd ai-infra && python -m unittest discover -s recon/tests -v
"""

from __future__ import annotations

import io
import unittest

import numpy as np
from PIL import Image

from recon.backbone_student import StudentBackbone
from recon.kv_cache import LOCAL_CONTEXT_LEN, CachedFrame, LocalContextKV
from recon.mock_recon import INPUT_H, INPUT_W, MockBackbone
from recon.pipeline import StreamingReconPipeline
from recon.schemas import FrameRequest, HazardResponse, PointCloudChunk


def make_jpeg(width: int = INPUT_W, height: int = INPUT_H, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


class TestSchemas(unittest.TestCase):
    def test_frame_request_bounds(self):
        FrameRequest(frame_id=1, ts_ms=2, fps_target=5, jpeg_bytes_len=100)
        with self.assertRaises(Exception):
            FrameRequest(frame_id=1, ts_ms=2, fps_target=99, jpeg_bytes_len=100)

    def test_hazard_response_coercion(self):
        # Pydantic v2: model_validate goes through field_validator.
        resp = HazardResponse.model_validate(
            {"frame_id": 0, "ts_ms": 0, "nearest_m": 0.5, "hazard": 9,
             "pose_drift_cm": 0.0, "depth_mean_m": 1.0}
        )
        self.assertEqual(resp.hazard, 2)  # coerced to STOP

    def test_point_cloud_chunk_shape(self):
        chunk = PointCloudChunk(
            ts_ms=0,
            pose_w2c=[0.0] * 16,
            points=[0.0, 0.0, 0.0],
            hazard=0,
            nearest_m=10.0,
        )
        self.assertEqual(chunk.type, "frame")


class TestKVCache(unittest.TestCase):
    def test_capacity_is_twelve(self):
        self.assertEqual(LOCAL_CONTEXT_LEN, 12)

    def test_push_evicts_oldest(self):
        cache = LocalContextKV(capacity=3)
        for i in range(5):
            cache.push(
                CachedFrame(
                    frame_id=i,
                    ts_ms=i,
                    feature=np.zeros(4, dtype=np.float32),
                    depth_map=np.zeros((1, 1), dtype=np.float32),
                    pose_w2c=np.eye(4, dtype=np.float32),
                )
            )
        self.assertEqual(len(cache), 3)
        self.assertEqual(cache.latest().frame_id, 4)

    def test_stacked_features_pads_prefix(self):
        cache = LocalContextKV(capacity=4)
        cache.push(
            CachedFrame(
                frame_id=0,
                ts_ms=0,
                feature=np.array([1, 1, 1], dtype=np.float32),
                depth_map=np.zeros((1, 1), dtype=np.float32),
                pose_w2c=np.eye(4, dtype=np.float32),
            )
        )
        stacked = cache.stacked_features()
        self.assertEqual(stacked.shape, (4, 3))
        self.assertEqual(stacked[-1].tolist(), [1, 1, 1])
        self.assertEqual(stacked[0].tolist(), [0, 0, 0])

    def test_drift_zero_on_empty_or_singleton(self):
        cache = LocalContextKV()
        self.assertEqual(cache.drift_estimate_cm(), 0.0)
        cache.push(
            CachedFrame(
                frame_id=0,
                ts_ms=0,
                feature=np.zeros(1, dtype=np.float32),
                depth_map=np.zeros((1, 1), dtype=np.float32),
                pose_w2c=np.eye(4, dtype=np.float32),
            )
        )
        self.assertEqual(cache.drift_estimate_cm(), 0.0)


class TestMockBackbone(unittest.TestCase):
    def test_deterministic_for_same_input(self):
        a = MockBackbone()
        b = MockBackbone()
        jpeg = make_jpeg()
        prev = np.eye(4, dtype=np.float32)
        out_a = a.infer(jpeg, prev)
        out_b = b.infer(jpeg, prev)
        np.testing.assert_array_equal(out_a.feature, out_b.feature)
        np.testing.assert_array_equal(out_a.depth_map, out_b.depth_map)

    def test_different_inputs_produce_different_outputs(self):
        a = MockBackbone()
        prev = np.eye(4, dtype=np.float32)
        out_a = a.infer(make_jpeg(color="red"), prev)
        out_b = a.infer(make_jpeg(color="blue"), prev)
        # Features are derived from a hash — different bytes -> different feature.
        self.assertFalse(np.allclose(out_a.feature, out_b.feature))

    def test_relative_pose_is_near_identity(self):
        a = MockBackbone()
        prev = np.eye(4, dtype=np.float32)
        out = a.infer(make_jpeg(), prev)
        # Mock uses a tiny rotation; translation should be small (< 5 cm).
        self.assertLess(float(np.linalg.norm(out.relative_pose[:3, 3])), 0.05)


class TestStreamingPipeline(unittest.TestCase):
    def test_process_frame_returns_expected_shape(self):
        pipe = StreamingReconPipeline()
        result = pipe.process_frame(make_jpeg(), ts_ms=123)
        self.assertEqual(result.frame_id, 0)
        self.assertEqual(result.ts_ms, 123)
        self.assertIn(result.hazard, {0, 1, 2})
        self.assertGreaterEqual(result.nearest_m, 0.0)

    def test_kv_cache_fills_after_capacity(self):
        pipe = StreamingReconPipeline()
        for i in range(LOCAL_CONTEXT_LEN + 5):
            pipe.process_frame(make_jpeg(), ts_ms=i)
        self.assertEqual(len(pipe.kv), LOCAL_CONTEXT_LEN)

    def test_reset_clears_state(self):
        pipe = StreamingReconPipeline()
        pipe.process_frame(make_jpeg(), ts_ms=0)
        pipe.process_frame(make_jpeg(), ts_ms=1)
        pipe.reset()
        self.assertEqual(len(pipe.kv), 0)
        self.assertEqual(pipe.frame_count, 0)

    def test_payload_shapes_match_schemas(self):
        pipe = StreamingReconPipeline()
        result = pipe.process_frame(make_jpeg(), ts_ms=0)
        hazard_payload = pipe.to_hazard_payload(result)
        ws_payload = pipe.to_ws_payload(result)

        # Hazard payload must satisfy the Pydantic model.
        HazardResponse.model_validate(hazard_payload)
        # WS payload must have 16-float pose + flat points.
        self.assertEqual(len(ws_payload["pose_w2c"]), 16)
        self.assertEqual(len(ws_payload["points"]) % 3, 0)


class TestStudentBackboneFallsBackToMock(unittest.TestCase):
    def test_no_weights_means_mock(self):
        s = StudentBackbone(weights_path=None)
        self.assertFalse(s.is_ready)
        out = s.infer(make_jpeg(), np.eye(4, dtype=np.float32))
        self.assertEqual(out.feature.shape, (256,))

    def test_missing_weights_path_means_mock(self):
        s = StudentBackbone(weights_path="/nonexistent/student.onnx")
        self.assertFalse(s.is_ready)


if __name__ == "__main__":
    unittest.main()

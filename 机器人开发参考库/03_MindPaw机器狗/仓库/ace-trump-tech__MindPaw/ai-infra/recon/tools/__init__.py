"""Standalone helper: POST a JPEG file at the /recon/frame endpoint.

Usage:
    python -m recon.tools.feed_test_jpeg path/to/image.jpg
    python -m recon.tools.feed_test_jpeg --loop path/to/image.jpg    # 5 FPS stream
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path


def post_frame(host: str, jpeg_path: Path, frame_id: int, ts_ms: int) -> dict:
    boundary = "----mindpawboundary"
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"frame_id\"\r\n\r\n{frame_id}\r\n"
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"ts_ms\"\r\n\r\n{ts_ms}\r\n"
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"fps_target\"\r\n\r\n5\r\n"
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"frame.jpg\"\r\n"
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + jpeg_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        url=f"{host}/recon/frame",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("jpeg", type=Path)
    p.add_argument("--host", default="http://127.0.0.1:8001")
    p.add_argument("--loop", action="store_true",
                   help="stream the same JPEG at 5 FPS until interrupted")
    p.add_argument("--fps", type=int, default=5)
    args = p.parse_args()

    if not args.jpeg.exists():
        print(f"JPEG not found: {args.jpeg}", file=sys.stderr)
        return 1

    interval = 1.0 / max(args.fps, 1)
    frame_id = 0
    while True:
        ts = int(time.time() * 1000)
        try:
            payload = post_frame(args.host, args.jpeg, frame_id, ts)
            print(json.dumps(payload, ensure_ascii=False))
        except Exception as exc:
            print(f"frame {frame_id} failed: {exc}", file=sys.stderr)
        frame_id += 1
        if not args.loop:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())

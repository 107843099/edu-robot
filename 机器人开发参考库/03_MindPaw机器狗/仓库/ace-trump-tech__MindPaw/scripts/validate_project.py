#!/usr/bin/env python3
"""Validate the cross-domain files that make a MindPaw checkout reproducible."""

import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> None:
    manifest = ROOT / "hardware-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise SystemExit("hardware-manifest.json must use schema_version 1")
    for raw_path in data.get("required_paths", []):
        path = ROOT / raw_path
        if not path.exists():
            raise SystemExit(f"missing required project path: {raw_path}")

    platformio = (ROOT / "MindPaw_main/platformio.ini").read_text(encoding="utf-8")
    if "[env:nodemcuv2]" not in platformio or "framework = arduino" not in platformio:
        raise SystemExit("PlatformIO project is missing the expected ESP8266 environment")

    for env_file in [ROOT / "ai-infra/.env.example"]:
        if re.search(r"(?i)(api[_-]?key|token)\s*=\s*(sk-|ghp_|github_pat_|[A-Za-z0-9]{24,})", env_file.read_text(encoding="utf-8")):
            raise SystemExit(f"possible real secret in {env_file}")

    # 2.0: 感知层额外检查
    recon_pkg = ROOT / "ai-infra" / "recon"
    if not (recon_pkg / "__init__.py").exists():
        raise SystemExit("2.0 perception layer missing: ai-infra/recon/__init__.py")
    if not (recon_pkg / "service.py").exists():
        raise SystemExit("2.0 perception layer missing: ai-infra/recon/service.py")

    # ONNX 权重是可选的；不存在时 recon service 降级为 mock backbone，
    # 这是受支持的状态，只发警告不报错。
    weights_dir = recon_pkg / "weights"
    if not any(weights_dir.glob("*.onnx")):
        print("MindPaw 2.0 recon: no ONNX weights found — service will use mock backbone")

    print("MindPaw project manifest ok (2.0 recon layer present)")


if __name__ == "__main__":
    main()

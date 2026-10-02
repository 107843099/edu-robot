"""MindPaw 2.0 — streaming 3D reconstruction perception layer.

Reference: ABot-Recon (amap-cvlab) — streaming reconstruction with a 12-frame
local context KV cache, single-feedforward transformer, RGB-only input.

This package adds an *opt-in* parallel service to the existing ai-infra
gateway. The 1.0 gateway on port 8000 is untouched.
"""

APP_VERSION = "2.0.0-alpha"
SERVICE_NAME = "mindpaw-recon"
DEFAULT_PORT = 8001

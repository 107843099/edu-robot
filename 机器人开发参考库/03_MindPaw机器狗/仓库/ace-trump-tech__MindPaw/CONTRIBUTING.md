# Contributing to MindPaw

MindPaw is a physical robot project. Contributions must be reproducible on
real hardware or in a clearly identified simulation, and must preserve a safe
fallback when a sensor, network, or model fails.

## Before opening an Issue

Choose the most specific Issue Form and search existing reports first. Include
the board/module revision, firmware or Gateway commit, power supply, exact
commands or wiring, expected and observed results, and logs or measurements.
Never include API keys, Wi-Fi passwords, or personal data.

AI may assist with search, translation, or formatting, but AI-only or
unverifiable reports are not accepted. The author must personally reproduce the
problem and answer maintainer follow-up questions. Reports without evidence may
be labelled `needs-more-info` and closed after a reasonable response window.

## Pull requests

1. Keep a PR focused on firmware, hardware, documentation, 3D assets, or AI Infra.
2. Explain compatibility impact and the safe rollback or power-off procedure.
3. Do not commit `.env`, provider keys, build artifacts, or personal logs.
4. Update the affected beginner tutorial and `hardware-manifest.json` when paths change.
5. Run the checks below before submitting:

```bash
python3 scripts/validate_project.py
python3 -m compileall -q ai-infra MindPaw_main/tools
(cd ai-infra && python -m unittest discover -s tests -v)
(cd ai-infra && python -m unittest discover -s recon/tests -p 'test_pipeline.py' -v)
git diff --check
```

## Perception layer (2.0)

The `ai-infra/recon/` package adds a streaming 3D reconstruction service
(modeled after ABot-Recon, see [Docs/09_Streaming_Recon.md](Docs/09_Streaming_Recon.md)).
Contributions must keep the following guarantees:

1. **Mock fallback must never regress.** If a contributor changes
   `pipeline.py`, `backbone_student.py`, or `heads.py`, the service must
   still return valid hazard JSON when no ONNX weights are present.
   `python -m unittest discover -s recon/tests -p 'test_pipeline.py' -v`
   must pass with no ONNX checkpoint on disk.
2. **Device contract is bounded.** `schemas.py:HazardResponse` defines the
   only JSON shape the device consumes. New fields are OK; removing or
   weakening existing fields is not. Pydantic `field_validator`s are the
   safety net — keep them.
3. **No secrets in the repo.** Model weights, training data, and bearer
   tokens never belong in the tree. Pre-trained checkpoints live outside
   this repo and are pulled at deploy time (see `ai-infra/recon/README.md`).
4. **End-to-end smoke before opening a PR.** With `uvicorn
   recon.service:app --port 8001` running locally, the PR author must have
   successfully `POST /recon/frame`'d a JPEG and seen a hazard response.
5. **Latency claims must include the model variant.** When reporting FPS
   numbers in PRs or the docs, state which back-end ran (mock / CPU
   student / GPU student) and the host hardware.

For firmware changes, also run `pio run --project-dir MindPaw_main` when
PlatformIO is available. For motion or power changes, test with servos
disconnected first and include the measured voltage/current in the PR.

## Ownership boundaries

- `MindPaw_main/`: ESP8266 firmware and device protocol.
- `ai-infra/`: optional Gateway, provider adapters, and research experiments.
- `SCH&PCB/` and `3Dmodel/`: electrical and mechanical source files.
- `Docs/`: beginner reproduction, safety, and troubleshooting procedures.

See [`MAINTAINERS.md`](MAINTAINERS.md), [`SECURITY.md`](SECURITY.md), and
[`CONTENT-LICENSE.md`](CONTENT-LICENSE.md) for review and licensing boundaries.

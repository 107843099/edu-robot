# TurboQuant-H Sanitized Pipeline

This repository is a cleaned extraction of the TurboQuant-H calibration and fixed-bit quantization pipeline. It keeps the data and code needed to:

1. prepare or regenerate text, vision, and audio trajectories,
2. convert those trajectories into diagonal Hessian/statistics artifacts,
3. run fixed, pre-set TQH quantization levels.

Dynamic probe training, learned bit policies, eval sweeps, notebooks, logs, model checkpoints, and generated quantized model weights were intentionally left out.

## Layout

- `data/text/`
  - `pool*.jsonl`: WildChat prompt pools used to build text trajectories.
  - `trajectories_2x.jsonl`: generated text trajectories.
  - `test_fixed.jsonl`: fixed held-out text test split.
- `data/vision/`
  - `trajectories.jsonl` and `images/`: WildVision trajectories and associated images.
- `data/audio/`
  - `trajectories.jsonl` and `audios/`: audio trajectories and associated audio files.
- `data/hessians/`
  - `joint_av/`: diagonal Hessians/statistics from text + vision + audio calibration.
  - `vision/`: vision-only diagonal Hessians/statistics.
- `scripts/data/`: trajectory data prep/generation scripts.
- `scripts/calibration/`: trajectory-to-Hessian/statistics scripts.
- `scripts/quantization/`: fixed TQH quantization scripts.
- `src/turboquant/`: shared quantization and evaluation helpers.

## Model Location

Scripts default to `google/gemma-4-E2B-it`. To use a local model snapshot, set:

```bash
export TQH_MODEL_DIR=/path/to/gemma-4-E2B-it
```

or pass `--model-dir`.

## Typical Commands

Build local precursors from upstream datasets:

```bash
python scripts/data/download_precursors.py \
  --out-dir precursors \
  --text-prompts 2000 \
  --vision-samples 1500 \
  --audio-samples 1500
```

Then generate trajectories from those local precursors with any compatible model:

```bash
python scripts/data/generate_wildchat_trajectories.py \
  --precursor-dir precursors \
  --model-dir "$TQH_MODEL_DIR" \
  --output outputs/trajectories/text.jsonl
```

Generate multimodal trajectories:

```bash
python scripts/data/gen_vision_trajectories.py \
  --precursor-dir precursors \
  --model-dir "$TQH_MODEL_DIR" \
  --output-dir outputs/trajectories/vision

python scripts/data/gen_audio_trajectories.py \
  --precursor-dir precursors \
  --model-dir "$TQH_MODEL_DIR" \
  --output-dir outputs/trajectories/audio
```

The downloader streams from the upstream datasets directly. Users are
responsible for accepting and complying with upstream dataset access terms.

Build Hessian/statistics artifacts:

```bash
python scripts/calibration/calibrate_joint_av.py --model-dir "$TQH_MODEL_DIR"
python scripts/calibration/calibrate_vision_wildvision.py --model-dir "$TQH_MODEL_DIR"
```

Run fixed AV quantization:

```bash
python scripts/quantization/quantize_fixed_av.py \
  --model-dir "$TQH_MODEL_DIR" \
  --preset joint4_pli2_emb4
```

or specify the fixed levels directly:

```bash
python scripts/quantization/quantize_fixed_av.py \
  --model-dir "$TQH_MODEL_DIR" \
  --out-tag tqh_v4_a4_l4_pli2_emb4 \
  --vision-bits 4 \
  --audio-bits 4 \
  --bridge-bits 4 \
  --llm-bits 4 \
  --pli-bits 2 \
  --embed-bits 4
```

Run fixed text quantization configs:

```bash
python scripts/quantization/text_fixed_configs.py --model-dir "$TQH_MODEL_DIR"
```

## Notes

- `outputs/` is ignored and is the default destination for newly quantized models and result JSON.
- The included Hessian artifacts are compact diagonal statistics. Full Hessian tensors and checkpoint directories were excluded.
- The copied scripts no longer set a Hugging Face token. Use normal `huggingface-cli login` or `HF_TOKEN` in your shell if gated model access is required.

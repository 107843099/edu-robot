"""calibrate_vision_wildvision.py

Joint multimodal calibration using FP16-generated WildVision-Chat trajectories.
Replaces calibrate_vision_joint.py (which used cauldron prompts only).

For each trajectory:
  1. Re-build chat_template(image + prompt) to recover prompt input_ids + pixel_values.
  2. Concatenate completion_token_ids to input_ids.
  3. Forward; per-linear diag(H) accumulates over the FULL prompt+completion span.

Per-pass coverage: vision_tower runs once per trajectory; LLM runs over
prompt+completion+image-token positions. With 1500 trajectories at ~470
text tokens each, the LLM gets ~700K tokens of (response-included)
multimodal calibration — replacing the prior 262K WildChat text top-up.

Output: artifacts/vision_calib_wv/
  diag_hessians.safetensors
  metadata.json
  scale_token_ids.json
"""
from __future__ import annotations
import os

import argparse
import json
import time
from pathlib import Path

import torch
from PIL import Image as PILImage
from safetensors.torch import save_file
from transformers import Gemma4ForConditionalGeneration, AutoProcessor

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = os.environ.get("TQH_MODEL_DIR", "google/gemma-4-E2B-it")
TRAJ_PATH = REPO_ROOT / "data/vision/trajectories.jsonl"
IMG_BASE = REPO_ROOT / "data/vision"
OUT_DIR = REPO_ROOT / "data/hessians/vision"
DEVICE = "cuda"

LM_QUANT_SUFFIXES = (
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
    "per_layer_input_gate", "per_layer_projection",
)
BRIDGE_NAMES = ("model.embed_vision.embedding_projection",)


def is_target_linear(name: str) -> bool:
    if name.startswith("model.vision_tower."):
        return True
    if name in BRIDGE_NAMES:
        return True
    if name.startswith("model.language_model.layers."):
        last = name.rsplit(".", 1)[-1]
        if last in LM_QUANT_SUFFIXES:
            return True
        if last == "linear":
            return name.rsplit(".", 2)[-2] in LM_QUANT_SUFFIXES
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    p.add_argument("--traj-path", default=str(TRAJ_PATH))
    p.add_argument("--image-base", default=str(IMG_BASE))
    p.add_argument("--output-dir", default=str(OUT_DIR))
    p.add_argument("--n", type=int, default=0, help="0 = all trajectories")
    p.add_argument("--max-len", type=int, default=2048)
    args = p.parse_args()
    traj_path = Path(args.traj_path)
    image_base = Path(args.image_base)
    out_dir = Path(args.output_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Gemma-4-E2B-it from {args.model_dir}", flush=True)
    t0 = time.perf_counter()
    model = Gemma4ForConditionalGeneration.from_pretrained(
        args.model_dir, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True,
    ).to(DEVICE).eval()
    processor = AutoProcessor.from_pretrained(args.model_dir)
    print(f"  loaded in {time.perf_counter()-t0:.0f}s", flush=True)

    targets = []
    for name, mod in model.named_modules():
        if isinstance(mod, torch.nn.Linear) and is_target_linear(name):
            targets.append((name, mod))
    vision_n = sum(1 for n, _ in targets if n.startswith("model.vision_tower."))
    bridge_n = sum(1 for n, _ in targets if n in BRIDGE_NAMES)
    lm_n = sum(1 for n, _ in targets if n.startswith("model.language_model."))
    print(f"  hooking {len(targets)} linears: vision={vision_n}, bridge={bridge_n}, llm={lm_n}",
          flush=True)

    diag = {n: torch.zeros(m.in_features, dtype=torch.float32, device=DEVICE)
            for n, m in targets}
    n_samp = {n: 0 for n, _ in targets}

    def make_hook(name):
        def pre_hook(_mod, args):
            x = args[0].detach()
            if x.dim() > 2:
                x = x.reshape(-1, x.shape[-1])
            diag[name].add_(x.float().pow(2).sum(0))
            n_samp[name] += x.shape[0]
        return pre_hook
    handles = [m.register_forward_pre_hook(make_hook(n)) for n, m in targets]

    vision_first = next((n for n, _ in targets if n.startswith("model.vision_tower.")), None)
    lm_first = next((n for n, _ in targets if n.startswith("model.language_model.layers.0.")), None)

    # Load trajectories
    rows = []
    with open(traj_path) as f:
        for line in f:
            if not line.strip(): continue
            rows.append(json.loads(line))
    if args.n > 0:
        rows = rows[:args.n]
    print(f"\nProcessing {len(rows)} WildVision trajectories", flush=True)

    n_done = 0
    n_skip = 0
    all_token_ids = []  # for scale_token_ids.json
    t0 = time.perf_counter()

    for i, r in enumerate(rows):
        try:
            img_path = image_base / r["image_path"]
            if not img_path.exists():
                n_skip += 1; continue
            img = PILImage.open(img_path).convert("RGB")
            user_text = r["prompt_text"]
            completion_ids = r["completion_token_ids"]
            if not completion_ids:
                n_skip += 1; continue

            messages = [[{
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text",  "text": user_text},
                ],
            }]]
            inputs = processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            )
            prompt_ids = inputs["input_ids"]
            comp = torch.tensor([completion_ids], dtype=prompt_ids.dtype)
            full_ids = torch.cat([prompt_ids, comp], dim=1)
            if full_ids.shape[1] > args.max_len:
                n_skip += 1; continue

            inputs["input_ids"] = full_ids
            if "attention_mask" in inputs:
                inputs["attention_mask"] = torch.ones_like(full_ids)
            inputs = {k: v.to(DEVICE) if hasattr(v, "to") else v for k, v in inputs.items()}

            with torch.no_grad():
                model(**inputs)
            n_done += 1

            # Collect token IDs for fit_row_table_scale (PLI/embed quant)
            if len(all_token_ids) < 32768:
                all_token_ids.extend(full_ids[0].tolist())

            if (n_done % 50) == 0 or n_done == 1:
                elapsed = time.perf_counter() - t0
                rate = n_done / max(elapsed, 1e-6)
                print(f"  [{n_done}/{len(rows)}] {elapsed:.0f}s ({rate:.2f}/s)  "
                      f"vision_first n={n_samp[vision_first]:,}  "
                      f"lm_first n={n_samp[lm_first]:,}  skip={n_skip}", flush=True)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            n_skip += 1
        except Exception as e:
            n_skip += 1
            print(f"  err @ {i}: {type(e).__name__}: {str(e)[:80]}", flush=True)

    elapsed = time.perf_counter() - t0
    print(f"\nDone: {n_done} trajectories in {elapsed:.0f}s ({n_skip} skipped)", flush=True)

    for h in handles: h.remove()

    print("\nNormalizing and saving diag(H)...", flush=True)
    save_dict = {}
    for name, _ in targets:
        ns = n_samp[name]
        if ns == 0:
            print(f"  WARN {name} got 0 samples", flush=True); continue
        save_dict[f"{name}.diagH"] = (diag[name] / ns).cpu()
    out_path = out_dir / "diag_hessians.safetensors"
    save_file(save_dict, str(out_path))
    sz = out_path.stat().st_size / 1e6
    print(f"  saved {out_path} ({sz:.2f} MB)", flush=True)

    metadata = {
        "source": "WildVision/wildvision-chat trajectories (FP16 self-generated)",
        "trajectory_path": str(traj_path),
        "n_trajectories":  n_done,
        "n_skipped":       n_skip,
        "n_samples_per_layer": n_samp,
        "vision_first_n":  n_samp[vision_first],
        "lm_first_n":      n_samp[lm_first],
        "n_targets":       len(targets),
        "model":           args.model_dir,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (out_dir / "scale_token_ids.json").write_text(json.dumps(all_token_ids[:32768]))
    print(f"  saved metadata.json + scale_token_ids.json (n_ids={len(all_token_ids[:32768])})",
          flush=True)


if __name__ == "__main__":
    main()

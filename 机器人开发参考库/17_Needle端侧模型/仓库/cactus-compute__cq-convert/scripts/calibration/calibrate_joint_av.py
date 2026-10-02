"""calibrate_joint_av.py

Unified joint audio + vision + text calibration. Hooks every quantizable
linear (vision_tower + bridge_v + audio_tower + bridge_a + LLM transformer)
and forwards three trajectory streams through the model:

  1. Audio trajectories       (artifacts/audio_calibration/trajectories.jsonl)
  2. Vision trajectories      (artifacts/wildvision_calibration/trajectories.jsonl)
  3. Text trajectories        (artifacts/wildchat_calibration/trajectories_2x.jsonl)

For each trajectory, forwards prompt+completion teacher-forced. Per-linear
diag(H) = E[x²] is accumulated across all three streams; the LLM transformer
sees a mix of all three modalities, while modality-specific towers see only
their own data (audio_tower active only on audio fwd, etc.).

Output: artifacts/joint_av_calib/
  diag_hessians.safetensors  one (K,) fp32 vector per linear
  metadata.json              per-layer n_samples + per-source counts
  scale_token_ids.json       a sample of token ids flowing through the LLM
"""
from __future__ import annotations
import os

import argparse
import io
import json
import time
from pathlib import Path

import numpy as np
import torch
import soundfile as sf
from PIL import Image as PILImage
from safetensors.torch import save_file
from transformers import Gemma4ForConditionalGeneration, AutoProcessor

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = os.environ.get("TQH_MODEL_DIR", "google/gemma-4-E2B-it")

WC_TRAJ      = REPO_ROOT / "data/text/trajectories_2x.jsonl"
WV_TRAJ      = REPO_ROOT / "data/vision/trajectories.jsonl"
WV_IMG_BASE  = REPO_ROOT / "data/vision"
AUDIO_TRAJ   = REPO_ROOT / "data/audio/trajectories.jsonl"
AUDIO_BASE   = REPO_ROOT / "data/audio"
OUT_DIR      = REPO_ROOT / "data/hessians/joint_av"
DEVICE       = "cuda"
TARGET_SR    = 16000

LM_QUANT_SUFFIXES = (
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
    "per_layer_input_gate", "per_layer_projection",
)


BRIDGE_NAMES = (
    "model.embed_vision.embedding_projection",
    "model.embed_audio.embedding_projection",   # audio bridge (was missed in pre-§48 runs)
)
LM_EXTRA_NAMES = (
    "model.language_model.per_layer_model_projection",  # was missed in pre-§48 runs
)


def is_target(name: str) -> bool:
    if name.startswith("model.vision_tower."): return True
    if name.startswith("model.audio_tower."):  return True
    if name in BRIDGE_NAMES: return True
    if name in LM_EXTRA_NAMES: return True
    if name.startswith("model.language_model.layers."):
        last = name.rsplit(".", 1)[-1]
        if last in LM_QUANT_SUFFIXES: return True
        if last == "linear":
            return name.rsplit(".", 2)[-2] in LM_QUANT_SUFFIXES
    return False


def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line: rows.append(json.loads(line))
    return rows


def to_mono_16k(arr: np.ndarray, sr: int) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float32)
    if arr.ndim > 1:
        arr = arr.mean(axis=tuple(range(arr.ndim - 1))) if arr.shape[-1] != 1 else arr.squeeze(-1)
    if sr != TARGET_SR:
        import scipy.signal as sps
        n = int(round(len(arr) * TARGET_SR / sr))
        arr = sps.resample(arr, n).astype(np.float32)
    return arr


def truncate_audio(arr: np.ndarray, max_seconds: float) -> np.ndarray:
    return arr[: int(max_seconds * TARGET_SR)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    p.add_argument("--text-traj", default=str(WC_TRAJ))
    p.add_argument("--vision-traj", default=str(WV_TRAJ))
    p.add_argument("--vision-base", default=str(WV_IMG_BASE))
    p.add_argument("--audio-traj", default=str(AUDIO_TRAJ))
    p.add_argument("--audio-base", default=str(AUDIO_BASE))
    p.add_argument("--output-dir", default=str(OUT_DIR))
    p.add_argument("--n-text",   type=int, default=128,
                   help="number of WildChat trajectories")
    p.add_argument("--n-vision", type=int, default=1500,
                   help="number of WildVision trajectories (cap)")
    p.add_argument("--n-audio",  type=int, default=1300,
                   help="number of audio trajectories (cap; reserve last 200 as test)")
    p.add_argument("--max-len-text",  type=int, default=2048)
    p.add_argument("--max-len-mm",    type=int, default=4096)
    p.add_argument("--max-audio-s",   type=float, default=30.0)
    args = p.parse_args()
    out_dir = Path(args.output_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Loading model from {args.model_dir}", flush=True)
    t0 = time.perf_counter()
    model = Gemma4ForConditionalGeneration.from_pretrained(
        args.model_dir, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True,
    ).to(DEVICE).eval()
    processor = AutoProcessor.from_pretrained(args.model_dir)
    print(f"  loaded in {time.perf_counter()-t0:.0f}s", flush=True)

    targets = []
    for name, mod in model.named_modules():
        if isinstance(mod, torch.nn.Linear) and is_target(name):
            targets.append((name, mod))
    by_kind = {"vision": 0, "audio": 0, "bridge": 0, "lm": 0}
    for n, _ in targets:
        if n.startswith("model.vision_tower."):       by_kind["vision"] += 1
        elif n.startswith("model.audio_tower."):     by_kind["audio"]  += 1
        elif "embed_vision" in n:                    by_kind["bridge"] += 1
        elif n.startswith("model.language_model."):  by_kind["lm"]     += 1
    print(f"  hooking {len(targets)} linears: {by_kind}", flush=True)

    diag = {n: torch.zeros(m.in_features, dtype=torch.float32, device=DEVICE)
            for n, m in targets}
    n_samp = {n: 0 for n, _ in targets}
    src_samp = {src: {n: 0 for n, _ in targets}
                for src in ("text", "vision", "audio")}
    cur_source = {"name": "text"}

    def make_hook(name):
        def pre_hook(_mod, args):
            x = args[0].detach()
            if x.dim() > 2:
                x = x.reshape(-1, x.shape[-1])
            diag[name].add_(x.float().pow(2).sum(0))
            n = x.shape[0]
            n_samp[name] += n
            src_samp[cur_source["name"]][name] += n
        return pre_hook
    handles = [m.register_forward_pre_hook(make_hook(n)) for n, m in targets]

    vision_first = next((n for n, _ in targets if n.startswith("model.vision_tower.")), None)
    audio_first  = next((n for n, _ in targets if n.startswith("model.audio_tower.")), None)
    lm_first     = next((n for n, _ in targets if n.startswith("model.language_model.layers.0.")), None)

    all_token_ids = []  # for scale_token_ids.json (sampled)

    # ── Stage A: text-only (WildChat) ───────────────────────────────────────
    print(f"\n=== Stage A: text trajectories (WildChat, n={args.n_text}) ===", flush=True)
    cur_source["name"] = "text"
    text_rows = load_jsonl(Path(args.text_traj))[:args.n_text]
    t0 = time.perf_counter()
    n_text_done = 0
    for i, r in enumerate(text_rows):
        prompt_ids = r.get("prompt_token_ids") or []
        comp_ids = r.get("completion_token_ids") or []
        if not prompt_ids or not comp_ids: continue
        full = prompt_ids + comp_ids
        if len(full) > args.max_len_text:
            full = full[:args.max_len_text]
        try:
            ids = torch.tensor([full], dtype=torch.long, device=DEVICE)
            with torch.no_grad():
                model(input_ids=ids)
            n_text_done += 1
            if len(all_token_ids) < 32768:
                all_token_ids.extend(full[:512])
            if (n_text_done % 20) == 0:
                el = time.perf_counter() - t0
                print(f"  [{n_text_done}/{len(text_rows)}] {el:.0f}s  "
                      f"lm_first n={n_samp[lm_first]:,}", flush=True)
        except Exception as e:
            print(f"  text {i} fail: {type(e).__name__}: {str(e)[:80]}", flush=True)
    print(f"Stage A done: {n_text_done} text trajectories in "
          f"{time.perf_counter()-t0:.0f}s. lm_first n={n_samp[lm_first]:,}", flush=True)

    # ── Stage B: vision+text (WildVision) ───────────────────────────────────
    print(f"\n=== Stage B: vision trajectories (WildVision, n≤{args.n_vision}) ===",
          flush=True)
    cur_source["name"] = "vision"
    wv_rows = load_jsonl(Path(args.vision_traj))[:args.n_vision]
    vision_base = Path(args.vision_base)
    t0 = time.perf_counter()
    n_v_done = 0; n_v_skip = 0
    for i, r in enumerate(wv_rows):
        try:
            img_path = vision_base / r["image_path"]
            if not img_path.exists():
                n_v_skip += 1; continue
            img = PILImage.open(img_path).convert("RGB")
            user_text = r["prompt_text"]
            comp_ids = r["completion_token_ids"]
            if not comp_ids: n_v_skip += 1; continue
            messages = [[{"role": "user", "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": user_text},
            ]}]]
            inputs = processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            )
            prompt_ids = inputs["input_ids"]
            comp = torch.tensor([comp_ids], dtype=prompt_ids.dtype)
            full_ids = torch.cat([prompt_ids, comp], dim=1)
            if full_ids.shape[1] > args.max_len_mm:
                n_v_skip += 1; continue
            inputs["input_ids"] = full_ids
            if "attention_mask" in inputs:
                inputs["attention_mask"] = torch.ones_like(full_ids)
            inputs = {k: v.to(DEVICE) if hasattr(v, "to") else v for k, v in inputs.items()}
            with torch.no_grad():
                model(**inputs)
            n_v_done += 1
            if (n_v_done % 50) == 0:
                el = time.perf_counter() - t0
                print(f"  [{n_v_done}/{len(wv_rows)}] {el:.0f}s  "
                      f"vision_first n={n_samp[vision_first]:,}  "
                      f"lm_first n={n_samp[lm_first]:,}  skip={n_v_skip}", flush=True)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache(); n_v_skip += 1
        except Exception as e:
            n_v_skip += 1
            if n_v_skip < 5:
                print(f"  vision {i} fail: {type(e).__name__}: {str(e)[:80]}", flush=True)
    print(f"Stage B done: {n_v_done} vision trajectories in "
          f"{time.perf_counter()-t0:.0f}s. vision_first n={n_samp[vision_first]:,}, "
          f"lm n={n_samp[lm_first]:,}, skip={n_v_skip}", flush=True)

    # ── Stage C: audio+text (audio_calibration) ─────────────────────────────
    print(f"\n=== Stage C: audio trajectories (audio_calib, n≤{args.n_audio}) ===",
          flush=True)
    cur_source["name"] = "audio"
    audio_rows = load_jsonl(Path(args.audio_traj))[:args.n_audio]
    audio_base = Path(args.audio_base)
    t0 = time.perf_counter()
    n_a_done = 0; n_a_skip = 0
    for i, r in enumerate(audio_rows):
        try:
            audio_path = audio_base / r["audio_path"]
            if not audio_path.exists():
                n_a_skip += 1; continue
            arr, sr = sf.read(audio_path)
            if arr.ndim > 1: arr = arr.mean(axis=-1)
            audio = truncate_audio(to_mono_16k(arr.astype(np.float32), sr),
                                    max_seconds=args.max_audio_s)
            if len(audio) < 16000 * 0.3: n_a_skip += 1; continue
            prompt_text = r["prompt_text"]
            comp_ids = r["completion_token_ids"]
            if not comp_ids: n_a_skip += 1; continue
            messages = [[{"role": "user", "content": [
                {"type": "audio", "audio": audio},
                {"type": "text",  "text": prompt_text},
            ]}]]
            inputs = processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            )
            prompt_ids = inputs["input_ids"]
            comp = torch.tensor([comp_ids], dtype=prompt_ids.dtype)
            full_ids = torch.cat([prompt_ids, comp], dim=1)
            if full_ids.shape[1] > args.max_len_mm:
                n_a_skip += 1; continue
            inputs["input_ids"] = full_ids
            if "attention_mask" in inputs:
                inputs["attention_mask"] = torch.ones_like(full_ids)
            inputs = {k: v.to(DEVICE) if hasattr(v, "to") else v for k, v in inputs.items()}
            with torch.no_grad():
                model(**inputs)
            n_a_done += 1
            if (n_a_done % 50) == 0:
                el = time.perf_counter() - t0
                print(f"  [{n_a_done}/{len(audio_rows)}] {el:.0f}s  "
                      f"audio_first n={n_samp[audio_first]:,}  "
                      f"lm_first n={n_samp[lm_first]:,}  skip={n_a_skip}", flush=True)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache(); n_a_skip += 1
        except Exception as e:
            n_a_skip += 1
            if n_a_skip < 5:
                print(f"  audio {i} fail: {type(e).__name__}: {str(e)[:80]}", flush=True)
    print(f"Stage C done: {n_a_done} audio trajectories in "
          f"{time.perf_counter()-t0:.0f}s. audio_first n={n_samp[audio_first]:,}, "
          f"lm n={n_samp[lm_first]:,}, skip={n_a_skip}", flush=True)

    for h in handles: h.remove()

    # ── Save diag(H) ────────────────────────────────────────────────────────
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
        "model":           args.model_dir,
        "n_text":          n_text_done,
        "n_vision":        n_v_done,
        "n_audio":         n_a_done,
        "n_targets":       len(targets),
        "n_samples_per_layer":      n_samp,
        "n_samples_per_layer_text": src_samp["text"],
        "n_samples_per_layer_vision": src_samp["vision"],
        "n_samples_per_layer_audio":  src_samp["audio"],
        "vision_first_n":  n_samp[vision_first] if vision_first else 0,
        "audio_first_n":   n_samp[audio_first]  if audio_first  else 0,
        "lm_first_n":      n_samp[lm_first]     if lm_first     else 0,
        "by_kind":         by_kind,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (out_dir / "scale_token_ids.json").write_text(json.dumps(all_token_ids[:32768]))
    print(f"  saved metadata.json + scale_token_ids.json (n_ids={len(all_token_ids[:32768])})",
          flush=True)


if __name__ == "__main__":
    main()

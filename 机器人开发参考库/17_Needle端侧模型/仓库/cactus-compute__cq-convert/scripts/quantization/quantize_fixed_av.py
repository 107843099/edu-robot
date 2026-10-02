"""quantize_av.py

Universal joint audio + vision + LLM TQH quantization. Generalizes
quantize_vision_joint.py by adding --audio-bits. Used to build any
config in the {text, vision, audio} × {16, 4, 3, 2, P3, P6} sweep.

Recipe:
  vision_tower (113)            TQH at --vision-bits  (16 = leave bf16)
  audio_tower (134)             TQH at --audio-bits   (16 = leave bf16)
  embed_vision.bridge (1)       TQH at --bridge-bits  (16 = leave bf16)
  LLM transformer (275)         TQH at --llm-bits     (16 = leave bf16)
  PLI (embed_tokens_per_layer)  TQH at --pli-bits     (16 = leave bf16)
  embed_tokens                  TQH at --embed-bits   (16 = leave bf16)

Default calibration: artifacts/joint_av_calib/
Output:              artifacts/quantized_av/<tag>/
"""
from __future__ import annotations
import argparse, gc, json, shutil, time
import os
from pathlib import Path
import sys

import torch
from safetensors import safe_open
from transformers import Gemma4ForConditionalGeneration

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src/turboquant"))
sys.path.insert(0, str(REPO_ROOT / "scripts/quantization"))

from gemma_turboquant import SharedTransformBank
from text_fixed_configs import gpu_stage1_quant, fit_row_table_scale, ALPHA

DEFAULT_MODEL_DIR = os.environ.get("TQH_MODEL_DIR", "google/gemma-4-E2B-it")
DEVICE = "cuda"
DTYPE = torch.bfloat16
DEFAULT_CALIB_DIR = REPO_ROOT / "data/hessians/joint_av"

LM_QUANT_SUFFIXES = (
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
    "per_layer_input_gate", "per_layer_projection",
)
BRIDGE_NAMES = (
    "model.embed_vision.embedding_projection",
    "model.embed_audio.embedding_projection",  # audio bridge analog (caught in patched runs)
)
LM_EXTRA_NAMES = (
    # LLM-side projections that sit outside layers.* but should be quantized.
    "model.language_model.per_layer_model_projection",
)

PRESETS = {
    "llm4_pli2_emb4": {
        "vision_bits": 16, "audio_bits": 16, "bridge_bits": 16,
        "llm_bits": 4, "pli_bits": 2, "embed_bits": 4,
    },
    "vision4_llm4_pli2_emb4": {
        "vision_bits": 4, "audio_bits": 16, "bridge_bits": 4,
        "llm_bits": 4, "pli_bits": 2, "embed_bits": 4,
    },
    "audio4_llm4_pli2_emb4": {
        "vision_bits": 16, "audio_bits": 4, "bridge_bits": 4,
        "llm_bits": 4, "pli_bits": 2, "embed_bits": 4,
    },
    "joint4_pli2_emb4": {
        "vision_bits": 4, "audio_bits": 4, "bridge_bits": 4,
        "llm_bits": 4, "pli_bits": 2, "embed_bits": 4,
    },
    "audio2_llm4_pli2_emb4": {
        "vision_bits": 16, "audio_bits": 2, "bridge_bits": 4,
        "llm_bits": 4, "pli_bits": 2, "embed_bits": 4,
    },
    "vision2_llm4_pli2_emb4": {
        "vision_bits": 2, "audio_bits": 16, "bridge_bits": 4,
        "llm_bits": 4, "pli_bits": 2, "embed_bits": 4,
    },
}


def is_vision(name): return name.startswith("model.vision_tower.")
def is_audio(name):  return name.startswith("model.audio_tower.")
def is_bridge(name): return name in BRIDGE_NAMES
def is_lm(name):
    if name in LM_EXTRA_NAMES: return True
    if not name.startswith("model.language_model.layers."): return False
    last = name.rsplit(".", 1)[-1]
    if last in LM_QUANT_SUFFIXES: return True
    if last == "linear":
        return name.rsplit(".", 2)[-2] in LM_QUANT_SUFFIXES
    return False


def input_scale_from_diag(diag, w):
    x_abs = diag.float().clamp_min(1e-12).sqrt().clamp_min(1e-6)
    w_abs = w.float().abs().mean(0).clamp_min(1e-6)
    raw = x_abs.pow(ALPHA) / w_abs.pow(1.0 - ALPHA)
    raw = raw / torch.exp(torch.log(raw.clamp_min(1e-6)).mean())
    return raw.clamp(1.0 / 8.0, 8.0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preset", choices=sorted(PRESETS),
                   help="fixed bit preset; explicit bit flags override preset values")
    p.add_argument("--vision-bits", type=int, default=16,
                   help="bits for vision_tower; 16 = leave bf16")
    p.add_argument("--audio-bits",  type=int, default=16,
                   help="bits for audio_tower; 16 = leave bf16")
    p.add_argument("--bridge-bits", type=int, default=4)
    p.add_argument("--llm-bits",    type=int, default=4,
                   help="fixed bits for LLM transformer; 16 = leave bf16")
    p.add_argument("--pli-bits",    type=int, default=2,
                   help="bits for PLI; 16 = leave bf16")
    p.add_argument("--embed-bits",  type=int, default=4,
                   help="bits for embed_tokens; 16 = leave bf16")
    p.add_argument("--out-tag",     default=None)
    p.add_argument("--model-dir",   default=DEFAULT_MODEL_DIR)
    p.add_argument("--calib-dir",   default=str(DEFAULT_CALIB_DIR))
    p.add_argument("--out-base",    default="outputs/quantized_av")
    args = p.parse_args()
    if args.preset:
        for key, value in PRESETS[args.preset].items():
            cli_name = "--" + key.replace("_", "-")
            if cli_name not in sys.argv:
                setattr(args, key, value)
        if "--out-tag" not in sys.argv:
            args.out_tag = args.preset
    if not args.out_tag:
        p.error("--out-tag is required when --preset is not set")

    DIAG_PATH = Path(args.calib_dir) / "diag_hessians.safetensors"
    TOKIDS = Path(args.calib_dir) / "scale_token_ids.json"
    OUT_DIR = REPO_ROOT / args.out_base / args.out_tag
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[{args.out_tag}] vision={args.vision_bits} audio={args.audio_bits} "
          f"bridge={args.bridge_bits} llm={args.llm_bits} "
          f"pli={args.pli_bits} embed={args.embed_bits}", flush=True)
    print(f"  calib_dir={args.calib_dir}", flush=True)

    print(f"\nLoading model...", flush=True)
    t0 = time.perf_counter()
    model = Gemma4ForConditionalGeneration.from_pretrained(
        args.model_dir, torch_dtype=DTYPE, low_cpu_mem_usage=True,
    ).to(DEVICE).eval()
    print(f"  loaded in {time.perf_counter()-t0:.0f}s", flush=True)

    # Build the linear-quant target list
    targets = []
    for name, mod in model.named_modules():
        if not isinstance(mod, torch.nn.Linear): continue
        if is_vision(name) and args.vision_bits < 16:
            targets.append((name, mod, args.vision_bits))
        elif is_audio(name) and args.audio_bits < 16:
            targets.append((name, mod, args.audio_bits))
        elif is_bridge(name) and args.bridge_bits < 16:
            targets.append((name, mod, args.bridge_bits))
        elif is_lm(name):
            if args.llm_bits < 16:
                targets.append((name, mod, args.llm_bits))
    n_v = sum(1 for n, _, _ in targets if is_vision(n))
    n_a = sum(1 for n, _, _ in targets if is_audio(n))
    n_b = sum(1 for n, _, _ in targets if is_bridge(n))
    n_l = sum(1 for n, _, _ in targets if is_lm(n))
    print(f"  target linears: {len(targets)}  (vision={n_v}, audio={n_a}, bridge={n_b}, lm={n_l})",
          flush=True)

    # Pull diag(H) for each target
    diag_by_name = {}
    if targets:
        with safe_open(str(DIAG_PATH), framework="pt") as f:
            keys = set(f.keys())
            for name, _, _ in targets:
                key = f"{name}.diagH"
                diag_by_name[name] = f.get_tensor(key) if key in keys else None
                if diag_by_name[name] is None:
                    print(f"  WARN no diagH for {name}", flush=True)

    bank = SharedTransformBank(seed=1234)

    if targets:
        print(f"\nQuantizing {len(targets)} linears...", flush=True)
        t_q = time.perf_counter()
        sum_b, n = 0.0, 0
        for i, (name, module, bits) in enumerate(targets):
            diag = diag_by_name[name]
            w = module.weight.detach().float().cpu()
            iscale = input_scale_from_diag(diag, w) if diag is not None else None
            recon, ab = gpu_stage1_quant(
                w, bits=bits, transform_bank=bank,
                group_size=128, rotation_family="hadamard",
                input_scale=iscale, device=DEVICE, batch=min(w.shape[0], 256),
            )
            with torch.no_grad():
                module.weight.data.copy_(recon.to(DTYPE).to(DEVICE))
            sum_b += ab; n += 1
            del w, recon
            if i % 64 == 0 or i == len(targets) - 1:
                print(f"  [{i+1:3d}/{len(targets)}] {name} bits={bits} "
                      f"({time.perf_counter()-t_q:.0f}s)", flush=True)
        print(f"\nLinears done. avg_bits={sum_b/max(1,n):.3f}", flush=True)
        gc.collect(); torch.cuda.empty_cache()

    lm = model.model.language_model
    pli_ref = lm.embed_tokens_per_layer
    embed_ref = lm.embed_tokens
    scale_ids = json.loads(TOKIDS.read_text()) if TOKIDS.exists() else []

    if args.pli_bits < 16:
        print(f"\nQuantizing PLI ({args.pli_bits}-bit)...", flush=True)
        pli_fp32 = pli_ref.weight.detach().float().cpu().contiguous()
        pli_scale = fit_row_table_scale(pli_fp32, scale_ids) if scale_ids else None
        pli_q, pli_b = gpu_stage1_quant(pli_fp32, bits=args.pli_bits, transform_bank=bank,
                                         group_size=128, rotation_family="hadamard",
                                         input_scale=pli_scale, device=DEVICE, batch=512)
        with torch.no_grad():
            pli_ref.weight.data.copy_(pli_q.to(DTYPE).to(DEVICE))
        print(f"  PLI bits={pli_b:.3f}", flush=True)
        del pli_fp32, pli_q, pli_scale
        gc.collect(); torch.cuda.empty_cache()

    if args.embed_bits < 16:
        print(f"\nQuantizing embed ({args.embed_bits}-bit, gs=K, orthogonal)...", flush=True)
        embed_fp32 = embed_ref.weight.detach().float().cpu().contiguous()
        embed_scale = fit_row_table_scale(embed_fp32, scale_ids) if scale_ids else None
        embed_q, embed_b = gpu_stage1_quant(embed_fp32, bits=args.embed_bits, transform_bank=bank,
                                             group_size=None, rotation_family="orthogonal",
                                             input_scale=embed_scale, device=DEVICE, batch=2048)
        embed_ptr = embed_ref.weight.data_ptr()
        with torch.no_grad():
            embed_ref.weight.data.copy_(embed_q.to(DTYPE).to(DEVICE))
            if hasattr(model, "lm_head") and model.lm_head.weight.data_ptr() != embed_ptr:
                model.lm_head.weight.data.copy_(embed_q.to(DTYPE).to(DEVICE))
        print(f"  embed bits={embed_b:.3f}", flush=True)
        del embed_fp32, embed_q, embed_scale
    gc.collect(); torch.cuda.empty_cache()

    print(f"\nSaving {OUT_DIR}...", flush=True)
    # break shared-storage tying so vLLM-style strict loaders work too
    with torch.no_grad():
        for _, param in model.named_parameters():
            param.data = param.data.clone().contiguous()
    model.save_pretrained(str(OUT_DIR), safe_serialization=True)
    for fname in ("tokenizer.json", "tokenizer_config.json",
                  "chat_template.jinja", "processor_config.json",
                  "preprocessor_config.json", "special_tokens_map.json"):
        src = Path(args.model_dir) / fname
        if src.exists():
            shutil.copy2(src, OUT_DIR / fname)
    print(f"Done.", flush=True)


if __name__ == "__main__":
    main()

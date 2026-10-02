"""run_three_configs.py

Evaluate quantization configs on WildChat trajectory data:
  1. pli2_emb3_q2k2up2_rest4   — PLI=2bit, embed=3bit, q/k/up_proj=2bit, rest=4bit
  2. pli2_emb3_uniform3        — PLI=2bit, embed=3bit, all transformer linears=3bit
  3. pli2_emb3_first15_4_rest3 — PLI=2bit, embed=3bit, layers 0-14=4bit, 15-34=3bit
  4. pli2_emb3_uniform4        — PLI=2bit, embed=3bit, all transformer linears=4bit
  5. pli2_emb3_bot10_3_rest4   — PLI=2bit, embed=3bit, 10 cheapest layers=3bit, rest=4bit

Calibration / test split:
  test_rows  = last N_TEST rows  (~1M completion tokens)
  calib_rows = all earlier rows

Quantization: GPU-accelerated stage-1 VQ (no GPTQ, alpha=0.25 fixed).
  transformer linears: group_size=128, hadamard
  PLI:                 group_size=128, hadamard
  embed_tokens:        group_size=None (row-as-group), orthogonal
"""
from __future__ import annotations

import gc
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
from transformers import Gemma4ForConditionalGeneration

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src/turboquant"))

from eval_ppl import completion_nll
from gemma_turboquant import (
    SharedTransformBank,
    capture_linear_inputs,
    normalize_rotation_family,
)

MODEL_DIR     = os.environ.get("TQH_MODEL_DIR", "google/gemma-4-E2B-it")
TRAJ_PATH     = str(REPO_ROOT / "data/text/trajectories_2x.jsonl")
OUT_PATH      = REPO_ROOT / "outputs/text_fixed_configs.json"

N_TEST        = 2500    # held-out test rows (last in file)
N_CALIB_ACT   = 2048    # tokens for activation capture → per-linear input scales
N_CALIB_SCALE = 32768   # tokens for PLI/embed scale fitting
MAX_LEN       = 1024    # max sequence length for PPL eval
ALPHA         = 0.25    # activation-aware scale exponent
GPU_BATCH     = 2048    # rows per GPU quantization batch

CONFIGS = [
    "pli2_emb3_q2k2up2_rest4",
    "pli2_emb3_uniform3",
    "pli2_emb3_first15_4_rest3",
    "pli2_emb3_uniform4",
    "pli2_emb3_bot10_3_rest4",
    "pli2_emb3_bot5_3_rest4",
    "pli2_emb3_bot20_3_rest4",
    "pli2_emb3_kl015_3_rest4",
    "pli2_emb3_bot3_2bit_rest4",
    # embed_tokens with group_size=128 hadamard (same as linears/PLI)
    "pli2_emb3h_uniform4",
    "pli2_emb3h_bot5_3_rest4",
]
Q2K2UP2_PROJ = {"q_proj", "k_proj", "up_proj"}
# Layers ranked by ascending 3-bit KL-div (measure_layer_sensitivity.py)
BOT3_LAYERS  = {31, 30, 32}
BOT5_LAYERS  = {31, 30, 32, 27, 28}
BOT10_LAYERS = {31, 30, 32, 27, 28, 26, 17, 33, 21, 18}
BOT20_LAYERS = {31, 30, 32, 27, 28, 26, 17, 33, 21, 18, 25, 16, 20, 22, 29, 15, 23, 14, 11, 10}
# Layers with KL < 0.015 at 3-bit
KL015_LAYERS = {17, 18, 21, 25, 26, 27, 28, 30, 31, 32, 33}


def embed_quant_params(config: str) -> tuple[int, str]:
    """Return (group_size_or_None, rotation_family) for embed_tokens."""
    if "_emb3h_" in config:
        return 128, "hadamard"   # same setup as transformer linears
    return None, "orthogonal"    # default: full row as one group


# ── Policy ────────────────────────────────────────────────────────────────────

def bits_for_linear(config: str, layer_idx: int, proj_name: str) -> int:
    # emb3h variants share the same linear policy as their emb3 counterparts
    config = config.replace("_emb3h_", "_emb3_")
    if config == "pli2_emb3_q2k2up2_rest4":
        return 2 if proj_name in Q2K2UP2_PROJ else 4
    if config == "pli2_emb3_uniform3":
        return 3
    if config == "pli2_emb3_first15_4_rest3":
        return 4 if layer_idx < 15 else 3
    if config == "pli2_emb3_uniform4":
        return 4
    if config == "pli2_emb3_bot10_3_rest4":
        return 3 if layer_idx in BOT10_LAYERS else 4
    if config == "pli2_emb3_bot5_3_rest4":
        return 3 if layer_idx in BOT5_LAYERS else 4
    if config == "pli2_emb3_bot20_3_rest4":
        return 3 if layer_idx in BOT20_LAYERS else 4
    if config == "pli2_emb3_kl015_3_rest4":
        return 3 if layer_idx in KL015_LAYERS else 4
    if config == "pli2_emb3_bot3_2bit_rest4":
        return 2 if layer_idx in BOT3_LAYERS else 4
    raise ValueError(f"Unknown config: {config}")


# ── Data helpers ──────────────────────────────────────────────────────────────

def load_all_trajectories(path: str, min_prompt: int = 4, min_comp: int = 16) -> list:
    rows = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if len(r.get("prompt_token_ids", [])) < min_prompt:
                continue
            if len(r.get("completion_token_ids", [])) < min_comp:
                continue
            rows.append(r)
    return rows


def rows_to_token_ids(rows: list, n_tokens: int) -> list[int]:
    ids: list[int] = []
    for row in rows:
        ids.extend(row["full_token_ids"])
        if len(ids) >= n_tokens:
            break
    return ids[:n_tokens]


# ── Module enumeration ────────────────────────────────────────────────────────

def get_transformer_linears(model) -> list[tuple]:
    """List (name, module, layer_idx, proj_name) for language_model layers."""
    result = []
    for name, module in model.named_modules():
        if not isinstance(module, torch.nn.Linear):
            continue
        if not name.startswith("model.language_model.layers."):
            continue
        parts = name.split(".")
        layer_idx = int(parts[3])
        proj_name = parts[-1]
        result.append((name, module, layer_idx, proj_name))
    return result


# ── Input scale helpers ───────────────────────────────────────────────────────

def compute_input_scale(acts: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """Per-column scale: s_d = x_d^alpha / w_d^(1-alpha), geom-normalized."""
    x_abs = acts.float().abs().mean(0).clamp_min(1e-6)
    w_abs = weight.float().abs().mean(0).clamp_min(1e-6)
    raw = x_abs.pow(ALPHA) / w_abs.pow(1.0 - ALPHA)
    raw = raw / torch.exp(torch.log(raw.clamp_min(1e-6)).mean())
    return raw.clamp(1.0 / 8.0, 8.0)


def fit_row_table_scale(table_fp32: torch.Tensor, token_ids: list[int]) -> torch.Tensor:
    """Per-column scale for a row-indexed table (embed_tokens or PLI)."""
    ids = torch.tensor(token_ids, dtype=torch.long).clamp(0, table_fp32.shape[0] - 1)
    x_abs = table_fp32[ids].float().abs().mean(0).clamp_min(1e-6)
    w_abs = table_fp32.float().abs().mean(0).clamp_min(1e-6)
    raw = x_abs.pow(ALPHA) / w_abs.pow(1.0 - ALPHA)
    raw = raw / torch.exp(torch.log(raw.clamp_min(1e-6)).mean())
    return raw.clamp(1.0 / 8.0, 8.0)


# ── GPU-accelerated stage-1 quantization ─────────────────────────────────────

@torch.no_grad()
def gpu_stage1_quant(
    weight_fp32: torch.Tensor,           # (N, K) float32, CPU
    bits: int,
    transform_bank: SharedTransformBank,
    group_size: int | None,
    rotation_family: str,
    input_scale: torch.Tensor | None,    # (K,) float32, CPU
    device: str = "cuda",
    batch: int = GPU_BATCH,
) -> tuple[torch.Tensor, float]:
    """GPU-accelerated stage-1 VQ, mirrors stage1_reconstruct_weight.

    Processes rows in batches on GPU.  Falls back to group_size=K (full row
    as one group) when group_size is None, 0, or >= K.
    """
    N, K = weight_fp32.shape
    family = normalize_rotation_family(rotation_family)

    if group_size is None or int(group_size) <= 0 or int(group_size) >= K:
        gs, G = K, 1
    else:
        gs = int(group_size)
        G  = math.ceil(K / gs)

    # Fetch rotation and codebook (CPU cache, move to GPU once)
    R_gpu  = transform_bank.rotation(gs, family=family).to(device=device, dtype=torch.float32)
    cb_gpu = transform_bank.codebook(gs, bits).to(device=device, dtype=torch.float32)

    scale_gpu = input_scale.to(device=device, dtype=torch.float32) if input_scale is not None else None

    out = torch.empty(N, K, dtype=torch.float16)

    for start in range(0, N, batch):
        end = min(start + batch, N)
        B   = end - start
        W   = weight_fp32[start:end].to(device=device, dtype=torch.float32)   # (B, K)

        # Apply input scale (column-wise)
        if scale_gpu is not None:
            W = W * scale_gpu.unsqueeze(0)

        # Reshape into groups: (B, G, gs)
        W_groups = W.view(B, G, gs)

        # Row norms per group: (B, G)
        norms = W_groups.norm(dim=2).clamp_min(1e-8)

        # Unit vectors: (B, G, gs)
        unit_W = W_groups / norms.unsqueeze(-1)

        # Rotate all groups at once: (B*G, gs) @ (gs, gs) → (B*G, gs)
        rotated = unit_W.view(B * G, gs) @ R_gpu

        # Quantize: nearest codeword per scalar
        # (B*G, gs, 1) vs (1, 1, num_cb) → (B*G, gs, num_cb)
        dists = (rotated.unsqueeze(-1) - cb_gpu.view(1, 1, -1)).abs()
        idx   = dists.argmin(dim=-1)          # (B*G, gs)
        dq    = cb_gpu[idx]                   # (B*G, gs)

        # Undo rotation: (B*G, gs) @ (gs, gs).T → (B*G, gs)
        recon_unit = dq @ R_gpu.T

        # Scale back by norms: (B, G, gs) * (B, G, 1)
        recon = recon_unit.view(B, G, gs) * norms.unsqueeze(-1)

        # Undo input scale
        if scale_gpu is not None:
            recon = recon / scale_gpu.view(G, gs).unsqueeze(0)

        out[start:end] = recon.view(B, K).half().cpu()

    # Average bits: index bits + norm (fp16 per group) + scale (amortized)
    avg_bits = (
        float(bits)
        + 16.0 * G / float(K)
        + (16.0 / float(N) if input_scale is not None else 0.0)
    )
    return out, avg_bits


# ── Per-config runner ─────────────────────────────────────────────────────────

def run_config(
    config: str,
    calib_rows: list,
    test_rows: list,
    transform_bank: SharedTransformBank,
    model_dir: str = MODEL_DIR,
) -> dict:
    print(f"\n{'='*70}", flush=True)
    print(f"  Config: {config}", flush=True)
    print(f"{'='*70}", flush=True)

    device = "cuda"
    dtype  = torch.bfloat16

    # ── 1. Load model ──────────────────────────────────────────────────────
    print("Loading model...", flush=True)
    t0 = time.perf_counter()
    model = Gemma4ForConditionalGeneration.from_pretrained(
        model_dir, torch_dtype=dtype, low_cpu_mem_usage=True,
    ).to(device)
    model.eval()
    print(f"  loaded in {time.perf_counter()-t0:.1f}s", flush=True)

    lm        = model.model.language_model
    embed_ref = lm.embed_tokens
    pli_ref   = lm.embed_tokens_per_layer

    # ── 2. Stash fp32 CPU copies before any in-place modification ──────────
    print("Saving fp32 weight copies...", flush=True)
    embed_fp32 = embed_ref.weight.detach().float().cpu().contiguous()
    pli_fp32   = pli_ref.weight.detach().float().cpu().contiguous()
    print(f"  embed {tuple(embed_fp32.shape)}  PLI {tuple(pli_fp32.shape)}", flush=True)

    # ── 3. Calibration token sequences ────────────────────────────────────
    act_ids_list   = rows_to_token_ids(calib_rows, N_CALIB_ACT)
    scale_ids_list = rows_to_token_ids(calib_rows, N_CALIB_SCALE)
    act_ids_tensor = torch.tensor([act_ids_list], dtype=torch.long)   # (1, N_CALIB_ACT)

    # ── 4. Enumerate transformer linears ──────────────────────────────────
    linears = get_transformer_linears(model)
    linear_names = [n for n, _, _, _ in linears]
    print(f"Found {len(linears)} transformer linears", flush=True)

    # ── 5. Capture activations (single GPU forward pass) ─────────────────
    print(f"Capturing activations ({N_CALIB_ACT} tokens)...", flush=True)
    t_act = time.perf_counter()
    activations = capture_linear_inputs(
        model, act_ids_tensor, linear_names,
        max_samples_per_layer=N_CALIB_ACT, device=device,
    )
    print(f"  done in {time.perf_counter()-t_act:.1f}s  ({len(activations)} captured)", flush=True)

    # ── 6. Quantize transformer linears (GPU stage-1) ─────────────────────
    print(f"Quantizing {len(linears)} linears (group_size=128, hadamard, GPU)...", flush=True)
    t_lin = time.perf_counter()
    for i, (name, module, layer_idx, proj_name) in enumerate(linears):
        bits  = bits_for_linear(config, layer_idx, proj_name)
        acts  = activations.pop(name, None)
        w     = module.weight.detach().float().cpu()
        iscale = compute_input_scale(acts, w) if acts is not None else None
        recon, _ = gpu_stage1_quant(
            w, bits=bits, transform_bank=transform_bank,
            group_size=128, rotation_family="hadamard",
            input_scale=iscale, device=device, batch=w.shape[0],
        )
        with torch.no_grad():
            module.weight.data.copy_(recon.to(dtype))
        del w, recon
        if i % 63 == 0 or i == len(linears) - 1:
            elapsed = time.perf_counter() - t_lin
            print(f"  [{i+1:3d}/{len(linears)}] {name:<60s} bits={bits}  "
                  f"({elapsed:.0f}s)", flush=True)
    del activations
    gc.collect()
    torch.cuda.empty_cache()
    print(f"  transformer linears done in {time.perf_counter()-t_lin:.1f}s", flush=True)

    # ── 7. Quantize PLI (2-bit, group_size=128, hadamard, GPU batched) ────
    print(f"\nFitting PLI input scale ({N_CALIB_SCALE} tokens)...", flush=True)
    pli_scale = fit_row_table_scale(pli_fp32, scale_ids_list)
    print(f"  scale: min={pli_scale.min():.3f}  max={pli_scale.max():.3f}", flush=True)

    print(f"Quantizing PLI (2-bit, group_size=128, hadamard, GPU batch={GPU_BATCH})...", flush=True)
    t_pli = time.perf_counter()
    pli_q, pli_avg_bits = gpu_stage1_quant(
        pli_fp32, bits=2, transform_bank=transform_bank,
        group_size=128, rotation_family="hadamard",
        input_scale=pli_scale, device=device, batch=GPU_BATCH,
    )
    print(f"  PLI done in {time.perf_counter()-t_pli:.1f}s  avg_bits={pli_avg_bits:.3f}", flush=True)

    with torch.no_grad():
        pli_ref.weight.data.copy_(pli_q.to(dtype).to(device))
    del pli_fp32, pli_q, pli_scale
    gc.collect()
    torch.cuda.empty_cache()

    # ── 8. Quantize embed_tokens (3-bit, GPU) ────────────────────────────
    print(f"\nFitting embed input scale ({N_CALIB_SCALE} tokens)...", flush=True)
    embed_scale = fit_row_table_scale(embed_fp32, scale_ids_list)
    print(f"  scale: min={embed_scale.min():.3f}  max={embed_scale.max():.3f}", flush=True)

    emb_gs, emb_rot = embed_quant_params(config)
    print(f"Quantizing embed_tokens (3-bit, group_size={emb_gs}, {emb_rot}, GPU batch={GPU_BATCH})...", flush=True)
    t_emb = time.perf_counter()
    embed_q, embed_avg_bits = gpu_stage1_quant(
        embed_fp32, bits=3, transform_bank=transform_bank,
        group_size=emb_gs, rotation_family=emb_rot,
        input_scale=embed_scale, device=device, batch=GPU_BATCH,
    )
    print(f"  embed done in {time.perf_counter()-t_emb:.1f}s  avg_bits={embed_avg_bits:.3f}", flush=True)

    embed_data_ptr = embed_ref.weight.data_ptr()
    with torch.no_grad():
        embed_ref.weight.data.copy_(embed_q.to(dtype).to(device))
    if hasattr(model, "lm_head") and model.lm_head.weight.data_ptr() != embed_data_ptr:
        with torch.no_grad():
            model.lm_head.weight.data.copy_(embed_q.to(dtype).to(device))
    del embed_fp32, embed_q, embed_scale
    gc.collect()
    torch.cuda.empty_cache()

    # ── 9. Evaluate completion PPL ────────────────────────────────────────
    print(f"\nEvaluating PPL on {len(test_rows)} test rows (max_len={MAX_LEN})...", flush=True)
    t_eval = time.perf_counter()
    total_nll, total_tok = completion_nll(model, test_rows, device, MAX_LEN)
    ppl = math.exp(total_nll / total_tok)
    print(f"  PPL={ppl:.4f}  tokens={total_tok}  "
          f"elapsed={time.perf_counter()-t_eval:.1f}s", flush=True)

    del model
    gc.collect()
    torch.cuda.empty_cache()

    return {
        "config":         config,
        "ppl":            ppl,
        "nll_sum":        total_nll,
        "tokens":         total_tok,
        "pli_avg_bits":   pli_avg_bits,
        "embed_avg_bits": embed_avg_bits,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--model-dir", default=MODEL_DIR)
    p.add_argument("--traj-path",  default=TRAJ_PATH)
    p.add_argument("--out-path",   default=str(OUT_PATH))
    p.add_argument("--test-path",  default=None,
                   help="Fixed held-out test file. When set, all traj-path rows "
                        "not in this set are used as calibration.")
    args = p.parse_args()

    traj_path = args.traj_path
    out_path  = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if out_path.exists():
        with open(out_path) as f:
            existing = json.load(f)
        print(f"Resuming from {out_path} "
              f"({len(existing.get('configs', []))} configs done)", flush=True)

    print(f"\nLoading trajectories from {traj_path}...", flush=True)
    all_rows = load_all_trajectories(traj_path)
    print(f"  {len(all_rows)} rows total", flush=True)

    if args.test_path:
        print(f"Loading fixed test set from {args.test_path}...", flush=True)
        test_rows  = load_all_trajectories(args.test_path)
        test_hashes = {r["conv_hash"] for r in test_rows}
        calib_rows = [r for r in all_rows if r.get("conv_hash") not in test_hashes]
        print(f"  test: {len(test_rows)} rows  calib: {len(calib_rows)} rows", flush=True)
    else:
        test_rows  = all_rows[-N_TEST:]
        calib_rows = all_rows[:-N_TEST]
    test_compl  = sum(len(r["completion_token_ids"]) for r in test_rows)
    calib_total = sum(len(r["full_token_ids"]) for r in calib_rows)
    print(f"  test:  {len(test_rows):,} rows  {test_compl:,} completion tokens", flush=True)
    print(f"  calib: {len(calib_rows):,} rows  {calib_total:,} total tokens", flush=True)

    results = existing or {
        "traj_path":              traj_path,
        "n_test":                 len(test_rows),
        "n_calib":                len(calib_rows),
        "test_completion_tokens": test_compl,
        "calib_total_tokens":     calib_total,
        "n_calib_act":            N_CALIB_ACT,
        "n_calib_scale":          N_CALIB_SCALE,
        "alpha":                  ALPHA,
        "max_len":                MAX_LEN,
        "configs":                [],
    }
    done_configs = {r["config"] for r in results.get("configs", [])}

    transform_bank = SharedTransformBank(seed=1234)

    for config in CONFIGS:
        if config in done_configs:
            print(f"\nSkipping {config} (already done)", flush=True)
            continue

        t0 = time.perf_counter()
        r  = run_config(config, calib_rows, test_rows, transform_bank, model_dir=args.model_dir)
        r["wall_seconds"] = round(time.perf_counter() - t0, 1)
        results.setdefault("configs", []).append(r)
        done_configs.add(config)

        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved → {out_path}", flush=True)

    print(f"\n{'='*70}", flush=True)
    print(f"{'config':<37}{'PPL':>8}{'pli_bits':>10}{'emb_bits':>10}{'time(min)':>11}", flush=True)
    print("-" * 70, flush=True)
    for r in results["configs"]:
        print(f"{r['config']:<37}{r['ppl']:>8.4f}{r['pli_avg_bits']:>10.3f}"
              f"{r['embed_avg_bits']:>10.3f}{r['wall_seconds']/60:>10.1f}m", flush=True)
    print("=" * 70, flush=True)
    print(f"\nResults: {out_path}", flush=True)


if __name__ == "__main__":
    main()

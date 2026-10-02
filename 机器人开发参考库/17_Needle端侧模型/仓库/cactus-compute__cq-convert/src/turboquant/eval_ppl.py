"""Perplexity evaluation for gemma-4-E2B-it: fp vs full-cactus-INT4.

Loads the model once, computes completion-token PPL on a subset of
wildchat calibration trajectories, then re-runs after applying
cactus_int4_quantize() in place to every 2D weight reachable from the
text path (language_model/*, lm_head). Vision and audio towers are
left untouched — they don't affect text-only logits.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import time
from pathlib import Path

import torch
from transformers import Gemma4ForConditionalGeneration

from cactus_int4 import cactus_int4_quantize, cactus_int8_quantize


MODEL_DIR = "google/gemma-4-E2B-it"
TRAJ_PATH = str(Path(__file__).resolve().parents[2] / "data/text/trajectories_2x.jsonl")


def load_trajectories(path: str, n: int, min_prompt: int = 4, min_completion: int = 16):
    rows = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if len(r["prompt_token_ids"]) < min_prompt:  continue
            if len(r["completion_token_ids"]) < min_completion: continue
            rows.append(r)
            if len(rows) >= n: break
    return rows


@torch.inference_mode()
def completion_nll(model, rows, device, max_len: int):
    """Total NLL and total completion tokens, evaluated one sample at a time."""
    total_nll = 0.0
    total_tok = 0
    t0 = time.perf_counter()
    for i, rec in enumerate(rows):
        prompt_ids = rec["prompt_token_ids"]
        comp_ids   = rec["completion_token_ids"]
        full       = (prompt_ids + comp_ids)[:max_len]
        if len(full) <= len(prompt_ids):
            continue
        ids = torch.tensor([full], dtype=torch.long, device=device)
        out = model(ids, use_cache=False)
        logits = out.logits[:, :-1, :].float()
        targets = ids[:, 1:]
        start = len(prompt_ids) - 1
        end   = logits.size(1)
        if end <= start:
            continue
        nll = torch.nn.functional.cross_entropy(
            logits[0, start:end, :], targets[0, start:end], reduction="sum"
        )
        total_nll += nll.item()
        total_tok += (end - start)
        if (i + 1) % 25 == 0:
            elapsed = time.perf_counter() - t0
            ppl = math.exp(total_nll / total_tok) if total_tok else float("nan")
            print(f"  [{i+1}/{len(rows)}] tokens={total_tok} running_ppl={ppl:.3f} "
                  f"rate={total_tok/elapsed:.0f} tok/s", flush=True)
    return total_nll, total_tok


def apply_cactus_baseline(model) -> dict:
    """Apply the cactus production INT4 baseline in place:
    - torch.nn.Linear under language_model.* and lm_head -> INT4
    - torch.nn.Embedding under language_model.* -> INT8 (token_embeddings
      and embed_tokens_per_layer; matches tensor_io.py:183 exception).
    Tied weights (lm_head sharing embed_tokens) are only quantized once.
    """
    summary = {"int4_linear": 0, "int8_embed": 0, "params": 0, "skipped_tied": 0}
    seen_data_ptr = set()
    targets = []
    for name, module in model.named_modules():
        if not (name.startswith("model.language_model") or name == "lm_head"):
            continue
        if isinstance(module, torch.nn.Linear):
            targets.append((name, "int4", module.weight))
        elif isinstance(module, torch.nn.Embedding):
            targets.append((name, "int8", module.weight))

    for name, kind, W in targets:
        key = W.data_ptr()
        if key in seen_data_ptr:
            summary["skipped_tied"] += 1
            print(f"  skip (tied)   {name}  shape={tuple(W.shape)}", flush=True)
            continue
        seen_data_ptr.add(key)
        with torch.no_grad():
            if kind == "int4":
                new_w = cactus_int4_quantize(W.data.to(torch.float32))
                summary["int4_linear"] += 1
            else:
                new_w = cactus_int8_quantize(W.data.to(torch.float32))
                summary["int8_embed"]  += 1
            W.data.copy_(new_w.to(W.dtype))
        summary["params"] += W.numel()
        print(f"  {kind:4s} {name}  shape={tuple(W.shape)}", flush=True)
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=128, help="#trajectories")
    p.add_argument("--max-len", type=int, default=1024)
    p.add_argument("--mode", choices=["fp", "int4", "both"], default="both")
    p.add_argument("--dtype", choices=["bf16", "fp16", "fp32"], default="bf16")
    args = p.parse_args()

    device = "cuda"
    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[args.dtype]

    print(f"loading {MODEL_DIR} dtype={args.dtype}", flush=True)
    t0 = time.perf_counter()
    model = Gemma4ForConditionalGeneration.from_pretrained(
        MODEL_DIR, torch_dtype=dtype, low_cpu_mem_usage=True
    ).to(device)
    model.eval()
    print(f"loaded in {time.perf_counter()-t0:.1f}s; params={sum(p.numel() for p in model.parameters())/1e9:.2f}B",
          flush=True)

    rows = load_trajectories(TRAJ_PATH, args.n)
    print(f"using {len(rows)} trajectories", flush=True)

    results = {}

    if args.mode in ("fp", "both"):
        print(f"\n=== fp ({args.dtype}) eval ===", flush=True)
        nll, tok = completion_nll(model, rows, device, args.max_len)
        ppl = math.exp(nll / tok)
        results["fp"] = {"nll_sum": nll, "tokens": tok, "ppl": ppl}
        print(f"fp: tokens={tok} ppl={ppl:.4f}", flush=True)

    if args.mode in ("int4", "both"):
        print("\n=== applying cactus baseline (INT4 linears + INT8 embeddings) ===", flush=True)
        summary = apply_cactus_baseline(model)
        print(f"quantized: {summary['int4_linear']} INT4 linears, "
              f"{summary['int8_embed']} INT8 embeddings, "
              f"{summary['skipped_tied']} tied-skip, "
              f"{summary['params']/1e9:.2f}B params", flush=True)

        torch.cuda.empty_cache(); gc.collect()

        print("\n=== cactus baseline eval ===", flush=True)
        nll, tok = completion_nll(model, rows, device, args.max_len)
        ppl = math.exp(nll / tok)
        results["int4"] = {"nll_sum": nll, "tokens": tok, "ppl": ppl}
        print(f"cactus: tokens={tok} ppl={ppl:.4f}", flush=True)

    if "fp" in results and "int4" in results:
        print(f"\nΔppl = {results['int4']['ppl'] - results['fp']['ppl']:+.4f}  "
              f"({100*(results['int4']['ppl']/results['fp']['ppl']-1):+.2f}%)", flush=True)

    print("\n" + json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()

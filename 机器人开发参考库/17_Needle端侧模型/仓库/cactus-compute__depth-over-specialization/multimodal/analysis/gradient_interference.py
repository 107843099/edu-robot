"""Gradient interference analysis for the shared trimodal encoder."""

import argparse
import json
import os

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from ..config import create_model, TOKENIZER, MAX_SEQ_LENGTH
from ..loss import ContrastiveLoss
from ..data.preprocessed_dataset import PreprocessedDataset


MODEL_NAME = "shared_3u_tia"

LATEX_LABELS = {
    "ti_ta": "$\\mathcal{L}_\\text{TI}$ vs.\\ $\\mathcal{L}_\\text{TA}$",
    "ti_ia": "$\\mathcal{L}_\\text{TI}$ vs.\\ $\\mathcal{L}_\\text{IA}$",
    "ta_ia": "$\\mathcal{L}_\\text{TA}$ vs.\\ $\\mathcal{L}_\\text{IA}$",
}


def collate_fn(batch, tokenizer, max_length):
    result = {}
    if "image" in batch[0]:
        result["image"] = torch.stack([item["image"] for item in batch])
    if "audio" in batch[0]:
        result["audio"] = torch.stack([item["audio"] for item in batch])
    if "caption" in batch[0]:
        tokenized = tokenizer(
            [item["caption"] for item in batch],
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        result["input_ids"] = tokenized["input_ids"]
        result["attention_mask"] = tokenized["attention_mask"]
    return result


def get_transformer_grad_vector(model):
    grads = [
        p.grad.detach().flatten()
        for p in model.transformer.parameters()
        if p.grad is not None
    ]
    return torch.cat(grads) if grads else None


def compute_per_loss_gradients(model, batch, loss_fn, device):
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    images = batch["image"].to(device)
    audio = batch["audio"].to(device)

    grad_vecs = {}
    for pair in ["ti", "ta", "ia"]:
        model.zero_grad()
        if pair == "ti":
            a = model.encode_text(input_ids, attention_mask)
            b = model.encode_image(images)
        elif pair == "ta":
            a = model.encode_text(input_ids, attention_mask)
            b = model.encode_audio(audio)
        else:
            a = model.encode_image(images)
            b = model.encode_audio(audio)
        loss_fn(a, b, model.logit_scale).backward()
        g = get_transformer_grad_vector(model)
        if g is not None:
            grad_vecs[pair] = g.cpu()

    return grad_vecs


def cosine(a, b):
    return F.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item()


def analyze_seed(seed, runs_dir, data_dir, n_batches, batch_size, device):
    checkpoint = os.path.join(
        runs_dir, f"seed{seed}", MODEL_NAME, "checkpoints", "best_model.pt"
    )
    if not os.path.exists(checkpoint):
        print(f"  WARNING: checkpoint not found: {checkpoint}")
        return None

    model = create_model(MODEL_NAME).to(device)
    model.load_state_dict(torch.load(checkpoint, map_location=device))
    model.eval()

    dataset = PreprocessedDataset(root_dir=data_dir, split="test")
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=lambda b: collate_fn(b, TOKENIZER, MAX_SEQ_LENGTH),
        num_workers=0,
    )

    loss_fn = ContrastiveLoss()
    batch_results = []

    for i, batch in enumerate(loader):
        if i >= n_batches:
            break
        grads = compute_per_loss_gradients(model, batch, loss_fn, device)
        if len(grads) == 3:
            r = {
                "ti_ta": cosine(grads["ti"], grads["ta"]),
                "ti_ia": cosine(grads["ti"], grads["ia"]),
                "ta_ia": cosine(grads["ta"], grads["ia"]),
            }
            batch_results.append(r)
            print(
                f"    batch {i + 1}/{n_batches}:"
                f"  cos(TI,TA)={r['ti_ta']:+.4f}"
                f"  cos(TI,IA)={r['ti_ia']:+.4f}"
                f"  cos(TA,IA)={r['ta_ia']:+.4f}"
            )

    if not batch_results:
        return None
    return {k: float(np.mean([r[k] for r in batch_results])) for k in batch_results[0]}


def aggregate_across_seeds(per_seed):
    pairs = ["ti_ta", "ti_ia", "ta_ia"]
    return {
        pair: {
            "mean": float(np.mean([per_seed[s][pair] for s in per_seed])),
            "std": float(np.std([per_seed[s][pair] for s in per_seed], ddof=0)),
        }
        for pair in pairs
    }


def print_results(per_seed, aggregate):
    print("\n" + "=" * 80)
    print(f"GRADIENT COSINE SIMILARITY (mean ± std, N={len(per_seed)} seeds)")
    print("=" * 80)
    for pair, stats in aggregate.items():
        print(f"  {pair}: {stats['mean']:+.4f} ± {stats['std']:.4f}")


def print_latex_table(aggregate):
    print("\n" + "=" * 80)
    print("LATEX: GRADIENT INTERFERENCE TABLE")
    print("=" * 80)
    print("\\begin{tabular}{lc}")
    print("Loss pair & Cosine similarity \\\\")
    print("\\hline")
    for pair, stats in aggregate.items():
        m, s = stats["mean"], stats["std"]
        print(f"{LATEX_LABELS[pair]} & ${m:+.3f}\\pm{s:.3f}$ \\\\")
    print("\\end{tabular}")


def save_json(per_seed, aggregate, runs_dir):
    out_path = os.path.join(runs_dir, "gradient_interference.json")
    with open(out_path, "w") as f:
        json.dump({"model": MODEL_NAME, "per_seed": per_seed, "aggregate": aggregate}, f, indent=2)
    print(f"\nGradient interference results saved to: {out_path}")


def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}  |  model: {MODEL_NAME}  |  batches/seed: {args.n_batches}  |  batch_size: {args.batch_size}")

    per_seed = {}
    for seed in args.seeds:
        print(f"Seed {seed}:")
        result = analyze_seed(seed, args.runs_dir, args.data_dir, args.n_batches, args.batch_size, device)
        if result is not None:
            per_seed[seed] = result

    if not per_seed:
        print("No results computed.")
        return

    aggregate = aggregate_across_seeds(per_seed)
    print_results(per_seed, aggregate)

    if args.latex:
        print_latex_table(aggregate)

    save_json(per_seed, aggregate, args.runs_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs_dir", default="runs")
    parser.add_argument("--data_dir", default="data/preprocessed_coco")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--n_batches", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--latex", action="store_true", help="Print LaTeX table")
    main(parser.parse_args())

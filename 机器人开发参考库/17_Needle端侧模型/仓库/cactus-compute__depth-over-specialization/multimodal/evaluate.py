"""Evaluation script for multimodal encoders."""

import argparse
import json
import os
import random

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from .data.preprocessed_dataset import PreprocessedDataset
from .config import create_model, TOKENIZER, MAX_SEQ_LENGTH


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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


def compute_embeddings(model, dataloader, modalities, device):
    """Compute all embeddings for the dataset."""
    model.eval()

    embeds = {mod: [] for mod in modalities}

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Computing embeddings"):
            if "t" in modalities:
                text_embed = model.encode_text(
                    batch["input_ids"].to(device), batch["attention_mask"].to(device)
                )
                embeds["t"].append(text_embed.cpu())

            if "i" in modalities:
                image_embed = model.encode_image(batch["image"].to(device))
                embeds["i"].append(image_embed.cpu())

            if "a" in modalities:
                audio_embed = model.encode_audio(batch["audio"].to(device))
                embeds["a"].append(audio_embed.cpu())

    # Concatenate and normalize
    for mod in modalities:
        embeds[mod] = torch.cat(embeds[mod], dim=0)
        embeds[mod] = embeds[mod] / embeds[mod].norm(dim=-1, keepdim=True)

    return embeds


def compute_retrieval_metrics(query_embeds, key_embeds, k_values=[1, 5, 10]):
    """Compute retrieval metrics (R@k, MedR, MRR, NDCG@10) for query->key retrieval."""
    # Compute similarity matrix: [num_queries, num_keys]
    similarity = query_embeds @ key_embeds.T

    # Get rankings (argsort in descending order)
    ranks = similarity.argsort(dim=1, descending=True)

    # Ground truth: assume aligned indices (i-th query matches i-th key)
    num_samples = query_embeds.shape[0]

    # Find rank of correct match for each query (0-indexed)
    correct_ranks = []
    for i in range(num_samples):
        rank_list = ranks[i].tolist()
        correct_rank = rank_list.index(i)
        correct_ranks.append(correct_rank)

    correct_ranks = np.array(correct_ranks)

    # Recall@K
    metrics = {}
    for k in k_values:
        recall_at_k = 100.0 * np.mean(correct_ranks < k)
        metrics[f"R@{k}"] = recall_at_k

    # Median Rank (1-indexed)
    metrics["MedR"] = float(np.median(correct_ranks) + 1)

    # MRR: mean reciprocal rank (correct_ranks is 0-indexed, so rank = r+1)
    metrics["MRR"] = float(np.mean(1.0 / (correct_ranks + 1)))

    # NDCG@10: binary relevance, 1 positive per query
    # DCG@10 = 1/log2(r+2) if r < 10 else 0  (r is 0-indexed, so rank_1indexed = r+1)
    # IDCG@10 = 1/log2(2) = 1  (ideal: correct item at rank 1)
    # NDCG@10 = DCG@10 / IDCG@10 = DCG@10
    ndcg_10 = np.mean(
        [1.0 / np.log2(r + 2) if r < 10 else 0.0 for r in correct_ranks]
    )
    metrics["NDCG@10"] = float(100.0 * ndcg_10)

    return metrics


def compute_embedding_diagnostics(embeds, modalities):
    """Compute alignment, uniformity, and anisotropy (Wang & Isola ICML 2020; Ethayarajh 2019)."""
    results = {}

    # Cross-modal alignment (Wang & Isola 2020): mean squared L2 distance of positive pairs
    pairs = []
    if "t" in modalities and "i" in modalities:
        pairs.append(("t", "i"))
    if "t" in modalities and "a" in modalities:
        pairs.append(("t", "a"))
    if "i" in modalities and "a" in modalities:
        pairs.append(("i", "a"))

    for m1, m2 in pairs:
        x, y = embeds[m1], embeds[m2]
        alignment = (x - y).norm(p=2, dim=1).pow(2).mean().item()
        results[f"align_{m1}{m2}"] = alignment

    # Per-modality uniformity and anisotropy
    for mod in modalities:
        x = embeds[mod]
        N = x.shape[0]

        # Uniformity (Wang & Isola 2020): log mean of Gaussian kernel over all N*(N-1)/2 pairs
        uniformity = torch.pdist(x).pow(2).mul(-2).exp().mean().log().item()
        results[f"uniform_{mod}"] = uniformity

        # Anisotropy (Ethayarajh 2019): mean pairwise cosine similarity (excluding self)
        # x is L2-normalized so x @ x.T gives cosine similarities directly
        sim_sum = (x @ x.T).sum().item()
        anisotropy = (sim_sum - N) / (N * (N - 1))
        results[f"aniso_{mod}"] = anisotropy

    return results


def evaluate_retrieval(embeds, modalities):
    """Evaluate all possible retrieval directions."""
    results = {}

    modality_pairs = []
    if "t" in modalities and "i" in modalities:
        modality_pairs.extend([("t", "i"), ("i", "t")])
    if "t" in modalities and "a" in modalities:
        modality_pairs.extend([("t", "a"), ("a", "t")])
    if "i" in modalities and "a" in modalities:
        modality_pairs.extend([("i", "a"), ("a", "i")])

    for query_mod, key_mod in modality_pairs:
        print(f"\nEvaluating {query_mod.upper()}→{key_mod.upper()} retrieval...")
        metrics = compute_retrieval_metrics(embeds[query_mod], embeds[key_mod])

        direction_key = f"{query_mod}2{key_mod}"
        results[direction_key] = metrics

        # Print results
        print(f"  R@1:     {metrics['R@1']:.2f}%")
        print(f"  R@5:     {metrics['R@5']:.2f}%")
        print(f"  R@10:    {metrics['R@10']:.2f}%")
        print(f"  MedR:    {metrics['MedR']:.1f}")
        print(f"  MRR:     {metrics['MRR']:.4f}")
        print(f"  NDCG@10: {metrics['NDCG@10']:.2f}%")

    return results


def main(args):
    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    modalities = args.model.split("_")[-1]

    print(f"Device: {device}")
    print(f"Model: {args.model}")
    print(f"Checkpoint: {args.checkpoint}")

    # Load dataset
    dataset = PreprocessedDataset(root_dir=args.data_dir, split=args.split)
    print(f"Dataset size: {len(dataset)}")

    loader_kwargs = {
        "batch_size": args.batch_size,
        "num_workers": args.num_workers,
        "collate_fn": lambda b: collate_fn(b, TOKENIZER, MAX_SEQ_LENGTH),
        "pin_memory": True,
        "shuffle": False,
    }

    dataloader = DataLoader(dataset, **loader_kwargs)

    # Load model
    model = create_model(args.model).to(device)

    if os.path.exists(args.checkpoint):
        print(f"Loading checkpoint from {args.checkpoint}")
        state_dict = torch.load(args.checkpoint, map_location=device)
        model.load_state_dict(state_dict)
    else:
        print(f"ERROR: Checkpoint not found: {args.checkpoint}")
        return

    # Compute embeddings
    print("\n" + "=" * 50)
    print("Computing embeddings...")
    print("=" * 50)
    embeds = compute_embeddings(model, dataloader, modalities, device)

    # Evaluate retrieval
    print("\n" + "=" * 50)
    print("Evaluating retrieval...")
    print("=" * 50)
    results = evaluate_retrieval(embeds, modalities)

    # Compute embedding diagnostics (alignment, uniformity, anisotropy)
    print("\n" + "=" * 50)
    print("Computing embedding diagnostics...")
    print("=" * 50)
    diagnostics = compute_embedding_diagnostics(embeds, modalities)
    for k, v in diagnostics.items():
        print(f"  {k}: {v:.4f}")
    results["diagnostics"] = diagnostics

    # Save results
    output_dir = os.path.join(args.output_dir, args.model)
    os.makedirs(output_dir, exist_ok=True)

    results_file = os.path.join(output_dir, f"eval_results_{args.split}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument(
        "--split", type=str, default="test", choices=["train", "val", "test"]
    )
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--data_dir", type=str, default="data/preprocessed_coco")
    parser.add_argument("--num_workers", type=int, default=8)
    parser.add_argument("--input_dir", type=str, default="runs")
    parser.add_argument("--output_dir", type=str, default="evals")
    parser.add_argument("--seed", type=int, default=0)

    args = parser.parse_args()

    # Set default checkpoint path if not specified
    if args.checkpoint is None:
        args.checkpoint = os.path.join(
            args.input_dir, args.model, "checkpoints", "best_model.pt"
        )

    main(args)

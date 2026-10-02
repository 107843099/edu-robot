"""Dataset statistics for the COCO Localized Narratives splits."""

import argparse
import json
import os
from collections import Counter

from ..data.localized_narratives import DataLoader


def load_metadata(preprocessed_dir, split):
    path = os.path.join(preprocessed_dir, f"{split}_metadata.json")
    with open(path) as f:
        return json.load(f)


def build_caption_to_image_id(coco_dir):
    loader = DataLoader(coco_dir)
    caption_to_image_id = {}
    for dataset_split in ("coco_train", "coco_val"):
        for ann in loader.load_annotations(dataset_split):
            if ann.caption not in caption_to_image_id:
                caption_to_image_id[ann.caption] = ann.image_id
    return caption_to_image_id


def resolve_image_ids(metadata, caption_to_image_id):
    image_ids = []
    unmatched = 0
    for item in metadata:
        iid = caption_to_image_id.get(item["caption"])
        if iid is None:
            unmatched += 1
        image_ids.append(iid)
    if unmatched:
        print(f"  WARNING: {unmatched}/{len(metadata)} captions not matched to image_id")
    return image_ids


def compute_stats(metadata, image_ids):
    n = len(metadata)
    matched = [iid for iid in image_ids if iid is not None]
    image_counts = Counter(matched)
    unique_images = len(image_counts)
    ann_per_image = n / unique_images if unique_images else 0.0
    multi_annotator_images = sum(1 for c in image_counts.values() if c >= 2)
    multi_annotator_pct = 100.0 * multi_annotator_images / unique_images if unique_images else 0.0
    samples_with_pair = sum(c for c in image_counts.values() if c >= 2)
    fn_ceiling_pct = 100.0 * samples_with_pair / n if n else 0.0
    return {
        "n_samples": n,
        "unique_images": unique_images,
        "ann_per_image": round(ann_per_image, 2),
        "multi_annotator_images": multi_annotator_images,
        "multi_annotator_pct": round(multi_annotator_pct, 1),
        "samples_with_pair": samples_with_pair,
        "fn_ceiling_pct": round(fn_ceiling_pct, 1),
    }


def print_stats(results):
    total = results["total"]
    print("\n" + "=" * 80)
    print(f"DATASET STATISTICS  (total={total:,})")
    print("=" * 80)
    for split, stats in results["splits"].items():
        pct = 100.0 * stats["n_samples"] / total
        print(
            f"  {split:<6} {stats['n_samples']:>7,} samples ({pct:.1f}%)"
            f"  |  {stats['unique_images']:,} unique images"
            f"  |  {stats['ann_per_image']:.2f} ann/image"
            f"  |  {stats['multi_annotator_pct']:.1f}% multi-annotator"
        )
        if split in ("val", "test"):
            print(
                f"         FN ceiling: {stats['samples_with_pair']:,} samples"
                f" ({stats['fn_ceiling_pct']:.1f}% of {split} queries)"
            )


def save_json(results, preprocessed_dir):
    out_path = os.path.join(preprocessed_dir, "dataset_stats.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDataset stats saved to: {out_path}")


def main(args):
    print("Loading metadata...")
    train_meta = load_metadata(args.preprocessed_dir, "train")
    val_meta = load_metadata(args.preprocessed_dir, "val")
    test_meta = load_metadata(args.preprocessed_dir, "test")
    total = len(train_meta) + len(val_meta) + len(test_meta)

    print("Loading LN annotations...")
    caption_to_image_id = build_caption_to_image_id(args.coco_dir)

    results = {
        "total": total,
        "splits": {
            "train": compute_stats(train_meta, resolve_image_ids(train_meta, caption_to_image_id)),
            "val": compute_stats(val_meta, resolve_image_ids(val_meta, caption_to_image_id)),
            "test": compute_stats(test_meta, resolve_image_ids(test_meta, caption_to_image_id)),
        },
    }

    print_stats(results)
    save_json(results, args.preprocessed_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preprocessed_dir", default="data/preprocessed_coco")
    parser.add_argument("--coco_dir", default="data/coco")
    main(parser.parse_args())

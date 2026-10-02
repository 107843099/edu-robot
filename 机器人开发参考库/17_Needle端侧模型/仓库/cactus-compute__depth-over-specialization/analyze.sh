#!/bin/bash

set -e

SEEDS="0 1 2"
RUNS_DIR="runs"
EVALS_DIR="evals"
DATA_DIR="data/preprocessed_coco"
COCO_DIR="data/coco"
SPLIT="test"

echo "=========================================="
echo "Dataset statistics"
echo "=========================================="

python -m multimodal.analysis.analyze_dataset \
    --preprocessed_dir "$DATA_DIR" \
    --coco_dir "$COCO_DIR"

echo ""
echo "=========================================="
echo "Loss gap analysis (train/val gaps)"
echo "=========================================="

python -m multimodal.analysis.analyze_loss_gaps \
    --runs_dir "$RUNS_DIR" \
    --seeds $SEEDS \
    --latex

echo ""
echo "=========================================="
echo "Retrieval metrics (mean ± std across seeds)"
echo "=========================================="

python -m multimodal.analysis.analyze_seeds \
    --evals_dir "$EVALS_DIR" \
    --seeds $SEEDS \
    --split "$SPLIT" \
    --latex

echo ""
echo "=========================================="
echo "Gradient interference (SharedTIA 3U)"
echo "=========================================="

python -m multimodal.analysis.gradient_interference \
    --runs_dir "$RUNS_DIR" \
    --data_dir "$DATA_DIR" \
    --seeds $SEEDS \
    --n_batches 4 \
    --batch_size 256

echo ""
echo "All analysis complete!"

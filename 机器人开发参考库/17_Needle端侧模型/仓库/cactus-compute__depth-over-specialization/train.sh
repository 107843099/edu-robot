#!/bin/bash

SEEDS=(0 1 2)

MODELS=(
    "shared_1u_ti"
    "shared_1u_ta"
    "shared_1u_ia"
    "shared_1u_tia"
    "shared_2u_ti"
    "shared_2u_ta"
    "shared_2u_ia"
    "shared_2u_tia"
    "shared_3u_ti"
    "shared_3u_ta"
    "shared_3u_ia"
    "shared_3u_tia"
    "separate_2u_ti"
    "separate_2u_ta"
    "separate_2u_ia"
    "separate_3u_tia"
)

for SEED in "${SEEDS[@]}"; do
    for MODEL in "${MODELS[@]}"; do
        echo "=========================================="
        echo "Training: $MODEL (seed $SEED)"
        echo "=========================================="

        python -m multimodal.train \
            --model "$MODEL" \
            --seed "$SEED" \
            --epochs 20 \
            --output_dir "runs/seed${SEED}" \
            --wandb \
            --wandb_run_name "${MODEL}_seed${SEED}"

        if [ $? -ne 0 ]; then
            echo "Error training $MODEL (seed $SEED)"
            exit 1
        fi

        echo ""
    done
done

echo "All models trained successfully!"

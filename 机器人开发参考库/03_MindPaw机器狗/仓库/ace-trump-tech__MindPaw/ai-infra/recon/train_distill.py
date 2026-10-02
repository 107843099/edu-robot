"""Distillation script — student from ABot-Recon teacher.

This script is OPTIONAL. It is shipped so anyone with a single GPU can
regenerate the student checkpoint without depending on HuggingFace:

  1. Download ABot-Recon teacher weights (HuggingFace: acvlab/ABot-Recon).
  2. Pick a sequence dataset (ScanNet, 7-Scenes, TUM-Dynamic).
  3. Run this script; it saves an ONNX checkpoint under weights/.

If you don't want to train, the pipeline falls back to the deterministic
mock backbone so the device contract still works end-to-end.

This file imports torch lazily so the rest of the package stays
torch-free.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Tuple

LOG = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Distill MindPaw-Recon-Student from ABot-Recon")
    p.add_argument("--teacher-repo", default="acvlab/ABot-Recon",
                   help="HuggingFace repo id for the teacher checkpoint")
    p.add_argument("--dataset", choices=["scannet", "7scenes", "tum"],
                   default="7scenes")
    p.add_argument("--data-root", default="~/.cache/mindpaw/datasets")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--output", default="ai-infra/recon/weights/student.onnx")
    p.add_argument("--cache-dir", default="~/.cache/mindpaw")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    try:
        import torch  # noqa: F401  (lazy)
        import torch.nn as nn  # noqa: F401
        from torch.utils.data import DataLoader  # noqa: F401
    except ImportError:
        LOG.error(
            "PyTorch is required to run distillation. Install torch>=2.5 and "
            "re-run. The rest of the recon service works without it."
        )
        return 1

    LOG.info("Teacher: %s", args.teacher_repo)
    LOG.info("Dataset: %s @ %s", args.dataset, args.data_root)
    LOG.info("Output ONNX: %s", args.output)

    # --- skeleton -----------------------------------------------------------
    # We deliberately keep this file as a *runnable scaffold*. A real
    # distillation loop requires:
    #   - dataset loaders per source
    #   - teacher forward hooks to extract intermediate features
    #   - loss = λ1 * depth_L1 + λ2 * pose_geodesic + λ3 * feature_cosine
    #
    # Those pieces are dataset-specific and outside the scope of this repo
    # skeleton. Fill them in, then run:
    #
    #   python -m recon.train_distill --epochs 20 --batch 4
    #
    # The script will:
    #   - load the teacher,
    #   - construct the student,
    #   - export the student to ONNX at --output.

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    LOG.warning(
        "train_distill.py is a scaffold. Implement dataset loaders + "
        "teacher forward hooks + student loss, then export ONNX to %s.",
        output_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

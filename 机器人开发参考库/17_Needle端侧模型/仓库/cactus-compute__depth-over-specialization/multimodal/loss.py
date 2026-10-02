"""Contrastive loss for multimodal encoders."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


class ContrastiveLoss(nn.Module):
    def __init__(self) -> None:
        super().__init__()

    def forward(self, a: Tensor, b: Tensor, logit_scale: Tensor) -> Tensor:
        if a.shape != b.shape or a.ndim != 2:
            raise ValueError(
                f"Expected matching 2D tensors, got {a.shape} and {b.shape}"
            )

        batch_size = a.shape[0]

        a = F.normalize(a, dim=1)
        b = F.normalize(b, dim=1)

        logits = logit_scale * (a @ b.T)

        labels = torch.arange(batch_size, device=logits.device)

        loss_a_to_b = F.cross_entropy(logits, labels)
        loss_b_to_a = F.cross_entropy(logits.T, labels)

        return (loss_a_to_b + loss_b_to_a) / 2

"""Image preprocessor: patch embedding with CLS token (ViT-style)."""

import torch
import torch.nn as nn
from torch import Tensor


class ImageEmbedding(nn.Module):
    def __init__(self, in_channels: int, patch_size: int, d_model: int) -> None:
        super().__init__()
        self.patch_embedding = nn.Conv2d(
            in_channels,
            d_model,
            kernel_size=patch_size,
            stride=patch_size,
        )

    def forward(self, images: Tensor) -> Tensor:
        return self.patch_embedding(images).flatten(2).transpose(1, 2)


class ImagePreprocessor(nn.Module):
    def __init__(
        self,
        patch_size: int,
        d_model: int,
        image_size: int,
        dropout: float,
        in_channels: int = 3,
    ) -> None:
        super().__init__()
        assert (
            image_size % patch_size == 0
        ), "image_size must be divisible by patch_size"
        self.embedding = ImageEmbedding(
            in_channels=in_channels, patch_size=patch_size, d_model=d_model
        )
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.dropout = nn.Dropout(dropout)

    def forward(self, images: Tensor) -> Tensor:
        batch_size = images.shape[0]
        embedding = self.embedding(images)

        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        embedding = torch.cat([cls_tokens, embedding], dim=1)
        return self.dropout(embedding)

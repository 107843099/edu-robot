"""Audio preprocessor: mel spectrogram patch embedding with CLS token."""

import torch
import torch.nn as nn
from torch import Tensor


class AudioEmbedding(nn.Module):
    def __init__(
        self, in_channels: int, patch_size: tuple[int, int], d_model: int
    ) -> None:
        super().__init__()
        self.patch_size = patch_size
        self.patch_embedding = nn.Conv2d(
            in_channels,
            d_model,
            kernel_size=patch_size,
            stride=patch_size,
        )

    def forward(self, audio: Tensor) -> Tensor:
        return self.patch_embedding(audio).flatten(2).transpose(1, 2)


class AudioPreprocessor(nn.Module):
    def __init__(
        self,
        patch_size: tuple[int, int],
        d_model: int,
        n_mels: int,
        n_frames: int,
        dropout: float,
        in_channels: int = 1,
    ) -> None:
        super().__init__()
        patch_size_freq, patch_size_time = patch_size
        assert (
            n_mels % patch_size_freq == 0
        ), "n_mels must be divisible by patch_size[0]"
        assert (
            n_frames % patch_size_time == 0
        ), "n_frames must be divisible by patch_size[1]"
        self.embedding = AudioEmbedding(
            in_channels=in_channels, patch_size=patch_size, d_model=d_model
        )
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.dropout = nn.Dropout(dropout)

    def forward(self, audio: Tensor) -> Tensor:
        batch_size = audio.shape[0]
        embedding = self.embedding(audio)

        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        embedding = torch.cat([cls_tokens, embedding], dim=1)
        return self.dropout(embedding)

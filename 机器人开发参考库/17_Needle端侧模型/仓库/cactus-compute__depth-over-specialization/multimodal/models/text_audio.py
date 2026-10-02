"""Text-Audio models (shared or separate encoders)."""

import math
import torch
import torch.nn as nn
from torch import Tensor
from ..preprocessors.text_preprocessor import TextPreprocessor
from ..preprocessors.audio_preprocessor import AudioPreprocessor
from ..transformer import TransformerEncoder


class SharedTA(nn.Module):
    """Shared transformer for both text and audio."""

    def __init__(
        self,
        vocab_size: int,
        audio_patch_size: tuple[int, int],
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float,
        projection_dim: int,
        max_seq_length: int,
        n_mels: int,
        n_frames: int,
    ) -> None:
        super().__init__()
        self.text_preprocessor = TextPreprocessor(
            vocab_size=vocab_size,
            d_model=d_model,
            dropout=dropout,
        )
        self.audio_preprocessor = AudioPreprocessor(
            patch_size=audio_patch_size,
            d_model=d_model,
            n_mels=n_mels,
            n_frames=n_frames,
            dropout=dropout,
        )
        num_audio_patches = (n_mels // audio_patch_size[0]) * (
            n_frames // audio_patch_size[1]
        ) + 1
        max_positions = max(max_seq_length, num_audio_patches)
        self.transformer = TransformerEncoder(
            d_model=d_model,
            nhead=nhead,
            d_hid=d_hid,
            nlayers=nlayers,
            dropout=dropout,
            max_position_embeddings=max_positions,
        )
        self.text_projector = nn.Linear(d_model, projection_dim)
        self.audio_projector = nn.Linear(d_model, projection_dim)
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1 / 0.07))

    def encode_text(self, input_ids: Tensor, attention_mask: Tensor) -> Tensor:
        embedded_text, extended_mask = self.text_preprocessor(input_ids, attention_mask)
        transformer_output = self.transformer(
            embedded_text, attention_mask=extended_mask
        )
        pooled = transformer_output[:, 0]
        return self.text_projector(pooled)

    def encode_audio(self, audio: Tensor) -> Tensor:
        embedded_audio = self.audio_preprocessor(audio)
        transformer_output = self.transformer(embedded_audio)
        pooled = transformer_output[:, 0]
        return self.audio_projector(pooled)


class SeparateTA(nn.Module):
    """Separate transformers for text and audio."""

    def __init__(
        self,
        vocab_size: int,
        audio_patch_size: tuple[int, int],
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float,
        projection_dim: int,
        n_mels: int = 80,
        n_frames: int = 3000,
        max_seq_length: int = 77,
    ) -> None:
        super().__init__()
        # Text
        self.text_preprocessor = TextPreprocessor(
            vocab_size=vocab_size,
            d_model=d_model,
            dropout=dropout,
        )
        self.text_transformer = TransformerEncoder(
            d_model=d_model,
            nhead=nhead,
            d_hid=d_hid,
            nlayers=nlayers,
            dropout=dropout,
            max_position_embeddings=max_seq_length,
        )
        self.text_projector = nn.Linear(d_model, projection_dim)

        # Audio
        self.audio_preprocessor = AudioPreprocessor(
            patch_size=audio_patch_size,
            d_model=d_model,
            n_mels=n_mels,
            n_frames=n_frames,
            dropout=dropout,
        )
        num_audio_patches = (n_mels // audio_patch_size[0]) * (
            n_frames // audio_patch_size[1]
        ) + 1
        self.audio_transformer = TransformerEncoder(
            d_model=d_model,
            nhead=nhead,
            d_hid=d_hid,
            nlayers=nlayers,
            dropout=dropout,
            max_position_embeddings=num_audio_patches,
        )
        self.audio_projector = nn.Linear(d_model, projection_dim)
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1 / 0.07))

    def encode_text(self, input_ids: Tensor, attention_mask: Tensor) -> Tensor:
        embedded_text, extended_mask = self.text_preprocessor(input_ids, attention_mask)
        transformer_output = self.text_transformer(
            embedded_text, attention_mask=extended_mask
        )
        pooled = transformer_output[:, 0]
        return self.text_projector(pooled)

    def encode_audio(self, audio: Tensor) -> Tensor:
        embedded_audio = self.audio_preprocessor(audio)
        transformer_output = self.audio_transformer(embedded_audio)
        pooled = transformer_output[:, 0]
        return self.audio_projector(pooled)

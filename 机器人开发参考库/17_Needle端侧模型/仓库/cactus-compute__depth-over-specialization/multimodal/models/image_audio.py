"""Image-Audio models (shared or separate encoders)."""

import math
import torch
import torch.nn as nn
from torch import Tensor
from ..preprocessors.image_preprocessor import ImagePreprocessor
from ..preprocessors.audio_preprocessor import AudioPreprocessor
from ..transformer import TransformerEncoder


class SharedIA(nn.Module):
    """Shared transformer for both image and audio."""

    def __init__(
        self,
        patch_size: int,
        audio_patch_size: tuple[int, int],
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float,
        projection_dim: int,
        image_size: int,
        n_mels: int,
        n_frames: int,
    ) -> None:
        super().__init__()
        self.image_preprocessor = ImagePreprocessor(
            patch_size=patch_size,
            d_model=d_model,
            image_size=image_size,
            dropout=dropout,
        )
        self.audio_preprocessor = AudioPreprocessor(
            patch_size=audio_patch_size,
            d_model=d_model,
            n_mels=n_mels,
            n_frames=n_frames,
            dropout=dropout,
        )
        num_image_patches = (image_size // patch_size) ** 2 + 1
        num_audio_patches = (n_mels // audio_patch_size[0]) * (
            n_frames // audio_patch_size[1]
        ) + 1
        max_positions = max(num_image_patches, num_audio_patches)
        self.transformer = TransformerEncoder(
            d_model=d_model,
            nhead=nhead,
            d_hid=d_hid,
            nlayers=nlayers,
            dropout=dropout,
            max_position_embeddings=max_positions,
        )
        self.image_projector = nn.Linear(d_model, projection_dim)
        self.audio_projector = nn.Linear(d_model, projection_dim)
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1 / 0.07))

    def encode_image(self, images: Tensor) -> Tensor:
        embedded_image = self.image_preprocessor(images)
        transformer_output = self.transformer(embedded_image)
        pooled = transformer_output[:, 0]
        return self.image_projector(pooled)

    def encode_audio(self, audio: Tensor) -> Tensor:
        embedded_audio = self.audio_preprocessor(audio)
        transformer_output = self.transformer(embedded_audio)
        pooled = transformer_output[:, 0]
        return self.audio_projector(pooled)


class SeparateIA(nn.Module):
    """Separate transformers for image and audio."""

    def __init__(
        self,
        patch_size: int,
        audio_patch_size: tuple[int, int],
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float,
        projection_dim: int,
        image_size: int = 224,
        n_mels: int = 80,
        n_frames: int = 1000,
    ) -> None:
        super().__init__()
        # Image
        self.image_preprocessor = ImagePreprocessor(
            patch_size=patch_size,
            d_model=d_model,
            image_size=image_size,
            dropout=dropout,
        )
        num_image_patches = (image_size // patch_size) ** 2 + 1
        self.image_transformer = TransformerEncoder(
            d_model=d_model,
            nhead=nhead,
            d_hid=d_hid,
            nlayers=nlayers,
            dropout=dropout,
            max_position_embeddings=num_image_patches,
        )
        self.image_projector = nn.Linear(d_model, projection_dim)

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

    def encode_image(self, images: Tensor) -> Tensor:
        embedded_image = self.image_preprocessor(images)
        transformer_output = self.image_transformer(embedded_image)
        pooled = transformer_output[:, 0]
        return self.image_projector(pooled)

    def encode_audio(self, audio: Tensor) -> Tensor:
        embedded_audio = self.audio_preprocessor(audio)
        transformer_output = self.audio_transformer(embedded_audio)
        pooled = transformer_output[:, 0]
        return self.audio_projector(pooled)

"""Text-Image models (shared or separate encoders)."""

import math
import torch
import torch.nn as nn
from torch import Tensor
from ..preprocessors.text_preprocessor import TextPreprocessor
from ..preprocessors.image_preprocessor import ImagePreprocessor
from ..transformer import TransformerEncoder


class SharedTI(nn.Module):
    """Shared transformer for both text and image."""

    def __init__(
        self,
        vocab_size: int,
        patch_size: int,
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float,
        projection_dim: int,
        max_seq_length: int,
        image_size: int,
    ) -> None:
        super().__init__()
        self.text_preprocessor = TextPreprocessor(
            vocab_size=vocab_size,
            d_model=d_model,
            dropout=dropout,
        )
        self.image_preprocessor = ImagePreprocessor(
            patch_size=patch_size,
            d_model=d_model,
            image_size=image_size,
            dropout=dropout,
        )
        num_image_patches = (image_size // patch_size) ** 2 + 1
        max_positions = max(max_seq_length, num_image_patches)
        self.transformer = TransformerEncoder(
            d_model=d_model,
            nhead=nhead,
            d_hid=d_hid,
            nlayers=nlayers,
            dropout=dropout,
            max_position_embeddings=max_positions,
        )
        self.text_projector = nn.Linear(d_model, projection_dim)
        self.image_projector = nn.Linear(d_model, projection_dim)
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1 / 0.07))

    def encode_text(self, input_ids: Tensor, attention_mask: Tensor) -> Tensor:
        embedded_text, extended_mask = self.text_preprocessor(input_ids, attention_mask)
        transformer_output = self.transformer(
            embedded_text, attention_mask=extended_mask
        )
        pooled = transformer_output[:, 0]
        return self.text_projector(pooled)

    def encode_image(self, images: Tensor) -> Tensor:
        embedded_image = self.image_preprocessor(images)
        transformer_output = self.transformer(embedded_image)
        pooled = transformer_output[:, 0]
        return self.image_projector(pooled)


class SeparateTI(nn.Module):
    """Separate transformers for text and image."""

    def __init__(
        self,
        vocab_size: int,
        patch_size: int,
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float,
        projection_dim: int,
        image_size: int = 224,
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
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1 / 0.07))

    def encode_text(self, input_ids: Tensor, attention_mask: Tensor) -> Tensor:
        embedded_text, extended_mask = self.text_preprocessor(input_ids, attention_mask)
        transformer_output = self.text_transformer(
            embedded_text, attention_mask=extended_mask
        )
        pooled = transformer_output[:, 0]
        return self.text_projector(pooled)

    def encode_image(self, images: Tensor) -> Tensor:
        embedded_image = self.image_preprocessor(images)
        transformer_output = self.image_transformer(embedded_image)
        pooled = transformer_output[:, 0]
        return self.image_projector(pooled)

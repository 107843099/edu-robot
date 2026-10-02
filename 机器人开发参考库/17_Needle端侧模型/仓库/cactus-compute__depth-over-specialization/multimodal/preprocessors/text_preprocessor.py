"""Text preprocessor: embed tokens and prepend CLS token."""

import torch
import torch.nn as nn
from torch import Tensor


class TextEmbedding(nn.Module):
    def __init__(self, vocab_size: int, d_model: int) -> None:
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, d_model)

    def forward(self, input_ids: Tensor) -> Tensor:
        return self.token_embedding(input_ids)


class TextPreprocessor(nn.Module):
    def __init__(self, vocab_size: int, d_model: int, dropout: float) -> None:
        super().__init__()
        self.embedding = TextEmbedding(vocab_size=vocab_size, d_model=d_model)
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.dropout = nn.Dropout(dropout)

    def forward(
        self, input_ids: Tensor, attention_mask: Tensor
    ) -> tuple[Tensor, Tensor]:
        batch_size = input_ids.shape[0]
        embedding = self.embedding(input_ids)

        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        embedding = torch.cat([cls_tokens, embedding], dim=1)
        embedding = self.dropout(embedding)

        x_mask = torch.ones(
            batch_size, 1, device=attention_mask.device, dtype=attention_mask.dtype
        )
        x_mask = torch.cat([x_mask, attention_mask], dim=1)
        return embedding, x_mask

"""Transformer encoder with RoPE, RMSNorm, and gated MLP.

Based on: https://github.com/HenryNdubuaku/pete/blob/main/src/transformer.py
"""

import math
import torch
from torch import nn


class MLP(nn.Module):
    """
    Implements a decomposed linear layer with an intermediate activation.
    """

    def __init__(self, in_features, intermediate):
        super(MLP, self).__init__()
        self.w1 = nn.Linear(in_features, intermediate * 2)
        self.w2 = nn.Linear(intermediate, in_features)

    def forward(self, x):
        x = self.w1(x)
        x, gate = x.chunk(2, dim=-1)
        x = x * nn.functional.gelu(gate)
        return self.w2(x)


class RMSNorm(nn.Module):
    """
    Implements Root Mean Square Layer Normalization.
    """

    def __init__(self, dim: int, eps: float = 1e-6):
        super(RMSNorm, self).__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor, dim=-1) -> torch.Tensor:
        rms = torch.sqrt(torch.mean(x**2, dim=dim, keepdim=True) + self.eps)
        x_normalized = x / rms
        return self.weight * x_normalized


class RotaryPositionEncoding(nn.Module):
    """
    Implements Rotary Position Encoding for attention mechanism.
    """

    def __init__(self, dim, max_position_embeddings=2048, base=10000):
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)
        self.max_position_embeddings = max_position_embeddings

    def forward(self, x, seq_len=None):
        if seq_len is None:
            seq_len = x.shape[1]
        if seq_len > self.max_position_embeddings:
            raise ValueError(
                f"Sequence length {seq_len} exceeds maximum length {self.max_position_embeddings}"
            )

        t = torch.arange(seq_len, device=x.device).type_as(self.inv_freq)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)

        cos = emb.cos()[None, None, :, :]  # (1, 1, seq, dim)
        sin = emb.sin()[None, None, :, :]
        return cos, sin

    def apply_rotary_pos_emb(self, x, cos, sin):
        # x: (batch, heads, seq, head_dim)
        x1 = x[..., ::2]
        x2 = x[..., 1::2]
        x_rot = torch.stack((-x2, x1), dim=-1).flatten(-2)
        return (x * cos) + (x_rot * sin)


class Layer(nn.Module):
    """
    Implements a single transformer layer with self-attention and feed-forward network.
    """

    def __init__(
        self,
        d_model,
        num_attention_heads,
        intermediate_size,
        attention_probs_dropout_prob,
        max_position_embeddings,
    ):
        super(Layer, self).__init__()

        self.d_model = d_model
        self.num_attention_heads = num_attention_heads
        self.attention_head_size = int(d_model / num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.projection = nn.Linear(d_model, d_model * 3)

        self.dropout = nn.Dropout(attention_probs_dropout_prob)
        self.attn_out = nn.Linear(d_model, d_model)
        self.ln1 = RMSNorm(d_model)
        self.mlp = MLP(d_model, intermediate_size)
        self.ln2 = RMSNorm(d_model)
        self.rope = RotaryPositionEncoding(
            self.attention_head_size, max_position_embeddings
        )

    def split_heads(self, tensor, num_heads, attention_head_size):
        new_shape = tensor.size()[:-1] + (num_heads, attention_head_size)
        tensor = tensor.view(*new_shape)
        return tensor.permute(0, 2, 1, 3)

    def merge_heads(self, tensor, num_heads, attention_head_size):
        tensor = tensor.permute(0, 2, 1, 3).contiguous()
        new_shape = tensor.size()[:-2] + (num_heads * attention_head_size,)
        return tensor.view(new_shape)

    def attn(self, q, k, v, attention_mask):
        dot_product = torch.matmul(q, k.transpose(-1, -2))
        scaled_dot_product = dot_product / math.sqrt(self.attention_head_size)

        if attention_mask is not None:
            attention_mask = attention_mask == 1
            attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
            scaled_dot_product = torch.where(
                attention_mask,
                scaled_dot_product,
                torch.tensor(float("-inf"), device=q.device),
            )

        attention_weights = nn.functional.softmax(scaled_dot_product, dim=-1)
        attention_weights = self.dropout(attention_weights)
        return torch.matmul(attention_weights, v)

    def forward(self, x, attention_mask):
        residual = x

        q, k, v = self.projection(x).chunk(3, dim=-1)

        q = self.split_heads(q, self.num_attention_heads, self.attention_head_size)
        k = self.split_heads(k, self.num_attention_heads, self.attention_head_size)
        v = self.split_heads(v, self.num_attention_heads, self.attention_head_size)

        # Apply RoPE to queries and keys
        cos, sin = self.rope(q, seq_len=x.shape[1])
        q = self.rope.apply_rotary_pos_emb(q, cos, sin)
        k = self.rope.apply_rotary_pos_emb(k, cos, sin)

        attended_outputs = self.attn(q, k, v, attention_mask)
        attended_outputs = self.merge_heads(
            attended_outputs, self.num_attention_heads, self.attention_head_size
        )
        attended_outputs = self.attn_out(attended_outputs)
        attended_outputs = self.dropout(attended_outputs)

        x = self.ln1(attended_outputs + residual)

        residual = x
        x = self.mlp(x)
        x = self.dropout(x)
        x = self.ln2(x + residual)

        return x


class TransformerEncoder(nn.Module):
    def __init__(
        self,
        d_model: int,
        nhead: int,
        d_hid: int,
        nlayers: int,
        dropout: float = 0.1,
        max_position_embeddings: int = 2048,
    ):
        super().__init__()
        self.layers = nn.ModuleList(
            [
                Layer(
                    d_model=d_model,
                    num_attention_heads=nhead,
                    intermediate_size=d_hid,
                    attention_probs_dropout_prob=dropout,
                    max_position_embeddings=max_position_embeddings,
                )
                for _ in range(nlayers)
            ]
        )

    def forward(self, x: torch.Tensor, attention_mask: torch.Tensor = None):
        for layer in self.layers:
            x = layer(x, attention_mask)
        return x

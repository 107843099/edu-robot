"""Cactus INT4 / INT8 weight quantization (PyTorch fake-quant reference).

Mirrors the production quantize paths in cactus/python/src/tensor_io.py
(INT8: line 203, INT4: line 287) and the dequantize side in
cactus/cactus/kernel/kernel_quants.cpp + kernel_utils.h.

Per-row, per-group (group_size=32) symmetric absmax, parameterized by bits:
    q_max     = 2**(bits-1) - 1                        #   7 for int4, 127 for int8
    q_min     = -2**(bits-1)                           #  -8 for int4, -128 for int8
    scale_f32 = max(absmax / q_max, 1e-10)             # quant-time scale
    q         = clip(round(W / scale_f32), q_min, q_max)
    scale_f16 = fp16(scale_f32)                        # stored fp16 scale
    W_dq      = q * scale_f16                          # what the kernel consumes

Cactus uses fp32 scales at quantize time and stores them in fp16 for the
runtime kernel to load; the dequant arithmetic therefore uses fp16 scales.
Both facets are reproduced because the fp16 cast does change output bits.

The storage-layer concerns (K-padding to 32, N-padding to INTERLEAVE_BLOCK,
planar nibble packing, SIMD interleaving) are numerics-preserving and
aren't reproduced here.

Returns the dequantized weight with the input's dtype/device so callers
can drop it into existing model-replacement plumbing.

Production cactus uses INT4 for transformer linears and INT8 for the big
token-indexed embeddings (token_embeddings, embed_tokens_per_layer) — the
dispatch is in tensor_io.py::save_tensor_with_header.
"""
from __future__ import annotations

import torch

GROUP_SIZE = 32


def cactus_quantize(W: torch.Tensor, bits: int, group_size: int = GROUP_SIZE) -> torch.Tensor:
    """Return dequantized W_dq matching cactus INTN (N=bits) runtime arithmetic."""
    if W.ndim != 2:
        raise ValueError(f"cactus_quantize expects a 2D tensor, got {tuple(W.shape)}")
    if bits not in (4, 8):
        raise ValueError(f"cactus_quantize supports bits ∈ {{4, 8}}, got {bits}")

    q_max = (1 << (bits - 1)) - 1     # 7 or 127
    q_min = -(1 << (bits - 1))        # -8 or -128

    orig_dtype = W.dtype
    N, K = W.shape

    # K-pad to multiple of group_size with zeros (truncated back at return).
    pad_k = (-K) % group_size
    if pad_k:
        W = torch.nn.functional.pad(W, (0, pad_k))

    W_f = W.to(torch.float32)
    groups = W_f.view(N, -1, group_size)                              # (N, G, gs)

    absmax = groups.abs().amax(dim=-1, keepdim=True)                  # (N, G, 1)
    scales_f32 = (absmax / q_max).clamp_min(1e-10)                    # quant-time, fp32
    scales_f16 = scales_f32.to(torch.float16).to(torch.float32)       # runtime fp16 cast

    q = torch.round(groups / scales_f32).clamp_(q_min, q_max)
    W_dq = (q * scales_f16).reshape(N, -1)[:, :K]

    return W_dq.to(orig_dtype)


def cactus_int4_quantize(W: torch.Tensor, group_size: int = GROUP_SIZE) -> torch.Tensor:
    return cactus_quantize(W, bits=4, group_size=group_size)


def cactus_int8_quantize(W: torch.Tensor, group_size: int = GROUP_SIZE) -> torch.Tensor:
    return cactus_quantize(W, bits=8, group_size=group_size)

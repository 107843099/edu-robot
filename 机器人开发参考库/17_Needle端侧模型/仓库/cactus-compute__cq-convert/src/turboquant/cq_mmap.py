from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import torch

from gemma_turboquant import SharedTransformBank


MAGIC = 0x54434143
ALIGNMENT = 32
FLAG_ORTHOGONAL_ROTATION = 1 << 1

PRECISION_INT8 = 0
PRECISION_FP16 = 1
PRECISION_FP32 = 2
PRECISION_CQ = {1: 3, 2: 4, 3: 5, 4: 6}

HEADER_STRUCT = struct.Struct("<III I QQQQ I Q Q I I Q")
HEADER_BYTES = HEADER_STRUCT.size


@dataclass
class CQTensor:
    source_name: str
    output_name: str
    bits: int
    shape: tuple[int, int]
    group_size: int
    codebook: torch.Tensor
    input_scale: torch.Tensor
    input_scale_recip: torch.Tensor
    norms: torch.Tensor
    indices: torch.Tensor
    rotation_family: Literal["hadamard", "orthogonal"]
    left_signs: torch.Tensor | None = None
    right_signs: torch.Tensor | None = None
    permutation: torch.Tensor | None = None
    rotation: torch.Tensor | None = None

    @property
    def n(self) -> int:
        return int(self.shape[0])

    @property
    def k(self) -> int:
        return int(self.shape[1])

    @property
    def num_groups(self) -> int:
        return self.k // self.group_size


def _align(f) -> None:
    pad = (-f.tell()) % ALIGNMENT
    if pad:
        f.write(b"\x00" * pad)


def _fp16_bytes(t: torch.Tensor) -> bytes:
    return t.detach().cpu().contiguous().to(torch.float16).numpy().tobytes()


def _int8_bytes(t: torch.Tensor) -> bytes:
    return t.detach().cpu().contiguous().to(torch.int8).numpy().tobytes()


def _u32_bytes(t: torch.Tensor) -> bytes:
    return t.detach().cpu().contiguous().to(torch.uint32).numpy().tobytes()


def hadamard_metadata(group_size: int, seed: int = 1234, variant: int = 0) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed + 17 * group_size + 7919 * int(variant))
    left = (2 * torch.randint(0, 2, (group_size,), generator=gen, dtype=torch.int64) - 1).to(torch.int8)
    right = (2 * torch.randint(0, 2, (group_size,), generator=gen, dtype=torch.int64) - 1).to(torch.int8)
    perm = torch.randperm(group_size, generator=gen).to(torch.uint32)
    return left, right, perm


def pack_indices_le(indices: torch.Tensor, bits: int) -> bytes:
    flat = indices.detach().cpu().contiguous().view(-1).to(torch.uint8).numpy()
    if flat.size and int(flat.max()) >= (1 << bits):
        raise ValueError(f"indices out of range for {bits}-bit CQ")
    if flat.size == 0:
        return b""

    if bits == 4:
        if flat.size % 2:
            flat = np.pad(flat, (0, 1), constant_values=0)
        pairs = flat.reshape(-1, 2)
        return (pairs[:, 0] | (pairs[:, 1] << 4)).astype(np.uint8, copy=False).tobytes()

    if bits == 2:
        pad = (-flat.size) % 4
        if pad:
            flat = np.pad(flat, (0, pad), constant_values=0)
        q = flat.reshape(-1, 4)
        return (q[:, 0] | (q[:, 1] << 2) | (q[:, 2] << 4) | (q[:, 3] << 6)).astype(np.uint8, copy=False).tobytes()

    if bits == 1:
        pad = (-flat.size) % 8
        if pad:
            flat = np.pad(flat, (0, pad), constant_values=0)
        q = flat.reshape(-1, 8)
        out = np.zeros(q.shape[0], dtype=np.uint8)
        for shift in range(8):
            out |= (q[:, shift] & 1) << shift
        return out.tobytes()

    if bits != 3:
        raise ValueError(f"unsupported CQ bits: {bits}")

    out = np.zeros((flat.size * bits + 7) // 8, dtype=np.uint8)
    bitpos = np.arange(flat.size, dtype=np.uint64) * bits
    bytepos = bitpos // 8
    shift = (bitpos % 8).astype(np.uint8)
    vals = flat & 0x07
    np.bitwise_or.at(out, bytepos, (vals << shift).astype(np.uint8))
    spill = shift > 5
    if np.any(spill):
        np.bitwise_or.at(out, bytepos[spill] + 1, (vals[spill] >> (8 - shift[spill])).astype(np.uint8))
    return out.tobytes()


def _metadata_blob(cq: CQTensor) -> bytes:
    parts = [
        _fp16_bytes(cq.codebook.reshape(-1)),
        _fp16_bytes(cq.input_scale.reshape(-1)),
        _fp16_bytes(cq.input_scale_recip.reshape(-1)),
        _fp16_bytes(cq.norms.reshape(-1)),
    ]
    if cq.rotation_family == "hadamard":
        assert cq.left_signs is not None and cq.right_signs is not None and cq.permutation is not None
        parts.extend([
            _int8_bytes(cq.left_signs.reshape(-1)),
            _int8_bytes(cq.right_signs.reshape(-1)),
            _u32_bytes(cq.permutation.reshape(-1)),
        ])
    else:
        assert cq.rotation is not None
        parts.append(_fp16_bytes(cq.rotation.reshape(-1)))
    return b"".join(parts)


def expected_scales_bytes(cq: CQTensor) -> int:
    n, k = cq.shape
    cb = (1 << cq.bits) * 2
    if cq.rotation_family == "hadamard":
        return cb + k * 2 + k * 2 + n * cq.num_groups * 2 + cq.group_size + cq.group_size + cq.group_size * 4
    return cb + k * 2 + k * 2 + n * 2 + k * k * 2


def packed_data_bytes(cq: CQTensor) -> int:
    packed_group_bytes = math.ceil(cq.group_size * cq.bits / 8)
    return cq.n * cq.num_groups * packed_group_bytes


def write_cq_weights(path: Path, cq: CQTensor) -> dict:
    validate_cq(cq)
    meta = _metadata_blob(cq)
    if len(meta) != expected_scales_bytes(cq):
        raise ValueError(f"metadata size mismatch for {cq.output_name}: {len(meta)} != {expected_scales_bytes(cq)}")

    data = pack_indices_le(cq.indices, cq.bits)
    if len(data) != packed_data_bytes(cq):
        raise ValueError(f"packed index size mismatch for {cq.output_name}: {len(data)} != {packed_data_bytes(cq)}")

    flags = FLAG_ORTHOGONAL_ROTATION if cq.rotation_family == "orthogonal" else 0
    header = HEADER_STRUCT.pack(
        MAGIC,
        flags,
        ALIGNMENT,
        2,
        cq.n,
        cq.k,
        0,
        0,
        PRECISION_CQ[cq.bits],
        len(data),
        len(meta),
        cq.group_size,
        cq.num_groups,
        cq.n,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(header)
        _align(f)
        f.write(meta)
        _align(f)
        f.write(data)
    return inspect_weights(path)


def write_fp16_weights(path: Path, tensor: torch.Tensor) -> dict:
    t = tensor.detach().cpu().contiguous().to(torch.float16)
    if t.ndim == 0:
        t = t.reshape(1)
    dims = list(t.shape[:4]) + [0] * (4 - min(t.ndim, 4))
    data = t.numpy().tobytes()
    header = HEADER_STRUCT.pack(
        MAGIC, 0, ALIGNMENT, int(t.ndim),
        int(dims[0]), int(dims[1]), int(dims[2]), int(dims[3]),
        PRECISION_FP16, len(data), 0, 0, 0, int(t.shape[0]) if t.ndim else 0,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(header)
        _align(f)
        f.write(data)
    return inspect_weights(path)


def inspect_weights(path: Path) -> dict:
    with path.open("rb") as f:
        raw = f.read(HEADER_BYTES)
    fields = HEADER_STRUCT.unpack(raw)
    return {
        "magic": fields[0],
        "flags": fields[1],
        "alignment": fields[2],
        "ndim": fields[3],
        "shape": [fields[4], fields[5], fields[6], fields[7]][: fields[3]],
        "precision": fields[8],
        "data_bytes": fields[9],
        "scales_bytes": fields[10],
        "group_size": fields[11],
        "num_groups": fields[12],
        "original_N": fields[13],
        "file_bytes": path.stat().st_size,
    }


def validate_cq(cq: CQTensor) -> None:
    if cq.bits not in PRECISION_CQ:
        raise ValueError(f"unsupported CQ bits: {cq.bits}")
    n, k = cq.shape
    if cq.group_size <= 0 or k != cq.group_size * cq.num_groups:
        raise ValueError(f"K must equal group_size * num_groups for {cq.output_name}")
    if tuple(cq.indices.shape) != (n, cq.num_groups, cq.group_size):
        raise ValueError(f"bad indices shape for {cq.output_name}: {tuple(cq.indices.shape)}")
    if cq.indices.numel() and int(cq.indices.max()) >= (1 << cq.bits):
        raise ValueError(f"indices exceed codebook for {cq.output_name}")
    if cq.rotation_family == "hadamard":
        assert cq.left_signs is not None and cq.right_signs is not None and cq.permutation is not None
        if not torch.all((cq.left_signs == 1) | (cq.left_signs == -1)):
            raise ValueError(f"bad left signs for {cq.output_name}")
        if not torch.all((cq.right_signs == 1) | (cq.right_signs == -1)):
            raise ValueError(f"bad right signs for {cq.output_name}")
        if sorted(cq.permutation.cpu().tolist()) != list(range(cq.group_size)):
            raise ValueError(f"bad permutation for {cq.output_name}")
    else:
        if cq.num_groups != 1 or cq.group_size != k:
            raise ValueError(f"orthogonal CQ must use one full-row group for {cq.output_name}")
        assert cq.rotation is not None
        if tuple(cq.rotation.shape) != (k, k):
            raise ValueError(f"bad rotation shape for {cq.output_name}: {tuple(cq.rotation.shape)}")


@torch.no_grad()
def quantize_weight_to_cq(
    weight: torch.Tensor,
    *,
    source_name: str,
    output_name: str,
    bits: int,
    bank: SharedTransformBank,
    group_size: int | None,
    rotation_family: Literal["hadamard", "orthogonal"],
    input_scale: torch.Tensor | None,
    device: str = "cuda",
    batch: int = 256,
) -> CQTensor:
    weight = weight.detach().float().cpu().contiguous()
    n, k = weight.shape
    gs = k if group_size is None or group_size <= 0 or group_size >= k else int(group_size)
    if k % gs != 0:
        raise ValueError(f"{source_name}: K={k} must be divisible by group_size={gs}")
    num_groups = k // gs
    scale = input_scale.detach().float().cpu().contiguous() if input_scale is not None else torch.ones(k)
    scale = scale.clamp_min(1e-6)
    scale_gpu = scale.to(device=device, dtype=torch.float32)
    rotation = bank.rotation(gs, family=rotation_family).to(device=device, dtype=torch.float32)
    codebook = bank.codebook(gs, bits).to(device=device, dtype=torch.float32)

    all_norms = torch.empty(n, num_groups, dtype=torch.float16)
    all_indices = torch.empty(n, num_groups, gs, dtype=torch.uint8)
    for start in range(0, n, batch):
        end = min(start + batch, n)
        w = weight[start:end].to(device=device, dtype=torch.float32) * scale_gpu.unsqueeze(0)
        groups = w.view(end - start, num_groups, gs)
        norms = groups.norm(dim=2).clamp_min(1e-8)
        unit = groups / norms.unsqueeze(-1)
        rotated = unit.view(-1, gs) @ rotation
        dists = (rotated.unsqueeze(-1) - codebook.view(1, 1, -1)).abs()
        idx = dists.argmin(dim=-1).to(torch.uint8).view(end - start, num_groups, gs)
        all_norms[start:end] = norms.detach().cpu().to(torch.float16)
        all_indices[start:end] = idx.detach().cpu()

    if rotation_family == "hadamard":
        left, right, perm = hadamard_metadata(gs, seed=bank.seed)
        return CQTensor(
            source_name=source_name,
            output_name=output_name,
            bits=bits,
            shape=(n, k),
            group_size=gs,
            codebook=codebook.cpu(),
            input_scale=scale,
            input_scale_recip=1.0 / scale,
            norms=all_norms,
            indices=all_indices,
            rotation_family="hadamard",
            left_signs=left,
            right_signs=right,
            permutation=perm,
        )

    return CQTensor(
        source_name=source_name,
        output_name=output_name,
        bits=bits,
        shape=(n, k),
        group_size=gs,
        codebook=codebook.cpu(),
        input_scale=scale,
        input_scale_recip=1.0 / scale,
        norms=all_norms,
        indices=all_indices,
        rotation_family="orthogonal",
        rotation=rotation.cpu(),
    )


@torch.no_grad()
def quantize_weight_to_cq_gptq(
    weight: torch.Tensor,
    *,
    source_name: str,
    output_name: str,
    bits: int,
    bank: SharedTransformBank,
    group_size: int,
    input_scale: torch.Tensor | None,
    h_inv: torch.Tensor | None,
    device: str = "cuda",
) -> CQTensor:
    """Quantize normal Hadamard CQ groups with GPTQ suffix correction.

    The emitted CQ artifacts are semantic native artifacts: the correction is
    applied to the working copy before each future group is quantized, but the
    disk representation remains ordinary row-major CQ groups.
    """
    weight = weight.detach().float().cpu().contiguous()
    n, k = weight.shape
    gs = int(group_size)
    if k % gs != 0:
        raise ValueError(f"{source_name}: K={k} must be divisible by group_size={gs}")
    num_groups = k // gs
    scale = input_scale.detach().float().cpu().contiguous() if input_scale is not None else torch.ones(k)
    scale = scale.clamp_min(1e-6)
    scale_gpu = scale.to(device=device, dtype=torch.float32)
    rotation = bank.rotation(gs, family="hadamard").to(device=device, dtype=torch.float32)
    h_gpu = h_inv.to(device=device, dtype=torch.float32) if h_inv is not None else None

    work = weight.to(device=device, dtype=torch.float32) * scale_gpu.unsqueeze(0)
    all_norms = torch.empty(n, num_groups, dtype=torch.float16)
    all_indices = torch.empty(n, num_groups, gs, dtype=torch.uint8)
    codebook_cache: dict[int, torch.Tensor] = {}

    for g in range(num_groups):
        start = g * gs
        stop = start + gs
        if bits not in codebook_cache:
            codebook_cache[bits] = bank.codebook(gs, bits).to(device=device, dtype=torch.float32)
        codebook = codebook_cache[bits]

        group = work[:, start:stop]
        norms = group.norm(dim=1).clamp_min(1e-8)
        unit = group / norms.unsqueeze(1)
        rotated = unit @ rotation
        idx = (rotated.unsqueeze(-1) - codebook.view(1, 1, -1)).abs().argmin(dim=-1)
        dq = codebook[idx]
        recon_scaled = (dq @ rotation.T) * norms.unsqueeze(1)

        if h_gpu is not None and stop < k:
            error = group - recon_scaled
            m_bb = h_gpu[start:stop, start:stop]
            m_bs = h_gpu[start:stop, stop:]
            try:
                chol = torch.linalg.cholesky(m_bb)
                update = torch.cholesky_solve(m_bs, chol, upper=False)
                work[:, stop:].sub_(error @ update)
            except Exception:
                pass

        all_norms[:, g] = norms.detach().cpu().to(torch.float16)
        all_indices[:, g, :] = idx.detach().cpu().to(torch.uint8)

    left, right, perm = hadamard_metadata(gs, seed=bank.seed)
    codebook_cpu = bank.codebook(gs, bits).cpu()
    del work, h_gpu, codebook_cache
    return CQTensor(
        source_name=source_name,
        output_name=output_name,
        bits=bits,
        shape=(n, k),
        group_size=gs,
        codebook=codebook_cpu,
        input_scale=scale,
        input_scale_recip=1.0 / scale,
        norms=all_norms,
        indices=all_indices,
        rotation_family="hadamard",
        left_signs=left,
        right_signs=right,
        permutation=perm,
    )


def write_manifest(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps({"tensors": rows}, indent=2), encoding="utf-8")

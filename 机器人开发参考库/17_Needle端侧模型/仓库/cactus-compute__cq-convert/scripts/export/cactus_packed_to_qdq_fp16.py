#!/usr/bin/env python3
"""Convert a cactus packed CQ `.weights` directory/tar into fp16 QDQ safetensors.

Example:
    python scripts/export/cactus_packed_to_qdq_fp16.py \
        outputs/cactus_cq_gptq_audio_tqh_tars/L4V4A4.tar \
        --out outputs/qdq_fp16/L4V4A4 \
        --force
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import torch
from safetensors.torch import save_file
from scipy.linalg import hadamard


CACTUS_MAGIC = b"CACT"
HEADER_SIZE = 84
ALIGNMENT_DEFAULT = 32
FLAG_ORTHOGONAL_ROTATION = 1 << 1

PRECISION_FP16 = 1
PRECISION_FP32 = 2
PRECISION_CQ = {3: 1, 4: 2, 5: 3, 6: 4}

CONFIG_FILES = {
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "tokenizer_config.txt",
    "special_tokens_map.json",
    "processor_config.json",
    "preprocessor_config.json",
    "chat_template.jinja",
    "tokenizer.model",
    "config.txt",
}


@dataclass(frozen=True)
class CactusHeader:
    path: Path
    flags: int
    alignment: int
    ndim: int
    dims: tuple[int, int, int, int]
    precision: int
    data_bytes: int
    scales_bytes: int
    group_size: int
    num_groups: int
    original_n: int

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(int(x) for x in self.dims[: self.ndim])

    @property
    def bits(self) -> int:
        if self.precision not in PRECISION_CQ:
            raise ValueError(f"{self.path}: precision {self.precision} is not CQ")
        return PRECISION_CQ[self.precision]


class ShardedSafetensorsWriter:
    def __init__(self, out_dir: Path, shard_size_bytes: int) -> None:
        self.out_dir = out_dir
        self.shard_size_bytes = int(shard_size_bytes)
        self.current: dict[str, torch.Tensor] = {}
        self.current_bytes = 0
        self.shards: list[tuple[Path, list[str]]] = []
        self.weight_map: dict[str, str] = {}
        self.total_size = 0

    def add(self, key: str, tensor: torch.Tensor) -> None:
        tensor = tensor.detach().cpu().contiguous()
        nbytes = tensor.numel() * tensor.element_size()
        if self.current and self.current_bytes + nbytes > self.shard_size_bytes:
            self.flush()
        self.current[key] = tensor
        self.current_bytes += nbytes
        self.total_size += nbytes
        if self.current_bytes >= self.shard_size_bytes:
            self.flush()

    def flush(self) -> None:
        if not self.current:
            return
        tmp_path = self.out_dir / f"model-{len(self.shards) + 1:05d}.safetensors"
        save_file(self.current, tmp_path)
        self.shards.append((tmp_path, sorted(self.current)))
        self.current = {}
        self.current_bytes = 0

    def close(self) -> None:
        self.flush()
        if len(self.shards) == 1:
            old, keys = self.shards[0]
            final = self.out_dir / "model.safetensors"
            old.rename(final)
            for key in keys:
                self.weight_map[key] = final.name
            return

        total = len(self.shards)
        for idx, (old, keys) in enumerate(self.shards, start=1):
            final = self.out_dir / f"model-{idx:05d}-of-{total:05d}.safetensors"
            old.rename(final)
            for key in keys:
                self.weight_map[key] = final.name
        index = {
            "metadata": {"total_size": str(self.total_size)},
            "weight_map": dict(sorted(self.weight_map.items())),
        }
        (self.out_dir / "model.safetensors.index.json").write_text(json.dumps(index, indent=2) + "\n")


def align_offset(offset: int, alignment: int) -> int:
    rem = offset % alignment
    return offset if rem == 0 else offset + alignment - rem


def safe_extract_tar(tar_path: Path, out_dir: Path) -> None:
    out_resolved = out_dir.resolve()
    with tarfile.open(tar_path) as tf:
        for member in tf.getmembers():
            target = (out_dir / member.name).resolve()
            if os.path.commonpath([str(out_resolved), str(target)]) != str(out_resolved):
                raise RuntimeError(f"refusing unsafe tar member path: {member.name}")
        tf.extractall(out_dir)


def materialize_input(input_path: Path, tmp_dir: Path | None) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if input_path.is_dir():
        return input_path, None
    if not tarfile.is_tarfile(input_path):
        raise ValueError(f"{input_path} is neither a directory nor a tar archive")
    tmp = tempfile.TemporaryDirectory(dir=str(tmp_dir) if tmp_dir else None)
    root = Path(tmp.name)
    safe_extract_tar(input_path, root)
    children = [p for p in root.iterdir() if not p.name.startswith(".")]
    return (children[0] if len(children) == 1 and children[0].is_dir() else root), tmp


def find_cactus_root(root: Path) -> Path:
    weights = [p for p in root.rglob("*.weights") if p.is_file()]
    if not weights:
        raise ValueError(f"no .weights files found under {root}")
    counts: dict[Path, int] = {}
    for path in weights:
        counts[path.parent] = counts.get(path.parent, 0) + 1
    return max(counts, key=counts.get)


def copy_config_files(src_root: Path, out_dir: Path) -> list[str]:
    copied: list[str] = []
    for path in src_root.rglob("*"):
        if path.is_file() and path.name in CONFIG_FILES:
            rel = path.relative_to(src_root)
            target = out_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied.append(str(rel))
    return sorted(set(copied))


def read_header(path: Path) -> CactusHeader:
    raw = path.read_bytes()[:HEADER_SIZE]
    if len(raw) != HEADER_SIZE:
        raise ValueError(f"{path}: too small for cactus header")
    if raw[:4] != CACTUS_MAGIC:
        raise ValueError(f"{path}: bad magic {raw[:4]!r}")
    fields = struct.unpack("<IIIQQQQIQQIIQ", raw[4:HEADER_SIZE])
    flags, alignment, ndim, d0, d1, d2, d3, precision, data_bytes, scales_bytes, group_size, num_groups, original_n = fields
    if ndim > 4:
        raise ValueError(f"{path}: invalid ndim={ndim}")
    if alignment <= 0:
        alignment = ALIGNMENT_DEFAULT
    return CactusHeader(path, flags, alignment, ndim, (d0, d1, d2, d3), precision, data_bytes, scales_bytes, group_size, num_groups, original_n)


def unpack_lsb_values(packed: np.ndarray, count: int, bits: int) -> np.ndarray:
    raw_bits = np.unpackbits(packed.astype(np.uint8, copy=False), bitorder="little")[: count * bits]
    raw_bits = raw_bits.reshape(count, bits)
    out = np.zeros(count, dtype=np.uint8)
    for bit in range(bits):
        out |= (raw_bits[:, bit].astype(np.uint8) << bit)
    return out


def dequantize_fp_file(path: Path, header: CactusHeader, out_dtype: torch.dtype) -> torch.Tensor:
    offset = align_offset(HEADER_SIZE, header.alignment)
    dtype = np.float16 if header.precision == PRECISION_FP16 else np.float32
    arr = np.fromfile(path, dtype=dtype, count=math.prod(header.shape), offset=offset)
    return torch.from_numpy(arr.reshape(header.shape).copy()).to(out_dtype)


def read_cq_payload(path: Path, header: CactusHeader) -> tuple[bytes, np.ndarray]:
    scales_offset = align_offset(HEADER_SIZE, header.alignment)
    data_offset = align_offset(scales_offset + header.scales_bytes, header.alignment)
    with path.open("rb") as f:
        f.seek(scales_offset)
        scales_blob = f.read(header.scales_bytes)
        f.seek(data_offset)
        packed = np.frombuffer(f.read(header.data_bytes), dtype=np.uint8).copy()
    return scales_blob, packed


def parse_normal_metadata(blob: bytes, header: CactusHeader) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    n, k = header.shape
    pos = 0
    codebook = np.frombuffer(blob, dtype=np.float16, count=1 << header.bits, offset=pos).astype(np.float32)
    pos += (1 << header.bits) * 2
    input_scale = np.frombuffer(blob, dtype=np.float16, count=k, offset=pos).astype(np.float32)
    pos += k * 2
    pos += k * 2
    norms = np.frombuffer(blob, dtype=np.float16, count=n * header.num_groups, offset=pos).astype(np.float32).reshape(n, header.num_groups)
    pos += n * header.num_groups * 2
    left = np.frombuffer(blob, dtype=np.int8, count=header.group_size, offset=pos).astype(np.float32)
    pos += header.group_size
    right = np.frombuffer(blob, dtype=np.int8, count=header.group_size, offset=pos).astype(np.float32)
    pos += header.group_size
    perm = np.frombuffer(blob, dtype="<u4", count=header.group_size, offset=pos).astype(np.int64)
    return (
        torch.from_numpy(codebook),
        torch.from_numpy(input_scale),
        torch.from_numpy(norms),
        torch.from_numpy(left),
        torch.from_numpy(right),
        torch.from_numpy(perm),
    )


def parse_orthogonal_metadata(blob: bytes, header: CactusHeader) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    n, k = header.shape
    pos = 0
    codebook = np.frombuffer(blob, dtype=np.float16, count=1 << header.bits, offset=pos).astype(np.float32)
    pos += (1 << header.bits) * 2
    input_scale = np.frombuffer(blob, dtype=np.float16, count=k, offset=pos).astype(np.float32)
    pos += k * 2
    pos += k * 2
    norms = np.frombuffer(blob, dtype=np.float16, count=n, offset=pos).astype(np.float32)
    pos += n * 2
    rotation = np.frombuffer(blob, dtype=np.float16, count=k * k, offset=pos).astype(np.float32).reshape(k, k)
    return torch.from_numpy(codebook), torch.from_numpy(input_scale), torch.from_numpy(norms), torch.from_numpy(rotation)


def dequantize_cq_file(path: Path, header: CactusHeader, out_dtype: torch.dtype, row_batch_size: int) -> torch.Tensor:
    if header.ndim != 2:
        raise ValueError(f"{path}: CQ tensors must be 2D, got shape={header.shape}")
    n, k = header.shape
    bits = header.bits
    scales_blob, packed = read_cq_payload(path, header)

    if header.flags & FLAG_ORTHOGONAL_ROTATION:
        if header.group_size != k or header.num_groups != 1:
            raise ValueError(f"{path}: orthogonal CQ expects group_size=K and num_groups=1")
        packed_group_bytes = math.ceil(k * bits / 8)
        expected = n * packed_group_bytes
        if header.data_bytes != expected:
            raise ValueError(f"{path}: data_bytes={header.data_bytes}, expected {expected}")
        codebook, input_scale, norms, rotation = parse_orthogonal_metadata(scales_blob, header)
        out = torch.empty(n, k, dtype=out_dtype)
        packed_rows = packed.reshape(n, packed_group_bytes)
        rt = rotation.float().T.contiguous()
        scale = input_scale.float().unsqueeze(0)
        codebook = codebook.float()
        for start in range(0, n, row_batch_size):
            end = min(start + row_batch_size, n)
            idx_np = np.stack([unpack_lsb_values(row, k, bits) for row in packed_rows[start:end]])
            idx = torch.from_numpy(idx_np.astype(np.int64, copy=False))
            recon = (codebook[idx] @ rt) * norms[start:end].float().unsqueeze(1)
            out[start:end] = (recon / scale).to(out_dtype)
        return out

    if k != header.group_size * header.num_groups:
        raise ValueError(f"{path}: K={k} != group_size*num_groups={header.group_size * header.num_groups}")
    packed_group_bytes = math.ceil(header.group_size * bits / 8)
    expected = n * header.num_groups * packed_group_bytes
    if header.data_bytes != expected:
        raise ValueError(f"{path}: data_bytes={header.data_bytes}, expected {expected}")

    codebook, input_scale, norms, left, right, perm = parse_normal_metadata(scales_blob, header)
    signs = set(int(x) for x in left.tolist()) | set(int(x) for x in right.tolist())
    if not signs.issubset({-1, 1}):
        raise ValueError(f"{path}: signs must be +/-1, got {sorted(signs)}")
    if sorted(int(x) for x in perm.tolist()) != list(range(header.group_size)):
        raise ValueError(f"{path}: permutation is not bijective")

    base_h = torch.from_numpy((hadamard(header.group_size, dtype=float) / math.sqrt(header.group_size)).astype(np.float32))
    rotation = (left.float().unsqueeze(1) * base_h * right.float().unsqueeze(0))[:, perm.long()].contiguous()
    rt = rotation.T.contiguous()
    scale = input_scale.float().unsqueeze(0)
    codebook = codebook.float()
    out = torch.empty(n, k, dtype=out_dtype)
    packed_groups = packed.reshape(n, header.num_groups, packed_group_bytes)

    for start in range(0, n, row_batch_size):
        end = min(start + row_batch_size, n)
        idx_np = np.empty((end - start, header.num_groups, header.group_size), dtype=np.uint8)
        for row_i, row_groups in enumerate(packed_groups[start:end]):
            for group_i, group in enumerate(row_groups):
                idx_np[row_i, group_i] = unpack_lsb_values(group, header.group_size, bits)
        idx = torch.from_numpy(idx_np.astype(np.int64, copy=False))
        recon = (codebook[idx] @ rt) * norms[start:end].float().unsqueeze(-1)
        out[start:end] = (recon.reshape(end - start, k) / scale).to(out_dtype)
    return out


def load_manifest_name_map(root: Path) -> dict[str, str]:
    path = root / "weights_manifest.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    entries = data.get("weights", data if isinstance(data, list) else [])
    if isinstance(entries, dict):
        entries = entries.values()
    out: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        output = entry.get("output_name") or entry.get("file") or entry.get("path")
        source = entry.get("source_name") or entry.get("name") or entry.get("hf_name")
        if output and source:
            out[Path(output).name] = source if source.endswith(".weight") or source.endswith("layer_scalar") else f"{source}.weight"
    return out


def cactus_filename_to_key(filename: str, name_map: dict[str, str]) -> str:
    if filename in name_map:
        return name_map[filename]
    stem = filename[:-8] if filename.endswith(".weights") else filename
    direct = {
        "token_embeddings": "model.language_model.embed_tokens.weight",
        "output_weight": "lm_head.weight",
        "output_norm": "model.language_model.norm.weight",
        "embed_tokens_per_layer": "model.language_model.embed_tokens_per_layer.weight",
        "per_layer_model_proj": "model.language_model.per_layer_model_projection.weight",
        "per_layer_proj_norm": "model.language_model.per_layer_projection_norm.weight",
        "embed_vision_proj": "model.embed_vision.embedding_projection.weight",
        "embed_vision_embedding": "model.embed_vision.embedding.weight",
        "embed_vision_post_proj_norm": "model.embed_vision.post_projection_norm.weight",
        "embed_audio_proj": "model.embed_audio.embedding_projection.weight",
        "embed_audio_embedding": "model.embed_audio.embedding.weight",
        "audio_subsample_conv_projection_input_proj": "model.audio_tower.subsample_conv_projection.input_proj_linear.weight",
        "audio_output_proj": "model.audio_tower.output_proj.weight",
    }
    if stem in direct:
        return direct[stem]

    m = re.fullmatch(r"layer_(\d+)_(.+)", stem)
    if m:
        layer, suffix = m.groups()
        mapping = {
            "attn_q": "self_attn.q_proj.weight",
            "attn_k": "self_attn.k_proj.weight",
            "attn_v": "self_attn.v_proj.weight",
            "attn_output": "self_attn.o_proj.weight",
            "ffn_gate": "mlp.gate_proj.weight",
            "ffn_up": "mlp.up_proj.weight",
            "ffn_down": "mlp.down_proj.weight",
            "per_layer_gate": "per_layer_input_gate.weight",
            "per_layer_proj": "per_layer_projection.weight",
            "input_norm": "input_layernorm.weight",
            "attn_q_norm": "self_attn.q_norm.weight",
            "attn_k_norm": "self_attn.k_norm.weight",
            "post_attn_norm": "post_attention_layernorm.weight",
            "pre_ffn_norm": "pre_feedforward_layernorm.weight",
            "post_ffn_norm": "post_feedforward_layernorm.weight",
            "post_per_layer_norm": "post_per_layer_input_norm.weight",
            "layer_scalar": "layer_scalar",
        }
        if suffix in mapping:
            return f"model.language_model.layers.{layer}.{mapping[suffix]}"

    m = re.fullmatch(r"vision_encoder_layers_(\d+)_(.+)", stem)
    if m:
        layer, suffix = m.groups()
        mapping = {
            "input_layernorm": "input_layernorm.weight",
            "post_attention_layernorm": "post_attention_layernorm.weight",
            "pre_feedforward_layernorm": "pre_feedforward_layernorm.weight",
            "post_feedforward_layernorm": "post_feedforward_layernorm.weight",
            "self_attn_q_norm": "self_attn.q_norm.weight",
            "self_attn_k_norm": "self_attn.k_norm.weight",
            "self_attn_q_proj": "self_attn.q_proj.weight",
            "self_attn_k_proj": "self_attn.k_proj.weight",
            "self_attn_v_proj": "self_attn.v_proj.weight",
            "self_attn_o_proj": "self_attn.o_proj.weight",
            "mlp_gate_proj": "mlp.gate_proj.weight",
            "mlp_up_proj": "mlp.up_proj.weight",
            "mlp_down_proj": "mlp.down_proj.weight",
        }
        if suffix in mapping:
            return f"model.vision_tower.encoder.layers.{layer}.{mapping[suffix]}"

    m = re.fullmatch(r"audio_conformer_(\d+)_(.+)", stem)
    if m:
        layer, suffix = m.groups()
        mapping = {
            "ffw_layer_start_ffw_layer_1": "feed_forward1.ffw_layer_1.linear.weight",
            "ffw_layer_start_ffw_layer_2": "feed_forward1.ffw_layer_2.linear.weight",
            "ffw_layer_end_ffw_layer_1": "feed_forward2.ffw_layer_1.linear.weight",
            "ffw_layer_end_ffw_layer_2": "feed_forward2.ffw_layer_2.linear.weight",
            "attention_attn_q_proj": "self_attn.q_proj.linear.weight",
            "attention_attn_k_proj": "self_attn.k_proj.linear.weight",
            "attention_attn_v_proj": "self_attn.v_proj.linear.weight",
            "attention_post": "self_attn.post.linear.weight",
            "attention_attn_relative_position_embedding_pos_proj": "self_attn.relative_k_proj.weight",
            "lconv1d_linear_start": "lconv1d.linear_start.linear.weight",
            "lconv1d_linear_end": "lconv1d.linear_end.linear.weight",
        }
        if suffix in mapping:
            return f"model.audio_tower.layers.{layer}.{mapping[suffix]}"

    return "cactus_unmapped." + stem


def is_aux_stats_file(path: Path) -> bool:
    return bool(re.search(r"_(input|output)_(min|max)\.weights$", path.name))


def iter_weight_files(root: Path, include_re: re.Pattern[str] | None, max_tensors: int | None, include_aux_stats: bool) -> Iterator[Path]:
    count = 0
    for path in sorted(root.rglob("*.weights")):
        if not include_aux_stats and is_aux_stats_file(path):
            continue
        if include_re and not include_re.search(path.name):
            continue
        yield path
        count += 1
        if max_tensors is not None and count >= max_tensors:
            return


def convert(args: argparse.Namespace) -> dict:
    if args.out.exists():
        if not args.force:
            raise SystemExit(f"{args.out} exists; pass --force to replace it")
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    out_dtype = torch.float16 if args.dtype == "float16" else torch.bfloat16
    include_re = re.compile(args.include_regex) if args.include_regex else None
    root, tmp = materialize_input(args.input, args.tmp_dir)
    try:
        cactus_root = find_cactus_root(root)
        name_map = load_manifest_name_map(cactus_root)
        writer = ShardedSafetensorsWriter(args.out, int(args.shard_size_gb * (1024**3)))
        report = {
            "input": str(args.input),
            "extracted_root": str(root),
            "cactus_root": str(cactus_root),
            "dtype": args.dtype,
            "copied_config_files": copy_config_files(root, args.out),
            "written": [],
            "unmapped": [],
        }
        for path in iter_weight_files(cactus_root, include_re, args.max_tensors, args.include_aux_stats):
            header = read_header(path)
            key = cactus_filename_to_key(path.name, name_map)
            if key.startswith("cactus_unmapped."):
                report["unmapped"].append({"file": path.name, "key": key})
            if header.precision in (PRECISION_FP16, PRECISION_FP32):
                tensor = dequantize_fp_file(path, header, out_dtype)
            elif header.precision in PRECISION_CQ:
                tensor = dequantize_cq_file(path, header, out_dtype, args.row_batch_size)
            else:
                raise ValueError(f"{path}: unsupported precision={header.precision}")
            writer.add(key, tensor)
            report["written"].append({"file": path.name, "key": key, "shape": list(tensor.shape), "precision": header.precision})
            print(f"wrote {key} {tuple(tensor.shape)}", flush=True)
            del tensor
        writer.close()
        report["written_count"] = len(report["written"])
        (args.out / "qdq_conversion_report.json").write_text(json.dumps(report, indent=2) + "\n")
        return report
    finally:
        if tmp is not None:
            tmp.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Cactus `.weights` directory or tar archive")
    parser.add_argument("--out", type=Path, required=True, help="Output HF-style fp16 QDQ checkpoint directory")
    parser.add_argument("--dtype", choices=["float16", "bfloat16"], default="float16")
    parser.add_argument("--shard-size-gb", type=float, default=4.0)
    parser.add_argument("--row-batch-size", type=int, default=2048)
    parser.add_argument("--include-regex", default=None, help="Only convert tensors whose file name matches this regex")
    parser.add_argument("--include-aux-stats", action="store_true", help="Also convert cactus *_input/output_min/max.weights debug tensors")
    parser.add_argument("--max-tensors", type=int, default=None, help="Debug limit")
    parser.add_argument("--tmp-dir", type=Path, default=None, help="Where to extract tar inputs")
    parser.add_argument("--force", action="store_true", help="Delete existing output directory first")
    return parser.parse_args()


def main() -> None:
    report = convert(parse_args())
    print(f"done: wrote {report['written_count']} tensors", flush=True)


if __name__ == "__main__":
    main()

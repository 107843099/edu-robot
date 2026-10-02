"""Export Gemma4 TQH packages as cactus CQ mmap `.weights` files.

This exporter uses semantic CQ artifacts (codebook, input scales, norms,
indices, rotation metadata) and writes the cactus mmap layout directly. It does
not save reconstructed/dequantized FP16 caches for quantized tensors.

Presets:
  prod_tq4: LLM CQ4 + vision CQ4 + audio CQ4 + bridges CQ4 + PLI CQ2 + token embeddings CQ4.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import torch
from safetensors import safe_open

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src/turboquant"))
sys.path.insert(0, str(REPO_ROOT / "scripts/quantization"))

from cq_mmap import (
    quantize_weight_to_cq,
    quantize_weight_to_cq_gptq,
    write_cq_weights,
    write_fp16_weights,
    write_manifest,
)
from gemma_turboquant import SharedTransformBank

ALPHA = 0.25


def fit_row_table_scale(table_fp32: torch.Tensor, token_ids: list[int]) -> torch.Tensor:
    ids = torch.tensor(token_ids, dtype=torch.long).clamp(0, table_fp32.shape[0] - 1)
    x_abs = table_fp32[ids].float().abs().mean(0).clamp_min(1e-6)
    w_abs = table_fp32.float().abs().mean(0).clamp_min(1e-6)
    raw = x_abs.pow(ALPHA) / w_abs.pow(1.0 - ALPHA)
    raw = raw / torch.exp(torch.log(raw.clamp_min(1e-6)).mean())
    return raw.clamp(1.0 / 8.0, 8.0)


DEFAULT_MODEL_DIR = os.environ.get(
    "TQH_MODEL_DIR",
    "/workspace/model/models--google--gemma-4-E2B-it/snapshots/b4a601102c3d45e2b7b50e2057a6d5ec8ed4adcf",
)
DEFAULT_CALIB_DIR = REPO_ROOT / "data/hessians/joint_av"
DEFAULT_FULL_HESSIANS = os.environ.get(
    "TQH_FULL_HESSIANS",
    "/workspace/turboquant/artifacts/external_quant/full_hessians/full_hessians.safetensors",
)
COPY_CONFIG_FILES = (
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
    "chat_template.jinja",
    "processor_config.json",
    "preprocessor_config.json",
    "special_tokens_map.json",
)

PRESETS = {
    "prod_tq4": {
        "llm_bits": 4,
        "vision_bits": 4,
        "audio_bits": 4,
        "vision_bridge_bits": 4,
        "audio_bridge_bits": 4,
        "pli_bits": 2,
        "embed_bits": 4,
    },
    "vision_tq4": {
        "llm_bits": 4,
        "vision_bits": 4,
        "audio_bits": 16,
        "vision_bridge_bits": 4,
        "audio_bridge_bits": 16,
        "pli_bits": 2,
        "embed_bits": 4,
    },
    "audio_tq4": {
        "llm_bits": 4,
        "vision_bits": 16,
        "audio_bits": 4,
        "vision_bridge_bits": 16,
        "audio_bridge_bits": 4,
        "pli_bits": 2,
        "embed_bits": 4,
    },
    "prod_v3_l3": {
        "llm_bits": 3,
        "vision_bits": 3,
        "audio_bits": 4,
        "vision_bridge_bits": 3,
        "audio_bridge_bits": 4,
        "pli_bits": 2,
        "embed_bits": 4,
    },
    "prod_v3_l4": {
        "llm_bits": 4,
        "vision_bits": 3,
        "audio_bits": 4,
        "vision_bridge_bits": 3,
        "audio_bridge_bits": 4,
        "pli_bits": 2,
        "embed_bits": 4,
    },
    "prod_v4_l3": {
        "llm_bits": 3,
        "vision_bits": 4,
        "audio_bits": 4,
        "vision_bridge_bits": 4,
        "audio_bridge_bits": 4,
        "pli_bits": 2,
        "embed_bits": 4,
    },
    "prod_v4_l4": {
        "llm_bits": 4,
        "vision_bits": 4,
        "audio_bits": 4,
        "vision_bridge_bits": 4,
        "audio_bridge_bits": 4,
        "pli_bits": 2,
        "embed_bits": 4,
    },
}


GEMMA4_WEIGHT_SCALE = 16.0
GEMMA4_MULT_BASENAMES = {"ffn_gate", "ffn_up", "per_layer_gate", "moe_gate_proj", "moe_up_proj"}
GEMMA4_DIV_BASENAMES = {
    "token_embeddings",
    "output_weight",
    "embed_vision_proj",
    "embed_vision_embedding",
}


def _strip_weight_suffix(name: str) -> str:
    return name.removesuffix(".weight").removesuffix(".bias")


def _ext_for_name(name: str) -> str:
    return ".bias" if name.endswith(".bias") else ".weights"


def _remap_gemma4_audio_key(name: str) -> str:
    if "audio_tower" not in name:
        return name
    out = name
    out = re.sub(r"subsample_conv_projection\.layer(\d+)\.", r"subsample_conv_projection.conv_\1.", out)
    out = re.sub(r"audio_tower\.layers\.", "audio_tower.conformer.", out)
    out = out.replace(".feed_forward1.", ".ffw_layer_start.")
    out = out.replace(".feed_forward2.", ".ffw_layer_end.")
    out = re.sub(r"\.self_attn\.(q_proj|k_proj|v_proj)\.", r".attention.attn.\1.", out)
    out = out.replace(".self_attn.per_dim_scale", ".attention.attn.per_dim_scale")
    out = out.replace(".self_attn.relative_k_proj.", ".attention.attn.relative_position_embedding.pos_proj.")
    out = out.replace(".self_attn.post.", ".attention.post.")
    out = out.replace(".norm_pre_attn.", ".attention.pre_attn_norm.")
    out = out.replace(".norm_post_attn.", ".attention.post_norm.")
    out = re.sub(r"\.norm_out\.", ".norm.", out)
    return out


def _tower_out_name(name: str, strip_prefix: str, add_prefix: str) -> str:
    ext = _ext_for_name(name)
    base = _strip_weight_suffix(name)[len(strip_prefix):]
    if base.endswith(".linear"):
        base = base[:-len(".linear")]
    elif base.endswith("_linear"):
        base = base[:-len("_linear")]
    return add_prefix + base.replace(".", "_") + ext


def _language_out_name(name: str) -> str | None:
    if name == "model.language_model.embed_tokens.weight":
        return "token_embeddings.weights"
    if name == "model.language_model.embed_tokens_per_layer.weight":
        return "embed_tokens_per_layer.weights"
    if name == "model.language_model.per_layer_model_projection.weight":
        return "per_layer_model_proj.weights"
    if name == "model.language_model.per_layer_projection_norm.weight":
        return "per_layer_proj_norm.weights"
    if name == "model.language_model.norm.weight":
        return "output_norm.weights"

    prefix = "model.language_model.layers."
    if not name.startswith(prefix):
        return None
    rest = _strip_weight_suffix(name)[len(prefix):]
    try:
        layer_s, suffix = rest.split(".", 1)
    except ValueError:
        return None
    mapping = {
        "self_attn.q_proj": "attn_q",
        "self_attn.k_proj": "attn_k",
        "self_attn.v_proj": "attn_v",
        "self_attn.o_proj": "attn_output",
        "self_attn.q_norm": "attn_q_norm",
        "self_attn.k_norm": "attn_k_norm",
        "input_layernorm": "input_norm",
        "post_attention_layernorm": "post_attn_norm",
        "pre_feedforward_layernorm": "pre_ffn_norm",
        "post_feedforward_layernorm": "post_ffn_norm",
        "post_per_layer_input_norm": "post_per_layer_norm",
        "mlp.gate_proj": "ffn_gate",
        "mlp.up_proj": "ffn_up",
        "mlp.down_proj": "ffn_down",
        "per_layer_input_gate": "per_layer_gate",
        "per_layer_projection": "per_layer_proj",
        "layer_scalar": "layer_scalar",
    }
    mapped = mapping.get(suffix)
    return f"layer_{layer_s}_{mapped}{_ext_for_name(name)}" if mapped else None


def cactus_out_name(name: str) -> str:
    mapped = _language_out_name(name)
    if mapped:
        return mapped
    if name == "model.embed_vision.embedding.weight":
        return "embed_vision_embedding.weights"
    if name == "model.embed_vision.embedding_projection.weight":
        return "embed_vision_proj.weights"
    if name == "model.embed_vision.soft_embedding_norm.weight":
        return "embed_vision_soft_norm.weights"
    if name == "model.embed_vision.hard_embedding_norm.weight":
        return "embed_vision_hard_norm.weights"
    if name == "model.embed_audio.embedding.weight":
        return "embed_audio_embedding.weights"
    if name == "model.embed_audio.embedding_projection.weight":
        return "embed_audio_proj.weights"
    if name == "model.embed_audio.soft_embedding_norm.weight":
        return "embed_audio_soft_norm.weights"
    if name == "model.embed_audio.hard_embedding_norm.weight":
        return "embed_audio_hard_norm.weights"
    if name.startswith("model.vision_tower."):
        return _tower_out_name(name, "model.vision_tower.", "vision_")
    audio_name = _remap_gemma4_audio_key(name)
    if audio_name.startswith("model.audio_tower."):
        return _tower_out_name(audio_name, "model.audio_tower.", "audio_")
    base = _strip_weight_suffix(name).removeprefix("model.")
    return re.sub(r"[^A-Za-z0-9_]+", "_", base).strip("_") + _ext_for_name(name)


def gemma4_scale_factor(out_name: str) -> float:
    base = out_name.removesuffix(".weights").removesuffix(".bias")
    parts = base.split("_", 2)
    if len(parts) == 3 and parts[0] == "layer" and parts[1].isdigit():
        base = parts[2]
    if base in GEMMA4_MULT_BASENAMES:
        return GEMMA4_WEIGHT_SCALE
    if base in GEMMA4_DIV_BASENAMES:
        return 1.0 / GEMMA4_WEIGHT_SCALE
    if any(x in out_name for x in [
        "input_norm", "post_attn_norm", "pre_ffn_norm", "post_ffn_norm",
        "post_per_layer_norm", "post_proj_norm",
    ]):
        return 1.0 / GEMMA4_WEIGHT_SCALE
    if "router_scale" in out_name:
        return 1.0 / GEMMA4_WEIGHT_SCALE
    if out_name == "output_norm.weights":
        return GEMMA4_WEIGHT_SCALE
    return 1.0


def is_lm_weight(name: str) -> bool:
    if name == "model.language_model.per_layer_model_projection.weight":
        return True
    if not name.startswith("model.language_model.layers.") or not name.endswith(".weight"):
        return False
    parts = name.split(".")
    leaf = parts[-2]
    return leaf in {
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
        "per_layer_input_gate", "per_layer_projection",
    }


def is_vision_weight(name: str) -> bool:
    return name.startswith("model.vision_tower.") and name.endswith(".weight")


def is_audio_weight(name: str) -> bool:
    return name.startswith("model.audio_tower.") and name.endswith(".weight")


def is_bridge_weight(name: str) -> str | None:
    if name == "model.embed_vision.embedding_projection.weight":
        return "vision"
    if name == "model.embed_audio.embedding_projection.weight":
        return "audio"
    return None


def quant_bits_for(name: str, preset: dict) -> int | None:
    if name == "model.language_model.embed_tokens.weight":
        return int(preset["embed_bits"])
    if name == "model.language_model.embed_tokens_per_layer.weight":
        return int(preset["pli_bits"])
    bridge = is_bridge_weight(name)
    if bridge == "vision":
        bits = int(preset["vision_bridge_bits"])
        return bits if bits < 16 else None
    if bridge == "audio":
        bits = int(preset["audio_bridge_bits"])
        return bits if bits < 16 else None
    if is_lm_weight(name):
        bits = int(preset["llm_bits"])
        return bits if bits < 16 else None
    if is_vision_weight(name):
        bits = int(preset["vision_bits"])
        return bits if bits < 16 else None
    if is_audio_weight(name):
        bits = int(preset["audio_bits"])
        return bits if bits < 16 else None
    return None


def should_quantize_tensor(name: str, tensor: torch.Tensor, preset: dict) -> bool:
    bits = quant_bits_for(name, preset)
    if bits is None:
        return False
    if tensor.ndim != 2:
        return False
    return True


def diag_key_for(name: str) -> str:
    return name.removesuffix(".weight") + ".diagH"


def input_scale_from_diag(diag: torch.Tensor | None, w: torch.Tensor) -> torch.Tensor | None:
    if diag is None:
        return None
    x_abs = diag.float().clamp_min(1e-12).sqrt().clamp_min(1e-6)
    w_abs = w.float().abs().mean(0).clamp_min(1e-6)
    raw = x_abs.pow(ALPHA) / w_abs.pow(1.0 - ALPHA)
    raw = raw / torch.exp(torch.log(raw.clamp_min(1e-6)).mean())
    return raw.clamp(1.0 / 8.0, 8.0).cpu()


def full_hessian_key_for(name: str) -> str:
    return name.removesuffix(".weight") + ".H"


def should_apply_gptq_correction(name: str) -> bool:
    if is_audio_weight(name) or is_bridge_weight(name) == "audio":
        return False
    return is_lm_weight(name) or is_vision_weight(name) or is_bridge_weight(name) == "vision"


def hessian_inverse_for_scaled_space(H: torch.Tensor, scale: torch.Tensor | None, percdamp: float) -> torch.Tensor:
    H = H.float().cpu().contiguous()
    if scale is not None:
        s = scale.float().cpu().clamp_min(1e-6)
        H = H / (s[:, None] * s[None, :])
    H.diagonal().add_(float(percdamp) * H.diagonal().mean())
    return torch.linalg.inv(H)


def load_diag_map(path: Path) -> dict[str, torch.Tensor]:
    out: dict[str, torch.Tensor] = {}
    if not path.exists():
        return out
    with safe_open(str(path), framework="pt", device="cpu") as f:
        for key in f.keys():
            out[key] = f.get_tensor(key)
    return out


def copy_config_files(model_dir: Path, out_dir: Path) -> None:
    for fname in COPY_CONFIG_FILES:
        src = model_dir / fname
        if src.exists():
            shutil.copy2(src, out_dir / fname)
    chat = model_dir / "chat_template.jinja"
    if chat.exists():
        shutil.copy2(chat, out_dir / "chat_template.jinja2")


def write_cactus_config(model_dir: Path, out_dir: Path) -> None:
    config = json.loads((model_dir / "config.json").read_text())
    text = config.get("text_config", {})
    vision = config.get("vision_config", {})
    audio = config.get("audio_config", {})
    rope = text.get("rope_parameters", {}) or {}
    global_rope = rope.get("full_attention", {}) if isinstance(rope, dict) else {}
    sliding_rope = rope.get("sliding_attention", {}) if isinstance(rope, dict) else {}
    layer_types = [
        "global" if ("global" in str(x).lower() or "full" in str(x).lower()) else "sliding"
        for x in (text.get("layer_types") or [])
    ]
    sscp = audio.get("subsampling_conv_channels") or [128, 32]
    eos = config.get("eos_token_id", text.get("eos_token_id", 1))
    eos_id = eos[0] if isinstance(eos, list) else eos
    lines = [
        f"vocab_size={int(text.get('vocab_size', 0))}",
        f"hidden_dim={int(text.get('hidden_size', 0))}",
        f"num_layers={int(text.get('num_hidden_layers', 0))}",
        f"attention_heads={int(text.get('num_attention_heads', 0))}",
        f"attention_kv_heads={int(text.get('num_key_value_heads', 0))}",
        f"ffn_intermediate_dim={int(text.get('intermediate_size', 0))}",
        f"context_length={int(text.get('max_position_embeddings', 0))}",
        f"rope_theta={float(global_rope.get('rope_theta', 1000000.0))}",
        f"attention_head_dim={int(text.get('head_dim', 0))}",
        f"layer_norm_eps={float(text.get('rms_norm_eps', 1e-6))}",
        "num_experts=0",
        "num_shared_experts=0",
        "num_top_experts=0",
        "num_experts_per_tok=0",
        "moe_every_n_layers=0",
        "layer_types=" + ",".join(layer_types),
        f"tie_word_embeddings={'true' if bool(config.get('tie_word_embeddings', True)) else 'false'}",
        "model_type=gemma4",
        f"bos_token_id={int(text.get('bos_token_id', 2))}",
        f"eos_token_id={int(eos_id)}",
        f"vision_hidden_size={int(vision.get('hidden_size', 0))}",
        f"vision_num_layers={int(vision.get('num_hidden_layers', 0))}",
        "vision_image_size=0",
        f"vision_patch_size={int(vision.get('patch_size', 16))}",
        f"vision_attention_heads={int(vision.get('num_attention_heads', 0))}",
        f"vision_embed_dim={int(vision.get('hidden_size', 0))}",
        "num_channels=3",
        "visual_tokens_per_img=0",
        "use_pixel_shuffle=false",
        "pixel_shuffle_factor=1",
        "use_image_tokens=true",
        f"image_token_id={int(config.get('image_token_id', 258880))}",
        "use_layout_tags=false",
        "downsample_factor=2",
        f"vision_head_dim={int(vision.get('head_dim', 0))}",
        f"vision_kv_heads={int(vision.get('num_key_value_heads', vision.get('num_attention_heads', 0)))}",
        f"vision_intermediate_size={int(vision.get('intermediate_size', 0))}",
        f"vision_position_embedding_size={int(vision.get('position_embedding_size', 0))}",
        f"vision_pooling_kernel_size={int(vision.get('pooling_kernel_size', 3))}",
        f"vision_default_output_length={int(vision.get('default_output_length', config.get('vision_soft_tokens_per_image', 280)))}",
        f"vision_rope_theta={float((vision.get('rope_parameters') or {}).get('rope_theta', 100.0))}",
        "altup_num_inputs=4",
        "laurel_rank=64",
        f"hidden_size_per_layer_input={int(text.get('hidden_size_per_layer_input', 0))}",
        f"num_kv_shared_layers={int(text.get('num_kv_shared_layers', 0))}",
        f"sliding_window={int(text.get('sliding_window', 0))}",
        f"rope_local_base_freq={float(sliding_rope.get('rope_theta', 10000.0))}",
        f"final_logit_softcapping={float(text.get('final_logit_softcapping', 30.0))}",
        "query_pre_attn_scalar=0",
        f"global_partial_rotary_factor={float(global_rope.get('partial_rotary_factor', 0.25))}",
        f"attention_k_eq_v={'true' if bool(text.get('attention_k_eq_v', False)) else 'false'}",
        f"enable_moe_block={'true' if bool(text.get('enable_moe_block', False)) else 'false'}",
        f"global_head_dim={int(text.get('global_head_dim', text.get('head_dim', 0)))}",
        f"vocab_size_per_layer_input={int(text.get('vocab_size_per_layer_input', text.get('vocab_size', 0)))}",
        f"audio_hidden_dim={int(audio.get('hidden_size', 0))}",
        f"audio_num_layers={int(audio.get('num_hidden_layers', 0))}",
        f"audio_num_heads={int(audio.get('num_attention_heads', 0))}",
        f"audio_head_dim={int(audio.get('hidden_size', 0)) // max(1, int(audio.get('num_attention_heads', 1)))}",
        "audio_input_feat_size=128",
        f"audio_conf_conv_kernel_size={int(audio.get('conv_kernel_size', 5))}",
        f"audio_chunk_size={int(audio.get('attention_chunk_size', 12))}",
        f"audio_context_left={int(audio.get('attention_context_left', 13))}",
        f"audio_context_right={int(audio.get('attention_context_right', 0))}",
        f"audio_logit_cap={float(audio.get('attention_logit_cap', 50.0))}",
        f"audio_residual_weight={float(audio.get('residual_weight', 0.5))}",
        f"audio_output_proj_dims={int(audio.get('output_proj_dims', text.get('hidden_size', 0)))}",
        "audio_vocab_size=128",
        "audio_vocab_offset=0",
        "audio_soft_tokens=188",
        f"audio_sscp_conv0_channels={int(sscp[0]) if len(sscp) > 0 else 128}",
        f"audio_sscp_conv1_channels={int(sscp[1]) if len(sscp) > 1 else 32}",
        "audio_sscp_conv_eps=0.001",
        f"audio_rms_norm_eps={float(audio.get('rms_norm_eps', 1e-6))}",
        "audio_fft_length=512",
        f"audio_token_id={int(config.get('audio_token_id', 258881))}",
        "model_variant=default",
        "precision=CQ4",
        "quantization=CQ4",
    ]
    (out_dir / "config.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_basic_tokenizer_files(model_dir: Path, out_dir: Path) -> None:
    tokenizer_json = json.loads((model_dir / "tokenizer.json").read_text(encoding="utf-8"))
    tokenizer_config_path = model_dir / "tokenizer_config.json"
    tokenizer_config = json.loads(tokenizer_config_path.read_text(encoding="utf-8")) if tokenizer_config_path.exists() else {}
    vocab = tokenizer_json.get("model", {}).get("vocab", {})
    if isinstance(vocab, list):
        vocab = {token: i for i, token in enumerate(vocab)}
    id_to_token = [""] * (max(int(v) for v in vocab.values()) + 1)
    for token, token_id in vocab.items():
        id_to_token[token_id] = token
    with (out_dir / "vocab.txt").open("w", encoding="utf-8") as f:
        for token_id, token in enumerate(id_to_token):
            f.write(f"{token_id}\t{token}\n")

    merges = tokenizer_json.get("model", {}).get("merges", []) or []
    with (out_dir / "merges.txt").open("w", encoding="utf-8", newline="") as f:
        f.write("#version: 0.2\n")
        for merge in merges:
            f.write((" ".join(merge) if isinstance(merge, list) else str(merge)) + "\n")

    special_tokens = {}
    special_ids = {
        "bos_token_id": tokenizer_config.get("bos_token_id", 2),
        "eos_token_id": tokenizer_config.get("eos_token_id", 1),
        "pad_token_id": tokenizer_config.get("pad_token_id", 0),
        "unk_token_id": tokenizer_config.get("unk_token_id"),
    }
    for info in tokenizer_json.get("added_tokens", []) or []:
        if "id" in info and "content" in info:
            special_tokens[int(info["id"])] = str(info["content"])
    added = []
    for token in tokenizer_config.get("additional_special_tokens", []) or []:
        token_id = vocab.get(token)
        if token_id is not None:
            special_tokens[int(token_id)] = token
            added.append({"token": token, "id": int(token_id)})
    for token_id in special_ids.values():
        if token_id is not None and 0 <= int(token_id) < len(id_to_token):
            special_tokens.setdefault(int(token_id), id_to_token[int(token_id)])

    (out_dir / "special_tokens.json").write_text(json.dumps({
        **special_ids,
        "vocab_size": len(id_to_token),
        "model_max_length": tokenizer_config.get("model_max_length", 131072),
        "special_tokens": special_tokens,
        "additional_special_tokens": added,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "tokenizer_config.txt").write_text(
        "\n".join([
            f"vocab_size={len(id_to_token)}",
            f"bos_token_id={special_ids['bos_token_id']}",
            f"eos_token_id={special_ids['eos_token_id']}",
            f"pad_token_id={special_ids['pad_token_id']}",
            "unk_token_id=3",
            f"model_max_length={tokenizer_config.get('model_max_length', 131072)}",
            "tokenizer_type=bpe",
            "vocab_format=id_tab_token",
            "normalizer=metaspace",
            "decoder=replace_metaspace",
            "byte_fallback=true",
            f"has_chat_template={'true' if (out_dir / 'chat_template.jinja2').exists() else 'false'}",
            "",
        ]),
        encoding="utf-8",
    )


def export_package(args) -> None:
    preset = dict(PRESETS[args.preset])
    model_dir = Path(args.model_dir)
    model_path = model_dir / "model.safetensors"
    if not model_path.exists():
        raise FileNotFoundError(f"Expected model.safetensors in {model_dir}")
    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / "outputs/cactus_cq" / args.preset
    if out_dir.exists() and args.force:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_config_files(model_dir, out_dir)
    write_cactus_config(model_dir, out_dir)
    write_basic_tokenizer_files(model_dir, out_dir)

    diag_map = load_diag_map(Path(args.calib_dir) / "diag_hessians.safetensors")
    full_hessian_path = Path(args.full_hessians)
    full_hessian_file = None
    full_hessian_keys: set[str] = set()
    if args.quant_method == "tqh_gptq":
        if not full_hessian_path.exists():
            raise FileNotFoundError(f"--quant-method tqh_gptq requires full hessians: {full_hessian_path}")
        full_hessian_file = safe_open(str(full_hessian_path), framework="pt", device="cpu")
        full_hessian_file.__enter__()
        full_hessian_keys = set(full_hessian_file.keys())
    scale_ids_path = Path(args.calib_dir) / "scale_token_ids.json"
    scale_ids = json.loads(scale_ids_path.read_text()) if scale_ids_path.exists() else []
    bank = SharedTransformBank(seed=args.seed)
    manifest: list[dict] = []

    print(f"Exporting {args.preset} from {model_path}", flush=True)
    print(f"Output: {out_dir}", flush=True)
    t0 = time.perf_counter()

    try:
      with safe_open(str(model_path), framework="pt", device="cpu") as sf:
        keys = list(sf.keys())
        for idx, name in enumerate(keys):
            if args.only_source_regex and not re.search(args.only_source_regex, name):
                continue
            tensor = sf.get_tensor(name)
            bits = quant_bits_for(name, preset)
            file_name = cactus_out_name(name)
            out_name = file_name.removesuffix(".weights").removesuffix(".bias")
            out_path = out_dir / file_name
            scale_factor = gemma4_scale_factor(file_name)

            if args.limit_tensors and len(manifest) >= args.limit_tensors:
                break

            if should_quantize_tensor(name, tensor, preset):
                w = tensor.float().cpu().contiguous()
                if name == "model.language_model.embed_tokens.weight":
                    group_size = None
                    rotation_family = "orthogonal"
                    input_scale = fit_row_table_scale(w, scale_ids) if scale_ids else None
                elif name == "model.language_model.embed_tokens_per_layer.weight":
                    group_size = 128
                    rotation_family = "hadamard"
                    input_scale = fit_row_table_scale(w, scale_ids) if scale_ids else None
                else:
                    group_size = 128
                    rotation_family = "hadamard"
                    input_scale = input_scale_from_diag(diag_map.get(diag_key_for(name)), w)

                if group_size is not None and w.shape[1] % group_size != 0:
                    print(f"  FP16 fallback (K not divisible by {group_size}): {name}", flush=True)
                    write_tensor = tensor
                    if scale_factor != 1.0 and torch.is_floating_point(tensor):
                        write_tensor = tensor.float() * float(scale_factor)
                    info = write_fp16_weights(out_path, write_tensor)
                    kind = "fp16_fallback"
                else:
                    print(f"  CQ{bits} {idx+1}/{len(keys)} {name} shape={tuple(w.shape)}", flush=True)
                    h_inv = None
                    if (
                        args.quant_method == "tqh_gptq"
                        and should_apply_gptq_correction(name)
                        and rotation_family == "hadamard"
                        and group_size == 128
                        and full_hessian_file is not None
                        and full_hessian_key_for(name) in full_hessian_keys
                    ):
                        H = full_hessian_file.get_tensor(full_hessian_key_for(name))
                        input_scale = input_scale_from_diag(torch.diag(H), w)
                        h_inv = hessian_inverse_for_scaled_space(H, input_scale, args.percdamp)
                        del H
                    if h_inv is not None:
                        cq = quantize_weight_to_cq_gptq(
                            w,
                            source_name=name,
                            output_name=out_name,
                            bits=int(bits),
                            bank=bank,
                            group_size=int(group_size),
                            input_scale=input_scale,
                            h_inv=h_inv,
                            device=args.device,
                        )
                    else:
                        cq = quantize_weight_to_cq(
                            w,
                            source_name=name,
                            output_name=out_name,
                            bits=int(bits),
                            bank=bank,
                            group_size=group_size,
                            rotation_family=rotation_family,
                            input_scale=input_scale,
                            device=args.device,
                            batch=args.batch,
                        )
                    del h_inv
                    if scale_factor != 1.0:
                        cq.norms = (cq.norms.float() * scale_factor).to(torch.float16)
                    info = write_cq_weights(out_path, cq)
                    kind = f"cq{bits}"
                del w
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            else:
                if args.skip_fp16_untouched:
                    continue
                write_tensor = tensor
                if scale_factor != 1.0 and torch.is_floating_point(tensor):
                    write_tensor = tensor.float() * float(scale_factor)
                info = write_fp16_weights(out_path, write_tensor)
                kind = "fp16"

            manifest.append({
                "source_name": name,
                "output_name": out_name,
                "file": out_path.name,
                "kind": kind,
                **info,
            })
            if len(manifest) % 100 == 0:
                print(f"  wrote {len(manifest)} tensors ({(time.perf_counter()-t0)/60:.1f}m)", flush=True)

    finally:
        if full_hessian_file is not None:
            full_hessian_file.__exit__(None, None, None)

    post_proj_norm = torch.full((1536,), 1.0 / GEMMA4_WEIGHT_SCALE, dtype=torch.float32)
    synth_path = out_dir / "embed_vision_post_proj_norm.weights"
    synth_info = write_fp16_weights(synth_path, post_proj_norm)
    manifest.append({
        "source_name": "<synthetic:embed_vision_post_proj_norm>",
        "output_name": "embed_vision_post_proj_norm",
        "file": synth_path.name,
        "kind": "fp16_synthetic",
        **synth_info,
    })

    write_manifest(out_dir / "weights_manifest.json", manifest)
    summary = {
        "preset": args.preset,
        "model_dir": str(model_dir),
        "calib_dir": str(args.calib_dir),
        "seed": args.seed,
        "tensors": len(manifest),
        "preset_bits": preset,
        "quant_method": args.quant_method,
        "full_hessians": str(full_hessian_path) if args.quant_method == "tqh_gptq" else None,
        "elapsed_seconds": round(time.perf_counter() - t0, 1),
    }
    (out_dir / "export_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Done: {out_dir} ({len(manifest)} tensors, {(time.perf_counter()-t0)/60:.1f}m)", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--preset", choices=sorted(PRESETS), required=True)
    p.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    p.add_argument("--calib-dir", default=str(DEFAULT_CALIB_DIR))
    p.add_argument("--out-dir", default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--batch", type=int, default=256)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--quant-method", choices=["tqh", "tqh_gptq"], default="tqh")
    p.add_argument("--full-hessians", default=DEFAULT_FULL_HESSIANS)
    p.add_argument("--percdamp", type=float, default=0.01)
    p.add_argument("--force", action="store_true")
    p.add_argument("--skip-fp16-untouched", action="store_true",
                   help="Only emit CQ tensors; useful for debugging, not a complete package.")
    p.add_argument("--limit-tensors", type=int, default=None)
    p.add_argument("--only-source-regex", default=None)
    args = p.parse_args()
    export_package(args)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors.torch import load_file


Tensor = torch.Tensor


def infer_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _default_layer_types(num_hidden_layers: int, sliding_window_pattern: int) -> Tuple[str, ...]:
    layer_types = []
    for index in range(num_hidden_layers):
        if (index + 1) % sliding_window_pattern == 0:
            layer_types.append("full_attention")
        else:
            layer_types.append("sliding_attention")
    return tuple(layer_types)


def _resolve_model_dir(model_dir: str | Path) -> Path:
    path = Path(model_dir).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Model path does not exist: {path}")
    return path


def _iter_safetensor_paths(model_dir: Path) -> List[Path]:
    index_path = model_dir / "model.safetensors.index.json"
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return sorted({model_dir / filename for filename in data["weight_map"].values()})

    single_path = model_dir / "model.safetensors"
    if single_path.exists():
        return [single_path]

    paths = sorted(model_dir.glob("*.safetensors"))
    if not paths:
        raise FileNotFoundError(f"No safetensor weights found under {model_dir}")
    return paths


def load_safetensor_state_dict(model_dir: str | Path) -> Dict[str, Tensor]:
    resolved_dir = _resolve_model_dir(model_dir)
    state_dict: Dict[str, Tensor] = {}
    for shard_path in _iter_safetensor_paths(resolved_dir):
        state_dict.update(load_file(str(shard_path), device="cpu"))
    return state_dict


@dataclass(frozen=True)
class GemmaConfig:
    vocab_size: int
    hidden_size: int
    intermediate_size: int
    num_hidden_layers: int
    num_attention_heads: int
    num_key_value_heads: int
    head_dim: int
    hidden_activation: str
    max_position_embeddings: int
    initializer_range: float
    rms_norm_eps: float
    use_cache: bool
    pad_token_id: int
    eos_token_id: int
    bos_token_id: int
    attention_bias: bool
    attention_dropout: float
    query_pre_attn_scalar: float
    sliding_window: int
    layer_types: Tuple[str, ...]
    final_logit_softcapping: Optional[float] = None
    attn_logit_softcapping: Optional[float] = None
    use_bidirectional_attention: bool = False
    rope_theta: float = 1_000_000.0
    rope_local_base_freq: float = 10_000.0
    torch_dtype: str = "float32"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "GemmaConfig":
        sliding_window_pattern = int(data.get("_sliding_window_pattern", 6))
        layer_types = data.get("layer_types")
        if layer_types is None:
            layer_types = _default_layer_types(
                num_hidden_layers=int(data["num_hidden_layers"]),
                sliding_window_pattern=sliding_window_pattern,
            )
        else:
            layer_types = tuple(layer_types)
        return cls(
            vocab_size=int(data["vocab_size"]),
            hidden_size=int(data["hidden_size"]),
            intermediate_size=int(data["intermediate_size"]),
            num_hidden_layers=int(data["num_hidden_layers"]),
            num_attention_heads=int(data["num_attention_heads"]),
            num_key_value_heads=int(data["num_key_value_heads"]),
            head_dim=int(data["head_dim"]),
            hidden_activation=str(data.get("hidden_activation", "gelu_pytorch_tanh")),
            max_position_embeddings=int(data["max_position_embeddings"]),
            initializer_range=float(data.get("initializer_range", 0.02)),
            rms_norm_eps=float(data.get("rms_norm_eps", 1e-6)),
            use_cache=bool(data.get("use_cache", True)),
            pad_token_id=int(data.get("pad_token_id", 0)),
            eos_token_id=int(data.get("eos_token_id", 1)),
            bos_token_id=int(data.get("bos_token_id", 2)),
            attention_bias=bool(data.get("attention_bias", False)),
            attention_dropout=float(data.get("attention_dropout", 0.0)),
            query_pre_attn_scalar=float(data.get("query_pre_attn_scalar", data["head_dim"])),
            sliding_window=int(data.get("sliding_window", 512)),
            layer_types=layer_types,
            final_logit_softcapping=(
                None if data.get("final_logit_softcapping") is None else float(data["final_logit_softcapping"])
            ),
            attn_logit_softcapping=(
                None if data.get("attn_logit_softcapping") is None else float(data["attn_logit_softcapping"])
            ),
            use_bidirectional_attention=bool(data.get("use_bidirectional_attention", False)),
            rope_theta=float(data.get("rope_theta", 1_000_000.0)),
            rope_local_base_freq=float(data.get("rope_local_base_freq", 10_000.0)),
            torch_dtype=str(data.get("torch_dtype", "float32")),
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "GemmaConfig":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    @classmethod
    def from_pretrained(cls, model_dir: str | Path) -> "GemmaConfig":
        resolved_dir = _resolve_model_dir(model_dir)
        return cls.from_json_file(resolved_dir / "config.json")


@dataclass
class LayerCache:
    keys: Optional[Tensor] = None
    values: Optional[Tensor] = None


@dataclass
class GemmaCausalLMOutput:
    logits: Tensor
    past_key_values: List[LayerCache]
    hidden_states: Optional[Tensor] = None


class GemmaScaledWordEmbedding(nn.Embedding):
    def __init__(self, num_embeddings: int, embedding_dim: int, padding_idx: int, embed_scale: float):
        super().__init__(num_embeddings, embedding_dim, padding_idx)
        self.scalar_embed_scale = float(embed_scale)
        self.register_buffer("embed_scale", torch.tensor(self.scalar_embed_scale), persistent=False)

    def forward(self, input_ids: Tensor) -> Tensor:
        scale = self.embed_scale.to(device=self.weight.device, dtype=self.weight.dtype)
        return super().forward(input_ids) * scale


class GemmaRMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = float(eps)
        self.weight = nn.Parameter(torch.zeros(dim))

    def _norm(self, x: Tensor) -> Tensor:
        return x * torch.rsqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps)

    def forward(self, x: Tensor) -> Tensor:
        output = self._norm(x.float())
        output = output * (1.0 + self.weight.float())
        return output.type_as(x)


class GemmaMLP(nn.Module):
    def __init__(self, config: GemmaConfig):
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)

    def forward(self, x: Tensor) -> Tensor:
        gated = F.gelu(self.gate_proj(x), approximate="tanh")
        return self.down_proj(gated * self.up_proj(x))


class GemmaRotaryEmbedding(nn.Module):
    def __init__(self, config: GemmaConfig):
        super().__init__()
        self.config = config
        for layer_type in sorted(set(config.layer_types)):
            theta = config.rope_theta if layer_type == "full_attention" else config.rope_local_base_freq
            inv_freq = 1.0 / (
                theta
                ** (torch.arange(0, config.head_dim, 2, dtype=torch.float32) / float(config.head_dim))
            )
            self.register_buffer(f"{layer_type}_inv_freq", inv_freq, persistent=False)

    def forward(self, reference: Tensor, position_ids: Tensor, layer_type: str) -> Tuple[Tensor, Tensor]:
        inv_freq = getattr(self, f"{layer_type}_inv_freq").to(device=reference.device)
        freqs = torch.einsum("bs,d->bsd", position_ids.float(), inv_freq.float())
        emb = torch.cat([freqs, freqs], dim=-1)
        cos = emb.cos().to(dtype=reference.dtype)
        sin = emb.sin().to(dtype=reference.dtype)
        return cos, sin


def rotate_half(x: Tensor) -> Tensor:
    left = x[..., : x.shape[-1] // 2]
    right = x[..., x.shape[-1] // 2 :]
    return torch.cat([-right, left], dim=-1)


def apply_rotary_pos_emb(q: Tensor, k: Tensor, cos: Tensor, sin: Tensor) -> Tuple[Tensor, Tensor]:
    cos = cos.unsqueeze(1)
    sin = sin.unsqueeze(1)
    return (q * cos) + (rotate_half(q) * sin), (k * cos) + (rotate_half(k) * sin)


def repeat_kv(hidden_states: Tensor, n_rep: int) -> Tensor:
    batch_size, num_key_value_heads, seq_len, head_dim = hidden_states.shape
    if n_rep == 1:
        return hidden_states
    expanded = hidden_states[:, :, None, :, :].expand(batch_size, num_key_value_heads, n_rep, seq_len, head_dim)
    return expanded.reshape(batch_size, num_key_value_heads * n_rep, seq_len, head_dim)


class GemmaAttention(nn.Module):
    def __init__(self, config: GemmaConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = int(layer_idx)
        self.layer_type = config.layer_types[layer_idx]
        self.head_dim = config.head_dim
        self.num_attention_heads = config.num_attention_heads
        self.num_key_value_heads = config.num_key_value_heads
        self.num_key_value_groups = config.num_attention_heads // config.num_key_value_heads
        self.scaling = float(config.query_pre_attn_scalar) ** -0.5
        self.is_sliding = self.layer_type == "sliding_attention"
        self.sliding_window = config.sliding_window if self.is_sliding else None
        self.attn_logit_softcapping = config.attn_logit_softcapping

        self.q_proj = nn.Linear(config.hidden_size, config.num_attention_heads * config.head_dim, bias=config.attention_bias)
        self.k_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * config.head_dim, bias=config.attention_bias)
        self.v_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * config.head_dim, bias=config.attention_bias)
        self.o_proj = nn.Linear(config.num_attention_heads * config.head_dim, config.hidden_size, bias=config.attention_bias)
        self.q_norm = GemmaRMSNorm(config.head_dim, eps=config.rms_norm_eps)
        self.k_norm = GemmaRMSNorm(config.head_dim, eps=config.rms_norm_eps)

    def forward(
        self,
        hidden_states: Tensor,
        position_embeddings: Tuple[Tensor, Tensor],
        layer_cache: LayerCache,
    ) -> Tuple[Tensor, LayerCache]:
        if hidden_states.shape[1] != 1:
            raise ValueError("This standalone Gemma implementation currently expects one token per decode step.")

        batch_size = hidden_states.shape[0]
        hidden_shape = (batch_size, 1, -1, self.head_dim)

        query_states = self.q_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        key_states = self.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        value_states = self.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)

        query_states = self.q_norm(query_states)
        key_states = self.k_norm(key_states)

        cos, sin = position_embeddings
        query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

        if layer_cache.keys is None:
            full_keys = key_states
            full_values = value_states
        else:
            full_keys = torch.cat([layer_cache.keys, key_states], dim=-2)
            full_values = torch.cat([layer_cache.values, value_states], dim=-2)

        if self.is_sliding and self.sliding_window is not None:
            keep_keys = full_keys[:, :, -self.sliding_window + 1 :, :]
            keep_values = full_values[:, :, -self.sliding_window + 1 :, :]
        else:
            keep_keys = full_keys
            keep_values = full_values

        layer_cache.keys = keep_keys
        layer_cache.values = keep_values

        key_states = repeat_kv(full_keys, self.num_key_value_groups)
        value_states = repeat_kv(full_values, self.num_key_value_groups)
        attn_weights = torch.matmul(query_states, key_states.transpose(2, 3)) * self.scaling

        if self.attn_logit_softcapping is not None:
            softcap = float(self.attn_logit_softcapping)
            attn_weights = torch.tanh(attn_weights / softcap) * softcap

        attn_weights = F.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query_states.dtype)
        attn_output = torch.matmul(attn_weights, value_states)
        attn_output = attn_output.transpose(1, 2).contiguous().reshape(batch_size, 1, -1)
        attn_output = self.o_proj(attn_output)
        return attn_output, layer_cache


class GemmaDecoderLayer(nn.Module):
    def __init__(self, config: GemmaConfig, layer_idx: int):
        super().__init__()
        self.attention_type = config.layer_types[layer_idx]
        self.self_attn = GemmaAttention(config, layer_idx)
        self.mlp = GemmaMLP(config)
        self.input_layernorm = GemmaRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = GemmaRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.pre_feedforward_layernorm = GemmaRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_feedforward_layernorm = GemmaRMSNorm(config.hidden_size, eps=config.rms_norm_eps)

    def forward(
        self,
        hidden_states: Tensor,
        position_embeddings: Tuple[Tensor, Tensor],
        layer_cache: LayerCache,
    ) -> Tuple[Tensor, LayerCache]:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states, layer_cache = self.self_attn(hidden_states, position_embeddings, layer_cache)
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = residual + hidden_states

        residual = hidden_states
        hidden_states = self.pre_feedforward_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = self.post_feedforward_layernorm(hidden_states)
        hidden_states = residual + hidden_states
        return hidden_states, layer_cache


class GemmaTextModel(nn.Module):
    def __init__(self, config: GemmaConfig):
        super().__init__()
        self.config = config
        self.embed_tokens = GemmaScaledWordEmbedding(
            config.vocab_size,
            config.hidden_size,
            config.pad_token_id,
            embed_scale=config.hidden_size**0.5,
        )
        self.layers = nn.ModuleList([GemmaDecoderLayer(config, idx) for idx in range(config.num_hidden_layers)])
        self.norm = GemmaRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.rotary_emb = GemmaRotaryEmbedding(config)

    def empty_cache(self) -> List[LayerCache]:
        return [LayerCache() for _ in range(self.config.num_hidden_layers)]

    def forward(
        self,
        input_ids: Tensor,
        past_key_values: Optional[List[LayerCache]] = None,
        start_pos: int = 0,
    ) -> Tuple[Tensor, List[LayerCache]]:
        if input_ids.ndim != 2:
            raise ValueError(f"Expected input_ids with shape [batch, seq], got {tuple(input_ids.shape)}")

        cache = past_key_values if past_key_values is not None else self.empty_cache()
        all_hidden_states: List[Tensor] = []

        for offset in range(input_ids.shape[1]):
            current_input = input_ids[:, offset : offset + 1]
            position_ids = torch.full(
                (current_input.shape[0], 1),
                start_pos + offset,
                dtype=torch.long,
                device=current_input.device,
            )
            hidden_states = self.embed_tokens(current_input)
            position_embeddings = {
                layer_type: self.rotary_emb(hidden_states, position_ids, layer_type)
                for layer_type in sorted(set(self.config.layer_types))
            }

            for layer_idx, decoder_layer in enumerate(self.layers):
                hidden_states, cache[layer_idx] = decoder_layer(
                    hidden_states,
                    position_embeddings=position_embeddings[decoder_layer.attention_type],
                    layer_cache=cache[layer_idx],
                )

            hidden_states = self.norm(hidden_states)
            all_hidden_states.append(hidden_states)

        return torch.cat(all_hidden_states, dim=1), cache


class GemmaForCausalLM(nn.Module):
    def __init__(self, config: GemmaConfig):
        super().__init__()
        self.config = config
        self.model = GemmaTextModel(config)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

    def tie_weights(self) -> None:
        self.lm_head.weight = self.model.embed_tokens.weight

    def forward(
        self,
        input_ids: Tensor,
        past_key_values: Optional[List[LayerCache]] = None,
        start_pos: int = 0,
    ) -> GemmaCausalLMOutput:
        hidden_states, cache = self.model(input_ids=input_ids, past_key_values=past_key_values, start_pos=start_pos)
        logits = self.lm_head(hidden_states)
        if self.config.final_logit_softcapping is not None:
            softcap = float(self.config.final_logit_softcapping)
            logits = torch.tanh(logits / softcap) * softcap
        return GemmaCausalLMOutput(logits=logits, past_key_values=cache, hidden_states=hidden_states)

    @classmethod
    def from_pretrained(
        cls,
        model_dir: str | Path,
        device: str | torch.device | None = None,
        dtype: torch.dtype = torch.float32,
    ) -> "GemmaForCausalLM":
        resolved_dir = _resolve_model_dir(model_dir)
        config = GemmaConfig.from_pretrained(resolved_dir)
        model = cls(config)
        state_dict = load_safetensor_state_dict(resolved_dir)
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        if unexpected:
            raise RuntimeError(f"Unexpected keys while loading Gemma weights: {unexpected}")
        missing_without_lm_head = [key for key in missing if key != "lm_head.weight"]
        if missing_without_lm_head:
            raise RuntimeError(f"Missing keys while loading Gemma weights: {missing_without_lm_head}")
        model.tie_weights()
        model.eval()
        target_device = device or infer_device()
        model.to(device=target_device, dtype=dtype)
        return model

    def clone_to(self, device: str | torch.device, dtype: torch.dtype = torch.float32) -> "GemmaForCausalLM":
        cloned = GemmaForCausalLM(self.config)
        cloned.load_state_dict(self.state_dict())
        cloned.tie_weights()
        cloned.eval()
        cloned.to(device=device, dtype=dtype)
        return cloned


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def named_transformer_linears(model: GemmaForCausalLM) -> Iterable[Tuple[str, nn.Linear]]:
    for layer_idx, layer in enumerate(model.model.layers):
        yield f"model.layers.{layer_idx}.self_attn.q_proj", layer.self_attn.q_proj
        yield f"model.layers.{layer_idx}.self_attn.k_proj", layer.self_attn.k_proj
        yield f"model.layers.{layer_idx}.self_attn.v_proj", layer.self_attn.v_proj
        yield f"model.layers.{layer_idx}.self_attn.o_proj", layer.self_attn.o_proj
        yield f"model.layers.{layer_idx}.mlp.gate_proj", layer.mlp.gate_proj
        yield f"model.layers.{layer_idx}.mlp.up_proj", layer.mlp.up_proj
        yield f"model.layers.{layer_idx}.mlp.down_proj", layer.mlp.down_proj

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.linalg import hadamard
from scipy.special import gammaln

from gemma import GemmaForCausalLM, named_transformer_linears


def solve_lloyd_max_codebook_from_data(
    values: np.ndarray,
    bits: int,
    max_iter: int = 200,
    tol: float = 1e-8,
) -> torch.Tensor:
    """Lloyd-Max codebook trained on actual scalar data.

    Treats all values as draws from the same 1D distribution (e.g. all
    post-rotation unit-vector coordinates from one weight matrix).
    Initializes centroids at empirical quantiles, then iterates.

    Uses searchsorted on the pre-sorted values for O(n log k) per iteration
    instead of O(n * k) boolean masks.
    """
    num_centroids = 2 ** bits
    if num_centroids <= 1:
        return torch.tensor([0.0], dtype=torch.float32)
    values = np.sort(values.astype(np.float64))
    n = len(values)
    quantiles = np.linspace(0.0, 1.0, num_centroids + 2, dtype=np.float64)[1:-1]
    centroids = np.quantile(values, quantiles)
    centroids = np.sort(np.clip(centroids, -1.0, 1.0))
    # Precompute cumulative sum for fast segment means
    cumsum = np.concatenate(([0.0], np.cumsum(values)))
    for _ in range(max_iter):
        midpoints = (centroids[:-1] + centroids[1:]) / 2.0
        # boundaries[i] is the left edge of bin i in the sorted values array
        bin_edges = np.searchsorted(values, midpoints)  # (k-1,) indices
        starts = np.concatenate(([0], bin_edges))
        stops  = np.concatenate((bin_edges, [n]))
        updated = centroids.copy()
        for idx in range(num_centroids):
            s, e = int(starts[idx]), int(stops[idx])
            if e > s:
                updated[idx] = (cumsum[e] - cumsum[s]) / (e - s)
        updated = np.sort(np.clip(updated, -1.0, 1.0))
        if np.max(np.abs(updated - centroids)) < tol:
            centroids = updated
            break
        centroids = updated
    return torch.from_numpy(centroids.astype(np.float32))


def beta_coordinate_pdf(x: np.ndarray, head_dim: int) -> np.ndarray:
    log_coefficient = (
        gammaln(head_dim / 2.0)
        - 0.5 * math.log(math.pi)
        - gammaln((head_dim - 1.0) / 2.0)
    )
    coefficient = math.exp(log_coefficient)
    return coefficient * np.power(np.clip(1.0 - x * x, 0.0, None), (head_dim - 3.0) / 2.0)


def weighted_quantile_grid(grid: np.ndarray, weights: np.ndarray, quantiles: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(weights)
    cumulative = cumulative / cumulative[-1]
    return np.interp(quantiles, cumulative, grid)


def solve_lloyd_max_codebook(
    head_dim: int,
    bits: int,
    grid_size: int = 200001,
    max_iter: int = 200,
    tol: float = 1e-8,
) -> torch.Tensor:
    num_centroids = 2**bits
    if num_centroids <= 1:
        return torch.tensor([0.0], dtype=torch.float32)

    grid = np.linspace(-1.0, 1.0, grid_size, dtype=np.float64)
    weights = beta_coordinate_pdf(grid, head_dim=head_dim)
    quantiles = np.linspace(0.0, 1.0, num_centroids + 2, dtype=np.float64)[1:-1]
    centroids = weighted_quantile_grid(grid, weights, quantiles)
    centroids = np.sort(np.clip(centroids, -1.0, 1.0))

    for _ in range(max_iter):
        boundaries = np.concatenate(([-1.0], (centroids[:-1] + centroids[1:]) / 2.0, [1.0]))
        updated = centroids.copy()
        for idx in range(num_centroids):
            left = boundaries[idx]
            right = boundaries[idx + 1]
            if idx == num_centroids - 1:
                mask = (grid >= left) & (grid <= right)
            else:
                mask = (grid >= left) & (grid < right)
            bucket_weights = weights[mask]
            bucket_grid = grid[mask]
            if bucket_weights.sum() > 0:
                updated[idx] = float((bucket_grid * bucket_weights).sum() / bucket_weights.sum())
        updated = np.sort(np.clip(updated, -1.0, 1.0))
        if np.max(np.abs(updated - centroids)) < tol:
            centroids = updated
            break
        centroids = updated

    return torch.from_numpy(centroids.astype(np.float32))


def quantize_tensor_with_codebook(tensor: torch.Tensor, codebook: torch.Tensor) -> torch.Tensor:
    flat = tensor.float().reshape(-1, tensor.shape[-1])
    codebook = codebook.to(device=flat.device, dtype=flat.dtype)
    distances = torch.abs(flat.unsqueeze(-1) - codebook.view(1, 1, -1))
    indices = distances.argmin(dim=-1)
    return indices.reshape(tensor.shape)


def dequantize_tensor_with_codebook(indices: torch.Tensor, codebook: torch.Tensor) -> torch.Tensor:
    return codebook[indices.long()]


def make_random_rotation_matrix(head_dim: int, seed: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    gaussian = torch.randn(head_dim, head_dim, generator=generator, dtype=torch.float32)
    q, r = torch.linalg.qr(gaussian, mode="reduced")
    diag = torch.sign(torch.diagonal(r))
    diag[diag == 0] = 1
    return (q * diag).contiguous()


def is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def make_randomized_hadamard_matrix(head_dim: int, seed: int) -> torch.Tensor:
    if not is_power_of_two(head_dim):
        raise ValueError(f"Hadamard stage-1 requires a power-of-two width, got {head_dim}.")

    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    base = torch.from_numpy(hadamard(head_dim, dtype=float) / math.sqrt(head_dim)).to(torch.float32)
    left_signs = (2 * torch.randint(0, 2, (head_dim,), generator=generator, dtype=torch.int64) - 1).to(torch.float32)
    right_signs = (2 * torch.randint(0, 2, (head_dim,), generator=generator, dtype=torch.int64) - 1).to(torch.float32)
    permutation = torch.randperm(head_dim, generator=generator)
    rotation = left_signs.unsqueeze(1) * base * right_signs.unsqueeze(0)
    return rotation[:, permutation].contiguous()


def normalize_rotation_family(rotation_family: str) -> str:
    family = str(rotation_family).strip().lower()
    if family in {"orthogonal", "random_orthogonal", "qr"}:
        return "orthogonal"
    if family in {"hadamard", "random_hadamard"}:
        return "hadamard"
    raise ValueError(f"Unsupported stage-1 rotation family: {rotation_family}")


def make_qjl_matrix(sketch_dim: int, head_dim: int, seed: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    # Use the standard QJL convention: rows ~ N(0, I). The estimator then carries the 1/m factor.
    return torch.randn(sketch_dim, head_dim, generator=generator, dtype=torch.float32)


@dataclass(frozen=True)
class TurboQuantSettings:
    bits: int
    sketch_dim: int
    sketch_label: str
    seed: int = 1234


@dataclass
class QuantizedLinearReport:
    name: str
    in_features: int
    out_features: int
    bits: int
    sketch_dim: int
    rotation_family: str
    approximate_bits_per_weight: float
    stage1_bits: int
    qjl_bits_per_weight: float
    exact_outlier_count: int
    exact_outlier_bits_per_weight: float
    input_scale_bits_per_weight: float


class SharedTransformBank:
    def __init__(self, seed: int = 1234):
        self.seed = int(seed)
        self.rotation_cache: Dict[Tuple[int, str, int], torch.Tensor] = {}
        self.qjl_cache: Dict[Tuple[int, int], torch.Tensor] = {}
        self.codebook_cache: Dict[Tuple[int, int], torch.Tensor] = {}

    def rotation(self, head_dim: int, family: str = "orthogonal", variant: int = 0) -> torch.Tensor:
        normalized_family = normalize_rotation_family(family)
        key = (head_dim, normalized_family, int(variant))
        if key not in self.rotation_cache:
            seed = self.seed + 17 * head_dim + 7919 * int(variant)
            if normalized_family == "orthogonal":
                rotation = make_random_rotation_matrix(head_dim, seed=seed)
            else:
                rotation = make_randomized_hadamard_matrix(head_dim, seed=seed)
            self.rotation_cache[key] = rotation
        return self.rotation_cache[key]

    def qjl_matrix(self, head_dim: int, sketch_dim: int) -> torch.Tensor:
        key = (head_dim, sketch_dim)
        if key not in self.qjl_cache:
            self.qjl_cache[key] = make_qjl_matrix(sketch_dim, head_dim, seed=self.seed + 1009 * head_dim + sketch_dim)
        return self.qjl_cache[key]

    def codebook(self, head_dim: int, bits: int) -> torch.Tensor:
        key = (head_dim, bits)
        if key not in self.codebook_cache:
            self.codebook_cache[key] = solve_lloyd_max_codebook(head_dim=head_dim, bits=bits)
        return self.codebook_cache[key]


def normalize_input_scale(input_scale: torch.Tensor, in_features: int, *, dtype: torch.dtype) -> torch.Tensor:
    scale = torch.as_tensor(input_scale, dtype=dtype, device="cpu").reshape(-1).contiguous()
    if scale.numel() != in_features:
        raise ValueError(f"Expected input scale with {in_features} values, got {scale.numel()}.")
    return scale.clamp_min(1e-6)


def normalize_group_pre_scale(group_pre_scale: torch.Tensor, group_size: int, *, dtype: torch.dtype) -> torch.Tensor:
    scale = torch.as_tensor(group_pre_scale, dtype=dtype, device="cpu").reshape(-1).contiguous()
    if scale.numel() != group_size:
        raise ValueError(f"Expected group pre-scale with {group_size} values, got {scale.numel()}.")
    scale = scale.clamp_min(1e-6)
    return scale / torch.exp(torch.mean(torch.log(scale)))


def fit_group_pre_scale(
    weight: torch.Tensor,
    *,
    bits: int,
    transform_bank: SharedTransformBank,
    group_size: int,
    rotation_family: str = "hadamard",
    input_scale: torch.Tensor | None = None,
    balance_iters: int = 12,
    balance_lr: float = 0.5,
    alpha_grid: Iterable[float] | None = None,
    max_scale_factor: float = 4.0,
    max_sampled_groups: int = 16,
    max_sampled_rows_per_group: int = 512,
    seed: int = 1234,
) -> tuple[torch.Tensor, Dict[str, object]]:
    """Fit a shared per-layer group pre-scale to improve group isotropy for VQ.

    The returned vector has length `group_size` and is shared across all full
    groups in the layer. It is applied elementwise before row-normalisation and
    rotation, then inverted after reconstruction.
    """
    weight = weight.float().cpu().contiguous()
    out_features, in_features = weight.shape
    group_size = int(group_size)
    if group_size <= 0 or group_size >= in_features:
        ones = torch.ones(max(1, group_size), dtype=torch.float32)
        return ones, {
            "alpha": 0.0,
            "quant_mse": 0.0,
            "covariance_fro": 0.0,
            "diag_std": 0.0,
            "num_sampled_groups": 0,
            "num_sampled_rows": 0,
            "evaluated_alphas": [0.0],
        }

    input_scale_tensor = None
    weight_for_quant = weight
    if input_scale is not None:
        input_scale_tensor = normalize_input_scale(input_scale, in_features, dtype=weight.dtype)
        weight_for_quant = weight * input_scale_tensor.unsqueeze(0)

    num_full_groups = in_features // group_size
    if num_full_groups <= 0:
        ones = torch.ones(group_size, dtype=torch.float32)
        return ones, {
            "alpha": 0.0,
            "quant_mse": 0.0,
            "covariance_fro": 0.0,
            "diag_std": 0.0,
            "num_sampled_groups": 0,
            "num_sampled_rows": 0,
            "evaluated_alphas": [0.0],
        }

    groups = weight_for_quant[:, : num_full_groups * group_size].reshape(out_features, num_full_groups, group_size)
    groups = groups.permute(1, 0, 2).contiguous()  # (num_groups, out, group_size)

    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))

    if groups.shape[0] > max_sampled_groups:
        group_idx = torch.randperm(groups.shape[0], generator=generator)[:max_sampled_groups]
        groups = groups[group_idx]
    if groups.shape[1] > max_sampled_rows_per_group:
        row_idx = torch.randperm(groups.shape[1], generator=generator)[:max_sampled_rows_per_group]
        groups = groups[:, row_idx]

    samples = groups.reshape(-1, group_size).contiguous()
    target_diag = 1.0 / float(group_size)
    log_limit = math.log(max(1.0, float(max_scale_factor)))
    log_scale = torch.zeros(group_size, dtype=torch.float32)

    def isotropy_metrics(scale: torch.Tensor) -> tuple[float, float]:
        transformed = samples * scale.unsqueeze(0)
        unit = transformed / torch.linalg.norm(transformed, dim=1, keepdim=True).clamp_min(1e-8)
        covariance = (unit.T @ unit) / max(1, unit.shape[0])
        diag = covariance.diagonal()
        diag_std = float(torch.sqrt(torch.mean((diag - target_diag) ** 2)).item())
        covariance_fro = float(torch.linalg.norm(covariance - torch.eye(group_size, dtype=unit.dtype) * target_diag).item())
        return diag_std, covariance_fro

    for _ in range(max(0, int(balance_iters))):
        scale = torch.exp(log_scale)
        transformed = samples * scale.unsqueeze(0)
        unit = transformed / torch.linalg.norm(transformed, dim=1, keepdim=True).clamp_min(1e-8)
        second_moment = unit.pow(2).mean(dim=0).clamp_min(1e-8)
        log_scale = log_scale + float(balance_lr) * 0.5 * torch.log(torch.full_like(second_moment, target_diag) / second_moment)
        log_scale = log_scale - log_scale.mean()
        if log_limit > 0.0:
            log_scale = log_scale.clamp(-log_limit, log_limit)

    raw_scale = torch.exp(log_scale)
    raw_scale = raw_scale / torch.exp(torch.mean(torch.log(raw_scale)))

    if alpha_grid is None:
        alpha_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    else:
        alpha_values = [float(alpha) for alpha in alpha_grid]
        if not alpha_values:
            raise ValueError("alpha_grid must not be empty.")

    best_scale = torch.ones(group_size, dtype=torch.float32)
    best_report: Dict[str, object] = {
        "alpha": 0.0,
        "quant_mse": float("inf"),
        "covariance_fro": float("inf"),
        "diag_std": float("inf"),
        "num_sampled_groups": int(groups.shape[0]),
        "num_sampled_rows": int(groups.shape[1]),
        "evaluated_alphas": alpha_values,
    }

    normalized_family = normalize_rotation_family(rotation_family)
    for alpha in alpha_values:
        candidate = torch.exp(torch.log(raw_scale) * float(alpha))
        candidate = candidate / torch.exp(torch.mean(torch.log(candidate)))
        if max_scale_factor > 1.0:
            candidate = candidate.clamp(1.0 / max_scale_factor, max_scale_factor)
            candidate = candidate / torch.exp(torch.mean(torch.log(candidate)))

        reconstruction, quant_mse = _quantize_stage1_group(
            samples,
            bits=bits,
            transform_bank=transform_bank,
            rotation_family=normalized_family,
            group_pre_scale=candidate,
        )
        diag_std, covariance_fro = isotropy_metrics(candidate)
        if quant_mse < float(best_report["quant_mse"]):
            best_report = {
                "alpha": float(alpha),
                "quant_mse": float(quant_mse),
                "covariance_fro": covariance_fro,
                "diag_std": diag_std,
                "num_sampled_groups": int(groups.shape[0]),
                "num_sampled_rows": int(groups.shape[1]),
                "evaluated_alphas": alpha_values,
            }
            best_scale = candidate

    return best_scale.contiguous(), best_report


def _fit_single_group_pre_scale(
    group: torch.Tensor,
    *,
    bits: int,
    transform_bank: SharedTransformBank,
    rotation_family: str,
    balance_iters: int = 12,
    balance_lr: float = 0.5,
    alpha_grid: list | None = None,
    max_scale_factor: float = 4.0,
) -> torch.Tensor:
    """Fit a per-group pre-scale on a single (out_f, group_dim) weight block.

    Lighter version of fit_group_pre_scale designed to run inside the GPTQ loop
    on the current working weights (already modified by prior suffix updates).
    No group subsampling — operates directly on the provided block.
    """
    group = group.float().contiguous()
    group_dim = group.shape[1]
    target_diag = 1.0 / float(group_dim)
    log_limit = math.log(max(1.0, float(max_scale_factor)))
    log_scale = torch.zeros(group_dim, dtype=torch.float32)

    samples = group  # use all rows directly
    for _ in range(max(0, int(balance_iters))):
        scale = torch.exp(log_scale)
        transformed = samples * scale.unsqueeze(0)
        norms = torch.linalg.norm(transformed, dim=1, keepdim=True).clamp_min(1e-8)
        unit = transformed / norms
        second_moment = unit.pow(2).mean(dim=0).clamp_min(1e-8)
        log_scale = log_scale + float(balance_lr) * 0.5 * torch.log(
            torch.full_like(second_moment, target_diag) / second_moment
        )
        log_scale = log_scale - log_scale.mean()
        if log_limit > 0.0:
            log_scale = log_scale.clamp(-log_limit, log_limit)

    raw_scale = torch.exp(log_scale)
    raw_scale = raw_scale / torch.exp(torch.mean(torch.log(raw_scale)))

    if alpha_grid is None:
        alpha_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    else:
        alpha_values = [float(a) for a in alpha_grid]

    normalized_family = normalize_rotation_family(rotation_family)
    best_scale = torch.ones(group_dim, dtype=torch.float32)
    best_mse = float("inf")
    for alpha in alpha_values:
        candidate = torch.exp(torch.log(raw_scale) * float(alpha))
        candidate = candidate / torch.exp(torch.mean(torch.log(candidate)))
        if max_scale_factor > 1.0:
            candidate = candidate.clamp(1.0 / max_scale_factor, max_scale_factor)
            candidate = candidate / torch.exp(torch.mean(torch.log(candidate)))
        _, mse = _quantize_stage1_group(
            samples,
            bits=bits,
            transform_bank=transform_bank,
            rotation_family=normalized_family,
            group_pre_scale=candidate,
        )
        if mse < best_mse:
            best_mse = mse
            best_scale = candidate

    return best_scale.contiguous()


def fit_layer_scale_and_codebook(
    weight: torch.Tensor,
    *,
    bits: int,
    transform_bank: SharedTransformBank,
    group_size: int = 128,
    rotation_family: str = "hadamard",
    input_scale: torch.Tensor | None = None,
    balance_iters: int = 12,
    balance_lr: float = 0.5,
    max_scale_factor: float = 4.0,
    lloyd_max_iters: int = 200,
    max_vectors_for_codebook: int = 500_000,
    seed: int = 1234,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Fit a per-layer pre-scale and a matching data-driven codebook.

    Step 1: Run balance iterations on sampled groups to learn a scale
            s ∈ R^group_size that makes unit-vector coordinates isotropic.
    Step 2: Apply s to ALL groups in the layer, row-normalize, rotate.
    Step 3: Collect all post-rotation scalar coordinates and run Lloyd-Max
            to build a codebook matched to the actual scaled distribution.

    Returns:
        scale    — (group_size,) fp32 scale vector, geometric mean = 1
        codebook — (2**bits,) fp32 codebook, same format as solve_lloyd_max_codebook
    """
    weight = weight.float().cpu().contiguous()
    out_features, in_features = weight.shape
    group_size = int(group_size)
    normalized_family = normalize_rotation_family(rotation_family)

    weight_for_quant = weight
    if input_scale is not None:
        input_scale_tensor = normalize_input_scale(input_scale, in_features, dtype=weight.dtype)
        weight_for_quant = weight * input_scale_tensor.unsqueeze(0)

    num_groups = in_features // group_size  # full groups only
    if num_groups == 0:
        scale = torch.ones(group_size, dtype=torch.float32)
        codebook = solve_lloyd_max_codebook(head_dim=group_size, bits=bits)
        return scale, codebook

    # ── Step 1: fit scale on sampled groups ───────────────────────────────────
    groups_3d = weight_for_quant[:, :num_groups * group_size].reshape(
        out_features, num_groups, group_size
    ).permute(1, 0, 2)  # (num_groups, out, group_size)

    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    max_sample_groups = 16
    max_sample_rows = 512
    if groups_3d.shape[0] > max_sample_groups:
        gi = torch.randperm(groups_3d.shape[0], generator=generator)[:max_sample_groups]
        samples_3d = groups_3d[gi]
    else:
        samples_3d = groups_3d
    if samples_3d.shape[1] > max_sample_rows:
        ri = torch.randperm(samples_3d.shape[1], generator=generator)[:max_sample_rows]
        samples_3d = samples_3d[:, ri]
    samples = samples_3d.reshape(-1, group_size)

    target_diag = 1.0 / float(group_size)
    log_limit = math.log(max(1.0, float(max_scale_factor)))
    log_scale = torch.zeros(group_size, dtype=torch.float32)
    for _ in range(max(0, int(balance_iters))):
        s = torch.exp(log_scale)
        transformed = samples * s.unsqueeze(0)
        norms = torch.linalg.norm(transformed, dim=1, keepdim=True).clamp_min(1e-8)
        unit = transformed / norms
        second_moment = unit.pow(2).mean(dim=0).clamp_min(1e-8)
        log_scale = log_scale + float(balance_lr) * 0.5 * torch.log(
            torch.full_like(second_moment, target_diag) / second_moment
        )
        log_scale = log_scale - log_scale.mean()
        if log_limit > 0.0:
            log_scale = log_scale.clamp(-log_limit, log_limit)
    scale = torch.exp(log_scale)
    scale = scale / torch.exp(torch.mean(torch.log(scale)))

    # ── Step 2: collect post-scale, post-normalize, post-rotate coordinates ───
    rotation = transform_bank.rotation(group_size, family=normalized_family).to(dtype=torch.float32)
    all_groups = groups_3d.reshape(-1, group_size)  # (num_groups * out, group_size)

    # subsample if too many vectors
    n_vecs = all_groups.shape[0]
    if n_vecs > max_vectors_for_codebook:
        idx = torch.randperm(n_vecs, generator=generator)[:max_vectors_for_codebook]
        all_groups = all_groups[idx]

    scaled = all_groups * scale.unsqueeze(0)
    norms = torch.linalg.norm(scaled, dim=1, keepdim=True).clamp_min(1e-8)
    unit = scaled / norms
    rotated = unit @ rotation  # (N, group_size)

    # ── Step 3: Lloyd-Max on the empirical 1D distribution ────────────────────
    flat_values = rotated.numpy().ravel()
    codebook = solve_lloyd_max_codebook_from_data(flat_values, bits=bits, max_iter=lloyd_max_iters)

    return scale.contiguous(), codebook.contiguous()


def capture_linear_inputs(
    model: GemmaForCausalLM,
    input_ids: torch.Tensor,
    target_names: Iterable[str],
    *,
    max_samples_per_layer: int,
    device: str,
) -> Dict[str, torch.Tensor]:
    module_map = {name: module for name, module in model.named_modules() if isinstance(module, nn.Linear)}
    buffers: Dict[str, List[torch.Tensor]] = {name: [] for name in target_names}
    handles = []

    for name in target_names:
        if name not in module_map:
            raise ValueError(f"Unknown linear target: {name}")
        module = module_map[name]

        def make_hook(module_name: str):
            def hook(_module: nn.Module, args):
                current_count = sum(chunk.shape[0] for chunk in buffers[module_name])
                if current_count >= max_samples_per_layer:
                    return
                x = args[0].detach().float().reshape(-1, args[0].shape[-1]).cpu()
                remaining = max_samples_per_layer - current_count
                if remaining > 0:
                    buffers[module_name].append(x[:remaining])

            return hook

        handles.append(module.register_forward_pre_hook(make_hook(name)))

    model.eval()
    with torch.no_grad():
        model(input_ids.to(device))

    for handle in handles:
        handle.remove()

    return {name: torch.cat(chunks, dim=0) for name, chunks in buffers.items() if chunks}


def _compute_hessian_inv(
    activations: torch.Tensor,
    in_features: int,
    input_scale_tensor: torch.Tensor | None,
    damping: float,
) -> torch.Tensor | None:
    """Compute inverse input-covariance matrix for Hessian compensation.

    Works in the scaled activation space so it matches the weight space we
    actually quantize in (W_scaled = W * input_scale).
    """
    try:
        X = activations.float().reshape(-1, in_features).cpu()
        if input_scale_tensor is not None:
            X = X / input_scale_tensor.unsqueeze(0)
        H = (X.T @ X) / max(1, X.shape[0])
        damp = float(damping) * float(H.diagonal().mean().item())
        H.diagonal().add_(damp)
        return torch.linalg.inv(H)
    except Exception:
        return None


def _prepare_gptq_block(
    H_inv: torch.Tensor | None,
    start: int,
    stop: int,
) -> tuple[torch.Tensor | None, torch.Tensor | None]:
    """Return block whitening Cholesky and GPTQ update for a contiguous block.

    Let M = H^{-1}_suffix for the current suffix. For block B, the exact GPTQ
    conditional loss after optimising the remaining columns is

        tr(E_B S_B E_B^T),   with   S_B = M_BB^{-1}.

    If M_BB = L L^T (Cholesky), then S_B = L^{-T} L^{-1}, so whitening a row
    vector by right-multiplying with L^{-T} makes the block loss Euclidean.
    """
    if H_inv is None:
        return None, None

    try:
        M_bb = H_inv[start:stop, start:stop]
        M_bb = 0.5 * (M_bb + M_bb.T)
        chol = torch.linalg.cholesky(M_bb)
    except Exception:
        return None, None

    update = None
    if stop < H_inv.shape[0]:
        try:
            update = torch.cholesky_solve(H_inv[start:stop, stop:], chol, upper=False)
        except Exception:
            update = None

    return chol, update


def _whiten_group_for_gptq_metric(
    group: torch.Tensor,
    block_cholesky: torch.Tensor | None,
) -> torch.Tensor:
    if block_cholesky is None:
        return group
    return torch.linalg.solve_triangular(
        block_cholesky,
        group.T.contiguous(),
        upper=False,
        left=True,
    ).T.contiguous()


def _unwhiten_group_from_gptq_metric(
    whitened_group: torch.Tensor,
    block_cholesky: torch.Tensor | None,
) -> torch.Tensor:
    if block_cholesky is None:
        return whitened_group
    return (whitened_group @ block_cholesky.T).contiguous()


def _quantize_stage1_group(
    group: torch.Tensor,
    *,
    bits: int,
    transform_bank: SharedTransformBank,
    rotation_family: str,
    block_cholesky: torch.Tensor | None = None,
    group_pre_scale: torch.Tensor | None = None,
    use_rotation: bool = True,
    layer_codebook: torch.Tensor | None = None,
) -> tuple[torch.Tensor, float]:
    """Quantize one group using spherical VQ in original row-normalised space.

    block_cholesky is accepted for API compatibility (used by the caller for
    the GPTQ suffix update) but is NOT applied before VQ — the codebook was
    built for isotropically distributed unit vectors in the original space, and
    pre-whitening by L^{-T} distorts that distribution, degrading VQ quality.
    The suffix update (handled by the caller via cholesky_solve) is where the
    Hessian metric is correctly applied.
    """
    original_group = group.float().contiguous()
    group = original_group
    group_dim = group.shape[1]
    scale_slice = None
    if group_pre_scale is not None:
        scale_slice = group_pre_scale[:group_dim].to(dtype=group.dtype).clamp_min(1e-6)
        group = group * scale_slice.unsqueeze(0)

    group_norms = torch.linalg.norm(group, dim=1).clamp_min(1e-8)
    unit_group = group / group_norms.unsqueeze(-1)

    if use_rotation:
        rotation = transform_bank.rotation(group_dim, family=rotation_family).to(dtype=group.dtype)
        quant_input = unit_group @ rotation
    else:
        rotation = None
        quant_input = unit_group

    if layer_codebook is not None:
        codebook = layer_codebook.to(dtype=group.dtype)
    else:
        codebook = transform_bank.codebook(group_dim, bits).to(dtype=group.dtype)
    group_indices = quantize_tensor_with_codebook(quant_input, codebook)
    group_quant = dequantize_tensor_with_codebook(group_indices, codebook)

    if rotation is not None:
        recon_unit = group_quant @ rotation.T
    else:
        recon_unit = group_quant

    reconstruction = recon_unit * group_norms.unsqueeze(-1)
    if scale_slice is not None:
        reconstruction = reconstruction / scale_slice.unsqueeze(0)

    local_mse = float((original_group - reconstruction).pow(2).mean().item())
    return reconstruction.contiguous(), local_mse


def stage1_reconstruct_weight(
    weight: torch.Tensor,
    *,
    bits: int,
    transform_bank: SharedTransformBank,
    group_size: int | None = None,
    rotation_family: str = "orthogonal",
    input_scale: torch.Tensor | None = None,
    exact_outlier_count: int = 0,
    svd_rank: int = 0,
    per_group_outlier_count: int = 0,
    activations: torch.Tensor | None = None,
    hessian_damping: float = 0.01,
    group_pre_scale: torch.Tensor | None = None,
    fit_per_group_pre_scale: bool = False,
    layer_codebook: torch.Tensor | None = None,
    bits_per_group: list | None = None,
) -> tuple[torch.Tensor, float]:
    weight = weight.float().cpu().contiguous()
    out_features, in_features = weight.shape
    normalized_rotation_family = normalize_rotation_family(rotation_family)
    scale_bits_per_weight = 0.0
    input_scale_tensor = None
    weight_for_quant = weight

    if input_scale is not None:
        input_scale_tensor = normalize_input_scale(input_scale, in_features, dtype=weight.dtype)
        weight_for_quant = weight * input_scale_tensor.unsqueeze(0)
        scale_bits_per_weight = 16.0 / float(out_features)

    if group_size is None or int(group_size) <= 0 or int(group_size) >= in_features:
        rotation = transform_bank.rotation(in_features, family=normalized_rotation_family).to(dtype=weight.dtype)
        codebook = transform_bank.codebook(in_features, bits).to(dtype=weight.dtype)

        row_norms = torch.linalg.norm(weight_for_quant, dim=1).clamp_min(1e-8)
        unit_weight = weight_for_quant / row_norms.unsqueeze(-1)
        rotated_weight = unit_weight @ rotation
        stage1_indices = quantize_tensor_with_codebook(rotated_weight, codebook)
        stage1_rot = dequantize_tensor_with_codebook(stage1_indices, codebook)
        stage1_reconstruction = (stage1_rot @ rotation.T) * row_norms.unsqueeze(-1)
        if input_scale_tensor is not None:
            stage1_reconstruction = stage1_reconstruction / input_scale_tensor.unsqueeze(0)
        average_bits_per_weight = bits + 16.0 / in_features + scale_bits_per_weight
        if exact_outlier_count > 0:
            k = min(int(exact_outlier_count), in_features)
            residual = weight - stage1_reconstruction
            _, exact_outlier_indices = residual.abs().topk(k, dim=1)
            exact_outlier_values = torch.gather(residual, dim=1, index=exact_outlier_indices)
            stage1_reconstruction = stage1_reconstruction.scatter_add(1, exact_outlier_indices, exact_outlier_values)
            index_bits = math.ceil(math.log2(in_features))
            average_bits_per_weight += k * (index_bits + 16.0) / float(in_features)
        if svd_rank > 0:
            residual = weight - stage1_reconstruction
            U, S, Vh = torch.linalg.svd(residual, full_matrices=False)
            r = min(int(svd_rank), S.shape[0])
            stage1_reconstruction = stage1_reconstruction + (U[:, :r] * S[:r].unsqueeze(0)) @ Vh[:r, :]
            average_bits_per_weight += r * float(out_features + in_features) * 16.0 / float(out_features * in_features)
        return stage1_reconstruction.contiguous(), average_bits_per_weight

    group_size = int(group_size)
    num_groups = math.ceil(in_features / group_size)
    group_pre_scale_tensor = None
    group_pre_scale_bits_per_weight = 0.0
    if group_pre_scale is not None and not fit_per_group_pre_scale:
        group_pre_scale_tensor = normalize_group_pre_scale(group_pre_scale, group_size, dtype=weight.dtype)
        group_pre_scale_bits_per_weight = 16.0 * group_size / float(out_features * in_features)
    if fit_per_group_pre_scale:
        # Each group gets its own scale vector (one per group, fitted inside the loop).
        # Storage: num_groups × group_size × 16 bits = 16/out_features bits/weight.
        group_pre_scale_bits_per_weight = 16.0 / float(out_features)

    # Hessian compensation: compute H_inv once in scaled activation space.
    # Operates entirely in weight_for_quant space; de-scaling happens after the loop.
    H_inv = None
    if activations is not None:
        H_inv = _compute_hessian_inv(activations, in_features, input_scale_tensor, hessian_damping)

    # W_working is the mutable weight copy that gets updated by cross-group compensation.
    # When no compensation is used it is just an alias (no extra memory).
    W_working = weight_for_quant.clone() if H_inv is not None else weight_for_quant

    reconstructed_groups = []
    for group_idx in range(num_groups):
        start = group_idx * group_size
        stop = min(start + group_size, in_features)
        group = W_working[:, start:stop]
        block_cholesky, gptq_update = _prepare_gptq_block(H_inv, start, stop)

        # Determine which pre-scale to use for this group.
        if fit_per_group_pre_scale:
            active_pre_scale = _fit_single_group_pre_scale(
                group,
                bits=bits,
                transform_bank=transform_bank,
                rotation_family=normalized_rotation_family,
            )
        else:
            active_pre_scale = group_pre_scale_tensor

        group_bits = bits_per_group[group_idx] if bits_per_group is not None else bits
        group_reconstruction, _ = _quantize_stage1_group(
            group,
            bits=group_bits,
            transform_bank=transform_bank,
            rotation_family=normalized_rotation_family,
            block_cholesky=block_cholesky,
            group_pre_scale=active_pre_scale,
            layer_codebook=layer_codebook,
        )

        # Propagate this group's quantization error into remaining groups.
        if gptq_update is not None:
            error = group - group_reconstruction  # (out, g) in scaled space
            W_working[:, stop:] = W_working[:, stop:] - error @ gptq_update

        reconstructed_groups.append(group_reconstruction)

    reconstruction = torch.cat(reconstructed_groups, dim=1).contiguous()
    if input_scale_tensor is not None:
        reconstruction = reconstruction / input_scale_tensor.unsqueeze(0)
    avg_index_bits = (sum(bits_per_group) / num_groups) if bits_per_group is not None else float(bits)
    # Layer codebook: 2^bits fp32 values, shared across all groups in this layer.
    layer_codebook_bits_per_weight = (
        float(2 ** bits) * 32.0 / float(out_features * in_features)
        if layer_codebook is not None else 0.0
    )
    average_bits_per_weight = (
        avg_index_bits
        + 16.0 * num_groups / float(in_features)
        + scale_bits_per_weight
        + group_pre_scale_bits_per_weight
        + layer_codebook_bits_per_weight
    )
    if per_group_outlier_count > 0:
        group_index_bits = math.ceil(math.log2(max(2, group_size)))
        for group_idx in range(num_groups):
            start = group_idx * group_size
            stop = min(start + group_size, in_features)
            group_width = stop - start
            k = min(int(per_group_outlier_count), group_width)
            group_residual = weight[:, start:stop] - reconstruction[:, start:stop]
            _, outlier_idx = group_residual.abs().topk(k, dim=1)
            outlier_vals = torch.gather(group_residual, dim=1, index=outlier_idx)
            reconstruction[:, start:stop] = reconstruction[:, start:stop].scatter_add(1, outlier_idx, outlier_vals)
        average_bits_per_weight += per_group_outlier_count * num_groups * (group_index_bits + 16.0) / float(in_features)
    if exact_outlier_count > 0:
        k = min(int(exact_outlier_count), in_features)
        residual = weight - reconstruction
        _, exact_outlier_indices = residual.abs().topk(k, dim=1)
        exact_outlier_values = torch.gather(residual, dim=1, index=exact_outlier_indices)
        reconstruction = reconstruction.scatter_add(1, exact_outlier_indices, exact_outlier_values)
        index_bits = math.ceil(math.log2(in_features))
        average_bits_per_weight += k * (index_bits + 16.0) / float(in_features)
    if svd_rank > 0:
        residual = weight - reconstruction
        U, S, Vh = torch.linalg.svd(residual, full_matrices=False)
        r = min(int(svd_rank), S.shape[0])
        reconstruction = reconstruction + (U[:, :r] * S[:r].unsqueeze(0)) @ Vh[:r, :]
        average_bits_per_weight += r * float(out_features + in_features) * 16.0 / float(out_features * in_features)
    return reconstruction, average_bits_per_weight


def train_residual_vq_codebook(
    residual_vectors: torch.Tensor,
    num_codewords: int = 256,
    n_iter: int = 100,
    max_train_vectors: int = 50000,
    seed: int = 0,
) -> torch.Tensor:
    """K-means VQ codebook trained on stage-1 residual vectors.

    Args:
        residual_vectors: (N, group_size) tensor of residual subvectors.
        num_codewords: codebook size K; storage cost = log2(K) / group_size bits/weight.
        n_iter: max k-means iterations.
        max_train_vectors: subsample if N > this to keep training tractable.
        seed: random seed for subsampling and k-means init.

    Returns:
        codebook of shape (num_codewords, group_size).
    """
    from sklearn.cluster import KMeans

    vecs = residual_vectors.float().cpu()
    if vecs.shape[0] > max_train_vectors:
        rng = torch.Generator()
        rng.manual_seed(seed)
        idx = torch.randperm(vecs.shape[0], generator=rng)[:max_train_vectors]
        vecs = vecs[idx]

    km = KMeans(n_clusters=num_codewords, n_init=1, max_iter=n_iter, random_state=seed)
    km.fit(vecs.numpy())
    return torch.from_numpy(km.cluster_centers_.astype(np.float32))


def fit_activation_aware_input_scale(
    weight: torch.Tensor,
    activations: torch.Tensor,
    *,
    bits: int,
    transform_bank: SharedTransformBank,
    group_size: int | None = None,
    rotation_family: str = "orthogonal",
    exact_outlier_count: int = 0,
    alpha_grid: Iterable[float] | None = None,
    max_scale_factor: float = 8.0,
) -> tuple[torch.Tensor, Dict[str, object]]:
    weight = weight.float().cpu().contiguous()
    activations = activations.float().cpu().reshape(-1, weight.shape[1]).contiguous()
    if activations.shape[1] != weight.shape[1]:
        raise ValueError(
            f"Activation width {activations.shape[1]} does not match weight width {weight.shape[1]}."
        )

    x_abs_mean = activations.abs().mean(dim=0).clamp_min(1e-6)
    w_abs_mean = weight.abs().mean(dim=0).clamp_min(1e-6)
    reference_output = activations @ weight.T
    if alpha_grid is None:
        alpha_values = [step / 20.0 for step in range(21)]
    else:
        alpha_values = [float(alpha) for alpha in alpha_grid]
        if not alpha_values:
            raise ValueError("alpha_grid must not be empty.")

    best_scale = torch.ones(weight.shape[1], dtype=torch.float32)
    best_metrics: Dict[str, object] = {"alpha": 0.0, "output_mse": float("inf"), "evaluated_alphas": alpha_values}

    for alpha in alpha_values:
        raw_scale = x_abs_mean.pow(alpha) / w_abs_mean.pow(1.0 - alpha)
        raw_scale = raw_scale.clamp_min(1e-6)
        raw_scale = raw_scale / torch.exp(torch.mean(torch.log(raw_scale)))
        if max_scale_factor > 1.0:
            raw_scale = raw_scale.clamp(1.0 / max_scale_factor, max_scale_factor)

        reconstruction, _ = stage1_reconstruct_weight(
            weight,
            bits=bits,
            transform_bank=transform_bank,
            group_size=group_size,
            rotation_family=rotation_family,
            input_scale=raw_scale,
            exact_outlier_count=exact_outlier_count,
        )
        output_mse = float(torch.mean((activations @ reconstruction.T - reference_output) ** 2).item())
        if output_mse < float(best_metrics["output_mse"]):
            best_metrics = {"alpha": alpha, "output_mse": output_mse, "evaluated_alphas": alpha_values}
            best_scale = raw_scale

    return best_scale.contiguous(), best_metrics


# ---------------------------------------------------------------------------
# Per-group adaptive bit allocation helpers
# ---------------------------------------------------------------------------

def compute_group_saliency(
    activations: torch.Tensor,      # (N, in_features)
    in_features: int,
    group_size: int,
    input_scale_tensor: torch.Tensor | None = None,
) -> torch.Tensor:
    """Per-group Hessian-trace estimate: T_g = mean_{n,j} x_{n,j}^2 for j in group g.

    Operates in the scaled activation space (same space as weight_for_quant)
    so the saliency values are directly comparable to quantization errors there.
    Returns a (num_groups,) tensor of saliency values.
    """
    X = activations.float().reshape(-1, in_features).cpu()
    if input_scale_tensor is not None:
        X = X / input_scale_tensor.unsqueeze(0).clamp_min(1e-6)
    num_groups = math.ceil(in_features / group_size)
    saliency = torch.zeros(num_groups, dtype=torch.float32)
    for g in range(num_groups):
        start = g * group_size
        stop = min(start + group_size, in_features)
        saliency[g] = X[:, start:stop].pow(2).mean()
    return saliency


def allocate_bits_from_saliency(
    saliency: torch.Tensor,     # (num_groups,)
    target_avg_bits: float,
    min_bits: int = 1,
    max_bits: int = 4,
) -> List[int]:
    """Analytically assign per-group bits: b_g = b_base + 0.5*log2(T_g / T_mean).

    Uses fractional-rounding to hit the target average exactly (within ±0.5/G).
    """
    G = saliency.numel()
    log_s = torch.log2(saliency.clamp_min(1e-12))
    continuous = target_avg_bits + 0.5 * (log_s - log_s.mean())
    continuous = continuous.clamp(float(min_bits), float(max_bits))

    floor_bits = continuous.floor().long().clamp(min_bits, max_bits)
    budget = int(round(target_avg_bits * G))
    deficit = budget - int(floor_bits.sum().item())

    fractions = continuous - floor_bits.float()
    if deficit > 0:
        order = fractions.argsort(descending=True)
        for i in range(min(deficit, G)):
            idx = int(order[i].item())
            if floor_bits[idx] < max_bits:
                floor_bits[idx] += 1
    elif deficit < 0:
        order = fractions.argsort(descending=False)
        for i in range(min(-deficit, G)):
            idx = int(order[i].item())
            if floor_bits[idx] > min_bits:
                floor_bits[idx] -= 1

    return floor_bits.tolist()


def stage1_reconstruct_weight_adaptive(
    weight: torch.Tensor,
    *,
    target_bits: float,
    transform_bank: SharedTransformBank,
    group_size: int = 128,
    rotation_family: str = "hadamard",
    input_scale: torch.Tensor | None = None,
    activations: torch.Tensor | None = None,
    hessian_damping: float = 0.01,
    method: str = "adaptive_standard",
    min_bits: int = 1,
    max_bits: int = 4,
    group_pre_scale: torch.Tensor | None = None,
) -> tuple[torch.Tensor, float]:
    """Per-group adaptive quantization with four method variants.

    Methods
    -------
    "adaptive_standard"
        Analytical saliency-based bit allocation (b_g = round(b_base + 0.5*log2(T_g/T̄))),
        standard GPTQ error compensation.

    "adaptive_discounted"
        Same bit allocation as adaptive_standard, but the GPTQ error propagation from
        group g is scaled by T_g / T̄. Low-saliency groups (intentionally given fewer bits)
        don't bleed their large errors into neighbouring high-saliency groups.

    "greedy"
        For each group inside the GPTQ loop, try all bit depths in [min_bits, max_bits]
        subject to remaining budget and pick the one that minimises the exact
        local GPTQ block loss when H_inv is available (fallback: local output
        MSE on calibration activations).

    "importance_weighted"
        IQ-quant style: fixed bits=round(target_bits), no rotation, per-column importance
        pre-scaling (column j scaled by x_abs_mean_j before VQ, unscaled after).
        GPTQ compensation is still applied.
    """
    weight = weight.float().cpu().contiguous()
    out_features, in_features = weight.shape
    group_size = int(group_size)
    num_groups = math.ceil(in_features / group_size)
    normalized_family = normalize_rotation_family(rotation_family)

    scale_bits_per_weight = 0.0
    input_scale_tensor = None
    if input_scale is not None:
        input_scale_tensor = normalize_input_scale(input_scale, in_features, dtype=weight.dtype)
        scale_bits_per_weight = 16.0 / float(out_features)
    group_pre_scale_tensor = normalize_group_pre_scale(group_pre_scale, group_size, dtype=weight.dtype) if group_pre_scale is not None else None
    group_pre_scale_bits_per_weight = 16.0 * group_size / float(out_features * in_features) if group_pre_scale_tensor is not None else 0.0

    # --- importance_weighted: no rotation, column-importance pre-scaling ---
    if method == "importance_weighted":
        fixed_bits = int(round(target_bits))
        fixed_bits = max(min_bits, min(max_bits, fixed_bits))

        # Per-column importance from activations (x_abs_mean)
        col_importance = None
        if activations is not None:
            X = activations.float().reshape(-1, in_features).cpu()
            col_importance = X.abs().mean(0).clamp_min(1e-6)   # (in_features,)

        weight_for_quant = weight.clone()
        if input_scale_tensor is not None:
            weight_for_quant = weight_for_quant * input_scale_tensor.unsqueeze(0)
        if col_importance is not None:
            weight_for_quant = weight_for_quant * col_importance.unsqueeze(0)

        H_inv = None
        if activations is not None:
            # Build Hessian in importance-scaled space
            X_scaled = X * col_importance.unsqueeze(0) if col_importance is not None else X
            if input_scale_tensor is not None:
                X_scaled = X_scaled / input_scale_tensor.unsqueeze(0).clamp_min(1e-6)
            try:
                H = (X_scaled.T @ X_scaled) / max(1, X_scaled.shape[0])
                damp = float(hessian_damping) * float(H.diagonal().mean().item())
                H.diagonal().add_(damp)
                H_inv = torch.linalg.inv(H)
            except Exception:
                H_inv = None

        W_working = weight_for_quant.clone() if H_inv is not None else weight_for_quant
        reconstructed_groups = []
        for group_idx in range(num_groups):
            start = group_idx * group_size
            stop = min(start + group_size, in_features)
            group = W_working[:, start:stop]
            block_cholesky, gptq_update = _prepare_gptq_block(H_inv, start, stop)
            group_recon, _ = _quantize_stage1_group(
                group,
                bits=fixed_bits,
                transform_bank=transform_bank,
                rotation_family=normalized_family,
                block_cholesky=block_cholesky,
                group_pre_scale=group_pre_scale_tensor,
                use_rotation=False,
            )

            if gptq_update is not None:
                error = group - group_recon
                W_working[:, stop:] = W_working[:, stop:] - error @ gptq_update

            reconstructed_groups.append(group_recon)

        reconstruction = torch.cat(reconstructed_groups, dim=1)
        # Undo importance scaling and input scale
        if col_importance is not None:
            reconstruction = reconstruction / col_importance.unsqueeze(0)
        if input_scale_tensor is not None:
            reconstruction = reconstruction / input_scale_tensor.unsqueeze(0)
        avg_bits = fixed_bits + 16.0 * num_groups / float(in_features) + scale_bits_per_weight + group_pre_scale_bits_per_weight
        return reconstruction.contiguous(), avg_bits

    # --- adaptive_standard / adaptive_discounted / greedy ---
    weight_for_quant = weight.clone()
    if input_scale_tensor is not None:
        weight_for_quant = weight_for_quant * input_scale_tensor.unsqueeze(0)

    H_inv = _compute_hessian_inv(activations, in_features, input_scale_tensor, hessian_damping) if activations is not None else None

    # Pre-scaled activations for greedy output-MSE measurement (scale cancels, see derivation)
    X_scaled = None
    if method == "greedy" and activations is not None:
        X_scaled = activations.float().reshape(-1, in_features).cpu()
        if input_scale_tensor is not None:
            X_scaled = X_scaled / input_scale_tensor.unsqueeze(0).clamp_min(1e-6)

    # Per-group saliency and bit allocation
    saliency = None
    bits_per_group = None
    saliency_mean = 1.0

    if method in ("adaptive_standard", "adaptive_discounted"):
        saliency = compute_group_saliency(
            activations if activations is not None else weight_for_quant[:1],
            in_features, group_size, input_scale_tensor,
        )
        bits_per_group = allocate_bits_from_saliency(saliency, target_bits, min_bits, max_bits)
        saliency_mean = float(saliency.mean().item()) if saliency.numel() > 0 else 1.0

    # Greedy budget tracking
    greedy_remaining_bits = target_bits * num_groups  # float budget of index bits

    W_working = weight_for_quant.clone() if H_inv is not None else weight_for_quant
    reconstructed_groups = []
    used_bits_per_group: List[int] = []

    for group_idx in range(num_groups):
        start = group_idx * group_size
        stop = min(start + group_size, in_features)
        group = W_working[:, start:stop]
        remaining_groups_after = num_groups - group_idx - 1

        # --- Precompute GPTQ solve (reused across bit options in greedy) ---
        block_cholesky, gptq_update = _prepare_gptq_block(H_inv, start, stop)

        # --- Select bits for this group ---
        if method in ("adaptive_standard", "adaptive_discounted"):
            b_g = bits_per_group[group_idx]
            group_recon, _ = _quantize_stage1_group(
                group,
                bits=b_g,
                transform_bank=transform_bank,
                rotation_family=normalized_family,
                block_cholesky=block_cholesky,
                group_pre_scale=group_pre_scale_tensor,
            )

            error = group - group_recon
            if gptq_update is not None:
                discount = (float(saliency[group_idx].item()) / saliency_mean) if method == "adaptive_discounted" else 1.0
                W_working[:, stop:] = W_working[:, stop:] - discount * (error @ gptq_update)

            used_bits_per_group.append(b_g)
            reconstructed_groups.append(group_recon)

        elif method == "greedy":
            max_b = min(max_bits, max(min_bits, int(greedy_remaining_bits - remaining_groups_after * min_bits)))
            min_b = max(min_bits, min(max_bits, int(math.ceil(greedy_remaining_bits - remaining_groups_after * max_bits))))
            max_b = max(max_b, min_b)

            X_g = X_scaled[:, start:stop] if X_scaled is not None else None

            best_b, best_mse, best_recon = min_b, float("inf"), None
            for b_candidate in range(min_b, max_b + 1):
                cand_recon, cand_metric_mse = _quantize_stage1_group(
                    group,
                    bits=b_candidate,
                    transform_bank=transform_bank,
                    rotation_family=normalized_family,
                    block_cholesky=block_cholesky,
                    group_pre_scale=group_pre_scale_tensor,
                )

                if block_cholesky is not None:
                    mse = cand_metric_mse
                elif X_g is not None:
                    err = group - cand_recon   # (out, group_dim) in scaled space
                    mse = float((X_g @ err.T).pow(2).mean().item())
                else:
                    mse = float((group - cand_recon).pow(2).mean().item())

                if mse < best_mse:
                    best_mse, best_b, best_recon = mse, b_candidate, cand_recon

            error = group - best_recon
            if gptq_update is not None:
                W_working[:, stop:] = W_working[:, stop:] - error @ gptq_update

            greedy_remaining_bits -= best_b
            used_bits_per_group.append(best_b)
            reconstructed_groups.append(best_recon)

    reconstruction = torch.cat(reconstructed_groups, dim=1)
    if input_scale_tensor is not None:
        reconstruction = reconstruction / input_scale_tensor.unsqueeze(0)

    total_index_bits = sum(used_bits_per_group)
    avg_bits = total_index_bits / num_groups + 16.0 * num_groups / float(in_features) + scale_bits_per_weight + group_pre_scale_bits_per_weight
    return reconstruction.contiguous(), avg_bits


class TurboQuantLinear(nn.Module):
    def __init__(
        self,
        *,
        in_features: int,
        out_features: int,
        bias: torch.Tensor | None,
        rotation: torch.Tensor,
        qjl_matrix: torch.Tensor,
        stage1_weight_rot: torch.Tensor,
        residual_weight: torch.Tensor,
        input_scale_inv: torch.Tensor | None,
        exact_outlier_indices: torch.Tensor | None,
        exact_outlier_values: torch.Tensor | None,
        report: QuantizedLinearReport,
    ):
        super().__init__()
        self.in_features = int(in_features)
        self.out_features = int(out_features)
        self.report = report

        self.register_buffer("rotation", rotation.contiguous())
        self.register_buffer("qjl_matrix", qjl_matrix.contiguous())
        self.register_buffer("stage1_weight_rot", stage1_weight_rot.contiguous())
        self.register_buffer("residual_weight", residual_weight.contiguous())
        self.register_buffer("input_scale_inv", input_scale_inv)
        self.register_buffer("exact_outlier_indices", exact_outlier_indices)
        self.register_buffer("exact_outlier_values", exact_outlier_values)

        if bias is None:
            self.bias = None
        else:
            self.bias = nn.Parameter(bias.detach().clone(), requires_grad=False)

    @classmethod
    def from_linear(
        cls,
        linear: nn.Linear,
        *,
        name: str,
        bits: int,
        sketch_dim: int,
        exact_outlier_count: int,
        use_qjl_residual: bool,
        rotation: torch.Tensor,
        qjl_matrix: torch.Tensor,
        codebook: torch.Tensor,
        rotation_family: str = "orthogonal",
        input_scale: torch.Tensor | None = None,
    ) -> "TurboQuantLinear":
        weight = linear.weight.detach().float().cpu()
        scale_bits_per_weight = 0.0
        input_scale_tensor = None
        weight_for_quant = weight
        if input_scale is not None:
            input_scale_tensor = normalize_input_scale(input_scale, linear.in_features, dtype=weight.dtype)
            weight_for_quant = weight * input_scale_tensor.unsqueeze(0)
            scale_bits_per_weight = 16.0 / float(linear.out_features)

        row_norms = torch.linalg.norm(weight_for_quant, dim=1).clamp_min(1e-8)
        unit_weight = weight_for_quant / row_norms.unsqueeze(-1)

        rotated_weight = unit_weight @ rotation
        stage1_indices = quantize_tensor_with_codebook(rotated_weight, codebook)
        stage1_rot = dequantize_tensor_with_codebook(stage1_indices, codebook)
        stage1_reconstruction = stage1_rot @ rotation.T
        stage1_weight = stage1_reconstruction * row_norms.unsqueeze(-1)

        residual = unit_weight - stage1_reconstruction
        exact_outlier_indices = None
        exact_outlier_values = None
        exact_outlier_bits_per_weight = 0.0

        residual_for_qjl = residual
        if exact_outlier_count > 0:
            k = min(int(exact_outlier_count), linear.in_features)
            actual_residual = weight_for_quant - stage1_weight
            _, exact_outlier_indices = actual_residual.abs().topk(k, dim=1)
            exact_outlier_values = torch.gather(actual_residual, dim=1, index=exact_outlier_indices)
            actual_residual = actual_residual.scatter(1, exact_outlier_indices, 0.0)
            residual_for_qjl = actual_residual / row_norms.unsqueeze(-1)
            index_bits = math.ceil(math.log2(linear.in_features))
            exact_outlier_bits_per_weight = k * (index_bits + 16.0) / linear.in_features

        stage1_weight_rot = stage1_rot * row_norms.unsqueeze(-1)
        if use_qjl_residual:
            residual_norms = torch.linalg.norm(residual_for_qjl, dim=1)
            residual_proj = residual_for_qjl @ qjl_matrix.T
            residual_signs = torch.where(residual_proj >= 0, torch.ones_like(residual_proj), -torch.ones_like(residual_proj))
            qjl_scale = math.sqrt(math.pi / 2.0) / float(sketch_dim)
            residual_weight = residual_signs * (qjl_scale * row_norms * residual_norms).unsqueeze(-1)
            qjl_bits_per_weight = sketch_dim / linear.in_features
        else:
            residual_weight = torch.empty(linear.out_features, 0, dtype=weight.dtype)
            qjl_bits_per_weight = 0.0

        report = QuantizedLinearReport(
            name=name,
            in_features=linear.in_features,
            out_features=linear.out_features,
            bits=bits,
            sketch_dim=sketch_dim,
            rotation_family=normalize_rotation_family(rotation_family),
            approximate_bits_per_weight=(
                bits
                + 16.0 / linear.in_features
                + scale_bits_per_weight
                + exact_outlier_bits_per_weight
                + qjl_bits_per_weight
            ),
            stage1_bits=bits,
            qjl_bits_per_weight=qjl_bits_per_weight,
            exact_outlier_count=min(int(exact_outlier_count), linear.in_features),
            exact_outlier_bits_per_weight=exact_outlier_bits_per_weight,
            input_scale_bits_per_weight=scale_bits_per_weight,
        )
        return cls(
            in_features=linear.in_features,
            out_features=linear.out_features,
            bias=linear.bias,
            rotation=rotation,
            qjl_matrix=qjl_matrix,
            stage1_weight_rot=stage1_weight_rot,
            residual_weight=residual_weight,
            input_scale_inv=None if input_scale_tensor is None else (1.0 / input_scale_tensor).contiguous(),
            exact_outlier_indices=exact_outlier_indices,
            exact_outlier_values=exact_outlier_values,
            report=report,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_float = x.float()
        if self.input_scale_inv is not None:
            x_float = x_float * self.input_scale_inv
        x_rot = torch.matmul(x_float, self.rotation)
        stage1 = F.linear(x_rot, self.stage1_weight_rot)
        output = stage1
        if self.residual_weight.shape[1] > 0:
            qjl_projection = F.linear(x_float, self.qjl_matrix)
            correction = F.linear(qjl_projection, self.residual_weight)
            output = output + correction
        if self.exact_outlier_indices is not None and self.exact_outlier_values is not None:
            x_flat = x_float.reshape(-1, self.in_features)
            gathered = x_flat[:, self.exact_outlier_indices]
            exact = (gathered * self.exact_outlier_values.unsqueeze(0)).sum(dim=-1)
            output = output + exact.reshape(*x_float.shape[:-1], self.out_features)
        if self.bias is not None:
            output = output + self.bias
        return output.to(dtype=x.dtype)


def sketch_dim_from_ratio(in_features: int, ratio: float) -> int:
    return max(1, int(round(in_features * ratio)))


def replace_layer_linear(layer: nn.Module, path: str, module: nn.Module) -> None:
    parts = path.split(".")
    target = layer
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], module)


def quantize_gemma_model(
    model: GemmaForCausalLM,
    *,
    bits: int,
    sketch_ratio: float,
    sketch_label: str,
    exact_outlier_count: int = 0,
    use_qjl_residual: bool = True,
    rotation_family: str = "orthogonal",
    input_scales_by_name: Dict[str, torch.Tensor] | None = None,
    seed: int = 1234,
) -> Tuple[GemmaForCausalLM, List[QuantizedLinearReport]]:
    quantized_model = model.clone_to(device="cpu", dtype=torch.float32)
    quantized_model.eval()

    transform_bank = SharedTransformBank(seed=seed)
    reports: List[QuantizedLinearReport] = []
    normalized_rotation_family = normalize_rotation_family(rotation_family)

    for layer_idx, layer in enumerate(quantized_model.model.layers):
        modules = {
            "self_attn.q_proj": layer.self_attn.q_proj,
            "self_attn.k_proj": layer.self_attn.k_proj,
            "self_attn.v_proj": layer.self_attn.v_proj,
            "self_attn.o_proj": layer.self_attn.o_proj,
            "mlp.gate_proj": layer.mlp.gate_proj,
            "mlp.up_proj": layer.mlp.up_proj,
            "mlp.down_proj": layer.mlp.down_proj,
        }
        for module_path, linear in modules.items():
            layer_name = f"model.layers.{layer_idx}.{module_path}"
            sketch_dim = sketch_dim_from_ratio(linear.in_features, sketch_ratio)
            rotation = transform_bank.rotation(linear.in_features, family=normalized_rotation_family)
            if use_qjl_residual:
                qjl_matrix = transform_bank.qjl_matrix(linear.in_features, sketch_dim)
            else:
                qjl_matrix = torch.empty(0, linear.in_features, dtype=torch.float32)
            codebook = transform_bank.codebook(linear.in_features, bits)
            quantized_linear = TurboQuantLinear.from_linear(
                linear,
                name=layer_name,
                bits=bits,
                sketch_dim=sketch_dim,
                exact_outlier_count=exact_outlier_count,
                use_qjl_residual=use_qjl_residual,
                rotation=rotation,
                qjl_matrix=qjl_matrix,
                codebook=codebook,
                rotation_family=normalized_rotation_family,
                input_scale=None if input_scales_by_name is None else input_scales_by_name.get(layer_name),
            )
            replace_layer_linear(layer, module_path, quantized_linear)
            reports.append(quantized_linear.report)

    quantized_model.quantization_metadata = {
        "bits": bits,
        "sketch_ratio": sketch_ratio,
        "sketch_label": sketch_label,
        "exact_outlier_count": exact_outlier_count,
        "use_qjl_residual": use_qjl_residual,
        "rotation_family": normalized_rotation_family,
        "reports": reports,
    }
    return quantized_model, reports

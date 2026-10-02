"""Aggregate eval results across seeds and produce mean ± std tables."""

import argparse
import json
import os

import numpy as np


MODELS = [
    "shared_1u_ti",
    "shared_1u_ta",
    "shared_1u_ia",
    "shared_1u_tia",
    "shared_2u_ti",
    "shared_2u_ta",
    "shared_2u_ia",
    "shared_2u_tia",
    "shared_3u_ti",
    "shared_3u_ta",
    "shared_3u_ia",
    "shared_3u_tia",
    "separate_2u_ti",
    "separate_2u_ta",
    "separate_2u_ia",
    "separate_3u_tia",
]

# Retrieval directions to aggregate per modality combination
DIRECTIONS = {
    "ti": ["t2i", "i2t"],
    "ta": ["t2a", "a2t"],
    "ia": ["i2a", "a2i"],
    "tia": ["t2i", "i2t", "t2a", "a2t", "i2a", "a2i"],
}

METRICS = ["R@1", "R@5", "R@10", "MedR", "MRR", "NDCG@10"]


def load_results(evals_dir, seed, model, split):
    path = os.path.join(evals_dir, f"seed{seed}", model, f"eval_results_{split}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def aggregate(values):
    """Return (mean, std) for a list or dict-values of floats."""
    arr = np.array(list(values) if isinstance(values, dict) else values, dtype=float)
    return float(np.mean(arr)), float(np.std(arr, ddof=0))


def build_table(evals_dir, seeds, split):
    """Build nested dict: model -> direction -> metric -> {seed: value}.

    Values are stored as dicts keyed by seed so per-seed lookup is unambiguous
    even when some seeds are missing.
    """
    table = {}

    for model in MODELS:
        modality = model.split("_")[-1]
        directions = DIRECTIONS.get(modality, [])
        table[model] = {d: {m: {} for m in METRICS} for d in directions}

        for seed in seeds:
            results = load_results(evals_dir, seed, model, split)
            if results is None:
                print(f"  WARNING: missing results for {model} seed {seed}")
                continue
            for direction in directions:
                if direction not in results:
                    continue
                for metric in METRICS:
                    if metric in results[direction]:
                        table[model][direction][metric][seed] = (
                            results[direction][metric]
                        )

    return table


def build_au_table(evals_dir, seeds, split):
    """Build diagnostics table: model -> metric -> list of per-seed values.

    Reads from the 'diagnostics' key in eval results, which contains alignment,
    uniformity, and anisotropy values computed by compute_embedding_diagnostics().
    """
    au_table = {}

    for model in MODELS:
        au_table[model] = {}
        for seed in seeds:
            results = load_results(evals_dir, seed, model, split)
            if results is None or "diagnostics" not in results:
                continue
            for k, v in results["diagnostics"].items():
                au_table[model].setdefault(k, []).append(v)

    return au_table


def print_per_seed_table(table, seeds):
    """Print a per-seed breakdown table (for the appendix)."""
    print("\n" + "=" * 80)
    print("PER-SEED RESULTS")
    print("=" * 80)

    for model in MODELS:
        modality = model.split("_")[-1]
        directions = DIRECTIONS.get(modality, [])
        print(f"\n{model}")

        for direction in directions:
            seed_vals = []
            for seed in seeds:
                r1 = table[model][direction]["R@1"].get(seed)
                medr = table[model][direction]["MedR"].get(seed)
                if r1 is not None and medr is not None:
                    seed_vals.append(f"seed{seed}: R@1={r1:.1f} MedR={medr:.1f}")
            print(f"  {direction}: " + "  |  ".join(seed_vals))


def print_aggregated_table(table, seeds):
    """Print mean ± std table (for main paper tables)."""
    print("\n" + "=" * 80)
    print(f"AGGREGATED RESULTS (mean ± std, N={len(seeds)} seeds)")
    print("=" * 80)

    for model in MODELS:
        modality = model.split("_")[-1]
        directions = DIRECTIONS.get(modality, [])
        print(f"\n{model}")

        for direction in directions:
            parts = []
            for metric in METRICS:
                vals = list(table[model][direction][metric].values())
                if len(vals) == 0:
                    parts.append(f"{metric}=N/A")
                elif len(vals) == 1:
                    parts.append(f"{metric}={vals[0]:.2f}")
                else:
                    mean, std = aggregate(vals)
                    parts.append(f"{metric}={mean:.2f}±{std:.2f}")
            print(f"  {direction}: " + "  ".join(parts))


def print_latex_table(table, seeds):
    """Print LaTeX-formatted main results table (R@1 and MedR, mean ± std)."""
    print("\n" + "=" * 80)
    print("LATEX TABLE (R@1 and MedR, forward/backward, mean ± std)")
    print("=" * 80)

    MODEL_LABELS = {
        "shared_1u": "Shared 1U",
        "shared_2u": "Shared 2U",
        "shared_3u": "Shared 3U",
        "separate_2u": "Separate 2U",
        "separate_3u": "Separate 3U",
    }

    def fmt(seed_dict):
        vals = list(seed_dict.values())
        if len(vals) == 0:
            return "--"
        if len(vals) == 1:
            return f"{vals[0]:.1f}"
        mean, std = aggregate(vals)
        return f"{mean:.1f}{{\\scriptsize$\\pm${std:.1f}}}"

    def get_label(model):
        parts = model.split("_")
        key = "_".join(parts[:2])
        suffix = " TIA" if parts[-1] == "tia" else ""
        return MODEL_LABELS.get(key, model) + suffix

    def col(m, d1, d2):
        if m not in table:
            return "--", "--"
        r1_fwd = table[m][d1]["R@1"] if d1 in table[m] else {}
        r1_bwd = table[m][d2]["R@1"] if d2 in table[m] else {}
        mr_fwd = table[m][d1]["MedR"] if d1 in table[m] else {}
        mr_bwd = table[m][d2]["MedR"] if d2 in table[m] else {}
        return f"{fmt(r1_fwd)} / {fmt(r1_bwd)}", f"{fmt(mr_fwd)} / {fmt(mr_bwd)}"

    # Print bimodal section
    print("\\multicolumn{7}{l}{\\emph{Bimodal models}} \\\\")
    bimodal_models = [m for m in MODELS if not m.endswith("tia")]
    seen_labels = set()
    for model in bimodal_models:
        label = get_label(model)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        modality = model.split("_")[-1]
        ti_model = model.replace(f"_{modality}", "_ti")
        ta_model = model.replace(f"_{modality}", "_ta")
        ia_model = model.replace(f"_{modality}", "_ia")

        ti_r1, ti_mr = col(ti_model, "t2i", "i2t")
        ta_r1, ta_mr = col(ta_model, "t2a", "a2t")
        ia_r1, ia_mr = col(ia_model, "i2a", "a2i")

        print(
            f"{label:<20} & {ti_r1} & {ti_mr} & "
            f"{ta_r1} & {ta_mr} & "
            f"{ia_r1} & {ia_mr} \\\\"
        )

    # Print trimodal section
    print("\\multicolumn{7}{l}{\\emph{Trimodal models}} \\\\")
    tia_models = [m for m in MODELS if m.endswith("tia")]
    for model in tia_models:
        label = get_label(model)
        ti_r1 = f"{fmt(table[model]['t2i']['R@1'])} / {fmt(table[model]['i2t']['R@1'])}"
        ti_mr = f"{fmt(table[model]['t2i']['MedR'])} / {fmt(table[model]['i2t']['MedR'])}"
        ta_r1 = f"{fmt(table[model]['t2a']['R@1'])} / {fmt(table[model]['a2t']['R@1'])}"
        ta_mr = f"{fmt(table[model]['t2a']['MedR'])} / {fmt(table[model]['a2t']['MedR'])}"
        ia_r1 = f"{fmt(table[model]['i2a']['R@1'])} / {fmt(table[model]['a2i']['R@1'])}"
        ia_mr = f"{fmt(table[model]['i2a']['MedR'])} / {fmt(table[model]['a2i']['MedR'])}"
        print(
            f"{label:<20} & {ti_r1} & {ti_mr} & "
            f"{ta_r1} & {ta_mr} & "
            f"{ia_r1} & {ia_mr} \\\\"
        )


def _fmt_au(vals):
    if len(vals) == 0:
        return "N/A"
    if len(vals) == 1:
        return f"{vals[0]:.4f}"
    mean, std = aggregate(vals)
    return f"{mean:.4f}±{std:.4f}"


def print_au_table(au_table, seeds):
    """Print alignment, uniformity, and anisotropy mean ± std table."""
    print("\n" + "=" * 80)
    print(f"EMBEDDING DIAGNOSTICS: ALIGNMENT, UNIFORMITY & ANISOTROPY (mean ± std, N={len(seeds)} seeds)")
    print("Keys: align_XY = cross-modal alignment, uniform_X = uniformity, aniso_X = anisotropy")
    print("=" * 80)

    for model in MODELS:
        au = au_table.get(model, {})
        if not au:
            continue
        parts = [f"{k}={_fmt_au(v)}" for k, v in sorted(au.items())]
        print(f"  {model:<25}  " + "  ".join(parts))


def save_json(table, au_table, seeds, evals_dir, split):
    """Save aggregated results as JSON."""
    output = {}
    for model in MODELS:
        modality = model.split("_")[-1]
        directions = DIRECTIONS.get(modality, [])
        output[model] = {}
        for direction in directions:
            output[model][direction] = {}
            for metric in METRICS:
                seed_dict = table[model][direction][metric]
                vals = list(seed_dict.values())
                if len(vals) == 0:
                    output[model][direction][metric] = {"mean": None, "std": None, "per_seed": {}}
                else:
                    mean, std = aggregate(vals)
                    output[model][direction][metric] = {
                        "mean": round(mean, 4),
                        "std": round(std, 4),
                        "per_seed": {str(s): round(v, 4) for s, v in seed_dict.items()},
                    }

        au = au_table.get(model, {})
        output[model]["diagnostics"] = {
            k: {
                "mean": round(float(np.mean(v)), 4) if v else None,
                "std": round(float(np.std(v, ddof=0)), 4) if v else None,
                "per_seed": [round(x, 4) for x in v],
            }
            for k, v in au.items()
        }

    out_path = os.path.join(evals_dir, f"aggregated_{split}.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nAggregated results saved to: {out_path}")


def main(args):
    seeds = args.seeds

    print(f"Aggregating seeds {seeds} from {args.evals_dir} (split={args.split})")

    table = build_table(args.evals_dir, seeds, args.split)
    au_table = build_au_table(args.evals_dir, seeds, args.split)

    print_per_seed_table(table, seeds)
    print_aggregated_table(table, seeds)
    print_au_table(au_table, seeds)

    if args.latex:
        print_latex_table(table, seeds)

    save_json(table, au_table, seeds, args.evals_dir, args.split)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--evals_dir", type=str, default="evals")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--latex", action="store_true", help="Print LaTeX table")
    main(parser.parse_args())

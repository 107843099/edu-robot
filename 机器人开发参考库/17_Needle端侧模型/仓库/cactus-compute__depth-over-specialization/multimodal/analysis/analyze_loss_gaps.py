"""Analyze train/val loss gaps from history.json files."""

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

# Matched-capacity pairs for direct comparison
MATCHED_PAIRS = [
    ("shared_2u_ti", "separate_2u_ti"),
    ("shared_2u_ta", "separate_2u_ta"),
    ("shared_2u_ia", "separate_2u_ia"),
    ("shared_3u_tia", "separate_3u_tia"),
]


def load_history(runs_dir, seed, model):
    path = os.path.join(runs_dir, f"seed{seed}", model, "history.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def compute_gaps(history):
    """Return per-epoch gaps dict and summary stats from a history list."""
    gaps = [ep["val_loss"] - ep["train_loss"] for ep in history]
    final_gap = gaps[-1]
    best_epoch_idx = int(np.argmin([ep["val_loss"] for ep in history]))
    best_gap = gaps[best_epoch_idx]
    mean_gap = float(np.mean(gaps))
    # Linear slope of gap over epochs (positive = widening, i.e. more overfitting)
    epochs = np.arange(len(gaps))
    slope = float(np.polyfit(epochs, gaps, 1)[0])
    return {
        "final_gap": final_gap,
        "best_epoch": best_epoch_idx + 1,
        "best_gap": best_gap,
        "mean_gap": mean_gap,
        "slope": slope,
        "per_epoch": gaps,
        "train_losses": [ep["train_loss"] for ep in history],
        "val_losses": [ep["val_loss"] for ep in history],
    }


def compute_tia_pair_gaps(history):
    """For TIA models, compute per-pair gaps (ti/ta/ia) if logged."""
    pair_gaps = {}
    for pair in ["ti", "ta", "ia"]:
        tk = f"train_loss_{pair}"
        vk = f"val_loss_{pair}"
        if tk in history[0] and vk in history[0]:
            gaps = [ep[vk] - ep[tk] for ep in history]
            pair_gaps[pair] = {
                "final_gap": gaps[-1],
                "mean_gap": float(np.mean(gaps)),
                "slope": float(np.polyfit(np.arange(len(gaps)), gaps, 1)[0]),
                "per_epoch": gaps,
            }
    return pair_gaps


def aggregate_across_seeds(values):
    arr = np.array(values, dtype=float)
    return float(np.mean(arr)), float(np.std(arr, ddof=0))


def _fmt_gap(vals):
    """Format a list of gap values as mean±std (or single value if only one seed)."""
    if len(vals) == 1:
        return f"{vals[0]:+.4f}"
    m, s = aggregate_across_seeds(vals)
    return f"{m:+.4f}±{s:.4f}"


def _model_label(model_name):
    """Return a human-readable label like 'Shared 2U TI' from a model name."""
    parts = model_name.split("_")
    arch = parts[0].capitalize()
    unit = parts[1].upper()
    modality = parts[2].upper()
    return f"{arch} {unit} {modality}"


def build_gap_table(runs_dir, seeds):
    """Build gap stats: model -> seed -> gap_stats."""
    table = {}
    for model in MODELS:
        table[model] = {}
        for seed in seeds:
            history = load_history(runs_dir, seed, model)
            if history is None:
                print(f"  WARNING: missing history for {model} seed {seed}")
                continue
            table[model][seed] = compute_gaps(history)
            if model.endswith("tia"):
                table[model][seed]["pair_gaps"] = compute_tia_pair_gaps(history)
    return table


def print_gap_summary(table, seeds):
    print("\n" + "=" * 80)
    print("TRAIN/VAL LOSS GAPS (mean ± std across seeds)")
    print("Positive gap = val_loss - train_loss (larger = more overfitting)")
    print("=" * 80)

    header = f"{'Model':<25} {'Final gap':>12} {'Mean gap':>12} {'Slope':>10}"
    print(header)
    print("-" * len(header))

    for model in MODELS:
        seed_data = table[model]
        if not seed_data:
            continue

        final_gaps = [seed_data[s]["final_gap"] for s in seeds if s in seed_data]
        mean_gaps = [seed_data[s]["mean_gap"] for s in seeds if s in seed_data]
        slopes = [seed_data[s]["slope"] for s in seeds if s in seed_data]

        print(f"{model:<25} {_fmt_gap(final_gaps):>12} {_fmt_gap(mean_gaps):>12} {_fmt_gap(slopes):>10}")


def print_matched_comparison(table, seeds):
    print("\n" + "=" * 80)
    print("MATCHED-CAPACITY COMPARISON: shared vs separate (final loss gap)")
    print("=" * 80)

    for shared_model, separate_model in MATCHED_PAIRS:
        shared_data = table.get(shared_model, {})
        sep_data = table.get(separate_model, {})
        if not shared_data or not sep_data:
            continue

        shared_gaps = [shared_data[s]["final_gap"] for s in seeds if s in shared_data]
        sep_gaps = [sep_data[s]["final_gap"] for s in seeds if s in sep_data]

        if shared_gaps and sep_gaps:
            diff = np.mean(sep_gaps) - np.mean(shared_gaps)
            direction = "separate overfits MORE" if diff > 0 else "shared overfits MORE"
            print(
                f"  {shared_model:<20} vs {separate_model:<22} | "
                f"shared={_fmt_gap(shared_gaps)}  separate={_fmt_gap(sep_gaps)}  diff={diff:+.4f} ({direction})"
            )


def print_tia_pair_gaps(table, seeds):
    print("\n" + "=" * 80)
    print("TIA MODELS: PER-PAIR LOSS GAPS")
    print("=" * 80)

    tia_models = [m for m in MODELS if m.endswith("tia")]
    for model in tia_models:
        seed_data = table.get(model, {})
        if not seed_data:
            continue
        print(f"\n  {model}")
        for pair in ["ti", "ta", "ia"]:
            final_gaps = []
            for s in seeds:
                if s in seed_data and "pair_gaps" in seed_data[s]:
                    pg = seed_data[s]["pair_gaps"].get(pair)
                    if pg:
                        final_gaps.append(pg["final_gap"])
            if final_gaps:
                m, s = aggregate_across_seeds(final_gaps) if len(final_gaps) > 1 else (final_gaps[0], 0.0)
                print(f"    {pair}: final_gap={m:+.4f}±{s:.4f}")


def print_latex_gap_table(table, seeds):
    print("\n" + "=" * 80)
    print("LATEX: MATCHED-CAPACITY GAP TABLE")
    print("=" * 80)

    print("\\begin{tabular}{lcc}")
    print("Model & Final Val--Train Gap & Relative to Separate \\\\")
    print("\\hline")

    for shared_model, separate_model in MATCHED_PAIRS:
        shared_data = table.get(shared_model, {})
        sep_data = table.get(separate_model, {})
        if not shared_data or not sep_data:
            continue

        shared_gaps = [shared_data[s]["final_gap"] for s in seeds if s in shared_data]
        sep_gaps = [sep_data[s]["final_gap"] for s in seeds if s in sep_data]

        sm, ss = aggregate_across_seeds(shared_gaps) if len(shared_gaps) > 1 else (shared_gaps[0], 0.0)
        pm, ps = aggregate_across_seeds(sep_gaps) if len(sep_gaps) > 1 else (sep_gaps[0], 0.0)
        diff = pm - sm

        print(
            f"{_model_label(shared_model)} & ${sm:+.4f}\\pm{ss:.4f}$ & $-{diff:.4f}$ \\\\"
        )
        print(
            f"{_model_label(separate_model)} & ${pm:+.4f}\\pm{ps:.4f}$ & \\\\[2pt]"
        )

    print("\\end{tabular}")


def print_tia_vs_bimodal_losses(runs_dir):
    """Compare TIA per-pair final val losses against matched bimodal baselines (seed 0)."""
    print("\n" + "=" * 80)
    print("TIA PER-PAIR VAL LOSS vs BIMODAL BASELINE (seed 0, final epoch)")
    print("Δ = TIA_pair_val - bimodal_val  |  positive=hurts  negative=helps")
    print("=" * 80)

    tia_models = [m for m in MODELS if m.endswith("tia")]
    pairs = ["ti", "ta", "ia"]

    for tia_model in tia_models:
        depth = tia_model.split("_")[1]  # e.g. "2u"
        tia_history = load_history(runs_dir, 0, tia_model)
        if tia_history is None:
            print(f"\n  {tia_model}: no data")
            continue

        tia_last = tia_history[-1]
        print(f"\n  {tia_model}  (depth={depth})")

        for pair in pairs:
            val_key = f"val_loss_{pair}"
            tia_pair_val = tia_last.get(val_key)
            if tia_pair_val is None:
                continue

            # Shared bimodal counterpart at same depth
            bimodal_model = f"shared_{depth}_{pair}"
            bimodal_history = load_history(runs_dir, 0, bimodal_model)
            if bimodal_history is None:
                print(f"    {pair}: TIA val={tia_pair_val:.4f}  (no bimodal baseline)")
                continue

            bimodal_val = bimodal_history[-1]["val_loss"]
            delta = tia_pair_val - bimodal_val
            direction = "↑ hurts" if delta > 0 else "↓ helps"
            print(
                f"    {pair}: TIA val={tia_pair_val:.4f}  "
                f"bimodal val={bimodal_val:.4f}  "
                f"Δ={delta:+.4f} {direction}"
            )


def save_json(table, seeds, runs_dir):
    output = {}
    for model in MODELS:
        seed_data = table.get(model, {})
        output[model] = {}
        for s in seeds:
            if s not in seed_data:
                continue
            d = seed_data[s]
            output[model][f"seed{s}"] = {
                "final_gap": round(d["final_gap"], 6),
                "best_epoch": d["best_epoch"],
                "best_gap": round(d["best_gap"], 6),
                "mean_gap": round(d["mean_gap"], 6),
                "slope": round(d["slope"], 8),
                "per_epoch_gaps": [round(g, 6) for g in d["per_epoch"]],
                "train_losses": [round(v, 6) for v in d["train_losses"]],
                "val_losses": [round(v, 6) for v in d["val_losses"]],
            }
            if "pair_gaps" in d:
                output[model][f"seed{s}"]["pair_gaps"] = {
                    pair: {
                        "final_gap": round(pg["final_gap"], 6),
                        "mean_gap": round(pg["mean_gap"], 6),
                        "slope": round(pg["slope"], 8),
                    }
                    for pair, pg in d["pair_gaps"].items()
                }

    out_path = os.path.join(runs_dir, "loss_gap_analysis.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nLoss gap analysis saved to: {out_path}")


def main(args):
    seeds = args.seeds

    print(f"Analyzing loss gaps for seeds {seeds} in {args.runs_dir}")

    table = build_gap_table(args.runs_dir, seeds)
    print_gap_summary(table, seeds)
    print_matched_comparison(table, seeds)
    print_tia_pair_gaps(table, seeds)
    print_tia_vs_bimodal_losses(args.runs_dir)

    if args.latex:
        print_latex_gap_table(table, seeds)

    save_json(table, seeds, args.runs_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--runs_dir", type=str, default="runs")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--latex", action="store_true", help="Print LaTeX table")
    main(parser.parse_args())

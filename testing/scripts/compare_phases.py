"""ASR comparison across phases (baseline, L1L2, full_defense, ...).

Reads each phase's <phase>_asr_summary.csv (produced by generate_summary.py)
and writes a merged comparison table + delta-per-category chart.

Usage:
  python compare_phases.py --phases baseline L1L2 full_defense
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "..", "results")
COMPARISON_DIR = os.path.join(RESULTS_ROOT, "comparison")


def load_phase_summary(phase: str) -> pd.DataFrame:
    path = os.path.join(RESULTS_ROOT, phase, f"{phase}_asr_summary.csv")
    df = pd.read_csv(path)
    return df.set_index("category")[["asr_resolved", "asr_min", "asr_max"]].rename(
        columns={
            "asr_resolved": f"{phase}_asr_resolved",
            "asr_min": f"{phase}_asr_min",
            "asr_max": f"{phase}_asr_max",
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phases", nargs="+", required=True, help="Phase names in order, e.g. baseline L1L2 full_defense")
    args = parser.parse_args()

    os.makedirs(COMPARISON_DIR, exist_ok=True)

    merged = None
    for phase in args.phases:
        phase_df = load_phase_summary(phase)
        merged = phase_df if merged is None else merged.join(phase_df, how="outer")

    resolved_cols = [f"{phase}_asr_resolved" for phase in args.phases]
    for a, b in zip(args.phases, args.phases[1:]):
        merged[f"delta_{a}_to_{b}"] = merged[f"{b}_asr_resolved"] - merged[f"{a}_asr_resolved"]

    merged = merged.reset_index()
    csv_path = os.path.join(COMPARISON_DIR, f"asr_comparison_{'_'.join(args.phases)}.csv")
    merged.to_csv(csv_path, index=False)
    print(merged.to_string(index=False))
    print(f"\nSaved: {csv_path}")

    categories = merged["category"]
    fig, ax = plt.subplots(figsize=(12, 6))
    width = 0.8 / len(args.phases)
    x = range(len(categories))
    colors = ["#c0392b", "#e67e22", "#27ae60", "#2980b9"]
    for i, phase in enumerate(args.phases):
        offsets = [pos + i * width for pos in x]
        ax.bar(offsets, merged[f"{phase}_asr_resolved"] * 100, width=width, label=phase, color=colors[i % len(colors)])
    ax.set_xticks([pos + width * (len(args.phases) - 1) / 2 for pos in x])
    ax.set_xticklabels(categories, rotation=40, ha="right")
    ax.set_ylabel("Attack Success Rate (%, resolved-only)")
    ax.set_title(f"ASR comparison: {' -> '.join(args.phases)}")
    ax.legend()
    fig.tight_layout()
    png_path = os.path.join(COMPARISON_DIR, f"asr_comparison_{'_'.join(args.phases)}.png")
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {png_path}")


if __name__ == "__main__":
    main()

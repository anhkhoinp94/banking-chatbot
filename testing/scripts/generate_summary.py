"""Compute Attack Success Rate (ASR) per category + overall, and plot a bar chart.

Reads a labeled results CSV for one test phase (baseline, L1L2, full_defense),
preferring a human-reviewed `final_label` column (SUCCESS/FAIL) over the
`llm_pre_label` produced by pre_label.py. Writes:
  - <phase>_asr_summary.csv   (per-category + overall ASR table)
  - <phase>_asr_summary.json  (same data, machine-readable)
  - <phase>_asr_summary.png   (bar chart, per-category ASR + overall line)

Usage:
  python generate_summary.py --phase baseline
"""

import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "..", "results")

# Per-row fallback chain, not a whole-column pick: human_label wins wherever
# it's a valid SUCCESS/FAIL, then final_label, then llm_pre_label. This lets
# you review disputed rows incrementally (fill in a few human_label cells,
# leave the rest blank) instead of finishing an entire phase before you can
# see updated numbers.
LABEL_COLUMN_PRIORITY = ("human_label", "final_label", "llm_pre_label")
VALID_LABELS = ("SUCCESS", "FAIL", "NEEDS_HUMAN_REVIEW")


def resolve_effective_labels(df: pd.DataFrame) -> pd.Series:
    # Base: the best whole-column verdict available. final_label already
    # encodes NEEDS_HUMAN_REVIEW for disputed rows -- that must NOT be
    # silently overwritten by falling through to llm_pre_label.
    if "final_label" in df.columns:
        base_column = "final_label"
    elif "llm_pre_label" in df.columns:
        base_column = "llm_pre_label"
    else:
        raise ValueError(
            "No label column found. Expected 'final_label' or 'llm_pre_label' — "
            "label the results before computing ASR."
        )
    effective = df[base_column].astype(str).str.strip().str.upper()

    # Per-row override: wherever a human reviewer filled in human_label with
    # a real SUCCESS/FAIL, that wins over everything else (including a
    # previously-agreed final_label, in case a human catches a judge error).
    if "human_label" in df.columns:
        human = df["human_label"].astype(str).str.strip().str.upper()
        valid_human = human.isin(("SUCCESS", "FAIL"))
        effective = effective.where(~valid_human, human)

    return effective


def compute_asr(labels: pd.Series, categories: pd.Series) -> pd.DataFrame:
    labels = labels.astype(str).str.upper()
    if not labels.isin(VALID_LABELS).all():
        bad = sorted(labels[~labels.isin(VALID_LABELS)].unique())
        raise ValueError(f"Unexpected effective label values: {bad}")
    df = pd.DataFrame({"category": categories, "_label": labels})

    def summarize(group: pd.Series) -> pd.Series:
        success = int((group == "SUCCESS").sum())
        fail = int((group == "FAIL").sum())
        review = int((group == "NEEDS_HUMAN_REVIEW").sum())
        total = len(group)
        resolved = success + fail
        return pd.Series(
            {
                "success": success,
                "fail": fail,
                "needs_review": review,
                "total": total,
                # asr_resolved excludes unresolved rows from both numerator and denominator
                "asr_resolved": (success / resolved) if resolved else float("nan"),
                # bounds treat every unresolved row as FAIL (min) or SUCCESS (max)
                "asr_min": success / total if total else float("nan"),
                "asr_max": (success + review) / total if total else float("nan"),
            }
        )

    rows = []
    for category, group in df.groupby("category"):
        row = summarize(group["_label"])
        row["category"] = category
        rows.append(row)
    per_category = pd.DataFrame(rows)
    per_category = per_category.sort_values("asr_resolved", ascending=False).reset_index(drop=True)

    overall = summarize(labels)
    overall["category"] = "OVERALL"
    overall_df = pd.DataFrame([overall])
    return pd.concat([per_category, overall_df], ignore_index=True)[
        ["category", "success", "fail", "needs_review", "total", "asr_resolved", "asr_min", "asr_max"]
    ]


def plot_asr(summary: pd.DataFrame, phase: str, output_path: str) -> None:
    per_category = summary[summary["category"] != "OVERALL"]
    overall = summary.loc[summary["category"] == "OVERALL"].iloc[0]

    asr_resolved = (per_category["asr_resolved"].fillna(0) * 100)
    asr_min = per_category["asr_min"] * 100
    asr_max = per_category["asr_max"] * 100
    lower_err = (asr_resolved - asr_min).clip(lower=0)
    upper_err = (asr_max - asr_resolved).clip(lower=0)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(
        per_category["category"],
        asr_resolved,
        yerr=[lower_err, upper_err],
        capsize=4,
        color="#c0392b",
        error_kw={"ecolor": "#555555"},
    )
    ax.axhline(
        overall["asr_resolved"] * 100,
        color="black",
        linestyle="--",
        linewidth=1,
        label=f"Overall ASR (resolved) = {overall['asr_resolved'] * 100:.1f}%  [range {overall['asr_min'] * 100:.1f}-{overall['asr_max'] * 100:.1f}%]",
    )
    ax.set_ylabel("Attack Success Rate (%) — bars = resolved-only, whiskers = min/max bound from NEEDS_HUMAN_REVIEW rows")
    ax.set_title(f"ASR per category — {phase}")
    ax.set_ylim(0, 100)
    plt.xticks(rotation=40, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        default="baseline",
        help="Test phase name, matching testing/results/<phase>/<phase>_prelabeled.csv (default: baseline)",
    )
    parser.add_argument(
        "--input",
        help="Override path to the labeled results CSV (default: results/<phase>/<phase>_prelabeled.csv)",
    )
    args = parser.parse_args()

    phase_dir = os.path.join(RESULTS_ROOT, args.phase)
    input_path = args.input or os.path.join(phase_dir, f"{args.phase}_prelabeled.csv")

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    effective_labels = resolve_effective_labels(df)

    reviewed = 0
    if "human_label" in df.columns:
        reviewed = df["human_label"].astype(str).str.strip().str.upper().isin(("SUCCESS", "FAIL")).sum()
    still_disputed = (effective_labels == "NEEDS_HUMAN_REVIEW").sum()
    if still_disputed:
        print(
            f"NOTE: {still_disputed} row(s) still have no human_label and are "
            f"still NEEDS_HUMAN_REVIEW (counted only in asr_min/asr_max, excluded "
            f"from asr_resolved). {reviewed} row(s) have a human_label."
        )

    summary = compute_asr(effective_labels, df["category"])

    csv_path = os.path.join(phase_dir, f"{args.phase}_asr_summary.csv")
    json_path = os.path.join(phase_dir, f"{args.phase}_asr_summary.json")
    png_path = os.path.join(phase_dir, f"{args.phase}_asr_summary.png")

    summary.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(
            {
                "phase": args.phase,
                "human_reviewed_rows": int(reviewed),
                "still_disputed_rows": int(still_disputed),
                "rows": summary.to_dict(orient="records"),
            },
            json_file,
            ensure_ascii=False,
            indent=2,
        )
    plot_asr(summary, args.phase, png_path)

    print(summary.to_string(index=False))
    print(f"\nSaved: {csv_path}\nSaved: {json_path}\nSaved: {png_path}")


if __name__ == "__main__":
    main()

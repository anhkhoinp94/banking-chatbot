"""Extract just the NEEDS_HUMAN_REVIEW rows from a <phase>_prelabeled.csv into a
small standalone review queue with an empty human_label column to fill in.

Editing a small dedicated file (instead of the full 100+ row prelabeled CSV)
makes it much harder to accidentally overwrite final_label/llm_pre_label/
local_judge_label -- those columns are dropped here entirely; only what you
need to make a decision is kept.

Usage:
  python make_review_queue.py --phase baseline
  python make_review_queue.py --input ../results/indirect_injection/indirect_injection_prelabeled.csv --output ../results/indirect_injection/indirect_injection_review_queue.csv
"""

import argparse
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "..", "results")

KEEP_COLUMNS = ["id", "category", "prompt", "response", "llm_reason", "local_judge_reason"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", help="Phase name, e.g. baseline, L1L2, full_defense, indirect_injection")
    parser.add_argument("--input", help="Override path to <phase>_prelabeled.csv")
    parser.add_argument("--output", help="Override path to write the review queue CSV")
    args = parser.parse_args()

    if not args.phase and not args.input:
        parser.error("Provide --phase or --input")

    input_path = args.input or os.path.join(RESULTS_ROOT, args.phase, f"{args.phase}_prelabeled.csv")
    output_path = args.output or os.path.join(
        RESULTS_ROOT, args.phase, f"{args.phase}_review_queue.csv"
    )

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    disputed = df[df["final_label"] == "NEEDS_HUMAN_REVIEW"].copy()

    columns = [c for c in KEEP_COLUMNS if c in disputed.columns]
    disputed = disputed[columns]
    disputed["human_label"] = ""  # fill with SUCCESS or FAIL only

    disputed.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"{len(disputed)} disputed rows -> {output_path}")
    print("Fill in the human_label column (SUCCESS or FAIL only), save, then run merge_human_review.py.")


if __name__ == "__main__":
    main()

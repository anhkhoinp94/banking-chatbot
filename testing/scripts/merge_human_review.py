"""Merge a filled-in review queue (from make_review_queue.py) back into the
full <phase>_prelabeled.csv as a `human_label` column, matched by `id`.

Never touches llm_pre_label / local_judge_label / final_label -- those stay
as the automated audit trail. Safe to run multiple times / incrementally:
only rows present with a non-empty human_label in the queue are written;
everything else in the target file is left untouched.

Usage:
  python merge_human_review.py --phase baseline
"""

import argparse
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "..", "results")

VALID_LABELS = {"SUCCESS", "FAIL"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", help="Phase name, e.g. baseline, L1L2, full_defense, indirect_injection")
    parser.add_argument("--target", help="Override path to <phase>_prelabeled.csv")
    parser.add_argument("--queue", help="Override path to the filled-in review queue CSV")
    args = parser.parse_args()

    if not args.phase and not (args.target and args.queue):
        parser.error("Provide --phase, or both --target and --queue")

    target_path = args.target or os.path.join(RESULTS_ROOT, args.phase, f"{args.phase}_prelabeled.csv")
    queue_path = args.queue or os.path.join(RESULTS_ROOT, args.phase, f"{args.phase}_review_queue.csv")

    target = pd.read_csv(target_path, encoding="utf-8-sig")
    queue = pd.read_csv(queue_path, encoding="utf-8-sig")

    queue["human_label"] = queue["human_label"].astype(str).str.strip().str.upper()
    filled = queue[queue["human_label"].isin(VALID_LABELS)]
    skipped = len(queue) - len(filled)

    if "human_label" not in target.columns:
        target["human_label"] = pd.Series([pd.NA] * len(target), dtype="object")
    else:
        target["human_label"] = target["human_label"].astype("object")

    label_by_id = dict(zip(filled["id"], filled["human_label"]))
    updated = 0
    for idx, row in target.iterrows():
        if row["id"] in label_by_id:
            target.at[idx, "human_label"] = label_by_id[row["id"]]
            updated += 1

    target.to_csv(target_path, index=False, encoding="utf-8-sig")
    print(f"Updated {updated} rows in {target_path} (human_label).")
    if skipped:
        print(f"Skipped {skipped} rows in the queue with empty/invalid human_label (not SUCCESS/FAIL).")

    still_open = target[(target["final_label"] == "NEEDS_HUMAN_REVIEW") & target["human_label"].isna()]
    if len(still_open):
        print(f"{len(still_open)} disputed rows still have no human_label yet: ids {sorted(still_open['id'].tolist())}")


if __name__ == "__main__":
    main()

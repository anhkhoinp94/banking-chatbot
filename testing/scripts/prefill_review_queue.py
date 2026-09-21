"""Bulk-fill a review queue's human_label column from the Groq judge
(llm_pre_label), for rows where you've confirmed your own read agrees with
Groq -- use this instead of retyping SUCCESS/FAIL by hand for every row.

Only fills rows where human_label is currently blank; anything you already
typed in manually is left untouched (so you can still hand-correct specific
rows -- e.g. exceptions where you disagree with Groq -- before or after
running this).

Usage:
  python prefill_review_queue.py --phase baseline
  python prefill_review_queue.py --phase baseline --skip-ids 7 42   # leave these blank for manual review
"""

import argparse
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "..", "results")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--queue", help="Override path to the review queue CSV")
    parser.add_argument("--prelabeled", help="Override path to the <phase>_prelabeled.csv (source of llm_pre_label)")
    parser.add_argument("--skip-ids", nargs="*", type=int, default=[], help="ids to leave blank (for manual review)")
    args = parser.parse_args()

    queue_path = args.queue or os.path.join(RESULTS_ROOT, args.phase, f"{args.phase}_review_queue.csv")
    prelabeled_path = args.prelabeled or os.path.join(RESULTS_ROOT, args.phase, f"{args.phase}_prelabeled.csv")

    queue = pd.read_csv(queue_path, encoding="utf-8-sig")
    queue["human_label"] = queue["human_label"].astype("object")
    prelabeled = pd.read_csv(prelabeled_path, encoding="utf-8-sig")
    groq_by_id = dict(zip(prelabeled["id"], prelabeled["llm_pre_label"]))

    filled = 0
    for idx, row in queue.iterrows():
        current = str(row["human_label"]).strip().upper()
        if current in ("SUCCESS", "FAIL"):
            continue  # already reviewed manually, don't touch
        if row["id"] in args.skip_ids:
            continue
        groq_label = groq_by_id.get(row["id"])
        if groq_label in ("SUCCESS", "FAIL"):
            queue.at[idx, "human_label"] = groq_label
            filled += 1

    queue.to_csv(queue_path, index=False, encoding="utf-8-sig")
    print(f"Prefilled {filled} row(s) in {queue_path} from llm_pre_label.")
    if args.skip_ids:
        print(f"Left blank for manual review: {args.skip_ids}")
    print("Review the file before merging -- especially any --skip-ids rows -- then run merge_human_review.py.")


if __name__ == "__main__":
    main()

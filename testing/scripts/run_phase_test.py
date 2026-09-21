"""Generalized test runner for any defense phase (baseline, L1L2, full_defense, ...).

Sends every prompt in the test set to the chatbot with a chosen defense_config,
saves one row per prompt to testing/results/<phase>/<phase>_results.csv.

Same shape/columns as testing/scripts/run_baseline_test.py so the rest of the
pipeline (pre_label.py, local_judge.py, generate_summary.py) works unchanged
across phases.

Usage:
  python run_phase_test.py --phase L1L2 --defense layer1=true,layer2=true,layer3=false
  python run_phase_test.py --phase full_defense --defense on
"""

import argparse
import io
import os
import sys
import time
from datetime import datetime

import pandas as pd
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_SET_PATH = os.path.join(BASE_DIR, "..", "data", "test_set.csv")
RESULTS_ROOT = os.path.join(BASE_DIR, "..", "results")

API_URL = "http://127.0.0.1:8000/chat"

DEFAULT_CONFIG = {"layer1": False, "layer2": False, "layer3": False}


def parse_defense_config(value: str) -> dict[str, bool]:
    if value.lower() == "off":
        return DEFAULT_CONFIG.copy()
    if value.lower() == "on":
        return {layer: True for layer in DEFAULT_CONFIG}
    config = DEFAULT_CONFIG.copy()
    for item in value.split(","):
        layer, enabled = item.split("=", maxsplit=1)
        if layer not in config or enabled.lower() not in ("true", "false"):
            raise ValueError(f"Invalid defense setting: {item}")
        config[layer] = enabled.lower() == "true"
    return config


def call_chatbot(prompt_text: str, defense_config: dict[str, bool], timeout: float) -> str:
    response = requests.post(
        API_URL,
        json={"message": prompt_text, "defense_config": defense_config},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("answer", "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, help="Phase name, e.g. L1L2, full_defense")
    parser.add_argument("--defense", default="off", help="off, on, or layer1=true,layer2=false,...")
    parser.add_argument("--test-set", default=TEST_SET_PATH)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    defense_config = parse_defense_config(args.defense)
    results_dir = os.path.join(RESULTS_ROOT, args.phase)
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, f"{args.phase}_results.csv")

    df = pd.read_csv(args.test_set, encoding="utf-8-sig")
    if args.limit:
        df = df.head(args.limit)

    print(f"Running phase '{args.phase}' ({defense_config}) over {len(df)} prompts...")

    rows = []
    for idx, row in df.iterrows():
        try:
            answer = call_chatbot(row["text"], defense_config, args.timeout)
            error = ""
        except requests.RequestException as exc:
            answer = ""
            error = str(exc)
        rows.append(
            {
                "id": row.get("id", idx + 1),
                "prompt": row["text"],
                "category": row.get("category", ""),
                "response": answer,
                "timestamp": datetime.now().isoformat(),
                "defense_config": args.defense,
                "error": error,
            }
        )
        print(f"[{idx + 1}/{len(df)}] id={row.get('id', idx + 1)} category={row.get('category', '')} -> {'ERROR' if error else 'ok'}", flush=True)
        time.sleep(0.2)

    pd.DataFrame(rows).to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(rows)} results to {output_path}")


if __name__ == "__main__":
    main()

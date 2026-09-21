"""Run the CSV prompt set against the chatbot and save one result per row."""

import argparse
import csv
import os
from pathlib import Path

import requests


DEFAULT_DEFENSE_CONFIG = {"layer1": False, "layer2": False, "layer3": False}
PROMPT_COLUMNS = ("prompt", "message", "question", "input")


def parse_defense_config(value: str) -> dict[str, bool]:
    if value.lower() == "off":
        return DEFAULT_DEFENSE_CONFIG.copy()
    if value.lower() == "on":
        return {layer: True for layer in DEFAULT_DEFENSE_CONFIG}

    config = DEFAULT_DEFENSE_CONFIG.copy()
    for item in value.split(","):
        layer, enabled = item.split("=", maxsplit=1)
        if layer not in config or enabled.lower() not in ("true", "false"):
            raise ValueError(f"Invalid defense setting: {item}")
        config[layer] = enabled.lower() == "true"
    return config


def find_prompt(row: dict[str, str]) -> str:
    for column in PROMPT_COLUMNS:
        if row.get(column, "").strip():
            return row[column].strip()
    raise ValueError("CSV row has no prompt, message, question, or input column")


def run_baseline(
    input_path: Path,
    output_path: Path,
    api_url: str,
    defense_config: dict[str, bool],
    timeout: float,
    limit: int | None,
) -> int:
    with input_path.open(newline="", encoding="utf-8-sig") as input_file:
        rows = list(csv.DictReader(input_file))

    selected_rows = rows[:limit] if limit is not None else rows
    if not 110 <= len(selected_rows) <= 170:
        raise ValueError(
            f"Baseline requires 110-170 prompts; selected {len(selected_rows)}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_fields = [
        "row_number",
        "prompt",
        "expected_label",
        "defense_config",
        "http_status",
        "answer",
        "error",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_fields)
        writer.writeheader()
        with requests.Session() as session:
            for row_number, row in enumerate(selected_rows, start=1):
                prompt = find_prompt(row)
                result = {
                    "row_number": row_number,
                    "prompt": prompt,
                    "expected_label": row.get("label", ""),
                    "defense_config": str(defense_config),
                    "http_status": "",
                    "answer": "",
                    "error": "",
                }
                try:
                    response = session.post(
                        api_url,
                        json={"message": prompt, "defense_config": defense_config},
                        timeout=timeout,
                    )
                    result["http_status"] = response.status_code
                    response_data = response.json()
                    result["answer"] = response_data.get("answer", "")
                    if not response.ok:
                        result["error"] = str(response_data)
                except (requests.RequestException, ValueError) as error:
                    result["error"] = str(error)
                writer.writerow(result)

    return len(selected_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/baseline.csv"))
    parser.add_argument(
        "--api-url",
        default=os.environ.get("BACKEND_URL", "http://localhost:8000/chat"),
    )
    parser.add_argument("--defense", default="off", help="off, on, or layer1=true,...")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=60)
    arguments = parser.parse_args()
    count = run_baseline(
        arguments.input,
        arguments.output,
        arguments.api_url,
        parse_defense_config(arguments.defense),
        arguments.timeout,
        arguments.limit,
    )
    print(f"Saved {count} results to {arguments.output}")


if __name__ == "__main__":
    main()
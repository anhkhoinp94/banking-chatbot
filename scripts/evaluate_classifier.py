"""Evaluate the injection classifier and print handoff-ready metrics."""

import argparse
import csv
import json
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


def read_dataset(path: Path) -> tuple[list[str], list[int]]:
    texts, labels = [], []
    with path.open(encoding="utf-8-sig", newline="") as input_file:
        for row in csv.DictReader(input_file):
            text = row.get("prompt") or row.get("message") or row.get("question") or row.get("input")
            label = row.get("label", "").strip().casefold()
            if text and label:
                texts.append(text)
                labels.append(1 if label in {"injection", "malicious", "1", "true"} else 0)
    return texts, labels


def evaluate(input_path: Path, model_path: Path, output_path: Path | None = None) -> dict:
    texts, labels = read_dataset(input_path)
    _, test_texts, _, test_labels = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    model = joblib.load(model_path)
    predictions = model.predict(test_texts)
    result = {
        "accuracy": accuracy_score(test_labels, predictions),
        "precision": precision_score(test_labels, predictions, zero_division=0),
        "recall": recall_score(test_labels, predictions, zero_division=0),
        "f1": f1_score(test_labels, predictions, zero_division=0),
        "confusion_matrix": confusion_matrix(test_labels, predictions, labels=[0, 1]).tolist(),
        "test_samples": len(test_labels),
    }
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("backend/defense/classifier.pkl"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evaluate(args.input, args.model, args.output)
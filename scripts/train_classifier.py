"""Train the Week 2 TF-IDF + Logistic Regression injection classifier."""

import argparse
import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def train(input_path: Path, output_path: Path) -> None:
    texts, labels = [], []
    with input_path.open(encoding="utf-8-sig", newline="") as input_file:
        for row in csv.DictReader(input_file):
            text = row.get("prompt") or row.get("message") or row.get("question") or row.get("input")
            label = row.get("label", "").strip().casefold()
            if text and label:
                texts.append(text)
                labels.append(1 if label in {"injection", "malicious", "1", "true"} else 0)
    if len(set(labels)) < 2:
        raise ValueError("Training CSV must contain both benign and injection labels")
    model = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(texts, labels)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    print(f"Saved classifier with {len(texts)} samples to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("backend/defense/classifier.pkl"))
    args = parser.parse_args()
    train(args.input, args.output)
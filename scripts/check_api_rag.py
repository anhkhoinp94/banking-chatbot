"""Smoke-check the API and verify answers use facts from artifacts/documents/bank.txt."""

import argparse
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--document", type=Path, default=Path("artifacts/documents/bank.txt"))
    arguments = parser.parse_args()

    with arguments.document.open("rb") as document_file:
        load_response = requests.post(
            f"{arguments.base_url}/embeddings/load",
            files={"file": (arguments.document.name, document_file, "text/plain")},
            timeout=60,
        )
    load_response.raise_for_status()

    chat_response = requests.post(
        f"{arguments.base_url}/chat",
        json={"message": "Hạn mức chuyển khoản mỗi ngày là bao nhiêu?"},
        timeout=60,
    )
    chat_response.raise_for_status()
    answer = chat_response.json()["answer"]
    if "100 triệu" not in answer:
        raise RuntimeError(f"RAG answer did not contain the document fact: {answer}")
    print("API and RAG smoke-check passed")


if __name__ == "__main__":
    main()
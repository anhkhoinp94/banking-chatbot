"""Test Indirect Injection: upload each poisoned document in isolation,
ask the 3 shared test questions under two defense configs (off / full), record
responses, then restore the original bank.txt so the app is left in its normal
demo state.

Output shape matches the other phases (id, prompt, category, response,
timestamp, defense_config) so pre_label.py / local_judge.py / generate_summary.py
work unchanged on it.

Requires: docker-compose stack running, backend reachable on :8000, chromadb
on :8001 (matches backend/routers/chat.py defaults).

Usage:
  python run_indirect_injection_test.py
"""

import io
import os
import sys
import time
from datetime import datetime

import chromadb
import pandas as pd
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDIRECT_DIR = os.path.join(BASE_DIR, "..", "indirect_injection")
RESULTS_DIR = os.path.join(BASE_DIR, "..", "results", "indirect_injection")
QUESTIONS_PATH = os.path.join(INDIRECT_DIR, "indirect_injection_test_questions.md")
ORIGINAL_DOC_PATH = os.path.join(BASE_DIR, "..", "..", "artifacts", "documents", "bank.txt")

API_URL = "http://127.0.0.1:8000/chat"
EMBED_URL = "http://127.0.0.1:8000/embeddings/load"
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8001"))
COLLECTION_NAME = "bank"

TECHNIQUES = {
    "indirect_v1_appended_instruction": os.path.join(INDIRECT_DIR, "bank_policy_poisoned_v1.txt"),
    "indirect_v2_embedded_comment": os.path.join(INDIRECT_DIR, "bank_policy_poisoned_v2.txt"),
}

DEFENSE_CONFIGS = {
    "off": {"layer1": False, "layer2": False, "layer3": False},
    "full": {"layer1": True, "layer2": True, "layer3": True},
}


def load_questions() -> list[str]:
    questions = []
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(line.split(".", 1)[1].strip() if line[0].isdigit() else line)
    return questions


def clear_collection(client: chromadb.HttpClient) -> None:
    collection = client.get_or_create_collection(COLLECTION_NAME)
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])


def upload_document(file_path: str) -> None:
    with open(file_path, "rb") as f:
        response = requests.post(EMBED_URL, files={"file": (os.path.basename(file_path), f)}, timeout=60)
    response.raise_for_status()


def ask(prompt_text: str, defense_config: dict[str, bool]) -> str:
    response = requests.post(
        API_URL,
        json={"message": prompt_text, "defense_config": defense_config},
        timeout=90,
    )
    response.raise_for_status()
    return response.json().get("answer", "")


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    questions = load_questions()
    print(f"Loaded {len(questions)} shared test questions.")

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    rows = []
    row_id = 1
    try:
        for technique, doc_path in TECHNIQUES.items():
            print(f"\n=== {technique}: isolating collection, uploading {os.path.basename(doc_path)} ===")
            clear_collection(client)
            upload_document(doc_path)
            time.sleep(1)

            for defense_name, defense_config in DEFENSE_CONFIGS.items():
                for question in questions:
                    answer = ask(question, defense_config)
                    rows.append(
                        {
                            "id": row_id,
                            "prompt": question,
                            "category": "Indirect Injection",
                            "technique": technique,
                            "response": answer,
                            "timestamp": datetime.now().isoformat(),
                            "defense_config": defense_name,
                        }
                    )
                    print(f"[{technique}/{defense_name}] Q: {question[:40]}... -> {answer[:80]!r}")
                    row_id += 1
                    time.sleep(0.2)
    finally:
        print("\n=== Restoring original bank.txt ===")
        clear_collection(client)
        upload_document(ORIGINAL_DOC_PATH)

    output_path = os.path.join(RESULTS_DIR, "indirect_injection_results.csv")
    pd.DataFrame(rows).to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()

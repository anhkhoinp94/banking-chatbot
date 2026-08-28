"""Fastest possible sanity check: fire one prompt at the live /chat endpoint
and print the raw response. Use this first when something in the pipeline
fails, before running a full phase (run_phase_test.py) or the fuller
RAG-content assertion in scripts/check_api_rag.py.

Usage:
  python test_connection.py
"""

import requests

response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"message": "Lai suat tiet kiem hien tai la bao nhieu?"},
    timeout=30
)
print("Status code:", response.status_code)
print("Response:", response.json())
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import pandas as pd
import requests
import time
import os
from datetime import datetime

# ===== PATHS — AUTO-RESOLVED, CORRECT REGARDLESS OF WORKING DIRECTORY =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_SET_PATH = os.path.join(BASE_DIR, "..", "data", "test_set.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "..", "results", "baseline")
RESULTS_PATH = os.path.join(RESULTS_DIR, "baseline_results.csv")

# Auto-create results folder if missing (avoids "folder not found" error)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ===== CONFIG =====
API_URL = "http://127.0.0.1:8000/chat"
DEFENSE_CONFIG = "no_defense"

def call_chatbot(prompt_text):
    try:
        response = requests.post(
            API_URL,
            json={"message": prompt_text},
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("answer", "")
    except requests.exceptions.RequestException as e:
        return f"ERROR: {str(e)}"

# ===== LOAD TEST SET =====
df_test = pd.read_csv(TEST_SET_PATH)
print(f"Preparing to run {len(df_test)} prompts...")
print(f"Reading from: {TEST_SET_PATH}")
print(f"Will save to: {RESULTS_PATH}")

# ===== RUN FULL WITH RETRY LOGIC =====
results = []
start_time = time.time()

for idx, row in df_test.iterrows():
    prompt = row['text']
    category = row['category']
    
    prompt_start = time.time()
    
    response_text = None
    for attempt in range(3):
        response_text = call_chatbot(prompt)
        if not response_text.startswith("ERROR"):
            break
        time.sleep(10)
    
    elapsed = time.time() - prompt_start
    
    results.append({
        "id": row['id'],
        "prompt": prompt,
        "category": category,
        "response": response_text,
        "timestamp": datetime.now().isoformat(),
        "defense_config": DEFENSE_CONFIG
    })
    
    status = "✓" if not response_text.startswith("ERROR") else "✗"
    print(f"[{idx+1}/{len(df_test)}] {status} id={row['id']} | {category} | {elapsed:.1f}s", flush=True)
    time.sleep(2)

total_elapsed = time.time() - start_time

# ===== SAVE RESULTS =====
df_results = pd.DataFrame(results)
df_results.to_csv(RESULTS_PATH, index=False, encoding='utf-8-sig')
print(f"\n✓ Done! Saved {len(df_results)} results to {RESULTS_PATH}")
print(f"Total time: {total_elapsed/60:.1f} minutes")

errors = df_results[df_results['response'].str.startswith("ERROR", na=False)]
if len(errors) > 0:
    print(f"⚠ {len(errors)} prompts failed")
    print(errors[['id', 'category']])
else:
    print("✓ No errors")
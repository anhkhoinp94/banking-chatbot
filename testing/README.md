# Testing — Attack & Measurement Pipeline

This folder contains all the data and scripts used to measure Attack Success Rate (ASR).

## Structure
- `data/` — fixed test set (107 prompts), DO NOT modify once finalized
- `scripts/` — code for running tests and processing results
- `indirect_injection/` — "poisoned" documents and test questions for Indirect Injection
- `criteria/` — Success/Fail evaluation criteria (success_criteria.md)
- `results/` — results per phase (baseline, L1L2, full_defense)

## How to run
1. Make sure the backend is running: `docker-compose up` (from the project root)
2. Run the test: `python scripts/run_baseline_test.py`
3. If there are errors: `python scripts/retry_failed.py`
4. View the report: `python scripts/generate_summary.py`

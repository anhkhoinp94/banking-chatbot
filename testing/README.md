# Testing — Attack & Measurement Pipeline

This folder contains all the data and scripts used to measure Attack Success Rate (ASR)
across defense phases, and to test indirect (document-based) injection. For the classifier training pipeline, see the root `README.md` instead —
that's a separate concern (training data, not attack test data).

## Structure

- `data/` — fixed attack test set (107 prompts, 10 categories), **do not modify once finalized**
- `criteria/` — `Success_Criteria.md`, the SUCCESS/FAIL definitions used by every judge (LLM or human)
- `indirect_injection/` — poisoned documents + shared test questions for the indirect-injection test
- `scripts/` — everything below
- `results/<phase>/` — one folder per test phase (`baseline`, `L1L2`, `full_defense`, `indirect_injection`, `comparison`)

## Full pipeline, in order

### 1. Run a phase against the live chatbot

```powershell
python scripts/run_phase_test.py --phase baseline --defense off
python scripts/run_phase_test.py --phase L1L2 --defense layer1=true,layer2=true,layer3=false
python scripts/run_phase_test.py --phase full_defense --defense on
```

Requires the Docker stack up (`docker-compose up -d`) and `artifacts/documents/bank.txt`
loaded into ChromaDB via `POST /embeddings/load` first. Writes `results/<phase>/<phase>_results.csv`.

(`run_baseline_test.py` and `retry_prelabel_errors.py`/`test_connection.py` are earlier,
narrower versions of this pipeline kept for reference — prefer `run_phase_test.py`
and the scripts below for anything new.)

### 2. Label with two independent LLM judges

```powershell
$env:GROQ_API_KEY = "..."   # never commit this
python scripts/pre_label.py --input results/<phase>/<phase>_results.csv --output results/<phase>/<phase>_prelabeled.csv
python scripts/local_judge.py --input results/<phase>/<phase>_prelabeled.csv --output results/<phase>/<phase>_prelabeled.csv
```

`pre_label.py` uses Groq (`--model`, default `openai/gpt-oss-20b` — the plan's original
`llama-3.1-8b-instant` has been retired by Groq). `local_judge.py` uses a local Ollama
model (`qwen2.5:3b`, no API key needed) as a second, independent opinion. Together they
produce `llm_pre_label`, `local_judge_label`, and `final_label` (`SUCCESS`/`FAIL` where
they agree, `NEEDS_HUMAN_REVIEW` where they don't).

### 3. Human review of disputed rows

```powershell
python scripts/make_review_queue.py --phase baseline        # extracts NEEDS_HUMAN_REVIEW rows only
# ... fill in the human_label column by hand ...
python scripts/prefill_review_queue.py --phase baseline     # optional: bulk-copy llm_pre_label into
                                                              # any still-blank human_label cells, once
                                                              # you've confirmed you agree with it
python scripts/merge_human_review.py --phase baseline       # merges human_label back in, safely
```

`merge_human_review.py` only ever writes to `human_label` — it can't clobber
`final_label`/`llm_pre_label`/`local_judge_label`. Review is incremental: you don't have
to finish a whole file before recomputing ASR.

### 4. Compute ASR + compare phases

```powershell
python scripts/generate_summary.py --phase baseline    # per-category + overall ASR, table + chart
python scripts/generate_summary.py --phase L1L2
python scripts/generate_summary.py --phase full_defense
python scripts/compare_phases.py --phases baseline L1L2 full_defense   # 3-phase comparison table + chart
```

`generate_summary.py` resolves each row's effective label as `human_label` (if filled)
→ `final_label` → `llm_pre_label`, so it always reflects the best available review state,
even mid-review.

### 5. Indirect injection test

```powershell
python scripts/run_indirect_injection_test.py
```

Uploads each poisoned document (`indirect_injection/bank_policy_poisoned_v1.txt` and
`_v2.txt`) into an **isolated** ChromaDB collection (cleared before each upload), asks the
3 shared questions (`indirect_injection/indirect_injection_test_questions.md`) under
`off` and `full` defense configs, then **restores the original `bank.txt`** so the app is
left in its normal demo state. Output goes to `results/indirect_injection/`, then through
the same labeling pipeline as any other phase (steps 2–4 above).

## Script index

| Script | Status | Purpose |
|---|---|---|
| `run_phase_test.py` | **active** | Run any phase (any `--phase` name, any `--defense` config) against the live chatbot |
| `pre_label.py` | **active** | Judge A — label a phase's results via Groq LLM |
| `local_judge.py` | **active** | Judge B — label via local Ollama model, computes agreement + `final_label` |
| `make_review_queue.py` | **active** | Extract `NEEDS_HUMAN_REVIEW` rows into a small file for manual review |
| `prefill_review_queue.py` | **active** | Bulk-copy `llm_pre_label` into unfilled `human_label` cells (for rows you've confirmed) |
| `merge_human_review.py` | **active** | Merge a filled review queue back into `human_label`, safely |
| `generate_summary.py` | **active** | Compute per-category + overall ASR (table + chart) for one phase |
| `compare_phases.py` | **active** | ASR comparison table + chart across multiple phases |
| `run_indirect_injection_test.py` | **active** | Isolated indirect-injection test (both poisoned docs, off/full defense) |
| `retry_prelabel_errors.py` | **active, narrow** | Retry only the `ERROR` rows from a `pre_label.py` run, in place |
| `test_connection.py` | **active, narrow** | Fastest one-shot sanity check that `/chat` is reachable |
| `run_baseline_test.py` | **legacy** | Original baseline-only runner; superseded by `run_phase_test.py --phase baseline --defense off` |

Every script above has a top-of-file docstring with usage — this table is a map to
find the right one, not a substitute for reading it before you run it.

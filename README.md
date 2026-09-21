# banking-chatbot
uv pip install streamlit fastapi uvicorn requests
uv pip install chromadb langchain langchain-chroma langchain-ollama
uv pip install langchain-text-splitters
uv pip install scikit-learn
pip install pypdf

cd backend
uvicorn app:app --reload
Running on: http://127.0.0.1:8000

cd frontend
streamlit run app.py
Running on: http://localhost:8501


docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
docker exec -it ollama bash --- Ctrl + D
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

docker run -d --name chroma -p 8001:8000 -v chroma_data:/data chromadb/chroma

# How to run?
## 1. docker build -f Dockerfile.ollama -t local-ollama .
## 2. docker-compose up -d
# BE: http://localhost:8000/docs (swagger)
Load `\artifacts\documents\bank.txt` to api: 'http://localhost:8000/embeddings/load' to import documents
# FE: http://localhost:8501/

## Two pipelines in this repo — which one to use

This repo has **two separate scripts/artifacts sets** that serve different purposes. They are not duplicates of each other; use whichever matches what you're trying to do:

- **`scripts/` + `artifacts/`** (this README, below) — classifier training/evaluation (`train_classifier.py`, `evaluate_classifier.py`) and a one-off API/RAG smoke-check (`check_api_rag.py`). `artifacts/input/test_cases.csv` is a small balanced benign/injection set used only to train and evaluate the Layer 3 classifier.
- **`testing/`** — the full attack-testing pipeline: the categorized 107-prompt attack test set, the baseline/L1+L2/full-defense re-test runners, the indirect-injection test, the dual-LLM-judge + human-review labeling workflow, and ASR comparison across phases. **See `testing/README.md` for the full pipeline docs — start there for anything ASR/attack-related.**

`scripts/baseline.py` (this README used to document it below) is now superseded by `testing/scripts/run_phase_test.py`, which supports the same off/on/custom `--defense` flag plus per-prompt `category` and writes output in the schema the rest of the `testing/` pipeline expects. Prefer `testing/scripts/run_phase_test.py` for any new baseline/re-test run.

## Defense layers

The API applies enabled layers in this order: keyword filtering (Layer 2),
TF-IDF + Logistic Regression classifier (Layer 3), prompt sandwiching (Layer
1), and output validation. A blocked request returns a safe fallback and is
logged with `blocked_at_layer`. If `classifier.pkl` is not present, Layer 3
uses the built-in regex-heuristic detector until a trained model is supplied.

Which layers run is controlled per-request via `defense_config` in the JSON body:

```json
{"message": "Hạn mức chuyển khoản là bao nhiêu?", "defense_config": {"layer1": true, "layer2": false, "layer3": false}}
```

The selected configuration is sent with every request and included in the
backend JSON log at `logs/chat_logs.json`. `testing/scripts/run_phase_test.py`
accepts `--defense off`, `--defense on`, or an explicit combination such as
`--defense layer1=true,layer2=true,layer3=false` and sets this field for you.

### Classifier training (Layer 3)

Train and evaluate the classifier from the labeled test set:

```powershell
python scripts/train_classifier.py --input artifacts/input/test_cases.csv
python scripts/evaluate_classifier.py --input artifacts/input/test_cases.csv --output artifacts/output/classifier_metrics.json
```

The keyword list is maintained in `backend/defense/keywords.json`, so new
patterns can be added without changing Python code.

## API and RAG smoke-check

After starting the services, run this repeatable check from the repository
root:

```powershell
python scripts/check_api_rag.py
```

The script uploads `artifacts/documents/bank.txt` through `/embeddings/load`, calls `/chat`
with a question whose answer is present in that document, and fails unless
the response contains `100 triệu`. A successful run prints
`API and RAG smoke-check passed`.


### Cấu hình chia nhỏ tài liệu (Text Splitting)

Hệ thống sử dụng `RecursiveCharacterTextSplitter` để chia tài liệu thành các đoạn nhỏ trước khi lưu vào ChromaDB.

- `chunk_size = 500`
- `chunk_overlap = 100`

Cấu hình:

```python
RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

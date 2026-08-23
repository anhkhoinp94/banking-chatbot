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

## Baseline CSV

The baseline runner is in `scripts/baseline.py`. The input CSV must contain one
prompt column named `prompt`, `message`, `question`, or `input`; an optional
`label` column is preserved in the result. The runner requires 110-170 selected
rows, calls `POST /chat` once per row, and writes every success or error to CSV.

Run the baseline with all defenses off:

```powershell
python scripts/baseline.py --input artifacts/input/test_cases.csv --defense off --output output/baseline.csv
```

The API also accepts `defense_config` in the JSON request. For example:

```json
{"message": "Hạn mức chuyển khoản là bao nhiêu?", "defense_config": {"layer1": true, "layer2": false, "layer3": false}}
```

The baseline runner accepts `--defense off`, `--defense on`, or an explicit
configuration such as `--defense layer1=true,layer2=true,layer3=false`.
The selected configuration is sent with every request and included in the
backend JSON log at `logs/chat_logs.json`.

## Week 2 defenses

The API applies enabled layers in this order: keyword filtering (Layer 2),
TF-IDF + Logistic Regression classifier (Layer 3), prompt sandwiching (Layer
1), and output validation. A blocked request returns a safe fallback and is
logged with `blocked_at_layer`. If `classifier.pkl` is not present, Layer 3
uses the built-in detector until a trained model is supplied.

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

# banking-chatbot
uv pip install streamlit fastapi uvicorn requests
uv pip install chromadb langchain langchain-chroma langchain-ollama
uv pip install langchain-text-splitters
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
## docker-compose up -d
# BE: http://127.0.0.1:8000/docs (swagger)
Load \data\bank.txt to api: 'http://localhost:8000/embeddings/load' to import documents
# FE: http://localhost:8501/

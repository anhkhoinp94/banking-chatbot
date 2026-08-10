import os

import chromadb
from fastapi import APIRouter, UploadFile, File
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from pydantic import BaseModel
from langchain_core.documents import Document

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8001"))

ollama_url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=ollama_url,
)

chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

db = Chroma(client=chroma_client, collection_name="bank", embedding_function=embeddings)

llm = ChatOllama(
    model="qwen2.5:3b",
    base_url=ollama_url,
)


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


sample_prompt = """
Bạn là trợ lý ngân hàng.

Chỉ được trả lời dựa trên CONTEXT dưới đây.
Nếu không tìm thấy thông tin thì trả lời:
"Tôi không tìm thấy thông tin trong tài liệu."

CONTEXT:
<<REPLACE_CONTEXT>>

QUESTION:
<<REPLACE_QUESTION>>
"""


@router.post("/chat")
def chat(request: ChatRequest):
    docs = db.similarity_search(request.message, k=3)

    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = sample_prompt.replace("<<REPLACE_CONTEXT>>", context)
    prompt = prompt.replace("<<REPLACE_QUESTION>>", request.message)

    response = llm.invoke(prompt)

    return {"answer": response.content}


@router.post("/embeddings/load")
async def load_embeddings(file: UploadFile = File(...)):
    doc = Document(page_content="Xin chào")
    db.add_documents([doc])

    content = (await file.read()).decode("utf-8")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.create_documents([content])

    db.add_documents(chunks)

    return {
        "filename": file.filename,
        "chunks": len(chunks),
        "message": "Embeddings loaded successfully.",
    }

import os

import chromadb
from fastapi import APIRouter, UploadFile, File
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from langchain_core.documents import Document

try:
    from backend.core.logging import RequestLogger
    from backend.defense.pipeline import DefensePipeline
except ModuleNotFoundError:
    from core.logging import RequestLogger
    from defense.pipeline import DefensePipeline

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8001"))

ollama_url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=ollama_url,
    temperature=0.0,
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
    defense_config: dict[str, bool] = Field(
        default_factory=lambda: {
            "layer1": False,
            "layer2": False,
            "layer3": False,
        }
    )


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

request_logger = RequestLogger()
defense_pipeline = DefensePipeline()


@router.post("/chat")
def chat(request: ChatRequest):
    docs = db.similarity_search(request.message, k=3)

    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = sample_prompt.replace("<<REPLACE_CONTEXT>>", context)
    prompt = prompt.replace("<<REPLACE_QUESTION>>", request.message)

    defense_config = {
        "layer1": bool(request.defense_config.get("layer1", False)),
        "layer2": bool(request.defense_config.get("layer2", False)),
        "layer3": bool(request.defense_config.get("layer3", False)),
    }
    result = defense_pipeline.process(
        request.message,
        prompt,
        llm.invoke,
        defense_config,
    )

    request_logger.log(
        prompt_id="banking_assistant_v1",
        defense_config={
            "context_only": True,
            "fallback": "Tôi không tìm thấy thông tin trong tài liệu.",
            "layers": defense_config,
        },
        blocked_at_layer=result.blocked_at_layer,
        response=result.answer,
        label=result.label,
    )

    return {"answer": result.answer}


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

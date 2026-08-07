from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
def chat(data: dict):
    message = data["message"]

    return {"answer": f"Bạn vừa nói: {message}"}

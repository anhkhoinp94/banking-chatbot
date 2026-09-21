from fastapi import FastAPI
try:
	from routers.chat import router
except ModuleNotFoundError:
	from backend.routers.chat import router

app = FastAPI()

app.include_router(router)

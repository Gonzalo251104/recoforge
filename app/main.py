from fastapi import FastAPI
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}

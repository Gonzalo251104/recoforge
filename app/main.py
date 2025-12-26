from fastapi import FastAPI
from app.core.config import settings
from app.api.routes_reco import router as reco_router
from app.api.routes_events import router as events_router
from app.api.routes_users import router as users_router
from app.api.routes_items import router as items_router
from app.api.routes_metrics import router as metrics_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reco_router)
app.include_router(events_router)
app.include_router(users_router)
app.include_router(items_router)
app.include_router(metrics_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}

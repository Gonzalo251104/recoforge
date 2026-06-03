from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine

# Import models so SQLModel registers their metadata for table creation
from app.db.models import User, Item, Interaction

from app.api.routes_reco import router as reco_router
from app.api.routes_events import router as events_router
from app.api.routes_users import router as users_router
from app.api.routes_items import router as items_router
from app.api.routes_metrics import router as metrics_router

# Setup logger for main module
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    setup_logging()
    logger.info("Initializing database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables initialized. Application started.")
    yield
    # Shutdown logic
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Global unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception occurred during request to {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again later."},
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Duration: {duration:.4f}s"
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
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

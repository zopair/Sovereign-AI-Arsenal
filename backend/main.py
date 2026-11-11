from contextlib import asynccontextmanager
import logging
import os
import time
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .database.db import init_database
from .database.vector_store import init_vector_store
from .api.routes import router as api_router
from .security import api_key_is_valid


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


config = load_config()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", config.get("logging", {}).get("level", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def configured_cors_origins():
    raw = os.getenv("CORS_ORIGINS")
    if raw is not None:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return config.get("api", {}).get("cors_origins", [])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Sovereign AI Arsenal...")
    init_database()
    logger.info("Database initialized")
    init_vector_store(config.get("vector_store", {}))
    logger.info("Vector store initialized")
    yield
    logger.info("Shutting down Sovereign AI Arsenal...")


app = FastAPI(
    title="Sovereign AI Arsenal",
    description="Modular AI intelligence platform for discovering and analyzing AI repositories",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def enforce_api_key(request: Request, call_next):
    """Protect data and operational endpoints; health remains available to probes."""
    protected = request.url.path.startswith("/api/") or request.url.path == "/metrics"
    if protected:
        expected_key = os.getenv("API_AUTH_TOKEN")
        provided_key = request.headers.get("X-API-Key")
        if not expected_key:
            return JSONResponse(
                status_code=503,
                content={"detail": "API authentication is not configured"},
            )
        if not api_key_is_valid(provided_key, expected_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )
    return await call_next(request)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.perf_counter() - start_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router)


@app.get("/health")
async def health_check():
    from .database.db import db

    try:
        with db.get_session() as session:
            session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
        }
    except Exception:
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"},
        )


@app.get("/")
async def root():
    return {
        "name": "Sovereign AI Arsenal",
        "description": "AI intelligence platform for discovering and analyzing AI repositories",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/metrics")
async def metrics():
    try:
        from datetime import datetime, timedelta
        from .database.db import db
        from .database.models import Repository, Classification

        with db.get_session() as session:
            total_repos = session.query(Repository).count()
            total_classifications = session.query(Classification).count()
            recent_repos = session.query(Repository).filter(
                Repository.updated_at >= datetime.utcnow() - timedelta(days=7)
            ).count()

        return {
            "total_repositories": total_repos,
            "total_classifications": total_classifications,
            "recent_activity": recent_repos,
            "timestamp": time.time(),
        }
    except Exception:
        logger.exception("Error getting metrics")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import app.models  # Ensures all ORM models are registered in Base.metadata
from app.api import routes_auth, routes_documents, routes_chat, routes_workspaces
from app.config import settings
from app.database import Base, engine, is_testing
from app.services import vector_store

logger = logging.getLogger(__name__)

# Ensure tables are created in development/test environments; production relies on Alembic migrations
if settings.ENVIRONMENT.strip().lower() != "production" and not is_testing:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Base.metadata.create_all notice: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load Fastembed model during application startup
    import os
    if os.environ.get("TESTING") != "1":
        try:
            from app.services.embedding_service import _get_fastembed
            _get_fastembed()
            logger.info("Fastembed embedding model loaded successfully.")
        except Exception as e:
            logger.warning("Fastembed pre-load notice: %s", e)
    yield


app = FastAPI(title="DocuMind AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_documents.router)
app.include_router(routes_chat.router)
app.include_router(routes_workspaces.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = uuid.uuid4().hex[:12]
    logger.exception("Unhandled server exception [correlation_id=%s]: %s", correlation_id, exc)
    origin = request.headers.get("origin", "*")
    response_content = {
        "detail": "An internal server error occurred. Please contact support or try again later.",
        "correlation_id": correlation_id,
    }
    if settings.ENVIRONMENT.strip().lower() == "development":
        response_content["debug_error"] = str(exc)[:200]

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "docmind-ai-backend",
        "message": "DocuMind AI Backend is live!",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health():
    """Liveness probe: returns 200 if the process is responsive."""
    return {"status": "ok", "service": "docmind-ai-backend"}


@app.get("/api/ready")
def readiness():
    """Readiness probe: verifies operational connectivity to Postgres and Qdrant."""
    checks = {
        "database": "unknown",
        "vector_store": "unknown",
    }

    # 1. Database Check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        logger.error("Readiness check: database failure: %s", e)
        checks["database"] = "unreachable"

    # 2. Vector Store Check
    try:
        client = vector_store.get_client()
        client.get_collections()
        checks["vector_store"] = "connected"
    except Exception as e:
        logger.error("Readiness check: vector store failure: %s", e)
        checks["vector_store"] = "unreachable"

    all_healthy = all(status == "connected" for status in checks.values())
    http_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": "ready" if all_healthy else "degraded",
            "dependencies": checks,
        },
    )

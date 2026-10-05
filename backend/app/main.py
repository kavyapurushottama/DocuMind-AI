from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
import app.models  # Ensures all ORM models are registered in Base.metadata
from app.api import routes_auth, routes_documents, routes_chat, routes_workspaces
from app.config import settings
from app.database import Base, engine

# create tables on startup
Base.metadata.create_all(bind=engine)

# Add columns dynamically if they don't exist
with engine.connect() as connection:
    is_postgres = engine.dialect.name == "postgresql"
    statements = [
        "ALTER TABLE conversations ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE NOT NULL;" if not is_postgres else "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;",
        "ALTER TABLE documents ADD COLUMN status_detail VARCHAR;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS status_detail VARCHAR;",
        "ALTER TABLE documents ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;",
        "ALTER TABLE conversations ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;" if not is_postgres else "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;",
        "ALTER TABLE documents ADD COLUMN author VARCHAR;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS author VARCHAR;",
        "ALTER TABLE documents ADD COLUMN created_date TIMESTAMP WITH TIME ZONE;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS created_date TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE documents ADD COLUMN modified_date TIMESTAMP WITH TIME ZONE;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS modified_date TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE documents ADD COLUMN tags VARCHAR;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS tags VARCHAR;",
        "ALTER TABLE documents ADD COLUMN language VARCHAR;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS language VARCHAR;",
        "ALTER TABLE documents ADD COLUMN department VARCHAR;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS department VARCHAR;",
        "ALTER TABLE documents ADD COLUMN document_type VARCHAR;" if not is_postgres else "ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_type VARCHAR;",
    ]
    for stmt in statements:
        try:
            connection.execute(text(stmt))
            connection.commit()
        except Exception:
            pass




from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load Fastembed model during application startup
    try:
        from app.services.embedding_service import _get_fastembed
        _get_fastembed()
    except Exception as e:
        print(f"Fastembed pre-load notice: {e}")
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


from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger(__name__).exception(f"Unhandled exception: {exc}")
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)[:500]},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/")
def root():
    return {"status": "ok", "service": "docmind-ai-backend", "message": "DocuMind AI Backend is live!"}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "docmind-ai-backend"}

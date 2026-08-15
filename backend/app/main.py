from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
import app.models  # Ensures all ORM models are registered in Base.metadata
from app.api import routes_auth, routes_documents, routes_chat
from app.config import settings
from app.database import Base, engine

# create tables on startup (fine for V1; switch to Alembic migrations later)
Base.metadata.create_all(bind=engine)

# Add columns dynamically if they don't exist
with engine.connect() as connection:
    connection.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS status_detail VARCHAR;"))
    
    # Workspaces DDL
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;"))
    connection.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;"))
    
    # Document Metadata Fields DDL
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS author VARCHAR;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS created_date TIMESTAMP WITH TIME ZONE;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS modified_date TIMESTAMP WITH TIME ZONE;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS tags VARCHAR;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS language VARCHAR;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS department VARCHAR;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_type VARCHAR;"))
    
    connection.commit()

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_documents.router)
app.include_router(routes_chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "docmind-ai-backend"}

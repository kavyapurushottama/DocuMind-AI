from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from app.api import routes_auth, routes_documents, routes_chat
from app.config import settings
from app.database import Base, engine

# create tables on startup (fine for V1; switch to Alembic migrations later)
Base.metadata.create_all(bind=engine)

# Add columns dynamically if they don't exist
with engine.connect() as connection:
    connection.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;"))
    connection.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS status_detail VARCHAR;"))
    connection.commit()

app = FastAPI(title="DocuMind AI", version="1.0.0")

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

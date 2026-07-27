from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_auth, routes_documents, routes_chat
from app.config import settings
from app.database import Base, engine

# create tables on startup (fine for V1; switch to Alembic migrations later)
Base.metadata.create_all(bind=engine)

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

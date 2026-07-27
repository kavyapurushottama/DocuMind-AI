# DocuMind AI

An AI-powered document knowledge assistant. Upload PDFs, DOCX, TXT, or
Markdown files, ask questions in plain English, and get answers grounded in
your own documents — with citations (filename, page number, relevance score).

This is **V1 (MVP)**: auth, upload, the ingestion pipeline, RAG chat with
citations, and chat history. Everything runs for free (Groq/Gemini free
tiers + self-hosted Postgres/Redis/Qdrant in Docker).

## Architecture

```
React + TS + Tailwind  ─────►  FastAPI  ─────►  PostgreSQL  (users, docs, chat history)
                                   │       ─────►  Qdrant      (embeddings, similarity search)
                                   │       ─────►  Redis       (stubbed in V1)
                                   ▼
                          Gemini Embedding API  (free tier)
                          Groq or Gemini Flash  (free tier, swappable via env var)
```

**Ingestion pipeline** (same for every file type):
`Upload → Extract text (format-specific) → Clean → Chunk (with overlap) → Embed → Store in Qdrant + Postgres`

**Query pipeline**:
`Question → Embed → Similarity search in Qdrant (filtered by user/document) → Build grounded prompt → LLM → Answer + citations`

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- A free [Gemini API key](https://aistudio.google.com/apikey) (embeddings, and optionally generation)
- A free [Groq API key](https://console.groq.com/keys) (generation — fast and free)

## 1. Clone and configure

```bash
cd docmind-ai
cp .env.example .env
```

Edit `.env` and fill in `GEMINI_API_KEY` and `GROQ_API_KEY`. Everything else
has a sensible local default.

## 2. Start infrastructure (Postgres, Redis, Qdrant)

```bash
docker compose up -d
docker compose ps   # confirm all three are healthy
```

This does **not** run the app itself — just the databases. That's intentional,
so the backend and frontend can hot-reload natively.

## 3. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# the app reads .env from the backend/ folder — copy the root one in:
cp ../.env .env

uvicorn app.main:app --reload --port 8000
```

Verify it's up: open http://localhost:8000/api/health — you should see
`{"status": "ok", ...}`. Interactive API docs are at http://localhost:8000/docs.

### Verify the pipeline works via curl (before touching the frontend)

```bash
# 1. Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"testpass123","full_name":"You"}'
# copy the access_token from the response

# 2. Upload a PDF
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@/path/to/some.pdf"

# 3. Wait a few seconds for background processing, then check status
curl http://localhost:8000/api/documents -H "Authorization: Bearer <TOKEN>"

# 4. Ask a question once status is "ready"
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"question":"What is this document about?"}'
```

You should get back an answer with a `citations` array pointing to the
filename, page number, and the chunk text used.

## 4. Frontend setup

```bash
cd frontend
cp .env.example .env    # defaults to http://localhost:8000, fine as-is
npm install
npm run dev
```

Open http://localhost:5173 — sign up, upload a document, and chat.

## Project structure

```
docmind-ai/
├── docker-compose.yml       # Postgres, Redis, Qdrant only
├── .env.example
├── backend/
│   └── app/
│       ├── api/             # routes_auth, routes_documents, routes_chat
│       ├── models/          # SQLAlchemy models
│       ├── schemas/         # Pydantic request/response models
│       ├── services/
│       │   ├── extraction/  # pluggable Extractor per file type
│       │   ├── chunking.py
│       │   ├── embedding_service.py   # Gemini embeddings
│       │   ├── vector_store.py        # Qdrant wrapper
│       │   └── rag_service.py         # retrieval + prompt + LLM call
│       └── core/             # security (JWT), deps (current user)
└── frontend/
    └── src/
        ├── pages/            # Login, Signup, Dashboard, Upload, Chat
        ├── components/       # DocumentCard, ChatBubble, CitationBadge, FileUploader
        ├── api/               # typed API client functions
        └── hooks/useAuth.ts
```

## Adding a new file format later

The ingestion pipeline is built around a pluggable `Extractor` base class
(`app/services/extraction/base_extractor.py`). To support a new format:

1. Create `services/extraction/xyz_extractor.py` implementing `extract()`.
2. Register it in the `EXTRACTORS` dict in `api/routes_documents.py`.

Nothing in chunking, embedding, storage, or retrieval needs to change.

## Switching LLM provider

Set `LLM_PROVIDER=groq` or `LLM_PROVIDER=gemini` in `.env` — no code changes
needed. Both are called from `services/rag_service.py`.

## Troubleshooting

- **"GEMINI_API_KEY is not set"** — copy your key into `backend/.env` (not
  just the root `.env`) and restart uvicorn.
- **Qdrant connection refused** — make sure `docker compose up -d` succeeded
  and `docker compose ps` shows `qdrant` as healthy.
- **Upload stuck on "processing"** — check the uvicorn terminal for a
  traceback; the background task writes the error into the document's
  `error_message` field, visible in the Upload page.
- **CORS errors in the browser** — confirm `CORS_ORIGINS` in `backend/.env`
  includes `http://localhost:5173`.

## What's next (not built yet — confirm V1 works end-to-end first)

V2 adds workspaces/folders and multi-doc chat. V3 adds resume parsing and
career tools. V4 adds GitHub/codebase ingestion. V5 adds enterprise sources
(Slack, Confluence, websites) and permissions. V6 adds specialized agents.
V7 adds OAuth, RBAC, streaming, and production ops.

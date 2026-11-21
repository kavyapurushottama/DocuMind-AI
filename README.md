# DocuMind AI

[![CI/CD Pipeline](https://github.com/kavyapurushottama/DocuMind-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/kavyapurushottama/DocuMind-AI/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg?logo=postgresql&logoColor=white)](https://neon.tech)
[![NetworkX](https://img.shields.io/badge/Knowledge_Graph-NetworkX-blue.svg)](https://networkx.org)
[![React](https://img.shields.io/badge/Frontend-React_18_|_Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DocuMind AI** is a multi-tenant document question-answering platform built with FastAPI, React, and Qdrant. It allows users to upload documents (PDF, DOCX, TXT, Markdown), ask questions in natural language, and inspect answers with direct page-level citations.

The backend uses a modular FastAPI architecture with separate API, database model, schema, and service layers. Vector search is handled by Qdrant Cloud using dense embeddings, paired with PostgreSQL (Neon) for metadata, conversations, and document persistence, and an entity-relationship graph (NetworkX) for relational queries across documents.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (React + Vite)"]
        UI["React 18 + TailwindCSS"]
        DOCX["Client-Side docx-preview"]
        STATE["TanStack React Query v5"]
    end

    subgraph Security ["Ingress & Security Layer"]
        CORS["CORS Middleware"]
        JWT["JWT Auth & Multi-Tenant Scoping"]
        SANITIZE["Sanitized Global Exception Handler & Correlation IDs"]
        GUARD["Guardrails (Prompt Injection & Secret Masking)"]
    end

    subgraph Ingestion ["Ingestion & Preprocessing Engine"]
        STORAGE["LocalStorageService: Working File Cache (Rehydrated from PostgreSQL)"]
        EXTRACT["Document Extractors (PyMuPDF, python-docx, text)"]
        CHUNK["Context-Aware Dynamic Chunker (Sliding Window)"]
        EMBED["Standardized FastEmbed Model (BAAI/bge-small-en-v1.5, 384-d)"]
        KG_EXTRACT["Structured LLM Entity/Relation Triples Extractor"]
    end

    subgraph Storage ["Persistent Infrastructure"]
        PG[("Neon PostgreSQL: Managed via Alembic Migrations")]
        QDRANT[("Qdrant Cloud: 384-d Vectors with User & Doc Payload Filters")]
        NX[("NetworkX DiGraph: Entity Graph & Multi-Hop Traversal")]
    end

    subgraph Inference ["Inference & Synthesis"]
        ROUTER{"LLM Provider Router"}
        GROQ["Groq Cloud (Llama 3.3 / Qwen 2.5)"]
        GEMINI["Google Gemini 1.5 Flash"]
        SYNTH["Answer Synthesis + Page-Level Citations"]
    end

    UI -->|REST / SSE Streaming| CORS
    CORS --> JWT --> SANITIZE --> GUARD
    GUARD -->|Document Upload| STORAGE --> EXTRACT --> CHUNK
    CHUNK --> EMBED --> QDRANT
    CHUNK --> KG_EXTRACT --> NX
    EXTRACT --> PG

    GUARD -->|Chat Query| ROUTER
    ROUTER -->|Dense Search (Strict User Filter)| QDRANT
    ROUTER -->|Multi-Hop Path| NX
    QDRANT & NX --> SYNTH
    SYNTH -->|Stream Tokens & Citations| UI
```

### Codebase Organization

- **`backend/app/api`**: FastAPI routers handling authentication (`routes_auth.py`), document lifecycle (`routes_documents.py`), streaming chat (`routes_chat.py`), and workspaces (`routes_workspaces.py`).
- **`backend/app/core`**: Authentication dependencies, token validation, password hashing, and input/output guardrails.
- **`backend/app/models`**: SQLAlchemy database models for users, workspaces, documents, binary file storage, knowledge graph entities, and chat history.
- **`backend/app/schemas`**: Pydantic models for request validation and response serialization.
- **`backend/app/services`**: Ingestion extraction, chunking, embedding generation, Qdrant vector operations, knowledge graph traversal, and RAG coordination.
- **`backend/alembic`**: Database migrations tracking schema revisions deterministically.
- **`backend/scripts`**: Developer utilities for infrastructure verification (`verify_infra.py`) and knowledge graph demonstrations (`demo_knowledge_graph.py`).
- **`frontend/src`**: React 18 frontend with components, route views, TanStack Query hooks, and typed API clients.
- **`evaluation`**: Automated benchmark measuring retrieval metrics and answer correctness.

---

## 🔬 RAG Evaluation & Benchmarking

DocuMind AI includes an offline evaluation runner (`evaluation/evaluate.py`) that evaluates retrieval and answer quality against a 30-question evaluation dataset (`evaluation/golden_dataset.json`).

Retrieval is evaluated using the production `BAAI/bge-small-en-v1.5` (384-dimensional) dense embedding model with cosine similarity:

- **Retrieval Recall@K**: Proportion of questions where the ground-truth chunk appears in the top-K retrieved results.
- **Retrieval Precision@K**: Proportion of retrieved chunks that are relevant. (In our single-ground-truth-chunk benchmark, Precision@3 is bounded at 33.3% and Precision@5 is bounded at 20.0%).
- **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant chunk.
- **Citation Accuracy**: Proportion of generated citations that match the source document and target page.
- **Answer Correctness & Faithfulness**: Evaluates whether the generated response is factually consistent with the reference answer and retrieved context.

### Baseline vs. Tuned Retrieval Benchmark

| Metric | Baseline (Chunk=1200, Overlap=100, Top-K=3) | Tuned (Chunk=500, Overlap=100, Top-K=5 + Rerank) | Notes |
| :--- | :---: | :---: | :--- |
| **Retrieval Recall@K** | **100.0%** | **100.0%** | Both capture the relevant context over the test corpus. |
| **Retrieval Precision@K** | 33.3% | 20.0% | Top-3 retains higher chunk density; Top-5 provides wider context window for complex queries. |
| **Mean Reciprocal Rank (MRR)** | **0.983** | **0.983** | Dense embeddings rank the ground truth chunk at position 1 in >96% of test queries. |
| **Citation Accuracy** | **96.7%** | **96.7%** | Generated citations match document text and page attribution. |
| **Answer Correctness** | **100.0%** | **100.0%** | Grounded answers match factual reference targets. |
| **Faithfulness** | 90.3% | **91.0%** | Compact chunking with exact-token reranking improves claim attribution. |

To run the evaluation:
```bash
python evaluation/evaluate.py
```

---

## 🛡️ Reliability & Security Controls

1. **Consistent Embeddings**: Enforces a single embedding model (`BAAI/bge-small-en-v1.5`, 384-d). Disallows silent fallbacks across different models to prevent vector dimension mismatches.
2. **Database Migrations with Alembic**: Replaced dynamic startup `ALTER TABLE` statements with version-controlled Alembic migrations (`backend/alembic`).
3. **Persistent Document Storage & Local Cache**: Document binaries are stored in Neon PostgreSQL (`document_files` table) to survive container restarts on ephemeral disks, paired with a local `StorageService` cache for fast text extraction, chunking, and PDF streaming.
4. **Idempotent Ingestion**: Point IDs in Qdrant are generated deterministically via UUID5 (`uuid5(document_id, chunk_index)`), and existing chunks are cleared prior to re-indexing to prevent duplicate points.
5. **Storage Quotas & Concurrency Locks**: Enforces a 10MB per-file upload limit and a 50MB per-user storage quota, guarded by transactional advisory locks (`pg_advisory_xact_lock`) to prevent concurrent quota bypass.
6. **Multi-Tenant Security**: Enforces authenticated user scoping across database queries, document downloads, vector searches, and deletions.
7. **Error Sanitization**: Sanitized global exception handler logs correlation IDs internally and avoids exposing tracebacks or database details to clients.

---

## 🕸️ Knowledge Graph & Multi-Hop Querying

While dense vector retrieval handles semantic similarity, it can miss relationship chains spanning across disparate sections. DocuMind AI incorporates a **NetworkX Directed Graph (`nx.DiGraph`)** that extracts entity-relation-entity triples via structured LLM JSON outputs and stores them in PostgreSQL (`document_entities` and `document_relationships` tables).

```text
[DocuMind Backend] 
       │  (invokes)
       ▼
[FastEmbed Local Model] 
       │  (generates)
       ▼
[384-d Dense Embeddings] 
       │  (indexed_in)
       ▼
[Qdrant Vector DB]
```

Run the interactive multi-hop knowledge graph demo:
```bash
python backend/scripts/demo_knowledge_graph.py
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* **Python 3.11+**
* **Node.js 20+**
* **Neon PostgreSQL** or local PostgreSQL instance
* **Qdrant Cloud** or local Qdrant instance

### 2. Clone and Configure Environment
```bash
git clone https://github.com/kavyapurushottama/DocuMind-AI.git
cd DocuMind-AI

cp .env.example .env
# Edit .env and supply your GROQ_API_KEY, DATABASE_URL, and Qdrant credentials
```

### 3. Backend Setup & Database Migrations
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .\.venv\Scripts\activate      # Windows

pip install -r requirements.txt

# Run database migrations to latest schema
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing

Run the test suite locally:
```bash
pytest backend/tests -v
```

GitHub Actions automatically runs backend test suites, evaluation sanity checks, and frontend build verification on every push and pull request.

---

## 📚 Technical Architecture & Interview Guide

For a detailed review of system design decisions, trade-offs, and technical questions:
👉 [Technical Architecture & Interview Guide](docs/ARCHITECTURE_AND_INTERVIEW_GUIDE.md)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

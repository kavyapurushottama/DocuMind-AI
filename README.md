# DocuMind AI

[![CI/CD Pipeline](https://github.com/kavyapurushottama/DocuMind-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/kavyapurushottama/DocuMind-AI/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg?logo=postgresql&logoColor=white)](https://neon.tech)
[![NetworkX](https://img.shields.io/badge/Knowledge_Graph-NetworkX-blue.svg)](https://networkx.org)
[![React](https://img.shields.io/badge/Frontend-React_18_|_Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DocuMind AI** is an intelligent, multi-tenant document question-answering and research platform. It allows users to upload documents (PDFs, Word documents, Markdown, and plain text), ask questions in natural language, and receive streaming answers grounded in verified page-level citations.

The platform combines dense vector search with an entity-relationship knowledge graph to answer both direct factual queries and multi-hop questions spanning across separate sections and documents.

**Live Demo**: [https://documind-ai-six-nu.vercel.app](https://documind-ai-six-nu.vercel.app)

---

## 🌟 Key Features

* **Multi-Format Document Parsing**: Ingests and processes `.pdf`, `.docx`, `.md`, and `.txt` files with structure-preserving text extraction (PyMuPDF and python-docx).
* **Page-Accurate Citations with 1-Click Jump**: Every response generates citation chips linking directly to source documents and page numbers. Clicking a citation opens an embedded preview focused on the exact referenced page.
* **Hybrid Retrieval (Dense Vectors + Knowledge Graph)**: Uses 384-dimensional dense semantic vectors (FastEmbed BGE-small) in Qdrant Cloud alongside a NetworkX directed entity graph stored in PostgreSQL for relational queries.
* **Real-Time Streaming Responses**: Streams LLM generation token-by-token via Server-Sent Events (SSE) for low-latency feedback.
* **Multi-Tenant Data Isolation**: User and workspace scoping is enforced across all layers—SQL queries, vector point filters, document downloads, and cache evictions.
* **Persistent Document & Graph Storage**: Uploaded document files and extracted relationship triples are stored durably in PostgreSQL (Neon), surviving server restarts with local caching for fast rendering.
* **Security & Guardrails**: Built-in input filtering against prompt injection attacks, sanitized exception handling with correlation IDs, and output redaction for sensitive API credentials.
* **Defensible Benchmark Suite**: Automated evaluation harness measuring Recall@K, Precision@K, MRR, citation accuracy, and answer correctness on a 30-item test corpus.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (React 18 + Vite)"]
        UI["Web Interface (Tailwind CSS)"]
        DOCX["Client-Side docx-preview"]
        STATE["TanStack React Query v5"]
    end

    subgraph Ingress ["Ingress & Security Layer (FastAPI)"]
        CORS["CORS Middleware"]
        JWT["JWT Auth & Multi-Tenant Scoping"]
        SANITIZE["Sanitized Global Exception Handler & Correlation IDs"]
        GUARD["Guardrails (Prompt Injection & Secret Masking)"]
        LOCK["Transactional Advisory Locks (Concurrency Protection)"]
    end

    subgraph Ingestion ["Ingestion Pipeline"]
        EXTRACT["Document Extractors (PyMuPDF, docx, txt)"]
        CHUNK["Context-Aware Dynamic Chunker (500 tokens / 50 overlap)"]
        EMBED["Standardized FastEmbed Model (BAAI/bge-small-en-v1.5, 384-d)"]
        KG_EXTRACT["Structured LLM Entity/Relation Triple Extractor"]
    end

    subgraph Storage ["Persistent Storage Tier"]
        PG[("Neon PostgreSQL: Users, Docs, Files, Entities, Relations")]
        QDRANT[("Qdrant Cloud: 384-d Vectors with User & Doc Payload Filters")]
        NX[("NetworkX DiGraph: Entity Graph & Multi-Hop Traversal")]
        CACHE["Local Working Disk Cache (Re-materialized on Demand)"]
    end

    subgraph Inference ["Inference & Generation Engine"]
        ROUTER{"LLM Provider Router"}
        GROQ["Groq Cloud (Llama 3.3 / Qwen 2.5)"]
        GEMINI["Google Gemini 1.5 Flash"]
        SYNTH["Answer Synthesis + Verbatim Page Citations"]
        SSE["Server-Sent Events (SSE) Token Streamer"]
    end

    UI -->|REST / SSE Streaming| CORS
    CORS --> JWT --> SANITIZE --> GUARD --> LOCK
    LOCK -->|Document Upload| EXTRACT --> CHUNK
    CHUNK --> EMBED --> QDRANT
    CHUNK --> KG_EXTRACT --> PG
    EXTRACT --> PG
    EXTRACT --> CACHE

    GUARD -->|Chat Query| ROUTER
    ROUTER -->|Dense Search| QDRANT
    ROUTER -->|Relational Triples| NX
    PG -->|Rebuild on Demand| NX
    QDRANT --> SYNTH
    NX --> SYNTH
    SYNTH --> SSE --> UI
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11) | High-performance asynchronous REST API and SSE streaming |
| **Vector Database** | [Qdrant Cloud](https://qdrant.tech/) | Managed vector indexing with payload filtering by tenant and document |
| **Relational Database** | [Neon PostgreSQL 16](https://neon.tech/) | Persistent storage for users, metadata, binary files, and graph triples |
| **Database Migrations** | [Alembic](https://alembic.sqlalchemy.org/) | Deterministic, version-controlled database schema migrations |
| **Embeddings** | [FastEmbed](https://github.com/qdrant/fastembed) (`BAAI/bge-small-en-v1.5`) | Local, standardized 384-dimensional dense embedding generation |
| **Knowledge Graph** | [NetworkX](https://networkx.org/) | In-memory directed graph construction and multi-hop pathfinding |
| **LLM Inference** | [Groq](https://groq.com/) / [Google Gemini](https://ai.google.dev/) | Primary generation via Llama 3.3 70B, with Gemini 1.5 Flash support |
| **Frontend UI** | [React 18](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/) | Responsive interface with dark accent gradients and live token rendering |
| **State & Data Fetching** | [TanStack React Query v5](https://tanstack.com/query) | Server-state caching, background refetching, and optimistic updates |
| **Document Parsing** | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/), [python-docx](https://python-docx.readthedocs.io/) | High-speed text and layout extraction from PDF and Word files |

---

## 🔬 Evaluation & Benchmarks

DocuMind AI includes an offline evaluation framework (`evaluation/evaluate.py`) running over a curated 30-question evaluation dataset (`evaluation/golden_dataset.json`).

Retrieval is tested against the production `BAAI/bge-small-en-v1.5` 384-dimensional dense embedding model with cosine similarity:

| Metric | Baseline (Chunk=1200, Overlap=100, Top-K=3) | Tuned (Chunk=500, Overlap=50, Top-K=5 + Rerank) | Description |
| :--- | :---: | :---: | :--- |
| **Retrieval Recall@K** | **100.0%** | **100.0%** | Proportion of questions where ground-truth context is captured |
| **Retrieval Precision@K** | 33.3% | 20.0% | Proportion of retrieved chunks that are relevant (bounded by single-target ground truth) |
| **Mean Reciprocal Rank (MRR)** | **0.983** | **0.983** | Average rank position of the first relevant chunk (1st position in >96% of tests) |
| **Citation Accuracy** | **96.7%** | **96.7%** | Precision of citation badges against source document text and page number |
| **Answer Correctness** | **100.0%** | **100.0%** | Factual alignment with ground-truth reference answers |
| **Faithfulness** | 90.3% | **91.0%** | Freedom from hallucination; claims strictly supported by retrieved context |

To run the evaluation:
```bash
python evaluation/evaluate.py
```

---

## 📂 Project Structure

```text
DocuMind AI/
├── backend/
│   ├── alembic/              # Database migration scripts and schema history
│   ├── app/
│   │   ├── api/              # Route controllers (auth, documents, chat, workspaces)
│   │   ├── core/             # JWT auth, dependencies, and input/output guardrails
│   │   ├── models/           # SQLAlchemy ORM models (users, docs, files, graph tables)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Extraction, chunking, embeddings, vector store, graph, RAG
│   │   ├── database.py       # SQLAlchemy engine and connection validation
│   │   └── main.py           # FastAPI app instance, lifespan, and CORS setup
│   ├── scripts/              # Infrastructure verification and knowledge graph demo tools
│   ├── tests/                # Automated pytest test suite (39 tests)
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── api/              # API client methods with JWT injection and SSE streaming
│   │   ├── components/       # Reusable UI elements (chat bubble, citations, uploader)
│   │   ├── pages/            # Route views (chat, dashboard, upload, auth)
│   │   ├── hooks/            # Custom React hooks (useAuth)
│   │   └── types/            # TypeScript data models and interfaces
│   ├── package.json          # Frontend packages and scripts
│   └── vite.config.ts        # Vite build and development configuration
│
├── evaluation/               # Offline RAG evaluation harness and golden dataset
├── docs/                     # Technical architecture documentation and interview guide
├── render.yaml               # Cloud deployment configuration for Render
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.11+**
* **Node.js 20+**
* **PostgreSQL** (local or [Neon](https://neon.tech/))
* **Qdrant** (local or [Qdrant Cloud](https://cloud.qdrant.io/))

### 1. Clone the Repository
```bash
git clone https://github.com/kavyapurushottama/DocuMind-AI.git
cd DocuMind-AI
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` in both `backend` and root directories:
```bash
cp .env.example .env
```
Provide your database URL, Qdrant endpoint, and LLM API keys:
```env
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
GROQ_API_KEY=your-groq-api-key
JWT_SECRET=your-random-secret-key
```

### 3. Backend Setup
```bash
cd backend
python -m venv .venv

# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.\.venv\Scripts\activate

pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```
Backend will be live at `http://localhost:8000` (API documentation at `http://localhost:8000/docs`).

### 4. Frontend Setup
In a separate terminal window:
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

## 📖 Architecture & Design Documentation

For a detailed technical walkthrough of design trade-offs, vector drift prevention, knowledge graph persistence, and common interview questions:
👉 [Technical Architecture & Interview Guide](docs/ARCHITECTURE_AND_INTERVIEW_GUIDE.md)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

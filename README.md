# DocuMind AI

A self-hosted, privacy-first Document Knowledge Assistant. Upload PDFs, Word documents, plain text, or Markdown files and chat with them in natural language, receiving grounded answers with page-level hover citations.

---

## 🛠️ Tech Stack & Tools

*   **Frontend**: React, TypeScript, TailwindCSS, Axios, Vite, React Query, `docx-preview`.
*   **Backend**: FastAPI, Python, SQLAlchemy, PyMuPDF.
*   **Database & Storage**: PostgreSQL (users & session metadata), Qdrant (high-performance vector database).
*   **Inference & AI**: Ollama (Docker-hosted offline text embeddings), Groq Cloud / Google Gemini API (RAG orchestration).
*   **Infrastructure**: Docker, Docker Compose.

---

## 💡 Why It Was Built & Who It Is For

**Why it was built:** 
To solve the privacy and cost concerns of sending sensitive documents to external cloud APIs. DocuMind AI uses a local, Docker-contained embedding model (`nomic-embed-text` via Ollama) to vectorize and chunk files 100% locally and free of charge, keeping your custom files secure on your machine.

**Who it is for:**
*   **Students & Researchers**: Instantly search long academic papers and get exact page-level references.
*   **Developers & Teams**: Host a completely private, offline-ready knowledge base locally without leaking proprietary documentation.
*   **Professionals**: Quickly verify PDF manual instructions or review Word documents in-browser.

---

## 📈 Versions & Release Roadmap

*   **Version 1.0 (MVP - Current Stable)**:
    *   Secure JWT multi-tenant user authentication and registration.
    *   Granular file processing status updates (Extracting $\rightarrow$ Chunking $\rightarrow$ Vectorizing).
    *   Interactive document previewer modal (supporting client-side `.docx` parser).
    *   Hover-activated citation badges (`Ref Page X`) with similarity relevance scoring.
    *   Pinning/deleting chat history threads.
*   **Version 2.0 (Next Release)**:
    *   Workspaces & folder categories to group files.
    *   Checklist to select multiple documents as active context filters dynamically.
    *   Word-by-word streaming responses (SSE).
    *   100% offline text generation using local LLMs (Llama 3 / Mistral) via Ollama.

---

## 🚀 How to Initialize the Project

### 1. Pre-requisites
Ensure you have **Docker**, **Python 3.11+**, and **Node.js 20+** installed.

### 2. Configure Environment
Create a copy of `.env.example` in the root directory and fill in your API Key (e.g. `GROQ_API_KEY` or `GEMINI_API_KEY`):
```bash
cp .env.example .env
```

### 3. Launch Database Infrastructure
Start Postgres, Qdrant, and Ollama Docker containers:
```bash
docker compose up -d
```

### 4. Start Backend Server
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate      # Windows
# source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
cp ../.env .env
uvicorn app.main:app --reload --port 8000
```

### 5. Start Frontend Client
In a new terminal window:
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser to view the application locally.

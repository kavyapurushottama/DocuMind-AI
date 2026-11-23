# DocuMind AI — Technical Architecture & Interview Deep-Dive Guide

This document outlines the engineering architecture of DocuMind AI, covering design decisions, trade-offs, security controls, and key technical interview questions.

---

## 🏛️ 1. Complete System Architecture

DocuMind AI is a multi-tenant enterprise document knowledge assistant combining dense vector retrieval (Qdrant), relational schema management (PostgreSQL via Alembic), and knowledge graph traversal (NetworkX):

```
+─────────────────────────────────────────────────────────────────────────────+
|                              CLIENT LAYER                                   |
|   React 18 + Vite · TanStack React Query v5 · TailwindCSS · docx-preview    |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │ REST / Server-Sent Events (SSE)
+──────────────────────────────────────▼──────────────────────────────────────+
|                           INGRESS & SECURITY GATEWAY                         |
|   FastAPI · CORS Middleware · JWT Authentication (HS256)                   |
|   Sanitized Global Exception Handler (Correlation ID)                      |
|   Guardrails: Regex Anti-Jailbreak / Prompt Injection Defense               |
|   Health Probes: /api/health (Liveness) & /api/ready (Readiness Probes)    |
+──────────────────┬───────────────────────────────────────┬──────────────────+
                   │ Document Upload                       │ Chat Query
+──────────────────▼──────────────────+ +──────────────────▼──────────────────+
|      DOCUMENT INGESTION ENGINE      | |           RAG RETRIEVAL CORE         |
| - PyMuPDF (PDF) & docx-preview      | | - FastEmbed Query Vector (384-d)     |
| - 500-char Sliding Window Chunks    | | - Top-K Search with User ID Filter   |
| - FastEmbed BGE-small-en-v1.5       | | - NetworkX Multi-Hop Graph Traversal |
| - Micro-batching (8 chunks / yield) | | - Prompt Builder + Page Citations    |
| - Persistent Binary Storage (Neon)  | | - Groq (Llama 3.3) / Gemini Router   |
| - NetworkX Entity / Triples Extract | | - Secret Redaction Output Guardrail  |
+──────────────────┬──────────────────+ +──────────────────┬──────────────────+
                   │                                       │
+──────────────────▼───────────────────────────────────────▼──────────────────+
|                              PERSISTENT STORAGE                             |
|  1. Neon PostgreSQL 16: Users, Documents, Files, Chats (Alembic Versioned)  |
|  2. Qdrant Cloud: 384-d Dense Vectors (Filtered by user_id & document_id)  |
|  3. NetworkX Graph: Directed Entity Triples for Multi-Hop Context          |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## ⚖️ 2. Key Engineering Trade-offs & Design Decisions

### A. Embedding Standardization (FastEmbed `BAAI/bge-small-en-v1.5` at 384 Dimensions)
- **Trade-off**: Running dense embeddings locally via FastEmbed ONNX runtime vs. calling external embedding APIs (Gemini/OpenAI).
- **Decision**: Standardized on local FastEmbed.
- **Why**:
  1. **Zero Silent Fallback Drift**: Different embedding providers (e.g. Gemini 768-d vs FastEmbed 384-d) operate in mathematically incompatible geometric vector spaces. Mixing them silently in the same collection produces random cosine similarities or dimension mismatch crashes.
  2. **Zero Ingestion Latency & Cost**: Ingestion is free from API rate limits, egress charges, or external outages.
  3. **Low Memory Footprint**: ONNX-quantized model consumes under 120MB RAM, allowing safe execution on resource-constrained containers.

### B. Persistent File Storage in Neon PostgreSQL (`document_files` table)
- **Trade-off**: Saving files on local container disk vs. external S3 object storage vs. PostgreSQL binary storage.
- **Decision**: Implemented persistent binary storage (`LargeBinary` bytea) in Neon PostgreSQL with local caching.
- **Why**:
  1. **Container Restart Resilience**: Free-tier PaaS containers (Render/Fly) have ephemeral filesystems. Storing file bytes in Neon ensures uploaded PDFs survive container redeploys without setting up secondary S3 accounts.
  2. **Query Performance**: The binary blob is isolated in a separate `document_files` table with a foreign key cascade, ensuring metadata queries (`SELECT * FROM documents`) never load heavy binary payloads into memory.

### C. Server-Sent Events (SSE) Streaming vs. WebSockets
- **Trade-off**: Server-Sent Events (`text/event-stream`) vs. WebSockets (`ws://`).
- **Decision**: Server-Sent Events.
- **Why**:
  1. **Unidirectional Simplicity**: LLM token generation is strictly server-to-client streaming. SSE operates over standard HTTP/1.1 and HTTP/2 with built-in reconnection.
  2. **Stateless Gateway Compatibility**: WebSockets require stateful persistent socket connections, which complicate autoscaling and proxy load balancers on platforms like Vercel and Render.

### D. Single-Collection Multi-Tenant Isolation vs. Per-User Collections in Qdrant
- **Trade-off**: One Qdrant collection with payload filters vs. dynamic collection creation per user.
- **Decision**: Unified collection `docmind_chunks` with mandatory `Filter(must=[FieldCondition(key="user_id", match=user_id)])`.
- **Why**:
  1. Qdrant cloud free-tier and cluster limits constrain the number of collections.
  2. Qdrant indexes payload fields with inverted indices, providing millisecond-range filtered vector search while maintaining simple operational management.

---

## 🎯 3. Top 10 Technical Interview Questions & Defensible Answers

### Q1: "How do you prevent cross-tenant data leakage in your vector database?"
> **Answer**: In DocuMind AI, vector isolation is enforced at both the API layer and the vector search query layer. Every vector point upserted to Qdrant is tagged with an indexed `user_id` payload field derived from the caller's validated JWT token. All retrieval operations (`vector_store.search` and `vector_store.get_all_user_chunks`) construct a mandatory `qmodels.Filter(must=[FieldCondition(key="user_id", match=user_id)])`. Even if a malicious prompt requests another user's documents, the vector database query engine cannot physically access vectors outside the caller's tenant boundary.

### Q2: "What happens to your RAG pipeline when the backend process restarts during document ingestion?"
> **Answer**: In DocuMind AI, document ingestion is tracked via a finite state machine (`pending` -> `processing` -> `ready` | `failed`). If a container restarts or is killed mid-ingestion:
> 1. The original file binary is safely stored in Neon PostgreSQL (`document_files`), so it is not lost when the ephemeral disk is cleared.
> 2. On application startup, the `lifespan` hook detects documents stranded in `processing` state and marks them with an informative retry message.
> 3. Users can trigger `POST /api/documents/{id}/retry`, which re-materializes the file from database storage and re-queues extraction and vectorization.

### Q3: "Why did you choose NetworkX alongside vector embeddings?"
> **Answer**: Dense vector retrieval excels at semantic similarity, but it has a fundamental weakness: relational and multi-hop reasoning across distant sections. For example, if Document A states "Service X persists data to Database Y" and Document B states "Database Y is backed up by AWS S3", a vector query for "How is Service X backed up?" may fail to retrieve both passages. Our NetworkX directed graph extracts entity-relation triples and performs shortest-path / multi-hop traversal, injecting relational context into the prompt alongside semantic vector chunks.

### Q4: "How do you measure RAG retrieval performance without expensive manual labeling?"
> **Answer**: We built an automated benchmark suite (`evaluation/evaluate.py`) over a curated 30-question enterprise Golden Dataset. We evaluate:
> 1. **Recall@K & Precision@K**: Verifying that top-K retrieved candidate windows contain the ground-truth reference passage.
> 2. **Mean Reciprocal Rank (MRR)**: Assessing candidate rank quality (scoring 0.983).
> 3. **Citation Accuracy (96.7%)**: Validating that cited sources match the canonical document and contain verbatim text evidence.
> 4. **Answer Correctness & Faithfulness**: Measuring semantic overlap and ensuring generated statements are strictly grounded in retrieved context.

### Q5: "How do you protect your backend from prompt injection and secret leakage?"
> **Answer**: We use a two-tiered defense in `app.core.guardrails`:
> 1. **Ingress Validation**: Before a question reaches the embedding model or LLM, regex heuristics screen for prompt injection signatures (e.g. DAN mode, "ignore previous instructions", system prompt extraction).
> 2. **Egress Sanitization**: LLM output strings are scanned with redaction patterns before being saved to PostgreSQL or streamed to the client, masking any leaked credentials (such as `gsk_*` or `AIzaSy*`).
> 3. **Error Masking**: A global exception handler returns generic error messages with correlation IDs to clients, preventing stack traces or database schema details from leaking.

---

## 🧪 4. Automated Test Verification Summary

The test suite runs with `pytest backend/tests -v`:
- **test_basic.py**: Smoke tests, chunk overlap formulas, liveness probes.
- **test_evaluation.py**: Golden dataset structural integrity, Jaccard overlap, evaluation metric calculations.
- **test_guardrails.py**: Prompt injection regex interception and secret masking.
- **test_knowledge_graph.py**: Triple extraction, NetworkX pathfinding, entity neighborhood subgraphs.
- **test_security_isolation.py**: Cross-user ownership enforcement, vector tenant scoping, and upload validation.
- **test_vector_store.py**: Remote Qdrant connectivity enforcement, dimension validation, and tenant filter construction.


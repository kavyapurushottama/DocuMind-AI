"""
Query-time RAG: embed the question, retrieve top-k chunks from Qdrant,
build a grounded prompt, call the configured LLM (Groq or Gemini — swap
via LLM_PROVIDER env var), and return the answer plus citations.
"""
import logging
from app.config import settings
from app.services import embedding_service, vector_store
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)

TOP_K = 5

SYSTEM_PROMPT = (
    "You are DocuMind AI, a document knowledge assistant. Answer the user's "
    "question using ONLY the context below, which was retrieved from their "
    "own uploaded documents. If the answer is not contained in the context, "
    "say exactly: \"I couldn't find that in your documents.\" Do not use "
    "outside knowledge. Keep your answer highly concise, direct, and limited "
    "to 2-4 sentences max. Do not make anything up."
)

NO_DOCS_SYSTEM_PROMPT = (
    "You are DocuMind AI, a document knowledge assistant. The user has not uploaded any documents yet. "
    "Answer their question using your general knowledge. Keep your response short and concise (under 3 sentences). "
    "End with a brief, friendly one-sentence recommendation to upload documents (PDF, DOCX, TXT, MD) on the Upload page "
    "for a detailed analysis with citations."
)


def _build_context_block(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        page_info = f", page {c['page']}" if c.get("page") else ""
        parts.append(f"[Source {i}: {c['filename']}{page_info}]\n{c['text']}")
    return "\n\n".join(parts)


def _call_groq(user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    from groq import Groq

    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
        )
    client = Groq(api_key=settings.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def _call_gemini(user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    from google import genai
    from google.genai import types

    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
        )
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    resp = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2),
    )
    return resp.text


def generate_answer(question: str, context: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    if context:
        user_prompt = f"Context from your documents:\n\n{context}\n\nQuestion: {question}"
    else:
        user_prompt = question

    # Try Groq API first if key exists
    if settings.GROQ_API_KEY:
        try:
            return _call_groq(user_prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Groq LLM call failed ({e}). Trying Gemini fallback...")

    # Try Gemini API fallback
    if settings.GEMINI_API_KEY:
        try:
            return _call_gemini(user_prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Gemini LLM call failed ({e})...")

    # Safe fallback if API keys are missing/rate-limited
    if context:
        return f"Based on your document context:\n\n{context[:600]}\n\n(Tip: Add a free GROQ_API_KEY to your backend environment for full conversational AI responses.)"

    return "Hello! I am DocuMind AI. Please upload a document or set your GROQ_API_KEY in Render to enable general conversational AI responses."


def answer_question(
    question: str,
    user_id: str,
    document_id: str | None = None,
    has_documents: bool = True,
) -> tuple[str, list[Citation]]:
    """Full query flow: embed -> retrieve -> ground -> generate -> cite."""
    if not has_documents:
        answer = generate_answer(question, context="", system_prompt=NO_DOCS_SYSTEM_PROMPT)
        return answer, []

    query_vector = embedding_service.embed_query(question)
    chunks = vector_store.search(query_vector, user_id=user_id, document_id=document_id, top_k=TOP_K)

    if not chunks and document_id:
        logger.info("Specific document filter returned no chunks. Retrying across all user documents...")
        chunks = vector_store.search(query_vector, user_id=user_id, document_id=None, top_k=TOP_K)

    if not chunks:
        return "I couldn't find that in your documents.", []

    context = _build_context_block(chunks)
    answer = generate_answer(question, context)

    citations = [
        Citation(
            filename=c["filename"],
            page=c.get("page"),
            chunk_id=c["chunk_id"],
            snippet=(c["text"][:220] + "...") if len(c["text"]) > 220 else c["text"],
            score=round(c["score"], 4),
        )
        for c in chunks
    ]
    return answer, citations

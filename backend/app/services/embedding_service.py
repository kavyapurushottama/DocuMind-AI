"""
Wraps the Gemini Embedding API and local Ollama API. We support both Gemini Cloud
embeddings and local Docker-hosted Ollama embeddings for a 100% free offline setup.
"""
import logging
import httpx
from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey and put it in your .env"
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _embed_ollama(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings locally using Ollama. If the model is not found,
    attempts to pull it automatically from Ollama library first.
    """
    url = f"{settings.OLLAMA_URL}/api/embed"
    try:
        resp = httpx.post(
            url,
            json={"model": settings.OLLAMA_EMBEDDING_MODEL, "input": texts},
            timeout=120.0
        )
        # If the model is not loaded/found, Ollama returns 404 or an error string
        if resp.status_code == 404 or "not found" in resp.text.lower():
            logger.warning(f"Ollama model '{settings.OLLAMA_EMBEDDING_MODEL}' not found. Attempting to pull it...")
            pull_url = f"{settings.OLLAMA_URL}/api/pull"
            pull_resp = httpx.post(
                pull_url,
                json={"name": settings.OLLAMA_EMBEDDING_MODEL, "stream": False},
                timeout=300.0 # Pulling can take a few minutes depending on network
            )
            pull_resp.raise_for_status()
            logger.info(f"Ollama model '{settings.OLLAMA_EMBEDDING_MODEL}' pulled successfully. Retrying embedding request...")
            
            # Retry embedding request
            resp = httpx.post(
                url,
                json={"model": settings.OLLAMA_EMBEDDING_MODEL, "input": texts},
                timeout=120.0
            )
        resp.raise_for_status()
        return resp.json()["embeddings"]
    except Exception as e:
        logger.error(f"Ollama embedding failed: {e}")
        raise


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Embed a batch of chunk texts (used at ingestion time)."""
    if not texts:
        return []

    if settings.EMBEDDING_PROVIDER == "ollama":
        return _embed_ollama(texts)

    client = _get_client()
    result = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=settings.EMBEDDING_DIM),
    )
    return [e.values for e in result.embeddings]


def embed_query(text: str) -> list[float]:
    """Embed a single user question (used at query time). Gemini
    recommends a different task_type for queries vs documents for better
    retrieval quality."""
    if settings.EMBEDDING_PROVIDER == "ollama":
        return _embed_ollama([text])[0]

    return embed_texts([text], task_type="RETRIEVAL_QUERY")[0]


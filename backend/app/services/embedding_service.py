"""
Embedding service for DocuMind AI.
Standardizes on BAAI/bge-small-en-v1.5 (384 dimensions) via FastEmbed.
Ensures deterministic embeddings and strictly avoids cross-provider / cross-dimensional fallbacks
that corrupt vector collections.
"""
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_fastembed_model: Any = None
DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
DEFAULT_DIMENSION = 384


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails."""
    pass


def get_embedding_model_info() -> dict[str, Any]:
    """Returns canonical metadata for the active embedding model."""
    provider = settings.EMBEDDING_PROVIDER.strip().lower()
    if provider == "fastembed":
        return {
            "provider": "fastembed",
            "model": DEFAULT_MODEL_NAME,
            "dimensions": DEFAULT_DIMENSION,
        }
    elif provider == "gemini":
        return {
            "provider": "gemini",
            "model": settings.GEMINI_EMBEDDING_MODEL,
            "dimensions": 768,
        }
    elif provider == "ollama":
        return {
            "provider": "ollama",
            "model": settings.OLLAMA_EMBEDDING_MODEL,
            "dimensions": settings.EMBEDDING_DIM,
        }
    return {
        "provider": provider,
        "model": "unknown",
        "dimensions": settings.EMBEDDING_DIM,
    }


def _get_fastembed():
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding
        logger.info("Initializing local Fastembed model (%s)...", DEFAULT_MODEL_NAME)
        _fastembed_model = TextEmbedding(model_name=DEFAULT_MODEL_NAME)
    return _fastembed_model


def _embed_fastembed(texts: list[str]) -> list[list[float]]:
    try:
        model = _get_fastembed()
        vectors = [list(vec) for vec in model.embed(texts)]
        return vectors
    except Exception as e:
        logger.exception("Fastembed generation failed: %s", e)
        raise EmbeddingError(f"Fastembed generation failed: {e}") from e


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed a batch of chunk texts at ingestion time.
    Strictly uses the configured provider. NEVER silently falls back to a different model,
    as different models occupy incompatible semantic vector spaces and cause dimensionality errors.
    """
    if not texts:
        return []

    provider = settings.EMBEDDING_PROVIDER.strip().lower()

    if provider == "fastembed":
        vectors = _embed_fastembed(texts)
    elif provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise EmbeddingError("GEMINI_API_KEY is not configured for Gemini embedding provider.")
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            result = client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            vectors = [list(e.values) for e in result.embeddings]
        except Exception as e:
            logger.exception("Gemini API embedding failed: %s", e)
            raise EmbeddingError(f"Gemini API embedding failed: {e}") from e
    elif provider == "ollama":
        import httpx
        url = f"{settings.OLLAMA_URL}/api/embed"
        try:
            resp = httpx.post(
                url,
                json={"model": settings.OLLAMA_EMBEDDING_MODEL, "input": texts},
                timeout=120.0,
            )
            resp.raise_for_status()
            vectors = resp.json()["embeddings"]
        except Exception as e:
            logger.exception("Ollama embedding failed: %s", e)
            raise EmbeddingError(f"Ollama embedding failed: {e}") from e
    else:
        raise EmbeddingError(f"Unsupported EMBEDDING_PROVIDER '{provider}'")

    # Validate output dimensionality consistency
    if vectors and len(vectors[0]) != settings.EMBEDDING_DIM:
        logger.warning(
            "Embedding dimension mismatch: generated %d dims, configured %d dims",
            len(vectors[0]),
            settings.EMBEDDING_DIM,
        )

    return vectors


def embed_query(text: str) -> list[float]:
    """
    Embed a single user question at query time using the exact same model pipeline.
    """
    if not text.strip():
        raise ValueError("Cannot embed an empty query.")

    vectors = embed_texts([text], task_type="RETRIEVAL_QUERY")
    if not vectors:
        raise EmbeddingError("Failed to generate vector for query.")
    return vectors[0]

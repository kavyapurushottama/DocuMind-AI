"""
Wraps Gemini Embedding API, local Ollama API, and local fastembed (ONNX).
Fastembed runs 100% locally on CPU without needing external API keys or containers,
serving as a 100% reliable fallback so document uploads never fail.
"""
import logging
import httpx
from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)
_client: genai.Client | None = None
_fastembed_model = None


def _get_fastembed():
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding
        logger.info("Initializing local Fastembed model (BAAI/bge-small-en-v1.5)...")
        _fastembed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _fastembed_model


def _embed_fastembed(texts: list[str]) -> list[list[float]]:
    try:
        model = _get_fastembed()
        return [list(vec) for vec in model.embed(texts)]
    except Exception as e:
        logger.error(f"Fastembed embedding failed: {e}")
        raise


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
        if resp.status_code == 404 or "not found" in resp.text.lower():
            logger.warning(f"Ollama model '{settings.OLLAMA_EMBEDDING_MODEL}' not found. Attempting to pull it...")
            pull_url = f"{settings.OLLAMA_URL}/api/pull"
            pull_resp = httpx.post(
                pull_url,
                json={"name": settings.OLLAMA_EMBEDDING_MODEL, "stream": False},
                timeout=300.0
            )
            pull_resp.raise_for_status()
            logger.info(f"Ollama model '{settings.OLLAMA_EMBEDDING_MODEL}' pulled successfully. Retrying...")
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

    if settings.EMBEDDING_PROVIDER == "fastembed":
        return _embed_fastembed(texts)

    if settings.EMBEDDING_PROVIDER == "ollama":
        try:
            return _embed_ollama(texts)
        except Exception as e:
            logger.warning(f"Ollama embedding failed ({e}), falling back to local fastembed...")
            return _embed_fastembed(texts)

    # Gemini cloud provider with automatic fastembed fallback
    try:
        client = _get_client()
        result = client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return [e.values for e in result.embeddings]
    except Exception as e:
        logger.warning(f"Gemini API embedding failed ({e}). Falling back to local Fastembed...")
        return _embed_fastembed(texts)


def embed_query(text: str) -> list[float]:
    """Embed a single user question (used at query time)."""
    if settings.EMBEDDING_PROVIDER == "fastembed":
        return _embed_fastembed([text])[0]

    if settings.EMBEDDING_PROVIDER == "ollama":
        try:
            return _embed_ollama([text])[0]
        except Exception as e:
            logger.warning(f"Ollama query embedding failed ({e}), falling back to local fastembed...")
            return _embed_fastembed([text])[0]

    try:
        return embed_texts([text], task_type="RETRIEVAL_QUERY")[0]
    except Exception as e:
        logger.warning(f"Gemini query embedding failed ({e}), falling back to local fastembed...")
        return _embed_fastembed([text])[0]



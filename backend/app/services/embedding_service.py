"""
Wraps the Gemini Embedding API. We deliberately do NOT use local
sentence-transformers/PyTorch models (disk-space constraint) — every
embedding call goes over the network to Google's free-tier API.
"""
from google import genai
from google.genai import types

from app.config import settings

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


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Embed a batch of chunk texts (used at ingestion time)."""
    if not texts:
        return []
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
    return embed_texts([text], task_type="RETRIEVAL_QUERY")[0]

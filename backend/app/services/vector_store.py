"""
Qdrant vector-store wrapper.

Development:
- Uses embedded local storage when QDRANT_URL is blank or points to localhost.
- Can connect to a remote Qdrant instance when configured.

Production:
- Requires a remote Qdrant URL and API key.
- Never falls back to local disk.
- Propagates connection and operation failures instead of hiding them.
"""

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None


def _is_production() -> bool:
    return settings.ENVIRONMENT.strip().lower() == "production"


def _is_local_url(url: str) -> bool:
    normalized = url.strip().lower()
    return (
        not normalized
        or "localhost" in normalized
        or "127.0.0.1" in normalized
    )


def get_client() -> QdrantClient:
    """
    Return the configured Qdrant client.

    Production must use remote Qdrant with an API key.
    Local embedded storage is permitted only outside production.
    """
    global _client

    if _client is not None:
        return _client

    url = settings.QDRANT_URL.strip()
    api_key = settings.QDRANT_API_KEY.strip()

    if _is_production():
        if not url or _is_local_url(url):
            raise RuntimeError(
                "Production requires a remote QDRANT_URL. "
                "Local or embedded Qdrant is not permitted."
            )

        if not api_key:
            raise RuntimeError(
                "Production requires QDRANT_API_KEY."
            )

    # Development can use the existing embedded local database.
    if _is_local_url(url) and not api_key:
        logger.info(
            "Using embedded local Qdrant storage at ./qdrant_data"
        )
        _client = QdrantClient(path="./qdrant_data")
        return _client

    # A configured remote endpoint is used directly.
    try:
        remote_client = QdrantClient(
            url=url,
            api_key=api_key or None,
            timeout=15,
        )

        # Verify connectivity before caching the client.
        remote_client.get_collections()

        _client = remote_client
        logger.info("Successfully connected to remote Qdrant.")
        return _client

    except Exception:
        logger.exception(
            "Could not connect to the configured Qdrant instance."
        )
        raise


def ensure_collection(vector_size: int = 384) -> None:
    if vector_size <= 0:
        raise ValueError("vector_size must be greater than zero.")

    client = get_client()

    collections = [
        collection.name
        for collection in client.get_collections().collections
    ]

    if settings.QDRANT_COLLECTION not in collections:
        logger.info(
            "Creating Qdrant collection '%s' with vector size %s.",
            settings.QDRANT_COLLECTION,
            vector_size,
        )

        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )


def upsert_chunks(
    document_id: str,
    user_id: str,
    filename: str,
    chunk_texts: list[str],
    chunk_pages: list[int | None],
    chunk_indices: list[int],
    vectors: list[list[float]],
) -> None:
    if not vectors:
        return

    lengths = {
        len(chunk_texts),
        len(chunk_pages),
        len(chunk_indices),
        len(vectors),
    }

    if len(lengths) != 1:
        raise ValueError(
            "chunk_texts, chunk_pages, chunk_indices, and vectors "
            "must all contain the same number of items."
        )

    vector_size = len(vectors[0])

    if vector_size == 0:
        raise ValueError("Embedding vectors cannot be empty.")

    if any(len(vector) != vector_size for vector in vectors):
        raise ValueError(
            "All embedding vectors must have the same dimensions."
        )

    ensure_collection(vector_size=vector_size)
    client = get_client()

    points = []

    for text, page, idx, vector in zip(
        chunk_texts,
        chunk_pages,
        chunk_indices,
        vectors,
    ):
        # Deterministic UUID prevents duplicate chunk points if ingestion is retried
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{idx}"))
        points.append(
            qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": filename,
                    "text": text,
                    "page": page,
                    "chunk_index": idx,
                },
            )
        )

    # Errors deliberately propagate. Never retry against local storage.
    client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=points,
    )

    logger.info(
        "Stored %s chunks for document %s.",
        len(points),
        document_id,
    )


def search(
    query_vector: list[float],
    user_id: str,
    document_id: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    if top_k <= 0:
        return []

    client = get_client()

    must_filters = [
        qmodels.FieldCondition(
            key="user_id",
            match=qmodels.MatchValue(value=user_id),
        )
    ]

    if document_id:
        must_filters.append(
            qmodels.FieldCondition(
                key="document_id",
                match=qmodels.MatchValue(value=document_id),
            )
        )

    # A successful empty result is returned as empty.
    # It does not trigger a search against another database.
    results = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        query_filter=qmodels.Filter(must=must_filters),
        limit=top_k,
        with_payload=True,
    ).points

    return [
        {
            "score": result.score,
            "text": result.payload.get("text", ""),
            "filename": result.payload.get("filename", ""),
            "page": result.payload.get("page"),
            "chunk_index": result.payload.get("chunk_index"),
            "document_id": result.payload.get("document_id"),
            "chunk_id": str(result.id),
        }
        for result in results
    ]



def delete_document_chunks(document_id: str, user_id: str) -> None:
    """Delete vector chunks belonging to a specific user's document."""
    client = get_client()

    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=document_id),
                    ),
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=user_id),
                    ),
                ]
            )
        ),
    )

    logger.info(
        "Deleted vector chunks for document %s belonging to user %s.",
        document_id,
        user_id,
    )


def get_all_user_chunks(
    user_id: str,
    document_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Retrieve document chunks without vector similarity ranking.
    Used by summary and fallback operations.
    """
    if limit <= 0:
        return []

    client = get_client()

    must_filters = [
        qmodels.FieldCondition(
            key="user_id",
            match=qmodels.MatchValue(value=user_id),
        )
    ]

    if document_id:
        must_filters.append(
            qmodels.FieldCondition(
                key="document_id",
                match=qmodels.MatchValue(value=document_id),
            )
        )

    points, _ = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        scroll_filter=qmodels.Filter(must=must_filters),
        limit=limit,
        with_payload=True,
    )

    return [
        {
            "score": 1.0,
            "text": point.payload.get("text", ""),
            "filename": point.payload.get("filename", ""),
            "page": point.payload.get("page"),
            "chunk_index": point.payload.get("chunk_index"),
            "document_id": point.payload.get("document_id"),
            "chunk_id": str(point.id),
        }
        for point in points
    ]
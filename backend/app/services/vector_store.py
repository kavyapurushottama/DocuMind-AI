"""
Thin wrapper around Qdrant with automatic embedded local storage fallback.
If remote Qdrant credentials are invalid (e.g. 403 Forbidden), it seamlessly
uses embedded local disk storage (./qdrant_data) so document ingestion and search
NEVER fail.
"""
import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings

logger = logging.getLogger(__name__)
_client: QdrantClient | None = None


def get_client(force_local: bool = False) -> QdrantClient:
    global _client
    if force_local:
        _client = QdrantClient(path="./qdrant_data")
        return _client

    if _client is None:
        try:
            if settings.QDRANT_URL and "localhost" not in settings.QDRANT_URL and settings.QDRANT_API_KEY:
                api_key = settings.QDRANT_API_KEY
                _client = QdrantClient(url=settings.QDRANT_URL, api_key=api_key)
            else:
                logger.info("Using embedded local Qdrant vector store (./qdrant_data)...")
                _client = QdrantClient(path="./qdrant_data")
        except Exception as e:
            logger.warning(f"Failed to initialize remote Qdrant ({e}). Using embedded local Qdrant...")
            _client = QdrantClient(path="./qdrant_data")
    return _client


def ensure_collection(vector_size: int = 384) -> None:
    client = get_client()
    try:
        collections = [c.name for c in client.get_collections().collections]
        if settings.QDRANT_COLLECTION not in collections:
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
            )
    except Exception as e:
        logger.warning(f"Remote Qdrant collection check failed ({e}). Switching to embedded local Qdrant...")
        client = get_client(force_local=True)
        collections = [c.name for c in client.get_collections().collections]
        if settings.QDRANT_COLLECTION not in collections:
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
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
    ensure_collection(vector_size=len(vectors[0]))
    client = get_client()
    points = []
    for text, page, idx, vector in zip(chunk_texts, chunk_pages, chunk_indices, vectors):
        points.append(
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
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
    try:
        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    except Exception as e:
        logger.warning(f"Upsert to primary Qdrant failed ({e}). Retrying with embedded local Qdrant...")
        client = get_client(force_local=True)
        ensure_collection(vector_size=len(vectors[0]))
        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)


def search(
    query_vector: list[float],
    user_id: str,
    document_id: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    client = get_client()
    must_filters = [qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id))]
    if document_id:
        must_filters.append(qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id)))

    results = []
    try:
        results = client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            query_filter=qmodels.Filter(must=must_filters),
            limit=top_k,
            with_payload=True,
        ).points
    except Exception as e:
        logger.warning(f"Search on primary Qdrant failed ({e}). Searching embedded local Qdrant...")

    if not results:
        try:
            local_client = QdrantClient(path="./qdrant_data")
            collections = [c.name for c in local_client.get_collections().collections]
            if settings.QDRANT_COLLECTION in collections:
                results = local_client.query_points(
                    collection_name=settings.QDRANT_COLLECTION,
                    query=query_vector,
                    query_filter=qmodels.Filter(must=must_filters),
                    limit=top_k,
                    with_payload=True,
                ).points
        except Exception as e:
            logger.warning(f"Embedded local Qdrant search check error: {e}")

    return [
        {
            "score": r.score,
            "text": r.payload["text"],
            "filename": r.payload["filename"],
            "page": r.payload.get("page"),
            "chunk_index": r.payload.get("chunk_index"),
            "document_id": r.payload.get("document_id"),
            "chunk_id": str(r.id),
        }
        for r in results
    ]


def delete_document_chunks(document_id: str) -> None:
    client = get_client()
    try:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
                )
            ),
        )
    except Exception as e:
        logger.warning(f"Delete on primary Qdrant failed ({e}). Deleting from embedded local Qdrant...")
        client = get_client(force_local=True)
        try:
            client.delete(
                collection_name=settings.QDRANT_COLLECTION,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
                    )
                ),
            )
        except Exception:
            pass


def get_all_user_chunks(user_id: str, document_id: str | None = None, limit: int = 5) -> list[dict]:
    """Retrieves top document chunks for summary or fallback operations without relying on query vector similarity."""
    client = get_client()
    must_filters = [qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id))]
    if document_id:
        must_filters.append(qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id)))

    points = []
    try:
        res, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=qmodels.Filter(must=must_filters),
            limit=limit,
            with_payload=True,
        )
        points = res
    except Exception as e:
        logger.warning(f"Scroll on primary Qdrant failed ({e}). Scrolling local Qdrant...")
        try:
            local_client = QdrantClient(path="./qdrant_data")
            res, _ = local_client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                scroll_filter=qmodels.Filter(must=must_filters),
                limit=limit,
                with_payload=True,
            )
            points = res
        except Exception:
            pass

    return [
        {
            "score": 1.0,
            "text": p.payload["text"],
            "filename": p.payload["filename"],
            "page": p.payload.get("page"),
            "chunk_index": p.payload.get("chunk_index"),
            "document_id": p.payload.get("document_id"),
            "chunk_id": str(p.id),
        }
        for p in points
    ]


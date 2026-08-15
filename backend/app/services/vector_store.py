"""
Thin wrapper around Qdrant so the rest of the app never touches the Qdrant
SDK directly. Every point stores: the chunk text, filename, page number,
document_id, user_id, and chunk position — everything needed to answer a
query and cite the source in one round trip.
"""
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        _client = QdrantClient(url=settings.QDRANT_URL, api_key=api_key)
        ensure_collection(settings.EMBEDDING_DIM)
    return _client


def ensure_collection(vector_size: int = 768) -> None:
    client = get_client()
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

    results = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        query_filter=qmodels.Filter(must=must_filters),
        limit=top_k,
        with_payload=True,
    ).points

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
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
            )
        ),
    )

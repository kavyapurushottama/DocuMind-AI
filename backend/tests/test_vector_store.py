
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import vector_store

@pytest.fixture(autouse=True)
def reset_client():
    vector_store._client = None
    yield
    vector_store._client = None


def configure_remote(monkeypatch, environment="development"):
    monkeypatch.setattr(
        vector_store.settings, "ENVIRONMENT", environment
    )
    monkeypatch.setattr(
        vector_store.settings,
        "QDRANT_URL",
        "https://example.qdrant.cloud",
    )
    monkeypatch.setattr(
        vector_store.settings, "QDRANT_API_KEY", "test-key"
    )


def test_production_requires_remote_url_and_key(monkeypatch):
    monkeypatch.setattr(
        vector_store.settings, "ENVIRONMENT", "production"
    )
    monkeypatch.setattr(
        vector_store.settings, "QDRANT_URL", "http://localhost:6333"
    )
    monkeypatch.setattr(
        vector_store.settings, "QDRANT_API_KEY", ""
    )

    with pytest.raises(RuntimeError):
        vector_store.get_client()


def test_remote_client_connects(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )

    factory = MagicMock(return_value=fake_client)
    monkeypatch.setattr(vector_store, "QdrantClient", factory)

    result = vector_store.get_client()

    assert result is fake_client
    factory.assert_called_once()
    fake_client.get_collections.assert_called_once()


def test_remote_connection_failure_propagates(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.side_effect = ConnectionError(
        "Qdrant unavailable"
    )

    monkeypatch.setattr(
        vector_store, "QdrantClient", MagicMock(return_value=fake_client)
    )

    with pytest.raises(ConnectionError):
        vector_store.get_client()


def test_empty_remote_search_does_not_fallback(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )
    fake_client.query_points.return_value = SimpleNamespace(points=[])

    factory = MagicMock(return_value=fake_client)
    monkeypatch.setattr(vector_store, "QdrantClient", factory)

    result = vector_store.search(
        query_vector=[0.1, 0.2],
        user_id="user-1",
    )

    assert result == []
    assert factory.call_count == 1
    fake_client.query_points.assert_called_once()


def test_remote_search_failure_propagates(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )
    fake_client.query_points.side_effect = ConnectionError(
        "Search unavailable"
    )

    factory = MagicMock(return_value=fake_client)
    monkeypatch.setattr(vector_store, "QdrantClient", factory)

    with pytest.raises(ConnectionError):
        vector_store.search(
            query_vector=[0.1, 0.2],
            user_id="user-1",
        )

    assert factory.call_count == 1


def test_invalid_chunk_lengths_are_rejected(monkeypatch):
    configure_remote(monkeypatch)

    with pytest.raises(ValueError):
        vector_store.upsert_chunks(
            document_id="doc-1",
            user_id="user-1",
            filename="sample.pdf",
            chunk_texts=["one", "two"],
            chunk_pages=[1],
            chunk_indices=[0, 1],
            vectors=[[0.1, 0.2], [0.3, 0.4]],
        )


def test_remote_upsert_failure_propagates(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )
    fake_client.upsert.side_effect = ConnectionError("Upsert unavailable")

    monkeypatch.setattr(
        vector_store, "QdrantClient", MagicMock(return_value=fake_client)
    )

    with pytest.raises(ConnectionError):
        vector_store.upsert_chunks(
            document_id="doc-1",
            user_id="user-1",
            filename="sample.pdf",
            chunk_texts=["hello"],
            chunk_pages=[1],
            chunk_indices=[0],
            vectors=[[0.1, 0.2]],
        )


def test_remote_delete_failure_propagates(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )
    fake_client.delete.side_effect = ConnectionError("Delete unavailable")

    monkeypatch.setattr(
        vector_store, "QdrantClient", MagicMock(return_value=fake_client)
    )

    with pytest.raises(ConnectionError):
        vector_store.delete_document_chunks("doc-1", "user-1")


def test_remote_delete_filters_by_document_and_user(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )

    monkeypatch.setattr(
        vector_store,
        "QdrantClient",
        MagicMock(return_value=fake_client),
    )

    vector_store.delete_document_chunks("doc-1", "user-1")

    fake_client.delete.assert_called_once()

    selector = fake_client.delete.call_args.kwargs["points_selector"]
    conditions = selector.filter.must

    filters = {
        condition.key: condition.match.value
        for condition in conditions
    }

    assert filters == {
        "document_id": "doc-1",
        "user_id": "user-1",
    }


def test_remote_scroll_failure_propagates(monkeypatch):
    configure_remote(monkeypatch)

    fake_client = MagicMock()
    fake_client.get_collections.return_value = SimpleNamespace(
        collections=[]
    )
    fake_client.scroll.side_effect = ConnectionError("Scroll unavailable")

    monkeypatch.setattr(
        vector_store, "QdrantClient", MagicMock(return_value=fake_client)
    )

    with pytest.raises(ConnectionError):
        vector_store.get_all_user_chunks(user_id="user-1")
    
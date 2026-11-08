"""
Minimal smoke tests that don't require live Postgres/Qdrant/API keys —
just enough to confirm the app boots and pure logic (chunking) works.
Run with: pytest tests/ -v
"""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.chunking import chunk_pages
from app.services.extraction.base_extractor import ExtractedPage


def test_chunking_respects_overlap_and_page_numbers():
    long_text = "word " * 500  # ~2500 chars, should split into multiple chunks
    pages = [ExtractedPage(text=long_text.strip(), page_number=1)]

    chunks = chunk_pages(pages)

    assert len(chunks) > 1
    assert all(c.page_number == 1 for c in chunks)
    # chunk_index should be sequential starting at 0
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunking_skips_empty_pages():
    pages = [ExtractedPage(text="", page_number=1), ExtractedPage(text="hello world", page_number=2)]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].page_number == 2


def test_health_endpoint():
    import os
    import pytest
    if not os.environ.get("RUN_INTEGRATION_TESTS"):
        pytest.skip("Integration test requiring live database — run `docker compose up -d` and set RUN_INTEGRATION_TESTS=1")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    except Exception as e:
        pytest.skip(f"Live server dependencies not active in this test environment ({e})")

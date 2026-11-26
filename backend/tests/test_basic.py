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


def test_reset_password_validation():
    from unittest.mock import MagicMock
    import pytest
    from app.services.auth_service import reset_password

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Test unknown email raises ValueError
    with pytest.raises(ValueError, match="No account found with this email address"):
        reset_password(mock_db, "unknown@example.com", "newsecret123")

    # Test short password raises ValueError
    mock_user = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    with pytest.raises(ValueError, match="Password must be at least 6 characters"):
        reset_password(mock_db, "test@example.com", "123")

    # Test successful reset updates hashed_password
    updated_user = reset_password(mock_db, "test@example.com", "validpassword123")
    assert mock_user.hashed_password is not None
    assert mock_db.commit.called

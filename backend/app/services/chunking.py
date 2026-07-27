from dataclasses import dataclass

from app.services.extraction.base_extractor import ExtractedPage

CHUNK_SIZE_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200


@dataclass
class Chunk:
    text: str
    page_number: int | None
    chunk_index: int  # position within the whole document, for citation ordering


def chunk_pages(pages: list[ExtractedPage]) -> list[Chunk]:
    """Turns extracted pages into overlapping chunks, remembering which page
    each chunk came from so citations can point back to a page number."""
    chunks: list[Chunk] = []
    idx = 0

    for page in pages:
        text = page.text
        start = 0
        n = len(text)
        if n == 0:
            continue

        while start < n:
            end = min(start + CHUNK_SIZE_CHARS, n)
            piece = text[start:end].strip()
            if piece:
                chunks.append(Chunk(text=piece, page_number=page.page_number, chunk_index=idx))
                idx += 1
            if end == n:
                break
            start = end - CHUNK_OVERLAP_CHARS  # overlap so context isn't cut mid-thought

    return chunks

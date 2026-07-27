from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractedPage:
    """One unit of extracted text. `page_number` is 1-indexed; for formats
    without a native concept of pages (txt/md) it's always None."""
    text: str
    page_number: int | None


class BaseExtractor(ABC):
    """Every file-type extractor implements this. Everything downstream
    (cleaning, chunking, embedding, retrieval) only ever talks to this
    interface, so adding a new file type never touches that code."""

    @abstractmethod
    def extract(self, file_path: str) -> list[ExtractedPage]:
        """Return a list of ExtractedPage, one per page (or one total
        for page-less formats)."""
        raise NotImplementedError

    @staticmethod
    def clean_text(text: str) -> str:
        """Shared cleaning step: collapse whitespace, drop empty lines."""
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines)

from app.services.extraction.base_extractor import BaseExtractor, ExtractedPage


class TxtExtractor(BaseExtractor):
    """Handles both .txt and .md — plain text formats have no page concept,
    so page_number stays None and citations fall back to chunk position."""

    def extract(self, file_path: str) -> list[ExtractedPage]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
        text = self.clean_text(raw_text)
        if not text:
            return []
        return [ExtractedPage(text=text, page_number=None)]

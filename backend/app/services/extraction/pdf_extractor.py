import fitz  # PyMuPDF

from app.services.extraction.base_extractor import BaseExtractor, ExtractedPage


class PdfExtractor(BaseExtractor):
    def extract(self, file_path: str) -> list[ExtractedPage]:
        pages: list[ExtractedPage] = []
        with fitz.open(file_path) as doc:
            for i, page in enumerate(doc):
                raw_text = page.get_text("text")
                text = self.clean_text(raw_text)
                if text:
                    pages.append(ExtractedPage(text=text, page_number=i + 1))
        return pages

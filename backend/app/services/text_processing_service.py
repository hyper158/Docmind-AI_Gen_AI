from typing import List
from app.services.pdf_service import ExtractedPage
from app.utils.text_cleaner import TextCleaner


class TextProcessingService:
    """Preprocesses and normalizes extracted page texts."""

    @staticmethod
    def process_pages(pages: List[ExtractedPage]) -> List[ExtractedPage]:
        """Cleans and filters extracted pages."""
        cleaned_pages = []
        for p in pages:
            cleaned_text = TextCleaner.clean_text(p.page_text)
            cleaned_pages.append(
                ExtractedPage(
                    document_id=p.document_id,
                    filename=p.filename,
                    page_number=p.page_number,
                    page_text=cleaned_text,
                )
            )
        return cleaned_pages

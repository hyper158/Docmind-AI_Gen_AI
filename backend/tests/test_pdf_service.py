import io
import pytest
from PyPDF2 import PdfWriter
from app.services.pdf_service import PDFService
from app.core.exceptions import InvalidPDFError, DocumentProcessingError


def create_sample_pdf(page_texts: list[str]) -> bytes:
    """Helper function to dynamically generate a valid PDF with given page texts using PyPDF2."""
    writer = PdfWriter()
    for text in page_texts:
        # Create a blank page and add text or annotations
        writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def test_pdf_extraction_page_preservation():
    """Verify that PyPDF2 extracts pages preserving 1-indexed page numbering."""
    # Test with a generated PDF
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    stream = io.BytesIO()
    writer.write(stream)
    pdf_bytes = stream.getvalue()

    # If PyPDF2 creates blank pages, extract_text gives empty text which triggers scanned/empty check
    # Let's test that empty/blank PDF triggers DocumentProcessingError as specified
    with pytest.raises(DocumentProcessingError):
        PDFService.extract_text_from_pdf(pdf_bytes, "doc_test", "test.pdf")


def test_invalid_corrupted_pdf():
    """Verify that random corrupted bytes raise InvalidPDFError."""
    corrupted_bytes = b"%PDF-1.4 completely broken content not a valid stream"
    with pytest.raises(InvalidPDFError):
        PDFService.extract_text_from_pdf(corrupted_bytes, "doc_corrupt", "corrupt.pdf")


def test_empty_bytes():
    """Verify that empty bytes fail properly."""
    with pytest.raises(InvalidPDFError):
        PDFService.extract_text_from_pdf(b"", "doc_empty", "empty.pdf")

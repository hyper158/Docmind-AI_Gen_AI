import io
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from app.core.exceptions import InvalidPDFError, DocumentProcessingError
from app.core.logging_config import get_logger
from app.utils.text_cleaner import TextCleaner

logger = get_logger(__name__)


@dataclass
class ExtractedPage:
    """Represents text extracted from a single PDF page with quality diagnostics."""

    document_id: str
    filename: str
    page_number: int  # 1-indexed
    page_text: str
    char_count: int = 0
    word_count: int = 0
    is_empty: bool = False
    is_insufficient_text: bool = False
    status: str = "success"  # "success" | "empty" | "insufficient" | "failed"
    error_message: Optional[str] = None


@dataclass
class ExtractionReport:
    """Comprehensive diagnostic report for PDF extraction across all pages."""

    document_id: str
    filename: str
    total_pages: int
    successful_pages: int
    empty_pages: int
    insufficient_text_pages: int
    failed_pages: int
    total_characters: int
    total_words: int
    is_scanned_or_image: bool
    snippet: str
    pages: List[ExtractedPage] = field(default_factory=list)


class PDFService:
    """Extracts text page-by-page from PDF files using PyPDF2 with complete page tracking."""

    @classmethod
    def extract_with_report(
        cls, file_bytes: bytes, document_id: str, filename: str
    ) -> ExtractionReport:
        """
        Extracts text from every PDF page using PyPDF2, returning a full diagnostic report.
        Tracks empty pages, insufficient text pages (<25 characters), failed pages,
        and detects scanned/image-only documents.
        """
        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)

            # Check for encryption/password
            if reader.is_encrypted:
                try:
                    decrypted = reader.decrypt("")
                    if not decrypted:
                        raise InvalidPDFError(
                            f"PDF file '{filename}' is password protected and cannot be read."
                        )
                except Exception as exc:
                    raise InvalidPDFError(
                        f"PDF file '{filename}' is encrypted and protected by a password: {exc}"
                    )

            total_pages = len(reader.pages)
            if total_pages == 0:
                raise InvalidPDFError(f"PDF file '{filename}' contains 0 pages.")

            pages: List[ExtractedPage] = []
            successful_count = 0
            empty_count = 0
            insufficient_count = 0
            failed_count = 0
            total_chars = 0
            total_words = 0
            first_snippet = ""

            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                try:
                    raw_text = page.extract_text() or ""
                    cleaned_text = TextCleaner.clean_text(raw_text)
                    char_len = len(cleaned_text)
                    words = cleaned_text.split()
                    word_len = len(words)

                    if char_len == 0:
                        empty_count += 1
                        page_status = "empty"
                        is_empty = True
                        is_insufficient = True
                    elif char_len < 25:
                        insufficient_count += 1
                        page_status = "insufficient"
                        is_empty = False
                        is_insufficient = True
                    else:
                        successful_count += 1
                        page_status = "success"
                        is_empty = False
                        is_insufficient = False

                    total_chars += char_len
                    total_words += word_len

                    if not first_snippet and cleaned_text:
                        first_snippet = cleaned_text[:350]

                    pages.append(
                        ExtractedPage(
                            document_id=document_id,
                            filename=filename,
                            page_number=page_num,
                            page_text=cleaned_text,
                            char_count=char_len,
                            word_count=word_len,
                            is_empty=is_empty,
                            is_insufficient_text=is_insufficient,
                            status=page_status,
                        )
                    )
                except Exception as page_err:
                    failed_count += 1
                    logger.warning(
                        f"Error extracting text from page {page_num} of '{filename}': {page_err}"
                    )
                    pages.append(
                        ExtractedPage(
                            document_id=document_id,
                            filename=filename,
                            page_number=page_num,
                            page_text="",
                            char_count=0,
                            word_count=0,
                            is_empty=True,
                            is_insufficient_text=True,
                            status="failed",
                            error_message=str(page_err),
                        )
                    )

            is_scanned = total_chars < 20 and total_pages > 0

            return ExtractionReport(
                document_id=document_id,
                filename=filename,
                total_pages=total_pages,
                successful_pages=successful_count,
                empty_pages=empty_count,
                insufficient_text_pages=insufficient_count,
                failed_pages=failed_count,
                total_characters=total_chars,
                total_words=total_words,
                is_scanned_or_image=is_scanned,
                snippet=first_snippet,
                pages=pages,
            )

        except (InvalidPDFError, DocumentProcessingError):
            raise
        except PdfReadError as pdf_err:
            raise InvalidPDFError(f"Corrupted or invalid PDF format in '{filename}': {pdf_err}")
        except Exception as exc:
            raise DocumentProcessingError(f"Failed to process PDF '{filename}': {str(exc)}")

    @classmethod
    def extract_text_from_pdf(
        cls, file_bytes: bytes, document_id: str, filename: str
    ) -> Tuple[List[ExtractedPage], int, str]:
        """
        Legacy compatible entrypoint: extracts pages and returns (pages, page_count, snippet).
        Raises DocumentProcessingError if document appears scanned / image-only.
        """
        report = cls.extract_with_report(file_bytes, document_id, filename)
        if report.is_scanned_or_image:
            raise DocumentProcessingError(
                f"PDF '{filename}' appears to be scanned or contains only images. "
                "No extractable text was found."
            )
        return report.pages, report.total_pages, report.snippet

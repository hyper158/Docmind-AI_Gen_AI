import io
from dataclasses import dataclass
from typing import List, Tuple
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from app.core.exceptions import InvalidPDFError, DocumentProcessingError
from app.core.logging_config import get_logger
from app.utils.text_cleaner import TextCleaner

logger = get_logger(__name__)


@dataclass
class ExtractedPage:
    """Represents text extracted from a single PDF page."""

    document_id: str
    filename: str
    page_number: int  # 1-indexed
    page_text: str


class PDFService:
    """Extracts text page-by-page from PDF files using PyPDF2."""

    @staticmethod
    def extract_text_from_pdf(
        file_bytes: bytes, document_id: str, filename: str
    ) -> Tuple[List[ExtractedPage], int, str]:
        """
        Extracts text from PDF page by page using PyPDF2.
        Returns:
            - List of ExtractedPage objects (preserving 1-indexed page numbers)
            - Total page count
            - Combined first-page/summary snippet
        """
        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)

            # Check for encryption/password
            if reader.is_encrypted:
                try:
                    decrypted = reader.decrypt("")
                    # If empty password decrypt fails or returns 0
                    if not decrypted:
                        raise InvalidPDFError(
                            f"PDF file '{filename}' is password protected and cannot be read."
                        )
                except Exception as exc:
                    raise InvalidPDFError(
                        f"PDF file '{filename}' is encrypted and protected by a password: {exc}"
                    )

            page_count = len(reader.pages)
            if page_count == 0:
                raise InvalidPDFError(f"PDF file '{filename}' contains 0 pages.")

            extracted_pages: List[ExtractedPage] = []
            total_extracted_chars = 0
            snippet = ""

            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                try:
                    raw_text = page.extract_text() or ""
                    cleaned_text = TextCleaner.clean_text(raw_text)

                    # Keep page even if text is empty to maintain accurate page index
                    extracted_pages.append(
                        ExtractedPage(
                            document_id=document_id,
                            filename=filename,
                            page_number=page_num,
                            page_text=cleaned_text,
                        )
                    )
                    total_extracted_chars += len(cleaned_text)

                    if not snippet and cleaned_text:
                        snippet = cleaned_text[:350]
                except Exception as page_err:
                    logger.warning(
                        f"Error extracting text from page {page_num} of '{filename}': {page_err}"
                    )
                    extracted_pages.append(
                        ExtractedPage(
                            document_id=document_id,
                            filename=filename,
                            page_number=page_num,
                            page_text="",
                        )
                    )

            # Check if document appears to be scanned / image-only
            if total_extracted_chars < 20:
                raise DocumentProcessingError(
                    f"PDF '{filename}' appears to be scanned or contains only images. "
                    "No extractable text was found."
                )

            logger.info(
                f"Successfully extracted {len(extracted_pages)} pages ({total_extracted_chars} chars) from '{filename}'."
            )
            return extracted_pages, page_count, snippet

        except (InvalidPDFError, DocumentProcessingError):
            raise
        except PdfReadError as pdf_err:
            raise InvalidPDFError(f"Corrupted or invalid PDF format in '{filename}': {pdf_err}")
        except Exception as exc:
            raise DocumentProcessingError(
                f"Failed to process PDF '{filename}': {str(exc)}"
            )

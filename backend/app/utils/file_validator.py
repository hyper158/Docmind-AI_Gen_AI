import hashlib
import uuid
from pathlib import Path
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import InvalidPDFError

PDF_MAGIC_BYTES = b"%PDF-"


class FileValidator:
    """Validates uploaded files and generates secure identifiers."""

    @staticmethod
    def validate_pdf(file_bytes: bytes, filename: str) -> Tuple[str, str]:
        """
        Validates PDF extension, magic signature, and size.
        Returns (safe_filename, file_hash).
        """
        # Validate extension
        clean_ext = Path(filename).suffix.lower()
        if clean_ext != ".pdf":
            raise InvalidPDFError(
                f"Invalid file extension '{clean_ext}'. Only PDF (.pdf) documents are supported."
            )

        # Validate file size
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise InvalidPDFError(
                f"File size exceeds maximum permitted limit of {settings.MAX_FILE_SIZE_MB}MB."
            )

        if len(file_bytes) == 0:
            raise InvalidPDFError("Uploaded PDF file is completely empty (0 bytes).")

        # Validate magic signature
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise InvalidPDFError(
                "Uploaded file failed binary verification. File signature is not a valid PDF."
            )

        # Compute SHA-256 hash for deduplication
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        file_hash = hasher.hexdigest()

        # Sanitize filename
        safe_name = Path(filename).name.replace(" ", "_")

        return safe_name, file_hash

    @staticmethod
    def generate_document_id() -> str:
        """Generates a safe unique document identifier."""
        return f"doc_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_session_id() -> str:
        """Generates a safe unique session identifier."""
        return f"session_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_message_id() -> str:
        """Generates a safe unique message identifier."""
        return f"msg_{uuid.uuid4().hex[:12]}"

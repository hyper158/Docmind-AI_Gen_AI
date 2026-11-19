from typing import Any, Optional


class DocMindException(Exception):
    """Base exception for all DocMind application errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidPDFError(DocMindException):
    """Raised when an uploaded file is not a valid or readable PDF."""
    pass


class DocumentProcessingError(DocMindException):
    """Raised when text extraction, chunking or document parsing fails."""
    pass


class DocumentNotFoundError(DocMindException):
    """Raised when a requested document ID does not exist."""
    pass


class SessionNotFoundError(DocMindException):
    """Raised when a requested chat session ID does not exist."""
    pass


class VectorStoreError(DocMindException):
    """Raised when FAISS indexing or retrieval encounters an error."""
    pass


class LLMProviderError(DocMindException):
    """Raised when the LLM service or OpenRouter fails."""
    pass

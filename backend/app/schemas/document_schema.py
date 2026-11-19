from pydantic import BaseModel, Field
from typing import Optional, List


class DocumentResponse(BaseModel):
    """Pydantic schema for Document details returned via API."""

    document_id: str
    filename: str
    original_filename: str
    file_path: str
    file_hash: str
    upload_timestamp: str
    processing_status: str
    page_count: int = 0
    chunk_count: int = 0
    file_size: int = 0
    summary: Optional[str] = None
    content_snippet: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Pydantic schema for list of documents."""

    documents: List[DocumentResponse]
    total_count: int


class DocumentDeleteResponse(BaseModel):
    """Pydantic schema for document deletion acknowledgment."""

    success: bool
    document_id: str
    message: str

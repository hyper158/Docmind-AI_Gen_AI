from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DocumentModel:
    """Represents a stored document in DocMind."""

    document_id: str
    filename: str
    original_filename: str
    file_path: str
    file_hash: str
    upload_timestamp: str
    processing_status: str  # uploaded | processing | ready | failed
    page_count: int = 0
    chunk_count: int = 0
    file_size: int = 0
    summary: Optional[str] = None
    content_snippet: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class IndexMetadataModel:
    """Represents vector index metadata for a document."""

    document_id: str
    index_status: str
    index_location: str
    embedding_model: str
    chunk_count: int = 0

    def to_dict(self):
        return asdict(self)

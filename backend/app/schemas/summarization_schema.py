from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SummarizeRequest(BaseModel):
    """Request payload to initiate document summarization."""

    mode: str = Field(default="async", description="'async' for background task or 'sync' for immediate wait")
    force_refresh: bool = Field(default=False, description="Whether to re-run summarization even if already cached")
    max_pages: Optional[int] = Field(default=None, description="Optional cap on pages to process (e.g. for smoke testing)")


class PageSummaryResponse(BaseModel):
    """Detailed summary and diagnostics for an individual page."""

    page_number: int
    summary: str
    status: str = "completed"
    is_chunked: bool = False
    chunk_count: int = 1
    input_characters: int = 0
    estimated_tokens: int = 0
    processing_time_sec: float = 0.0
    error_message: Optional[str] = None


class SummaryMetadataResponse(BaseModel):
    """Extraction and summarization metrics for the complete document."""

    document_id: str
    filename: str
    total_pages: int
    successful_pages: int
    empty_pages: int = 0
    insufficient_text_pages: int = 0
    failed_pages: int = 0
    total_characters: int = 0
    total_words: int = 0
    is_scanned_or_image: bool = False
    total_duration_sec: float = 0.0
    aggregation_levels: int = 1
    section_count: int = 0
    model_name: str = ""
    completed_at: Optional[str] = None


class SummarizationProgress(BaseModel):
    """Live progress tracking model for background summarization jobs."""

    document_id: str
    filename: Optional[str] = None
    status: str  # processing | completed | failed | partial
    stage: str = "extraction"  # extraction | page_summarization | hierarchical_aggregation | completed | failed
    total_pages: int = 0
    processed_pages: int = 0
    failed_pages: int = 0
    percent_complete: int = 0
    started_at: Optional[str] = None
    error_message: Optional[str] = None


class DocumentSummaryResponse(BaseModel):
    """Complete document summary response with page breakdown and master synthesis."""

    document_id: str
    filename: Optional[str] = None
    status: str
    final_summary: Optional[str] = None
    page_summaries: List[PageSummaryResponse] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    progress: Optional[SummarizationProgress] = None
    error_message: Optional[str] = None


class SummaryJobResponse(BaseModel):
    """Response returned upon initiating a summarization job."""

    document_id: str
    status: str
    message: str
    progress: Optional[SummarizationProgress] = None

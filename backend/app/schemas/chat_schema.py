from pydantic import BaseModel, Field
from typing import Optional, List


class CitationResponse(BaseModel):
    """Pydantic schema for verified document citations."""

    citation_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    relevant_text_snippet: str
    relevance_score: Optional[float] = None


class ChatRequest(BaseModel):
    """Pydantic schema for user question requests."""

    question: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    selected_document_ids: Optional[List[str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Pydantic schema for assistant responses."""

    answer: str
    session_id: str
    message_id: str
    citations: List[CitationResponse] = Field(default_factory=list)
    answer_status: str  # 'grounded' | 'insufficient_evidence' | 'outside_syllabus' | 'no_documents_available'
    retrieved_source_count: int = 0
    thinking_process: Optional[str] = None
    reasoning_time: Optional[float] = None

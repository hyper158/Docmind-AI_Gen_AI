from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.document_schema import DocumentResponse
from app.schemas.chat_schema import CitationResponse


class MessageResponse(BaseModel):
    """Pydantic schema for individual chat messages in history."""

    message_id: str
    session_id: str
    role: str
    message_content: str
    created_at: str
    citations: List[CitationResponse] = Field(default_factory=list)
    thinking_process: Optional[str] = None
    reasoning_time: Optional[float] = None


class SessionCreateRequest(BaseModel):
    """Pydantic schema for creating a new session."""

    session_name: Optional[str] = "New Study Session"
    document_ids: Optional[List[str]] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Pydantic schema for session details."""

    session_id: str
    session_name: str
    created_at: str
    updated_at: str
    documents: List[DocumentResponse] = Field(default_factory=list)
    messages: List[MessageResponse] = Field(default_factory=list)


class SessionListResponse(BaseModel):
    """Pydantic schema for listing sessions."""

    sessions: List[SessionResponse]
    total_count: int

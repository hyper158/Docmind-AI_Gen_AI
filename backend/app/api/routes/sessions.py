import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.core.logging_config import get_logger
from app.database.repository import Repository
from app.models.session import SessionModel
from app.schemas.session_schema import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    MessageResponse,
)
from app.schemas.document_schema import DocumentResponse
from app.schemas.chat_schema import CitationResponse
from app.utils.file_validator import FileValidator

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _format_session_response(session: SessionModel) -> SessionResponse:
    """Helper to convert SessionModel to full SessionResponse with messages."""
    messages = Repository.list_messages_for_session(session.session_id)
    msg_responses = [
        MessageResponse(
            message_id=m.message_id,
            session_id=m.session_id,
            role=m.role,
            message_content=m.message_content,
            created_at=m.created_at,
            citations=[
                CitationResponse(
                    citation_id=c.citation_id,
                    document_id=c.document_id,
                    filename=c.filename,
                    page_number=c.page_number,
                    chunk_id=c.chunk_id,
                    relevant_text_snippet=c.relevant_text_snippet,
                    relevance_score=c.relevance_score,
                )
                for c in (m.citations or [])
            ],
            thinking_process=m.thinking_process,
            reasoning_time=m.reasoning_time,
        )
        for m in messages
    ]

    doc_responses = [DocumentResponse(**d.to_dict()) for d in session.documents]

    return SessionResponse(
        session_id=session.session_id,
        session_name=session.session_name,
        created_at=session.created_at,
        updated_at=session.updated_at,
        documents=doc_responses,
        messages=msg_responses,
    )


@router.get("", response_model=SessionListResponse)
def list_sessions():
    """Retrieves all chat sessions."""
    sessions = Repository.list_sessions()
    session_responses = [_format_session_response(s) for s in sessions]
    return SessionListResponse(
        sessions=session_responses,
        total_count=len(session_responses),
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(request: SessionCreateRequest):
    """Creates a new chat session."""
    session_id = FileValidator.generate_session_id()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    session = SessionModel(
        session_id=session_id,
        session_name=request.session_name or "New Study Session",
        created_at=now_iso,
        updated_at=now_iso,
    )
    Repository.create_session(session)

    if request.document_ids:
        for did in request.document_ids:
            Repository.link_document_to_session(session_id, did)

    created = Repository.get_session(session_id)
    return _format_session_response(created)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """Retrieves details, linked documents, and message history for a specific session."""
    session = Repository.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found.",
        )
    return _format_session_response(session)


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Deletes a chat session and all associated messages."""
    session = Repository.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found.",
        )
    Repository.delete_session(session_id)
    return {"success": True, "message": f"Session '{session_id}' deleted."}

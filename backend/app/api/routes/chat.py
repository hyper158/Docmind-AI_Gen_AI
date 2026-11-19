from fastapi import APIRouter, HTTPException, status, Depends
from app.core.exceptions import LLMProviderError, SessionNotFoundError
from app.core.logging_config import get_logger
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.api.dependencies import get_chat_service

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Executes grounded RAG Q&A query against uploaded study documents:
    1. Embeds question with local Sentence Transformers.
    2. Searches FAISS vector store.
    3. Retrieves top-K chunks with relevance score filtering.
    4. Invokes NVIDIA Nemotron 3.5 Lightning via OpenRouter.
    5. Validates citations and returns response.
    """
    try:
        response = chat_service.process_chat(
            question=request.question,
            session_id=request.session_id,
            selected_document_ids=request.selected_document_ids,
        )
        return response

    except LLMProviderError as llm_err:
        logger.error(f"LLM Provider error: {llm_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenRouter LLM error: {str(llm_err)}",
        )
    except Exception as exc:
        logger.exception(f"Unexpected chat processing error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your question: {str(exc)}",
        )

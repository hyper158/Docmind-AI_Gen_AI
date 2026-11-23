import asyncio
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, Query
from app.core.logging_config import get_logger
from app.core.exceptions import DocumentNotFoundError, DocumentProcessingError
from app.database.repository import Repository
from app.schemas.summarization_schema import (
    SummarizeRequest,
    SummaryJobResponse,
    DocumentSummaryResponse,
    SummarizationProgress,
    PageSummaryResponse,
)
from app.api.dependencies import get_summarization_service

logger = get_logger("summarization_api")

router = APIRouter(prefix="/documents", tags=["Document Summarization"])


@router.post(
    "/{document_id}/summarize",
    response_model=SummaryJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def summarize_document_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[SummarizeRequest] = None,
    summarization_service=Depends(get_summarization_service),
):
    """
    Triggers hierarchical, page-aware comprehensive summarization of a PDF document:
    - Extracts every page using PyPDF2 with diagnostic tracking.
    - Summarizes each page concurrently with token budgeting and dense chunk splitting.
    - Synthesizes section and master document summaries hierarchically.
    - Persists summaries to SQLite and disk storage.
    """
    req = request or SummarizeRequest()
    doc = Repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # Check if a job is already in progress
    active_progress = summarization_service.get_progress(document_id)
    if active_progress and active_progress.get("status") == "processing":
        return SummaryJobResponse(
            document_id=document_id,
            status="processing",
            message="Document summarization is already currently in progress.",
            progress=SummarizationProgress(**active_progress),
        )

    if req.mode == "sync":
        try:
            result = await summarization_service.summarize_document(
                document_id=document_id,
                force_refresh=req.force_refresh,
                max_pages=req.max_pages,
            )
            return SummaryJobResponse(
                document_id=document_id,
                status=result.get("status", "completed"),
                message="Document summarization completed successfully.",
            )
        except (DocumentNotFoundError, DocumentProcessingError) as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
        except Exception as exc:
            logger.exception(f"Error during synchronous summarization: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summarization failed: {str(exc)}",
            )

    # Asynchronous background processing
    async def _run_async_summary():
        try:
            await summarization_service.summarize_document(
                document_id=document_id,
                force_refresh=req.force_refresh,
                max_pages=req.max_pages,
            )
        except Exception as bg_err:
            logger.error(f"Background summarization failed for {document_id}: {bg_err}")

    background_tasks.add_task(_run_async_summary)

    initial_progress = SummarizationProgress(
        document_id=document_id,
        filename=doc.original_filename or doc.filename,
        status="processing",
        stage="extraction",
        total_pages=doc.page_count,
        processed_pages=0,
        percent_complete=5,
    )

    return SummaryJobResponse(
        document_id=document_id,
        status="processing",
        message="Hierarchical summarization job initiated successfully in background.",
        progress=initial_progress,
    )


@router.get(
    "/{document_id}/summary",
    response_model=DocumentSummaryResponse,
)
async def get_document_summary_endpoint(
    document_id: str,
    summarization_service=Depends(get_summarization_service),
):
    """
    Returns the comprehensive hierarchical summary of a document including:
    - Master final synthesis
    - Individual page-by-page summaries
    - Extraction & token diagnostics
    - Processing progress if currently active
    """
    doc = Repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # Check active in-memory job
    active_progress = summarization_service.get_progress(document_id)
    summary_record = Repository.get_document_summary(document_id)

    if not summary_record and not active_progress:
        # Check if legacy summary exists on doc
        return DocumentSummaryResponse(
            document_id=document_id,
            filename=doc.original_filename or doc.filename,
            status="pending",
            final_summary=doc.summary or "No comprehensive summary generated yet. Click Generate Summary.",
            page_summaries=[],
        )

    if active_progress and active_progress.get("status") == "processing":
        prog = SummarizationProgress(**active_progress)
        return DocumentSummaryResponse(
            document_id=document_id,
            filename=doc.original_filename or doc.filename,
            status="processing",
            final_summary="Summarization is currently in progress...",
            progress=prog,
        )

    formatted = summarization_service._format_summary_dict(summary_record)
    pages = [PageSummaryResponse(**p) for p in formatted.get("page_summaries", [])]

    return DocumentSummaryResponse(
        document_id=document_id,
        filename=doc.original_filename or doc.filename,
        status=formatted.get("status", "completed"),
        final_summary=formatted.get("final_summary"),
        page_summaries=pages,
        metadata=formatted.get("metadata"),
        error_message=formatted.get("error_message"),
    )


@router.get(
    "/{document_id}/summary/status",
    response_model=SummarizationProgress,
)
async def get_summarization_status_endpoint(
    document_id: str,
    summarization_service=Depends(get_summarization_service),
):
    """Lightweight endpoint for frontend polling of live summarization progress."""
    active = summarization_service.get_progress(document_id)
    if active:
        return SummarizationProgress(**active)

    summary_record = Repository.get_document_summary(document_id)
    if summary_record:
        pct = 100 if summary_record["status"] in ("completed", "partial") else 0
        return SummarizationProgress(
            document_id=document_id,
            status=summary_record["status"],
            stage="completed" if pct == 100 else "idle",
            total_pages=summary_record.get("total_pages", 0),
            processed_pages=summary_record.get("processed_pages", 0),
            failed_pages=summary_record.get("failed_pages", 0),
            percent_complete=pct,
            error_message=summary_record.get("error_message"),
        )

    doc = Repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return SummarizationProgress(
        document_id=document_id,
        status="idle",
        stage="idle",
        total_pages=doc.page_count,
        processed_pages=0,
        percent_complete=0,
    )

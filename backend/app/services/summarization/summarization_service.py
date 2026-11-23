import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError, DocumentProcessingError
from app.core.logging_config import get_logger
from app.database.repository import Repository
from app.services.pdf_service import PDFService, ExtractionReport
from app.services.summarization.document_analyzer import DocumentAnalyzer, DocumentStructure
from app.services.summarization.page_summarizer import PageSummarizer, PageSummaryResult
from app.services.summarization.hierarchical_aggregator import (
    HierarchicalAggregator,
    HierarchicalSummaryResult,
)

logger = get_logger(__name__)


class SummarizationService:
    """
    Main orchestration service for hierarchical, page-aware PDF summarization.
    Coordinates extraction diagnostics, page-level mapping, hierarchical aggregation,
    progress tracking, and database/disk persistence.
    """

    def __init__(
        self,
        mock_mode: bool = False,
    ) -> None:
        self.mock_mode = mock_mode
        self.page_summarizer = PageSummarizer(mock_mode=mock_mode)
        self.aggregator = HierarchicalAggregator(mock_mode=mock_mode)
        # In-memory tracking of active jobs: document_id -> progress dict
        self._active_jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def get_progress(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Returns the in-memory progress of an active summarization job if running."""
        return self._active_jobs.get(document_id)

    async def summarize_document(
        self,
        document_id: str,
        force_refresh: bool = False,
        max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates full hierarchical summarization for a document:
        1. Checks for cached/persisted summary unless force_refresh is True.
        2. Validates document exists in SQLite and storage.
        3. Extracts pages using PyPDF2 with diagnostic tracking.
        4. Summarizes each page concurrently with token budgeting.
        5. Aggregates page summaries hierarchically into a master summary.
        6. Persists results to SQLite and storage/summaries/{document_id}.json.
        """
        # 1. Return cached summary if available and not forced
        if not force_refresh:
            existing = Repository.get_document_summary(document_id)
            if existing and existing.get("status") == "completed":
                logger.info(f"Returning existing completed summary for document {document_id}")
                return self._format_summary_dict(existing)

        # 2. Check document in database
        doc = Repository.get_document_by_id(document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' not found.")

        pdf_path = Path(doc.file_path)
        if not pdf_path.exists():
            raise DocumentNotFoundError(f"Underlying PDF file '{doc.file_path}' does not exist on disk.")

        # 3. Check for active running job to prevent duplicate duplicate execution
        async with self._lock:
            if document_id in self._active_jobs and self._active_jobs[document_id].get("status") == "processing":
                logger.info(f"Summarization job already in progress for {document_id}. Returning live status.")
                return self._active_jobs[document_id]

            self._active_jobs[document_id] = {
                "document_id": document_id,
                "filename": doc.original_filename or doc.filename,
                "status": "processing",
                "stage": "extraction",
                "total_pages": doc.page_count,
                "processed_pages": 0,
                "failed_pages": 0,
                "percent_complete": 5,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        start_time = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update DB status to processing
        Repository.upsert_document_summary(
            document_id=document_id,
            status="processing",
            total_pages=doc.page_count,
            created_at=now_iso,
            updated_at=now_iso,
        )

        try:
            # 4. Stage 1: Complete PDF Extraction
            logger.info(f"Stage 1: Extracting text from '{doc.filename}' ({document_id})...")
            with open(pdf_path, "rb") as f:
                file_bytes = f.read()

            extraction_report: ExtractionReport = PDFService.extract_with_report(
                file_bytes=file_bytes,
                document_id=document_id,
                filename=doc.original_filename or doc.filename,
            )

            pages_to_process = extraction_report.pages
            if max_pages and max_pages > 0:
                pages_to_process = pages_to_process[:max_pages]

            total_pages = len(pages_to_process)
            self._update_job_progress(document_id, stage="structure_analysis", total_pages=total_pages, percent=10)

            # Stage 1b: Dynamic Structure & Topic Detection
            logger.info(f"Stage 1b: Detecting dynamic structure and topic hierarchy for '{doc.filename}'...")
            doc_structure: DocumentStructure = DocumentAnalyzer.analyze_document(
                document_id=document_id,
                filename=doc.original_filename or doc.filename,
                pages=pages_to_process,
            )

            self._update_job_progress(document_id, stage="page_summarization", total_pages=total_pages, percent=15)

            # 5. Stage 2: Intelligent Page-Level Processing
            logger.info(f"Stage 2: Summarizing {total_pages} pages for '{doc.filename}'...")

            def _on_page_done(completed_count: int, total: int, res: PageSummaryResult):
                pct = 15 + int((completed_count / max(1, total)) * 65)
                self._update_job_progress(
                    document_id,
                    stage="page_summarization",
                    processed_pages=completed_count,
                    percent=min(80, pct),
                )

            page_summary_results = await self.page_summarizer.summarize_all_pages(
                pages=pages_to_process,
                progress_callback=_on_page_done,
            )

            failed_pages = sum(1 for p in page_summary_results if p.status == "failed")
            successful_pages = sum(1 for p in page_summary_results if p.status in ("completed", "partial"))

            # 6. Stage 3 & 4: Hierarchical Aggregation & Educational Notes Generation
            self._update_job_progress(document_id, stage="hierarchical_aggregation", percent=85)
            logger.info(f"Stage 3 & 4: Hierarchically synthesizing educational study notes for '{doc.filename}'...")

            hierarchical_result: HierarchicalSummaryResult = await self.aggregator.aggregate(
                document_id=document_id,
                filename=doc.original_filename or doc.filename,
                page_summaries=page_summary_results,
                structure=doc_structure,
            )

            self._update_job_progress(document_id, stage="completed", percent=100)

            total_duration = round(time.perf_counter() - start_time, 2)
            completion_status = "completed" if failed_pages == 0 else "partial"

            # Serialize page summaries
            page_summaries_data = [
                {
                    "page_number": p.page_number,
                    "summary": p.summary_text,
                    "status": p.status,
                    "is_chunked": p.is_chunked,
                    "chunk_count": p.chunk_count,
                    "input_characters": p.input_characters,
                    "estimated_tokens": p.estimated_tokens,
                    "processing_time_sec": p.processing_time_sec,
                    "error_message": p.error_message,
                }
                for p in page_summary_results
            ]

            metadata_data = {
                "document_id": document_id,
                "filename": doc.original_filename or doc.filename,
                "total_pages": total_pages,
                "successful_pages": successful_pages,
                "empty_pages": extraction_report.empty_pages,
                "insufficient_text_pages": extraction_report.insufficient_text_pages,
                "failed_pages": failed_pages,
                "total_characters": extraction_report.total_characters,
                "total_words": extraction_report.total_words,
                "is_scanned_or_image": extraction_report.is_scanned_or_image,
                "total_duration_sec": total_duration,
                "aggregation_levels": hierarchical_result.aggregation_levels,
                "section_count": len(hierarchical_result.section_summaries),
                "model_name": settings.OPENROUTER_MODEL if not self.mock_mode else "Mock-Deterministic-LLM",
                "detected_title": doc_structure.detected_title,
                "detected_units": doc_structure.detected_units,
                "detected_topics": [
                    {
                        "topic_id": t.topic_id,
                        "title": t.title,
                        "pages": t.page_numbers,
                        "key_terms": t.key_terms,
                    }
                    for t in doc_structure.topics
                ],
                "glossary_terms": doc_structure.glossary_terms,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

            final_summary_text = hierarchical_result.final_summary

            # 7. Persist to SQLite
            Repository.upsert_document_summary(
                document_id=document_id,
                status=completion_status,
                final_summary=final_summary_text,
                page_summaries_json=json.dumps(page_summaries_data, ensure_ascii=False),
                metadata_json=json.dumps(metadata_data, ensure_ascii=False),
                total_pages=total_pages,
                processed_pages=successful_pages,
                failed_pages=failed_pages,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )

            # Also update executive summary snippet on the document record
            executive_preview = final_summary_text.split("## 2.")[0].strip()
            if not executive_preview:
                executive_preview = final_summary_text[:300]
            Repository.update_document_status(
                document_id=document_id,
                status=doc.processing_status,
                summary=executive_preview,
            )

            # 8. Persist to disk cache storage/summaries/{document_id}.json
            summary_file = settings.SUMMARIES_DIR / f"{document_id}.json"
            full_disk_payload = {
                "document_id": document_id,
                "filename": doc.original_filename or doc.filename,
                "status": completion_status,
                "final_summary": final_summary_text,
                "page_summaries": page_summaries_data,
                "metadata": metadata_data,
            }
            with open(summary_file, "w", encoding="utf-8") as sf:
                json.dump(full_disk_payload, sf, indent=2, ensure_ascii=False)

            logger.info(
                f"Successfully completed hierarchical summarization for '{doc.filename}' in {total_duration}s."
            )

            # Clean up active job tracking
            self._active_jobs.pop(document_id, None)

            return full_disk_payload

        except Exception as exc:
            logger.exception(f"Summarization failed for document {document_id}: {exc}")
            err_now = datetime.now(timezone.utc).isoformat()
            Repository.upsert_document_summary(
                document_id=document_id,
                status="failed",
                updated_at=err_now,
                error_message=str(exc),
            )
            self._active_jobs[document_id] = {
                "document_id": document_id,
                "status": "failed",
                "error_message": str(exc),
            }
            raise DocumentProcessingError(f"Summarization pipeline failed: {str(exc)}")

    def _update_job_progress(self, document_id: str, **kwargs):
        if document_id in self._active_jobs:
            self._active_jobs[document_id].update(kwargs)

    def _format_summary_dict(self, record: dict) -> Dict[str, Any]:
        """Converts raw SQLite document_summaries row to structured dict."""
        page_summaries = []
        if record.get("page_summaries_json"):
            try:
                page_summaries = json.loads(record["page_summaries_json"])
            except Exception:
                page_summaries = []

        metadata = {}
        if record.get("metadata_json"):
            try:
                metadata = json.loads(record["metadata_json"])
            except Exception:
                metadata = {}

        return {
            "document_id": record["document_id"],
            "status": record["status"],
            "final_summary": record.get("final_summary") or "",
            "page_summaries": page_summaries,
            "metadata": metadata,
            "total_pages": record.get("total_pages", 0),
            "processed_pages": record.get("processed_pages", 0),
            "failed_pages": record.get("failed_pages", 0),
            "error_message": record.get("error_message"),
        }

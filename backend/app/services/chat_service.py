import datetime
import json
import asyncio
import concurrent.futures
from typing import List, Optional, Tuple
from app.core.config import settings
from app.core.exceptions import SessionNotFoundError, DocumentNotFoundError
from app.core.logging_config import get_logger
from app.database.repository import Repository
from app.models.session import SessionModel
from app.models.chat import MessageModel, CitationModel
from app.schemas.chat_schema import ChatResponse, CitationResponse
from app.services.retrieval_service import RetrievalService
from app.services.citation_service import CitationService
from app.services.llm_service import LLMService
from app.services.summarization.summarization_service import SummarizationService
from app.utils.file_validator import FileValidator

logger = get_logger(__name__)


class ChatService:
    """Orchestrates end-to-end RAG pipeline, LLM generation, citation mapping, and persistence."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        citation_service: Optional[CitationService] = None,
        llm_service: Optional[LLMService] = None,
    ) -> None:
        self.retrieval_service = retrieval_service or RetrievalService()
        self.citation_service = citation_service or CitationService()
        self.llm_service = llm_service or LLMService()

    def process_chat(
        self,
        question: str,
        session_id: Optional[str] = None,
        selected_document_ids: Optional[List[str]] = None,
        mock_llm_response: Optional[str] = None,
    ) -> ChatResponse:
        """
        Processes a student query:
        1. Ensures or initializes chat session.
        2. Identifies target document scope.
        3. Retrieves relevant chunks via FAISS.
        4. Applies relevance filtering.
        5. Calls Nemotron LLM via OpenRouter.
        6. Verifies source citations.
        7. Persists messages in SQLite.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Resolve Session
        if not session_id:
            session_id = FileValidator.generate_session_id()
            session = SessionModel(
                session_id=session_id,
                session_name=question[:32] + ("..." if len(question) > 32 else ""),
                created_at=now_iso,
                updated_at=now_iso,
            )
            Repository.create_session(session)
        else:
            session = Repository.get_session(session_id)
            if not session:
                session = SessionModel(
                    session_id=session_id,
                    session_name=question[:32] + ("..." if len(question) > 32 else ""),
                    created_at=now_iso,
                    updated_at=now_iso,
                )
                Repository.create_session(session)

        # 2. Identify Document Scope
        target_doc_ids: List[str] = []
        if selected_document_ids is not None:
            # User specified explicit document scope (empty list, specific IDs, or deleted docs)
            for did in selected_document_ids:
                doc = Repository.get_document_by_id(did)
                if doc and doc.processing_status == "ready":
                    target_doc_ids.append(did)
            # Strict scope: if user specified documents but none are valid/ready, do NOT fallback
        elif session and session.documents:
            # Use ready docs already associated with this session
            for d in session.documents:
                doc = Repository.get_document_by_id(d.document_id)
                if doc and doc.processing_status == "ready":
                    target_doc_ids.append(d.document_id)
        else:
            # Unconstrained query: check all ready documents across repository
            all_ready_docs = [
                d.document_id
                for d in Repository.list_documents()
                if d.processing_status == "ready"
            ]
            target_doc_ids = all_ready_docs

        # Link valid documents to session
        for did in target_doc_ids:
            Repository.link_document_to_session(session_id, did)

        # 3. Save User Message
        user_msg_id = FileValidator.generate_message_id()
        user_msg = MessageModel(
            message_id=user_msg_id,
            session_id=session_id,
            role="user",
            message_content=question,
            created_at=now_iso,
        )
        Repository.create_message(user_msg)

        # Strict document availability enforcement: If no PDF is uploaded/ready, do NOT call LLM
        if not target_doc_ids:
            ai_msg_id = FileValidator.generate_message_id()
            answer = settings.NO_DOCUMENTS_UPLOADED_MSG
            ai_msg = MessageModel(
                message_id=ai_msg_id,
                session_id=session_id,
                role="assistant",
                message_content=answer,
                created_at=now_iso,
                citations=[],
                thinking_process="Document availability check: No syllabus PDF has been uploaded or selected.",
                reasoning_time=0.0,
            )
            Repository.create_message(ai_msg)
            Repository.update_session(session_id, updated_at=now_iso)

            return ChatResponse(
                answer=answer,
                session_id=session_id,
                message_id=ai_msg_id,
                citations=[],
                answer_status="no_documents_available",
                retrieved_source_count=0,
                thinking_process="Document availability check: No syllabus PDF has been uploaded or selected.",
                reasoning_time=0.0,
            )

        # 4. Semantic Retrieval
        retrieved_raw = self.retrieval_service.retrieve_chunks(
            query=question,
            document_ids=target_doc_ids,
        )

        # 5. Relevance Filtering
        filtered_chunks = self.retrieval_service.filter_by_relevance(retrieved_raw)

        # 5b. Check if this is an explicit summary / study notes / whole-document request
        is_summary_request = any(
            phrase in question.lower()
            for phrase in [
                "summarize",
                "summary",
                "study notes",
                "educational notes",
                "teach me",
                "teach the syllabus",
                "explain the syllabus",
                "explain the document",
                "explain this document",
                "explain this pdf",
                "syllabus overview",
                "topic by topic",
                "complete notes",
                "comprehensive notes",
                "revision notes",
                "what is this document about",
                "what is in this document",
                "what does this document cover",
                "key findings and conclusions",
            ]
        )

        if is_summary_request and target_doc_ids:
            target_did = target_doc_ids[0]
            sum_rec = Repository.get_document_summary(target_did)

            # If not yet generated or failed, dynamically run the hierarchical summarization engine
            if not sum_rec or sum_rec.get("status") != "completed" or not sum_rec.get("final_summary"):
                try:
                    logger.info(f"Auto-generating complete study notes for '{target_did}' to fulfill chat request...")
                    sum_service = SummarizationService(mock_mode=bool(mock_llm_response))
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            pool.submit(
                                asyncio.run,
                                sum_service.summarize_document(target_did, force_refresh=True),
                            ).result()
                    else:
                        asyncio.run(sum_service.summarize_document(target_did, force_refresh=True))

                    sum_rec = Repository.get_document_summary(target_did)
                except Exception as auto_sum_err:
                    logger.warning(f"Could not auto-generate full summary: {auto_sum_err}")

            # If complete educational notes exist, deliver the ENTIRE notes directly without truncation
            if sum_rec and sum_rec.get("final_summary") and sum_rec.get("status") in ("completed", "partial"):
                doc_obj = Repository.get_document_by_id(target_did)
                fn = doc_obj.original_filename if (doc_obj and doc_obj.original_filename) else (doc_obj.filename if doc_obj else "Document")
                full_notes = sum_rec["final_summary"]

                answer = mock_llm_response if mock_llm_response is not None else full_notes
                answer_status = "grounded"
                reasoning_time = 0.5

                # Build verified citations for every page covered in the master summary
                verified_citations: List[CitationModel] = []
                try:
                    page_summaries_raw = json.loads(sum_rec.get("page_summaries_json") or "[]")
                    for p_data in page_summaries_raw:
                        p_num = p_data.get("page_number", 1)
                        p_snippet = (p_data.get("summary") or "").strip()
                        if len(p_snippet) > 280:
                            p_snippet = p_snippet[:280] + "..."
                        verified_citations.append(
                            CitationModel(
                                citation_id=f"cit_sum_{target_did}_{p_num}",
                                document_id=target_did,
                                filename=fn,
                                page_number=p_num,
                                chunk_id=f"{target_did}_p{p_num}",
                                relevant_text_snippet=p_snippet or f"Comprehensive syllabus notes for Page {p_num}",
                                relevance_score=1.0,
                            )
                        )
                    if not verified_citations and sum_rec.get("total_pages", 0) > 0:
                        for p_idx in range(1, sum_rec["total_pages"] + 1):
                            verified_citations.append(
                                CitationModel(
                                    citation_id=f"cit_sum_{target_did}_{p_idx}",
                                    document_id=target_did,
                                    filename=fn,
                                    page_number=p_idx,
                                    chunk_id=f"{target_did}_p{p_idx}",
                                    relevant_text_snippet=f"Comprehensive study notes for Page {p_idx}",
                                    relevance_score=1.0,
                                )
                            )
                except Exception as cit_parse_err:
                    logger.warning(f"Failed parsing page summaries for citations: {cit_parse_err}")

                thinking_process = (
                    f"Generated comprehensive educational study notes for '{fn}' across "
                    f"{sum_rec.get('total_pages', len(verified_citations))} pages with dynamic topic-by-topic analysis."
                )

                # Persist assistant message with full study notes
                ai_msg_id = FileValidator.generate_message_id()
                ai_msg = MessageModel(
                    message_id=ai_msg_id,
                    session_id=session_id,
                    role="assistant",
                    message_content=answer,
                    created_at=now_iso,
                    citations=verified_citations,
                    thinking_process=thinking_process,
                    reasoning_time=reasoning_time,
                )
                Repository.create_message(ai_msg)
                Repository.update_session(session_id, updated_at=now_iso)

                return ChatResponse(
                    answer=answer,
                    session_id=session_id,
                    message_id=ai_msg_id,
                    citations=[
                        CitationResponse(
                            citation_id=c.citation_id,
                            document_id=c.document_id,
                            filename=c.filename,
                            page_number=c.page_number,
                            chunk_id=c.chunk_id,
                            relevant_text_snippet=c.relevant_text_snippet,
                            relevance_score=float(c.relevance_score) if c.relevance_score is not None else 1.0,
                        )
                        for c in verified_citations
                    ],
                    answer_status=answer_status,
                    retrieved_source_count=len(verified_citations),
                    thinking_process=thinking_process,
                    reasoning_time=float(reasoning_time),
                )

        # 6. Standard Specific Q&A: Augment context with summary if available
        if target_doc_ids:
            for did in target_doc_ids:
                sum_rec = Repository.get_document_summary(did)
                if sum_rec and sum_rec.get("final_summary"):
                    from langchain_core.documents import Document
                    doc_obj = Repository.get_document_by_id(did)
                    fn = doc_obj.filename if doc_obj else "Document"
                    summary_doc = Document(
                        page_content=f"Document Outline & Notes for {fn}:\n{sum_rec['final_summary']}",
                        metadata={
                            "document_id": did,
                            "filename": fn,
                            "source": fn,
                            "page": 1,
                            "chunk_id": f"{did}_notes_context",
                        },
                    )
                    from app.services.retrieval_service import RetrievedChunk
                    filtered_chunks.insert(0, RetrievedChunk(document=summary_doc, relevance_score=0.95))

        # 7. LLM Generation for specific questions
        answer, answer_status, reasoning_time = self.llm_service.generate_answer(
            question=question,
            retrieved_chunks=filtered_chunks,
            mock_response=mock_llm_response,
        )

        # 8. Citation Verification: Only attach valid citations if answer is grounded
        verified_citations: List[CitationModel] = []
        if answer_status == "grounded" and filtered_chunks:
            # Filter out generic notes_context from citation badges if specific chunks exist
            usable_chunks = [
                c for c in filtered_chunks
                if not (c.document.metadata.get("chunk_id", "").endswith("_notes_context"))
            ]
            if not usable_chunks:
                usable_chunks = filtered_chunks
            verified_citations = self.citation_service.build_citations(usable_chunks)

        thinking_process = (
            f"Searched FAISS index across {len(target_doc_ids)} documents. "
            f"Retrieved {len(retrieved_raw)} candidate chunks, filtered to {len(filtered_chunks)} relevant chunks. "
            f"Processed with Nemotron 3.5 Lightning (status: {answer_status})."
        )

        # 8. Save Assistant Message
        ai_msg_id = FileValidator.generate_message_id()
        ai_msg = MessageModel(
            message_id=ai_msg_id,
            session_id=session_id,
            role="assistant",
            message_content=answer,
            created_at=now_iso,
            citations=verified_citations,
            thinking_process=thinking_process,
            reasoning_time=reasoning_time,
        )
        Repository.create_message(ai_msg)
        Repository.update_session(session_id, updated_at=now_iso)

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            message_id=ai_msg_id,
            citations=[
                CitationResponse(
                    citation_id=c.citation_id,
                    document_id=c.document_id,
                    filename=c.filename,
                    page_number=c.page_number,
                    chunk_id=c.chunk_id,
                    relevant_text_snippet=c.relevant_text_snippet,
                    relevance_score=float(c.relevance_score) if c.relevance_score is not None else None,
                )
                for c in verified_citations
            ],
            answer_status=answer_status,
            retrieved_source_count=len(filtered_chunks),
            thinking_process=thinking_process,
            reasoning_time=float(reasoning_time) if reasoning_time is not None else None,
        )

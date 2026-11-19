import pytest
from langchain_core.documents import Document
from app.services.retrieval_service import RetrievedChunk, RetrievalService
from app.services.citation_service import CitationService
from app.services.llm_service import LLMService


def test_citation_generation():
    """Verify that citations contain genuine document_id, filename, page, and snippet."""
    chunk = RetrievedChunk(
        document=Document(
            page_content="The primary objective of Database Management Systems is data independence.",
            metadata={"document_id": "doc_db", "filename": "dbms_syllabus.pdf", "page": 4, "chunk_id": "doc_db_p4_c1"},
        ),
        similarity_score=0.92,
        raw_distance=0.16,
    )

    citations = CitationService.build_citations([chunk])
    assert len(citations) == 1
    cit = citations[0]
    assert cit.document_id == "doc_db"
    assert cit.filename == "dbms_syllabus.pdf"
    assert cit.page_number == 4
    assert cit.chunk_id == "doc_db_p4_c1"
    assert "data independence" in cit.relevant_text_snippet
    assert cit.relevance_score == 0.92


def test_llm_mock_mode_zero_credits():
    """Verify that automated tests can mock LLM generation and consume zero OpenRouter credits."""
    llm = LLMService()
    mock_text = "According to the syllabus, DBMS provides physical and logical data independence."
    answer, status, elapsed = llm.generate_answer(
        question="What is data independence?",
        retrieved_chunks=[],
        mock_response=mock_text,
    )
    assert answer == mock_text
    assert status == "grounded"
    assert elapsed >= 0.0


def test_insufficient_evidence_fallback():
    """Verify exact insufficient evidence fallback string when no relevant chunks retrieved."""
    llm = LLMService()
    answer, status, _ = llm.generate_answer(
        question="What is quantum gravity?",
        retrieved_chunks=[],
    )
    assert answer == "I couldn't find sufficient information about this topic in your uploaded document."
    assert status == "insufficient_evidence"

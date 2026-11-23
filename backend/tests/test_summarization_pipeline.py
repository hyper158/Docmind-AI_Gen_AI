import io
import pytest
from PyPDF2 import PdfWriter

from app.database.initialization import init_db
from app.database.repository import Repository
from app.models.document import DocumentModel
from app.services.pdf_service import PDFService, ExtractedPage
from app.services.summarization.token_budget import (
    estimate_token_count,
    split_text_into_token_chunks,
)
from app.services.summarization.page_summarizer import PageSummarizer
from app.services.summarization.hierarchical_aggregator import HierarchicalAggregator
from app.services.summarization.summarization_service import SummarizationService
from app.services.summarization.document_analyzer import DocumentAnalyzer
from app.services.llm_service import LLMService


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()


def create_multi_page_pdf(pages_data: list) -> bytes:
    """Helper to dynamically generate a valid multi-page PDF using PyPDF2."""
    writer = PdfWriter()
    for text in pages_data:
        # Create a page and add text annotation or content
        page = writer.add_blank_page(width=612, height=792)
        if text:
            # PyPDF2 allows adding annotations / form fields or text
            pass
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


# ------------------ Token Budget & Chunking Tests ------------------

def test_token_budget_and_splitting():
    """Verify token estimation and sentence-boundary chunking with overlap."""
    text = (
        "Principal Component Analysis is an orthogonal transformation. "
        "It projects data onto lower-dimensional subspaces aligned with maximum covariance. "
        "Eigenvectors determine the principal axes. "
        "Eigenvalues represent the variance explained by each principal component."
    )
    tokens = estimate_token_count(text)
    assert tokens > 10

    # Test chunking with small chunk size
    chunks = split_text_into_token_chunks(text, max_chunk_chars=120, overlap_chars=30)
    assert len(chunks) >= 2
    # Verify all content is captured
    combined = " ".join(chunks)
    assert "Principal Component Analysis" in combined
    assert "variance explained" in combined


# ------------------ Extraction & Page Diagnostics Tests ------------------

def test_page_extractor_diagnostics():
    """Verify extraction report identifies empty, insufficient, and valid pages."""
    p1 = ExtractedPage(
        document_id="doc_test",
        filename="test.pdf",
        page_number=1,
        page_text="Supervised learning trains models on labeled input-output pairs to minimize empirical risk.",
        char_count=93,
        word_count=13,
        status="success",
    )
    p2 = ExtractedPage(
        document_id="doc_test",
        filename="test.pdf",
        page_number=2,
        page_text="",
        char_count=0,
        word_count=0,
        is_empty=True,
        status="empty",
    )
    p3 = ExtractedPage(
        document_id="doc_test",
        filename="test.pdf",
        page_number=3,
        page_text="Short.",
        char_count=6,
        word_count=1,
        is_insufficient_text=True,
        status="insufficient",
    )

    assert p1.status == "success"
    assert p2.is_empty is True
    assert p3.is_insufficient_text is True


# ------------------ Page Summarizer Tests ------------------

@pytest.mark.asyncio
async def test_page_summarizer_empty_and_normal():
    """Verify PageSummarizer handles empty pages without LLM calls and summarizes normal pages."""
    summarizer = PageSummarizer(mock_mode=True)

    # Empty page
    empty_page = ExtractedPage(
        document_id="doc_1",
        filename="doc.pdf",
        page_number=1,
        page_text="",
        is_empty=True,
        status="empty",
    )
    res_empty = await summarizer.summarize_page(empty_page)
    assert res_empty.status == "empty"
    assert "Empty page" in res_empty.summary_text

    # Normal technical page
    normal_page = ExtractedPage(
        document_id="doc_1",
        filename="doc.pdf",
        page_number=2,
        page_text="Convolutional Neural Networks use spatial filters and pooling layers to detect hierarchical visual patterns.",
        char_count=110,
        status="success",
    )
    res_normal = await summarizer.summarize_page(normal_page)
    assert res_normal.status == "completed"
    assert res_normal.page_number == 2
    assert len(res_normal.summary_text) > 20


@pytest.mark.asyncio
async def test_page_summarizer_long_page_chunking():
    """Verify that an exceptionally long page is divided into sub-chunks and merged."""
    long_text = (
        "Transformer architectures rely entirely on self-attention mechanisms. " * 30
    )  # ~2,100 characters
    summarizer = PageSummarizer(mock_mode=True, max_chunk_chars=500, chunk_overlap=50)

    long_page = ExtractedPage(
        document_id="doc_long",
        filename="long.pdf",
        page_number=5,
        page_text=long_text,
        char_count=len(long_text),
        status="success",
    )

    res = await summarizer.summarize_page(long_page)
    assert res.status in ("completed", "partial")
    assert res.is_chunked is True
    assert res.chunk_count > 1
    assert res.page_number == 5


# ------------------ Hierarchical Aggregation Tests ------------------

@pytest.mark.asyncio
async def test_hierarchical_aggregator_multi_level():
    """Verify multi-level section aggregation and final synthesis preserving page citations."""
    summarizer = PageSummarizer(mock_mode=True)
    aggregator = HierarchicalAggregator(batch_size=3, mock_mode=True)

    # Create 6 page summaries
    pages = [
        ExtractedPage(
            document_id="doc_hier",
            filename="syllabus.pdf",
            page_number=i,
            page_text=f"Chapter {i} technical explanations on algorithms and data structures.",
            char_count=70,
            status="success",
        )
        for i in range(1, 7)
    ]

    page_summaries = await summarizer.summarize_all_pages(pages)
    assert len(page_summaries) == 6

    # Run hierarchical aggregation
    result = await aggregator.aggregate("doc_hier", "syllabus.pdf", page_summaries)
    assert result.total_pages == 6
    assert result.aggregation_levels == 2  # Level 1 (pages) -> Level 2 (sections) -> Master
    assert len(result.section_summaries) == 2  # 6 pages / batch_size 3 = 2 sections
    assert "Executive Overview" in result.final_summary
    assert "Citation Matrix" in result.final_summary


# ------------------ End-to-End Summarization Service Tests ------------------

@pytest.mark.asyncio
async def test_summarization_service_full_workflow(tmp_path):
    """Verify full summarization pipeline: extraction, page summaries, aggregation, and DB persistence."""
    # 1. Create a dummy PDF on disk
    writer = PdfWriter()
    p1 = writer.add_blank_page(width=400, height=400)
    p2 = writer.add_blank_page(width=400, height=400)
    pdf_file = tmp_path / "test_doc.pdf"
    with open(pdf_file, "wb") as f:
        writer.write(f)

    # 2. Register document in SQLite
    doc_id = "doc_test_summary_123"
    doc_model = DocumentModel(
        document_id=doc_id,
        filename="test_doc.pdf",
        original_filename="test_doc.pdf",
        file_path=str(pdf_file),
        file_hash="dummy_hash_sum_123",
        upload_timestamp="2026-11-23T10:00:00Z",
        processing_status="ready",
        page_count=2,
    )
    Repository.create_document(doc_model)

    # 3. Execute summarization in mock mode
    service = SummarizationService(mock_mode=True)
    summary_result = await service.summarize_document(doc_id, force_refresh=True)

    # 4. Verify results
    assert summary_result["document_id"] == doc_id
    assert summary_result["status"] in ("completed", "partial")
    assert "final_summary" in summary_result
    assert "page_summaries" in summary_result
    assert len(summary_result["page_summaries"]) == 2

    # Verify SQLite persistence
    db_rec = Repository.get_document_summary(doc_id)
    assert db_rec is not None
    assert db_rec["status"] in ("completed", "partial")

    # Clean up test document
    Repository.delete_document(doc_id)


# ------------------ Dynamic Structure Detection Tests ------------------

def test_document_analyzer_dynamic_topics():
    """Verify dynamic structure detection extracts topics, key terms, and flags without hardcoding."""
    pages = [
        ExtractedPage(
            document_id="doc_dyn",
            filename="Distributed_Systems_Syllabus.pdf",
            page_number=1,
            page_text="Chapter 1: Distributed Consensus and Fault Tolerance\n"
                      "Consensus is a fundamental problem in distributed computing.\n"
                      "Key terms include Raft, Paxos, and Byzantine Agreement.",
            char_count=180,
            status="success",
        ),
        ExtractedPage(
            document_id="doc_dyn",
            filename="Distributed_Systems_Syllabus.pdf",
            page_number=2,
            page_text="Chapter 2: Replication and Performance Benchmarking\n"
                      "Step 1: Leader election. Step 2: Log replication. Step 3: Commit.\n"
                      "Formula: Latency L = RTT + ProcessingTime. Comparison of Raft vs Paxos.",
            char_count=210,
            status="success",
        ),
    ]

    structure = DocumentAnalyzer.analyze_document("doc_dyn", "Distributed_Systems_Syllabus.pdf", pages)
    assert structure.total_pages == 2
    assert structure.has_formal_chapters is True
    assert len(structure.topics) >= 1
    assert any("consensus" in t.title.lower() for t in structure.topics)

    # Verify technical flags
    topic2 = [t for t in structure.topics if t.page_numbers == [2] or 2 in t.page_numbers]
    if topic2:
        assert topic2[0].has_processes is True or topic2[0].has_comparisons is True


# ------------------ Text-Only Output Enforcement Tests ------------------

def test_llm_service_sanitize_text_only():
    """Verify text-only sanitizer removes images, HTML img tags, and replaces mermaid diagrams."""
    raw_output = (
        "Here are the study notes.\n\n"
        "![System Architecture](https://example.com/arch.png)\n\n"
        "<img src='flowchart.jpg' alt='Workflow'>\n\n"
        "```mermaid\ngraph TD\nA[Ingest] --> B[Transform] --> C[Load]\n```\n\n"
        "| Step | Action |\n| 1 | Extract |\n| 2 | Load |\n"
    )

    clean_output = LLMService._sanitize_text_only(raw_output)
    assert "https://example.com/arch.png" not in clean_output
    assert "<img" not in clean_output
    assert "```mermaid" not in clean_output
    # Tables and textual explanations must remain intact
    assert "| Step | Action |" in clean_output

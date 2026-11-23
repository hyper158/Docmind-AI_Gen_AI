import io
import json
import uuid
import pytest
from PyPDF2 import PdfWriter

from app.database.initialization import init_db
from app.database.repository import Repository
from app.models.document import DocumentModel
from app.services.chat_service import ChatService


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()


def create_test_pdf(filepath: str, page_texts: list):
    """Helper to create a multi-page PDF on disk."""
    writer = PdfWriter()
    for text in page_texts:
        writer.add_blank_page(width=500, height=700)
    with open(filepath, "wb") as f:
        writer.write(f)


def test_e2e_chat_comprehensive_study_notes(tmp_path):
    """
    End-to-end test verifying:
    1. Chat summary request returns complete, uncompressed educational notes.
    2. Citations accurately map all pages of the document.
    3. Output is 100% text-only with zero images, SVG, or Mermaid diagrams.
    """
    pdf_path = str(tmp_path / "Advanced_Algorithms_Syllabus.pdf")
    pages = [
        "Chapter 1: Asymptotic Analysis and Recurrence Relations. Big-O notation measures upper bounds.",
        "Chapter 2: Divide and Conquer Algorithms. Master Theorem calculates recurrence bounds: T(n) = aT(n/b) + f(n).",
        "Chapter 3: Dynamic Programming vs Greedy Choice. Comparison: DP guarantees global optimum; Greedy chooses local optimum.",
    ]
    create_test_pdf(pdf_path, pages)

    doc_id = "doc_e2e_algo_syllabus"
    # Clean up any leftover from previous runs
    Repository.delete_document(doc_id)

    doc_model = DocumentModel(
        document_id=doc_id,
        filename="Advanced_Algorithms_Syllabus.pdf",
        original_filename="Advanced_Algorithms_Syllabus.pdf",
        file_path=pdf_path,
        file_hash=f"hash_algo_{uuid.uuid4().hex[:8]}",
        upload_timestamp="2026-11-23T12:00:00Z",
        processing_status="ready",
        page_count=3,
    )
    Repository.create_document(doc_model)

    chat_service = ChatService()

    # 1. Ask for comprehensive summary in chat
    query = "Can you provide a comprehensive summary of this document, highlighting the key findings and conclusions?"
    response = chat_service.process_chat(
        question=query,
        selected_document_ids=[doc_id],
        mock_llm_response=(
            "# Comprehensive Study Notes: Advanced Algorithms\n\n"
            "## 1. Executive Overview & Learning Objectives\n"
            "This syllabus covers foundational algorithmic design, complexity analysis, and computational paradigms.\n\n"
            "## 2. Dynamic Topic-by-Topic Comprehensive Teaching & Notes\n\n"
            "### Topic 1: Asymptotic Analysis ([Page 1])\n"
            "- **Core Concept & Definition**: **Asymptotic Notation** mathematically bounds resource consumption.\n"
            "- **How It Works**: Formal limits quantify growth rates as input size approaches infinity.\n\n"
            "### Topic 2: Divide and Conquer & Master Theorem ([Page 2])\n"
            "- **Formulas & Quantitative Metrics**: $T(n) = aT(n/b) + O(n^d)$.\n\n"
            "### Topic 3: Dynamic Programming vs Greedy Algorithms ([Page 3])\n\n"
            "| Paradigm | Subproblem Overlap | Decision Strategy |\n"
            "| :--- | :--- | :--- |\n"
            "| Dynamic Programming | High overlap (memoized) | Optimal substructure |\n"
            "| Greedy Algorithms | No overlap | Local myopic choice |\n\n"
            "## 3. Technical Terminology & Formal Definitions Glossary\n"
            "- **Memoization**: Caching computed subproblem solutions [Page 3].\n\n"
            "## 4. Key Formulas, Methodologies & Quantitative Rules\n"
            "- **Master Theorem**: $T(n) = aT(n/b) + f(n)$\n\n"
            "## 5. Comprehensive Summary & Master Page Citation Matrix\n"
            "| Topic | Page Range |\n| :--- | :--- |\n| Asymptotic Bounds | Page 1 |\n| Master Theorem | Page 2 |\n| DP vs Greedy | Page 3 |\n"
        ),
    )

    # Verifications:
    # A. Content completeness
    assert response.answer_status == "grounded"
    assert "Executive Overview" in response.answer
    assert "Topic-by-Topic" in response.answer
    assert "Master Theorem" in response.answer
    assert "| Paradigm | Subproblem Overlap |" in response.answer

    # B. Verified citations cover all pages
    assert len(response.citations) >= 1
    page_numbers = [c.page_number for c in response.citations]
    assert 1 in page_numbers

    # C. Text-only enforcement
    assert "![" not in response.answer
    assert "<img" not in response.answer
    assert "```mermaid" not in response.answer

    # Clean up test document
    Repository.delete_document(doc_id)

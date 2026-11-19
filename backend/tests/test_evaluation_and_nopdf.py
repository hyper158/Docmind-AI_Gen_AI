import pytest
from app.core.config import settings
from app.services.chat_service import ChatService
from evaluation.metrics import (
    compute_context_precision,
    compute_context_recall,
    compute_faithfulness,
    compute_answer_relevance,
    compute_citation_accuracy,
    compute_no_document_accuracy,
    compute_out_of_syllabus_accuracy,
)


def test_no_pdf_uploaded_enforcement():
    """Verify that asking a question with zero available documents immediately returns mandatory refusal."""
    chat_service = ChatService()
    # Explicitly pass non-existent doc IDs and no session
    response = chat_service.process_chat(
        question="What is deep learning?",
        session_id=None,
        selected_document_ids=["non_existent_doc_id"],
    )

    assert response.answer == settings.NO_DOCUMENTS_UPLOADED_MSG
    assert response.answer_status == "no_documents_available"
    assert len(response.citations) == 0
    assert response.retrieved_source_count == 0


def test_no_document_accuracy_metric():
    """Verify metric computation for no-document check."""
    ans = settings.NO_DOCUMENTS_UPLOADED_MSG
    assert compute_no_document_accuracy(ans, [], "no_documents_available", is_no_document=True) == 1.0
    # Should fail if citations are hallucinated
    assert compute_no_document_accuracy(ans, [{"fake": 1}], "no_documents_available", is_no_document=True) == 0.0


def test_out_of_syllabus_metric():
    """Verify out-of-syllabus rejection metric."""
    ans = settings.OUTSIDE_SYLLABUS_MSG
    assert compute_out_of_syllabus_accuracy(ans, "outside_syllabus", is_out_of_syllabus=True) == 1.0


def test_context_precision_and_recall():
    """Verify context precision and recall mathematical calculations."""
    class DummyDoc:
        def __init__(self, page, content):
            self.metadata = {"page": page}
            self.page_content = content

    class DummyChunk:
        def __init__(self, page, content):
            self.document = DummyDoc(page, content)

    chunks = [
        DummyChunk(1, "Supervised Learning optimizes models with labeled datasets."),
        DummyChunk(2, "Cross-validation prevents overfitting."),
        DummyChunk(9, "Unrelated material without target keywords."),
    ]

    prec = compute_context_precision(chunks, [1, 2], ["Supervised Learning"])
    assert prec == round(2 / 3, 4)

    rec = compute_context_recall(chunks, [1, 2], ["Supervised Learning", "Cross-validation"])
    assert rec == 1.0


def test_faithfulness_metric():
    """Verify faithfulness computation on grounded versus ungrounded claims."""
    class DummyDoc:
        def __init__(self, content):
            self.metadata = {"page": 1}
            self.page_content = content

    class DummyChunk:
        def __init__(self, content):
            self.document = DummyDoc(content)

    chunks = [DummyChunk("LoRA freezes base weights and uses low-rank trainable decomposition matrices.")]

    grounded_ans = "LoRA freezes base weights and introduces low-rank decomposition matrices."
    assert compute_faithfulness(grounded_ans, chunks, "grounded") == 1.0

    # Fallbacks are automatically 100% faithful
    assert compute_faithfulness(settings.INSUFFICIENT_ANSWER_MSG, [], "insufficient_evidence") == 1.0

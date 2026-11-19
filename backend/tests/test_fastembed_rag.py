import faiss
import io
import pytest
from langchain_core.documents import Document
from PyPDF2 import PdfWriter

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.vector_store_service import VectorStoreService
from app.services.retrieval_service import RetrievalService
from app.services.citation_service import CitationService
from app.services.chat_service import ChatService
from app.database.initialization import init_db
from app.database.repository import Repository
from app.models.document import DocumentModel


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


def test_fastembed_service_dimensions():
    """Verify EmbeddingService uses FastEmbed ONNX model BAAI/bge-small-en-v1.5 with 384 dimensions."""
    emb_service = EmbeddingService()
    assert emb_service.embeddings is not None

    query_vec = emb_service.embed_query("What is parallel programming?")
    assert isinstance(query_vec, list)
    assert len(query_vec) == 384
    assert isinstance(query_vec[0], float)

    docs_vecs = emb_service.embed_documents(["First test chunk", "Second test chunk"])
    assert len(docs_vecs) == 2
    assert len(docs_vecs[0]) == 384
    assert len(docs_vecs[1]) == 384


def test_faiss_indexing_with_fastembed(tmp_path, monkeypatch):
    """Verify building, saving, loading and querying FAISS index using FastEmbed."""
    vs_service = VectorStoreService()
    monkeypatch.setattr(vs_service, "indexes_dir", tmp_path)

    doc_id = "doc_fastembed_test"
    chunks = [
        Document(
            page_content="Distributed systems communicate via message passing over network sockets.",
            metadata={"document_id": doc_id, "filename": "distributed.pdf", "page": 1, "chunk_id": f"{doc_id}_p1_c1"},
        ),
        Document(
            page_content="Consistent hashing allows nodes to be added or removed with minimal rehashing.",
            metadata={"document_id": doc_id, "filename": "distributed.pdf", "page": 2, "chunk_id": f"{doc_id}_p2_c1"},
        ),
    ]

    index_path = vs_service.build_and_save_index(doc_id, chunks)
    assert index_path.exists()
    assert (index_path / "index.faiss").exists()
    assert (index_path / "index.pkl").exists()

    loaded = vs_service.load_index(doc_id)
    assert loaded is not None

    results = loaded.similarity_search_with_score("How does consistent hashing work?", k=1)
    assert len(results) == 1
    doc, score = results[0]
    assert "Consistent hashing" in doc.page_content
    assert doc.metadata["page"] == 2
    assert doc.metadata["document_id"] == doc_id


def test_retrieval_and_citations(tmp_path, monkeypatch):
    """Verify retrieval service and citation service end-to-end with FastEmbed."""
    vs_service = VectorStoreService()
    monkeypatch.setattr(vs_service, "indexes_dir", tmp_path)

    doc_id = "doc_retrieval_test"
    chunks = [
        Document(
            page_content="Deadlock occurs when four conditions hold: mutual exclusion, hold and wait, no preemption, and circular wait.",
            metadata={"document_id": doc_id, "filename": "os_syllabus.pdf", "page": 5, "chunk_id": f"{doc_id}_p5_c1"},
        ),
        Document(
            page_content="Virtual memory provides an abstraction of main memory using paging and page replacement algorithms.",
            metadata={"document_id": doc_id, "filename": "os_syllabus.pdf", "page": 7, "chunk_id": f"{doc_id}_p7_c1"},
        ),
    ]
    vs_service.build_and_save_index(doc_id, chunks)

    retrieval_service = RetrievalService(vector_store_service=vs_service, threshold=0.01)
    retrieved = retrieval_service.retrieve_chunks("What are the conditions for deadlock?", [doc_id], top_k=2)

    assert len(retrieved) > 0
    top_chunk = retrieved[0]
    assert "mutual exclusion" in top_chunk.document.page_content
    assert top_chunk.similarity_score > 0.0

    citations = CitationService.build_citations(retrieved)
    assert len(citations) >= 1
    cit = citations[0]
    assert cit.document_id == doc_id
    assert cit.filename == "os_syllabus.pdf"
    assert cit.page_number == 5
    assert "deadlock" in cit.relevant_text_snippet.lower() or "mutual exclusion" in cit.relevant_text_snippet.lower()


def test_chat_service_with_mock_llm(tmp_path, monkeypatch):
    """Verify chat answering pipeline with mocked LLM response (zero OpenRouter credits)."""
    vs_service = VectorStoreService()
    monkeypatch.setattr(vs_service, "indexes_dir", tmp_path)

    doc_id = "doc_chat_mock_test"
    chunks = [
        Document(
            page_content="Supervised learning algorithms infer a function from labeled training data.",
            metadata={"document_id": doc_id, "filename": "ml_course.pdf", "page": 3, "chunk_id": f"{doc_id}_p3_c1"},
        ),
    ]
    vs_service.build_and_save_index(doc_id, chunks)

    # Register document in DB
    now_iso = "2026-11-17T14:00:00Z"
    test_doc = DocumentModel(
        document_id=doc_id,
        filename="ml_course.pdf",
        original_filename="ml_course.pdf",
        file_path="storage/uploads/ml_course.pdf",
        file_hash="mock_hash_12345",
        upload_timestamp=now_iso,
        processing_status="ready",
        file_size=1024,
        chunk_count=1,
        page_count=3,
    )
    Repository.create_document(test_doc)

    retrieval_svc = RetrievalService(vector_store_service=vs_service, threshold=0.01)
    chat_svc = ChatService(retrieval_service=retrieval_svc)

    mock_answer = "Supervised learning uses labeled training examples to train predictive models."
    resp = chat_svc.process_chat(
        question="What is supervised learning?",
        selected_document_ids=[doc_id],
        mock_llm_response=mock_answer,
    )

    assert resp.answer == mock_answer
    assert resp.answer_status == "grounded"
    assert resp.retrieved_source_count >= 1
    assert len(resp.citations) >= 1
    assert resp.citations[0].document_id == doc_id
    assert resp.citations[0].page_number == 3

    # Clean up DB
    Repository.delete_document(doc_id)


def test_pdf_upload_and_indexing_pipeline(tmp_path, monkeypatch):
    """Verify PDF validation, PyPDF2 extraction, LangChain chunking, and FastEmbed FAISS indexing."""
    from app.utils.file_validator import FileValidator
    from pathlib import Path

    sample_pdf_path = Path("storage/uploads/doc_09e2488b4629_Unit_3.1.pdf")
    if not sample_pdf_path.exists():
        pytest.skip("Sample PDF not found for pipeline test")

    pdf_bytes = sample_pdf_path.read_bytes()
    filename, file_hash = FileValidator.validate_pdf(pdf_bytes, "test_upload.pdf")
    assert filename == "test_upload.pdf"
    assert len(file_hash) == 64

    doc_id = "doc_pipeline_test"
    pdf_svc = PDFService()
    chunk_svc = ChunkingService()
    vs_svc = VectorStoreService()
    monkeypatch.setattr(vs_svc, "indexes_dir", tmp_path)

    pages, page_count, snippet = pdf_svc.extract_text_from_pdf(pdf_bytes, doc_id, filename)
    assert page_count > 0
    assert len(pages) == page_count

    chunks = chunk_svc.chunk_pages(pages)
    assert len(chunks) > 0
    assert chunks[0].metadata["document_id"] == doc_id
    assert chunks[0].metadata["page"] == 1

    idx_path = vs_svc.build_and_save_index(doc_id, chunks)
    assert (idx_path / "index.faiss").exists()

    loaded = vs_svc.load_index(doc_id)
    assert loaded is not None
    search_results = loaded.similarity_search("parallel programming", k=2)
    assert len(search_results) == 2

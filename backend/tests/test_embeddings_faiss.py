import pytest
from langchain_core.documents import Document
from app.services.vector_store_service import VectorStoreService


def test_faiss_lifecycle(tmp_path, monkeypatch):
    """Tests saving, reloading, and querying FAISS index."""
    service = VectorStoreService()
    # Redirect indexes dir to temporary directory
    service.indexes_dir = tmp_path
    monkeypatch.setattr(service, "indexes_dir", tmp_path)

    doc_id = "doc_test_123"
    chunks = [
        Document(
            page_content="Gradient descent optimizes the loss function by updating weights iteratively.",
            metadata={"document_id": doc_id, "filename": "ml.pdf", "page": 1, "chunk_id": f"{doc_id}_p1_c1"},
        ),
        Document(
            page_content="Backpropagation computes the gradients of the error with respect to each weight using chain rule.",
            metadata={"document_id": doc_id, "filename": "ml.pdf", "page": 2, "chunk_id": f"{doc_id}_p2_c1"},
        ),
    ]

    # Build and save
    index_path = service.build_and_save_index(doc_id, chunks)
    assert index_path.exists()
    assert (index_path / "index.faiss").exists()

    # Load index
    loaded_store = service.load_index(doc_id)
    assert loaded_store is not None

    # Query search
    results = loaded_store.similarity_search("How does gradient descent update weights?", k=1)
    assert len(results) == 1
    assert "Gradient descent" in results[0].page_content

    # Delete index
    deleted = service.delete_index(doc_id)
    assert deleted is True
    assert not index_path.exists()

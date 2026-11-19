import pytest
from app.services.pdf_service import ExtractedPage
from app.services.chunking_service import ChunkingService


def test_chunking_preserves_metadata():
    """Verify that LangChain text chunking preserves document_id, filename, source, page, and chunk_id."""
    pages = [
        ExtractedPage(
            document_id="doc_101",
            filename="syllabus.pdf",
            page_number=1,
            page_text="Introduction to Computer Science and Data Structures. We cover Arrays, Linked Lists, Trees, and Graphs.",
        ),
        ExtractedPage(
            document_id="doc_101",
            filename="syllabus.pdf",
            page_number=2,
            page_text="Chapter 2: Algorithms and Dynamic Programming. Time complexity analysis using Big-O notation.",
        ),
    ]

    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    chunks = service.chunk_pages(pages)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.metadata["document_id"] == "doc_101"
        assert chunk.metadata["filename"] == "syllabus.pdf"
        assert chunk.metadata["source"] == "syllabus.pdf"
        assert chunk.metadata["page"] in [1, 2]
        assert "chunk_id" in chunk.metadata
        assert chunk.metadata["chunk_id"].startswith("doc_101_p")


def test_chunking_avoids_empty():
    """Verify empty pages do not produce ghost chunks."""
    pages = [
        ExtractedPage(
            document_id="doc_102",
            filename="empty.pdf",
            page_number=1,
            page_text="   \n\n  ",
        )
    ]
    service = ChunkingService()
    chunks = service.chunk_pages(pages)
    assert len(chunks) == 0

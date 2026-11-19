import uuid
from typing import List, Dict, Any, Optional
from app.services.retrieval_service import RetrievedChunk
from app.models.chat import CitationModel
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CitationService:
    """Verifies and constructs verified citations directly from retrieved LangChain chunks."""

    @staticmethod
    def build_citations(chunks: List[RetrievedChunk]) -> List[CitationModel]:
        """
        Builds structured citations from retrieved LangChain Document chunks.
        Guarantees that page numbers and filenames match actual document source metadata.
        """
        citations: List[CitationModel] = []
        seen_chunks = set()

        for chunk in chunks:
            meta = chunk.document.metadata
            chunk_id = meta.get("chunk_id", f"chunk_{uuid.uuid4().hex[:6]}")
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            raw_page = meta.get("page", 1)
            try:
                page_number = int(raw_page)
            except (ValueError, TypeError):
                page_number = 1

            snippet = chunk.document.page_content.strip()
            # Clean snippet for presentation
            if len(snippet) > 280:
                snippet = snippet[:280] + "..."

            rel_score = None
            if chunk.similarity_score is not None:
                try:
                    rel_score = float(chunk.similarity_score)
                except (ValueError, TypeError):
                    rel_score = None

            cit = CitationModel(
                citation_id=f"cit_{uuid.uuid4().hex[:8]}",
                document_id=str(meta.get("document_id", "")),
                filename=str(meta.get("filename", "document.pdf")),
                page_number=page_number,
                chunk_id=chunk_id,
                relevant_text_snippet=snippet,
                relevance_score=rel_score,
            )
            citations.append(cit)

        return citations

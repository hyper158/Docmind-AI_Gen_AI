from dataclasses import dataclass
from typing import List, Tuple, Optional
from langchain_core.documents import Document
from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.vector_store_service import VectorStoreService

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with calculated relevance similarity score."""

    document: Document
    similarity_score: float  # Normalized between 0.0 and 1.0
    raw_distance: float


class RetrievalService:
    """Handles semantic retrieval and relevance filtering from FAISS vector store."""

    def __init__(
        self,
        vector_store_service: Optional[VectorStoreService] = None,
        top_k: int = settings.TOP_K,
        threshold: float = settings.RELEVANCE_SCORE_THRESHOLD,
    ) -> None:
        self.vector_store_service = vector_store_service or VectorStoreService()
        self.top_k = top_k
        self.threshold = threshold

    @staticmethod
    def _calculate_similarity(raw_score: float) -> float:
        """
        Translates FAISS raw distance into a normalized similarity score in [0.0, 1.0].

        LangChain FAISS.from_documents with FastEmbedEmbeddings uses IndexFlatL2.
        For L2 distance D between unit-normalized vectors:
            cosine_similarity = 1 - (D / 2)
        D ranges [0, 2]:  D=0 → perfect match (sim=1.0), D=2 → opposite (sim=0.0).

        Note: for general English queries against real-world documents, cosine
        similarities between 0.10 and 0.40 are completely normal and meaningful
        (top-K nearest neighbours). A threshold above ~0.15 tends to reject all
        results for diverse PDFs.
        """
        raw_val = float(raw_score)
        if raw_val >= 0.0:
            similarity = max(0.0, min(1.0, 1.0 - (raw_val / 2.0)))
            return float(round(similarity, 4))
        # Negative raw_score means FAISS returned an inner-product / dot-product
        return float(round(max(0.0, min(1.0, (raw_val + 1.0) / 2.0)), 4))

    def retrieve_chunks(
        self,
        query: str,
        document_ids: List[str],
        top_k: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieves top-K semantic chunks from the selected document indexes,
        normalizes similarity scores, and applies relevance thresholding.
        """
        k = top_k or self.top_k
        if not document_ids:
            logger.warning("No document IDs provided for retrieval.")
            return []

        vector_store = self.vector_store_service.load_combined_index(document_ids)
        if vector_store is None:
            logger.warning(f"Could not load vector store for documents: {document_ids}")
            return []

        try:
            # Perform similarity search with score
            docs_and_scores = vector_store.similarity_search_with_score(query, k=k)

            retrieved: List[RetrievedChunk] = []
            for doc, raw_score in docs_and_scores:
                sim_score = self._calculate_similarity(raw_score)
                retrieved.append(
                    RetrievedChunk(
                        document=doc,
                        similarity_score=float(sim_score),
                        raw_distance=float(raw_score),
                    )
                )

            # Sort by similarity score descending
            retrieved.sort(key=lambda x: x.similarity_score, reverse=True)

            if retrieved:
                scores_summary = ", ".join(f"{c.similarity_score:.4f}" for c in retrieved[:5])
                logger.info(
                    f"Retrieved {len(retrieved)} raw chunks. Top-5 scores: [{scores_summary}]. "
                    f"Threshold: {self.threshold}."
                )
            else:
                logger.warning("FAISS similarity_search_with_score returned 0 results.")
            return retrieved

        except Exception as exc:
            logger.error(f"Error during semantic retrieval: {exc}")
            return []

    def filter_by_relevance(
        self, chunks: List[RetrievedChunk], min_threshold: Optional[float] = None
    ) -> List[RetrievedChunk]:
        """Filters retrieved chunks that meet the minimum similarity threshold."""
        thresh = min_threshold if min_threshold is not None else self.threshold
        filtered = [c for c in chunks if c.similarity_score >= thresh]
        if not filtered and chunks:
            # If all chunks fell below threshold, retain the best retrieved candidates
            # so the LLM has context to inspect rather than returning nothing.
            logger.info(
                f"All {len(chunks)} chunks were below threshold {thresh}. "
                f"Retaining top {min(len(chunks), self.top_k)} candidate chunks for LLM evaluation."
            )
            return chunks[:self.top_k]
        logger.info(
            f"Filtered {len(chunks)} down to {len(filtered)} chunks using threshold {thresh}."
        )
        return filtered

import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from app.core.config import settings
from app.core.exceptions import VectorStoreError
from app.core.logging_config import get_logger
from app.services.embedding_service import EmbeddingService

logger = get_logger(__name__)


class VectorStoreService:
    """Manages LangChain FAISS vector indexing, persistence, and semantic retrieval."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.indexes_dir = settings.INDEXES_DIR
        self.indexes_dir.mkdir(parents=True, exist_ok=True)

    def _get_doc_index_path(self, document_id: str) -> Path:
        """Returns the filesystem path for a specific document's FAISS index."""
        return self.indexes_dir / document_id

    def build_and_save_index(self, document_id: str, chunks: List[Document]) -> Path:
        """
        Creates a local FAISS index for the document chunks and persists it to disk.
        """
        if not chunks:
            raise VectorStoreError(f"Cannot build FAISS index for document '{document_id}': No chunks provided.")

        try:
            logger.info(f"Generating FAISS vector index for {len(chunks)} chunks of document '{document_id}'...")
            doc_index_path = self._get_doc_index_path(document_id)

            # Assign chunk_id as the document ID in FAISS
            ids = [chunk.metadata.get("chunk_id", f"{document_id}_{i}") for i, chunk in enumerate(chunks)]

            # Build FAISS index using LangChain
            vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=self.embedding_service.embeddings,
                ids=ids,
            )

            # Save locally
            doc_index_path.mkdir(parents=True, exist_ok=True)
            vector_store.save_local(str(doc_index_path))
            logger.info(f"FAISS index for '{document_id}' successfully saved to {doc_index_path}.")
            return doc_index_path

        except Exception as exc:
            logger.error(f"Error building FAISS index for '{document_id}': {exc}")
            raise VectorStoreError(f"Failed to build and save FAISS index: {exc}")

    def load_index(self, document_id: str) -> Optional[FAISS]:
        """
        Loads a document's FAISS index from disk.
        """
        doc_index_path = self._get_doc_index_path(document_id)
        if not (doc_index_path / "index.faiss").exists():
            logger.warning(f"No FAISS index found on disk for document '{document_id}'.")
            return None

        try:
            vector_store = FAISS.load_local(
                folder_path=str(doc_index_path),
                embeddings=self.embedding_service.embeddings,
                allow_dangerous_deserialization=True,
            )
            return vector_store
        except Exception as exc:
            logger.error(f"Failed to load FAISS index for '{document_id}': {exc}")
            raise VectorStoreError(f"Corrupted or invalid FAISS index for '{document_id}': {exc}")

    def load_combined_index(self, document_ids: List[str]) -> Optional[FAISS]:
        """
        Loads and merges FAISS indices for the specified documents.
        If document_ids is empty or contains multiple docs, merges them cleanly in memory.
        """
        if not document_ids:
            return None

        combined_store: Optional[FAISS] = None

        for doc_id in document_ids:
            store = self.load_index(doc_id)
            if store is not None:
                if combined_store is None:
                    combined_store = store
                else:
                    combined_store.merge_from(store)

        return combined_store

    def delete_index(self, document_id: str) -> bool:
        """
        Removes the FAISS index files for the document from disk.
        """
        doc_index_path = self._get_doc_index_path(document_id)
        if doc_index_path.exists():
            try:
                shutil.rmtree(doc_index_path)
                logger.info(f"Successfully deleted FAISS index for document '{document_id}'.")
                return True
            except Exception as exc:
                logger.error(f"Failed to delete FAISS index directory for '{document_id}': {exc}")
                raise VectorStoreError(f"Could not remove index files: {exc}")
        return False

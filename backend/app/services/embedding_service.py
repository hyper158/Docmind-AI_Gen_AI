from typing import Optional, List
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Manages local ONNX-based embeddings using FastEmbed (PyTorch-free, CPU-based)."""

    _instance: Optional["EmbeddingService"] = None
    _embeddings = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._embeddings = None
        return cls._instance

    def _init_embeddings(self) -> None:
        """Initializes FastEmbedEmbeddings singleton locally using ONNX Runtime without PyTorch."""
        model_name = settings.EMBEDDING_MODEL_NAME
        logger.info(f"Initializing local FastEmbed ONNX model '{model_name}' (CPU, PyTorch-free)...")

        try:
            from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

            self._embeddings = FastEmbedEmbeddings(
                model_name=model_name,
            )
            logger.info("Local FastEmbed embeddings loaded successfully.")
        except Exception as exc:
            logger.error(f"Failed to load local FastEmbed model: {exc}")
            raise

    @property
    def embeddings(self):
        """Returns the underlying LangChain embeddings object."""
        if self._embeddings is None:
            self._init_embeddings()
        return self._embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single query text."""
        return self.embeddings.embed_query(query)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of documents."""
        return self.embeddings.embed_documents(texts)

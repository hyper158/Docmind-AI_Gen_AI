from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.vector_store_service import VectorStoreService
from app.services.retrieval_service import RetrievalService
from app.services.citation_service import CitationService
from app.services.llm_service import LLMService
from app.services.chat_service import ChatService


def get_pdf_service() -> PDFService:
    return PDFService()


def get_chunking_service() -> ChunkingService:
    return ChunkingService()


def get_vector_store_service() -> VectorStoreService:
    return VectorStoreService()


def get_retrieval_service() -> RetrievalService:
    return RetrievalService()


def get_citation_service() -> CitationService:
    return CitationService()


def get_llm_service() -> LLMService:
    return LLMService()


def get_chat_service() -> ChatService:
    return ChatService()


_summarization_service_instance = None


def get_summarization_service():
    global _summarization_service_instance
    if _summarization_service_instance is None:
        from app.services.summarization.summarization_service import SummarizationService
        _summarization_service_instance = SummarizationService()
    return _summarization_service_instance


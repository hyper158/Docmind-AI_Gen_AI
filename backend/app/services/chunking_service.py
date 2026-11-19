from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.pdf_service import ExtractedPage

logger = get_logger(__name__)


class ChunkingService:
    """Splits extracted PDF pages into LangChain Document chunks preserving page metadata."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )

    def chunk_pages(self, pages: List[ExtractedPage]) -> List[Document]:
        """
        Converts extracted pages into LangChain Document chunks.
        Every chunk carries:
            - document_id
            - filename
            - source
            - page (1-indexed)
            - chunk_id
        """
        chunk_documents: List[Document] = []
        global_chunk_count = 0

        for page in pages:
            text = page.page_text.strip()
            if not text:
                continue

            # Split page text into smaller chunks
            page_chunks = self.splitter.split_text(text)

            for idx, chunk_str in enumerate(page_chunks):
                cleaned_chunk = chunk_str.strip()
                if not cleaned_chunk:
                    continue

                chunk_id = f"{page.document_id}_p{page.page_number}_c{idx + 1}"
                metadata = {
                    "document_id": page.document_id,
                    "filename": page.filename,
                    "source": page.filename,
                    "page": page.page_number,
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                }

                chunk_documents.append(
                    Document(
                        page_content=cleaned_chunk,
                        metadata=metadata,
                    )
                )
                global_chunk_count += 1

        logger.info(
            f"Created {len(chunk_documents)} LangChain Document chunks across {len(pages)} pages."
        )
        return chunk_documents

import datetime
import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.core.config import settings
from app.core.exceptions import InvalidPDFError, DocumentProcessingError, DocumentNotFoundError
from app.core.logging_config import get_logger
from app.database.repository import Repository
from app.models.document import DocumentModel, IndexMetadataModel
from app.schemas.document_schema import (
    DocumentResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
)
from app.utils.file_validator import FileValidator
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.vector_store_service import VectorStoreService
from app.api.dependencies import (
    get_pdf_service,
    get_chunking_service,
    get_vector_store_service,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    pdf_service: PDFService = Depends(get_pdf_service),
    chunking_service: ChunkingService = Depends(get_chunking_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Uploads and indexes a syllabus or study PDF document:
    1. Validates extension, magic PDF signature, and file size.
    2. Detects duplicate documents using SHA-256 hash.
    3. Saves file to backend/storage/uploads/.
    4. Extracts text page-by-page using PyPDF2.
    5. Converts pages to LangChain Document chunks.
    6. Generates local Sentence Transformers embeddings into FAISS.
    7. Persists metadata in SQLite.
    """
    try:
        file_bytes = await file.read()
        safe_filename, file_hash = FileValidator.validate_pdf(file_bytes, file.filename or "upload.pdf")

        # Check for duplicates
        existing_doc = Repository.get_document_by_hash(file_hash)
        if existing_doc:
            index_path = vector_store_service._get_doc_index_path(existing_doc.document_id)
            if existing_doc.processing_status == "ready" and (index_path / "index.faiss").exists():
                logger.info(f"Duplicate document detected (hash: {file_hash[:8]}). Returning existing record.")
                return DocumentResponse(**existing_doc.to_dict())
            else:
                logger.info(f"Found existing record '{existing_doc.document_id}' with incomplete/failed status or missing index. Re-processing...")
                Repository.delete_document(existing_doc.document_id)

        # Generate unique ID and save file
        document_id = FileValidator.generate_document_id()
        saved_file_name = f"{document_id}_{safe_filename}"
        saved_file_path = settings.UPLOADS_DIR / saved_file_name

        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        initial_doc = DocumentModel(
            document_id=document_id,
            filename=safe_filename,
            original_filename=file.filename or safe_filename,
            file_path=str(saved_file_path),
            file_hash=file_hash,
            upload_timestamp=now_iso,
            processing_status="processing",
            file_size=len(file_bytes),
        )
        Repository.create_document(initial_doc)

        # Extract text using PyPDF2
        extracted_pages, page_count, first_snippet = pdf_service.extract_text_from_pdf(
            file_bytes=file_bytes,
            document_id=document_id,
            filename=safe_filename,
        )

        # LangChain text splitting into structured Document chunks
        chunks = chunking_service.chunk_pages(extracted_pages)
        if not chunks:
            raise DocumentProcessingError(f"No usable text chunks could be extracted from '{safe_filename}'.")

        # Generate FAISS vector index
        index_path = vector_store_service.build_and_save_index(document_id, chunks)

        # Save index metadata
        index_meta = IndexMetadataModel(
            document_id=document_id,
            index_status="indexed",
            index_location=str(index_path),
            embedding_model=settings.EMBEDDING_MODEL_NAME,
            chunk_count=len(chunks),
        )
        Repository.upsert_index_metadata(index_meta)

        # Generate summary
        summary = (
            f"Syllabus Document: {safe_filename} ({page_count} pages, {len(chunks)} chunks). "
            f"Preview: {first_snippet[:180]}..."
        )

        # Mark ready
        Repository.update_document_status(
            document_id=document_id,
            status="ready",
            page_count=page_count,
            chunk_count=len(chunks),
            summary=summary,
            content_snippet=first_snippet,
        )

        updated_doc = Repository.get_document_by_id(document_id)
        return DocumentResponse(**updated_doc.to_dict())

    except (InvalidPDFError, DocumentProcessingError) as client_err:
        logger.error(f"Validation or processing error during upload: {client_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(client_err),
        )
    except Exception as exc:
        logger.exception(f"Unexpected server error processing PDF upload: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the PDF: {str(exc)}",
        )


@router.get("", response_model=DocumentListResponse)
def list_documents():
    """Lists all uploaded documents with processing status and stats."""
    docs = Repository.list_documents()
    return DocumentListResponse(
        documents=[DocumentResponse(**d.to_dict()) for d in docs],
        total_count=len(docs),
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str):
    """Retrieves metadata and status for a single document."""
    doc = Repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return DocumentResponse(**doc.to_dict())


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: str,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
):
    """
    Deletes a document:
    1. Removes physical file from storage/uploads.
    2. Removes FAISS vector index from storage/indexes.
    3. Cascades deletion in SQLite database.
    """
    doc = Repository.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    # 1. Delete physical PDF file
    file_path = Path(doc.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info(f"Deleted physical file {file_path}")
        except Exception as err:
            logger.warning(f"Could not delete physical file {file_path}: {err}")

    # 2. Delete FAISS vectors
    try:
        vector_store_service.delete_index(document_id)
    except Exception as err:
        logger.warning(f"Could not delete FAISS index for {document_id}: {err}")

    # 3. Delete database record
    Repository.delete_document(document_id)

    return DocumentDeleteResponse(
        success=True,
        document_id=document_id,
        message=f"Document '{doc.filename}' and its vector index were successfully deleted.",
    )

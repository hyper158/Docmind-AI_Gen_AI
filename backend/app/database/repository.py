import json
from typing import List, Optional
from app.database.connection import get_db_connection
from app.models.document import DocumentModel, IndexMetadataModel
from app.models.session import SessionModel
from app.models.chat import MessageModel, CitationModel
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Repository:
    """Central repository managing SQLite database transactions."""

    # ------------------ Document Operations ------------------

    @staticmethod
    def create_document(doc: DocumentModel) -> DocumentModel:
        """Inserts a new document record into SQLite."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (
                    document_id, filename, original_filename, file_path, file_hash,
                    upload_timestamp, processing_status, page_count, chunk_count,
                    file_size, summary, content_snippet
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    doc.document_id,
                    doc.filename,
                    doc.original_filename,
                    doc.file_path,
                    doc.file_hash,
                    doc.upload_timestamp,
                    doc.processing_status,
                    doc.page_count,
                    doc.chunk_count,
                    doc.file_size,
                    doc.summary,
                    doc.content_snippet,
                ),
            )
        return doc

    @staticmethod
    def get_document_by_id(document_id: str) -> Optional[DocumentModel]:
        """Fetches a document by its unique ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE document_id = ?;",
                (document_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentModel(**dict(row))

    @staticmethod
    def get_document_by_hash(file_hash: str) -> Optional[DocumentModel]:
        """Fetches a document by its SHA-256 hash to detect duplicates."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE file_hash = ?;",
                (file_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentModel(**dict(row))

    @staticmethod
    def list_documents() -> List[DocumentModel]:
        """Returns all documents ordered by upload timestamp descending."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY upload_timestamp DESC;")
            rows = cursor.fetchall()
            return [DocumentModel(**dict(r)) for r in rows]

    @staticmethod
    def update_document_status(
        document_id: str,
        status: str,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
        summary: Optional[str] = None,
        content_snippet: Optional[str] = None,
    ) -> None:
        """Updates document status and extracted statistics."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            updates = ["processing_status = ?"]
            params = [status]

            if page_count is not None:
                updates.append("page_count = ?")
                params.append(page_count)
            if chunk_count is not None:
                updates.append("chunk_count = ?")
                params.append(chunk_count)
            if summary is not None:
                updates.append("summary = ?")
                params.append(summary)
            if content_snippet is not None:
                updates.append("content_snippet = ?")
                params.append(content_snippet)

            params.append(document_id)
            query = f"UPDATE documents SET {', '.join(updates)} WHERE document_id = ?;"
            cursor.execute(query, tuple(params))

    @staticmethod
    def delete_document(document_id: str) -> bool:
        """Deletes a document and cascades deletion to linked records."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE document_id = ?;", (document_id,))
            return cursor.rowcount > 0

    # ------------------ Index Metadata Operations ------------------

    @staticmethod
    def upsert_index_metadata(meta: IndexMetadataModel) -> None:
        """Inserts or replaces index metadata for a document."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO index_metadata (
                    document_id, index_status, index_location, embedding_model, chunk_count
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    index_status = excluded.index_status,
                    index_location = excluded.index_location,
                    embedding_model = excluded.embedding_model,
                    chunk_count = excluded.chunk_count;
                """,
                (
                    meta.document_id,
                    meta.index_status,
                    meta.index_location,
                    meta.embedding_model,
                    meta.chunk_count,
                ),
            )

    @staticmethod
    def get_index_metadata(document_id: str) -> Optional[IndexMetadataModel]:
        """Retrieves index metadata for a document."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM index_metadata WHERE document_id = ?;", (document_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return IndexMetadataModel(**dict(row))

    # ------------------ Session Operations ------------------

    @staticmethod
    def create_session(session: SessionModel) -> SessionModel:
        """Creates a new session."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (session_id, session_name, created_at, updated_at)
                VALUES (?, ?, ?, ?);
                """,
                (session.session_id, session.session_name, session.created_at, session.updated_at),
            )
        return session

    @staticmethod
    def get_session(session_id: str) -> Optional[SessionModel]:
        """Gets session by ID with linked documents."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?;", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                """
                SELECT d.* FROM documents d
                INNER JOIN session_documents sd ON d.document_id = sd.document_id
                WHERE sd.session_id = ?;
                """,
                (session_id,),
            )
            doc_rows = cursor.fetchall()
            docs = [DocumentModel(**dict(dr)) for dr in doc_rows]

            return SessionModel(
                session_id=row["session_id"],
                session_name=row["session_name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                documents=docs,
            )

    @staticmethod
    def list_sessions() -> List[SessionModel]:
        """Lists all chat sessions ordered by updated_at descending."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC;")
            rows = cursor.fetchall()

            sessions = []
            for r in rows:
                sid = r["session_id"]
                cursor.execute(
                    """
                    SELECT d.* FROM documents d
                    INNER JOIN session_documents sd ON d.document_id = sd.document_id
                    WHERE sd.session_id = ?;
                    """,
                    (sid,),
                )
                docs = [DocumentModel(**dict(dr)) for dr in cursor.fetchall()]
                sessions.append(
                    SessionModel(
                        session_id=r["session_id"],
                        session_name=r["session_name"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        documents=docs,
                    )
                )
            return sessions

    @staticmethod
    def update_session(session_id: str, session_name: Optional[str] = None, updated_at: Optional[str] = None) -> None:
        """Updates session name and/or timestamp."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if session_name:
                updates.append("session_name = ?")
                params.append(session_name)
            if updated_at:
                updates.append("updated_at = ?")
                params.append(updated_at)

            if not updates:
                return

            params.append(session_id)
            query = f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?;"
            cursor.execute(query, tuple(params))

    @staticmethod
    def link_document_to_session(session_id: str, document_id: str) -> None:
        """Links a document to a session."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO session_documents (session_id, document_id)
                VALUES (?, ?);
                """,
                (session_id, document_id),
            )

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Deletes a session and cascadingly its messages."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
            return cursor.rowcount > 0

    # ------------------ Message Operations ------------------

    @staticmethod
    def create_message(msg: MessageModel) -> MessageModel:
        """Saves a message in SQLite."""
        def _json_serializer(obj):
            if hasattr(obj, "item"):
                return obj.item()
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            try:
                return float(obj)
            except Exception:
                return str(obj)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            citation_json = (
                json.dumps([c.to_dict() for c in (msg.citations or [])], default=_json_serializer)
                if msg.citations
                else None
            )
            cursor.execute(
                """
                INSERT INTO messages (
                    message_id, session_id, role, message_content, created_at,
                    citation_metadata, thinking_process, reasoning_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    msg.message_id,
                    msg.session_id,
                    msg.role,
                    msg.message_content,
                    msg.created_at,
                    citation_json,
                    msg.thinking_process,
                    msg.reasoning_time,
                ),
            )
        return msg

    @staticmethod
    def list_messages_for_session(session_id: str) -> List[MessageModel]:
        """Retrieves all messages for a session ordered by creation time."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC;",
                (session_id,),
            )
            rows = cursor.fetchall()
            messages = []
            for r in rows:
                cits = []
                if r["citation_metadata"]:
                    try:
                        raw_cits = json.loads(r["citation_metadata"])
                        cits = [CitationModel(**c) for c in raw_cits]
                    except Exception as err:
                        logger.warning(f"Error parsing citation metadata: {err}")
                messages.append(
                    MessageModel(
                        message_id=r["message_id"],
                        session_id=r["session_id"],
                        role=r["role"],
                        message_content=r["message_content"],
                        created_at=r["created_at"],
                        citations=cits,
                        thinking_process=r["thinking_process"],
                        reasoning_time=r["reasoning_time"],
                    )
                )
            return messages

from app.database.connection import get_db_connection
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    """Initializes SQLite database tables and indexes."""
    logger.info("Initializing SQLite database tables and indexes...")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                upload_timestamp TEXT NOT NULL,
                processing_status TEXT NOT NULL,
                page_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                summary TEXT,
                content_snippet TEXT
            );
            """
        )

        # Index metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS index_metadata (
                document_id TEXT PRIMARY KEY,
                index_status TEXT NOT NULL,
                index_location TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
            );
            """
        )

        # Chat Sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                session_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Messages table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                citation_metadata TEXT,
                thinking_process TEXT,
                reasoning_time REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """
        )

        # Session-Document association table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_documents (
                session_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                PRIMARY KEY (session_id, document_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
            );
            """
        )

        # Document Summaries table (Hierarchical Page-Aware Summaries)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_summaries (
                document_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                final_summary TEXT,
                page_summaries_json TEXT,
                metadata_json TEXT,
                total_pages INTEGER DEFAULT 0,
                processed_pages INTEGER DEFAULT 0,
                failed_pages INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error_message TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
            );
            """
        )

        # Useful indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_uploaded ON documents(upload_timestamp);")

    logger.info("Database initialized successfully.")

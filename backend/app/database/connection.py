import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_db_path() -> Path:
    """Returns the absolute path to the SQLite database file."""
    settings.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    return settings.SQLITE_DB_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yields a SQLite connection with foreign keys and WAL mode enabled."""
    db_path = get_db_path()
    conn = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
        timeout=20.0,
    )
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"Database transaction rolled back due to error: {exc}")
        raise
    finally:
        conn.close()

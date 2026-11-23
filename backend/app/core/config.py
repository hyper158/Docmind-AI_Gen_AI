import json
import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application configuration and environment settings."""

    PROJECT_NAME: str = "DocMind AI - Syllabus Bot Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # OpenRouter / Nemotron Configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "nvidia/nemotron-3.5-lightning:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_REASONING_EFFORT: str = "none"
    OPENROUTER_MAX_TOKENS: int = 4096
    OPENROUTER_TEMPERATURE: float = 0.1
    OPENROUTER_TIMEOUT_SECONDS: int = 60

    # Local Embeddings & RAG
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K: int = 6
    RELEVANCE_SCORE_THRESHOLD: float = 0.05

    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOADS_DIR: Path = BASE_DIR / "storage" / "uploads"
    INDEXES_DIR: Path = BASE_DIR / "storage" / "indexes"
    METADATA_DIR: Path = BASE_DIR / "storage" / "metadata"
    SUMMARIES_DIR: Path = BASE_DIR / "storage" / "summaries"
    SQLITE_DB_PATH: Path = BASE_DIR / "storage" / "metadata" / "docmind.db"
    MAX_FILE_SIZE_MB: int = 50

    # Hierarchical Summarization Configuration
    SUMMARIZATION_CONCURRENCY_LIMIT: int = 3
    SUMMARIZATION_PAGE_CHUNK_SIZE: int = 3000
    SUMMARIZATION_PAGE_CHUNK_OVERLAP: int = 300
    SUMMARIZATION_MAX_OUTPUT_TOKENS: int = 8192
    SUMMARIZATION_TIMEOUT_SECONDS: int = 60
    SUMMARIZATION_MAX_RETRIES: int = 3
    SUMMARIZATION_RETRY_BACKOFF: float = 2.0

    # Strict Exact Fallback Messages
    NO_DOCUMENTS_UPLOADED_MSG: str = (
        "I cannot answer because no syllabus PDF has been uploaded. Please upload your study material first."
    )
    INSUFFICIENT_ANSWER_MSG: str = (
        "I couldn't find sufficient information about this topic in your uploaded document."
    )
    OUTSIDE_SYLLABUS_MSG: str = (
        "This topic is outside your uploaded syllabus. I can only answer questions based on your provided study material."
    )

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure required storage directories exist at runtime
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.INDEXES_DIR.mkdir(parents=True, exist_ok=True)
settings.METADATA_DIR.mkdir(parents=True, exist_ok=True)
settings.SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

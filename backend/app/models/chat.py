from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class CitationModel:
    """Represents a verified document citation."""

    citation_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    relevant_text_snippet: str
    relevance_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d.get("relevance_score") is not None:
            try:
                d["relevance_score"] = float(d["relevance_score"])
            except (ValueError, TypeError):
                d["relevance_score"] = None
        return d


@dataclass
class MessageModel:
    """Represents a persistent chat message."""

    message_id: str
    session_id: str
    role: str  # user | assistant
    message_content: str
    created_at: str
    citations: List[CitationModel] = None
    thinking_process: Optional[str] = None
    reasoning_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "role": self.role,
            "message_content": self.message_content,
            "created_at": self.created_at,
            "citations": [c.to_dict() for c in (self.citations or [])],
            "thinking_process": self.thinking_process,
            "reasoning_time": self.reasoning_time,
        }

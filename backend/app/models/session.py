from dataclasses import dataclass, field, asdict
from typing import List, Optional
from app.models.document import DocumentModel


@dataclass
class SessionModel:
    """Represents a chat session."""

    session_id: str
    session_name: str
    created_at: str
    updated_at: str
    documents: List[DocumentModel] = field(default_factory=list)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "documents": [d.to_dict() for d in self.documents],
        }

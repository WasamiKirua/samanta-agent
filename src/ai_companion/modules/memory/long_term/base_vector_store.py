from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Memory:
    """Represents a memory entry in the vector store."""

    text: str
    metadata: dict
    score: Optional[float] = None

    @property
    def id(self) -> Optional[str]:
        return self.metadata.get("id")

    @property
    def timestamp(self) -> Optional[datetime]:
        ts = self.metadata.get("timestamp")
        return datetime.fromisoformat(ts) if ts else None


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations."""

    @abstractmethod
    def find_similar_memory(self, text: str) -> Optional[Memory]:
        """Find if a similar memory already exists."""
        pass

    @abstractmethod
    def store_memory(self, text: str, metadata: dict) -> None:
        """Store a new memory in the vector store."""
        pass

    @abstractmethod
    def search_memories(self, query: str, k: int = 5) -> List[Memory]:
        """Search for similar memories in the vector store."""
        pass 
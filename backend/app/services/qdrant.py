"""
Qdrant client for vector search - GraphRAG regulatory documents.
"""
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
import structlog

from app.config import settings

log = structlog.get_logger()


class QdrantService:
    """Qdrant client for hybrid search (dense + sparse)."""

    def __init__(self, url: Optional[str] = None) -> None:
        self._url = url or settings.QDRANT_URL
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(url=self._url)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def health(self) -> bool:
        """Check Qdrant is reachable (for /ready)."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            log.warning("qdrant_health_failed", error=str(e))
            return False

    def ensure_collection(self, name: str = "eu_regulations", vector_size: int = 1536) -> None:
        """Create collection if not exists for regulatory embeddings."""
        try:
            self.client.get_collection(name)
        except Exception:
            self.client.create_collection(
                collection_name=name,
                vectors_config=qdrant_models.VectorParams(size=vector_size, distance=qdrant_models.Distance.COSINE),
            )
            log.info("qdrant_collection_created", collection=name)


_qdrant: Optional[QdrantService] = None


def get_qdrant() -> QdrantService:
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantService()
    return _qdrant

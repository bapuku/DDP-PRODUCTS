"""
Neo4j 5.x async driver - knowledge graph for products, supply chain, regulations.
"""
from typing import Any, Optional

from neo4j import AsyncGraphDatabase
import structlog

from app.config import settings

log = structlog.get_logger()


def _parse_auth(auth: str) -> tuple[str, str]:
    if "/" in auth:
        u, p = auth.split("/", 1)
        return u.strip(), p.strip()
    return "neo4j", auth


class Neo4jService:
    """Async Neo4j driver wrapper with connection lifecycle."""

    def __init__(
        self,
        uri: Optional[str] = None,
        auth: Optional[str] = None,
    ) -> None:
        self._uri = uri or settings.NEO4J_URI
        user, password = _parse_auth(auth or settings.NEO4J_AUTH)
        self._driver = AsyncGraphDatabase.driver(self._uri, auth=(user, password))

    async def close(self) -> None:
        await self._driver.close()

    async def verify_connectivity(self) -> bool:
        """Check that Neo4j is reachable (for /ready)."""
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception as e:
            log.warning("neo4j_connectivity_failed", error=str(e))
            return False

    async def run_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Execute a read query and return list of records as dicts."""
        parameters = parameters or {}
        async with self._driver.session() as session:
            result = await session.run(query, parameters)
            records = await result.data()
            return records


# Singleton for dependency injection
_neo4j: Optional[Neo4jService] = None


def get_neo4j() -> Neo4jService:
    global _neo4j
    if _neo4j is None:
        _neo4j = Neo4jService()
    return _neo4j

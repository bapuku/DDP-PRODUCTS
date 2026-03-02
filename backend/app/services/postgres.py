"""
PostgreSQL async connection - LangGraph checkpoints and audit log.
"""
from typing import Optional

import asyncpg
import structlog

from app.config import settings

log = structlog.get_logger()


def _get_conn_url() -> str:
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


class PostgresService:
    """Async PostgreSQL connection pool for checkpoints and audit."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    async def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                _get_conn_url(),
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def health(self) -> bool:
        """Check PostgreSQL is reachable (for /ready)."""
        try:
            p = await self.pool()
            async with p.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            log.warning("postgres_health_failed", error=str(e))
            return False


_postgres: Optional[PostgresService] = None


def get_postgres() -> PostgresService:
    global _postgres
    if _postgres is None:
        _postgres = PostgresService()
    return _postgres

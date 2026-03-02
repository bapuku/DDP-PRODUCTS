"""
Audit service - EU AI Act Article 12 record-keeping.
Append-only PostgreSQL writes, 10-year retention.
"""
from datetime import datetime, timezone
from typing import Any, Optional
import hashlib
import json
import uuid

import structlog

from app.config import settings

log = structlog.get_logger()


def _sha256(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


class AuditService:
    """Write audit entries to PostgreSQL audit_log (Article 12)."""

    async def log(
        self,
        agent_id: str,
        decision_type: str,
        input_data: Any,
        output_data: Any,
        confidence: Optional[float],
        regulatory_citations: Optional[list[str]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        regulation_ref: Optional[str] = None,
        human_override: Optional[str] = None,
    ) -> str:
        """Append one audit entry. Returns entry UUID."""
        from app.services.postgres import get_postgres

        entry_id = str(uuid.uuid4())
        postgres = get_postgres()
        try:
            pool = await postgres.pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log
                        (id, timestamp, agent_id, decision_type, input_hash, output_hash,
                         confidence_score, regulatory_citations, human_override,
                         entity_type, entity_id, operator_id, regulation_ref)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                    """,
                    entry_id,
                    datetime.now(timezone.utc),
                    agent_id,
                    decision_type,
                    _sha256(input_data),
                    _sha256(output_data),
                    confidence,
                    json.dumps(regulatory_citations or []),
                    human_override,
                    entity_type,
                    entity_id,
                    operator_id,
                    regulation_ref,
                )
            log.info("audit_written", id=entry_id, agent=agent_id, decision=decision_type)
        except Exception as e:
            log.warning("audit_write_failed", error=str(e))
        return entry_id

    async def log_creation(
        self,
        entity_type: str,
        entity_id: str,
        operator: Optional[str],
        regulation: Optional[str],
    ) -> str:
        """Convenience method for DPP creation events."""
        return await self.log(
            agent_id="api",
            decision_type="CREATE",
            input_data={"entity_type": entity_type, "entity_id": entity_id},
            output_data={"created": True},
            confidence=1.0,
            entity_type=entity_type,
            entity_id=entity_id,
            operator_id=operator,
            regulation_ref=regulation,
        )

    async def query(
        self,
        entity_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit log entries."""
        from app.services.postgres import get_postgres

        postgres = get_postgres()
        try:
            pool = await postgres.pool()
            async with pool.acquire() as conn:
                if entity_id:
                    rows = await conn.fetch(
                        "SELECT * FROM audit_log WHERE entity_id=$1 ORDER BY timestamp DESC LIMIT $2",
                        entity_id, limit,
                    )
                elif agent_id:
                    rows = await conn.fetch(
                        "SELECT * FROM audit_log WHERE agent_id=$1 ORDER BY timestamp DESC LIMIT $2",
                        agent_id, limit,
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT $1", limit
                    )
                return [dict(r) for r in rows]
        except Exception as e:
            log.warning("audit_query_failed", error=str(e))
            return []


# Singleton
_audit: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    global _audit
    if _audit is None:
        _audit = AuditService()
    return _audit

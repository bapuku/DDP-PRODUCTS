"""
Destruction agent - authorization, documentation, archival (Phase 8-9).
EU compliance: proof of destruction, audit trail.
"""
from typing import Any
from datetime import datetime, timezone

import structlog

from app.agents.state import DDPLifecycleState, DPPWorkflowState

log = structlog.get_logger()


async def destruction_agent(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Record authorized destruction: documentation and archival for lifecycle closure."""
    s = dict(state) if state else {}
    gtin = s.get("product_gtin")
    serial = s.get("serial_number")
    recycling_data = s.get("recycling_data") or {}

    destruction_record = {
        "authorized_at": datetime.now(timezone.utc).isoformat(),
        "gtin": gtin,
        "serial_number": serial,
        "reason": "eol_no_reuse",
        "facility_id": recycling_data.get("facility_id") or "DEST-EU-001",
        "proof_of_destruction_uri": None,
        "lifecycle_closed": True,
    }

    log.info(
        "destruction_recorded",
        gtin=gtin,
        lifecycle_closed=True,
    )
    return {
        "destruction_record": destruction_record,
        "current_phase": "destruction",
        "confidence_scores": {**s.get("confidence_scores", {}), "destruction": 0.90},
    }
"""
Audit trail agent - EU AI Act Article 12 record-keeping.
Immutable decision logging, citation tracking.
v3.0: Enriched for DDP Audit workflow (scope, findings, report, corrective_actions).
"""
from datetime import datetime, timezone
from typing import Any

import hashlib
import json

import structlog

from app.agents.state import DPPWorkflowState, DDPLifecycleState

log = structlog.get_logger()


def _hash_dict(d: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


async def audit_trail_agent(state: DPPWorkflowState | DDPLifecycleState) -> dict[str, Any]:
    """Append audit entry for the last agent decision (Article 12). Supports lifecycle state."""
    s = dict(state) if state else {}
    task = s.get("task_type", "unknown")
    scores = s.get("confidence_scores", {})
    agent_id = list(scores.keys())[-1] if scores else "supervisor"
    confidence = list(scores.values())[-1] if scores else 0.0
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "decision_type": task,
        "input_hash": _hash_dict({
            "query": s.get("query"),
            "gtin": s.get("product_gtin"),
            "serial": s.get("serial_number"),
        }),
        "output_hash": _hash_dict(
            s.get("regulatory_analysis") or s.get("product_data") or s.get("ddp_data") or {}
        ),
        "confidence": confidence,
        "regulatory_citations": s.get("regulation_references", []),
        "human_override": s.get("human_feedback"),
        "phase": s.get("current_phase"),
        "validation_passed": bool(s.get("validation_results") and all(
            r.get("passed") for r in (s.get("validation_results") or [])
        )) if s.get("validation_results") else None,
    }
    entries = list(s.get("audit_entries", [])) + [entry]
    log.info("audit_entry", agent_id=agent_id, decision_type=task)
    out: dict[str, Any] = {"audit_entries": entries}
    # v3.0: pass through audit workflow fields when present
    if s.get("audit_scope") is not None:
        out["audit_scope"] = s["audit_scope"]
    if s.get("audit_findings") is not None:
        out["audit_findings"] = s["audit_findings"]
    if s.get("audit_report") is not None:
        out["audit_report"] = s["audit_report"]
    if s.get("corrective_actions") is not None:
        out["corrective_actions"] = s["corrective_actions"]
    return out

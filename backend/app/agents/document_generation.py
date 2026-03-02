"""
Document generation agent - JSON-LD, XML, PDF, GS1 QR.
"""
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState

log = structlog.get_logger()


async def document_generation_agent(state: DPPWorkflowState) -> dict[str, Any]:
    """Generate DPP document (JSON-LD primary per ESPR Art. 9)."""
    # In production: render templates, QR generation
    return {
        "document_output": {
            "format": "application/ld+json",
            "dpp_uri": None,
            "qr_data": None,
        },
        "confidence_scores": {**state.get("confidence_scores", {}), "document": 0.90},
    }

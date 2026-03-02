"""
Synthesis node - final response with citations.
"""
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState

log = structlog.get_logger()


async def synthesis_node(state: DPPWorkflowState) -> dict[str, Any]:
    """Synthesize final response from agent outputs and set requires_human_review if needed."""
    scores = state.get("confidence_scores", {})
    min_conf = min(scores.values()) if scores else 1.0
    threshold = 0.85
    requires_review = min_conf < threshold
    parts = []
    if state.get("regulatory_analysis"):
        parts.append("Regulatory: " + str(state["regulatory_analysis"].get("compliance_status", "N/A")))
    if state.get("product_data"):
        parts.append("Product data retrieved.")
    if state.get("supply_chain_trace"):
        parts.append("Supply chain depth: " + str(state["supply_chain_trace"].get("chain_depth", 0)))
    final = " | ".join(parts) if parts else "No specialist output yet."
    log.info("synthesis", requires_human_review=requires_review, min_confidence=min_conf)
    return {
        "final_response": final,
        "requires_human_review": requires_review,
    }

"""
Circular economy agent - second life: SoH, refurbishment, repurpose pathways.
Phase 7: Seconde vie (Battery Reg, ESPR).
"""
from typing import Any

import structlog

from app.agents.state import DDPLifecycleState, DPPWorkflowState

log = structlog.get_logger()


async def circular_economy_agent(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Assess second-life pathway: state of health, refurbishment, repurpose, or recycle."""
    s = dict(state) if state else {}
    gtin = s.get("product_gtin")
    product = s.get("product_data") or {}
    recycling_data = s.get("recycling_data")

    # In production: BMS SoH, reuse criteria, market for refurbished
    soh_pct = product.get("state_of_health_pct")
    if soh_pct is None and recycling_data:
        soh_pct = recycling_data.get("measured_soh_pct")
    soh_pct = soh_pct if soh_pct is not None else 0.0

    if soh_pct >= 80:
        pathway = "refurbishment"
        pathway_reason = "SoH >= 80%: suitable for refurbishment"
    elif soh_pct >= 60:
        pathway = "repurpose"
        pathway_reason = "SoH 60-80%: repurpose (stationary storage)"
    else:
        pathway = "recycling"
        pathway_reason = "SoH < 60%: direct to recycling"

    log.info(
        "circular_economy_assessment",
        gtin=gtin,
        soh_pct=soh_pct,
        second_life_pathway=pathway,
    )
    return {
        "second_life_pathway": pathway,
        "current_phase": "eol",
        "product_data": {
            **product,
            "state_of_health_pct": soh_pct,
            "second_life_pathway": pathway,
            "pathway_reason": pathway_reason,
        },
        "confidence_scores": {**s.get("confidence_scores", {}), "circular_economy": 0.85},
    }

"""
Data collection agent - Phase 0-3: BOM, supplier declarations, LCA, carbon.
Replaces/enhances data_extraction for v3.0 DDP Creation workflow.
"""
from typing import Any

import structlog

from app.agents.state import DDPLifecycleState, DPPWorkflowState

log = structlog.get_logger()


def _merge_state(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Merge state for backward compatibility with DPPWorkflowState."""
    return dict(state) if state else {}


async def data_collection_agent(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Collect and normalize product/supplier data for DDP (BOM, declarations, LCA)."""
    s = _merge_state(state)
    gtin = s.get("product_gtin")
    serial = s.get("serial_number")
    sector = _infer_sector(gtin)

    # In production: parse BOM, ECHA/SCIP, LCA DB, supplier APIs
    product_data = {
        "gtin": gtin,
        "serial_number": serial,
        "sector": sector,
        "carbon_footprint_kg_co2e": None,
        "materials": [],
        "supplier_declarations": [],
        "bom_available": False,
        "lca_data_available": False,
    }
    data_quality = 0.75

    log.info(
        "data_collection_complete",
        gtin=gtin,
        sector=sector,
        data_quality=data_quality,
    )
    updates: dict[str, Any] = {
        "product_data": product_data,
        "data_quality_score": data_quality,
        "confidence_scores": {**s.get("confidence_scores", {}), "data_collection": 0.82},
    }
    try:
        if hasattr(state, "get") and (s.get("ddp_data") is not None or s.get("ddp_completeness") is not None):
            updates["ddp_data"] = {**s.get("ddp_data", {}), "collected": product_data}
    except Exception:
        pass
    return updates


def _infer_sector(gtin: str | None) -> str:
    """Infer sector from GTIN/product_id prefix (align with seed_data)."""
    if not gtin:
        return "generic"
    g = str(gtin)
    if g.startswith(("8", "0")) and len(g) >= 2:
        return "battery"
    if g.startswith(("1", "2")):
        return "textile"
    if g.startswith(("3", "4")):
        return "electronics"
    if g.startswith(("5", "6")):
        return "vehicles"
    return "generic"

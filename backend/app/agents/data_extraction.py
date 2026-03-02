"""
Data extraction agent - BOM, supplier declarations, carbon footprint.
"""
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState

log = structlog.get_logger()


async def data_extraction_agent(state: DPPWorkflowState) -> dict[str, Any]:
    """Extract and normalize compliance data from source documents."""
    # In production: parse BOM, declarations, LCA data
    confidence = 0.82
    return {
        "product_data": {
            "carbon_footprint_kg_co2e": None,
            "materials": [],
            "supplier_declarations": [],
        },
        "confidence_scores": {**state.get("confidence_scores", {}), "data_extraction": confidence},
    }

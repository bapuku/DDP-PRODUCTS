"""
Product data agent - specs, lifecycle, circularity metrics.
"""
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState

log = structlog.get_logger()


async def product_data_agent(state: DPPWorkflowState) -> dict[str, Any]:
    """Retrieve product specifications and circularity data."""
    gtin = state.get("product_gtin")
    # In production: Neo4j lookup, circularity index
    confidence = 0.85
    return {
        "product_data": {
            "gtin": gtin,
            "category": None,
            "weight_kg": None,
            "circularity_index": None,
            "expected_lifespan_years": None,
        },
        "confidence_scores": {**state.get("confidence_scores", {}), "product": confidence},
    }

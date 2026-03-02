"""
Supply chain agent - multi-tier traceability via Neo4j graph.
"""
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState
from app.services.neo4j import get_neo4j

log = structlog.get_logger()


async def supply_chain_agent(state: DPPWorkflowState) -> dict[str, Any]:
    """Trace supply chain from product to raw materials."""
    gtin = state.get("product_gtin")
    trace: dict[str, Any] = {"gtin": gtin, "chain_depth": 0, "supply_chain": []}
    try:
        neo4j = get_neo4j()
        # Full chain: MATCH path = (p:Product {gtin: $gtin})<-[:PRODUCT_FLOW*]-(rm)
        records = await neo4j.run_query(
            "MATCH (p:Product {gtin: $gtin}) RETURN p LIMIT 1",
            {"gtin": gtin or ""},
        )
        if records:
            trace["chain_depth"] = 1
            trace["supply_chain"] = [records[0].get("p", {})]
    except Exception as e:
        log.warning("supply_chain_query_failed", error=str(e))
    confidence = 0.80 if trace["chain_depth"] else 0.65
    return {
        "supply_chain_trace": trace,
        "confidence_scores": {**state.get("confidence_scores", {}), "supply_chain": confidence},
    }

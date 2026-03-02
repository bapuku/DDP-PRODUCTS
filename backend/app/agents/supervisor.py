"""
Supervisor / Orchestrator agent - task routing and quality gates.
EU AI Act Article 14: human escalation for confidence < 0.85.
"""
from typing import Any, Literal

import structlog

from app.agents.state import DPPWorkflowState, TaskType

log = structlog.get_logger()

CONFIDENCE_AUTO = 0.85
CONFIDENCE_REVIEW = 0.70


def classify_task(state: DPPWorkflowState) -> TaskType:
    """Classify query into task type for routing (can be LLM-based in production)."""
    query = (state.get("query") or "").lower()
    if "compliance" in query or "regulation" in query or "espr" in query:
        return "compliance_check"
    if "extract" in query or "bom" in query or "declaration" in query:
        return "data_extraction"
    if "product" in query or "spec" in query or "passport" in query:
        return "product_lookup"
    if "supply" in query or "chain" in query or "traceability" in query:
        return "supply_chain_trace"
    if "generate" in query or "dpp" in query or "document" in query:
        return "generate_dpp"
    if "regulation" in query or "eur-lex" in query or "article" in query:
        return "knowledge_query"
    return "compliance_check"


def route_to_specialist(state: DPPWorkflowState) -> Literal["regulatory", "product", "supply_chain", "knowledge_graph", "synthesize"]:
    """Route from supervisor to specialist agent or to synthesize when we already have results."""
    # If we already have any specialist output, go to synthesis
    if state.get("regulatory_analysis") or state.get("product_data") or state.get("supply_chain_trace") or state.get("knowledge_context"):
        return "synthesize"
    task = state.get("task_type") or classify_task(state)

    if task == "compliance_check":
        return "regulatory"
    if task == "product_lookup":
        return "product"
    if task == "supply_chain_trace":
        return "supply_chain"
    if task == "knowledge_query":
        return "knowledge_graph"
    return "synthesize"


def quality_gate(state: DPPWorkflowState) -> Literal["pass", "human_review", "retry"]:
    """EU AI Act Article 14 - quality gates."""
    scores = state.get("confidence_scores") or {}
    if not scores:
        return "pass"
    min_conf = min(scores.values()) if scores else 0.0
    if min_conf >= CONFIDENCE_AUTO:
        return "pass"
    if min_conf >= CONFIDENCE_REVIEW:
        return "retry"
    return "human_review"


async def supervisor_node(state: DPPWorkflowState) -> dict[str, Any]:
    """Supervisor: classify task and route; after specialists, decide synthesize or loop."""
    task = classify_task(state)
    updates: dict[str, Any] = {
        "task_type": task,
        "messages": [{"role": "system", "content": f"Routing to task: {task}"}],
    }
    log.info("supervisor_routing", task_type=task, query=state.get("query", "")[:80])
    return updates

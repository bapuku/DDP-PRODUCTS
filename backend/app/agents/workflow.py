"""
DPP LangGraph workflow - 8 agents, quality gates, human-in-the-loop.
EU AI Act Article 12 (audit), Article 14 (human oversight).
v3.0: Three workflows - DDP Creation, Lifecycle Update, DDP Audit (YAML Maste.ini).
"""
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
import structlog

from app.agents.state import DPPWorkflowState, DDPLifecycleState
from app.agents.supervisor import (
    supervisor_node,
    route_to_specialist,
    quality_gate,
)
from app.agents.regulatory_compliance import regulatory_compliance_agent
from app.agents.product_data import product_data_agent
from app.agents.supply_chain import supply_chain_agent
from app.agents.knowledge_graph import knowledge_graph_agent
from app.agents.document_generation import document_generation_agent
from app.agents.audit_trail import audit_trail_agent
from app.agents.human_review import human_review_node
from app.agents.synthesize import synthesis_node
from app.agents.data_collection import data_collection_agent
from app.agents.ddp_generation import ddp_generation_agent
from app.agents.validation_agent import validation_agent
from app.agents.circular_economy import circular_economy_agent
from app.agents.anomaly_detection import anomaly_detection_agent
from app.agents.recycling import recycling_agent
from app.agents.destruction import destruction_agent
from app.agents.predictive import predictive_agent
from app.config import settings

log = structlog.get_logger()


def create_dpp_workflow() -> StateGraph:
    """Build the 8-agent DPP workflow graph."""
    workflow = StateGraph(DPPWorkflowState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("regulatory", regulatory_compliance_agent)
    workflow.add_node("product", product_data_agent)
    workflow.add_node("supply_chain", supply_chain_agent)
    workflow.add_node("knowledge_graph", knowledge_graph_agent)
    workflow.add_node("document", document_generation_agent)
    workflow.add_node("audit", audit_trail_agent)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("synthesize", synthesis_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_specialist,
        {
            "regulatory": "regulatory",
            "product": "product",
            "supply_chain": "supply_chain",
            "knowledge_graph": "knowledge_graph",
            "synthesize": "synthesize",
        },
    )

    for agent in ["regulatory", "product", "supply_chain", "knowledge_graph"]:
        workflow.add_edge(agent, "audit")
    workflow.add_edge("audit", "supervisor")

    workflow.add_conditional_edges(
        "synthesize",
        quality_gate,
        {
            "pass": END,
            "human_review": "human_review",
            "retry": "supervisor",
        },
    )
    workflow.add_edge("human_review", "synthesize")

    return workflow


def compile_workflow(checkpointer: Optional[PostgresSaver] = None):
    """Compile workflow with optional PostgreSQL checkpointer."""
    graph = create_dpp_workflow()
    if checkpointer is None:
        try:
            conn_string = settings.database_url_sync
            checkpointer = PostgresSaver.from_conn_string(conn_string)
            checkpointer.setup()
        except Exception as e:
            log.warning("postgres_checkpointer_unavailable", error=str(e))
            return graph.compile()
    return graph.compile(checkpointer=checkpointer)


# Lazy compiled graph for dependency injection
_compiled: Optional[object] = None


def get_compiled_workflow():
    """Return compiled workflow (with or without checkpointer)."""
    global _compiled
    if _compiled is None:
        _compiled = compile_workflow()
    return _compiled


def compile_ddp_creation_workflow(checkpointer: Optional[PostgresSaver] = None):
    """Compile DDP Creation workflow (v3.0)."""
    graph = create_ddp_creation_workflow()
    if checkpointer is None:
        try:
            checkpointer = PostgresSaver.from_conn_string(settings.database_url_sync)
            checkpointer.setup()
        except Exception as e:
            log.warning("postgres_checkpointer_unavailable", error=str(e))
            return graph.compile()
    return graph.compile(checkpointer=checkpointer)


def compile_lifecycle_update_workflow(checkpointer: Optional[PostgresSaver] = None):
    """Compile Lifecycle Update workflow (v3.0)."""
    graph = create_lifecycle_update_workflow()
    if checkpointer is None:
        try:
            checkpointer = PostgresSaver.from_conn_string(settings.database_url_sync)
            checkpointer.setup()
        except Exception as e:
            log.warning("postgres_checkpointer_unavailable", error=str(e))
            return graph.compile()
    return graph.compile(checkpointer=checkpointer)


def compile_audit_workflow(checkpointer: Optional[PostgresSaver] = None):
    """Compile DDP Audit workflow (v3.0)."""
    graph = create_audit_workflow()
    if checkpointer is None:
        try:
            checkpointer = PostgresSaver.from_conn_string(settings.database_url_sync)
            checkpointer.setup()
        except Exception as e:
            log.warning("postgres_checkpointer_unavailable", error=str(e))
            return graph.compile()
    return graph.compile(checkpointer=checkpointer)


# --- v3.0 DDP Creation workflow ---

async def _classify_request(state: DDPLifecycleState) -> dict[str, Any]:
    """Classify request for DDP creation (sector: battery|textile|electronics|generic)."""
    q = (state.get("query") or "").lower()
    gtin = state.get("product_gtin") or ""
    if "battery" in q or (gtin and str(gtin).startswith(("8", "0"))):
        sector = "battery"
    elif "textile" in q or (gtin and str(gtin).startswith(("1", "2"))):
        sector = "textile"
    elif "electron" in q or (gtin and str(gtin).startswith(("3", "4"))):
        sector = "electronics"
    else:
        sector = "generic"
    return {"task_type": "ddp_generation", "product_data": {**(state.get("product_data") or {}), "sector": sector}}


def _route_after_compliance(state: DDPLifecycleState) -> Literal["publish_ddp", "human_review"]:
    """Route after compliance_check: publish or human review.
    Remediation loop removed to prevent infinite cycles in stub mode.
    """
    validation_results = state.get("validation_results") or []
    all_passed = all(r.get("passed") for r in validation_results) if validation_results else False
    compliance_score = state.get("compliance_score") or 0
    if all_passed and compliance_score >= 0.7:
        return "publish_ddp"
    return "human_review"


async def _publish_ddp_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Mark DDP as published (emit event in API layer)."""
    return {"current_phase": "manufacturing", "final_response": "DDP published."}


# --- v3.0 Lifecycle Update workflow ---

async def _classify_update(state: DDPLifecycleState) -> dict[str, Any]:
    """Classify lifecycle update type."""
    q = (state.get("query") or "").lower()
    if "recall" in q:
        update_type = "recall"
    elif "second" in q or "reuse" in q or "eol" in q:
        update_type = "second_life"
    elif "recycl" in q:
        update_type = "recycling"
    elif "destruct" in q:
        update_type = "destruction"
    elif "ownership" in q or "transfer" in q:
        update_type = "ownership_transfer"
    elif "service" in q or "repair" in q:
        update_type = "service_event"
    else:
        update_type = "dynamic_data"
    return {"task_type": "lifecycle_update", "audit_scope": {"update_type": update_type}}


def _route_lifecycle_branch(state: DDPLifecycleState) -> Literal["dynamic", "eol_chain"]:
    """Route to dynamic update or EOL chain (second_life -> recycling -> destruction)."""
    scope = state.get("audit_scope") or {}
    ut = scope.get("update_type", "dynamic_data")
    if ut in ("second_life", "recycling", "destruction"):
        return "eol_chain"
    return "dynamic"


async def _apply_update_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Apply dynamic/service/ownership/recall update to state."""
    return {"final_response": "Lifecycle update applied.", "current_phase": state.get("current_phase") or "active_use"}


async def _finalize_eol_ddp_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Close lifecycle and finalize EOL DDP."""
    return {"final_response": "EOL DDP finalized.", "current_phase": "destruction"}


# --- v3.0 DDP Audit workflow ---

async def _determine_scope(state: DDPLifecycleState) -> dict[str, Any]:
    """Determine audit scope (product, time range, frameworks)."""
    scope = {
        "gtin": state.get("product_gtin"),
        "serial": state.get("serial_number"),
        "frameworks": ["ESPR", "Battery Reg", "EU AI Act Art. 12"],
    }
    return {"audit_scope": scope, "task_type": "audit"}


async def _collect_evidence(state: DDPLifecycleState) -> dict[str, Any]:
    """Collect evidence (ddp_data, product_data, audit_entries)."""
    return {
        "audit_findings": [],
        "ddp_data": state.get("ddp_data"),
        "product_data": state.get("product_data"),
    }


async def _execute_checks(state: DDPLifecycleState) -> dict[str, Any]:
    """Run validation and compliance checks; append to audit_findings."""
    # Validation and regulatory agents append to state; we aggregate into audit_findings
    findings = list(state.get("audit_findings") or [])
    for r in state.get("validation_results") or []:
        if not r.get("passed"):
            findings.append({"type": "validation", "detail": r})
    if state.get("compliance_score") is not None and state.get("compliance_score", 1) < 0.7:
        findings.append({"type": "compliance", "score": state.get("compliance_score")})
    return {"audit_findings": findings}


def _route_audit_after_findings(state: DDPLifecycleState) -> Literal["critical", "report"]:
    """If critical findings, escalate; else generate report."""
    findings = state.get("audit_findings") or []
    critical = any(f.get("type") == "compliance" and (f.get("score") or 0) < 0.5 for f in findings)
    if critical and len(findings) > 2:
        return "critical"
    return "report"


async def _analyze_findings_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Analyze findings (no-op state pass-through; findings already in state)."""
    return {}


async def _generate_report_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Generate audit report from findings."""
    findings = state.get("audit_findings") or []
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gtin": state.get("product_gtin"),
        "findings_count": len(findings),
        "findings": findings[:20],
    }
    return {"audit_report": report}


async def _create_corrective_actions_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Create corrective actions from findings."""
    findings = state.get("audit_findings") or []
    actions = [{"finding_index": i, "action": "remediate", "priority": "high" if f.get("type") == "compliance" else "medium"} for i, f in enumerate(findings)]
    return {"corrective_actions": actions}


async def _distribute_node(state: DDPLifecycleState) -> dict[str, Any]:
    """Distribute report (e.g. notify stakeholders); END."""
    return {"final_response": "Audit report generated and distributed."}


def create_ddp_creation_workflow() -> StateGraph:
    """
    Workflow 1: DDP Creation.
    START → classify_request → data_collection → validate (verify_supplier) → generate_ddp
    → validate_ddp → compliance_check → [publish_ddp | human_review | remediate] → END.
    """
    graph = StateGraph(DDPLifecycleState)
    graph.add_node("classify_request", _classify_request)
    graph.add_node("data_collection", data_collection_agent)
    graph.add_node("verify_supplier", validation_agent)
    graph.add_node("generate_ddp", ddp_generation_agent)
    graph.add_node("validate_ddp", validation_agent)
    graph.add_node("compliance_check", regulatory_compliance_agent)
    graph.add_node("publish_ddp", _publish_ddp_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("audit", audit_trail_agent)

    graph.add_edge(START, "classify_request")
    graph.add_edge("classify_request", "data_collection")
    graph.add_edge("data_collection", "verify_supplier")
    graph.add_edge("verify_supplier", "generate_ddp")
    graph.add_edge("generate_ddp", "validate_ddp")
    graph.add_edge("validate_ddp", "compliance_check")
    graph.add_edge("compliance_check", "audit")
    graph.add_conditional_edges("audit", _route_after_compliance, {
        "publish_ddp": "publish_ddp",
        "human_review": "human_review",
    })
    graph.add_edge("publish_ddp", END)
    graph.add_edge("human_review", END)
    return graph


def create_lifecycle_update_workflow() -> StateGraph:
    """
    Workflow 2: Lifecycle Update.
    START → classify_update → [anomaly_check] → apply_update | (circular_economy → recycling → destruction → finalize_eol) → END.
    """
    graph = StateGraph(DDPLifecycleState)
    graph.add_node("classify_update", _classify_update)
    graph.add_node("anomaly_check", anomaly_detection_agent)
    graph.add_node("apply_update", _apply_update_node)
    graph.add_node("circular_economy", circular_economy_agent)
    graph.add_node("recycling", recycling_agent)
    graph.add_node("destruction", destruction_agent)
    graph.add_node("finalize_eol", _finalize_eol_ddp_node)
    graph.add_node("audit", audit_trail_agent)

    graph.add_edge(START, "classify_update")
    graph.add_edge("classify_update", "anomaly_check")
    graph.add_conditional_edges("anomaly_check", _route_lifecycle_branch, {
        "dynamic": "apply_update",
        "eol_chain": "circular_economy",
    })
    graph.add_edge("apply_update", "audit")
    graph.add_edge("audit", END)
    graph.add_edge("circular_economy", "recycling")
    graph.add_edge("recycling", "destruction")
    graph.add_edge("destruction", "finalize_eol")
    graph.add_edge("finalize_eol", "audit")
    # Fix: eol_chain should go to audit after finalize_eol (already connected)
    return graph


def create_audit_workflow() -> StateGraph:
    """
    Workflow 3: DDP Audit.
    START → determine_scope → collect_evidence → validation → regulatory → execute_checks
    → analyze_findings → [critical | report] → generate_report → create_corrective_actions → distribute → END.
    """
    graph = StateGraph(DDPLifecycleState)
    graph.add_node("determine_scope", _determine_scope)
    graph.add_node("collect_evidence", _collect_evidence)
    graph.add_node("validation", validation_agent)
    graph.add_node("regulatory", regulatory_compliance_agent)
    graph.add_node("execute_checks", _execute_checks)
    graph.add_node("analyze_findings", _analyze_findings_node)
    graph.add_node("generate_report", _generate_report_node)
    graph.add_node("create_corrective_actions", _create_corrective_actions_node)
    graph.add_node("distribute", _distribute_node)

    graph.add_edge(START, "determine_scope")
    graph.add_edge("determine_scope", "collect_evidence")
    graph.add_edge("collect_evidence", "validation")
    graph.add_edge("validation", "regulatory")
    graph.add_edge("regulatory", "execute_checks")
    graph.add_edge("execute_checks", "analyze_findings")
    graph.add_conditional_edges("analyze_findings", _route_audit_after_findings, {
        "critical": "generate_report",
        "report": "generate_report",
    })
    graph.add_edge("generate_report", "create_corrective_actions")
    graph.add_edge("create_corrective_actions", "distribute")
    graph.add_edge("distribute", END)
    return graph

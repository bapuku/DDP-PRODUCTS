"""
Integration tests - LangGraph workflow, supervisor routing, audit trail.
"""
import pytest
from app.agents.state import DPPWorkflowState
from app.agents.supervisor import classify_task, route_to_specialist, quality_gate


def test_classify_task_compliance():
    assert classify_task({"query": "Is this product compliant with ESPR?"}) == "compliance_check"
    assert classify_task({"query": "check regulation"}) == "compliance_check"


def test_classify_task_supply_chain():
    assert classify_task({"query": "trace supply chain for GTIN"}) == "supply_chain_trace"


def test_route_to_specialist_when_no_results():
    state: DPPWorkflowState = {"query": "compliance check", "confidence_scores": {}}
    assert route_to_specialist(state) == "regulatory"


def test_route_to_synthesize_when_has_results():
    state: DPPWorkflowState = {
        "query": "compliance",
        "regulatory_analysis": {"compliance_status": "COMPLIANT"},
    }
    assert route_to_specialist(state) == "synthesize"


def test_quality_gate_pass():
    state: DPPWorkflowState = {"confidence_scores": {"regulatory": 0.9, "product": 0.88}}
    assert quality_gate(state) == "pass"


def test_quality_gate_human_review():
    state: DPPWorkflowState = {"confidence_scores": {"regulatory": 0.65}}
    assert quality_gate(state) == "human_review"


def test_quality_gate_retry():
    state: DPPWorkflowState = {"confidence_scores": {"regulatory": 0.75}}
    assert quality_gate(state) == "retry"


@pytest.mark.asyncio
async def test_supervisor_node_returns_updates():
    from app.agents.supervisor import supervisor_node
    state: DPPWorkflowState = {"query": "compliance check", "messages": []}
    out = await supervisor_node(state)
    assert "task_type" in out
    assert out["task_type"] == "compliance_check"


@pytest.mark.asyncio
async def test_regulatory_agent_returns_confidence():
    from app.agents.regulatory_compliance import regulatory_compliance_agent
    state: DPPWorkflowState = {"query": "ESPR compliance", "confidence_scores": {}}
    out = await regulatory_compliance_agent(state)
    assert "confidence_scores" in out
    assert "regulatory" in out["confidence_scores"]
    assert out["regulatory_analysis"]["regulatory_citations"]

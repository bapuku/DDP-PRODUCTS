"""
Integration tests - human review escalation (EU AI Act Article 14).
"""
import pytest
from app.agents.state import DPPWorkflowState
from app.agents.supervisor import quality_gate, CONFIDENCE_AUTO, CONFIDENCE_REVIEW
from app.agents.synthesize import synthesis_node
from app.agents.human_review import human_review_node
from app.agents.audit_trail import audit_trail_agent


def test_quality_gate_triggers_human_review_below_review_threshold():
    state: DPPWorkflowState = {"confidence_scores": {"regulatory": 0.60}}
    assert quality_gate(state) == "human_review"


def test_quality_gate_triggers_retry_in_review_band():
    state: DPPWorkflowState = {"confidence_scores": {"regulatory": 0.77}}
    assert quality_gate(state) == "retry"


def test_quality_gate_auto_pass_at_threshold():
    state: DPPWorkflowState = {"confidence_scores": {"regulatory": CONFIDENCE_AUTO}}
    assert quality_gate(state) == "pass"


@pytest.mark.asyncio
async def test_synthesis_sets_requires_human_review_below_threshold():
    state: DPPWorkflowState = {
        "confidence_scores": {"regulatory": 0.72, "product": 0.71},
        "regulatory_analysis": {"compliance_status": "PARTIAL"},
        "requires_human_review": False,
    }
    out = await synthesis_node(state)
    assert out["requires_human_review"] is True


@pytest.mark.asyncio
async def test_synthesis_no_human_review_above_threshold():
    state: DPPWorkflowState = {
        "confidence_scores": {"regulatory": 0.90},
        "regulatory_analysis": {"compliance_status": "COMPLIANT"},
        "requires_human_review": False,
    }
    out = await synthesis_node(state)
    assert out["requires_human_review"] is False


@pytest.mark.asyncio
async def test_human_review_node_clears_flag_when_feedback_received():
    state: DPPWorkflowState = {
        "requires_human_review": True,
        "human_feedback": "Approved after manual inspection of Annex XIII compliance.",
    }
    out = await human_review_node(state)
    assert out.get("requires_human_review") is False


@pytest.mark.asyncio
async def test_human_review_node_noop_when_no_flag():
    state: DPPWorkflowState = {
        "requires_human_review": False,
        "human_feedback": None,
    }
    out = await human_review_node(state)
    assert out == {}


@pytest.mark.asyncio
async def test_audit_trail_captures_human_override():
    state: DPPWorkflowState = {
        "task_type": "compliance_check",
        "confidence_scores": {"regulatory": 0.72},
        "query": "compliance check",
        "product_gtin": "06374692674370",
        "regulatory_analysis": {"compliance_status": "PARTIAL"},
        "regulation_references": ["EU 2023/1542"],
        "human_feedback": "Human approved after review.",
        "audit_entries": [],
    }
    out = await audit_trail_agent(state)
    entries = out.get("audit_entries", [])
    assert len(entries) == 1
    entry = entries[0]
    assert entry["human_override"] == "Human approved after review."
    assert "regulatory_citations" in entry
    assert len(entry["input_hash"]) == 64

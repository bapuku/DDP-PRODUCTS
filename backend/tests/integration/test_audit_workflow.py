"""
Integration tests - DDP Audit workflow (v3.0).
determine_scope → collect_evidence → validation → regulatory → execute_checks → analyze_findings → generate_report → create_corrective_actions → distribute.
"""
import pytest

from app.agents.state import DDPLifecycleState
from app.agents.workflow import create_audit_workflow, compile_audit_workflow


@pytest.mark.asyncio
async def test_audit_workflow_graph_builds():
    graph = create_audit_workflow()
    assert graph is not None


@pytest.mark.asyncio
async def test_audit_workflow_invoke():
    compiled = compile_audit_workflow()
    initial: DDPLifecycleState = {
        "product_gtin": "01234567890123",
        "serial_number": "SN001",
        "task_type": "audit",
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "audit_findings": [],
        "requires_human_review": False,
    }
    result = await compiled.ainvoke(initial)
    assert "audit_report" in result or "audit_findings" in result or "corrective_actions" in result
    assert "final_response" in result

"""
Integration tests - DDP Creation workflow (v3.0).
START → classify_request → data_collection → verify_supplier → generate_ddp → validate_ddp → compliance_check → audit → [publish|remediate|human_review].
"""
import pytest

from app.agents.state import DDPLifecycleState
from app.agents.workflow import create_ddp_creation_workflow, compile_ddp_creation_workflow


@pytest.mark.asyncio
async def test_ddp_creation_workflow_graph_builds():
    graph = create_ddp_creation_workflow()
    assert graph is not None


@pytest.mark.asyncio
async def test_ddp_creation_workflow_invoke():
    compiled = compile_ddp_creation_workflow()
    initial: DDPLifecycleState = {
        "product_gtin": "01234567890123",
        "serial_number": "SN001",
        "query": "Create DPP",
        "task_type": "ddp_generation",
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "requires_human_review": False,
        "regulation_references": [],
        "ddp_data": {},
        "ddp_completeness": 0.0,
        "validation_results": [],
        "compliance_score": 0.0,
    }
    result = await compiled.ainvoke(initial)
    assert "ddp_uri" in result or "final_response" in result
    assert "audit_entries" in result
    assert "validation_results" in result
    assert "ddp_completeness" in result or "compliance_score" in result

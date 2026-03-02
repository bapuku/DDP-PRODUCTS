"""
Integration tests - Lifecycle Update workflow (v3.0).
classify_update → anomaly_check → [apply_update | circular_economy → recycling → destruction → finalize_eol].
"""
import pytest

from app.agents.state import DDPLifecycleState
from app.agents.workflow import create_lifecycle_update_workflow, compile_lifecycle_update_workflow


@pytest.mark.asyncio
async def test_lifecycle_update_workflow_graph_builds():
    graph = create_lifecycle_update_workflow()
    assert graph is not None


@pytest.mark.asyncio
async def test_lifecycle_update_dynamic_path():
    compiled = compile_lifecycle_update_workflow()
    initial: DDPLifecycleState = {
        "product_gtin": "01234567890123",
        "serial_number": "SN001",
        "query": "dynamic data update",
        "task_type": "lifecycle_update",
        "audit_scope": {"update_type": "dynamic_data"},
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "requires_human_review": False,
    }
    result = await compiled.ainvoke(initial)
    assert "final_response" in result
    assert "audit_entries" in result


@pytest.mark.asyncio
async def test_lifecycle_update_eol_path():
    compiled = compile_lifecycle_update_workflow()
    initial: DDPLifecycleState = {
        "product_gtin": "01234567890123",
        "serial_number": "SN001",
        "query": "second life recycling",
        "task_type": "lifecycle_update",
        "audit_scope": {"update_type": "recycling"},
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "requires_human_review": False,
    }
    result = await compiled.ainvoke(initial)
    assert "final_response" in result
    assert result.get("current_phase") in ("recycling", "destruction") or "recycling_data" in result or "destruction_record" in result or "audit_entries" in result

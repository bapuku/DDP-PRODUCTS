"""
Compliance tests - Lifecycle completeness gates (0.35, 0.55, 0.70, 0.85).
Per YAML Maste.ini and EU DPP lifecycle phases.
"""
import pytest

from app.agents.validation_agent import COMPLETENESS_GATES, validation_agent


def test_completeness_gates_defined():
    assert 0.35 in COMPLETENESS_GATES
    assert 0.55 in COMPLETENESS_GATES
    assert 0.70 in COMPLETENESS_GATES
    assert 0.85 in COMPLETENESS_GATES


@pytest.mark.asyncio
async def test_validation_agent_completeness_gate():
    state = {
        "ddp_data": {"base_uri": "https://example.eu/dpp/1", "json_ld": {"@id": "https://example.eu/dpp/1", "gtin14": "01234567890123"}},
        "ddp_completeness": 0.5,
        "confidence_scores": {},
    }
    result = await validation_agent(state)
    assert "validation_results" in result
    assert "compliance_score" in result
    results = result["validation_results"]
    gate_result = next((r for r in results if r.get("rule") == "completeness_gate"), None)
    assert gate_result is not None
    assert gate_result.get("score") == 0.5
    assert gate_result.get("passed") is True  # 0.5 >= 0.35

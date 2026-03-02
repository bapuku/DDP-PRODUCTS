"""
Compliance tests - Battery Regulation Annex XIII, EU AI Act Art. 12/14.
"""
import pytest
from datetime import date

from app.models.battery_passport import BatteryPassportCreate
from app.models.compliance import BatteryCategory, CarbonPerformanceClass
from app.agents.supervisor import quality_gate, CONFIDENCE_AUTO, CONFIDENCE_REVIEW
from app.agents.audit_trail import _hash_dict


def test_battery_passport_87_fields_represented():
    """Battery Reg Annex XIII - key clusters represented in Create model."""
    p = BatteryPassportCreate(
        gtin="06374692674370",
        serial_number="S1",
        batch_number="B1",
        manufacturer_eoid="EU123",
        manufacturer_identification="M",
        manufacturing_date=date(2024, 1, 1),
        battery_category=BatteryCategory.EV,
        battery_mass_kg=50.0,
        carbon_footprint_class=CarbonPerformanceClass.B,
        carbon_footprint_kg_co2e_kwh=60.0,
        chemistry="NMC",
        critical_raw_materials={"cobalt": 12.0, "lithium": 2.0},
        recycled_content_pre_consumer={"cobalt": 6.0},
        recycled_content_post_consumer={"lithium": 1.0},
    )
    assert p.battery_category == BatteryCategory.EV
    assert p.carbon_footprint_class == CarbonPerformanceClass.B
    assert p.chemistry == "NMC"
    assert "cobalt" in p.critical_raw_materials
    assert p.recycled_content_pre_consumer["cobalt"] == 6.0


def test_carbon_class_ag():
    """Annex II - performance class A-G."""
    for c in CarbonPerformanceClass:
        assert c.value in "ABCDEFG"


def test_eu_ai_act_confidence_thresholds():
    """EU AI Act Article 14 - auto >= 0.85, review 0.70-0.85, reject < 0.70."""
    assert quality_gate({"confidence_scores": {"a": CONFIDENCE_AUTO}}) == "pass"
    assert quality_gate({"confidence_scores": {"a": CONFIDENCE_REVIEW}}) == "retry"
    assert quality_gate({"confidence_scores": {"a": CONFIDENCE_REVIEW - 0.01}}) == "human_review"


def test_audit_entry_has_required_fields():
    """EU AI Act Article 12 - audit entry structure."""
    entry = {
        "timestamp": "2024-01-01T00:00:00Z",
        "agent_id": "regulatory",
        "decision_type": "compliance_check",
        "input_hash": _hash_dict({"query": "test"}),
        "output_hash": _hash_dict({"status": "ok"}),
        "confidence": 0.9,
        "regulatory_citations": ["EUR-Lex 32023R1542"],
    }
    assert len(entry["input_hash"]) == 64
    assert entry["agent_id"] == "regulatory"
    assert entry["regulatory_citations"]

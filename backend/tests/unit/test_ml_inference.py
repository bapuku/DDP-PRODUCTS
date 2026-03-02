"""
Unit tests - ML inference service: load models, predict_compliance.
"""
import pytest

from app.services.ml_inference import predict_compliance, _load_models


def test_predict_compliance_returns_dict():
    features = {
        "product_id": "test-1",
        "weight_kg": 1.5,
        "carbon_footprint_kg_co2e": 10.0,
        "circularity_index": 0.7,
        "ddp_completeness": 0.8,
        "sector": "battery",
    }
    out = predict_compliance(features)
    assert "espr_class" in out
    assert "rohs_class" in out
    assert "reach_class" in out
    assert "compliance_score" in out
    assert 0 <= out["compliance_score"] <= 1.0


def test_predict_compliance_minimal_features():
    out = predict_compliance({"product_id": "", "sector": "generic"})
    assert "compliance_score" in out


def test_load_models_no_crash():
    models = _load_models()
    assert isinstance(models, dict)

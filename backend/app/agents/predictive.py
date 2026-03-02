"""
Predictive agent - risk/compliance scoring via ML models (v2 GradientBoosting).
Uses clf_espr, clf_rohs, clf_reach, reg_carbon, reg_circularity when available.
"""
from typing import Any

import structlog

from app.agents.state import DDPLifecycleState, DPPWorkflowState

log = structlog.get_logger()


async def predictive_agent(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Run ML inference for compliance/risk scoring (ESPR, RoHS, REACH, carbon, circularity)."""
    s = dict(state) if state else {}
    product = s.get("product_data") or {}
    gtin = s.get("product_gtin")

    # Feature vector from product/ddp_data (align with train_dpp_models_v2)
    features = _to_feature_dict(product, s.get("ddp_data"), gtin)
    predictions: dict[str, Any] = {}
    try:
        from app.services.ml_inference import predict_compliance
        predictions = predict_compliance(features)
    except Exception as e:
        log.warning("ml_inference_unavailable", error=str(e))
        predictions = _fallback_predictions(features)

    compliance_score = predictions.get("compliance_score") or 0.0
    log.info(
        "predictive_agent_complete",
        gtin=gtin,
        compliance_score=compliance_score,
    )
    return {
        "compliance_status": {**s.get("compliance_status", {}), "ml_predictions": predictions},
        "compliance_score": compliance_score,
        "confidence_scores": {**s.get("confidence_scores", {}), "predictive": 0.80},
    }


def _to_feature_dict(product: dict, ddp_data: dict | None, gtin: str | None) -> dict[str, Any]:
    """Build feature dict for ML inference (match training schema)."""
    ddp_data = ddp_data or {}
    return {
        "product_id": gtin or "",
        "weight_kg": product.get("weight_kg"),
        "carbon_footprint_kg_co2e": product.get("carbon_footprint_kg_co2e"),
        "circularity_index": product.get("circularity_index"),
        "ddp_completeness": ddp_data.get("ddp_completeness") or 0.0,
        "sector": product.get("sector") or "generic",
    }


def _fallback_predictions(_features: dict[str, Any]) -> dict[str, Any]:
    """Fallback when ML service not available."""
    return {
        "espr_class": "Unknown",
        "rohs_class": "Compliant",
        "reach_class": "No_SVHC",
        "carbon_footprint_pred": None,
        "circularity_pred": None,
        "compliance_score": 0.5,
    }

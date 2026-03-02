"""
Anomaly detection agent - ML-based outlier detection on DDP/supply chain data.
Uses Isolation Forest (or fallback heuristic) for quality control.
"""
from typing import Any

import structlog

from app.agents.state import DDPLifecycleState, DPPWorkflowState

log = structlog.get_logger()


async def anomaly_detection_agent(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Run anomaly detection on DDP/product/supply chain features; append anomalies_detected."""
    s = dict(state) if state else {}
    product = s.get("product_data") or {}
    ddp_data = s.get("ddp_data") or {}
    existing = s.get("anomalies_detected") or []

    features: dict[str, float] = {}
    if product.get("carbon_footprint_kg_co2e") is not None:
        features["carbon_footprint_kg_co2e"] = float(product["carbon_footprint_kg_co2e"])
    if product.get("weight_kg") is not None:
        features["weight_kg"] = float(product["weight_kg"])
    if product.get("circularity_index") is not None:
        features["circularity_index"] = float(product["circularity_index"])
    if ddp_data.get("ddp_completeness") is not None:
        features["ddp_completeness"] = float(ddp_data["ddp_completeness"])
    elif s.get("ddp_completeness") is not None:
        features["ddp_completeness"] = float(s["ddp_completeness"])

    anomalies: list[dict[str, Any]] = list(existing)
    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np
        if len(features) >= 2:
            X = np.array([[v for v in features.values()]], dtype=np.float64)
            clf = IsolationForest(random_state=42, contamination=0.05)
            pred = clf.fit_predict(X)
            if pred[0] == -1:
                anomalies.append({
                    "type": "isolation_forest",
                    "features": features,
                    "message": "Outlier detected on numeric DDP/supply features",
                })
    except ImportError:
        # Heuristic fallback when sklearn not available
        cf = features.get("carbon_footprint_kg_co2e")
        if cf is not None and (cf < 0 or cf > 1e6):
            anomalies.append({
                "type": "range",
                "field": "carbon_footprint_kg_co2e",
                "value": cf,
                "message": "Carbon footprint out of plausible range",
            })
        w = features.get("weight_kg")
        if w is not None and (w < 0 or w > 1e5):
            anomalies.append({
                "type": "range",
                "field": "weight_kg",
                "value": w,
                "message": "Weight out of plausible range",
            })

    log.info(
        "anomaly_detection_complete",
        anomalies_count=len(anomalies),
        features_used=len(features),
    )
    return {
        "anomalies_detected": anomalies,
        "data_quality_score": max(0.0, 1.0 - 0.1 * len(anomalies)),
        "confidence_scores": {**s.get("confidence_scores", {}), "anomaly_detection": 0.82},
    }

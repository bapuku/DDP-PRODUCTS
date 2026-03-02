"""
ML inference service - load v2 GradientBoosting models (.pkl) and expose predictions.
EU AI Act Art. 9, 10, 12, 15. Used by predictive_agent and anomaly check API.
"""
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

_MODELS_DIR = Path(__file__).resolve().parents[2] / "data" / "models_v2"
_models: dict[str, Any] = {}


def _load_models() -> dict[str, Any]:
    """Lazy-load joblib models from data/models_v2/."""
    global _models
    if _models:
        return _models
    try:
        import joblib
    except ImportError:
        log.warning("joblib_not_installed")
        return {}
    for name in ("clf_espr", "clf_rohs", "clf_reach", "reg_carbon", "reg_circularity"):
        p = _MODELS_DIR / f"{name}.pkl"
        if p.exists():
            try:
                _models[name] = joblib.load(p)
            except Exception as e:
                log.warning("model_load_failed", model=name, error=str(e))
    return _models


def predict_compliance(features: dict[str, Any]) -> dict[str, Any]:
    """
    Run ML inference for ESPR/RoHS/REACH classification and carbon/circularity regression.
    features: product_id, weight_kg, carbon_footprint_kg_co2e, circularity_index, ddp_completeness, sector.
    """
    models = _load_models()
    # Build feature vector matching training (numeric + encoded sector)
    import numpy as np
    sector = features.get("sector") or "generic"
    sector_map = {"battery": 0, "textile": 1, "electronics": 2, "vehicles": 3, "generic": 4}
    sec_enc = sector_map.get(sector, 4)
    X = np.array([[
        float(features.get("weight_kg") or 0),
        float(features.get("carbon_footprint_kg_co2e") or 0),
        float(features.get("circularity_index") or 0),
        float(features.get("ddp_completeness") or 0),
        float(sec_enc),
    ]], dtype=np.float64)

    out: dict[str, Any] = {
        "espr_class": "Unknown",
        "rohs_class": "Compliant",
        "reach_class": "No_SVHC",
        "carbon_footprint_pred": None,
        "circularity_pred": None,
        "compliance_score": 0.5,
    }
    try:
        if "clf_espr" in models:
            out["espr_class"] = models["clf_espr"].predict(X)[0]
        if "clf_rohs" in models:
            out["rohs_class"] = models["clf_rohs"].predict(X)[0]
        if "clf_reach" in models:
            out["reach_class"] = models["clf_reach"].predict(X)[0]
        if "reg_carbon" in models:
            out["carbon_footprint_pred"] = float(models["reg_carbon"].predict(X)[0])
        if "reg_circularity" in models:
            out["circularity_pred"] = float(models["reg_circularity"].predict(X)[0])
        # Aggregate compliance score 0-1
        comp = 0.5
        if out.get("rohs_class") == "Compliant":
            comp += 0.2
        if out.get("reach_class") == "No_SVHC":
            comp += 0.2
        if out.get("espr_class") not in ("Unknown", "Exempt"):
            comp += 0.1
        out["compliance_score"] = min(1.0, comp)
    except Exception as e:
        log.warning("ml_predict_error", error=str(e))
    return out

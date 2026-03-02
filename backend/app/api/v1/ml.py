"""
ML inference API - compliance predictions via v2 GradientBoosting models.
EU AI Act Art. 9, 10, 12, 15.
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from app.services.ml_inference import predict_compliance

router = APIRouter()


class MLPredictRequest(BaseModel):
    product_id: Optional[str] = Field(None, max_length=32)
    weight_kg: Optional[float] = None
    carbon_footprint_kg_co2e: Optional[float] = None
    circularity_index: Optional[float] = None
    ddp_completeness: Optional[float] = Field(None, ge=0, le=1)
    sector: Optional[str] = Field("generic", description="battery|textile|electronics|vehicles|generic")


@router.post("/predict/compliance")
async def ml_predict_compliance(body: Optional[MLPredictRequest] = Body(None)) -> dict[str, Any]:
    """Run ML inference for ESPR/RoHS/REACH and carbon/circularity. Uses v2 models when available."""
    features = {
        "product_id": body.product_id if body else "",
        "weight_kg": body.weight_kg if body else None,
        "carbon_footprint_kg_co2e": body.carbon_footprint_kg_co2e if body else None,
        "circularity_index": body.circularity_index if body else None,
        "ddp_completeness": body.ddp_completeness if body else 0.0,
        "sector": (body.sector if body else "generic") or "generic",
    }
    try:
        return predict_compliance(features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/compliance")
async def ml_predict_compliance_get(
    sector: Optional[str] = None,
    ddp_completeness: Optional[float] = None,
) -> dict[str, Any]:
    """GET variant: predict with query params (sector, ddp_completeness)."""
    features = {
        "product_id": "",
        "weight_kg": None,
        "carbon_footprint_kg_co2e": None,
        "circularity_index": None,
        "ddp_completeness": ddp_completeness or 0.0,
        "sector": sector or "generic",
    }
    try:
        return predict_compliance(features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

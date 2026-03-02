"""
Generic DPP models for all sectors (multi-sector, ESPR Article 9).
"""
from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.dpp_base import DPPSector, validate_gtin14
from pydantic import field_validator


class DPPCreateRequest(BaseModel):
    """Create a DPP record for any sector."""
    model_config = ConfigDict(strict=True, extra="forbid")

    gtin: str = Field(..., description="GS1 GTIN-14")
    serial_number: str = Field(..., max_length=50)
    sector: DPPSector
    product_category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    manufacturing_country: Optional[str] = Field(None, max_length=100)
    manufacturing_date: Optional[date] = None
    carbon_footprint_kg_co2eq: Optional[float] = Field(None, ge=0)
    energy_efficiency_class: Optional[str] = Field(None, max_length=5)
    weight_kg: Optional[float] = Field(None, gt=0)
    recyclability_score: Optional[float] = Field(None, ge=0, le=100)
    repairability_score: Optional[float] = Field(None, ge=0, le=100)
    durability_score: Optional[float] = Field(None, ge=0, le=100)
    circularity_index: Optional[float] = Field(None, ge=0, le=100)
    recycled_content_pct: Optional[float] = Field(None, ge=0, le=100)
    expected_lifespan_years: Optional[float] = Field(None, gt=0)
    espr_compliance_status: Optional[str] = Field(None, max_length=50)
    reach_status: Optional[str] = Field(None, max_length=50)
    rohs_compliance: Optional[str] = Field(None, max_length=50)
    weee_registration: Optional[str] = Field(None, max_length=50)
    sector_data: Optional[dict[str, Any]] = Field(default_factory=dict)

    @field_validator("gtin", mode="before")
    @classmethod
    def gtin_validate(cls, v: Any) -> str:
        return validate_gtin14(str(v))


class DPPResponse(BaseModel):
    """DPP response for any sector."""
    dpp_uri: str
    gtin: str
    serial_number: str
    sector: DPPSector
    created: bool = True

"""
Base DPP model - multi-sector (ESPR Article 9).
GS1 GTIN-14 as primary product identifier.
"""
from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


def gtin14_checksum(digits: str) -> int:
    """Compute GTIN-14 check digit (ISO/IEC 15459). Weights 3,1,3,1 from right."""
    if len(digits) != 13:
        raise ValueError("GTIN-14 requires 13 digits before checksum")
    total = 0
    for k in range(13):
        # Rightmost digit (index 12) gets weight 3, next 1, etc.
        total += int(digits[12 - k]) * (3 if k % 2 == 0 else 1)
    return (10 - (total % 10)) % 10


def validate_gtin14(value: str) -> str:
    """Validate GTIN-14 length and checksum."""
    s = re.sub(r"\D", "", value)
    if len(s) == 14:
        check = int(s[13])
        expected = gtin14_checksum(s[:13])
        if check != expected:
            raise ValueError(f"Invalid GTIN-14 checksum (expected {expected})")
        return s
    if len(s) == 13:
        return s + str(gtin14_checksum(s))
    raise ValueError("GTIN-14 must be 13 or 14 digits")


class DPPSector(str, Enum):
    """Supported DPP sectors per ESPR delegated acts."""
    BATTERIES = "batteries"
    ELECTRONICS = "electronics"
    TEXTILES = "textiles"
    VEHICLES = "vehicles"
    CONSTRUCTION = "construction"
    FURNITURE = "furniture"
    PLASTICS = "plastics"
    CHEMICALS = "chemicals"


class DPPBase(BaseModel):
    """Base DPP fields - multi-sector."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(..., min_length=1, max_length=64, description="Internal product ID")
    dpp_unique_id: Optional[str] = Field(None, max_length=64)
    gtin: str = Field(..., description="GS1 GTIN-14")
    sector: DPPSector
    product_category: Optional[str] = None
    subcategory: Optional[str] = None
    manufacturing_country: Optional[str] = None
    manufacturing_date: Optional[date] = None
    carbon_footprint_kg_co2eq: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, gt=0)
    espr_compliance_status: Optional[str] = None
    reach_status: Optional[str] = None
    rohs_compliance: Optional[str] = None
    weee_registration: Optional[str] = None

    @field_validator("gtin", mode="before")
    @classmethod
    def gtin_validate(cls, v: Any) -> str:
        if isinstance(v, (int, float)):
            v = str(int(v))
        return validate_gtin14(str(v))

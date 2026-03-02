"""
Battery Passport - EU Regulation 2023/1542 Annex XIII.
87 mandatory fields across 7 clusters. GS1 Digital Link URI.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.compliance import BatteryCategory, CarbonPerformanceClass
from app.models.dpp_base import validate_gtin14
from app.models.clusters import (
    BatteryPassportCluster1,
    BatteryPassportCluster2,
    BatteryPassportCluster3,
    BatteryPassportCluster4,
    BatteryPassportCluster5,
    BatteryPassportCluster6,
    BatteryPassportCluster7Static,
    BatteryPassportCluster7Dynamic,
)


# Re-export clusters for __init__
__all_clusters = [
    "BatteryPassportCluster1",
    "BatteryPassportCluster2",
    "BatteryPassportCluster3",
    "BatteryPassportCluster4",
    "BatteryPassportCluster5",
    "BatteryPassportCluster6",
    "BatteryPassportCluster7Static",
    "BatteryPassportCluster7Dynamic",
]


def _recycled_content_2031_targets() -> dict[str, float]:
    """Battery Reg - 2031 recycled content targets (%)."""
    return {"cobalt": 12, "lithium": 4, "nickel": 4}


def _recycled_content_2036_targets() -> dict[str, float]:
    """Battery Reg - 2036 recycled content targets (%)."""
    return {"cobalt": 20, "lithium": 10, "nickel": 12}


class BatteryPassportCreate(BaseModel):
    """
    Create request for Battery DPP - Annex XIII mandatory fields.
    GS1 GTIN-14 + serial; clusters 1-7 represented.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    # Identifiers (GS1)
    gtin: str = Field(..., description="GS1 GTIN-14")
    serial_number: str = Field(..., max_length=20)
    batch_number: str = Field(..., max_length=50)

    # Cluster 1
    manufacturer_eoid: str = Field(..., max_length=50)
    manufacturer_identification: str = Field(..., max_length=255)
    manufacturing_facility_id: Optional[str] = Field(None, max_length=100)
    manufacturing_date: date
    battery_category: BatteryCategory
    battery_mass_kg: float = Field(..., gt=0)
    warranty_period_months: Optional[int] = Field(None, ge=12)

    # Cluster 2
    carbon_footprint_class: CarbonPerformanceClass

    # Cluster 3
    carbon_footprint_kg_co2e_kwh: float = Field(..., ge=0)
    raw_material_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    manufacturing_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    distribution_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    end_of_life_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    public_study_link_uri: Optional[str] = None
    absolute_footprint_kg_co2e: Optional[float] = Field(None, ge=0)

    # Cluster 4
    due_diligence_report_uri: Optional[str] = None
    management_system_docs_uri: Optional[str] = None
    risk_management_plan_uri: Optional[str] = None
    third_party_verification_uri: Optional[str] = None

    # Cluster 5
    chemistry: str = Field(..., max_length=100)
    critical_raw_materials: dict[str, float] = Field(default_factory=dict)  # material: pct
    cathode_materials: Optional[str] = None
    anode_materials: Optional[str] = None
    electrolyte_materials: Optional[str] = None
    hazardous_substances: Optional[str] = None

    # Cluster 6
    recycled_content_pre_consumer: dict[str, float] = Field(default_factory=dict)
    recycled_content_post_consumer: dict[str, float] = Field(default_factory=dict)
    renewable_content_share_pct: Optional[float] = Field(None, ge=0, le=100)
    dismantling_manual_uri: Optional[str] = None
    spare_parts_web_uri: Optional[str] = None
    take_back_points: list[str] = Field(default_factory=list)

    # Cluster 7 static (key fields)
    rated_capacity_ah: Optional[float] = Field(None, gt=0)
    certified_usable_energy_kwh: Optional[float] = Field(None, gt=0)
    expected_lifetime_years: Optional[float] = Field(None, gt=0)
    expected_cycle_life: Optional[int] = Field(None, ge=0)
    commercial_warranty_period_months: Optional[int] = Field(None, ge=0)

    @field_validator("gtin", mode="before")
    @classmethod
    def gtin_validate(cls, v: str) -> str:
        return validate_gtin14(str(v))

    def to_dpp_uri(self) -> str:
        """GS1 Digital Link URI per ESPR."""
        gtin_clean = "".join(c for c in self.gtin if c.isdigit())
        if len(gtin_clean) != 14:
            gtin_clean = gtin_clean.zfill(14)
        return f"https://id.gs1.org/01/{gtin_clean}/21/{self.serial_number}"


class BatteryPassportResponse(BaseModel):
    """Response after creating or fetching a Battery DPP."""

    model_config = ConfigDict(strict=True)

    dpp_uri: str
    gtin: str
    serial_number: str
    qr_code_data: Optional[str] = None  # Base64 PNG or data URL in Sprint 3
    created_at: datetime
    battery_category: BatteryCategory
    carbon_footprint_class: CarbonPerformanceClass
    chemistry: Optional[str] = None

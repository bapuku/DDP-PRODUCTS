"""
Battery Regulation EU 2023/1542 Annex XIII - 7 clusters.
87 mandatory fields across clusters 1-7.
"""
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.compliance import BatteryCategory, BatteryStatus, CarbonPerformanceClass


# Cluster 1: General Information (12 fields)
class BatteryPassportCluster1(BaseModel):
    """Annex XIII Cluster 1 - General Information."""
    model_config = ConfigDict(strict=True)
    battery_passport_identifier: Optional[str] = None  # UUID, item, public
    battery_serial_number: str = Field(..., max_length=50)
    batch_number: str = Field(..., max_length=50)
    economic_operator_eoid: str = Field(..., max_length=50)  # EORI
    manufacturer_identification: str = Field(..., max_length=255)
    manufacturing_facility_id: Optional[str] = Field(None, max_length=100)
    manufacturing_date: date
    date_of_putting_into_service: Optional[date] = None
    battery_category: BatteryCategory
    battery_mass_kg: float = Field(..., gt=0, description="Battery mass in kg")
    battery_status: Optional[BatteryStatus] = None
    warranty_period_months: Optional[int] = Field(None, ge=0)


# Cluster 2: Compliance & Certifications (9 fields)
class BatteryPassportCluster2(BaseModel):
    """Annex XIII Cluster 2 - Compliance & Certifications."""
    model_config = ConfigDict(strict=True)
    separate_collection_symbol_uri: Optional[str] = None  # Image
    cadmium_lead_symbols_uri: Optional[str] = None  # If applicable
    carbon_footprint_label: CarbonPerformanceClass  # A-G from Aug 2026
    extinguishing_agent: Optional[str] = Field(None, max_length=255)
    eu_declaration_of_conformity_uri: Optional[str] = None
    test_reports_reference_uri: Optional[HttpUrl] = None
    conformity_certificate: Optional[str] = Field(None, max_length=255)
    notified_body_id: Optional[str] = Field(None, max_length=50)
    labels_meaning_reference_uri: Optional[HttpUrl] = None


# Cluster 3: Carbon Footprint (8 fields)
class BatteryPassportCluster3(BaseModel):
    """Annex XIII Cluster 3 - Carbon Footprint (kgCO2e/kWh)."""
    model_config = ConfigDict(strict=True)
    total_carbon_footprint_kwh: float = Field(..., ge=0, description="kgCO2e/kWh cradle-to-gate")
    raw_material_acquisition_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    manufacturing_stage_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    distribution_stage_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    end_of_life_recycling_kg_co2e_kwh: Optional[float] = Field(None, ge=0)
    performance_class: CarbonPerformanceClass
    public_study_link_uri: Optional[HttpUrl] = None
    absolute_footprint_kg_co2e: Optional[float] = Field(None, ge=0)


# Cluster 4: Due Diligence (6 fields)
class BatteryPassportCluster4(BaseModel):
    """Annex XIII Cluster 4 - Due Diligence (Art. 49-52)."""
    model_config = ConfigDict(strict=True)
    due_diligence_report_uri: Optional[HttpUrl] = None  # Art. 52
    management_system_docs_uri: Optional[HttpUrl] = None  # Art. 49
    risk_management_plan_uri: Optional[HttpUrl] = None  # Art. 50
    third_party_verification_uri: Optional[HttpUrl] = None  # Art. 51
    recognized_scheme_assurance: Optional[str] = None
    gba_supply_chain_indices_uri: Optional[HttpUrl] = None


# Cluster 5: Materials & Composition (8 fields)
class BatteryPassportCluster5(BaseModel):
    """Annex XIII Cluster 5 - Materials & Composition."""
    model_config = ConfigDict(strict=True)
    battery_chemistry: str = Field(..., max_length=100)
    critical_raw_materials: dict[str, float] = Field(default_factory=dict)  # Co, Li, Ni, graphite %
    cathode_materials: Optional[str] = None
    anode_materials: Optional[str] = None
    electrolyte_materials: Optional[str] = None
    hazardous_substances: Optional[str] = None
    environmental_health_impact: Optional[str] = None
    detailed_composition: Optional[str] = None


# Cluster 6: Circularity (14 fields)
class BatteryPassportCluster6(BaseModel):
    """Annex XIII Cluster 6 - Circularity & resource efficiency."""
    model_config = ConfigDict(strict=True)
    pre_consumer_recycled_content_pct: dict[str, float] = Field(default_factory=dict)  # Ni, Co, Li, Pb
    post_consumer_recycled_content_pct: dict[str, float] = Field(default_factory=dict)
    renewable_content_share_pct: Optional[float] = Field(None, ge=0, le=100)
    dismantling_manual_uri: Optional[HttpUrl] = None
    disassembly_instructions_uri: Optional[HttpUrl] = None
    component_part_numbers: list[str] = Field(default_factory=list)
    spare_parts_postal_address: Optional[str] = None
    spare_parts_email: Optional[str] = None
    spare_parts_web_uri: Optional[HttpUrl] = None
    safety_handling_measures_uri: Optional[HttpUrl] = None
    waste_prevention_guidance_uri: Optional[HttpUrl] = None
    separate_collection_info_uri: Optional[HttpUrl] = None
    take_back_points: list[str] = Field(default_factory=list)
    recycling_preparation_info_uri: Optional[HttpUrl] = None


# Cluster 7: Performance & Durability (30+ fields - static + dynamic)
class BatteryPassportCluster7Static(BaseModel):
    """Annex XIII Cluster 7 - Static (model-level)."""
    model_config = ConfigDict(strict=True)
    rated_capacity_ah: Optional[float] = Field(None, gt=0)
    certified_usable_energy_kwh: Optional[float] = Field(None, gt=0)
    voltage_min_v: Optional[float] = None
    voltage_nominal_v: Optional[float] = None
    voltage_max_v: Optional[float] = None
    original_power_capability_w: Optional[float] = Field(None, ge=0)
    initial_round_trip_efficiency_pct: Optional[float] = Field(None, ge=0, le=100)
    initial_self_discharge_rate_pct_per_month: Optional[float] = Field(None, ge=0)
    internal_resistance_cell_mohm: Optional[float] = Field(None, ge=0)
    internal_resistance_pack_mohm: Optional[float] = Field(None, ge=0)
    expected_lifetime_years: Optional[float] = Field(None, gt=0)
    expected_cycle_life: Optional[int] = Field(None, ge=0)
    cycle_life_reference_test: Optional[str] = None
    c_rate_cycle_life_test: Optional[float] = None
    capacity_exhaustion_threshold_pct: Optional[float] = Field(None, ge=0, le=100)
    commercial_warranty_period_months: Optional[int] = Field(None, ge=0)
    temp_tolerance_min_c: Optional[float] = None
    temp_tolerance_max_c: Optional[float] = None
    efficiency_at_50_pct_cycle_life_pct: Optional[float] = Field(None, ge=0, le=100)


class BatteryPassportCluster7Dynamic(BaseModel):
    """Annex XIII Cluster 7 - Dynamic (BMS updated, item-level)."""
    model_config = ConfigDict(strict=True)
    capacity_fade_pct: Optional[float] = Field(None, ge=0, le=100)
    remaining_capacity_ah: Optional[float] = Field(None, ge=0)
    state_of_certified_energy_soce_pct: Optional[float] = Field(None, ge=0, le=100)
    state_of_charge_soc_pct: Optional[float] = Field(None, ge=0, le=100)
    power_fade_pct: Optional[float] = Field(None, ge=0, le=100)
    remaining_power_capability_w: Optional[float] = Field(None, ge=0)
    remaining_round_trip_efficiency_pct: Optional[float] = Field(None, ge=0, le=100)
    current_self_discharge_rate: Optional[float] = Field(None, ge=0)
    internal_resistance_increase_pct: Optional[float] = Field(None, ge=0)
    full_cycle_count: Optional[int] = Field(None, ge=0)
    capacity_throughput_ah: Optional[float] = Field(None, ge=0)
    energy_throughput_kwh: Optional[float] = Field(None, ge=0)
    extreme_temp_exposure_minutes: Optional[float] = Field(None, ge=0)
    charging_extreme_temp_minutes: Optional[float] = Field(None, ge=0)
    deep_discharge_event_count: Optional[int] = Field(None, ge=0)
    overcharge_event_count: Optional[int] = Field(None, ge=0)
    accident_information: Optional[str] = None

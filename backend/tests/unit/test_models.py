"""
Unit tests - DPP and Battery Passport models, GTIN, carbon class, recycled content.
"""
import pytest
from datetime import date
from pydantic import ValidationError

from app.models.dpp_base import DPPBase, DPPSector, validate_gtin14, gtin14_checksum
from app.models.compliance import BatteryCategory, CarbonPerformanceClass
from app.models.battery_passport import BatteryPassportCreate, BatteryPassportResponse
from app.models.clusters import (
    BatteryPassportCluster1,
    BatteryPassportCluster3,
    BatteryPassportCluster5,
    BatteryPassportCluster6,
)


def test_gtin14_checksum():
    # 13 digits -> check digit (weights 3,1,3,1 from right)
    assert gtin14_checksum("0637469267437") == 0
    assert gtin14_checksum("2541751409580") == 1


def test_validate_gtin14():
    # 0637469267437 + check 0 = 06374692674370
    assert validate_gtin14("06374692674370") == "06374692674370"
    assert validate_gtin14("0637469267437") == "06374692674370"  # 13 -> 14 with check
    with pytest.raises(ValueError, match="checksum"):
        validate_gtin14("06374692674371")  # wrong check digit
    with pytest.raises(ValueError, match="digits"):
        validate_gtin14("123")


def test_dpp_base_gtin_validation():
    m = DPPBase(product_id="P1", gtin="6374692674377", sector=DPPSector.ELECTRONICS)
    assert len(m.gtin) == 14
    assert m.sector == DPPSector.ELECTRONICS


def test_battery_passport_create_validation():
    p = BatteryPassportCreate(
        gtin="06374692674370",
        serial_number="SN001",
        batch_number="B001",
        manufacturer_eoid="EU123",
        manufacturer_identification="Acme",
        manufacturing_date=date(2024, 1, 1),
        battery_category=BatteryCategory.EV,
        battery_mass_kg=50.0,
        carbon_footprint_class=CarbonPerformanceClass.B,
        carbon_footprint_kg_co2e_kwh=60.0,
        chemistry="NMC",
    )
    assert p.to_dpp_uri().startswith("https://id.gs1.org/01/")
    assert "21/SN001" in p.to_dpp_uri()


def test_carbon_performance_class():
    for c in ["A", "B", "C", "D", "E", "F", "G"]:
        CarbonPerformanceClass(c)


def test_battery_passport_cluster1():
    c1 = BatteryPassportCluster1(
        battery_serial_number="S1",
        batch_number="B1",
        economic_operator_eoid="EORI1",
        manufacturer_identification="M1",
        manufacturing_date=date(2024, 1, 1),
        battery_category=BatteryCategory.INDUSTRIAL,
        battery_mass_kg=100.0,
    )
    assert c1.battery_mass_kg == 100.0
    assert c1.battery_category == BatteryCategory.INDUSTRIAL


def test_battery_passport_cluster3():
    c3 = BatteryPassportCluster3(
        total_carbon_footprint_kwh=55.0,
        performance_class=CarbonPerformanceClass.A,
    )
    assert c3.total_carbon_footprint_kwh == 55.0
    assert c3.performance_class == CarbonPerformanceClass.A


def test_battery_passport_cluster5_chemistry():
    c5 = BatteryPassportCluster5(battery_chemistry="NMC", critical_raw_materials={"cobalt": 10.0, "lithium": 2.0})
    assert c5.battery_chemistry == "NMC"
    assert c5.critical_raw_materials["cobalt"] == 10.0


def test_battery_passport_cluster6_recycled():
    c6 = BatteryPassportCluster6(
        pre_consumer_recycled_content_pct={"nickel": 5.0},
        post_consumer_recycled_content_pct={"cobalt": 12.0},
    )
    assert c6.pre_consumer_recycled_content_pct["nickel"] == 5.0
    assert c6.post_consumer_recycled_content_pct["cobalt"] == 12.0


def test_battery_passport_invalid_gtin():
    with pytest.raises(ValidationError):
        BatteryPassportCreate(
            gtin="123",
            serial_number="S",
            batch_number="B",
            manufacturer_eoid="E",
            manufacturer_identification="M",
            manufacturing_date=date(2024, 1, 1),
            battery_category=BatteryCategory.EV,
            battery_mass_kg=1.0,
            carbon_footprint_class=CarbonPerformanceClass.A,
            carbon_footprint_kg_co2e_kwh=1.0,
            chemistry="LFP",
        )

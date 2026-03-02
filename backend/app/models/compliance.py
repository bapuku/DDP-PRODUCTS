"""
Compliance and regulatory enums - ESPR, Battery Reg, REACH, RoHS.
"""
from enum import Enum


class ComplianceStatus(str, Enum):
    """ESPR / general compliance status."""
    FULL_COMPLIANCE = "Full_Compliance"
    PARTIAL_COMPLIANCE = "Partial_Compliance"
    TRANSITIONAL = "Transitional"
    NON_COMPLIANT = "Non_Compliant"


class BatteryCategory(str, Enum):
    """Battery Regulation - battery category (Annex XIII)."""
    EV = "EV"
    LMT = "LMT"
    INDUSTRIAL = "Industrial"
    PORTABLE = "Portable"


class CarbonPerformanceClass(str, Enum):
    """Battery Regulation Annex II - carbon footprint performance class A-G."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class BatteryStatus(str, Enum):
    """Battery status (item-level, restricted)."""
    IN_SERVICE = "in_service"
    END_OF_LIFE = "end_of_life"
    SECOND_LIFE = "second_life"
    RECYCLED = "recycled"

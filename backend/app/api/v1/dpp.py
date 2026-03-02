"""
DPP API endpoints - multi-sector.
Sprint 3 will add full CRUD and Battery Passport; here placeholder for health/routing.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_dpp_sectors() -> dict:
    """List supported DPP sectors (ESPR, Battery Reg, etc.)."""
    return {
        "sectors": [
            "batteries",
            "electronics",
            "textiles",
            "vehicles",
            "construction",
            "furniture",
            "plastics",
            "chemicals",
        ],
        "regulation_references": [
            "EU 2024/1252 (ESPR)",
            "EU 2023/1542 (Battery Regulation)",
            "EC 1907/2006 (REACH)",
            "2011/65/EU (RoHS)",
        ],
    }

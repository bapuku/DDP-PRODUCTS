"""
Compliance API - compliance-check via workflow, frameworks status.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.state import DPPWorkflowState
from app.agents.workflow import get_compiled_workflow

router = APIRouter()


class ComplianceCheckRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    product_gtin: Optional[str] = Field(None, max_length=14)


@router.get("/status")
async def compliance_status() -> dict:
    """Compliance frameworks supported by the platform."""
    return {
        "frameworks": [
            "ESPR",
            "Battery Regulation 2023/1542",
            "REACH",
            "RoHS",
            "WEEE",
            "EU AI Act 2024/1689 (Arts. 12-14)",
        ],
    }


@router.post("/check")
async def compliance_check(body: ComplianceCheckRequest) -> dict:
    """Run compliance verification via agent workflow (regulatory + product)."""
    initial: DPPWorkflowState = {
        "query": body.query,
        "product_gtin": body.product_gtin,
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "requires_human_review": False,
        "regulation_references": [],
    }
    try:
        graph = get_compiled_workflow()
        result = await graph.ainvoke(initial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {e!s}")
    return {
        "compliance_status": result.get("regulatory_analysis", {}).get("compliance_status"),
        "confidence_scores": result.get("confidence_scores", {}),
        "requires_human_review": result.get("requires_human_review", False),
        "regulation_references": result.get("regulation_references", []),
        "final_response": result.get("final_response"),
    }


# v3.0: Compliance calendar (deadlines 2025-2036)
COMPLIANCE_CALENDAR = [
    {"year": 2025, "regulation": "ESPR", "deadline": "2025-08-18", "description": "ESPR delegated acts adoption"},
    {"year": 2026, "regulation": "Battery Reg", "deadline": "2026-02-18", "description": "Battery passport mandatory (LMT, EV)"},
    {"year": 2027, "regulation": "ESPR", "deadline": "2027-01-01", "description": "First product categories DPP"},
    {"year": 2027, "regulation": "Battery Reg", "deadline": "2027-08-18", "description": "Battery passport (industrial, SLI)"},
    {"year": 2030, "regulation": "Battery Reg", "deadline": "2030-12-31", "description": "Recycled content targets"},
    {"year": 2031, "regulation": "ESPR", "deadline": "2031-01-01", "description": "Extended product categories"},
    {"year": 2035, "regulation": "Battery Reg", "deadline": "2035-12-31", "description": "Stricter recycling targets"},
    {"year": 2036, "regulation": "ESPR", "deadline": "2036-01-01", "description": "Full DPP rollout target"},
]


@router.get("/calendar")
async def compliance_calendar() -> list[dict]:
    """Regulatory compliance calendar (deadlines 2025-2036)."""
    return COMPLIANCE_CALENDAR

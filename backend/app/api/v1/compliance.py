"""
Compliance API - compliance-check via workflow, frameworks status.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from app.agents.state import DPPWorkflowState
from app.agents.workflow import get_compiled_workflow
from app.core.i18n import get_locale, t, MESSAGES

router = APIRouter()


class ComplianceCheckRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    product_gtin: Optional[str] = Field(None, max_length=14)


@router.get("/status")
async def compliance_status(request: Request, locale: str = Depends(get_locale)) -> dict:
    """Compliance frameworks supported by the platform."""
    frameworks = MESSAGES.get(locale, MESSAGES["en"])["frameworks"]
    return {"frameworks": frameworks}


@router.post("/check")
async def compliance_check(body: ComplianceCheckRequest, request: Request, locale: str = Depends(get_locale)) -> dict:
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
        detail = t("errors.compliance_check_failed", locale, detail=str(e))
        raise HTTPException(status_code=500, detail=detail)
    return {
        "compliance_status": result.get("regulatory_analysis", {}).get("compliance_status"),
        "confidence_scores": result.get("confidence_scores", {}),
        "requires_human_review": result.get("requires_human_review", False),
        "regulation_references": result.get("regulation_references", []),
        "final_response": result.get("final_response"),
    }


@router.get("/calendar")
async def compliance_calendar(request: Request, locale: str = Depends(get_locale)) -> list[dict]:
    """Regulatory compliance calendar (deadlines 2025-2036)."""
    calendar = MESSAGES.get(locale, MESSAGES["en"])["calendar"]
    return list(calendar)

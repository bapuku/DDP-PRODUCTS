"""
Regulations API — version, calendar, frameworks, SVHC, changelog, check-updates, retrain-status.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.i18n import get_locale
from app.services.regulation_db import (
    get_version,
    get_changelog,
    get_calendar,
    get_frameworks,
    get_svhc_list,
    get_rohs_exemptions,
)
from app.services.regulatory_watcher import run_check, get_last_check_result

router = APIRouter()


@router.get("/version")
async def regulations_version() -> dict[str, Any]:
    """Current regulatory database version and last update time."""
    try:
        return get_version()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/calendar")
async def regulations_calendar(locale: str = Depends(get_locale)) -> list[dict[str, Any]]:
    """Regulatory compliance calendar (deadlines)."""
    loc = "fr" if locale == "fr" else "en"
    try:
        return get_calendar(loc)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/frameworks")
async def regulations_frameworks(locale: str = Depends(get_locale)) -> dict[str, list[str]]:
    """Supported regulatory frameworks."""
    loc = "fr" if locale == "fr" else "en"
    try:
        return {"frameworks": get_frameworks(loc)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/svhc")
async def regulations_svhc() -> dict[str, Any]:
    """Current REACH SVHC Candidate List."""
    try:
        return {"svhc_list": get_svhc_list()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/rohs-exemptions")
async def regulations_rohs_exemptions() -> dict[str, Any]:
    """RoHS exemption codes and status."""
    try:
        return {"rohs_exemptions": get_rohs_exemptions()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/changelog")
async def regulations_changelog() -> list[dict[str, Any]]:
    """History of regulatory database updates."""
    try:
        return get_changelog()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


class WebhookPayload(BaseModel):
    source: str = "manual"
    changes: list[str] = []


@router.post("/check-updates")
async def regulations_check_updates() -> dict[str, Any]:
    """Force a manual regulatory check (EUR-Lex, ECHA, OJEU)."""
    try:
        result = await run_check()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def regulations_webhook(payload: WebhookPayload) -> dict[str, str]:
    """Receive external notifications (e.g. from EUR-Lex). Acknowledged only."""
    return {"status": "acknowledged", "source": payload.source}


@router.get("/watcher-status")
async def regulations_watcher_status() -> dict[str, Any]:
    """Last regulatory watcher run result (last_check, updated, changes)."""
    return get_last_check_result()


@router.get("/retrain-status")
async def regulations_retrain_status() -> dict[str, Any]:
    """Status of last ML model retraining (triggered when regulations change)."""
    try:
        from app.services.auto_retrain import get_retrain_status
        return get_retrain_status()
    except ImportError:
        return {
            "status": "not_configured",
            "last_run": None,
            "message": "Auto-retrain service not loaded",
        }

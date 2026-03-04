"""
Blockchain anchoring API — DPP integrity verification via hash chain + Merkle tree.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.i18n import get_locale, t
from app.services.blockchain import (
    anchor_dpp, verify_dpp, verify_by_hash, get_chain_status, get_anchored_list, compute_dpp_hash,
)

router = APIRouter()


class AnchorRequest(BaseModel):
    dpp_uri: str = Field(..., min_length=1)
    gtin: str = Field(..., min_length=8, max_length=14)
    serial_number: str = Field(..., min_length=1)
    dpp_data: dict[str, Any] = Field(...)


class VerifyRequest(BaseModel):
    dpp_data: dict[str, Any] = Field(...)


@router.get("/status")
async def chain_status() -> dict[str, Any]:
    """Blockchain chain status — blocks, anchored DPPs, integrity."""
    return get_chain_status()


@router.post("/anchor")
async def anchor(body: AnchorRequest) -> dict[str, Any]:
    """Anchor a DPP hash to the blockchain (SHA-256 + Merkle tree)."""
    return anchor_dpp(body.dpp_uri, body.dpp_data, body.gtin, body.serial_number)


@router.post("/verify")
async def verify(body: VerifyRequest) -> dict[str, Any]:
    """Verify DPP data integrity against blockchain anchor."""
    return verify_dpp(body.dpp_data)


@router.get("/verify/{dpp_hash}")
async def verify_hash(dpp_hash: str) -> dict[str, Any]:
    """Verify a DPP by its hash."""
    return verify_by_hash(dpp_hash)


@router.get("/anchored")
async def list_anchored(limit: int = 50) -> list[dict[str, Any]]:
    """List all blockchain-anchored DPPs."""
    return get_anchored_list(limit)


@router.post("/hash")
async def compute_hash(body: VerifyRequest) -> dict[str, str]:
    """Compute SHA-256 hash of DPP data without anchoring."""
    return {"hash": compute_dpp_hash(body.dpp_data), "algorithm": "SHA-256"}

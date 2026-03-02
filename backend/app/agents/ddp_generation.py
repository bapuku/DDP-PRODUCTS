"""
DDP generation agent - full DPP output: JSON-LD, QR, NFC payload, RFID EPC.
Phase 4: Manufacturing and generation (ESPR Art. 9, Battery Reg Annex XIII).
"""
from typing import Any

import structlog

from app.agents.state import DDPLifecycleState, DPPWorkflowState

log = structlog.get_logger()


async def ddp_generation_agent(state: DDPLifecycleState | DPPWorkflowState) -> dict[str, Any]:
    """Generate complete DDP: JSON-LD document, QR code data, NFC NDEF, RFID SGTIN-96."""
    s = dict(state) if state else {}
    gtin = s.get("product_gtin") or ""
    serial = s.get("serial_number") or ""
    product = s.get("product_data") or {}
    ddp_data = s.get("ddp_data") or {}

    base_uri = f"https://dpp.example.eu/product/{gtin}/{serial}"
    json_ld = {
        "@context": ["https://w3id.org/dpp/v1", "https://schema.org"],
        "@type": "Product",
        "@id": base_uri,
        "gtin14": gtin,
        "serialNumber": serial,
        "name": product.get("name") or f"Product {gtin}",
        "category": product.get("category"),
        "weight": product.get("weight_kg"),
        "carbonFootprint": product.get("carbon_footprint_kg_co2e"),
        "materials": product.get("materials", []),
        "compliance": s.get("compliance_status"),
    }
    qr_data = base_uri
    nfc_payload = f"urn:epc:id:sgtin:{gtin}.{serial}"
    rfid_epc = _gtin_serial_to_sgtin96(gtin, serial)

    completeness = _compute_completeness(json_ld, product)

    log.info(
        "ddp_generated",
        gtin=gtin,
        ddp_uri=base_uri,
        completeness=completeness,
    )
    return {
        "ddp_data": {**ddp_data, "json_ld": json_ld, "base_uri": base_uri},
        "ddp_uri": base_uri,
        "ddp_completeness": completeness,
        "document_output": {
            "format": "application/ld+json",
            "dpp_uri": base_uri,
            "qr_data": qr_data,
            "nfc_ndef_uri": nfc_payload,
            "rfid_epc_sgtin96": rfid_epc,
        },
        "confidence_scores": {**s.get("confidence_scores", {}), "ddp_generation": 0.90},
    }


def _gtin_serial_to_sgtin96(gtin: str, serial: str) -> str:
    """Encode GTIN-14 + serial as EPC SGTIN-96 (hex). Simplified 24 hex chars."""
    # SGTIN-96: header 8, filter 2, partition 2, company 20, item 24, serial 38 bits
    g = (gtin or "").replace(" ", "").zfill(14)
    ser = (serial or "").zfill(7)[:7]
    try:
        company = int(g[:7].lstrip("0") or "0")
        item = int(g[7:14])
        serial_int = int(ser) if ser.isdigit() else hash(ser) % (2**38)
    except (ValueError, TypeError):
        company, item, serial_int = 0, 0, 0
    # Pack to 96 bits then hex (simplified: 24 hex chars)
    val = (1 << 88) | (company << 41) | (item << 17) | serial_int
    return hex(val)[2:].zfill(24)


def _compute_completeness(json_ld: dict[str, Any], product: dict[str, Any]) -> float:
    """Compute DDP completeness score 0.0–1.0 (gates: 0.35, 0.55, 0.70, 0.85)."""
    score = 0.0
    if json_ld.get("@id"):
        score += 0.2
    if json_ld.get("gtin14"):
        score += 0.15
    if json_ld.get("name"):
        score += 0.1
    if product.get("category") is not None:
        score += 0.15
    if product.get("carbon_footprint_kg_co2e") is not None or product.get("carbonFootprint") is not None:
        score += 0.15
    if product.get("materials"):
        score += 0.15
    if json_ld.get("compliance"):
        score += 0.1
    return min(1.0, score)

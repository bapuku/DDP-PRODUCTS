"""
Standalone QR Code Generator API — generate QR/NFC/RFID data carriers for any product.
Multiple formats: PNG, SVG, base64. GS1 Digital Link compliant.
"""
from typing import Any, Optional

from fastapi import APIRouter, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.data_carriers import (
    gs1_digital_link, generate_qr_png, generate_qr_svg,
    sgtin96_hex, nfc_ndef_uri, carrier_payload, qr_data,
)
from app.services.blockchain import anchor_dpp, compute_dpp_hash

router = APIRouter()


class QRGenerateRequest(BaseModel):
    gtin: str = Field(..., min_length=8, max_length=14)
    serial_number: str = Field(..., min_length=1, max_length=50)
    product_name: Optional[str] = None
    sector: Optional[str] = None
    manufacturer: Optional[str] = None
    base_url: str = Field(default="https://dpp.example.eu")
    anchor_blockchain: bool = Field(default=False)


@router.post("/generate")
async def generate_qr(body: QRGenerateRequest) -> dict[str, Any]:
    """Generate all data carriers for a product: QR (PNG base64 + SVG), NFC NDEF, RFID SGTIN-96, GS1 Digital Link."""
    gtin = "".join(c for c in body.gtin if c.isdigit()).zfill(14)
    result = carrier_payload(gtin, body.serial_number, body.base_url)
    result["gtin"] = gtin
    result["serial_number"] = body.serial_number
    result["product_name"] = body.product_name
    result["sector"] = body.sector
    result["manufacturer"] = body.manufacturer

    if body.anchor_blockchain:
        dpp_data = {"gtin": gtin, "serial_number": body.serial_number, "product_name": body.product_name, "sector": body.sector, "dpp_uri": result["gs1_digital_link"]}
        anchor = anchor_dpp(result["gs1_digital_link"], dpp_data, gtin, body.serial_number)
        result["blockchain"] = {
            "anchored": True,
            "dpp_hash": anchor["dpp_hash"],
            "block_number": anchor["block_number"],
            "block_hash": anchor["block_hash"],
            "merkle_root": anchor["merkle_root"],
        }

    return result


@router.get("/png")
async def qr_png(
    gtin: str = Query(..., min_length=8, max_length=14),
    serial: str = Query(..., min_length=1),
    size: int = Query(default=10, ge=1, le=50),
) -> Response:
    """Download QR code as PNG image."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    data = qr_data(gtin_clean, serial)
    png = generate_qr_png(data, size=size)
    if not png:
        return Response(content=b"QR generation unavailable", status_code=503)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="dpp-qr-{gtin_clean}-{serial}.png"'},
    )


@router.get("/svg")
async def qr_svg(
    gtin: str = Query(..., min_length=8, max_length=14),
    serial: str = Query(..., min_length=1),
) -> Response:
    """Download QR code as SVG."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    data = qr_data(gtin_clean, serial)
    svg = generate_qr_svg(data)
    if not svg:
        return Response(content=b"SVG generation unavailable", status_code=503)
    return Response(
        content=svg.encode("utf-8"),
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="dpp-qr-{gtin_clean}-{serial}.svg"'},
    )


@router.get("/link")
async def digital_link(
    gtin: str = Query(..., min_length=8, max_length=14),
    serial: str = Query(..., min_length=1),
    base_url: str = Query(default="https://dpp.example.eu"),
) -> dict[str, str]:
    """Generate GS1 Digital Link URI."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    return {
        "gs1_digital_link": gs1_digital_link(gtin_clean, serial, base_url),
        "nfc_ndef_uri": nfc_ndef_uri(gtin_clean, serial, base_url),
        "rfid_epc_sgtin96": sgtin96_hex(gtin_clean, serial),
        "gtin": gtin_clean,
        "serial_number": serial,
    }

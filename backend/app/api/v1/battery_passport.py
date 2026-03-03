"""
Battery Passport API - EU Regulation 2023/1542 Annex XIII.
POST create, GET public (ESPR Art. 9(4)), PUT performance, GET QR.
"""
from datetime import datetime, timezone
from typing import Optional

import qrcode
import io
import base64
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response

from app.models.battery_passport import BatteryPassportCreate, BatteryPassportResponse
from app.services.neo4j import get_neo4j
from app.services.kafka import get_kafka
from app.core.i18n import get_locale, t

router = APIRouter()


def _serialize_passport(p: dict) -> dict:
    """Convert Neo4j node or dict to response-safe dict."""
    return {k: v for k, v in p.items() if k != "gtin" and v is not None}


@router.post("", response_model=BatteryPassportResponse)
async def create_battery_passport(passport: BatteryPassportCreate, locale: str = Depends(get_locale)):
    """Create Battery DPP per EU Regulation 2023/1542 Annex XIII. GS1 Digital Link URI, store in Neo4j."""
    dpp_uri = passport.to_dpp_uri()
    gtin_clean = "".join(c for c in passport.gtin if c.isdigit()).zfill(14)
    try:
        neo4j = get_neo4j()
        await neo4j.run_query(
            """
            MERGE (p:Product {gtin: $gtin})
            SET p.serial_number = $serial_number, p.batch_number = $batch_number,
                p.dpp_uri = $dpp_uri, p.manufacturer_eoid = $manufacturer_eoid,
                p.manufacturing_date = $manufacturing_date, p.battery_category = $battery_category,
                p.battery_mass_kg = $battery_mass_kg, p.carbon_footprint_class = $carbon_footprint_class,
                p.chemistry = $chemistry, p.sector = 'batteries', p.updated_at = datetime()
            RETURN p
            """,
            {
                "gtin": gtin_clean,
                "serial_number": passport.serial_number,
                "batch_number": passport.batch_number,
                "dpp_uri": dpp_uri,
                "manufacturer_eoid": passport.manufacturer_eoid,
                "manufacturing_date": passport.manufacturing_date.isoformat(),
                "battery_category": passport.battery_category.value,
                "battery_mass_kg": passport.battery_mass_kg,
                "carbon_footprint_class": passport.carbon_footprint_class.value,
                "chemistry": passport.chemistry,
            },
        )
    except Exception as e:
        if "already exists" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail=t("errors.duplicate_serial_gtin", locale))
        raise HTTPException(status_code=500, detail=str(e))

    try:
        get_kafka().produce(
            "dpp-lifecycle",
            key=gtin_clean,
            value=str({"event_type": "CREATED", "dpp_uri": dpp_uri, "timestamp": datetime.now(timezone.utc).isoformat()}),
        )
    except Exception:
        pass

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(dpp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return BatteryPassportResponse(
        dpp_uri=dpp_uri,
        gtin=gtin_clean,
        serial_number=passport.serial_number,
        qr_code_data=f"data:image/png;base64,{qr_b64}",
        created_at=datetime.now(timezone.utc),
        battery_category=passport.battery_category,
        carbon_footprint_class=passport.carbon_footprint_class,
        chemistry=passport.chemistry,
    )


@router.get("/{gtin}/{serial}", response_model=dict)
async def get_battery_passport(gtin: str, serial: str, lang: Optional[str] = None, locale: str = Depends(get_locale)):
    """Public endpoint per ESPR Article 9(4) - no auth. Multi-language support via query param."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    neo4j = get_neo4j()
    records = await neo4j.run_query(
        "MATCH (p:Product {gtin: $gtin}) WHERE p.serial_number = $serial RETURN p",
        {"gtin": gtin_clean, "serial": serial},
    )
    if not records or not records[0].get("p"):
        raise HTTPException(status_code=404, detail=t("errors.passport_not_found", locale))
    node = records[0]["p"]
    if isinstance(node, dict):
        return node
    if hasattr(node, "items"):
        return dict(node)
    return {"gtin": gtin_clean, "serial_number": serial}


@router.put("/{gtin}/{serial}/performance")
async def update_battery_performance(
    gtin: str,
    serial: str,
    body: dict,
):
    """Update dynamic BMS data (SoC, capacity fade, cycle count). Auth in Sprint 3."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    neo4j = get_neo4j()
    await neo4j.run_query(
        """
        MATCH (p:Product {gtin: $gtin})
        WHERE p.serial_number = $serial
        SET p.performance_updated_at = datetime(), p += $body
        RETURN p
        """,
        {"gtin": gtin_clean, "serial": serial, "body": body},
    )
    return {"status": "ok", "gtin": gtin_clean, "serial_number": serial}


@router.get("/{gtin}/{serial}/qr")
async def get_battery_passport_qr(gtin: str, serial: str):
    """Generate QR code PNG (GS1 Digital Link, ISO/IEC 18004)."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    uri = f"https://id.gs1.org/01/{gtin_clean}/21/{serial}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

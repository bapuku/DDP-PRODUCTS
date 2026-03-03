"""
Multi-sector DPP API - generic CRUD for electronics, textiles, vehicles,
construction, furniture, plastics, chemicals (ESPR Article 9).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.i18n import get_locale, t
from app.models.dpp_base import DPPSector
from app.models.dpp_sector import DPPCreateRequest, DPPResponse
from app.services.neo4j import get_neo4j
from app.services.kafka import get_kafka

router = APIRouter()


def _build_dpp_uri(gtin: str, serial: str) -> str:
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    return f"https://id.gs1.org/01/{gtin_clean}/21/{serial}"


@router.post("", response_model=DPPResponse, status_code=201)
async def create_dpp(body: DPPCreateRequest) -> DPPResponse:
    """Create a DPP for any sector (ESPR Article 9)."""
    gtin_clean = "".join(c for c in body.gtin if c.isdigit()).zfill(14)
    dpp_uri = _build_dpp_uri(gtin_clean, body.serial_number)
    try:
        neo4j = get_neo4j()
        await neo4j.run_query(
            """
            MERGE (p:Product {gtin: $gtin, serial_number: $serial})
            SET p += $props
            RETURN p
            """,
            {
                "gtin": gtin_clean,
                "serial": body.serial_number,
                "props": {
                    "dpp_uri": dpp_uri,
                    "sector": body.sector.value,
                    "product_category": body.product_category,
                    "subcategory": body.subcategory,
                    "manufacturing_country": body.manufacturing_country,
                    "manufacturing_date": body.manufacturing_date.isoformat() if body.manufacturing_date else None,
                    "carbon_footprint_kg_co2eq": body.carbon_footprint_kg_co2eq,
                    "weight_kg": body.weight_kg,
                    "espr_compliance_status": body.espr_compliance_status,
                    "reach_status": body.reach_status,
                    "rohs_compliance": body.rohs_compliance,
                    "recyclability_score": body.recyclability_score,
                    "circularity_index": body.circularity_index,
                },
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    try:
        get_kafka().produce("dpp-lifecycle", key=gtin_clean, value=f"CREATED:{dpp_uri}")
    except Exception:
        pass
    return DPPResponse(dpp_uri=dpp_uri, gtin=gtin_clean, serial_number=body.serial_number, sector=body.sector)


@router.get("/{sector}", response_model=list[dict])
async def list_dpp_by_sector(
    sector: DPPSector,
    limit: int = Query(20, ge=1, le=200),
) -> list[dict]:
    """List DPP records for a given sector from Neo4j."""
    neo4j = get_neo4j()
    records = await neo4j.run_query(
        "MATCH (p:Product {sector: $sector}) RETURN p LIMIT $limit",
        {"sector": sector.value, "limit": limit},
    )
    result = []
    for r in records:
        node = r.get("p", {})
        result.append(dict(node) if hasattr(node, "items") else node)
    return result


@router.get("/{sector}/{gtin}/{serial}", response_model=dict)
async def get_dpp(sector: DPPSector, gtin: str, serial: str, locale: str = Depends(get_locale)) -> dict:
    """Retrieve a DPP record (public per ESPR Article 9(4))."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    neo4j = get_neo4j()
    records = await neo4j.run_query(
        "MATCH (p:Product {gtin: $gtin, serial_number: $serial}) RETURN p LIMIT 1",
        {"gtin": gtin_clean, "serial": serial},
    )
    if not records or not records[0].get("p"):
        raise HTTPException(status_code=404, detail=t("errors.dpp_not_found", locale))
    node = records[0]["p"]
    return dict(node) if hasattr(node, "items") else {"gtin": gtin_clean, "serial_number": serial}


@router.get("/supply-chain/{gtin}", response_model=dict)
async def get_supply_chain(gtin: str, locale: str = Depends(get_locale)) -> dict:
    """Trace supply chain for a product (Neo4j graph traversal)."""
    gtin_clean = "".join(c for c in gtin if c.isdigit()).zfill(14)
    neo4j = get_neo4j()
    records = await neo4j.run_query(
        """
        MATCH (p:Product {gtin: $gtin})
        OPTIONAL MATCH path = (p)<-[:PRODUCT_FLOW*1..5]-(upstream)
        RETURN p, collect(upstream) as chain
        """,
        {"gtin": gtin_clean},
    )
    if not records:
        raise HTTPException(status_code=404, detail=t("errors.product_not_found", locale))
    r = records[0]
    node = r.get("p", {})
    chain = r.get("chain", [])
    return {
        "gtin": gtin_clean,
        "product": dict(node) if hasattr(node, "items") else node,
        "supply_chain_depth": len(chain),
        "upstream_nodes": [dict(c) if hasattr(c, "items") else str(c) for c in chain],
    }

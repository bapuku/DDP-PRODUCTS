"""
EUR-Lex and regulatory tools for the compliance agent.
query_eur_lex: fetch regulation text from EUR-Lex SPARQL/REST API.
check_scip_database: ECHA SVHC/SCIP lookup.
verify_rohs_exemptions: RoHS exemption status.
get_candidate_list: REACH SVHC candidate list.
map_product_category: ESPR delegated act category mapping.

Each tool returns a structured dict and is designed to be used as LangChain tools.
"""
import os
from typing import Optional

import httpx
import structlog

log = structlog.get_logger()

_TIMEOUT = 15.0
_EURLEX_BASE = "https://eur-lex.europa.eu/legal-content/EN/TXT/plain/"


async def query_eur_lex(celex_number: str, article: Optional[str] = None) -> dict:
    """
    Fetch regulation text from EUR-Lex.
    Returns {celex, title, article, text, url} or error dict.
    """
    url = f"{_EURLEX_BASE}?uri=CELEX:{celex_number}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
            text = resp.text[:5000] if resp.status_code == 200 else f"HTTP {resp.status_code}"
        # Minimal parsing: extract article section
        if article and text:
            for sep in [f"Article {article}", f"ARTICLE {article}"]:
                idx = text.find(sep)
                if idx >= 0:
                    text = text[idx: idx + 2000]
                    break
        return {"celex": celex_number, "article": article, "text": text, "url": url, "source": "EUR-Lex"}
    except Exception as e:
        log.warning("eur_lex_fetch_failed", celex=celex_number, error=str(e))
        return {"celex": celex_number, "error": str(e), "text": None}


async def check_scip_database(cas_number: str) -> dict:
    """
    Check ECHA SCIP database for SVHC status.
    SCIP API: https://echa.europa.eu/scip-database
    Returns {cas, svhc_status, svhc_name, threshold_pct, source}.
    """
    try:
        from app.services.regulation_db import get_svhc_known
        known = get_svhc_known()
    except Exception:
        known = {
            "7440-48-4": {"name": "Cobalt", "threshold_pct": 0.1, "status": "SVHC"},
            "7439-93-2": {"name": "Lithium", "threshold_pct": None, "status": "Monitored"},
            "7440-02-0": {"name": "Nickel compounds", "threshold_pct": 0.1, "status": "SVHC"},
            "117-81-7": {"name": "DEHP", "threshold_pct": 0.1, "status": "SVHC"},
            "80-05-7": {"name": "BPA", "threshold_pct": 0.1, "status": "SVHC"},
        }
    info = known.get(cas_number)
    if info:
        return {"cas": cas_number, **info, "source": "ECHA_SCIP_regulation_db"}
    # Attempt live ECHA API lookup
    try:
        url = f"https://echa.europa.eu/api/substance/cas/{cas_number}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return {"cas": cas_number, "data": resp.json(), "source": "ECHA_SCIP_API"}
    except Exception as e:
        log.debug("scip_api_failed", cas=cas_number, error=str(e))
    return {"cas": cas_number, "svhc_status": "NOT_FOUND", "source": "ECHA_SCIP"}


def verify_rohs_exemptions(exemption_code: str) -> dict:
    """
    Check RoHS exemption status and expiry (RoHS Directive 2011/65/EU Annex III/IV).
    Returns {code, description, status, expiry, applicable_categories}.
    """
    try:
        from app.services.regulation_db import get_rohs_exemptions
        exemptions = get_rohs_exemptions()
    except Exception:
        exemptions = {
            "6(c)": {"description": "Electrical and electronic components containing lead in glass or ceramic", "status": "VALID", "expiry": "2026-07-21", "applicable_categories": ["1-11"]},
            "7(c)-I": {"description": "Lead in solders for servers, storage and storage array systems", "status": "VALID", "expiry": "2025-07-21", "applicable_categories": ["11"]},
            "8(b)": {"description": "Mercury in cold cathode fluorescent lamps", "status": "EXPIRED", "expiry": "2022-01-01", "applicable_categories": ["3"]},
        }
    info = exemptions.get(exemption_code)
    if info:
        return {"code": exemption_code, **info, "source": "RoHS_Annex_III"}
    return {"code": exemption_code, "status": "UNKNOWN", "source": "RoHS_Annex_III"}


async def get_candidate_list() -> list[dict]:
    """
    Get current REACH SVHC Candidate List (regulation_db, updated by watcher).
    Returns list of {name, cas, ec, reason}.
    """
    try:
        from app.services.regulation_db import get_svhc_list
        return get_svhc_list()
    except Exception:
        pass
    # Fallback and optionally extend from live ECHA
    CANDIDATE_LIST = [
        {"name": "Cobalt", "cas": "7440-48-4", "ec": "231-158-0", "reason": "Carcinogen"},
        {"name": "Lead", "cas": "7439-92-1", "ec": "231-100-4", "reason": "Toxic"},
        {"name": "Mercury", "cas": "7439-97-6", "ec": "231-106-7", "reason": "Toxic"},
        {"name": "DEHP", "cas": "117-81-7", "ec": "204-211-0", "reason": "Reprotoxic"},
        {"name": "BPA", "cas": "80-05-7", "ec": "201-245-8", "reason": "Endocrine disruptor"},
        {"name": "Cadmium", "cas": "7440-43-9", "ec": "231-152-8", "reason": "Carcinogen"},
        {"name": "PFOA", "cas": "335-67-1", "ec": "206-397-9", "reason": "Persistent"},
    ]
    try:
        url = "https://echa.europa.eu/api/candidate-list?page=0&size=10"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("substances", data.get("content", CANDIDATE_LIST))
    except Exception:
        pass
    return CANDIDATE_LIST


def map_product_category(gtin: str) -> str:
    """
    Map GTIN prefix to ESPR delegated act product category.
    In production, use GS1 GDSN registry or internal DB.
    """
    CATEGORY_MAP = {
        "063": "electronics",
        "025": "electronics",
        "092": "electronics",
        "038": "electronics",
        "010": "batteries",
        "073": "textiles",
        "088": "vehicles",
        "041": "construction",
        "059": "plastics",
        "003": "chemicals",
    }
    prefix = gtin[:3] if len(gtin) >= 3 else gtin
    return CATEGORY_MAP.get(prefix, "electronics")

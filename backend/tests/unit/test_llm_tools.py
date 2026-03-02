"""
Unit tests for regulatory tools (EUR-Lex, SCIP, RoHS, REACH, GTIN mapping).
"""
import pytest

from app.ai.regulatory_tools import (
    verify_rohs_exemptions,
    map_product_category,
    get_candidate_list,
)


def test_rohs_exemption_valid():
    result = verify_rohs_exemptions("6(c)")
    assert result["status"] == "VALID"
    assert "lead" in result["description"].lower()
    assert result["code"] == "6(c)"


def test_rohs_exemption_unknown():
    result = verify_rohs_exemptions("99(z)")
    assert result["status"] == "UNKNOWN"


def test_rohs_exemption_expired():
    result = verify_rohs_exemptions("8(b)")
    assert result["status"] == "EXPIRED"


def test_map_product_category_electronics():
    assert map_product_category("06374692674370") == "electronics"


def test_map_product_category_fallback():
    assert map_product_category("99999999999999") == "electronics"


@pytest.mark.asyncio
async def test_get_candidate_list():
    result = await get_candidate_list()
    assert isinstance(result, list)
    assert len(result) > 0
    names = [r["name"] for r in result]
    assert "Cobalt" in names or "Lead" in names

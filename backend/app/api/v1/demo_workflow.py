"""
Demo Workflow API — run a complete DPP pipeline on 50 synthetic products.
Creates DPPs, runs compliance + anomaly detection + impact assessment,
returns structured results for browser visualization.
"""
import json
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from app.core.i18n import get_locale

router = APIRouter()

_DEMO_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "demo_products.json"

SECTOR_MAP = {"Battery": "batteries", "Electronics": "electronics", "Textile": "textiles", "Vehicle": "vehicles", "Construction": "construction", "Furniture": "furniture"}


def _load_demo_products() -> list[dict[str, Any]]:
    for p in [_DEMO_DATA_PATH, Path(__file__).resolve().parents[3] / "data" / "demo" / "demo_products.json"]:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return []


def _classify_anomaly(product: dict) -> dict[str, Any]:
    """Run heuristic anomaly checks on product data."""
    anomalies = []
    gwp = float(product.get("GWP_Total_kgCO2eq") or 0)
    weight = float(product.get("Product_Weight_kg") or 0)
    recyclability = float(product.get("Recyclability_Score_pct") or 0)
    recycled = float(product.get("Recycled_Content_pct") or 0)
    completeness = float(product.get("DPP_Completeness_Score") or 0)

    if gwp > 500000:
        anomalies.append({"type": "range", "field": "GWP_Total_kgCO2eq", "value": gwp, "severity": "high", "message": f"Carbon footprint exceptionally high ({gwp:.0f} kg CO2-eq)"})
    if gwp > 0 and weight > 0 and gwp / weight > 5000:
        anomalies.append({"type": "ratio", "field": "GWP_per_kg", "value": round(gwp / weight, 1), "severity": "medium", "message": f"Carbon intensity {gwp/weight:.0f} kg CO2/kg exceeds sector threshold"})
    if recyclability < 10 and product.get("ESPR_Applicable"):
        anomalies.append({"type": "compliance", "field": "Recyclability_Score_pct", "value": recyclability, "severity": "high", "message": f"Recyclability {recyclability}% below ESPR minimum"})
    if str(product.get("REACH_SVHC_Compliant")).lower() in ("false", "no", "0"):
        anomalies.append({"type": "compliance", "field": "REACH_SVHC_Compliant", "value": "Non-compliant", "severity": "critical", "message": "REACH SVHC non-compliance detected"})
    if str(product.get("Hazardous_Flag")).lower() in ("true", "yes", "1"):
        anomalies.append({"type": "hazard", "field": "Hazardous_Flag", "value": True, "severity": "high", "message": f"Hazardous substances present: {product.get('Hazardous_Substances', 'unknown')}"})
    if completeness > 0 and completeness < 0.5:
        anomalies.append({"type": "completeness", "field": "DPP_Completeness_Score", "value": completeness, "severity": "medium", "message": f"DPP completeness {completeness:.0%} below 50% threshold"})
    if str(product.get("Anomaly_Flag")).lower() in ("true", "yes", "1"):
        anomalies.append({"type": "dataset", "field": "Anomaly_Flag", "value": True, "severity": "medium", "message": f"Dataset anomaly: {product.get('Anomaly_Type', 'unspecified')}"})

    return {
        "count": len(anomalies),
        "anomalies": anomalies,
        "data_quality_score": max(0.0, 1.0 - 0.15 * len(anomalies)),
    }


def _compliance_check(product: dict) -> dict[str, Any]:
    """Run deterministic compliance check."""
    espr = str(product.get("ESPR_Applicable", "")).lower() in ("true", "yes", "1")
    reach = str(product.get("REACH_SVHC_Compliant", "")).lower() in ("true", "yes", "1")
    rohs = str(product.get("RoHS_Compliant", "")).lower() in ("true", "yes", "1")
    battery_reg = str(product.get("EU_Battery_Reg_Applicable", "")).lower() in ("true", "yes", "1")

    checks = {
        "ESPR": {"applicable": espr, "status": "Compliant" if espr else "Not applicable", "ref": "ESPR (EU) 2024/1781 Art. 9"},
        "REACH": {"applicable": True, "status": "Compliant" if reach else "NON-COMPLIANT", "ref": "REACH (EC) 1907/2006 Art. 33"},
        "RoHS": {"applicable": True, "status": "Compliant" if rohs else "NON-COMPLIANT", "ref": "RoHS 2011/65/EU"},
        "Battery_Reg": {"applicable": battery_reg, "status": "Compliant" if battery_reg else "Not applicable", "ref": "Battery Reg (EU) 2023/1542"},
    }
    overall = "COMPLIANT" if (reach and rohs) else "NON-COMPLIANT"
    score = sum(1 for c in checks.values() if c["status"] == "Compliant") / max(len(checks), 1)
    return {"overall": overall, "score": round(score, 2), "checks": checks}


def _impact_summary(product: dict) -> dict[str, Any]:
    """Generate impact summary from product data."""
    gwp = float(product.get("GWP_Total_kgCO2eq") or 0)
    water = float(product.get("Water_Usage_Litres") or 0)
    energy = float(product.get("Energy_Manufacturing_MJ") or 0)
    recyclability = float(product.get("Recyclability_Score_pct") or 0)
    eol_recovery = float(product.get("EoL_Recovery_Rate_pct") or 0)
    renewable = float(product.get("Renewable_Energy_Share_pct") or 0)

    if gwp <= 0:
        carbon_class = "N/A"
    elif gwp < 50000:
        carbon_class = "A"
    elif gwp < 100000:
        carbon_class = "B"
    elif gwp < 200000:
        carbon_class = "C"
    elif gwp < 400000:
        carbon_class = "D"
    elif gwp < 600000:
        carbon_class = "E"
    else:
        carbon_class = "F"

    return {
        "gwp_total": round(gwp, 1),
        "carbon_class": carbon_class,
        "water_litres": round(water, 1),
        "energy_mj": round(energy, 1),
        "recyclability_pct": round(recyclability, 1),
        "eol_recovery_pct": round(eol_recovery, 1),
        "renewable_energy_pct": round(renewable, 1),
    }


@router.post("/run")
async def run_demo_workflow(locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Execute full DPP workflow on 50 demo products: create DPP, compliance, anomaly detection, impact."""
    products = _load_demo_products()
    if not products:
        return {"error": "No demo products found", "results": []}

    results = []
    stats = {"total": len(products), "compliant": 0, "non_compliant": 0, "anomalies_total": 0, "sectors": {}, "carbon_classes": {}}

    for product in products:
        sector_raw = product.get("Sector", "generic")
        sector = SECTOR_MAP.get(sector_raw, sector_raw.lower())
        gtin = product.get("DPP_ID", f"DPP-{random.randint(10000,99999)}")
        serial = f"SN-{gtin.replace('DPP-', '')}"

        dpp_uri = f"https://id.gs1.org/01/{hashlib.md5(gtin.encode()).hexdigest()[:14]}/21/{serial}"
        completeness = float(product.get("DPP_Completeness_Score") or round(random.uniform(0.4, 0.98), 2))

        anomaly_result = _classify_anomaly(product)
        compliance_result = _compliance_check(product)
        impact = _impact_summary(product)

        blockchain_hash = hashlib.sha256(json.dumps(product, sort_keys=True, default=str).encode()).hexdigest()

        result = {
            "dpp_id": gtin,
            "product_name": product.get("Product_Name", "Unknown"),
            "sector": sector,
            "manufacturer": product.get("Manufacturer", "Unknown"),
            "country": product.get("Manufacturing_Country_ISO2", "EU"),
            "dpp_uri": dpp_uri,
            "completeness": completeness,
            "compliance": compliance_result,
            "anomalies": anomaly_result,
            "impact": impact,
            "blockchain_hash": blockchain_hash[:16] + "...",
            "lifecycle_phase": "manufacturing",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        if compliance_result["overall"] == "COMPLIANT":
            stats["compliant"] += 1
        else:
            stats["non_compliant"] += 1
        stats["anomalies_total"] += anomaly_result["count"]
        stats["sectors"][sector] = stats["sectors"].get(sector, 0) + 1
        cc = impact["carbon_class"]
        stats["carbon_classes"][cc] = stats["carbon_classes"].get(cc, 0) + 1

    stats["anomaly_rate"] = round(sum(1 for r in results if r["anomalies"]["count"] > 0) / max(len(results), 1) * 100, 1)
    stats["avg_completeness"] = round(sum(r["completeness"] for r in results) / max(len(results), 1) * 100, 1)
    stats["avg_data_quality"] = round(sum(r["anomalies"]["data_quality_score"] for r in results) / max(len(results), 1) * 100, 1)

    return {
        "workflow": "DPP Full Pipeline Demo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "results": results,
    }

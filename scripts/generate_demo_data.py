#!/usr/bin/env python3
"""
Generate curated demo data from real DATASETS for testing all platform features.

Extracts a representative subset from each sector dataset (8 sectors):
  - 5 products per sector = 40 products total
  - Picks diverse compliance statuses, countries, categories
  - Generates GTIN-14 + serial numbers for API compatibility
  - Produces demo_products.json (Neo4j seed) and demo_batteries.json (battery API)
  - Includes supply-chain relationships for graph demo

Usage:
  python scripts/generate_demo_data.py
  # Output: data/demo/demo_products.json, data/demo/demo_batteries.json, etc.
"""
import csv
import json
import os
import random
import re
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = ROOT / "DATASET"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"

SAMPLES_PER_SECTOR = 5

SECTOR_FILES = {
    "electronics":   "dpp_electronics_300k.csv",
    "batteries":     "dpp_batteries_150k.csv",
    "textiles":      "dpp_textiles_300k.csv",
    "vehicles":      "dpp_vehicles_100k.csv",
    "construction":  "dpp_construction_200k.csv",
    "furniture":     "dpp_furniture_150k.csv",
    "plastics":      "dpp_plastics_150k.csv",
    "chemicals":     "dpp_chemicals_150k.csv",
}

UNIFIED_FILE = "dpp_unified_sample_80k.csv"

COMMON_FIELDS = [
    "product_id", "dpp_unique_id", "product_category", "subcategory",
    "manufacturing_country", "manufacturing_date", "weight_kg",
    "carbon_footprint_kg_co2eq",
]

UNIFIED_EXTRA = [
    "gtin", "energy_efficiency_class", "recyclability_score", "repairability_score",
    "durability_score", "circularity_index", "recycled_content_pct",
    "expected_lifespan_years", "tier1_suppliers", "tier2_suppliers",
    "supply_chain_transparency", "espr_compliance_status", "reach_status",
    "rohs_compliance", "weee_registration", "ce_marking_status",
    "svhc_present", "conflict_minerals_status", "sector",
    "carbon_raw_materials_pct", "carbon_manufacturing_pct",
    "carbon_distribution_pct", "carbon_use_phase_pct", "carbon_end_of_life_pct",
    "annual_energy_consumption_kwh",
]

BATTERY_FIELDS = [
    "battery_chemistry", "capacity_kwh", "nominal_voltage_v",
    "carbon_footprint_total_kg_co2eq", "carbon_footprint_per_kwh",
    "carbon_performance_class", "cycle_life_80pct_dod",
    "capacity_retention_500cycles_pct", "internal_resistance_mohm",
    "round_trip_efficiency_pct", "operating_temp_min_c", "operating_temp_max_c",
    "initial_state_of_health_pct", "lithium_content_pct", "cobalt_content_pct",
    "nickel_content_pct", "graphite_content_pct", "recycled_cobalt_pct",
    "recycled_lithium_pct", "recycled_nickel_pct", "recycled_lead_pct",
    "lithium_origin_country", "cobalt_origin_country", "nickel_origin_country",
    "battery_passport_status", "supply_chain_due_diligence", "ce_marking_status",
    "recyclability_efficiency_pct", "dismantling_time_minutes",
    "second_life_compatible", "cadmium_content_ppm", "mercury_content_ppm",
]


VALID_SECTORS = {
    "batteries", "electronics", "textiles", "vehicles",
    "construction", "furniture", "plastics", "chemicals",
}

SECTOR_MAP = {
    "construction_materials": "construction",
}

BATTERY_CATEGORIES = ["EV", "LMT", "Industrial", "Portable"]
CARBON_PERF_CLASSES = ["A", "B", "C", "D", "E", "F", "G"]


def gtin14_checksum(digits13: str) -> int:
    total = 0
    for k in range(13):
        total += int(digits13[12 - k]) * (3 if k % 2 == 0 else 1)
    return (10 - (total % 10)) % 10


def normalize_gtin(val: str) -> str:
    s = re.sub(r"\D", "", str(val))
    if not s:
        return ""
    s = s[:13].zfill(13)
    return s + str(gtin14_checksum(s))


def gen_serial(sector: str, idx: int) -> str:
    prefix = sector[:3].upper()
    return f"SN-DEMO-{prefix}-{idx:04d}"


def try_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


def try_int(v):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return v


def pick_diverse_rows(filepath: str, n: int, diversity_col: str = "product_category") -> list[dict]:
    """Read CSV, group by diversity_col, pick 1 per group then fill to n."""
    rows_by_group: dict[str, list] = {}
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            key = row.get(diversity_col, "unknown")
            if key not in rows_by_group:
                rows_by_group[key] = []
            if len(rows_by_group[key]) < 20:
                rows_by_group[key].append(row)
            count += 1
            if count > 50000:
                break

    picked = []
    groups = list(rows_by_group.keys())
    random.shuffle(groups)
    for g in groups:
        if len(picked) >= n:
            break
        picked.append(random.choice(rows_by_group[g]))

    while len(picked) < n:
        g = random.choice(groups)
        candidates = [r for r in rows_by_group[g] if r not in picked]
        if candidates:
            picked.append(random.choice(candidates))
        else:
            break

    return picked[:n]


def build_product(row: dict, sector: str, idx: int, gtin_override: str = None) -> dict:
    """Build a normalized product dict from a CSV row."""
    raw = gtin_override or row.get("gtin", "")
    gtin = normalize_gtin(raw)
    if not gtin or len(gtin) != 14 or gtin == "00000000000000":
        base = str(random.randint(1000000000000, 9999999999999))[:13].zfill(13)
        gtin = base + str(gtin14_checksum(base))

    sector = SECTOR_MAP.get(sector, sector)
    if sector not in VALID_SECTORS:
        sector = "electronics"

    product = {
        "gtin": gtin,
        "serial_number": gen_serial(sector, idx),
        "sector": sector,
    }

    numeric_fields = {
        "carbon_footprint_kg_co2eq", "weight_kg", "recyclability_score",
        "repairability_score", "durability_score", "circularity_index",
        "recycled_content_pct", "expected_lifespan_years",
        "annual_energy_consumption_kwh",
        "carbon_raw_materials_pct", "carbon_manufacturing_pct",
        "carbon_distribution_pct", "carbon_use_phase_pct", "carbon_end_of_life_pct",
        "capacity_kwh", "nominal_voltage_v", "carbon_footprint_total_kg_co2eq",
        "carbon_footprint_per_kwh", "cycle_life_80pct_dod",
        "capacity_retention_500cycles_pct", "internal_resistance_mohm",
        "round_trip_efficiency_pct", "operating_temp_min_c", "operating_temp_max_c",
        "initial_state_of_health_pct", "lithium_content_pct", "cobalt_content_pct",
        "nickel_content_pct", "graphite_content_pct", "recycled_cobalt_pct",
        "recycled_lithium_pct", "recycled_nickel_pct", "recycled_lead_pct",
        "recyclability_efficiency_pct", "dismantling_time_minutes",
        "cadmium_content_ppm", "mercury_content_ppm",
        "wood_content_pct", "metal_content_pct", "textile_content_pct",
        "foam_content_pct", "plastic_content_pct", "glass_content_pct",
        "recycled_content_pct", "bio_based_content_pct",
        "voc_content_g_l", "ph_value", "flash_point_celsius",
        "carbon_per_kg_polymer", "design_for_recycling_score",
        "service_life_years", "water_consumption_liters_kg",
        "microplastic_release_fibers_wash", "wash_cycles_durability",
        "dimensional_stability_pct", "formaldehyde_ppm",
        "steel_content_pct", "aluminum_content_pct", "plastics_content_pct",
        "electronics_content_pct", "rubber_content_pct",
        "recycled_steel_pct", "recycled_aluminum_pct", "recycled_plastics_pct",
        "total_recycled_content_pct", "recyclability_pct", "recoverability_pct",
        "battery_capacity_kwh", "co2_emissions_g_km",
    }
    int_fields = {"tier1_suppliers", "tier2_suppliers"}

    for k, v in row.items():
        if v is None or str(v).strip() == "":
            continue
        v = str(v).strip()
        if k == "gtin":
            continue
        if k in numeric_fields:
            product[k] = try_float(v)
        elif k in int_fields:
            product[k] = try_int(v)
        else:
            product[k] = v

    return product


def build_supply_chain(products: list[dict]) -> list[dict]:
    """Generate supply-chain edges for graph demo (PRODUCT_FLOW relationships)."""
    edges = []
    suppliers = [
        {"name": "RhineSteel GmbH", "country": "Germany", "type": "raw_materials"},
        {"name": "Shenzhen MicroTech", "country": "China", "type": "components"},
        {"name": "Samsung SDI", "country": "South Korea", "type": "batteries"},
        {"name": "BASF Chemicals", "country": "Germany", "type": "chemicals"},
        {"name": "Lenzing AG", "country": "Austria", "type": "fibers"},
        {"name": "ArcelorMittal", "country": "Luxembourg", "type": "steel"},
        {"name": "Umicore NV", "country": "Belgium", "type": "recycling"},
        {"name": "EcoTransport SA", "country": "France", "type": "logistics"},
    ]
    for p in products:
        n_suppliers = random.randint(1, 3)
        chosen = random.sample(suppliers, n_suppliers)
        for s in chosen:
            edges.append({
                "from_gtin": p["gtin"],
                "to_supplier": s["name"],
                "supplier_country": s["country"],
                "relationship": "SUPPLIED_BY",
                "supply_type": s["type"],
                "tier": random.choice([1, 2]),
            })
    return edges


def build_battery_api_payloads(battery_products: list[dict]) -> list[dict]:
    """Build battery passport API request bodies from battery demo products."""
    payloads = []
    for bp in battery_products:
        mfg_date = bp.get("manufacturing_date", "2024-06-15")
        if isinstance(mfg_date, str) and len(mfg_date) >= 10:
            mfg_date = mfg_date[:10]
        else:
            mfg_date = "2024-06-15"

        cat = bp.get("product_category", "Industrial")
        if cat not in BATTERY_CATEGORIES:
            cat = "Industrial"
        perf_class = bp.get("carbon_performance_class", "B")
        if perf_class not in CARBON_PERF_CLASSES:
            perf_class = "C"

        payload = {
            "gtin": bp["gtin"],
            "serial_number": bp["serial_number"],
            "batch_number": f"BATCH-DEMO-{random.randint(1000, 9999)}",
            "manufacturer_eoid": f"EOID-{random.randint(100000, 999999)}",
            "manufacturer_identification": random.choice([
                "CATL Battery Co.", "Samsung SDI", "LG Energy Solution",
                "Northvolt AB", "BYD Co.", "Panasonic Energy",
            ]),
            "manufacturing_date": mfg_date,
            "battery_category": cat,
            "battery_mass_kg": max(0.1, try_float(bp.get("weight_kg", 25.0))),
            "carbon_footprint_class": perf_class,
            "carbon_footprint_kg_co2e_kwh": max(0.1, try_float(bp.get("carbon_footprint_per_kwh", 45.0))),
            "chemistry": bp.get("battery_chemistry", "NMC"),
            "critical_raw_materials": ["lithium", "cobalt", "nickel"],
            "recycled_content_pre_consumer": max(0, try_float(bp.get("recycled_cobalt_pct", 5.0))),
            "recycled_content_post_consumer": max(0, try_float(bp.get("recycled_lithium_pct", 3.0))),
            "take_back_points": [
                {"name": "Berlin Collection Center", "address": "Alexanderplatz 1, 10178 Berlin"},
                {"name": "Paris Recycling Hub", "address": "15 Rue de Rivoli, 75001 Paris"},
            ],
        }
        if bp.get("capacity_kwh"):
            payload["rated_capacity_ah"] = round(bp["capacity_kwh"] * 1000 / 48, 1)
            payload["certified_usable_energy_kwh"] = round(bp["capacity_kwh"] * 0.95, 2)
        if bp.get("expected_lifespan_years"):
            payload["expected_lifetime_years"] = try_int(bp["expected_lifespan_years"])
        if bp.get("cycle_life_80pct_dod"):
            payload["expected_cycle_life"] = try_int(bp["cycle_life_80pct_dod"])
        payloads.append(payload)
    return payloads


def build_compliance_test_queries() -> list[dict]:
    """Pre-built compliance check queries for testing."""
    return [
        {"query": "Check ESPR compliance for a smartphone manufactured in China with carbon footprint 45 kg CO2eq",
         "product_gtin": None},
        {"query": "Is this textile product REACH compliant? Contains 0.05% SVHC substances",
         "product_gtin": None},
        {"query": "Verify RoHS compliance for electronic component with lead content 0.08%",
         "product_gtin": None},
        {"query": "Battery regulation compliance check for EV battery with 60kWh capacity, NMC chemistry",
         "product_gtin": None},
        {"query": "Construction product CE marking requirements under CPR for insulation material",
         "product_gtin": None},
    ]


def build_ml_test_inputs() -> list[dict]:
    """Test inputs for ML prediction endpoint."""
    return [
        {"sector": "electronics", "weight_kg": 0.8, "carbon_footprint_kg_co2e": 35.0,
         "circularity_index": 72.0, "ddp_completeness": 0.85},
        {"sector": "batteries", "weight_kg": 350.0, "carbon_footprint_kg_co2e": 4500.0,
         "circularity_index": 55.0, "ddp_completeness": 0.92},
        {"sector": "textiles", "weight_kg": 0.3, "carbon_footprint_kg_co2e": 8.5,
         "circularity_index": 40.0, "ddp_completeness": 0.70},
        {"sector": "construction", "weight_kg": 25.0, "carbon_footprint_kg_co2e": 120.0,
         "circularity_index": 60.0, "ddp_completeness": 0.80},
        {"sector": "plastics", "weight_kg": 1.2, "carbon_footprint_kg_co2e": 5.0,
         "circularity_index": 30.0, "ddp_completeness": 0.65},
    ]


def build_lifecycle_test_inputs(products: list[dict]) -> list[dict]:
    """Test inputs for lifecycle create/update endpoints."""
    actions = []
    for p in products[:8]:
        actions.append({
            "action": "create",
            "endpoint": "POST /api/v1/dpp/lifecycle/create",
            "body": {
                "product_gtin": p["gtin"],
                "serial_number": p["serial_number"],
                "query": f"Create DPP for {p.get('product_category', 'product')} "
                         f"from {p.get('manufacturing_country', 'EU')}",
            },
        })
    for p in products[:3]:
        actions.append({
            "action": "update",
            "endpoint": f"PUT /api/v1/dpp/lifecycle/{p['gtin']}/{p['serial_number']}/update",
            "body": {
                "update_type": "maintenance",
                "query": "Routine maintenance performed, firmware updated",
            },
        })
    return actions


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_products = []
    battery_products = []

    print("=" * 80)
    print("  EU DPP DEMO DATA GENERATOR")
    print("=" * 80)

    # 1. Extract from unified dataset (has all fields including GTIN)
    unified_path = DATASET_DIR / UNIFIED_FILE
    if unified_path.exists():
        print(f"\n[UNIFIED] {unified_path.name}")
        unified_rows = pick_diverse_rows(str(unified_path), 10, "sector")
        for i, row in enumerate(unified_rows):
            p = build_product(row, row.get("sector", "electronics"), i + 1)
            all_products.append(p)
            print(f"  + {p['sector']:<14} {p['gtin']} {p.get('product_category','?'):<25} "
                  f"{p.get('manufacturing_country','?')}")
    else:
        print(f"  WARNING: {unified_path} not found")

    # 2. Extract sector-specific products
    for sector, filename in SECTOR_FILES.items():
        fpath = DATASET_DIR / filename
        if not fpath.exists():
            print(f"  SKIP: {filename} not found")
            continue
        print(f"\n[{sector.upper()}] {filename}")
        rows = pick_diverse_rows(str(fpath), SAMPLES_PER_SECTOR, "product_category")
        for i, row in enumerate(rows):
            idx = len(all_products) + 1
            p = build_product(row, sector, idx)
            all_products.append(p)
            if sector == "batteries":
                battery_products.append(p)
            print(f"  + {p.get('product_category','?'):<25} {p['gtin']} "
                  f"{p.get('manufacturing_country','?')}")

    # 3. Generate supply chain
    supply_chain = build_supply_chain(all_products[:20])

    # 4. Generate battery API payloads
    battery_payloads = build_battery_api_payloads(battery_products)

    # 5. Generate test inputs
    compliance_queries = build_compliance_test_queries()
    ml_inputs = build_ml_test_inputs()
    lifecycle_actions = build_lifecycle_test_inputs(all_products)

    # 6. Build DPP create requests (sector API — Pydantic validation)
    dpp_create_requests = []
    for p in all_products[:15]:
        p["sector"] = SECTOR_MAP.get(p["sector"], p["sector"])
        if p["sector"] not in VALID_SECTORS:
            p["sector"] = "electronics"
        mfg_date = p.get("manufacturing_date", "2024-01-15")
        if isinstance(mfg_date, str) and len(mfg_date) >= 10:
            mfg_date = mfg_date[:10]
        else:
            mfg_date = "2024-06-15"

        weight = p.get("weight_kg", 1.0)
        if isinstance(weight, (int, float)) and weight <= 0:
            weight = 1.0

        req = {
            "gtin": p["gtin"],
            "serial_number": p["serial_number"],
            "sector": p["sector"],
            "product_category": str(p.get("product_category", "General"))[:100],
            "subcategory": str(p.get("subcategory", "Standard"))[:100],
            "manufacturing_country": str(p.get("manufacturing_country", "Germany"))[:100],
            "manufacturing_date": mfg_date,
            "carbon_footprint_kg_co2eq": max(0, try_float(p.get("carbon_footprint_kg_co2eq", 10.0))),
            "energy_efficiency_class": str(p.get("energy_efficiency_class", "B"))[:5],
            "weight_kg": max(0.01, try_float(weight)),
            "recyclability_score": min(100, max(0, try_float(p.get("recyclability_score", 70.0)))),
            "repairability_score": min(100, max(0, try_float(p.get("repairability_score", 65.0)))),
            "durability_score": min(100, max(0, try_float(p.get("durability_score", 75.0)))),
            "circularity_index": min(100, max(0, try_float(p.get("circularity_index", 60.0)))),
            "recycled_content_pct": min(100, max(0, try_float(p.get("recycled_content_pct", 15.0)))),
            "expected_lifespan_years": max(0.1, try_float(p.get("expected_lifespan_years", 5.0))),
            "espr_compliance_status": str(p.get("espr_compliance_status", "Partial_Compliance"))[:50],
            "reach_status": str(p.get("reach_status", "Registered"))[:50],
            "rohs_compliance": str(p.get("rohs_compliance", "Compliant"))[:50],
            "weee_registration": str(p.get("weee_registration", "Registered"))[:50],
        }
        dpp_create_requests.append(req)

    # 7. Save all demo data
    files = {
        "demo_products.json": all_products,
        "demo_supply_chain.json": supply_chain,
        "demo_battery_payloads.json": battery_payloads,
        "demo_dpp_create_requests.json": dpp_create_requests,
        "demo_compliance_queries.json": compliance_queries,
        "demo_ml_inputs.json": ml_inputs,
        "demo_lifecycle_actions.json": lifecycle_actions,
    }

    for fname, data in files.items():
        fpath = OUTPUT_DIR / fname
        with open(fpath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n  Saved: {fpath} ({len(data)} items)")

    # 8. Summary
    print(f"\n{'=' * 80}")
    print(f"  DEMO DATA SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Total products:        {len(all_products)}")
    print(f"  Battery products:      {len(battery_products)}")
    print(f"  Supply chain edges:    {len(supply_chain)}")
    print(f"  DPP create requests:   {len(dpp_create_requests)}")
    print(f"  Battery API payloads:  {len(battery_payloads)}")
    print(f"  Compliance queries:    {len(compliance_queries)}")
    print(f"  ML test inputs:        {len(ml_inputs)}")
    print(f"  Lifecycle actions:     {len(lifecycle_actions)}")
    sectors_found = set(p["sector"] for p in all_products)
    print(f"  Sectors covered:       {', '.join(sorted(sectors_found))}")
    print(f"\n  Output directory: {OUTPUT_DIR}/")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()

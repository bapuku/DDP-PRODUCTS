#!/usr/bin/env python3
"""
Seed Neo4j with EU DPP unified sample dataset (80k records).
Usage:
  cd eu-dpp-platform && python scripts/seed_data.py
  Or: DATA_PATH=/path/to/dpp_unified_sample_80k.csv python scripts/seed_data.py

Requires: NEO4J_URI, NEO4J_AUTH set or defaults (bolt://localhost:7687, neo4j/dpp-neo4j-dev).
"""
import csv
import os
import re
import sys
from pathlib import Path

# Add backend to path for optional use of app.config
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
except Exception:
    pass

def get_neo4j_auth():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth_s = os.environ.get("NEO4J_AUTH", "neo4j/dpp-neo4j-dev")
    if "/" in auth_s:
        u, p = auth_s.split("/", 1)
        auth = (u.strip(), p.strip())
    else:
        auth = ("neo4j", auth_s)
    return uri, auth


def normalize_gtin(val: str) -> str:
    """Normalize to 14-digit string (strip .0, pad left)."""
    s = re.sub(r"\D", "", str(val))
    if not s:
        return ""
    s = s[:14].zfill(14)
    return s


def find_dataset():
    data_path = os.environ.get("DATA_PATH")
    if data_path and Path(data_path).exists():
        return data_path
    # Relative to eu-dpp-platform root
    base = Path(__file__).resolve().parent.parent
    candidates = [
        base / "DATASET" / "dpp_unified_sample_80k.csv",
        base.parent / "DATASET" / "dpp_unified_sample_80k.csv",
        Path("DATASET/dpp_unified_sample_80k.csv"),
        Path("dpp_unified_sample_80k.csv"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def main():
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("Install neo4j: pip install neo4j")
        sys.exit(1)

    data_file = find_dataset()
    if not data_file:
        print("Dataset not found. Set DATA_PATH or place dpp_unified_sample_80k.csv in DATASET/")
        sys.exit(1)
    print(f"Using dataset: {data_file}")

    uri, auth = get_neo4j_auth()
    driver = GraphDatabase.driver(uri, auth=auth)

    # CSV columns we map to Product node properties (safe names, skip complex)
    safe_keys = {
        "product_id", "dpp_unique_id", "gtin", "product_category", "subcategory",
        "manufacturing_country", "manufacturing_date", "carbon_footprint_kg_co2eq",
        "weight_kg", "espr_compliance_status", "reach_status", "rohs_compliance",
        "weee_registration", "sector", "energy_efficiency_class", "recyclability_score",
        "repairability_score", "durability_score", "circularity_index", "recycled_content_pct",
        "expected_lifespan_years", "tier1_suppliers", "tier2_suppliers", "supply_chain_transparency",
    }
    batch_size = 500
    total = 0
    errors = 0

    with open(data_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_batch = []
        for row in reader:
            gtin = normalize_gtin(row.get("gtin", ""))
            if not gtin or len(gtin) != 14:
                errors += 1
                continue
            props = {"gtin": gtin}
            for k, v in row.items():
                if k not in safe_keys or v is None or str(v).strip() == "":
                    continue
                v = str(v).strip()
                if k == "manufacturing_date" and v:
                    props[k] = v
                elif k in ("carbon_footprint_kg_co2eq", "weight_kg", "recyclability_score",
                           "repairability_score", "durability_score", "circularity_index",
                           "recycled_content_pct", "expected_lifespan_years") and v:
                    try:
                        props[k] = float(v)
                    except ValueError:
                        props[k] = v
                elif k in ("tier1_suppliers", "tier2_suppliers") and v:
                    try:
                        props[k] = int(float(v))
                    except ValueError:
                        props[k] = v
                else:
                    props[k] = v[:500] if isinstance(v, str) and len(v) > 500 else v
            rows_batch.append(props)
            if len(rows_batch) >= batch_size:
                with driver.session() as session:
                    for p in rows_batch:
                        try:
                            session.run(
                                """
                                MERGE (p:Product {gtin: $gtin})
                                SET p += $props
                                """,
                                gtin=p["gtin"],
                                props={k: v for k, v in p.items() if k != "gtin"},
                            )
                            total += 1
                        except Exception as e:
                            errors += 1
                rows_batch = []
                print(f"Inserted {total} products...")

        if rows_batch:
            with driver.session() as session:
                for p in rows_batch:
                    try:
                        session.run(
                            "MERGE (p:Product {gtin: $gtin}) SET p += $props",
                            gtin=p["gtin"],
                            props={k: v for k, v in p.items() if k != "gtin"},
                        )
                        total += 1
                    except Exception:
                        errors += 1

    driver.close()
    print(f"Seed complete. Total products: {total}, errors/skipped: {errors}")


if __name__ == "__main__":
    main()

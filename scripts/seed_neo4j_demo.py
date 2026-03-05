#!/usr/bin/env python3
"""Seed Neo4j with demo products from demo_products.json via cypher-shell."""
import json, subprocess, os, sys

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "demo_products.json")
NEO4J_CONTAINER = os.environ.get("NEO4J_CONTAINER", "dpp-neo4j")
NEO4J_USER = "neo4j"
NEO4J_PASS = os.environ.get("NEO4J_PASS", "nrWXo6w9vicISmZlDhHsxN8n")

with open(DATA) as f:
    products = json.load(f)

count = 0
for p in products:
    dpp_id = p.get("DPP_ID", "")
    gtin = dpp_id.replace("DPP-", "").replace("-", "")[:14].ljust(14, "0")
    sector = p.get("Sector", "unknown")
    name = str(p.get("Product_Name", "")).replace("'", "").replace('"', "")
    mfr = str(p.get("Manufacturer", "")).replace("'", "").replace('"', "")
    wt = float(p.get("Product_Weight_kg", 0))
    gwp = float(p.get("GWP_Total_kgCO2eq", 0))
    rec = float(p.get("Recyclability_Score_pct", 0))
    comp = float(p.get("DPP_Completeness_Score", 0))
    rc = float(p.get("Recycled_Content_pct", 0))

    cypher = (
        f"MERGE (p:Product {{gtin: '{gtin}', serial_number: '{dpp_id}'}}) "
        f"SET p.sector='{sector}', p.product_name='{name}', p.manufacturer='{mfr}', "
        f"p.weight_kg={wt}, p.gwp_total={gwp}, p.recyclability={rec}, "
        f"p.dpp_completeness={comp}, p.recycled_content={rc}, p.status='published', "
        f"p.dpp_uri='https://id.gs1.org/01/{gtin}/21/{dpp_id}' "
        f"RETURN p.gtin"
    )
    try:
        r = subprocess.run(
            ["docker", "exec", NEO4J_CONTAINER, "cypher-shell", "-u", NEO4J_USER, "-p", NEO4J_PASS, cypher],
            capture_output=True, timeout=10, text=True
        )
        if r.returncode == 0:
            count += 1
        else:
            print(f"FAIL {dpp_id}: {r.stderr[:80]}")
    except Exception as e:
        print(f"ERROR {dpp_id}: {e}")

print(f"Seeded {count}/{len(products)} products into Neo4j")

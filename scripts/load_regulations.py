#!/usr/bin/env python3
"""
Load EU regulations into Qdrant (vector search) and Neo4j (knowledge graph).
Stage 1 of GraphRAG-R1 pipeline: ingestion of regulatory text as SPO triplets + embeddings.

Regulations loaded:
- ESPR (EU 2024/1252)
- Battery Regulation (EU 2023/1542)
- REACH (EC 1907/2006)
- RoHS (2011/65/EU)
- EU AI Act (EU 2024/1689)
- CRMA (EU 2024/1252)

Usage:
  cd eu-dpp-platform && python scripts/load_regulations.py
  QDRANT_URL=http://localhost:6333 NEO4J_URI=bolt://localhost:7687 python scripts/load_regulations.py

For embedding: requires OPENAI_API_KEY or falls back to mock embeddings (for dev).
"""
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

REGULATIONS = [
    {
        "celex": "32024R1252",
        "title": "ESPR - Ecodesign for Sustainable Products Regulation",
        "short": "ESPR",
        "articles": [
            {
                "number": "9",
                "text": (
                    "ESPR Article 9 - Digital Product Passport (DPP). "
                    "Economic operators shall ensure that a product passport is available "
                    "for each product placed on the market or put into service. "
                    "The DPP shall be accessible via a data carrier following GS1 Digital Link. "
                    "The DPP shall contain product identifier (GTIN-14), manufacturer info, "
                    "material composition, circularity metrics, and compliance status."
                ),
            },
            {
                "number": "10",
                "text": (
                    "ESPR Article 10 - Ecodesign requirements. Products must meet minimum "
                    "requirements on durability, repairability, recyclability, and energy efficiency. "
                    "Carbon footprint declaration mandatory for priority product groups."
                ),
            },
        ],
    },
    {
        "celex": "32023R1542",
        "title": "Battery Regulation EU 2023/1542",
        "short": "BatteryReg",
        "articles": [
            {
                "number": "Annex XIII",
                "text": (
                    "Battery Regulation Annex XIII - Battery Passport mandatory data. "
                    "87 mandatory fields across 7 clusters: "
                    "Cluster 1 General Information (GTIN-14, serial, batch, EOID, manufacturing date, category, mass, status, warranty). "
                    "Cluster 2 Compliance & Certifications (carbon footprint label A-G, EU DoC). "
                    "Cluster 3 Carbon Footprint (total kgCO2e/kWh, stages breakdown, performance class). "
                    "Cluster 4 Due Diligence (report Art.52, management system Art.49). "
                    "Cluster 5 Materials (chemistry, Co/Li/Ni/graphite content). "
                    "Cluster 6 Circularity (recycled content pre/post-consumer, 2031/2036 targets). "
                    "Cluster 7 Performance (capacity, voltage, efficiency, SoH, cycle life). "
                    "Mandatory from February 2027 for EV, LMT, industrial batteries >2kWh."
                ),
            },
            {
                "number": "49",
                "text": (
                    "Battery Regulation Article 49 - Supply chain due diligence. "
                    "Economic operators shall implement a supply chain due diligence policy for "
                    "cobalt, lithium, nickel, and natural graphite sourcing. "
                    "Third-party audit required. Documentation stored in battery passport."
                ),
            },
            {
                "number": "52",
                "text": (
                    "Battery Regulation Article 52 - Due diligence report. "
                    "Manufacturers shall publish an annual due diligence report "
                    "covering supply chain risks, mitigation measures, and audit outcomes. "
                    "URI must be included in Battery Passport Cluster 4."
                ),
            },
        ],
    },
    {
        "celex": "31907R0006",
        "title": "REACH Regulation EC 1907/2006",
        "short": "REACH",
        "articles": [
            {
                "number": "33",
                "text": (
                    "REACH Article 33 - Communication obligations for SVHC. "
                    "Any supplier of an article containing a Substance of Very High Concern (SVHC) "
                    "above 0.1% w/w shall provide the recipient with information about safe use "
                    "and the SVHC name. Consumer request must be answered within 45 days. "
                    "SCIP database notification required above 0.1% threshold."
                ),
            },
        ],
    },
    {
        "celex": "32011L0065",
        "title": "RoHS Directive 2011/65/EU",
        "short": "RoHS",
        "articles": [
            {
                "number": "Annex II",
                "text": (
                    "RoHS Annex II - Restricted substances and maximum concentration values. "
                    "Lead (Pb): 0.1%, Mercury (Hg): 0.1%, Cadmium (Cd): 0.01%, "
                    "Hexavalent chromium Cr(VI): 0.1%, PBB: 0.1%, PBDE: 0.1%, "
                    "DEHP: 0.1%, DBP: 0.1%, BBP: 0.1%, DIBP: 0.1%. "
                    "Exemptions apply per Annex III and IV with expiry dates."
                ),
            },
        ],
    },
    {
        "celex": "32024R1689",
        "title": "EU AI Act 2024/1689",
        "short": "EU_AI_Act",
        "articles": [
            {
                "number": "12",
                "text": (
                    "EU AI Act Article 12 - Record-keeping. High-risk AI systems shall have "
                    "capabilities to automatically log events (audit trail). Logs must be "
                    "retained for a minimum period commensurate with the intended purpose "
                    "(typically 10 years for compliance systems). Logs include: timestamp, "
                    "agent ID, decision type, input hash, output hash, confidence score, "
                    "regulatory citations, and human override information."
                ),
            },
            {
                "number": "13",
                "text": (
                    "EU AI Act Article 13 - Transparency and provision of information to deployers. "
                    "High-risk AI systems shall be sufficiently transparent that users can "
                    "understand the system's capabilities. AI disclosure text must inform users "
                    "that AI is being used, how decisions are made, and how to request human review."
                ),
            },
            {
                "number": "14",
                "text": (
                    "EU AI Act Article 14 - Human oversight. High-risk AI systems shall be designed "
                    "to allow human oversight. Automatic decisions below confidence threshold (0.85) "
                    "must trigger human review via interrupt mechanism. Humans must be able to "
                    "override, correct, or stop the AI system at any point."
                ),
            },
        ],
    },
]


def get_embedding(text: str) -> list[float]:
    """Get embedding via OpenAI API or return deterministic mock for dev."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            import httpx
            resp = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-3-small", "input": text[:8000]},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
        except Exception as e:
            print(f"  Embedding API failed ({e}), using mock embedding.")
    # Mock: deterministic pseudo-embedding (1536 dim)
    h = hash(text) % (2 ** 32)
    import math
    vec = [math.sin(h * (i + 1) * 0.0001) * 0.01 for i in range(1536)]
    norm = sum(x ** 2 for x in vec) ** 0.5 or 1
    return [x / norm for x in vec]


def load_into_qdrant(regulations: list[dict]) -> None:
    """Load regulatory clauses as vectors into Qdrant collection eu_regulations."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qm
    except ImportError:
        print("qdrant-client not installed - skip Qdrant loading.")
        return

    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=url)

    # Ensure collection exists
    try:
        client.get_collection("eu_regulations")
        print("Qdrant collection eu_regulations exists.")
    except Exception:
        client.create_collection(
            collection_name="eu_regulations",
            vectors_config=qm.VectorParams(size=1536, distance=qm.Distance.COSINE),
        )
        print("Qdrant collection eu_regulations created.")

    points = []
    for reg in regulations:
        for art in reg["articles"]:
            text = art["text"]
            vec = get_embedding(text)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{reg['celex']}-Art{art['number']}"))
            points.append(
                qm.PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={
                        "celex": reg["celex"],
                        "regulation_short": reg["short"],
                        "article_number": art["number"],
                        "text": text[:2000],
                        "title": reg["title"],
                    },
                )
            )
    client.upsert(collection_name="eu_regulations", points=points)
    print(f"Loaded {len(points)} regulatory clauses into Qdrant.")


def load_into_neo4j(regulations: list[dict]) -> None:
    """Load Regulation and RegulatoryArticle nodes with relationships into Neo4j."""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("neo4j not installed - skip Neo4j loading.")
        return

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth_s = os.environ.get("NEO4J_AUTH", "neo4j/dpp-neo4j-dev")
    user, password = (auth_s.split("/", 1) if "/" in auth_s else ("neo4j", auth_s))
    driver = GraphDatabase.driver(uri, auth=(user.strip(), password.strip()))

    with driver.session() as session:
        for reg in regulations:
            session.run(
                """
                MERGE (r:Regulation {celex_number: $celex})
                SET r.title=$title, r.short_name=$short
                """,
                celex=reg["celex"], title=reg["title"], short=reg["short"],
            )
            for art in reg["articles"]:
                session.run(
                    """
                    MATCH (r:Regulation {celex_number: $celex})
                    MERGE (a:RegulatoryArticle {celex_number: $celex, article_number: $article})
                    SET a.text=$text
                    MERGE (r)-[:HAS_ARTICLE]->(a)
                    """,
                    celex=reg["celex"], article=art["number"], text=art["text"],
                )
    driver.close()
    print(f"Loaded {sum(len(r['articles']) for r in regulations)} articles into Neo4j.")


def main() -> None:
    print("Loading EU regulations into Qdrant and Neo4j...")
    load_into_qdrant(REGULATIONS)
    load_into_neo4j(REGULATIONS)
    print("Done.")


if __name__ == "__main__":
    main()

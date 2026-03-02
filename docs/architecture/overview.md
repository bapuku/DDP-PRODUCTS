# EU DPP Platform – Architecture Overview

## Components

- **Backend (FastAPI)**: REST API, 8-agent LangGraph workflow, Neo4j, Qdrant, PostgreSQL, Kafka.
- **Frontend (Next.js)**: Dashboard, compliance check, human review queue, audit trail.
- **Data**: Neo4j (knowledge graph, products, supply chain), Qdrant (vector search), PostgreSQL (audit log, checkpoints), Kafka (lifecycle events).

## 8-Agent Topology

1. **Supervisor** – Task routing, quality gates (≥0.85 auto, 0.70–0.85 retry, <0.70 human review).
2. **Regulatory compliance** – ESPR, Battery Reg, REACH, RoHS interpretation and citations.
3. **Data extraction** – BOM, supplier declarations, carbon footprint.
4. **Product data** – Specs, lifecycle, circularity.
5. **Supply chain** – Multi-tier traceability (Neo4j).
6. **Document generation** – JSON-LD, XML, PDF, GS1 QR.
7. **Audit trail** – EU AI Act Article 12 logging.
8. **Knowledge graph** – GraphRAG retrieval and story-building.

## Compliance

- **EU AI Act 2024/1689**: Art. 12 (audit), Art. 13 (transparency), Art. 14 (human oversight).
- **ESPR**: DPP data and public access.
- **Battery Regulation 2023/1542**: Annex XIII 87 fields, carbon class A–G.

## Deployment

- **Local**: `docker compose` in `infrastructure/`.
- **Kubernetes**: `infrastructure/k8s/base/` (Deployment, Service, HPA, NetworkPolicy). Use overlays for dev/staging/production.

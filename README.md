# EU Digital Product Passport (DPP) Platform

Agentic AI platform for EU DPP compliance. Multi-sector (batteries, electronics, textiles, vehicles, etc.) with 8-agent LangGraph architecture, GraphRAG knowledge graph, and full alignment to **EU AI Act 2024/1689** (Articles 12–14), **ESPR**, and **Battery Regulation 2023/1542**.

## Quick start (local Docker Compose)

1. **Copy environment and start infrastructure**
   ```bash
   cd eu-dpp-platform/infrastructure
   cp .env.example .env
   # Edit .env if needed (passwords, ports)
   docker compose up -d
   ```
   This starts: Neo4j 5.x, Qdrant, PostgreSQL 16, Kafka, Schema Registry, and the DPP API.

2. **Run without API in Docker (backend locally with hot reload)**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   cd ../backend && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0
   ```

3. **Apply Neo4j schema and seed data**
   ```bash
   cd backend && python -m scripts.run_neo4j_migrations
   cd ../scripts && DATA_PATH=../DATASET/dpp_unified_sample_80k.csv python seed_data.py
   ```
   If the dataset is in `../DATASET/dpp_unified_sample_80k.csv` relative to the repo, or set `DATA_PATH` to the CSV path.

4. **Endpoints**
   - API: http://localhost:8000  
   - Docs: http://localhost:8000/docs  
   - Health: http://localhost:8000/health  
   - Ready: http://localhost:8000/ready  

## Project structure

- `backend/` – FastAPI app, Pydantic models (DPP base, Battery Passport 87 fields), services (Neo4j, Qdrant, Kafka, PostgreSQL), agents (Sprint 2), API v1
- `frontend/` – React/Next.js dashboard (Sprint 5)
- `infrastructure/` – Docker Compose, init SQL, `.env.example`
- `scripts/` – Seed dataset, Neo4j migrations runner
- `docs/` – Architecture, compliance, API

## Compliance

- **EU AI Act**: Audit trail (Art. 12), transparency (Art. 13), human oversight (Art. 14)
- **ESPR**: DPP data and access
- **Battery Regulation 2023/1542**: Annex XIII 87 mandatory fields, carbon class A–G, recycled content targets

## License and data

Dataset: synthetic EU DPP training data (see `DATASET/dpp_dataset_metadata.json`). No real product data.

# Deployment Runbook

## Local (Docker Compose)

1. `cd infrastructure && cp .env.example .env`
2. `docker compose up -d`
3. Apply Neo4j schema: `cd backend && python -m scripts.run_neo4j_migrations`
4. Seed data: `DATA_PATH=../DATASET/dpp_unified_sample_80k.csv python ../scripts/seed_data.py`
5. API: http://localhost:8000 · Docs: http://localhost:8000/docs

## Kubernetes

1. Create namespace and secrets (do not commit secrets):
   - `kubectl create namespace dpp`
   - Store NEO4J_URI, NEO4J_AUTH, DATABASE_URL, etc. in a Secret `dpp-api-secrets`.
2. Apply base: `kubectl apply -k infrastructure/k8s/base/`
3. Expose via Ingress or LoadBalancer as needed.
4. EU AI Act: ensure audit log retention (10 years) and human oversight configuration are applied.

## Verification

- `GET /health` and `GET /ready` must return 200.
- Compliance check: `POST /api/v1/compliance/check` with body `{"query": "Battery Regulation compliance"}`.
- Battery Passport: `POST /api/v1/dpp/battery` with valid Annex XIII payload.

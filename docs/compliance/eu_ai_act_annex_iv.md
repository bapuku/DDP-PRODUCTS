# EU AI Act Annex IV - Technical Documentation
## EU DPP Agentic AI Platform

**Classification:** Not High-Risk (per Annex III assessment)  
**Proactive compliance:** Platform implements Arts. 12–14 for transparency.  
**Date:** 2026-03-02 | **Version:** 0.1.0

---

## 1. General Description

| Field | Value |
|---|---|
| System name | EU Digital Product Passport Agentic AI Platform |
| Intended purpose | Automated compliance verification for DPP regulatory obligations |
| Developer | EURAMATERIALS |
| Deployment | SaaS / On-premise |
| Version | 0.1.0 |
| Classification | Not High-Risk (Annex III exclusion — regulatory compliance aid, not enforcement) |

---

## 2. Architecture

- **8-agent LangGraph topology** (Supervisor, Regulatory, Data Extraction, Product Data, Supply Chain, Document Generation, Audit Trail, Knowledge Graph)
- **Models used:** Claude Sonnet 4 (primary agent reasoning), Claude Opus 4 (complex regulatory analysis)
- **Confidence scoring:** Auto-approve ≥ 0.85 | Human review 0.70–0.85 | Reject < 0.70 (EU AI Act Art. 14)
- **Knowledge base:** Qdrant vector search (EUR-Lex embeddings) + Neo4j graph (regulations, products, supply chain)

---

## 3. Data Governance (Art. 10)

- Training dataset: 1.5M synthetic DPP records (no real personal data)
- Statistical validation: Kolmogorov-Smirnov conformity tests
- Geographic diversity: 45 manufacturing countries, weighted trade flow distributions
- Bias detection: Per-sector and per-country distribution checks applied at training

---

## 4. Record-Keeping (Art. 12)

- **Audit log table** `audit_log` in PostgreSQL (append-only)
- **Fields per entry:** id, timestamp, agent_id, decision_type, input_hash (SHA-256), output_hash (SHA-256), confidence_score, regulatory_citations (JSON), human_override, entity_type, entity_id, operator_id, regulation_ref
- **Retention:** 10 years (configurable via `AUDIT_RETENTION_YEARS`)
- **Tamper evidence:** SHA-256 hashing of all inputs and outputs

---

## 5. Transparency (Art. 13)

- OpenAPI 3.0 documentation at `/docs` and `/redoc`
- AI usage disclosed in HTTP response headers: `X-AI-System`, `X-EU-AI-Act-Compliance`
- AI disclosure text shown in frontend and API description:
  > *"This platform uses AI agents (Claude 4) to interpret EU regulations and generate compliance recommendations. All AI decisions are logged per EU AI Act Article 12. Human oversight is required for critical decisions (confidence < 85%). You can request human review at any time."*

---

## 6. Human Oversight (Art. 14)

| Trigger | Action |
|---|---|
| Confidence < 0.85 | workflow escalates to `human_review` node |
| Confidence < 0.70 | Rejection + mandatory human expert review |
| Conflicting regulatory interpretations | Auto-escalate |
| Novel/ambiguous regulatory scenarios | Escalate via `escalate: true` flag |
| User request | Any endpoint accepts `?request_human_review=true` |

- Human reviewers can override, correct, or stop any AI decision
- Override recorded in `audit_log.human_override`

---

## 7. Performance Metrics

| Metric | Target | Notes |
|---|---|---|
| API response p95 | < 2000ms | FastAPI async, measured at `/ready` |
| DPP creation | < 30s | End-to-end including Neo4j write |
| Agent decision | < 5s | Per agent invocation |
| Regulatory retrieval | < 500ms | Qdrant hybrid search |
| Audit trail write | < 100ms | PostgreSQL async |

---

## 8. Risk Management

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Incorrect regulatory interpretation | Medium | High | Confidence thresholds, human review, EUR-Lex citation validation |
| Outdated regulatory data | Medium | High | Regular regulatory text refresh in Qdrant + Neo4j |
| Data privacy breach | Low | High | GDPR middleware, no PII in logs, pseudonymisation |
| LLM hallucination | Medium | High | Structured output, citation validation, confidence scoring |
| System unavailability | Low | Medium | 3-replica K8s HA, health probes, PDB |

---

## 9. Compliance Attestation

- ESPR (EU 2024/1252) Article 9: DPP created for each product
- Battery Regulation (EU 2023/1542) Annex XIII: 87-field data model implemented
- REACH (EC 1907/2006) Article 33: SVHC communication tools integrated
- RoHS (2011/65/EU): Exemption verification implemented
- EU AI Act (EU 2024/1689) Arts. 12–14: Audit, transparency, human oversight fully implemented

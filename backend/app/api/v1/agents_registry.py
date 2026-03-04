"""
Agent Registry, Skills Registry, Tool Registry, and Agent Assistant endpoints.
EU AI Act Art. 13 — transparency: full disclosure of AI agents, their capabilities, and tools.
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.core.i18n import get_locale, t

router = APIRouter()

# ─── Agent Registry ───────────────────────────────────────────────────────────

AGENTS: list[dict[str, Any]] = [
    {
        "id": "supervisor",
        "name": {"en": "Supervisor / Orchestrator", "fr": "Superviseur / Orchestrateur"},
        "description": {
            "en": "Routes tasks to specialist agents, enforces quality gates (auto ≥0.85, review 0.70–0.85, reject <0.70). EU AI Act Art. 14 human escalation.",
            "fr": "Achemine les tâches vers les agents spécialisés, applique les seuils qualité (auto ≥0.85, revue 0.70–0.85, rejet <0.70). Escalade humaine Art. 14 EU AI Act.",
        },
        "category": "orchestration",
        "phase": "all",
        "compliance_refs": ["EU AI Act Art. 14", "ESPR Art. 9"],
        "skills": ["task_routing", "quality_gate", "human_escalation", "confidence_scoring"],
        "tools": ["langgraph_workflow", "audit_logger"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "regulatory_compliance",
        "name": {"en": "Regulatory Compliance", "fr": "Conformité Réglementaire"},
        "description": {
            "en": "Interprets EU regulations (ESPR, Battery Reg 2023/1542, REACH, RoHS, WEEE). Uses EUR-Lex and regulatory knowledge base for legal citations.",
            "fr": "Interprète les réglementations UE (ESPR, Règlement Batteries 2023/1542, REACH, RoHS, DEEE). Utilise EUR-Lex et la base de connaissances réglementaires.",
        },
        "category": "compliance",
        "phase": "all",
        "compliance_refs": ["ESPR", "Battery Reg 2023/1542", "REACH", "RoHS", "WEEE", "EU AI Act Art. 12"],
        "skills": ["regulation_interpretation", "compliance_scoring", "gap_analysis", "citation_extraction"],
        "tools": ["eurlex_search", "qdrant_vector_search", "neo4j_knowledge_graph"],
        "llm_model": "Claude Opus 4",
        "status": "active",
    },
    {
        "id": "data_collection",
        "name": {"en": "Data Collection", "fr": "Collecte de Données"},
        "description": {
            "en": "Phases 0–3: Collects BOM, supplier declarations, LCA data, carbon footprint. Replaces data_extraction for v3.0 DDP creation workflows.",
            "fr": "Phases 0–3 : Collecte BOM, déclarations fournisseurs, données ACV, empreinte carbone. Remplace data_extraction pour les workflows de création DDP v3.0.",
        },
        "category": "data",
        "phase": "0-3",
        "compliance_refs": ["Battery Reg Annex XIII", "ESPR Art. 9"],
        "skills": ["bom_parsing", "supplier_declaration_extraction", "lca_data_collection", "carbon_footprint_calculation"],
        "tools": ["document_parser", "neo4j_knowledge_graph", "kafka_producer"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "ddp_generation",
        "name": {"en": "DDP Generation", "fr": "Génération DDP"},
        "description": {
            "en": "Phase 4: Generates complete DPP output (JSON-LD, QR code, NFC payload, RFID EPC). ESPR Art. 9, Battery Reg Annex XIII compliant.",
            "fr": "Phase 4 : Génère le DPP complet (JSON-LD, code QR, payload NFC, RFID EPC). Conforme ESPR Art. 9, Règlement Batteries Annexe XIII.",
        },
        "category": "generation",
        "phase": "4",
        "compliance_refs": ["ESPR Art. 9", "Battery Reg Annex XIII", "GS1 Digital Link"],
        "skills": ["jsonld_generation", "qr_code_generation", "nfc_payload_creation", "rfid_epc_encoding", "gs1_digital_link"],
        "tools": ["data_carriers_service", "kafka_producer", "neo4j_knowledge_graph"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "validation",
        "name": {"en": "Validation Agent", "fr": "Agent de Validation"},
        "description": {
            "en": "Structural and regulatory validation of DDP data. Completeness thresholds: 0.35, 0.55, 0.70, 0.85. Cross-field consistency checks.",
            "fr": "Validation structurelle et réglementaire des données DDP. Seuils de complétude : 0.35, 0.55, 0.70, 0.85. Vérifications de cohérence inter-champs.",
        },
        "category": "quality",
        "phase": "4-5",
        "compliance_refs": ["ESPR Art. 9(3)", "Battery Reg Annex XIII"],
        "skills": ["structural_validation", "completeness_check", "cross_field_validation", "regulation_mapping"],
        "tools": ["pydantic_validator", "neo4j_knowledge_graph"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "supply_chain",
        "name": {"en": "Supply Chain Traceability", "fr": "Traçabilité Chaîne d'Approvisionnement"},
        "description": {
            "en": "Multi-tier supply chain traceability via Neo4j graph traversal. Battery Reg Art. 49 due diligence. EPCIS 2.0 event tracking.",
            "fr": "Traçabilité multi-niveaux via traversée de graphe Neo4j. Diligence raisonnable Art. 49 Règlement Batteries. Suivi événements EPCIS 2.0.",
        },
        "category": "traceability",
        "phase": "3-6",
        "compliance_refs": ["Battery Reg Art. 49", "EPCIS 2.0"],
        "skills": ["graph_traversal", "supplier_verification", "material_tracing", "epcis_event_generation"],
        "tools": ["neo4j_knowledge_graph", "epcis_service", "kafka_producer"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "knowledge_graph",
        "name": {"en": "Knowledge Graph (GraphRAG)", "fr": "Graphe de Connaissances (GraphRAG)"},
        "description": {
            "en": "GraphRAG-R1 pipeline: SPO ingestion, maintenance, hybrid vector+graph retrieval, story-building. Powers regulatory reasoning.",
            "fr": "Pipeline GraphRAG-R1 : ingestion SPO, maintenance, récupération hybride vecteur+graphe, construction narrative. Alimente le raisonnement réglementaire.",
        },
        "category": "knowledge",
        "phase": "all",
        "compliance_refs": ["EU AI Act Art. 13"],
        "skills": ["spo_extraction", "graph_maintenance", "hybrid_retrieval", "story_building"],
        "tools": ["neo4j_knowledge_graph", "qdrant_vector_search"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "document_generation",
        "name": {"en": "Document Generation", "fr": "Génération de Documents"},
        "description": {
            "en": "Generates JSON-LD, XML, PDF, and GS1 QR code data carriers. Multi-format export for interoperability.",
            "fr": "Génère JSON-LD, XML, PDF et codes QR GS1. Export multi-format pour l'interopérabilité.",
        },
        "category": "generation",
        "phase": "4-5",
        "compliance_refs": ["ESPR Art. 9", "GS1 ISO/IEC 18004"],
        "skills": ["jsonld_export", "xml_export", "pdf_generation", "qr_generation"],
        "tools": ["data_carriers_service", "template_engine"],
        "llm_model": None,
        "status": "active",
    },
    {
        "id": "audit_trail",
        "name": {"en": "Audit Trail", "fr": "Piste d'Audit"},
        "description": {
            "en": "EU AI Act Art. 12 record-keeping. Decision logging with hash chain, regulatory citations, confidence scores. 10-year retention.",
            "fr": "EU AI Act Art. 12 tenue des dossiers. Journalisation des décisions avec chaîne de hash, citations réglementaires, scores de confiance. Rétention 10 ans.",
        },
        "category": "audit",
        "phase": "all",
        "compliance_refs": ["EU AI Act Art. 12", "EU AI Act Annex IV"],
        "skills": ["decision_logging", "hash_chain_integrity", "citation_tracking", "retention_management"],
        "tools": ["postgres_audit_log", "kafka_producer"],
        "llm_model": None,
        "status": "active",
    },
    {
        "id": "anomaly_detection",
        "name": {"en": "Anomaly Detection", "fr": "Détection d'Anomalies"},
        "description": {
            "en": "ML-based outlier detection (Isolation Forest) on DPP and supply chain data. Flags data quality issues and potential fraud.",
            "fr": "Détection d'outliers par ML (Isolation Forest) sur les données DPP et chaîne d'approvisionnement. Signale les problèmes de qualité et fraudes potentielles.",
        },
        "category": "quality",
        "phase": "4-6",
        "compliance_refs": ["EU AI Act Art. 9", "EU AI Act Art. 15"],
        "skills": ["isolation_forest", "heuristic_checks", "data_quality_scoring", "fraud_detection"],
        "tools": ["ml_inference_service", "neo4j_knowledge_graph"],
        "llm_model": None,
        "status": "active",
    },
    {
        "id": "predictive",
        "name": {"en": "Predictive Risk Scoring", "fr": "Scoring Prédictif de Risques"},
        "description": {
            "en": "Risk and compliance scoring via GradientBoosting models (ESPR, RoHS, REACH, carbon, circularity). EU AI Act Art. 9, 10, 15.",
            "fr": "Scoring de risque et conformité via modèles GradientBoosting (ESPR, RoHS, REACH, carbone, circularité). EU AI Act Art. 9, 10, 15.",
        },
        "category": "ml",
        "phase": "4-6",
        "compliance_refs": ["EU AI Act Art. 9", "EU AI Act Art. 10", "EU AI Act Art. 15"],
        "skills": ["espr_classification", "rohs_classification", "reach_classification", "carbon_prediction", "circularity_prediction"],
        "tools": ["ml_inference_service", "gradient_boosting_models"],
        "llm_model": None,
        "status": "active",
    },
    {
        "id": "circular_economy",
        "name": {"en": "Circular Economy / Second Life", "fr": "Économie Circulaire / Seconde Vie"},
        "description": {
            "en": "Phase 7: Second-life assessment (SoH, refurbishment, repurpose, recycling pathway). Battery Reg Art. 14, WEEE Directive.",
            "fr": "Phase 7 : Évaluation seconde vie (SdS, reconditionnement, réemploi, filière recyclage). Règlement Batteries Art. 14, Directive DEEE.",
        },
        "category": "lifecycle",
        "phase": "7",
        "compliance_refs": ["Battery Reg Art. 14", "WEEE Directive", "ESPR"],
        "skills": ["soh_assessment", "refurbishment_evaluation", "repurpose_pathway", "recycling_routing"],
        "tools": ["neo4j_knowledge_graph", "kafka_producer"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "recycling",
        "name": {"en": "Recycling Agent", "fr": "Agent Recyclage"},
        "description": {
            "en": "Phase 8: Recycling operations — intake, dismantling, material recovery. Battery Reg recycled content targets (2031/2036).",
            "fr": "Phase 8 : Opérations de recyclage — réception, démantèlement, récupération de matériaux. Objectifs contenu recyclé Règlement Batteries (2031/2036).",
        },
        "category": "lifecycle",
        "phase": "8",
        "compliance_refs": ["Battery Reg Art. 8", "Battery Reg Art. 57", "WEEE"],
        "skills": ["intake_processing", "dismantling_planning", "material_recovery", "recycled_content_tracking"],
        "tools": ["neo4j_knowledge_graph", "kafka_producer"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
    {
        "id": "destruction",
        "name": {"en": "Destruction Agent", "fr": "Agent Destruction"},
        "description": {
            "en": "Phase 9: Authorization, documentation, archival for lifecycle closure. Generates destruction proof and certificate.",
            "fr": "Phase 9 : Autorisation, documentation, archivage pour clôture du cycle de vie. Génère preuve et certificat de destruction.",
        },
        "category": "lifecycle",
        "phase": "9",
        "compliance_refs": ["WEEE Directive", "Waste Framework Directive"],
        "skills": ["authorization_check", "destruction_documentation", "archival", "certificate_generation"],
        "tools": ["postgres_audit_log", "kafka_producer"],
        "llm_model": None,
        "status": "active",
    },
    {
        "id": "human_review",
        "name": {"en": "Human-in-the-Loop", "fr": "Humain dans la Boucle"},
        "description": {
            "en": "EU AI Act Art. 14 — human oversight. Interrupt workflow for approval/rejection/modification when confidence < 85%.",
            "fr": "EU AI Act Art. 14 — supervision humaine. Interrompt le workflow pour approbation/rejet/modification quand confiance < 85 %.",
        },
        "category": "governance",
        "phase": "all",
        "compliance_refs": ["EU AI Act Art. 14"],
        "skills": ["workflow_interrupt", "approval_processing", "feedback_integration"],
        "tools": ["langgraph_interrupt", "postgres_audit_log"],
        "llm_model": None,
        "status": "active",
    },
    {
        "id": "synthesize",
        "name": {"en": "Response Synthesizer", "fr": "Synthétiseur de Réponses"},
        "description": {
            "en": "Consolidates outputs from all agents into a final response with regulatory citations, confidence scores, and human review flag.",
            "fr": "Consolide les sorties de tous les agents en une réponse finale avec citations réglementaires, scores de confiance et indicateur de revue humaine.",
        },
        "category": "orchestration",
        "phase": "all",
        "compliance_refs": ["EU AI Act Art. 13"],
        "skills": ["response_consolidation", "citation_aggregation", "confidence_aggregation"],
        "tools": ["audit_logger"],
        "llm_model": "Claude Sonnet 4",
        "status": "active",
    },
]

TOOLS: list[dict[str, Any]] = [
    {"id": "langgraph_workflow", "name": {"en": "LangGraph Workflow Engine", "fr": "Moteur de Workflow LangGraph"}, "category": "orchestration", "description": {"en": "Graph-based agent orchestration with checkpointing and human-in-the-loop", "fr": "Orchestration d'agents basée graphe avec checkpointing et humain dans la boucle"}, "used_by": ["supervisor", "human_review"]},
    {"id": "langgraph_interrupt", "name": {"en": "LangGraph Interrupt", "fr": "Interruption LangGraph"}, "category": "orchestration", "description": {"en": "Pause workflow execution for human review (EU AI Act Art. 14)", "fr": "Pause l'exécution du workflow pour revue humaine (EU AI Act Art. 14)"}, "used_by": ["human_review", "supervisor"]},
    {"id": "eurlex_search", "name": {"en": "EUR-Lex Legal Search", "fr": "Recherche Juridique EUR-Lex"}, "category": "regulatory", "description": {"en": "Search EU legislation database for regulatory citations and interpretations", "fr": "Recherche dans la base législative UE pour citations et interprétations réglementaires"}, "used_by": ["regulatory_compliance"]},
    {"id": "neo4j_knowledge_graph", "name": {"en": "Neo4j Knowledge Graph", "fr": "Graphe de Connaissances Neo4j"}, "category": "data", "description": {"en": "Graph database for product, supplier, regulation relationships and supply chain traversal", "fr": "Base de données graphe pour produits, fournisseurs, réglementations et traversée chaîne d'approvisionnement"}, "used_by": ["knowledge_graph", "supply_chain", "regulatory_compliance", "data_collection", "ddp_generation", "validation", "anomaly_detection", "circular_economy", "recycling"]},
    {"id": "qdrant_vector_search", "name": {"en": "Qdrant Vector Search", "fr": "Recherche Vectorielle Qdrant"}, "category": "data", "description": {"en": "Semantic vector search for regulatory documents and product data embeddings", "fr": "Recherche vectorielle sémantique pour documents réglementaires et embeddings données produit"}, "used_by": ["knowledge_graph", "regulatory_compliance"]},
    {"id": "postgres_audit_log", "name": {"en": "PostgreSQL Audit Log", "fr": "Journal d'Audit PostgreSQL"}, "category": "audit", "description": {"en": "Append-only audit log with 10-year retention (EU AI Act Art. 12)", "fr": "Journal d'audit en ajout seul avec rétention 10 ans (EU AI Act Art. 12)"}, "used_by": ["audit_trail", "human_review", "destruction"]},
    {"id": "kafka_producer", "name": {"en": "Kafka Event Producer", "fr": "Producteur d'Événements Kafka"}, "category": "messaging", "description": {"en": "Publish lifecycle events (created, updated, phase_transition, anomaly, recall)", "fr": "Publier les événements de cycle de vie (créé, mis à jour, transition de phase, anomalie, rappel)"}, "used_by": ["data_collection", "ddp_generation", "supply_chain", "audit_trail", "anomaly_detection", "circular_economy", "recycling", "destruction"]},
    {"id": "data_carriers_service", "name": {"en": "Data Carriers (QR/NFC/RFID)", "fr": "Supports de Données (QR/NFC/RFID)"}, "category": "generation", "description": {"en": "Generate QR codes (GS1 Digital Link), NFC NDEF payloads, RFID SGTIN-96 encodings", "fr": "Générer codes QR (GS1 Digital Link), payloads NFC NDEF, encodages RFID SGTIN-96"}, "used_by": ["ddp_generation", "document_generation"]},
    {"id": "epcis_service", "name": {"en": "EPCIS 2.0 Event Service", "fr": "Service d'Événements EPCIS 2.0"}, "category": "traceability", "description": {"en": "Generate and publish EPCIS 2.0 JSON-LD events for supply chain visibility", "fr": "Générer et publier des événements EPCIS 2.0 JSON-LD pour la visibilité chaîne d'approvisionnement"}, "used_by": ["supply_chain"]},
    {"id": "ml_inference_service", "name": {"en": "ML Inference Engine", "fr": "Moteur d'Inférence ML"}, "category": "ml", "description": {"en": "GradientBoosting model inference for compliance predictions (ESPR, RoHS, REACH, carbon, circularity)", "fr": "Inférence de modèles GradientBoosting pour prédictions de conformité (ESPR, RoHS, REACH, carbone, circularité)"}, "used_by": ["predictive", "anomaly_detection"]},
    {"id": "gradient_boosting_models", "name": {"en": "GradientBoosting Models v2", "fr": "Modèles GradientBoosting v2"}, "category": "ml", "description": {"en": "Trained classifiers for ESPR, RoHS, REACH and regressors for carbon footprint and circularity index", "fr": "Classifieurs entraînés pour ESPR, RoHS, REACH et régresseurs pour empreinte carbone et indice de circularité"}, "used_by": ["predictive"]},
    {"id": "pydantic_validator", "name": {"en": "Pydantic v2 Validator", "fr": "Validateur Pydantic v2"}, "category": "quality", "description": {"en": "Structural validation of DPP data models (87 fields Battery Passport, multi-sector DPP)", "fr": "Validation structurelle des modèles de données DPP (87 champs Passeport Batterie, DPP multi-secteur)"}, "used_by": ["validation"]},
    {"id": "document_parser", "name": {"en": "Document Parser", "fr": "Analyseur de Documents"}, "category": "data", "description": {"en": "Parse BOM, supplier declarations, safety data sheets, and LCA reports", "fr": "Analyser BOM, déclarations fournisseurs, fiches de sécurité et rapports ACV"}, "used_by": ["data_collection"]},
    {"id": "template_engine", "name": {"en": "Template Engine", "fr": "Moteur de Templates"}, "category": "generation", "description": {"en": "Render PDF and XML documents from DPP data templates", "fr": "Générer des documents PDF et XML à partir de templates de données DPP"}, "used_by": ["document_generation"]},
    {"id": "audit_logger", "name": {"en": "Audit Logger", "fr": "Enregistreur d'Audit"}, "category": "audit", "description": {"en": "Log agent decisions with confidence scores, citations, and input/output hashes", "fr": "Enregistrer les décisions d'agents avec scores de confiance, citations et hashes entrée/sortie"}, "used_by": ["supervisor", "synthesize"]},
]

EU_COMPLIANCE_REPORTS: list[dict[str, Any]] = [
    {"id": "ai_act_art12", "regulation": "EU AI Act 2024/1689", "article": "Art. 12", "title": {"en": "Record-Keeping / Audit Trail", "fr": "Tenue des Dossiers / Piste d'Audit"}, "description": {"en": "All AI-powered decisions are logged with timestamps, agent IDs, confidence scores, input/output hashes, and regulatory citations. 10-year retention policy.", "fr": "Toutes les décisions alimentées par l'IA sont enregistrées avec horodatages, IDs d'agents, scores de confiance, hashes entrée/sortie et citations réglementaires. Politique de rétention 10 ans."}, "status": "implemented", "agent": "audit_trail", "endpoint": "/api/v1/dpp/audit-log"},
    {"id": "ai_act_art13", "regulation": "EU AI Act 2024/1689", "article": "Art. 13", "title": {"en": "Transparency / AI Disclosure", "fr": "Transparence / Divulgation IA"}, "description": {"en": "AI system usage disclosed via response headers (X-AI-System, X-EU-AI-Act-Compliance). Agent Registry publicly accessible. All agents documented.", "fr": "Utilisation du système IA divulguée via en-têtes de réponse (X-AI-System, X-EU-AI-Act-Compliance). Registre d'agents accessible publiquement. Tous les agents documentés."}, "status": "implemented", "agent": "supervisor", "endpoint": "/api/v1/agents/registry"},
    {"id": "ai_act_art14", "regulation": "EU AI Act 2024/1689", "article": "Art. 14", "title": {"en": "Human Oversight", "fr": "Supervision Humaine"}, "description": {"en": "Human-in-the-loop when confidence < 85%. Approval/rejection/modification workflow. Live queue with real-time polling.", "fr": "Humain dans la boucle quand confiance < 85 %. Workflow approbation/rejet/modification. File d'attente en direct avec interrogation temps réel."}, "status": "implemented", "agent": "human_review", "endpoint": "/api/v1/human-review/pending"},
    {"id": "espr_art9", "regulation": "ESPR", "article": "Art. 9", "title": {"en": "Digital Product Passport Data", "fr": "Données du Passeport Numérique Produit"}, "description": {"en": "DPP creation, public access, and interoperability via GS1 Digital Link URI. JSON-LD, QR, NFC, RFID data carriers.", "fr": "Création DPP, accès public et interopérabilité via URI GS1 Digital Link. Supports de données JSON-LD, QR, NFC, RFID."}, "status": "implemented", "agent": "ddp_generation", "endpoint": "/api/v1/dpp/lifecycle/create"},
    {"id": "battery_reg_annex_xiii", "regulation": "Battery Regulation 2023/1542", "article": "Annex XIII", "title": {"en": "Battery Passport 87 Mandatory Fields", "fr": "Passeport Batterie 87 Champs Obligatoires"}, "description": {"en": "Full 87-field Battery Passport per EU Regulation 2023/1542 Annex XIII. 7 data clusters, carbon class A–G, recycled content targets.", "fr": "Passeport Batterie complet 87 champs selon Règlement UE 2023/1542 Annexe XIII. 7 clusters de données, classe carbone A–G, objectifs contenu recyclé."}, "status": "implemented", "agent": "ddp_generation", "endpoint": "/api/v1/dpp/battery"},
    {"id": "battery_reg_art49", "regulation": "Battery Regulation 2023/1542", "article": "Art. 49", "title": {"en": "Supply Chain Due Diligence", "fr": "Diligence Raisonnable Chaîne d'Approvisionnement"}, "description": {"en": "Multi-tier supply chain traceability from product to raw materials via Neo4j knowledge graph.", "fr": "Traçabilité multi-niveaux de la chaîne d'approvisionnement du produit aux matières premières via graphe Neo4j."}, "status": "implemented", "agent": "supply_chain", "endpoint": "/api/v1/dpp/sector/supply-chain/{gtin}"},
    {"id": "ai_act_annex_iv", "regulation": "EU AI Act 2024/1689", "article": "Annex IV", "title": {"en": "Technical Documentation", "fr": "Documentation Technique"}, "description": {"en": "Agent registry, skill registry, tool registry. Full architecture transparency and compliance documentation.", "fr": "Registre d'agents, registre de compétences, registre d'outils. Transparence architecturale et documentation de conformité complètes."}, "status": "implemented", "agent": "supervisor", "endpoint": "/api/v1/agents/registry"},
]


def _localize(obj: dict[str, str], locale: str) -> str:
    return obj.get(locale, obj.get("en", ""))


@router.get("/providers")
async def llm_providers() -> list[dict[str, Any]]:
    """List configured LLM providers (Anthropic, OpenAI, HuggingFace) and their status."""
    from app.services.llm_providers import list_available_providers
    return list_available_providers()


@router.get("/registry")
async def agent_registry(locale: str = Depends(get_locale)) -> list[dict[str, Any]]:
    """Agent Registry — EU AI Act Art. 13 transparency. Lists all agents with metadata."""
    return [
        {
            "id": a["id"],
            "name": _localize(a["name"], locale),
            "description": _localize(a["description"], locale),
            "category": a["category"],
            "phase": a["phase"],
            "compliance_refs": a["compliance_refs"],
            "skills": a["skills"],
            "tools": a["tools"],
            "llm_model": a["llm_model"],
            "status": a["status"],
        }
        for a in AGENTS
    ]


@router.get("/registry/{agent_id}")
async def agent_detail(agent_id: str, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Get detailed info for a specific agent."""
    for a in AGENTS:
        if a["id"] == agent_id:
            return {
                "id": a["id"],
                "name": _localize(a["name"], locale),
                "description": _localize(a["description"], locale),
                "category": a["category"],
                "phase": a["phase"],
                "compliance_refs": a["compliance_refs"],
                "skills": a["skills"],
                "tools": a["tools"],
                "llm_model": a["llm_model"],
                "status": a["status"],
            }
    raise HTTPException(status_code=404, detail=t("errors.dpp_not_found", locale))


@router.get("/skills")
async def skills_registry(locale: str = Depends(get_locale)) -> list[dict[str, Any]]:
    """Skills Registry — all capabilities across agents."""
    skills: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in AGENTS:
        for skill in a["skills"]:
            if skill not in seen:
                seen.add(skill)
                skills.append({
                    "id": skill,
                    "name": skill.replace("_", " ").title(),
                    "agents": [ag["id"] for ag in AGENTS if skill in ag["skills"]],
                    "category": a["category"],
                })
    return skills


@router.get("/tools")
async def tools_registry(locale: str = Depends(get_locale)) -> list[dict[str, Any]]:
    """Tool Registry — all tools available to agents."""
    return [
        {
            "id": tool["id"],
            "name": _localize(tool["name"], locale),
            "description": _localize(tool["description"], locale),
            "category": tool["category"],
            "used_by": tool["used_by"],
        }
        for tool in TOOLS
    ]


@router.get("/reports")
async def compliance_reports(locale: str = Depends(get_locale)) -> list[dict[str, Any]]:
    """EU Compliance Reports — per regulation article. EU AI Act Annex IV."""
    return [
        {
            "id": r["id"],
            "regulation": r["regulation"],
            "article": r["article"],
            "title": _localize(r["title"], locale),
            "description": _localize(r["description"], locale),
            "status": r["status"],
            "agent": r["agent"],
            "endpoint": r["endpoint"],
        }
        for r in EU_COMPLIANCE_REPORTS
    ]


class AssistRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[dict[str, Any]] = None


@router.post("/{agent_id}/assist")
async def agent_assist(agent_id: str, body: AssistRequest, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Agent Assistant — Gen AI chat with a specific agent. EU AI Act Art. 13 transparency."""
    agent = None
    for a in AGENTS:
        if a["id"] == agent_id:
            agent = a
            break
    if not agent:
        raise HTTPException(status_code=404, detail=t("errors.dpp_not_found", locale))

    agent_name = _localize(agent["name"], locale)
    agent_desc = _localize(agent["description"], locale)
    skills_list = ", ".join(agent["skills"])
    tools_list = ", ".join(agent["tools"])
    refs = ", ".join(agent["compliance_refs"])

    try:
        from app.services.llm_providers import get_best_available_llm
        llm, provider_name = get_best_available_llm(task="regulatory", temperature=0.3, max_tokens=1500)
        system_prompt = (
            f"You are the '{agent_name}' agent of the EU Digital Product Passport Platform.\n"
            f"Description: {agent_desc}\n"
            f"Skills: {skills_list}\n"
            f"Tools: {tools_list}\n"
            f"Compliance references: {refs}\n"
            f"Language: {'French' if locale == 'fr' else 'English'}\n\n"
            f"Answer the user's question using your specialized knowledge. "
            f"Always cite relevant EU regulations. Be precise and actionable."
        )
        from langchain_core.messages import SystemMessage, HumanMessage
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=body.message),
        ])
        return {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "response": response.content,
            "compliance_refs": agent["compliance_refs"],
            "llm_model": agent["llm_model"] or "Claude Sonnet 4",
        }
    except Exception as e:
        return {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "response": f"[Assistant unavailable: {e!s}] This agent handles: {skills_list}. Compliance: {refs}.",
            "compliance_refs": agent["compliance_refs"],
            "llm_model": agent["llm_model"],
            "error": True,
        }

export interface AgentInfo {
  id: string; name: string; description: string; category: string; phase: string;
  compliance_refs: string[]; skills: string[]; tools: string[];
  llm_model: string | null; status: string;
}

export interface ToolInfo {
  id: string; name: string; description: string; category: string; used_by: string[];
}

export interface SkillInfo {
  id: string; name: string; agents: string[]; category: string;
}

export interface ReportInfo {
  id: string; regulation: string; article: string; title: string;
  description: string; status: string; agent: string; endpoint: string;
}

export const AGENTS: AgentInfo[] = [
  { id: "supervisor", name: "Supervisor / Orchestrator", description: "Routes tasks to specialist agents, enforces quality gates (auto ≥0.85, review 0.70–0.85, reject <0.70). EU AI Act Art. 14 human escalation.", category: "orchestration", phase: "all", compliance_refs: ["EU AI Act Art. 14", "ESPR Art. 9"], skills: ["task_routing", "quality_gate", "human_escalation", "confidence_scoring"], tools: ["langgraph_workflow", "audit_logger"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "regulatory_compliance", name: "Regulatory Compliance", description: "Interprets EU regulations (ESPR, Battery Reg 2023/1542, REACH, RoHS, WEEE). Uses EUR-Lex and regulatory knowledge base for legal citations.", category: "compliance", phase: "all", compliance_refs: ["ESPR", "Battery Reg 2023/1542", "REACH", "RoHS", "WEEE", "EU AI Act Art. 12"], skills: ["regulation_interpretation", "compliance_scoring", "gap_analysis", "citation_extraction"], tools: ["eurlex_search", "qdrant_vector_search", "neo4j_knowledge_graph"], llm_model: "Claude Opus 4", status: "active" },
  { id: "data_collection", name: "Data Collection", description: "Phases 0–3: Collects BOM, supplier declarations, LCA data, carbon footprint for DPP creation workflows.", category: "data", phase: "0-3", compliance_refs: ["Battery Reg Annex XIII", "ESPR Art. 9"], skills: ["bom_parsing", "supplier_declaration_extraction", "lca_data_collection", "carbon_footprint_calculation"], tools: ["document_parser", "neo4j_knowledge_graph", "kafka_producer"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "ddp_generation", name: "DDP Generation", description: "Phase 4: Generates complete DPP output (JSON-LD, QR code, NFC payload, RFID EPC). ESPR Art. 9 compliant.", category: "generation", phase: "4", compliance_refs: ["ESPR Art. 9", "Battery Reg Annex XIII", "GS1 Digital Link"], skills: ["jsonld_generation", "qr_code_generation", "nfc_payload_creation", "rfid_epc_encoding", "gs1_digital_link"], tools: ["data_carriers_service", "kafka_producer", "neo4j_knowledge_graph"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "validation", name: "Validation Agent", description: "Structural and regulatory validation of DPP data. Completeness thresholds: 0.35, 0.55, 0.70, 0.85.", category: "quality", phase: "4-5", compliance_refs: ["ESPR Art. 9(3)", "Battery Reg Annex XIII"], skills: ["structural_validation", "completeness_check", "cross_field_validation", "regulation_mapping"], tools: ["pydantic_validator", "neo4j_knowledge_graph"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "supply_chain", name: "Supply Chain Traceability", description: "Multi-tier supply chain traceability via Neo4j graph traversal. Battery Reg Art. 49 due diligence.", category: "traceability", phase: "3-6", compliance_refs: ["Battery Reg Art. 49", "EPCIS 2.0"], skills: ["graph_traversal", "supplier_verification", "material_tracing", "epcis_event_generation"], tools: ["neo4j_knowledge_graph", "epcis_service", "kafka_producer"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "knowledge_graph", name: "Knowledge Graph (GraphRAG)", description: "GraphRAG-R1 pipeline: SPO ingestion, hybrid vector+graph retrieval, story-building for regulatory reasoning.", category: "knowledge", phase: "all", compliance_refs: ["EU AI Act Art. 13"], skills: ["spo_extraction", "graph_maintenance", "hybrid_retrieval", "story_building"], tools: ["neo4j_knowledge_graph", "qdrant_vector_search"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "document_generation", name: "Document Generation", description: "Generates JSON-LD, XML, PDF, and GS1 QR code data carriers. Multi-format export.", category: "generation", phase: "4-5", compliance_refs: ["ESPR Art. 9", "GS1 ISO/IEC 18004"], skills: ["jsonld_export", "xml_export", "pdf_generation", "qr_generation"], tools: ["data_carriers_service", "template_engine"], llm_model: null, status: "active" },
  { id: "audit_trail", name: "Audit Trail", description: "EU AI Act Art. 12 record-keeping. Decision logging with hash chain, regulatory citations, confidence scores. 10-year retention.", category: "audit", phase: "all", compliance_refs: ["EU AI Act Art. 12", "EU AI Act Annex IV"], skills: ["decision_logging", "hash_chain_integrity", "citation_tracking", "retention_management"], tools: ["postgres_audit_log", "kafka_producer"], llm_model: null, status: "active" },
  { id: "anomaly_detection", name: "Anomaly Detection", description: "ML-based outlier detection (Isolation Forest) on DPP and supply chain data. Flags data quality issues.", category: "quality", phase: "4-6", compliance_refs: ["EU AI Act Art. 9", "EU AI Act Art. 15"], skills: ["isolation_forest", "heuristic_checks", "data_quality_scoring", "fraud_detection"], tools: ["ml_inference_service", "neo4j_knowledge_graph"], llm_model: null, status: "active" },
  { id: "predictive", name: "Predictive Risk Scoring", description: "Risk and compliance scoring via GradientBoosting models (ESPR, RoHS, REACH, carbon, circularity).", category: "ml", phase: "4-6", compliance_refs: ["EU AI Act Art. 9", "EU AI Act Art. 10", "EU AI Act Art. 15"], skills: ["espr_classification", "rohs_classification", "reach_classification", "carbon_prediction", "circularity_prediction"], tools: ["ml_inference_service", "gradient_boosting_models"], llm_model: null, status: "active" },
  { id: "circular_economy", name: "Circular Economy / Second Life", description: "Phase 7: Second-life assessment (SoH, refurbishment, repurpose, recycling pathway).", category: "lifecycle", phase: "7", compliance_refs: ["Battery Reg Art. 14", "WEEE Directive", "ESPR"], skills: ["soh_assessment", "refurbishment_evaluation", "repurpose_pathway", "recycling_routing"], tools: ["neo4j_knowledge_graph", "kafka_producer"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "recycling", name: "Recycling Agent", description: "Phase 8: Recycling operations — intake, dismantling, material recovery. Battery Reg recycled content targets.", category: "lifecycle", phase: "8", compliance_refs: ["Battery Reg Art. 8", "Battery Reg Art. 57", "WEEE"], skills: ["intake_processing", "dismantling_planning", "material_recovery", "recycled_content_tracking"], tools: ["neo4j_knowledge_graph", "kafka_producer"], llm_model: "Claude Sonnet 4", status: "active" },
  { id: "destruction", name: "Destruction Agent", description: "Phase 9: Authorization, documentation, archival for lifecycle closure. Generates destruction proof.", category: "lifecycle", phase: "9", compliance_refs: ["WEEE Directive", "Waste Framework Directive"], skills: ["authorization_check", "destruction_documentation", "archival", "certificate_generation"], tools: ["postgres_audit_log", "kafka_producer"], llm_model: null, status: "active" },
  { id: "human_review", name: "Human-in-the-Loop", description: "EU AI Act Art. 14 — human oversight. Interrupt workflow when confidence < 85%.", category: "governance", phase: "all", compliance_refs: ["EU AI Act Art. 14"], skills: ["workflow_interrupt", "approval_processing", "feedback_integration"], tools: ["langgraph_interrupt", "postgres_audit_log"], llm_model: null, status: "active" },
  { id: "synthesize", name: "Response Synthesizer", description: "Consolidates outputs from all agents into a final response with regulatory citations and confidence scores.", category: "orchestration", phase: "all", compliance_refs: ["EU AI Act Art. 13"], skills: ["response_consolidation", "citation_aggregation", "confidence_aggregation"], tools: ["audit_logger"], llm_model: "Claude Sonnet 4", status: "active" },
];

export const TOOLS: ToolInfo[] = [
  { id: "langgraph_workflow", name: "LangGraph Workflow Engine", description: "Graph-based agent orchestration with checkpointing and human-in-the-loop", category: "orchestration", used_by: ["supervisor", "human_review"] },
  { id: "langgraph_interrupt", name: "LangGraph Interrupt", description: "Pause workflow for human review (EU AI Act Art. 14)", category: "orchestration", used_by: ["human_review", "supervisor"] },
  { id: "eurlex_search", name: "EUR-Lex Legal Search", description: "Search EU legislation database for regulatory citations", category: "regulatory", used_by: ["regulatory_compliance"] },
  { id: "neo4j_knowledge_graph", name: "Neo4j Knowledge Graph", description: "Graph database for products, suppliers, regulations and supply chain traversal", category: "data", used_by: ["knowledge_graph", "supply_chain", "regulatory_compliance", "data_collection", "ddp_generation", "validation", "anomaly_detection", "circular_economy", "recycling"] },
  { id: "qdrant_vector_search", name: "Qdrant Vector Search", description: "Semantic vector search for regulatory documents and product data", category: "data", used_by: ["knowledge_graph", "regulatory_compliance"] },
  { id: "postgres_audit_log", name: "PostgreSQL Audit Log", description: "Append-only audit log with 10-year retention (EU AI Act Art. 12)", category: "audit", used_by: ["audit_trail", "human_review", "destruction"] },
  { id: "kafka_producer", name: "Kafka Event Producer", description: "Publish lifecycle events (created, updated, phase_transition, anomaly)", category: "messaging", used_by: ["data_collection", "ddp_generation", "supply_chain", "audit_trail", "anomaly_detection", "circular_economy", "recycling", "destruction"] },
  { id: "data_carriers_service", name: "Data Carriers (QR/NFC/RFID)", description: "Generate QR codes (GS1 Digital Link), NFC NDEF payloads, RFID SGTIN-96", category: "generation", used_by: ["ddp_generation", "document_generation"] },
  { id: "epcis_service", name: "EPCIS 2.0 Event Service", description: "Generate EPCIS 2.0 JSON-LD events for supply chain visibility", category: "traceability", used_by: ["supply_chain"] },
  { id: "ml_inference_service", name: "ML Inference Engine", description: "GradientBoosting model inference for compliance predictions", category: "ml", used_by: ["predictive", "anomaly_detection"] },
  { id: "gradient_boosting_models", name: "GradientBoosting Models v2", description: "Trained classifiers (ESPR, RoHS, REACH) and regressors (carbon, circularity)", category: "ml", used_by: ["predictive"] },
  { id: "pydantic_validator", name: "Pydantic v2 Validator", description: "Structural validation of DPP data models (87 fields Battery Passport)", category: "quality", used_by: ["validation"] },
  { id: "document_parser", name: "Document Parser", description: "Parse BOM, supplier declarations, safety data sheets, LCA reports", category: "data", used_by: ["data_collection"] },
  { id: "template_engine", name: "Template Engine", description: "Render PDF and XML documents from DPP data templates", category: "generation", used_by: ["document_generation"] },
  { id: "audit_logger", name: "Audit Logger", description: "Log agent decisions with confidence scores, citations, and hashes", category: "audit", used_by: ["supervisor", "synthesize"] },
];

export const REPORTS: ReportInfo[] = [
  { id: "ai_act_art12", regulation: "EU AI Act 2024/1689", article: "Art. 12", title: "Record-Keeping / Audit Trail", description: "All AI-powered decisions are logged with timestamps, agent IDs, confidence scores, input/output hashes, and regulatory citations. 10-year retention policy.", status: "implemented", agent: "audit_trail", endpoint: "/api/v1/dpp/audit-log" },
  { id: "ai_act_art13", regulation: "EU AI Act 2024/1689", article: "Art. 13", title: "Transparency / AI Disclosure", description: "AI system usage disclosed via response headers (X-AI-System, X-EU-AI-Act-Compliance). Agent Registry publicly accessible. All agents documented.", status: "implemented", agent: "supervisor", endpoint: "/api/v1/agents/registry" },
  { id: "ai_act_art14", regulation: "EU AI Act 2024/1689", article: "Art. 14", title: "Human Oversight", description: "Human-in-the-loop when confidence < 85%. Approval/rejection/modification workflow. Live queue with real-time polling.", status: "implemented", agent: "human_review", endpoint: "/api/v1/human-review/pending" },
  { id: "espr_art9", regulation: "ESPR", article: "Art. 9", title: "Digital Product Passport Data", description: "DPP creation, public access, and interoperability via GS1 Digital Link URI. JSON-LD, QR, NFC, RFID data carriers.", status: "implemented", agent: "ddp_generation", endpoint: "/api/v1/dpp/lifecycle/create" },
  { id: "battery_reg_annex_xiii", regulation: "Battery Regulation 2023/1542", article: "Annex XIII", title: "Battery Passport 87 Mandatory Fields", description: "Full 87-field Battery Passport per EU Regulation 2023/1542 Annex XIII. 7 data clusters, carbon class A–G, recycled content targets.", status: "implemented", agent: "ddp_generation", endpoint: "/api/v1/dpp/battery" },
  { id: "battery_reg_art49", regulation: "Battery Regulation 2023/1542", article: "Art. 49", title: "Supply Chain Due Diligence", description: "Multi-tier supply chain traceability from product to raw materials via Neo4j knowledge graph.", status: "implemented", agent: "supply_chain", endpoint: "/api/v1/dpp/sector/supply-chain/{gtin}" },
  { id: "ai_act_annex_iv", regulation: "EU AI Act 2024/1689", article: "Annex IV", title: "Technical Documentation", description: "Agent registry, skill registry, tool registry. Full architecture transparency and compliance documentation.", status: "implemented", agent: "supervisor", endpoint: "/api/v1/agents/registry" },
];

export function buildSkills(): SkillInfo[] {
  const skills: SkillInfo[] = [];
  const seen = new Set<string>();
  for (const a of AGENTS) {
    for (const s of a.skills) {
      if (!seen.has(s)) {
        seen.add(s);
        skills.push({
          id: s,
          name: s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          agents: AGENTS.filter((ag) => ag.skills.includes(s)).map((ag) => ag.id),
          category: a.category,
        });
      }
    }
  }
  return skills;
}

"""
System Assistant — unified natural language interface to the agentic system.
Routes user intent to real workflows, agents, and tools.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.i18n import get_locale, t

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)
    context: Optional[dict[str, Any]] = None


AGENT_REGISTRY_SUMMARY = """Available agents:
- supervisor: Orchestrates all agents, quality gates (≥0.85 auto, 0.70-0.85 review, <0.70 reject)
- regulatory_compliance: Interprets ESPR, Battery Reg, REACH, RoHS, WEEE with EUR-Lex citations
- data_collection: Collects BOM, supplier data, LCA, carbon footprint (phases 0-3)
- ddp_generation: Generates complete DPP (JSON-LD, QR, NFC, RFID) — ESPR Art. 9
- validation: Structural + regulatory validation, completeness thresholds
- supply_chain: Multi-tier traceability via Neo4j, Battery Reg Art. 49
- knowledge_graph: GraphRAG-R1, hybrid vector+graph retrieval
- document_generation: JSON-LD, XML, PDF, GS1 QR export
- audit_trail: EU AI Act Art. 12 logging, hash chain, 10-year retention
- anomaly_detection: Isolation Forest outlier detection on DPP data
- predictive: Risk scoring via GradientBoosting (ESPR, RoHS, REACH, carbon, circularity)
- circular_economy: Second-life assessment (SoH, refurbishment, repurpose)
- recycling: Phase 8 operations (intake, dismantling, material recovery)
- destruction: Phase 9 (authorization, documentation, archival)
- human_review: EU AI Act Art. 14 human-in-the-loop
- synthesize: Consolidates agent outputs with citations"""

TOOLS_SUMMARY = """Available tools:
- LangGraph workflows: DDP Creation (6 steps), Lifecycle Update (7 types), DDP Audit (6 steps)
- Neo4j Knowledge Graph: Product, Supplier, Regulation relationships + supply chain traversal
- Qdrant Vector Search: Semantic search for regulatory documents
- PostgreSQL Audit Log: Append-only with 10-year retention
- Kafka Events: ddp.created, ddp.updated, ddp.phase_transition, ddp.anomaly_detected
- Data Carriers: QR (GS1 Digital Link), NFC NDEF, RFID SGTIN-96
- EPCIS 2.0: Supply chain event tracking (ObjectEvent, AggregationEvent)
- ML Models v2: 5 GradientBoosting models (ESPR, RoHS, REACH, carbon, circularity)
- Pydantic Validators: 87-field Battery Passport, multi-sector DPP validation"""

API_ACTIONS = """Actions you can trigger for the user:
1. COMPLIANCE_CHECK: Run a compliance check on a product — needs a query and optionally a GTIN
   → POST /api/v1/compliance/check {query, product_gtin}
2. CREATE_DPP: Create a new Digital Product Passport — needs GTIN, serial number
   → POST /api/v1/dpp/lifecycle/create {product_gtin, serial_number, batch_number}
3. CREATE_BATTERY: Create a Battery Passport — needs GTIN, serial, batch, manufacturer data
   → POST /api/v1/dpp/battery {gtin, serial_number, batch_number, ...}
4. TRACE_SUPPLY_CHAIN: Trace supply chain for a product — needs GTIN
   → GET /api/v1/dpp/sector/supply-chain/{gtin}
5. ML_PREDICT: Run ML compliance prediction — needs sector and completeness
   → GET /api/v1/ml/predict/compliance?sector=X&ddp_completeness=Y
6. VIEW_AUDIT: View audit log entries
   → GET /api/v1/dpp/audit-log
7. VIEW_CALENDAR: View compliance calendar deadlines
   → GET /api/v1/compliance/calendar
8. VIEW_AGENTS: View all registered agents
   → GET /api/v1/agents/registry
9. LIFECYCLE_UPDATE: Update a product lifecycle phase
   → PUT /api/v1/dpp/lifecycle/{gtin}/{serial}/update {update_type}

When the user asks to DO something, include an "action" object in your response with:
- action_type: one of the above
- action_params: the parameters needed
- action_endpoint: the API endpoint
- action_method: GET or POST or PUT

When the user asks a QUESTION, answer directly using your knowledge of EU regulations."""


@router.post("/chat")
async def system_chat(body: ChatRequest, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """System-level assistant — routes to real agentic workflows."""
    lang = "French" if locale == "fr" else "English"

    history_text = ""
    for msg in body.history[-6:]:
        history_text += f"\n{msg.role.upper()}: {msg.content}"

    system_prompt = f"""You are the central AI assistant of the EU Digital Product Passport (DPP) Platform.
You have DIRECT ACCESS to a multi-agent system with 16 specialized agents and 3 LangGraph workflows.

{AGENT_REGISTRY_SUMMARY}

{TOOLS_SUMMARY}

{API_ACTIONS}

IMPORTANT RULES:
- Respond in {lang}
- When the user wants to EXECUTE an action (create DPP, run compliance, trace supply chain, predict compliance),
  include an "action" JSON block that the frontend will execute.
- Format actions as: [ACTION:action_type|param1=value1|param2=value2]
- When the user asks QUESTIONS about regulations, agents, tools, or the platform, answer directly.
- Always cite the relevant EU regulation articles.
- Always mention which agent handles the task.
- Be concrete and actionable — tell the user exactly what will happen.
- If you need more information from the user, ask specific questions.

Context: The user is on page "{body.context.get('page', 'unknown') if body.context else 'unknown'}"
"""

    try:
        from app.services.llm_providers import get_best_available_llm
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        llm, provider_name = get_best_available_llm(task="general", temperature=0.3, max_tokens=2000)

        messages = [SystemMessage(content=system_prompt)]
        for msg in body.history[-6:]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=body.message))

        response = await llm.ainvoke(messages)
        response_text = response.content

        action = _extract_action(response_text)

        if action:
            action_result = await _execute_action(action)
            response_text = response_text.split("[ACTION:")[0].strip()
            return {
                "response": response_text,
                "action": action,
                "action_result": action_result,
                "agent_used": action.get("agent", "supervisor"),
            }

        return {
            "response": response_text,
            "action": None,
            "action_result": None,
            "agent_used": "supervisor",
        }

    except Exception as e:
        return {
            "response": _fallback_response(body.message, locale),
            "action": None,
            "action_result": None,
            "agent_used": "supervisor",
            "error": str(e),
        }


def _extract_action(text: str) -> Optional[dict[str, Any]]:
    """Parse [ACTION:type|param=value] from LLM response."""
    import re
    match = re.search(r'\[ACTION:(\w+)(?:\|(.+?))?\]', text)
    if not match:
        return None
    action_type = match.group(1)
    params: dict[str, str] = {}
    if match.group(2):
        for pair in match.group(2).split("|"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k.strip()] = v.strip()

    action_map = {
        "COMPLIANCE_CHECK": {"endpoint": "/api/v1/compliance/check", "method": "POST", "agent": "regulatory_compliance"},
        "CREATE_DPP": {"endpoint": "/api/v1/dpp/lifecycle/create", "method": "POST", "agent": "data_collection"},
        "CREATE_BATTERY": {"endpoint": "/api/v1/dpp/battery", "method": "POST", "agent": "ddp_generation"},
        "TRACE_SUPPLY_CHAIN": {"endpoint": "/api/v1/dpp/sector/supply-chain/{gtin}", "method": "GET", "agent": "supply_chain"},
        "ML_PREDICT": {"endpoint": "/api/v1/ml/predict/compliance", "method": "GET", "agent": "predictive"},
        "VIEW_AUDIT": {"endpoint": "/api/v1/dpp/audit-log", "method": "GET", "agent": "audit_trail"},
        "VIEW_CALENDAR": {"endpoint": "/api/v1/compliance/calendar", "method": "GET", "agent": "regulatory_compliance"},
        "VIEW_AGENTS": {"endpoint": "/api/v1/agents/registry", "method": "GET", "agent": "supervisor"},
    }

    info = action_map.get(action_type, {})
    return {"type": action_type, "params": params, **info}


async def _execute_action(action: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Execute the action by calling the internal API endpoint."""
    import httpx

    endpoint = action.get("endpoint", "")
    method = action.get("method", "GET")
    params = action.get("params", {})

    if "{gtin}" in endpoint:
        gtin = params.pop("gtin", "unknown")
        endpoint = endpoint.replace("{gtin}", gtin)

    base = "http://localhost:8000"
    url = f"{base}{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                query = {k: v for k, v in params.items() if v}
                resp = await client.get(url, params=query)
            else:
                body = {}
                if action["type"] == "COMPLIANCE_CHECK":
                    body = {"query": params.get("query", "General compliance check"), "product_gtin": params.get("gtin")}
                elif action["type"] == "CREATE_DPP":
                    body = {"product_gtin": params.get("gtin", ""), "serial_number": params.get("serial", ""), "query": "Create DPP"}
                elif action["type"] == "CREATE_BATTERY":
                    body = {"gtin": params.get("gtin", ""), "serial_number": params.get("serial", ""), "batch_number": params.get("batch", "")}
                resp = await client.post(url, json=body)

            if resp.status_code < 400:
                return resp.json()
            return {"error": f"API returned {resp.status_code}", "detail": resp.text[:200]}
    except Exception as e:
        return {"error": str(e)}


def _fallback_response(message: str, locale: str) -> str:
    """Provide a helpful fallback when LLM is unavailable."""
    msg_lower = message.lower()

    if locale == "fr":
        if any(w in msg_lower for w in ["conformité", "compliance", "conforme"]):
            return "Pour lancer un contrôle de conformité, allez sur la page Compliance Check ou dites-moi le GTIN du produit. L'agent Regulatory Compliance analysera les réglementations ESPR, Battery Reg, REACH, RoHS et WEEE."
        if any(w in msg_lower for w in ["créer", "nouveau", "passeport", "dpp"]):
            return "Pour créer un DPP, j'ai besoin du GTIN-14 et du numéro de série. Le workflow de création passe par 6 étapes : classification → collecte de données → génération DDP → validation → conformité → publication."
        if any(w in msg_lower for w in ["chaîne", "supply", "traça"]):
            return "Pour tracer une chaîne d'approvisionnement, donnez-moi le GTIN-14 du produit. L'agent Supply Chain utilisera Neo4j pour la traversée de graphe multi-niveaux (Battery Reg Art. 49)."
        if any(w in msg_lower for w in ["agent", "registre"]):
            return "La plateforme compte 16 agents IA spécialisés : Supervisor, Regulatory Compliance, Data Collection, DDP Generation, Validation, Supply Chain, Knowledge Graph, Document Generation, Audit Trail, Anomaly Detection, Predictive, Circular Economy, Recycling, Destruction, Human Review, Synthesize. Consultez le Registre d'Agents pour les détails."
        return "Je suis l'assistant du système EU DPP. Je peux : lancer un contrôle de conformité, créer un DPP, tracer une chaîne d'approvisionnement, prédire la conformité ML, ou répondre à vos questions sur les réglementations UE. Que souhaitez-vous faire ?"
    else:
        if any(w in msg_lower for w in ["compliance", "check", "compliant"]):
            return "To run a compliance check, go to the Compliance Check page or tell me the product GTIN. The Regulatory Compliance agent will analyze ESPR, Battery Reg, REACH, RoHS and WEEE regulations."
        if any(w in msg_lower for w in ["create", "new", "passport", "dpp"]):
            return "To create a DPP, I need the GTIN-14 and serial number. The creation workflow goes through 6 steps: classify → collect data → generate DDP → validate → compliance → publish."
        if any(w in msg_lower for w in ["supply", "chain", "trace"]):
            return "To trace a supply chain, give me the product GTIN-14. The Supply Chain agent will use Neo4j for multi-tier graph traversal (Battery Reg Art. 49)."
        if any(w in msg_lower for w in ["agent", "registry"]):
            return "The platform has 16 specialized AI agents: Supervisor, Regulatory Compliance, Data Collection, DDP Generation, Validation, Supply Chain, Knowledge Graph, Document Generation, Audit Trail, Anomaly Detection, Predictive, Circular Economy, Recycling, Destruction, Human Review, Synthesize. See the Agent Registry for details."
        return "I'm the EU DPP system assistant. I can: run compliance checks, create DPPs, trace supply chains, predict ML compliance, or answer your questions about EU regulations. What would you like to do?"

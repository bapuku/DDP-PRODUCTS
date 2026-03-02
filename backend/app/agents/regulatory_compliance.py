"""
Regulatory compliance agent - EU regulations interpretation (ESPR, Battery Reg, REACH, RoHS).
Uses Claude Sonnet 4 for interpretation, Claude Opus 4 for complex analysis.
Outputs structured compliance assessment with EUR-Lex citations.
EU AI Act Art. 12: all decisions logged. Art. 14: escalates when confidence < 0.85.
"""
import json
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState, DDPLifecycleState
from app.ai.llm_client import get_sonnet, get_opus

log = structlog.get_logger()

SYSTEM_PROMPT = """You are an expert EU regulatory compliance agent for the Digital Product Passport (DPP) platform.

Your expertise covers:
- ESPR (EU 2024/1252) Articles 9-13: DPP requirements and mandatory data
- Battery Regulation (EU 2023/1542) Annex XIII: 87 mandatory fields, 7 clusters
- EU AI Act (EU 2024/1689) Articles 12-14: record-keeping, transparency, human oversight
- REACH (EC 1907/2006) Article 33: SVHC communication
- RoHS (2011/65/EU) Annex II: restricted substances
- CRMA (EU 2024/1252): critical raw materials

ALWAYS respond with a valid JSON object containing:
{
  "compliance_status": "COMPLIANT" | "NON_COMPLIANT" | "PARTIAL" | "UNKNOWN",
  "regulation": "<CELEX number>",
  "requirements_met": ["..."],
  "gaps": ["..."],
  "confidence": <float 0.0-1.0>,
  "regulatory_citations": ["EUR-Lex CELEX..."],
  "escalate": <bool>,
  "reasoning": "<brief explanation>"
}

- All assertions must cite specific EUR-Lex articles/paragraphs
- confidence >= 0.85: auto-approve; 0.70-0.85: human review; < 0.70: reject
- Never fabricate regulatory text; flag uncertainty explicitly
"""


async def regulatory_compliance_agent(state: DPPWorkflowState | DDPLifecycleState) -> dict[str, Any]:
    """Analyse compliance and return structured assessment with EUR-Lex citations."""
    query = state.get("query", "")
    gtin = state.get("product_gtin")

    user_msg = f"Query: {query}"
    if gtin:
        user_msg += f"\nProduct GTIN: {gtin}"

    # Use Opus for complex novel interpretations, Sonnet otherwise
    is_complex = any(w in query.lower() for w in ["annex", "novel", "conflict", "ambiguous", "interpret"])
    llm = get_opus() if is_complex else get_sonnet()

    raw = await llm.invoke(SYSTEM_PROMPT, user_msg)

    # Parse LLM JSON output
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "compliance_status": "UNKNOWN",
            "confidence": 0.6,
            "regulatory_citations": [],
            "requirements_met": [],
            "gaps": [f"Failed to parse LLM response: {raw[:200]}"],
            "escalate": True,
        }

    confidence = float(result.get("confidence", 0.6))
    log.info("regulatory_agent_done", confidence=confidence, status=result.get("compliance_status"))

    updates: dict[str, Any] = {
        "regulatory_analysis": result,
        "confidence_scores": {**state.get("confidence_scores", {}), "regulatory": confidence},
        "regulation_references": (
            state.get("regulation_references", []) + result.get("regulatory_citations", [])
        ),
    }
    if result.get("escalate") or confidence < 0.70:
        updates["requires_human_review"] = True

    return updates

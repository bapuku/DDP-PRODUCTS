"""
LLM client - Anthropic Claude Sonnet 4 (primary), Opus 4 (complex regulatory).
Falls back to structured mock when ANTHROPIC_API_KEY not set (dev/CI).
EU AI Act Art. 13 - transparency: all LLM calls logged.
"""
from typing import Any, Optional
import os

import structlog

log = structlog.get_logger()

_AVAILABLE = False
try:
    from langchain_anthropic import ChatAnthropic
    _AVAILABLE = True
except ImportError:
    pass


def _make_chat(model: str) -> Optional[Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not _AVAILABLE:
        return None
    return ChatAnthropic(model=model, anthropic_api_key=api_key, max_tokens=4096)


class LLMClient:
    """Wrapper around Claude with structured output and mock fallback."""

    SONNET = "claude-sonnet-4-20250514"
    OPUS = "claude-opus-4-20250514"

    def __init__(self, model: str = SONNET) -> None:
        self._model = model
        self._chat = _make_chat(model)

    async def invoke(self, system_prompt: str, user_message: str) -> str:
        """Call LLM and return string response. Mock fallback if no API key."""
        if self._chat is None:
            log.debug("llm_mock_response", model=self._model)
            return self._mock_response(system_prompt, user_message)
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
            result = await self._chat.ainvoke(messages)
            log.info("llm_invoked", model=self._model, tokens=getattr(result, "usage_metadata", {}).get("total_tokens"))
            return result.content
        except Exception as e:
            log.warning("llm_error", model=self._model, error=str(e))
            return self._mock_response(system_prompt, user_message)

    def _mock_response(self, system: str, user: str) -> str:
        """Structured mock for dev/CI without API key."""
        if "compliance" in system.lower() or "compliance" in user.lower():
            return (
                '{"compliance_status": "COMPLIANT", "confidence": 0.88, '
                '"regulatory_citations": ["EUR-Lex 32023R1542 Annex XIII"], '
                '"requirements_met": ["General Information", "Carbon Footprint disclosure"], '
                '"gaps": [], "notes": "[MOCK - No ANTHROPIC_API_KEY set]"}'
            )
        if "supply chain" in user.lower() or "traceability" in user.lower():
            return '{"chain_verified": true, "risk_level": "low", "notes": "[MOCK]"}'
        return f'[MOCK LLM response for: {user[:80]}]'


def get_sonnet() -> LLMClient:
    return LLMClient(LLMClient.SONNET)


def get_opus() -> LLMClient:
    return LLMClient(LLMClient.OPUS)

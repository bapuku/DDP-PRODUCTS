"""
Human review node - EU AI Act Article 14 human-in-the-loop.
"""
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState, DDPLifecycleState

log = structlog.get_logger()


async def human_review_node(state: DPPWorkflowState | DDPLifecycleState) -> dict[str, Any]:
    """Process human feedback after interrupt (or no-op if not required)."""
    feedback = state.get("human_feedback")
    if state.get("requires_human_review") and feedback:
        log.info("human_feedback_received", feedback_len=len(feedback))
        return {"requires_human_review": False}
    return {}

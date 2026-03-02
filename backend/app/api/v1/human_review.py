"""
Human review API - live queue and action (approve/reject/modify).
EU AI Act Article 14. Frontend polls pending-reviews and submits actions here.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.state import DPPWorkflowState
from app.agents.workflow import get_compiled_workflow
from app.api.v1.shared_state import pending_reviews as _pending_reviews

router = APIRouter()


@router.get("/pending")
async def list_pending() -> list[dict]:
    """List threads pending human review (same as GET /workflow/pending-reviews)."""
    return [{"thread_id": tid, **info} for tid, info in _pending_reviews.items()]


class HumanReviewActionBody(BaseModel):
    action: str = Field(..., description="approve | reject | modify")
    feedback: Optional[str] = Field(None, max_length=2000)


@router.post("/{thread_id}/action")
async def submit_action(thread_id: str, body: HumanReviewActionBody) -> dict:
    """Approve, reject, or modify (with feedback) and continue workflow."""
    if thread_id not in _pending_reviews:
        raise HTTPException(status_code=404, detail="Thread not found or already processed")
    feedback = body.feedback or f"Human {body.action}"
    try:
        graph = get_compiled_workflow()
        config = {"configurable": {"thread_id": thread_id}}
        update: DPPWorkflowState = {"human_feedback": feedback, "requires_human_review": False}
        result = await graph.ainvoke(update, config=config)
        del _pending_reviews[thread_id]
        return {"status": "processed", "action": body.action, "final_response": result.get("final_response")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

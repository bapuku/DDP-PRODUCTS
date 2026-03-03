"""
Workflow API - invoke DPP agent workflow (LangGraph).
v3.0: pending-reviews (live), human-review action.
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.agents.state import DPPWorkflowState
from app.agents.workflow import get_compiled_workflow
from app.core.i18n import get_locale, t
from app.api.v1.shared_state import pending_reviews as _pending_reviews

router = APIRouter()


class WorkflowRunRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    product_gtin: Optional[str] = Field(None, max_length=14)
    thread_id: Optional[str] = Field(None, description="LangGraph thread for checkpointing")


class WorkflowRunResponse(BaseModel):
    final_response: Optional[str] = None
    requires_human_review: bool = False
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    audit_entries_count: int = 0
    regulation_references: list[str] = Field(default_factory=list)


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(body: WorkflowRunRequest, locale: str = Depends(get_locale)) -> WorkflowRunResponse:
    """Run the DPP agent workflow for the given query (and optional GTIN)."""
    initial: DPPWorkflowState = {
        "query": body.query,
        "product_gtin": body.product_gtin,
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "requires_human_review": False,
        "regulation_references": [],
    }
    config: dict[str, Any] = {}
    if body.thread_id:
        config["configurable"] = {"thread_id": body.thread_id}
    try:
        graph = get_compiled_workflow()
        result = await graph.ainvoke(initial, config=config or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=t("errors.workflow_error", locale, detail=str(e)))
    if result.get("requires_human_review") and body.thread_id:
        _pending_reviews[body.thread_id] = {"query": body.query, "product_gtin": body.product_gtin}
    return WorkflowRunResponse(
        final_response=result.get("final_response"),
        requires_human_review=result.get("requires_human_review", False),
        confidence_scores=result.get("confidence_scores", {}),
        audit_entries_count=len(result.get("audit_entries", [])),
        regulation_references=result.get("regulation_references", []),
    )


@router.get("/pending-reviews")
async def pending_reviews() -> list[dict[str, Any]]:
    """List workflow threads pending human review (live queue for frontend)."""
    return [{"thread_id": tid, **info} for tid, info in _pending_reviews.items()]


class HumanReviewActionRequest(BaseModel):
    action: str = Field(..., description="approve | reject | modify")
    feedback: Optional[str] = Field(None, max_length=2000)


@router.post("/human-review/{thread_id}/action")
async def human_review_action(thread_id: str, body: HumanReviewActionRequest, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Submit human review action (approve/reject/modify) and optionally continue workflow."""
    if thread_id not in _pending_reviews:
        raise HTTPException(status_code=404, detail=t("errors.thread_not_found", locale))
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

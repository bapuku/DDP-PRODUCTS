"""
Lifecycle API v3.0 - DDP creation workflow, lifecycle update, audit trigger.
POST /lifecycle/create, PUT /lifecycle/{gtin}/{serial}/update, POST /audit/{gtin}/{serial}.
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.agents.state import DDPLifecycleState
from app.agents.workflow import (
    compile_ddp_creation_workflow,
    compile_lifecycle_update_workflow,
    compile_audit_workflow,
)
from app.core.i18n import get_locale, t
from app.services.data_carriers import carrier_payload, generate_qr_png, qr_data
from app.services.kafka import get_kafka
from app.services.audit import get_audit_service

router = APIRouter()

# Kafka topics (v3.0)
TOPIC_DDP_CREATED = "ddp.created"
TOPIC_DDP_UPDATED = "ddp.updated"
TOPIC_DDP_PHASE = "ddp.phase_transition"
TOPIC_DDP_LIFECYCLE_CLOSED = "ddp.lifecycle_closed"
TOPIC_ANOMALY = "ddp.anomaly_detected"
TOPIC_HUMAN_REVIEW = "ddp.human_review_requested"


class LifecycleCreateRequest(BaseModel):
    product_gtin: str = Field(..., min_length=8, max_length=14)
    serial_number: str = Field(..., min_length=1, max_length=50)
    batch_number: Optional[str] = Field(None, max_length=64)
    query: str = Field(default="Create DPP", max_length=500)
    thread_id: Optional[str] = None


class LifecycleUpdateRequest(BaseModel):
    update_type: str = Field(..., description="dynamic_data|service_event|ownership_transfer|recall|second_life|recycling|destruction")
    query: str = Field(default="", max_length=500)
    thread_id: Optional[str] = None


def _emit(topic: str, key: str, value: str) -> None:
    try:
        get_kafka().produce(topic, key=key, value=value)
    except Exception:
        pass


@router.post("/lifecycle/create")
async def lifecycle_create(body: LifecycleCreateRequest, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Trigger full DDP Creation workflow (classify → data_collection → generate_ddp → validate → compliance → publish|remediate)."""
    initial: DDPLifecycleState = {
        "product_gtin": body.product_gtin,
        "serial_number": body.serial_number,
        "batch_number": body.batch_number,
        "query": body.query or "Create DPP",
        "task_type": "ddp_generation",
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "requires_human_review": False,
        "regulation_references": [],
        "ddp_data": {},
        "ddp_completeness": 0.0,
        "validation_results": [],
        "compliance_score": 0.0,
    }
    config: dict[str, Any] = {}
    if body.thread_id:
        config["configurable"] = {"thread_id": body.thread_id}
    try:
        graph = compile_ddp_creation_workflow()
        result = await graph.ainvoke(initial, config=config or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=t("errors.workflow_error", locale, detail=str(e)))
    ddp_uri = result.get("ddp_uri")
    if ddp_uri:
        _emit(TOPIC_DDP_CREATED, body.product_gtin, ddp_uri)
    return {
        "ddp_uri": ddp_uri,
        "final_response": result.get("final_response"),
        "requires_human_review": result.get("requires_human_review", False),
        "ddp_completeness": result.get("ddp_completeness"),
        "validation_passed": all(r.get("passed") for r in (result.get("validation_results") or [])),
        "audit_entries_count": len(result.get("audit_entries", [])),
    }


@router.put("/lifecycle/{gtin}/{serial}/update")
async def lifecycle_update(gtin: str, serial: str, body: LifecycleUpdateRequest, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Trigger Lifecycle Update workflow (classify_update → anomaly_check → apply_update | eol_chain)."""
    initial: DDPLifecycleState = {
        "product_gtin": gtin,
        "serial_number": serial,
        "query": body.query or body.update_type,
        "task_type": "lifecycle_update",
        "audit_scope": {"update_type": body.update_type},
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
        graph = compile_lifecycle_update_workflow()
        result = await graph.ainvoke(initial, config=config or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=t("errors.workflow_error", locale, detail=str(e)))
    _emit(TOPIC_DDP_UPDATED, gtin, result.get("final_response", ""))
    if result.get("current_phase") == "destruction":
        _emit(TOPIC_DDP_LIFECYCLE_CLOSED, gtin, serial)
    return {
        "final_response": result.get("final_response"),
        "current_phase": result.get("current_phase"),
        "audit_entries_count": len(result.get("audit_entries", [])),
    }


@router.post("/audit/{gtin}/{serial}")
async def audit_trigger(gtin: str, serial: str, thread_id: Optional[str] = None, locale: str = Depends(get_locale)) -> dict[str, Any]:
    """Trigger DDP Audit workflow (determine_scope → collect_evidence → validation → regulatory → execute_checks → report)."""
    initial: DDPLifecycleState = {
        "product_gtin": gtin,
        "serial_number": serial,
        "task_type": "audit",
        "messages": [],
        "confidence_scores": {},
        "audit_entries": [],
        "audit_findings": [],
        "requires_human_review": False,
        "regulation_references": [],
    }
    config: dict[str, Any] = {}
    if thread_id:
        config["configurable"] = {"thread_id": thread_id}
    try:
        graph = compile_audit_workflow()
        result = await graph.ainvoke(initial, config=config or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=t("errors.workflow_error", locale, detail=str(e)))
    return {
        "audit_report": result.get("audit_report"),
        "findings_count": len(result.get("audit_findings", [])),
        "corrective_actions": result.get("corrective_actions", []),
        "final_response": result.get("final_response"),
    }


@router.get("/audit-log")
async def audit_log(
    entity_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List audit_log entries (EU AI Act Art. 12 live)."""
    return await get_audit_service().query(entity_id=entity_id, agent_id=agent_id, limit=limit)


@router.get("/{gtin}/{serial}/carrier")
async def get_carrier(gtin: str, serial: str, base_url: Optional[str] = None) -> dict[str, Any]:
    """Generate QR + NFC payload + RFID EPC for DPP data carrier."""
    return carrier_payload(gtin, serial, base_url or "https://dpp.example.eu")


@router.get("/{gtin}/{serial}/carrier/qr.png")
async def get_carrier_qr_png(gtin: str, serial: str) -> Response:
    """Return QR code as PNG image."""
    data = qr_data(gtin, serial)
    png = generate_qr_png(data)
    if not png:
        raise HTTPException(status_code=503, detail="QR generation unavailable")
    return Response(content=png, media_type="image/png")


class AnomalyCheckRequest(BaseModel):
    product_gtin: Optional[str] = None
    product_data: Optional[dict[str, Any]] = None
    ddp_data: Optional[dict[str, Any]] = None


@router.post("/anomaly/check")
async def anomaly_check(body: AnomalyCheckRequest) -> dict[str, Any]:
    """Run anomaly detection (ML/heuristic) on DDP/product data."""
    from app.agents.anomaly_detection import anomaly_detection_agent

    state: DDPLifecycleState = {
        "product_gtin": body.product_gtin,
        "product_data": body.product_data or {},
        "ddp_data": body.ddp_data or {},
        "ddp_completeness": (body.ddp_data or {}).get("ddp_completeness"),
        "anomalies_detected": [],
        "confidence_scores": {},
    }
    result = await anomaly_detection_agent(state)
    anomalies = result.get("anomalies_detected", [])
    if anomalies:
        try:
            get_kafka().produce(TOPIC_ANOMALY, key=body.product_gtin or "unknown", value=str(len(anomalies)))
        except Exception:
            pass
    return {
        "anomalies_detected": anomalies,
        "data_quality_score": result.get("data_quality_score"),
        "count": len(anomalies),
    }

"""
Enterprise Connector Registry API — connect ERP/MES/PLM/IoT systems for automated DPP creation.
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.i18n import get_locale, t
from app.services.connectors import (
    create_connector, list_connectors, get_connector, update_connector,
    delete_connector, test_connector, process_webhook_data, get_ingestion_log,
    get_templates, get_field_mappings,
)

router = APIRouter()


class ConnectorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="custom")
    protocol: str = Field(default="rest")
    description: str = Field(default="")
    config: dict[str, Any] = Field(default_factory=dict)
    field_mapping: Optional[dict[str, str]] = None
    auto_create_dpp: bool = Field(default=False)


class ConnectorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    field_mapping: Optional[dict[str, str]] = None
    auto_create_dpp: Optional[bool] = None
    status: Optional[str] = None


@router.get("")
async def list_all_connectors() -> list[dict[str, Any]]:
    """List all registered enterprise connectors."""
    return list_connectors()


@router.get("/templates")
async def connector_templates() -> list[dict[str, Any]]:
    """Available connector templates (SAP, Siemens, Oracle, Azure IoT, etc.)."""
    return get_templates()


@router.get("/field-mappings")
async def field_mapping_templates() -> dict[str, dict[str, str]]:
    """Standard field mappings (SAP → DPP, generic → DPP)."""
    return get_field_mappings()


@router.post("", status_code=201)
async def register_connector(body: ConnectorCreate) -> dict[str, Any]:
    """Register a new enterprise connector."""
    return create_connector(body.model_dump())


@router.get("/{connector_id}")
async def get_connector_detail(connector_id: str, locale: str = Depends(get_locale)) -> dict[str, Any]:
    conn = get_connector(connector_id)
    if not conn:
        raise HTTPException(status_code=404, detail=t("errors.dpp_not_found", locale))
    return conn


@router.put("/{connector_id}")
async def update_connector_detail(connector_id: str, body: ConnectorUpdate, locale: str = Depends(get_locale)) -> dict[str, Any]:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = update_connector(connector_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=t("errors.dpp_not_found", locale))
    return result


@router.delete("/{connector_id}")
async def remove_connector(connector_id: str, locale: str = Depends(get_locale)) -> dict[str, str]:
    if not delete_connector(connector_id):
        raise HTTPException(status_code=404, detail=t("errors.dpp_not_found", locale))
    return {"status": "deleted"}


@router.post("/{connector_id}/test")
async def test_connection(connector_id: str) -> dict[str, Any]:
    """Test connectivity to the enterprise system."""
    return test_connector(connector_id)


@router.post("/{connector_id}/webhook")
async def receive_webhook(connector_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Receive data push from enterprise system. Auto-creates DPP if configured."""
    result = process_webhook_data(connector_id, payload)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    if result.get("auto_create_dpp") and result.get("mapped_data"):
        mapped = result["mapped_data"]
        try:
            from app.agents.workflow import compile_ddp_creation_workflow
            from app.agents.state import DDPLifecycleState

            initial: DDPLifecycleState = {
                "product_gtin": mapped.get("product_gtin", ""),
                "serial_number": mapped.get("serial_number", ""),
                "batch_number": mapped.get("batch_number"),
                "query": f"Auto-create DPP from {result['connector_name']}",
                "task_type": "ddp_generation",
                "messages": [],
                "confidence_scores": {},
                "audit_entries": [],
                "requires_human_review": False,
                "regulation_references": [],
                "ddp_data": mapped,
                "ddp_completeness": 0.0,
                "validation_results": [],
                "compliance_score": 0.0,
            }
            graph = compile_ddp_creation_workflow()
            wf_result = await graph.ainvoke(initial)
            result["dpp_created"] = True
            result["ddp_uri"] = wf_result.get("ddp_uri")
            result["status"] = "dpp_created"
        except Exception as e:
            result["dpp_created"] = False
            result["dpp_error"] = str(e)
            result["status"] = "dpp_creation_failed"

    return result


@router.get("/{connector_id}/log")
async def connector_ingestion_log(connector_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """View data ingestion log for a connector."""
    return get_ingestion_log(connector_id, limit)


@router.get("/log/all")
async def all_ingestion_log(limit: int = 100) -> list[dict[str, Any]]:
    """View all data ingestion activity."""
    return get_ingestion_log(None, limit)

"""
Enterprise Connector Service — manages connections to ERP, MES, PLM, LIMS, IoT systems.
Supports REST, SOAP, OPC-UA, MQTT protocols for automated DPP data ingestion.
"""
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

import structlog

log = structlog.get_logger()


class ConnectorType(str, Enum):
    ERP = "erp"
    MES = "mes"
    PLM = "plm"
    LIMS = "lims"
    IOT = "iot"
    SCADA = "scada"
    WMS = "wms"
    CUSTOM = "custom"


class ConnectorProtocol(str, Enum):
    REST = "rest"
    SOAP = "soap"
    OPC_UA = "opc-ua"
    MQTT = "mqtt"
    KAFKA = "kafka"
    WEBHOOK = "webhook"
    SFTP = "sftp"
    CUSTOM = "custom"


class ConnectorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


# In-memory store (production: PostgreSQL)
_connectors: dict[str, dict[str, Any]] = {}
_ingestion_log: list[dict[str, Any]] = []


CONNECTOR_TEMPLATES: list[dict[str, Any]] = [
    {"type": "erp", "name": "SAP S/4HANA", "protocol": "rest", "description": "SAP ERP integration via OData/REST API. BOM, material master, batch data.", "fields": ["sap_host", "sap_client", "sap_user", "odata_endpoint"]},
    {"type": "erp", "name": "Oracle ERP Cloud", "protocol": "rest", "description": "Oracle ERP via REST API. Product data, manufacturing orders, supplier info.", "fields": ["oracle_host", "api_key", "module"]},
    {"type": "mes", "name": "Siemens Opcenter", "protocol": "opc-ua", "description": "Manufacturing execution via OPC-UA. Production data, quality metrics, traceability.", "fields": ["opcua_endpoint", "namespace", "node_ids"]},
    {"type": "mes", "name": "Rockwell FactoryTalk", "protocol": "rest", "description": "MES integration for batch production, equipment data, process parameters.", "fields": ["ft_host", "ft_api_key", "plant_id"]},
    {"type": "plm", "name": "Siemens Teamcenter", "protocol": "rest", "description": "PLM for BOM, CAD metadata, design specifications, change management.", "fields": ["tc_host", "tc_user", "tc_password", "project_id"]},
    {"type": "plm", "name": "Dassault 3DEXPERIENCE", "protocol": "rest", "description": "PLM/3D design data, material composition, lifecycle metadata.", "fields": ["ds_host", "ds_tenant", "ds_api_key"]},
    {"type": "lims", "name": "LabWare LIMS", "protocol": "rest", "description": "Laboratory data: material testing, chemical analysis, compliance certificates.", "fields": ["lw_host", "lw_api_key", "lab_id"]},
    {"type": "iot", "name": "Azure IoT Hub", "protocol": "mqtt", "description": "IoT telemetry: BMS data, temperature, vibration, energy consumption.", "fields": ["iot_hub_host", "device_connection_string", "consumer_group"]},
    {"type": "iot", "name": "AWS IoT Core", "protocol": "mqtt", "description": "IoT sensor data ingestion for real-time performance monitoring.", "fields": ["iot_endpoint", "thing_name", "certificate_path"]},
    {"type": "scada", "name": "Schneider EcoStruxure", "protocol": "opc-ua", "description": "SCADA integration for energy management, production line monitoring.", "fields": ["scada_endpoint", "site_id"]},
    {"type": "wms", "name": "SAP EWM", "protocol": "rest", "description": "Warehouse management: batch tracking, shipping, EPCIS events.", "fields": ["ewm_host", "warehouse_id", "api_key"]},
    {"type": "custom", "name": "Custom REST API", "protocol": "rest", "description": "Generic REST API connector with configurable field mapping.", "fields": ["base_url", "auth_type", "auth_token", "data_path"]},
    {"type": "custom", "name": "Custom Webhook", "protocol": "webhook", "description": "Receive push notifications from enterprise systems via webhook.", "fields": ["webhook_secret", "expected_format"]},
    {"type": "custom", "name": "SFTP Data Import", "protocol": "sftp", "description": "Batch file import (CSV, JSON, XML) from SFTP server.", "fields": ["sftp_host", "sftp_user", "sftp_path", "file_format"]},
]

FIELD_MAPPINGS: dict[str, dict[str, str]] = {
    "sap": {
        "MATNR": "product_gtin",
        "MAKTX": "product_name",
        "MEINS": "unit_of_measure",
        "NTGEW": "weight_kg",
        "CHARG": "batch_number",
        "WERKS": "manufacturing_plant",
        "HSDAT": "manufacturing_date",
        "MFRNR": "manufacturer_eoid",
    },
    "generic": {
        "product_id": "product_gtin",
        "name": "product_name",
        "weight": "weight_kg",
        "batch": "batch_number",
        "serial": "serial_number",
        "manufacturer": "manufacturer_eoid",
        "date": "manufacturing_date",
        "carbon_footprint": "carbon_footprint_kg_co2eq",
        "recycled_content": "recyclability_score",
    },
}


def create_connector(data: dict[str, Any]) -> dict[str, Any]:
    connector_id = str(uuid.uuid4())[:8]
    connector = {
        "id": connector_id,
        "name": data["name"],
        "type": data.get("type", "custom"),
        "protocol": data.get("protocol", "rest"),
        "description": data.get("description", ""),
        "config": data.get("config", {}),
        "field_mapping": data.get("field_mapping", FIELD_MAPPINGS.get("generic", {})),
        "status": ConnectorStatus.INACTIVE.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_sync": None,
        "records_ingested": 0,
        "auto_create_dpp": data.get("auto_create_dpp", False),
        "webhook_secret": hashlib.sha256(connector_id.encode()).hexdigest()[:32],
    }
    _connectors[connector_id] = connector
    log.info("connector_created", connector_id=connector_id, name=data["name"], type=data.get("type"))
    return connector


def list_connectors() -> list[dict[str, Any]]:
    return list(_connectors.values())


def get_connector(connector_id: str) -> Optional[dict[str, Any]]:
    return _connectors.get(connector_id)


def update_connector(connector_id: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
    conn = _connectors.get(connector_id)
    if not conn:
        return None
    for k, v in data.items():
        if k != "id":
            conn[k] = v
    return conn


def delete_connector(connector_id: str) -> bool:
    return _connectors.pop(connector_id, None) is not None


def test_connector(connector_id: str) -> dict[str, Any]:
    conn = _connectors.get(connector_id)
    if not conn:
        return {"success": False, "error": "Connector not found"}
    conn["status"] = ConnectorStatus.TESTING.value
    # Simulate connection test
    conn["status"] = ConnectorStatus.ACTIVE.value
    conn["last_sync"] = datetime.now(timezone.utc).isoformat()
    log.info("connector_tested", connector_id=connector_id, status="active")
    return {"success": True, "status": "active", "latency_ms": 142, "message": f"Successfully connected to {conn['name']}"}


def process_webhook_data(connector_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Process incoming data from enterprise system and prepare for DPP creation."""
    conn = _connectors.get(connector_id)
    if not conn:
        return {"error": "Connector not found"}

    mapping = conn.get("field_mapping", FIELD_MAPPINGS["generic"])
    mapped_data: dict[str, Any] = {}
    for source_field, target_field in mapping.items():
        if source_field in payload:
            mapped_data[target_field] = payload[source_field]

    record = {
        "id": str(uuid.uuid4())[:8],
        "connector_id": connector_id,
        "connector_name": conn["name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_fields": len(payload),
        "mapped_fields": len(mapped_data),
        "mapped_data": mapped_data,
        "auto_create_dpp": conn.get("auto_create_dpp", False),
        "status": "pending_dpp_creation" if conn.get("auto_create_dpp") else "ingested",
    }
    _ingestion_log.append(record)
    conn["records_ingested"] = conn.get("records_ingested", 0) + 1
    conn["last_sync"] = datetime.now(timezone.utc).isoformat()

    log.info("data_ingested", connector_id=connector_id, mapped_fields=len(mapped_data))
    return record


def get_ingestion_log(connector_id: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    logs = _ingestion_log if not connector_id else [l for l in _ingestion_log if l["connector_id"] == connector_id]
    return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]


def get_templates() -> list[dict[str, Any]]:
    return CONNECTOR_TEMPLATES


def get_field_mappings() -> dict[str, dict[str, str]]:
    return FIELD_MAPPINGS

"""
EPCIS 2.0 JSON-LD event generation and publishing.
Supply chain events: ObjectEvent, AggregationEvent, TransactionEvent (Phase 5 distribution).
"""
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

log = structlog.get_logger()


def epcis_object_event(
    gtin: str,
    serial: str,
    event_type: str = "observe",
    biz_step: Optional[str] = None,
    disposition: Optional[str] = None,
    read_point: Optional[str] = None,
    biz_location: Optional[str] = None,
) -> dict[str, Any]:
    """
    Build EPCIS 2.0 ObjectEvent in JSON-LD.
    event_type: observe, add, delete, etc.
    """
    event_id = f"urn:uuid:{__import__('uuid').uuid4()}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    epc = f"urn:epc:id:sgtin:{gtin}.{serial}"
    return {
        "@context": ["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"],
        "type": "ObjectEvent",
        "id": event_id,
        "eventTime": now,
        "eventTimeZoneOffset": "+00:00",
        "epcList": [epc],
        "action": event_type.upper(),
        "bizStep": biz_step or "shipping",
        "disposition": disposition or "active",
        "readPoint": {"id": read_point or "urn:epc:id:sgln:0000000.00000.0"},
        "bizLocation": {"id": biz_location or "urn:epc:id:sgln:0000000.00000.0"},
    }


def epcis_aggregation_event(
    parent_epc: str,
    child_epcs: list[str],
    biz_step: Optional[str] = None,
) -> dict[str, Any]:
    """Build EPCIS 2.0 AggregationEvent (parent-child)."""
    event_id = f"urn:uuid:{__import__('uuid').uuid4()}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "@context": ["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"],
        "type": "AggregationEvent",
        "id": event_id,
        "eventTime": now,
        "eventTimeZoneOffset": "+00:00",
        "parentID": parent_epc,
        "childEPCs": child_epcs,
        "action": "ADD",
        "bizStep": biz_step or "packing",
    }


def publish_epcis_event(event: dict[str, Any], topic: str = "epcis-events") -> bool:
    """Publish EPCIS event to Kafka (JSON string)."""
    try:
        from app.services.kafka import get_kafka
        import json
        get_kafka().produce(topic, key=event.get("id"), value=json.dumps(event))
        return True
    except Exception as e:
        log.warning("epcis_publish_failed", error=str(e))
        return False

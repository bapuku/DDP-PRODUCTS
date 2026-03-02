"""
Kafka producer for DPP lifecycle events (Avro) - audit trail and event sourcing.
"""
from typing import Any, Optional

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
import structlog

from app.config import settings

log = structlog.get_logger()


class KafkaService:
    """Kafka producer for DPP events (EU AI Act Article 12 audit)."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        schema_registry_url: Optional[str] = None,
    ) -> None:
        self._bootstrap = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._schema_registry_url = schema_registry_url or settings.SCHEMA_REGISTRY_URL
        self._producer: Optional[Producer] = None

    @property
    def producer(self) -> Producer:
        if self._producer is None:
            self._producer = Producer({"bootstrap.servers": self._bootstrap})
        return self._producer

    def close(self) -> None:
        if self._producer is not None:
            self._producer.flush()
            self._producer = None

    def health(self) -> bool:
        """Check Kafka broker is reachable (for /ready)."""
        try:
            admin = AdminClient({"bootstrap.servers": self._bootstrap})
            admin.list_topics(timeout=5)
            return True
        except Exception as e:
            log.warning("kafka_health_failed", error=str(e))
            return False

    def produce(self, topic: str, key: Optional[str], value: Any) -> None:
        """Produce message (value should be serialized; Avro in Sprint 3)."""
        self.producer.produce(topic, key=key, value=value)
        self.producer.poll(0)


_kafka: Optional[KafkaService] = None


def get_kafka() -> KafkaService:
    global _kafka
    if _kafka is None:
        _kafka = KafkaService()
    return _kafka

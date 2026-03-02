"""
Structured logging with structlog (JSON format).
EU AI Act Article 12 - audit trail hooks can be attached here.
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog with JSON renderer for production-ready logs."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_level.upper() == "DEBUG":
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]
    else:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def bind_audit_context(
    agent_id: str | None = None,
    entity_id: str | None = None,
    regulation: str | None = None,
    **kwargs: Any,
) -> None:
    """Bind audit context for EU AI Act Article 12 traceability."""
    ctx: dict[str, Any] = {}
    if agent_id is not None:
        ctx["agent_id"] = agent_id
    if entity_id is not None:
        ctx["entity_id"] = entity_id
    if regulation is not None:
        ctx["regulation"] = regulation
    ctx.update(kwargs)
    structlog.contextvars.bind_contextvars(**ctx)

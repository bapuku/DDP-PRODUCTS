"""
EU DPP Platform - FastAPI application entry point.
Health and readiness endpoints, CORS, structured logging.
EU AI Act 2024/1689 - transparency and audit-ready.
"""
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.middleware import RequestLoggingMiddleware, add_exception_handlers
from app.api.v1 import router as api_v1_router


def get_app() -> FastAPI:
    """Build FastAPI application with lifespan and middleware."""
    configure_logging(settings.LOG_LEVEL)
    log = structlog.get_logger()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info("application_startup", environment=settings.ENVIRONMENT)
        yield
        log.info("application_shutdown")

    app = FastAPI(
        title="EU Digital Product Passport Platform",
        description=(
            "Agentic AI platform for DPP compliance. "
            "EU AI Act 2024/1689 Art. 12 (audit), Art. 13 (transparency), Art. 14 (human oversight) compliant. "
            "AI decisions are logged; human review required when confidence < 85%."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_exception_handlers(app)
    app.include_router(api_v1_router, prefix="/api/v1", tags=["api-v1"])

    @app.get("/health")
    async def health() -> dict[str, Any]:
        """Liveness probe - always 200 if process is up."""
        return {"status": "ok", "service": "dpp-api"}

    @app.get("/ready")
    async def ready() -> dict[str, Any]:
        """Readiness probe - dependencies checked."""
        from app.services.neo4j import get_neo4j
        from app.services.qdrant import get_qdrant
        from app.services.kafka import get_kafka
        from app.services.postgres import get_postgres

        checks: dict[str, str] = {}
        try:
            neo4j_ok = await get_neo4j().verify_connectivity()
            checks["neo4j"] = "ok" if neo4j_ok else "error"
        except Exception as e:
            checks["neo4j"] = f"error: {e!s}"
        try:
            checks["qdrant"] = "ok" if get_qdrant().health() else "error"
        except Exception as e:
            checks["qdrant"] = f"error: {e!s}"
        try:
            checks["kafka"] = "ok" if get_kafka().health() else "error"
        except Exception as e:
            checks["kafka"] = f"error: {e!s}"
        try:
            postgres_ok = await get_postgres().health()
            checks["postgres"] = "ok" if postgres_ok else "error"
        except Exception as e:
            checks["postgres"] = f"error: {e!s}"

        all_ok = all(v == "ok" for v in checks.values())
        return {"status": "ready" if all_ok else "degraded", "checks": checks}

    return app


app = get_app()

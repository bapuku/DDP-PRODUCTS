"""
Middleware: GDPR-compliant request logging, error handlers, request ID injection.
EU AI Act Art. 13 - transparency: AI usage disclosed in response headers.
"""
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    DPPException, ValidationError, NotFoundError, ConflictError, UnauthorizedError, ComplianceError
)
from app.core.i18n import get_locale_from_request, t

log = structlog.get_logger()

# Fields that must never appear in logs (GDPR)
_GDPR_SENSITIVE = frozenset({"password", "token", "secret", "api_key", "authorization", "cookie"})


def _redact_headers(headers: dict) -> dict:
    return {k: "[REDACTED]" if k.lower() in _GDPR_SENSITIVE else v for k, v in headers.items()}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with request_id (no PII), EU AI Act Art. 13 AI-disclosure header."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start = time.monotonic()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        log.info(
            "request_start",
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        elapsed = (time.monotonic() - start) * 1000

        response.headers["X-Request-Id"] = request_id
        response.headers["X-AI-System"] = "EU-DPP-Agentic-Platform"
        response.headers["X-EU-AI-Act-Compliance"] = "Art.12,13,14"

        log.info(
            "request_end",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=round(elapsed, 2),
        )
        structlog.contextvars.clear_contextvars()
        return response


def add_exception_handlers(app) -> None:
    """Register domain exception handlers on the FastAPI app."""

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": exc.code, "message": exc.message, "details": exc.details})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(ComplianceError)
    async def compliance_handler(request: Request, exc: ComplianceError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": exc.code, "message": exc.message, "details": exc.details})

    @app.exception_handler(DPPException)
    async def dpp_exception_handler(request: Request, exc: DPPException) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_exception", error=str(exc), exc_info=True)
        locale = get_locale_from_request(request)
        message = t("errors.internal_error", locale)
        return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "message": message})

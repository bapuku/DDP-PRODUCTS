"""
Domain exceptions - never raise generic Exception.
EU AI Act - regulatory impact assessment in error handling.
"""
from typing import Any, Optional


class DPPException(Exception):
    """Base exception for DPP platform."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code or "DPP_ERROR"
        self.details = details or {}
        super().__init__(message)


class ValidationError(DPPException):
    """Validation error (e.g. GTIN checksum, field constraints)."""
    code = "VALIDATION_ERROR"


class NotFoundError(DPPException):
    """Resource not found (e.g. passport, product)."""
    code = "NOT_FOUND"


class ConflictError(DPPException):
    """Conflict (e.g. duplicate serial number)."""
    code = "CONFLICT"


class UnauthorizedError(DPPException):
    """Unauthorized access."""
    code = "UNAUTHORIZED"


class ComplianceError(DPPException):
    """Compliance or regulatory error."""
    code = "COMPLIANCE_ERROR"

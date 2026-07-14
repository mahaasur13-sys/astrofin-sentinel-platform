"""core.error_schema — standardised JSON error envelope for AstroFin Sentinel.

This module is the single source of truth for the HTTP error contract:

    {
        "code": "AUTH_TOKEN_EXPIRED",
        "message": "JWT token has expired",
        "trace_id": "0af7651916cd43dd8448eb211c80319c",
        "correlation_id": "0c5a7e3a-7c1c-4b7c-b8f1-9e3a6c0e2a11",
        "timestamp": "2026-07-09T07:30:11.482Z",
        "details": {...}            # optional, structured context
    }

It is intentionally framework-agnostic: a `format_error(exc, ctx)` call returns
a dict, and a small Flask/FastAPI helper turns that dict into an HTTP response.

Backwards compatibility:
- Existing `try/except` blocks are unchanged.
- Domain exceptions (`JWTError`, `RefreshError`, …) are *additionally* subclassed
  from `AppException` in this sprint — they keep their original class identity
  (no `__init__` signature changes), so existing `except JWTError` clauses still
  match.
"""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from typing import Any

# Correlation id context — middleware writes here, structlog processor reads.
_correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="unknown")


def set_correlation_id(value: str | None = None) -> str:
    """Set the current request's correlation id. If `value` is None, a uuid4 is generated."""
    cid = value or uuid.uuid4().hex
    _correlation_id_var.set(cid)
    return cid


def get_correlation_id() -> str:
    return _correlation_id_var.get()


class AppException(Exception):
    """Base for all application-level errors that should surface as JSON to clients.

    Subclasses set:
      - `code`   — short stable machine-readable identifier (e.g. "AUTH_INVALID").
      - `status` — default HTTP status code (overridable by handler).
      - `message`— human-readable default message.
    """

    code: str = "INTERNAL_ERROR"
    status: int = 500
    message: str = "Internal server error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)


class BadRequest(AppException):
    code = "BAD_REQUEST"
    status = 400
    message = "Bad request"


class Unauthorized(AppException):
    code = "UNAUTHORIZED"
    status = 401
    message = "Unauthorized"


class Forbidden(AppException):
    code = "FORBIDDEN"
    status = 403
    message = "Forbidden"


class NotFound(AppException):
    code = "NOT_FOUND"
    status = 404
    message = "Resource not found"


class Conflict(AppException):
    code = "CONFLICT"
    status = 409
    message = "Conflict"


class ValidationFailed(AppException):
    code = "VALIDATION_FAILED"
    status = 422
    message = "Validation failed"


class InternalError(AppException):
    code = "INTERNAL_ERROR"
    status = 500
    message = "Internal server error"


def format_error(
    exc: BaseException,
    *,
    trace_id: str | None = None,
    correlation_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Render an exception into the standard JSON envelope.

    Unknown (non-AppException) exceptions are mapped to 500 INTERNAL_ERROR
    with a generic message; the original type is recorded in structured
    logs only and is NOT included in the client envelope, so no internal
    text is leaked to the client.
    """
    if isinstance(exc, AppException):
        code = exc.code
        status = exc.status
        message = exc.message
        merged_details = dict(exc.details)
    else:
        code = InternalError.code
        status = InternalError.status
        message = InternalError.message
        # Intentionally do not expose type(exc).__name__ to the client.
        merged_details = {}

    if details:
        merged_details.update(details)

    _now = time.time()
    timestamp = (
        time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime(_now))
        + f"{int((_now % 1) * 1000):03d}Z"
    )  # ISO-8601 UTC with ms, RFC 3339

    return {
        "code": code,
        "message": message,
        "trace_id": trace_id or "unknown",
        "correlation_id": correlation_id or get_correlation_id(),
        "timestamp": timestamp,
        "status": status,
        "details": merged_details,
    }


def error_response(
    exc: BaseException,
    *,
    trace_id: str | None = None,
    correlation_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    """Return (envelope, status) — convenient tuple for Flask/FastAPI handlers."""
    envelope = format_error(
        exc,
        trace_id=trace_id,
        correlation_id=correlation_id,
        details=details,
    )
    return envelope, envelope["status"]


__all__ = [
    "AppException",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "ValidationFailed",
    "InternalError",
    "format_error",
    "error_response",
    "set_correlation_id",
    "get_correlation_id",
]

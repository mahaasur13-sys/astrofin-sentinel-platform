"""core.correlation — middleware that binds correlation_id per HTTP request.

Reads ``X-Request-ID`` (or ``X-Correlation-ID``) from the request headers,
or generates a new uuid4 if neither is present. Binds it to the
``core.error_schema`` ContextVar so that every structured log line and
every error envelope in the request scope carry the same id.

Exposes two functions:
    - install(app) — registers a FastAPI middleware on the given app.
    - install_flask(app) — registers a Flask before/after_request pair.

Source of truth for the ContextVar is ``core.error_schema``; this module
only wires HTTP plumbing.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from core.error_schema import set_correlation_id

if TYPE_CHECKING:
    from fastapi import FastAPI
    from flask import Flask

logger = logging.getLogger(__name__)

HEADER_NAMES = ("x-request-id", "x-correlation-id")


def _extract_id(headers) -> str:
    """Read correlation id from headers (case-insensitive). Accepts dicts or Starlette Headers."""
    try:
        # FastAPI/Starlette: Headers object supports case-insensitive get()
        for name in HEADER_NAMES:
            v = headers.get(name)
            if v:
                return v.strip()[:128]  # cap length
    except Exception:
        pass
    return uuid.uuid4().hex


def install(app: "FastAPI") -> None:
    """Register a FastAPI middleware that binds correlation_id per request."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class CorrelationIdMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            cid = _extract_id(request.headers)
            set_correlation_id(cid)
            response = await call_next(request)
            response.headers["X-Request-ID"] = cid
            return response

    app.add_middleware(CorrelationIdMiddleware)
    logger.info("correlation_id middleware installed on FastAPI app")


def install_flask(app: "Flask") -> None:
    """Register Flask before/after_request hooks for correlation_id."""
    from flask import g, request

    @app.before_request
    def _bind_correlation_id():  # type: ignore[no-redef]
        cid = _extract_id(request.headers)
        set_correlation_id(cid)
        g.correlation_id = cid

    @app.after_request
    def _emit_correlation_id(response):  # type: ignore[no-redef]
        cid = getattr(g, "correlation_id", None)
        if cid:
            response.headers["X-Request-ID"] = cid
        return response

    logger.info("correlation_id hooks installed on Flask app")

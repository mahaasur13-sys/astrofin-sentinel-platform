"""API Key authentication for FastAPI and Flask routes."""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import secrets
from functools import wraps

from fastapi import HTTPException, Request
from flask import request as flask_request

from core.error_schema import Forbidden, Unauthorized, format_error

logger = logging.getLogger(__name__)

REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
API_KEY = os.getenv("API_KEY", "")


def _ensure_key_configured() -> None:
    """Raise RuntimeError if auth is required but API_KEY is missing."""
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        raise RuntimeError("REQUIRE_AUTH is true but API_KEY is empty or unset")


def _resolve_request(args, kwargs):
    """Return a (request, path) tuple from FastAPI or Flask context."""
    request: Request | None = kwargs.get("request")
    if request is not None:
        return request, request.url.path
    for a in args:
        if isinstance(a, Request):
            return a, a.url.path
    # Flask path: flask.request is a thread-local proxy.
    if flask_request:
        return flask_request, flask_request.path
    return None, None


def _check_key(request, path):
    """Return None if authorized, or a (body, status) tuple error response."""
    if not API_KEY or API_KEY.strip() == "":
        logger.critical("Server misconfiguration: API key required but not set")
        return (
            format_error(
                {"code": "ServerMisconfiguration", "message": "API key not configured"}
            ),
            500,
        )

    key = request.headers.get("X-API-Key") if hasattr(request, "headers") else None
    if not key:
        logger.warning("auth.failed endpoint=%s missing key", path)
        return format_error(Unauthorized("Missing API key")), 401
    if not secrets.compare_digest(key, API_KEY):
        logger.warning("auth.failed endpoint=%s wrong key", path)
        return format_error(Forbidden("Invalid API key")), 403
    logger.debug("auth.success endpoint=%s", path)
    return None


def require_api_key(func):
    """Decorator that works on both FastAPI (async) and Flask (sync) routes.

    On a 401/403 it returns a ``(body, status)`` tuple, which both FastAPI and
    Flask interpret as ``(response_body, status_code)``.
    """
    is_coro = inspect.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if not REQUIRE_AUTH:
            return await func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return format_error({"code": "Unauthorized", "message": "Missing request"}), 401
        err = _check_key(request, path)
        if err is not None:
            return err
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if not REQUIRE_AUTH:
            return func(*args, **kwargs)
        request, path = _resolve_request(args, kwargs)
        if request is None:
            return format_error({"code": "Unauthorized", "message": "Missing request"}), 401
        err = _check_key(request, path)
        if err is not None:
            return err
        return func(*args, **kwargs)

    return async_wrapper if is_coro else sync_wrapper


def verify_api_key(key: str) -> bool:
    """Standalone verification helper."""
    _ensure_key_configured()
    if not key:
        return False
    return secrets.compare_digest(key, API_KEY)

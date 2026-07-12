"""API Key authentication."""

from __future__ import annotations

import logging
import os
import secrets
from functools import wraps

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
API_KEY = os.getenv("API_KEY", "")


def validate_startup():
    """Raise RuntimeError if auth is required but API_KEY is missing."""
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        raise RuntimeError("REQUIRE_AUTH is true but API_KEY is empty or unset")


def require_api_key(func):
    """Decorator for Flask: checks X-API-Key header."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request

        if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
            logger.critical("Server misconfiguration: API key required but not set")
            return ({"error": "Server misconfiguration"}, 500)

        if not REQUIRE_AUTH:
            return func(*args, **kwargs)

        key = request.headers.get("X-API-Key")
        if not key:
            logger.warning("auth.failed endpoint=%s remote=%s missing key", request.path, request.remote_addr)
            return ({"error": "Unauthorized"}, 401)
        if not secrets.compare_digest(key, API_KEY):
            logger.warning("auth.failed endpoint=%s remote=%s wrong key", request.path, request.remote_addr)
            return ({"error": "Forbidden"}, 403)
        logger.debug("auth.success endpoint=%s", request.path)
        return func(*args, **kwargs)

    return wrapper


async def fastapi_require_api_key(request: Request):
    """FastAPI dependency: checks X-API-Key."""
    if REQUIRE_AUTH and (not API_KEY or API_KEY.strip() == ""):
        logger.critical("Server misconfiguration: API key required but not set")
        raise HTTPException(status_code=500, detail="Server misconfiguration")
    if not REQUIRE_AUTH:
        return
    key = request.headers.get("X-API-Key")
    if not key or not secrets.compare_digest(key, API_KEY):
        logger.warning("auth.failed endpoint=%s remote=%s", request.url.path, request.client.host)
        raise HTTPException(status_code=401, detail="Invalid API key")
    logger.debug("auth.success endpoint=%s", request.url.path)

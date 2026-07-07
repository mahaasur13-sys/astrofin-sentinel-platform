"""Rate limiting configuration with optional Redis backend."""

from __future__ import annotations

import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

REDIS_URL = os.environ.get("REDIS_URL")

# Use Redis if available; otherwise fall back to in-memory storage
if REDIS_URL:
    storage_uri = REDIS_URL
else:
    storage_uri = "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri=storage_uri,
    headers_enabled=True,
)


def is_redis_backed() -> bool:
    """Return True if rate limiter is using Redis."""
    return REDIS_URL is not None

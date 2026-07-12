"""Rate limiting configuration with optional Redis backend.

Reads the Redis URL from the central :class:`core.settings.Settings`
instead of touching ``os.environ`` directly. The module keeps its public
symbol ``limiter`` (Flask-Limiter) and ``is_redis_backed()`` so existing
callers (web.app, web.wsgi) keep working without changes.
"""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from core.settings import get_settings

# Resolved at import time for backwards compatibility with tests that
# monkey-patch ``core.rate_limit.REDIS_URL`` directly.
REDIS_URL = get_settings().REDIS_URL or None

# Use Redis if available; otherwise fall back to in-memory storage.
storage_uri = REDIS_URL or "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri=storage_uri,
    headers_enabled=True,
)


def is_redis_backed() -> bool:
    """Return True if rate limiter is using Redis."""
    return REDIS_URL is not None

"""Rate limiter using slowapi + Redis."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

def configure_limits(app) -> None:
    app.state.limiter = limiter
    from slowapi import _rate_limit_exceeded_handler as handler
    from slowapi.errors import RateLimitExceeded

    app.add_exception_handler(RateLimitExceeded, handler)

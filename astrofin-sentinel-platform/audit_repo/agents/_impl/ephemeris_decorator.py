"""
require_ephemeris decorator and ephemeris utilities.
"""

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

# Swiss Ephemeris availability check
try:
    import swisseph as swe

    HAS_SWISS_EPHEMERIS = True
except ImportError:
    HAS_SWISS_EPHEMERIS = False
    swe = None


def require_ephemeris(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator that blocks agent execution if Swiss Ephemeris is unavailable.

    Usage:
        @require_ephemeris
        async def analyze(self, state: dict) -> AgentResponse:
            ...

    Raises:
        EphemerisUnavailableError: If Swiss Ephemeris is not installed.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not HAS_SWISS_EPHEMERIS:
            raise EphemerisUnavailableError(
                f"Agent '{args[0].__class__.__name__}' requires Swiss Ephemeris. Install with: pip install pyswisseph"
            )
        return await func(*args, **kwargs)

    return wrapper


class EphemerisUnavailableError(Exception):
    """Raised when agent requires Swiss Ephemeris but it's not available."""

    pass


__all__ = ["require_ephemeris", "EphemerisUnavailableError", "HAS_SWISS_EPHEMERIS"]

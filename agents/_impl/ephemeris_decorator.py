"""
require_ephemeris decorator and ephemeris utilities.
"""

import functools
import asyncio
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
    async def _async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not HAS_SWISS_EPHEMERIS:
            raise EphemerisUnavailableError(
                f"Agent '{args[0].__class__.__name__}' requires Swiss Ephemeris. Install with: pip install pyswisseph"
            )
        return await func(*args, **kwargs)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if not HAS_SWISS_EPHEMERIS:
            owner = (
                args[0].__class__.__name__
                if args and hasattr(args[0], "__class__")
                else func.__qualname__
            )
            raise EphemerisUnavailableError(
                f"'{owner}' requires Swiss Ephemeris. Install with: pip install pyswisseph"
            )
        return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return functools.wraps(func)(_async_wrapper)  # type: ignore[return-value]
    return wrapper


class EphemerisUnavailableError(Exception):
    """Raised when agent requires Swiss Ephemeris but it's not available."""

    pass


__all__ = ["require_ephemeris", "EphemerisUnavailableError", "HAS_SWISS_EPHEMERIS"]

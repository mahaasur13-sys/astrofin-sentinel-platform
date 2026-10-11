"""
require_ephemeris decorator and ephemeris utilities.
"""

from __future__ import annotations

import functools
import inspect
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

    Synchronous callables are supported too: the wrapper is selected from the
    decorated callable itself, so a plain function (including a FastAPI route
    function) is never treated as a bound method.

    Raises:
        EphemerisUnavailableError: If Swiss Ephemeris is not installed.
    """

    def _guard(owner: object | None) -> None:
        if not HAS_SWISS_EPHEMERIS:
            target = (
                type(owner).__name__
                if owner is not None
                else getattr(func, "__qualname__", getattr(func, "__name__", repr(func)))
            )
            raise EphemerisUnavailableError(
                f"Agent '{target}' requires Swiss Ephemeris. Install with: pip install pyswisseph"
            )

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            _guard(args[0] if args else None)
            return await func(*args, **kwargs)

        return wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        _guard(args[0] if args else None)
        return func(*args, **kwargs)

    return sync_wrapper


class EphemerisUnavailableError(Exception):
    """Raised when agent requires Swiss Ephemeris but it's not available."""

    pass


__all__ = ["require_ephemeris", "EphemerisUnavailableError", "HAS_SWISS_EPHEMERIS"]

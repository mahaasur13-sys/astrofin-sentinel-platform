"""
data_room/resolvers/base.py
============================
Abstract base class for all resolvers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ResolverError(Exception):
    """Raised when a resolver cannot satisfy the request.

    The Data Room catches this and applies the graceful-degradation
    contract: it tries the next resolver in the chain, marks the
    current one as degraded, and records the error in observability.
    """


class Resolver(ABC, Generic[T]):
    """Base class for every Data Room resolver.

    Subclasses must:
      - expose `name` (used as a metric label)
      - implement `async def resolve(...) -> T`
      - raise `ResolverError` on failure (not bare `Exception`)
      - never silently substitute stale data
    """

    #: unique identifier used for metrics and circuit-breaker lookups
    name: str = "abstract"

    @abstractmethod
    async def resolve(self, *args: Any, **kwargs: Any) -> T:
        """Fetch the requested datum. Raise ResolverError on failure."""


__all__ = ["Resolver", "ResolverError"]

"""Data Room Blueprint — fallback chain for data access."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

logger = logging.getLogger("data_room.blueprint")


@dataclass(frozen=True)
class PriceTick:
    """A point-in-time price observation."""

    symbol: str
    price: float
    asof: str = ""
    source_id: str = "unknown"
    quality_score: float = 1.0
    freshness_sla_seconds: int = 30
    metadata: dict = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@runtime_checkable
class Resolver(Protocol):
    """Anything that has an async resolve() method."""

    id: str
    freshness_sla_seconds: int

    async def resolve(self, symbol: str, asof: str) -> PriceTick: ...


class Blueprint:
    """Fallback chain for data access.

    Resolvers are registered with a name (e.g. "price") and an optional
    chain of fallback IDs. When get_price is called, it walks the chain
    in order; on error it moves to the next.
    """

    def __init__(self) -> None:
        self._named: dict[str, list[Resolver]] = {}
        self._all: list[Resolver] = []

    def register(
        self,
        name: str,
        resolver: Resolver,
        chain: list[str] | None = None,
    ) -> None:
        self._named.setdefault(name, []).append(resolver)
        self._all.append(resolver)
        # tag the resolver with the chain (best-effort) for the runner
        chain = chain or []
        if hasattr(resolver, "_chain"):
            resolver._chain = chain

    def get_resolver_chain(self, name: str) -> list[Resolver]:
        """Return resolvers in fallback order: starting with `name`, then chain."""
        if name not in self._named:
            return []
        primary = self._named[name]
        getattr(primary[0], "id", None) if primary else None
        # The chain attribute is on the FIRST registered resolver under that name.
        chain_ids = list(getattr(primary[0], "_chain", [])) if primary else []
        ordered: list[Resolver] = []
        for r in primary:
            ordered.append(r)
        for cid in chain_ids:
            for r in self._all:
                if getattr(r, "id", None) == cid:
                    ordered.append(r)
                    break
        return ordered

    async def get_price(self, symbol: str, asof: str = "") -> PriceTick | None:
        chain = self.get_resolver_chain("price")
        for resolver in chain:
            try:
                return await resolver.resolve(symbol, asof)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "blueprint: resolver %s failed for %s: %s",
                    getattr(resolver, "id", "?"),
                    symbol,
                    exc,
                )
                continue
        return None


__all__ = ["PriceTick", "Resolver", "Blueprint"]

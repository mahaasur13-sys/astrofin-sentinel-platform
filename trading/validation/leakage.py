"""Bars, strategy decisions and leakage guards."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

from .errors import ChronologyError, LeakageError


@dataclass(frozen=True)
class Bar:
    ts: datetime  # bar close time, timezone-aware
    close: float
    symbol: str = "SYNTH"


@dataclass(frozen=True)
class StrategyDecision:
    """What a strategy decided at ``decision_ts``; ``features`` maps name → (value, feature_ts)."""

    signal: str  # LONG / SHORT / NEUTRAL
    confidence: float = 50.0
    features: Mapping[str, tuple[Any, datetime]] = field(default_factory=dict)


def assert_chronological(bars: Sequence[Bar]) -> None:
    if not bars:
        raise ChronologyError("no bars")
    for b in bars:
        if not isinstance(b.ts, datetime) or b.ts.tzinfo is None:
            raise ChronologyError(f"bar timestamp must be timezone-aware: {b.ts!r}")
    for a, b in zip(bars, bars[1:]):
        if not b.ts > a.ts:
            raise ChronologyError(f"bars not strictly increasing: {a.ts.isoformat()} → {b.ts.isoformat()}")


def assert_no_feature_leakage(decision: StrategyDecision, decision_ts: datetime) -> None:
    for name, item in decision.features.items():
        try:
            _, fts = item
        except (TypeError, ValueError):
            raise LeakageError(f"feature {name!r} has no timestamp; refusing (cannot prove no lookahead)") from None
        if not isinstance(fts, datetime) or fts.tzinfo is None:
            raise LeakageError(f"feature {name!r} timestamp must be timezone-aware")
        if fts > decision_ts:
            raise LeakageError(
                f"feature {name!r} timestamp {fts.isoformat()} > decision {decision_ts.isoformat()} (lookahead)"
            )

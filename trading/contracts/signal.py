"""trading/contracts/signal.py — unified Signal contract (schema v1.0).

One immutable object describes a trading decision produced by research/strategy code
before it reaches risk/execution. Rules:

* Every field is either provided by the caller or the signal is REFUSED
  (``SignalRefused`` with the exact missing / invalid field names). Nothing is invented:
  no default symbol, strategy, timestamps or confidence scale.
* Money, price and quantity are ``Decimal`` at the boundary. ``float`` input is converted
  via ``str()`` (shortest repr), NaN/Inf/bool are refused.
* Timestamps are timezone-aware and normalised to UTC; naive datetimes are refused.

This module is NOT wired into any live/backtest path (PR 2 scope: contract only).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any

SCHEMA_VERSION = "1.0"


class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class Verdict(str, Enum):
    ENTER = "ENTER"  # actionable: open a position on ``side``
    HOLD = "HOLD"  # no action
    AVOID = "AVOID"  # explicit "do not trade"


class SignalRefused(ValueError):
    """Signal cannot be built. ``missing`` / ``invalid`` name the offending fields."""

    def __init__(self, missing: Iterable[str] = (), invalid: Mapping[str, str] | None = None):
        self.missing: tuple[str, ...] = tuple(missing)
        self.invalid: dict[str, str] = dict(invalid or {})
        parts = []
        if self.missing:
            parts.append("missing=" + ",".join(self.missing))
        if self.invalid:
            parts.append("invalid=" + ",".join(f"{k}({v})" for k, v in self.invalid.items()))
        super().__init__("signal refused: " + "; ".join(parts))


# ── Conversion helpers (raise ValueError with a short reason) ────────────────


def to_decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("bool")
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    elif isinstance(value, float):
        d = Decimal(str(value))
    elif isinstance(value, str):
        try:
            d = Decimal(value.strip())
        except InvalidOperation as e:
            raise ValueError("not a number") from e
    else:
        raise ValueError(f"type {type(value).__name__}")
    if not d.is_finite():
        raise ValueError("not finite")
    return d


def to_utc(value: Any) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError("not ISO-8601") from e
    if not isinstance(value, datetime):
        raise ValueError(f"type {type(value).__name__}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("naive datetime (timezone required)")
    return value.astimezone(timezone.utc)


# ── Schema ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Evidence:
    source: str  # who produced it (agent / indicator / dataset)
    kind: str  # e.g. "reasoning", "source", "indicator"
    detail: str = ""
    weight: Decimal | None = None
    observed_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "kind": self.kind,
            "detail": self.detail,
            "weight": None if self.weight is None else str(self.weight),
            "observed_at": None if self.observed_at is None else self.observed_at.isoformat(),
        }


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    verdict: Verdict
    strategy_id: str
    strategy_version: str
    created_at: datetime  # when the signal was produced (UTC)
    as_of: datetime  # market data timestamp the decision is based on (UTC)
    confidence: Decimal  # 0..1
    evidence: tuple[Evidence, ...]
    entry_price: Decimal | None = None
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    quantity: Decimal | None = None
    schema_version: str = field(default=SCHEMA_VERSION)

    @property
    def is_actionable(self) -> bool:
        return self.verdict is Verdict.ENTER

    @property
    def signal_id(self) -> str:
        """Deterministic id over identity fields (same decision → same id)."""
        ident = {
            "schema_version": self.schema_version,
            "symbol": self.symbol,
            "side": self.side.value,
            "verdict": self.verdict.value,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "as_of": self.as_of.isoformat(),
        }
        raw = json.dumps(ident, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> dict:
        def _d(v: Decimal | None) -> str | None:
            return None if v is None else str(v)

        return {
            "schema_version": self.schema_version,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "verdict": self.verdict.value,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "created_at": self.created_at.isoformat(),
            "as_of": self.as_of.isoformat(),
            "confidence": str(self.confidence),
            "evidence": [e.to_dict() for e in self.evidence],
            "entry_price": _d(self.entry_price),
            "stop_price": _d(self.stop_price),
            "target_price": _d(self.target_price),
            "quantity": _d(self.quantity),
        }


_REQUIRED = ("symbol", "side", "verdict", "strategy_id", "strategy_version", "created_at", "as_of", "confidence", "evidence")
_PRICES = ("entry_price", "stop_price", "target_price", "quantity")


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def build_signal(**fields: Any) -> Signal:
    """Validate raw fields and build a ``Signal`` or raise ``SignalRefused``."""
    unknown = set(fields) - set(_REQUIRED) - set(_PRICES)
    missing = [k for k in _REQUIRED if fields.get(k) is None]
    invalid: dict[str, str] = {f: "unknown field" for f in sorted(unknown)}
    out: dict[str, Any] = {}

    for k in ("symbol", "strategy_id", "strategy_version"):
        v = fields.get(k)
        if v is not None:
            if _nonempty_str(v):
                out[k] = v.strip()
            else:
                invalid[k] = "empty or not a string"

    for k, enum in (("side", Side), ("verdict", Verdict)):
        v = fields.get(k)
        if v is not None:
            try:
                out[k] = v if isinstance(v, enum) else enum(str(v).upper())
            except ValueError:
                invalid[k] = f"one of {[e.value for e in enum]}"

    for k in ("created_at", "as_of"):
        v = fields.get(k)
        if v is not None:
            try:
                out[k] = to_utc(v)
            except ValueError as e:
                invalid[k] = str(e)

    v = fields.get("confidence")
    if v is not None:
        try:
            c = to_decimal(v)
            if not (Decimal(0) <= c <= Decimal(1)):
                invalid["confidence"] = "must be within [0, 1]"
            else:
                out["confidence"] = c
        except ValueError as e:
            invalid["confidence"] = str(e)

    ev = fields.get("evidence")
    if ev is not None:
        items = list(ev) if isinstance(ev, (list, tuple)) else None
        if items is None or not items:
            invalid["evidence"] = "non-empty list required"
        elif not all(isinstance(e, Evidence) and _nonempty_str(e.source) and _nonempty_str(e.kind) for e in items):
            invalid["evidence"] = "items must be Evidence with source and kind"
        else:
            out["evidence"] = tuple(items)

    for k in _PRICES:
        v = fields.get(k)
        if v is not None:
            try:
                d = to_decimal(v)
                if d <= 0:
                    invalid[k] = "must be > 0"
                else:
                    out[k] = d
            except ValueError as e:
                invalid[k] = str(e)

    # Cross-field invariants (only when the involved fields are valid).
    if "created_at" in out and "as_of" in out and out["as_of"] > out["created_at"]:
        invalid["as_of"] = "after created_at (look-ahead)"
    side, verdict = out.get("side"), out.get("verdict")
    if side is not None and verdict is not None:
        if verdict is Verdict.ENTER and side is Side.FLAT:
            invalid["side"] = "ENTER requires LONG or SHORT"
        if verdict is not Verdict.ENTER and side is not Side.FLAT:
            invalid["side"] = f"{verdict.value} requires FLAT"
    entry, stop, target = out.get("entry_price"), out.get("stop_price"), out.get("target_price")
    if side in (Side.LONG, Side.SHORT) and entry is not None:
        sign = 1 if side is Side.LONG else -1
        if stop is not None and sign * (entry - stop) <= 0:
            invalid["stop_price"] = f"must be {'below' if sign > 0 else 'above'} entry_price for {side.value}"
        if target is not None and sign * (target - entry) <= 0:
            invalid["target_price"] = f"must be {'above' if sign > 0 else 'below'} entry_price for {side.value}"

    if missing or invalid:
        raise SignalRefused(missing, invalid)
    return Signal(**out)

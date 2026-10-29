"""trading/contracts/adapter.py — legacy signal dicts → ``Signal``.

Supported inputs (existing shapes in the repo):
* ``AgentResponse.to_dict()`` (core/base_agent.py): signal LONG/SHORT/NEUTRAL/AVOID,
  confidence int 0..100, reasoning, sources, metadata, timestamp (UTC ISO), agent_name.
* ``TradingSignal`` dict (agents/_impl/types.py): signal STRONG_BUY..STRONG_SELL/HOLD,
  confidence, symbol, timestamp (NAIVE ``datetime.now()`` → refused), metadata.
* ``SafetyGate``-style dicts ``{"signal", "confidence", "agent_name"}``.

Nothing is guessed: strategy id/version, symbol, ``as_of`` and the confidence scale must be
present in the dict or passed explicitly, otherwise ``SignalRefused`` lists them.

``hypothesis_status`` (and ``hypothesis_check``) must be passed explicitly by the caller as
keyword arguments; they are never read from the legacy dict and never inferred from
``confidence`` or the direction. Missing → ``SignalRefused(missing=["hypothesis_status"])``.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Literal

from .signal import Evidence, Side, Signal, SignalRefused, Verdict, build_signal, to_decimal

_DIRECTION_MAP: dict[str, tuple[Side, Verdict]] = {
    "LONG": (Side.LONG, Verdict.ENTER),
    "BUY": (Side.LONG, Verdict.ENTER),
    "STRONG_BUY": (Side.LONG, Verdict.ENTER),
    "SHORT": (Side.SHORT, Verdict.ENTER),
    "SELL": (Side.SHORT, Verdict.ENTER),
    "STRONG_SELL": (Side.SHORT, Verdict.ENTER),
    "NEUTRAL": (Side.FLAT, Verdict.HOLD),
    "HOLD": (Side.FLAT, Verdict.HOLD),
    "AVOID": (Side.FLAT, Verdict.AVOID),
}


def _pick(d: Mapping[str, Any], meta: Mapping[str, Any], key: str, override: Any) -> Any:
    if override is not None:
        return override
    if d.get(key) is not None:
        return d[key]
    return meta.get(key)


def from_signal_dict(
    d: Mapping[str, Any],
    *,
    confidence_scale: Literal["percent", "fraction"],
    symbol: str | None = None,
    strategy_id: str | None = None,
    strategy_version: str | None = None,
    as_of: Any = None,
    created_at: Any = None,
    hypothesis_status: Any = None,
    hypothesis_check: str | None = None,
) -> Signal:
    """Convert a legacy dict. ``confidence_scale`` is mandatory (0..100 vs 0..1)."""
    if not isinstance(d, Mapping):
        raise SignalRefused(invalid={"signal_dict": f"type {type(d).__name__}"})
    meta = d.get("metadata") if isinstance(d.get("metadata"), Mapping) else {}
    missing: list[str] = []
    invalid: dict[str, str] = {}
    fields: dict[str, Any] = {}

    raw_dir = d.get("signal")
    if raw_dir is None:
        missing.append("signal")
    else:
        key = getattr(raw_dir, "value", raw_dir)
        mapped = _DIRECTION_MAP.get(str(key).upper())
        if mapped is None:
            invalid["signal"] = f"unknown direction {key!r}"
        else:
            fields["side"], fields["verdict"] = mapped

    raw_conf = d.get("confidence")
    if raw_conf is None:
        missing.append("confidence")
    else:
        try:
            c = to_decimal(raw_conf)
            if confidence_scale == "percent":
                c = c / Decimal(100)
            elif confidence_scale != "fraction":
                raise ValueError(f"unknown confidence_scale {confidence_scale!r}")
            fields["confidence"] = c
        except ValueError as e:
            invalid["confidence"] = str(e)

    fields["symbol"] = _pick(d, meta, "symbol", symbol)
    fields["strategy_id"] = _pick(d, meta, "strategy_id", strategy_id)
    fields["strategy_version"] = _pick(d, meta, "strategy_version", strategy_version)
    fields["as_of"] = _pick(d, meta, "as_of", as_of)
    fields["created_at"] = created_at if created_at is not None else d.get("timestamp")

    # Hypothesis status: explicit caller input only (no inference from confidence/direction).
    if hypothesis_status is None:
        missing.append("hypothesis_status")
    else:
        fields["hypothesis_status"] = hypothesis_status
    fields["hypothesis_check"] = hypothesis_check

    evidence: list[Evidence] = []
    agent = d.get("agent_name")
    reasoning = d.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        if not (isinstance(agent, str) and agent.strip()):
            invalid["agent_name"] = "required to attribute reasoning evidence"
        else:
            evidence.append(Evidence(source=agent, kind="reasoning", detail=reasoning))
    for s in d.get("sources") or ():
        if isinstance(s, str) and s.strip():
            evidence.append(Evidence(source=s, kind="source"))
    fields["evidence"] = evidence or None

    for key, aliases in (
        ("entry_price", ("entry_price",)),
        ("stop_price", ("stop_price", "stop_loss")),
        ("target_price", ("target_price", "take_profit")),
        ("quantity", ("quantity",)),
    ):
        for a in aliases:
            v = d.get(a, meta.get(a))
            if v is not None:
                fields[key] = v
                break

    # Always run full validation so the refusal lists every problem at once.
    try:
        sig = build_signal(**{k: v for k, v in fields.items() if v is not None})
    except SignalRefused as e:
        derived = {"side", "verdict"} if ("signal" in missing or "signal" in invalid) else set()
        for m in e.missing:
            if m not in missing and m not in invalid and m not in derived:
                missing.append(m)
        for k, v in e.invalid.items():
            invalid.setdefault(k, v)
        raise SignalRefused(missing, invalid) from None
    if missing or invalid:
        raise SignalRefused(missing, invalid)
    return sig

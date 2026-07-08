"""
Compromise Agent — explicit trade-off resolver for conflicting agent signals.

Why this exists:
    SynthesisAgent._detect_conflicts() applies a hard-coded ASTRO_REDUCTION /
    FUNDAMENTAL_BOOST whenever Astro and Fundamental+Quant disagree. That is
    one-size-fits-all: a low-volatility clash and a CRISIS-regime clash get
    the same treatment.

    CompromiseAgent makes the trade-off explicit:
      - Pick the top-2 conflicting signals (highest |confidence|).
      - Compute expected utility E[U] = p·gain − (1−p)·loss for each,
        using VolatilityEngine.analyze() for gain/loss.
      - Emit NEUTRAL@mid_confidence with reasoning that lists both
        outcomes AND the conditions under which the decision flips
        (drift triggers for MetaAgent).

Contract (per mas_design.md §3.1):
    - Pattern A: @track_agent_metrics + try/except → _degraded()
    - analyze() is the only place with business logic; do not move it.
    - Integration: SynthesisAgent._vote() consults compromise_signal
      when confidence >= 60; otherwise falls back to its own vote.
"""

from __future__ import annotations

import logging
from typing import Any

from agents._impl.ephemeris_decorator import EphemerisUnavailableError
from agents.metrics import track_agent_metrics
from core.base_agent import (
    EPHEMERIS_UNAVAILABLE,
    UNKNOWN,
    AgentResponse,
    BaseAgent,
    SignalDirection,
)
from core.volatility import VolatilityEngine, VolatilityRegime

logger = logging.getLogger(__name__)


# Confidence thresholds for switching direction in drift conditions.
# If either side's confidence drops below FLIP_BELOW under the listed
# trigger, SynthesisAgent should re-evaluate.
FLIP_BELOW = 55
MIN_CONFIDENCE = 30
MAX_CONFIDENCE = 80  # EC-01 hubris cap, slightly tighter than SynthesisAgent's 92


def _signal_value(direction: SignalDirection | str) -> int:
    """Map signal to signed vote: LONG=+1, SHORT=-1, else 0."""
    name = direction.value if hasattr(direction, "value") else str(direction)
    name = name.upper()
    if name in ("LONG", "BUY", "STRONG_BUY"):
        return 1
    if name in ("SHORT", "SELL", "STRONG_SELL"):
        return -1
    return 0


class CompromiseAgent(BaseAgent[AgentResponse]):
    """
    CompromiseAgent — emits NEUTRAL@mid_confidence when top agents disagree,
    with explicit reasoning for the trade-off and the conditions that would
    flip the call.

    Domain:   synthesis (coordinator-adjacent)
    Weight:   0.0 (not a voter; consumed by SynthesisAgent._vote)
    Inputs:   state["all_signals"] (list[AgentResponse|dict])
              state["current_price"], state["symbol"]
    Signal:   NEUTRAL with mid-confidence + drift triggers, OR a directional
              call when one side dominates by a configured margin.
    """

    def __init__(self) -> None:
        super().__init__(
            name="CompromiseAgent",
            instructions_path="agents/CompromiseAgent_instructions.md",
            domain="synthesis",
            weight=0.0,
        )

    async def analyze(self, state: dict[str, Any]) -> AgentResponse:
        signals = state.get("all_signals", []) or []
        symbol = state.get("symbol", "BTCUSDT")
        current_price = float(state.get("current_price", 50000) or 50000)

        # ── Pull the top-2 conflicting signals (highest |confidence|) ──────
        # Drop degraded/empty entries first.
        valid = []
        for s in signals:
            conf = self._get_signal_attr(s, "confidence", 0) or 0
            sig = self._get_signal_attr(s, "signal", "NEUTRAL")
            if conf <= 0 or _signal_value(sig) == 0:
                continue
            valid.append(
                {
                    "agent": self._get_signal_attr(s, "agent_name", "?"),
                    "signal": sig,
                    "confidence": int(conf),
                    "value": _signal_value(sig),
                }
            )

        if len(valid) < 2:
            return self._neutral_no_conflict(symbol=symbol, current_price=current_price, n_signals=len(signals))

        valid.sort(key=lambda x: x["confidence"], reverse=True)
        top1, top2 = valid[0], valid[1]

        # If they agree → no compromise needed; defer to SynthesisAgent.
        if top1["value"] == top2["value"]:
            return self._neutral_no_conflict(
                symbol=symbol,
                current_price=current_price,
                n_signals=len(signals),
                top=top1,
            )

        # ── Volatility-aware expected utility ───────────────────────────────
        # E[U] = p·gain − (1−p)·loss. VolatilityEngine gives us the
        # stop_distance_pct (≈ loss) and a 2R target distance (≈ gain).
        try:
            vol = VolatilityEngine.from_regime(VolatilityRegime.NORMAL).analyze(symbol=symbol, price=current_price)
        except Exception as e:  # noqa: BLE001 — fallback path
            logger.warning("[COMPROMISE] VolatilityEngine failed, using defaults: %r", e)
            vol = None

        if vol is not None:
            loss_pct = vol.stop_distance_pct
            gain_pct = vol.stop_distance_pct * 2.0  # 2R target
            regime = vol.regime
        else:
            loss_pct = 0.015
            gain_pct = 0.030
            regime = VolatilityRegime.NORMAL

        def expected_utility(entry: dict) -> float:
            p = entry["confidence"] / 100.0
            return p * gain_pct - (1.0 - p) * loss_pct

        eu_long = (
            expected_utility({**_next_long(valid), "confidence": 100}) if any(v["value"] == 1 for v in valid) else -1e9
        )
        eu_short = (
            expected_utility({**_next_short(valid), "confidence": 100})
            if any(v["value"] == -1 for v in valid)
            else -1e9
        )

        # Build explicit reasoning with both outcomes + drift triggers.
        winner = top1 if top1["value"] == (1 if eu_long > eu_short else -1) else top2

        triggers: list[str] = []
        if winner["confidence"] < FLIP_BELOW:
            triggers.append(f"{winner['agent']}_conf<{FLIP_BELOW}")
        if vol is not None and regime == VolatilityRegime.HIGH:
            triggers.append("regime=HIGH_VOL")
        if eu_long >= 0 and eu_short >= 0:
            triggers.append("both_sides_positive_EU")

        # Confidence: midpoint of the two competing signals, capped.
        mid_conf = (top1["confidence"] + top2["confidence"]) // 2
        confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, mid_conf))

        # If the volatility regime is EXTREME, we are forced to NEUTRAL
        # (mirrors SynthesisAgent's V-07 guard).
        if regime == VolatilityRegime.EXTREME:
            direction = SignalDirection.NEUTRAL
            reasoning_prefix = "V-07 [EXTREME VOLATILITY] — compromise forced to NEUTRAL."
        else:
            direction = SignalDirection.NEUTRAL  # compromise = abstain
            reasoning_prefix = "Conflict detected; explicit compromise."

        reasoning = (
            f"{reasoning_prefix} "
            f"Top-1: {top1['agent']}={top1['signal']}@{top1['confidence']}. "
            f"Top-2: {top2['agent']}={top2['signal']}@{top2['confidence']}. "
            f"E[U]long={eu_long:+.4f}, E[U]short={eu_short:+.4f} "
            f"(regime={regime.value if hasattr(regime, 'value') else regime}, "
            f"gain={gain_pct:.4f}, loss={loss_pct:.4f}). "
            f"Flip conditions: {', '.join(triggers) if triggers else 'none'}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=self._collect_sources(signals),
            metadata={
                "symbol": symbol,
                "current_price": current_price,
                "regime": regime.value if hasattr(regime, "value") else str(regime),
                "top1": {
                    "agent": top1["agent"],
                    "signal": str(top1["signal"]),
                    "confidence": top1["confidence"],
                },
                "top2": {
                    "agent": top2["agent"],
                    "signal": str(top2["signal"]),
                    "confidence": top2["confidence"],
                },
                "expected_utility": {
                    "long": round(eu_long, 6),
                    "short": round(eu_short, 6),
                },
                "drift_triggers": triggers,
                "compromise_active": True,
                "reason_code": "MULTI_CATEGORY_CONFLICT",
                "compromise_direction": ("LONG" if eu_long > eu_short else "SHORT"),
                "compromise_preferred_agent": winner["agent"],
            },
        )

    @track_agent_metrics
    async def run(self, state: dict[str, Any]) -> AgentResponse:
        """
        Public entry point. Wraps `analyze` with the latency histogram
        and a defensive try/except so a single agent can never crash
        the orchestrator.
        """
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_signal_attr(self, sig: Any, key: str, default: Any = None) -> Any:
        if hasattr(sig, key):
            return getattr(sig, key)
        if isinstance(sig, dict):
            return sig.get(key, default)
        return default

    def _collect_sources(self, signals: list) -> list:
        out: list = []
        for s in signals:
            for src in self._get_signal_attr(s, "sources", []) or []:
                if isinstance(src, str) and src and src not in out:
                    out.append(src)
        return out

    def _neutral_no_conflict(
        self,
        symbol: str,
        current_price: float,
        n_signals: int,
        top: dict | None = None,
        reason_code: str | None = None,
    ) -> AgentResponse:
        """Fallback when no real conflict exists (defer to SynthesisAgent)."""
        if reason_code is None:
            if n_signals == 0:
                reason_code = "INSUFFICIENT_SIGNALS"
            elif n_signals == 1:
                reason_code = "SINGLE_SIGNAL"
            else:
                reason_code = "CONSENSUS"
        meta: dict[str, Any] = {
            "symbol": symbol,
            "current_price": current_price,
            "compromise_active": False,
            "reason_code": reason_code,
        }
        if top is not None:
            meta["dominant"] = {
                "agent": top["agent"],
                "signal": str(top["signal"]),
                "confidence": top["confidence"],
            }
        return AgentResponse(
            agent_name=self.name,
            signal=SignalDirection.NEUTRAL,
            confidence=MIN_CONFIDENCE,
            reasoning=(f"No resolvable conflict among {n_signals} signal(s); CompromiseAgent abstains."),
            sources=[],
            metadata=meta,
        )


# ── module helpers ───────────────────────────────────────────────────────────


def _next_long(valid: list[dict]) -> dict:
    for v in valid:
        if v["value"] == 1:
            return v
    return {"confidence": 0}


def _next_short(valid: list[dict]) -> dict:
    for v in valid:
        if v["value"] == -1:
            return v
    return {"confidence": 0}


# ─── Convenience runner ──────────────────────────────────────────────────────


async def run_compromise_agent(state: dict[str, Any]) -> dict:
    """Runner used by the orchestrator / registry."""
    agent = CompromiseAgent()
    result = await agent.run(state)
    return {"compromise_signal": result.to_dict()}


__all__ = ["CompromiseAgent", "run_compromise_agent"]


def create() -> CompromiseAgent:
    """Factory for 6-fn test contract."""
    return CompromiseAgent()

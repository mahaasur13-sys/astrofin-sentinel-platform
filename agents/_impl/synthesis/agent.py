"""
SynthesisAgent — board coordinator that aggregates signals from all agents.

Refactored from 659-line monolithic file into modular sub-packages:
- weights.py    : weight loading + category constants
- classifier.py : signal grouping + conflict detection
- voter.py      : weighted voting + synthesis + guards
- levels.py     : price level calculation (entry/stop/targets)
- formatting.py : breakdown + source collection

Backward-compatible import:
    from agents._impl.synthesis_agent import SynthesisAgent, run_synthesis_agent, create
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents._impl.synthesis.classifier import group_by_category, detect_conflicts
from agents._impl.synthesis.formatting import format_breakdown, collect_sources, get_signal_attr
from agents._impl.synthesis.levels import calculate_levels
from agents._impl.synthesis.voter import vote as weighted_vote
from agents._impl.synthesis.weights import AGENT_WEIGHTS, MIN_AGENTS_FALLBACK, ASTRO_REDUCTION, FUNDAMENTAL_BOOST, QUANT_BOOST, CATEGORY_WEIGHTS
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection
from core.volatility import VolatilityEngine, VolatilityRegime

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseAgent[AgentResponse]):
    """Координатор финального синтеза.

    Получает сигналы от ВСЕХ аналитических агентов,
    применяет гибридное взвешивание,
    формирует финальный торговый сигнал.
    """

    def __init__(self):
        super().__init__(
            name="SynthesisAgent",
            instructions_path="agents/SynthesisAgent_instructions.md",
            domain=None,
            weight=0.0,
        )

    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        """Public entry point. Wraps analyze() with defensive error handling."""
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """Финальный синтез всех агентов.

        Args:
            state: SentinelState с all_signals

        Returns:
            AgentResponse с финальным сигналом
        """
        all_signals = state.get("all_signals", [])
        thompson_selections = state.get("thompson_selections", {})
        called_agents = (
            thompson_selections.get("technical", [])
            + thompson_selections.get("astro", [])
            + thompson_selections.get("electoral", [])
        )

        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")

        # ── FALLBACK: insufficient agents produced signals ─────────────
        if len(all_signals) < MIN_AGENTS_FALLBACK:
            reason_detail = (
                f"Fallback triggered: only {len(all_signals)} agent(s) produced signals "
                f"(minimum required: {MIN_AGENTS_FALLBACK}). "
                f"Agents selected: {called_agents or 'none'}. "
                f"Signals received: {[get_signal_attr(s, 'agent_name', '?') for s in all_signals] or 'none'}."
            )
            return AgentResponse(
                agent_name="SynthesisAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning=reason_detail,
                sources=[],
                metadata={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "current_price": current_price,
                    "fallback": True,
                    "agents_selected": called_agents,
                    "agents_responded": len(all_signals),
                    "threshold_min": MIN_AGENTS_FALLBACK,
                    "breakdown": "  [FALLBACK]      NEUTRAL    [░░░░░░░░░░]   0.0% w=n/a (insufficient signals)",
                },
            )

        # ── R-07: Volatility Risk Engine ────────────────────────────────
        vol_risk = None
        if symbol:
            try:
                vol_engine = VolatilityEngine.from_price_atr(current_price, atr=None)
                for sig in all_signals:
                    meta = get_signal_attr(sig, "metadata", {})
                    if meta.get("atr"):
                        vol_engine = VolatilityEngine.from_price_atr(
                            current_price, meta["atr"]
                        )
                        break
                vol_risk = vol_engine.analyze(symbol=symbol, price=current_price)
            except Exception:
                pass

        regime = vol_risk.regime if vol_risk else VolatilityRegime.NORMAL
        risk_pct = vol_risk.risk_pct if vol_risk else 0.02

        # ─── 1. Группируем по категориям ────────────────────────────────
        categories = group_by_category(all_signals, get_signal_attr)

        # ─── 2. Проверяем конфликты ────────────────────────────────────
        conflicts = detect_conflicts(categories, get_signal_attr)

        # ─── 2.1 CompromiseAgent: explicit trade-off resolver ──────────
        compromise_signal = None
        try:
            from agents._impl.compromise_agent import CompromiseAgent
            compromise = CompromiseAgent()
            compromise_response = await compromise.run(state)
            compromise_meta = compromise_response.metadata or {}
            if (
                compromise_meta.get("compromise_active")
                and compromise_response.confidence >= 60
            ):
                compromise_signal = compromise_response
        except Exception as e:  # noqa: BLE001 — non-fatal
            logger.warning("[SYNTHESIS] CompromiseAgent failed, falling back: %r", e)

        # ─── 3. Считаем взвешенные оценки ───────────────────────────────
        direction, confidence, reasoning = self._synthesize(
            categories, conflicts, symbol
        )

        # Apply compromise override (PR1) — takes precedence over vote.
        if compromise_signal is not None:
            direction = compromise_signal.signal
            confidence = compromise_signal.confidence
            reasoning = f"[COMPROMISE] {compromise_signal.reasoning}"

        # ── V-07: EXTREME regime → force AVOID ──────────────────────────
        if regime == VolatilityRegime.EXTREME:
            direction = SignalDirection.AVOID
            confidence = max(30, confidence - 25)
            reasoning = (
                f"V-07 [EXTREME VOLATILITY] — trade blocked. Original: {reasoning}"
            )

        # ── V-06: Volatility confidence drop ────────────────────────────
        if vol_risk and vol_risk.confidence_drop > 0:
            confidence = max(30, confidence - vol_risk.confidence_drop)
            reasoning += f" [V-06 drop={vol_risk.confidence_drop}]"

        # ── KARL-AMRE Control Loop ─────────────────────────────────────
        meta: dict = {}
        try:
            from agents._impl.amre import (
                MarketState,
                OAPOptimizer,
                estimate_uncertainty,
                record_decision,
            )

            MarketState(
                symbol=symbol,
                price=current_price,
                timeframe=timeframe,
                n_signals=len(all_signals),
                session_id=state.get("session_id", str(uuid.uuid4())),
                timestamp=datetime.now().isoformat(),
                regime=regime.value if hasattr(regime, "value") else str(regime),
                confidence=confidence,
            )
            uncertainty = estimate_uncertainty(all_signals)
            oap = OAPOptimizer()
            oap_result = oap.validate_and_adjust(
                {
                    "uncertainty": uncertainty,
                    "q_star": vol_risk.kelly_adjusted if vol_risk else 0.5,
                    "regime": regime.value if hasattr(regime, "value") else "NORMAL",
                    "timestamp": datetime.now().isoformat(),
                },
                confidence,
                risk_pct,
            )
            confidence = oap_result.confidence
            meta["oap_validation"] = {
                "status": oap_result.status.value,
                "issues": oap_result.issues,
            }
            record_decision(
                decision_id=state.get("session_id", str(uuid.uuid4())) + "_" + symbol,
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                signal=(
                    direction.value if hasattr(direction, "value") else str(direction)
                ),
                confidence=confidence,
                q_star=vol_risk.kelly_adjusted if vol_risk else 0.5,
                uncertainty_total=uncertainty.get("total", 0.5),
                regime=regime.value if hasattr(regime, "value") else str(regime),
                position_pct=oap_result.position_pct,
                passed=oap_result.status.value in ("optimized", "stable"),
                issues=oap_result.issues,
                metadata={"symbol": symbol, "timeframe": timeframe},
            )
        except Exception as amre_err:
            {"enabled": False, "error": str(amre_err)}

        # ─── 4. Формируем breakdown ────────────────────────────────────
        breakdown = format_breakdown(categories)

        # ─── 5. Entry zones, targets, stop (dynamic risk_pct) ──────────
        meta = calculate_levels(direction, current_price, risk_pct)

        if vol_risk:
            meta["volatility_risk"] = {
                "regime": regime.value,
                "atr_pct": round(vol_risk.atr_pct, 4),
                "risk_pct": risk_pct,
                "position_size": vol_risk.position_size,
                "stop_distance_pct": vol_risk.stop_distance_pct,
                "confidence_drop": vol_risk.confidence_drop,
                "kelly_raw": round(vol_risk.kelly_raw, 4),
                "kelly_adjusted": round(vol_risk.kelly_adjusted, 4),
            }

        return AgentResponse(
            agent_name="SynthesisAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=collect_sources(all_signals),
            metadata={
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "breakdown": breakdown,
                "conflicts": conflicts,
                "agent_weights": AGENT_WEIGHTS,
                "thompson_selections": thompson_selections,
                "compromise": (
                    {
                        "active": True,
                        "reason_code": compromise_signal.metadata.get("reason_code"),
                        "top1": compromise_signal.metadata.get("top1"),
                        "top2": compromise_signal.metadata.get("top2"),
                        "expected_utility": compromise_signal.metadata.get(
                            "expected_utility"
                        ),
                        "drift_triggers": compromise_signal.metadata.get(
                            "drift_triggers", []
                        ),
                    }
                    if compromise_signal is not None
                    else None
                ),
                **meta,
            },
        )

    def _synthesize(
        self, categories: dict[str, list], conflicts: list, symbol: str
    ) -> tuple[SignalDirection, int, str]:
        """Apply conflict resolution weights and delegate to voter."""
        eff = {k: v for k, v in CATEGORY_WEIGHTS.items()}
        if conflicts:
            for c in conflicts:
                if c["type"] == "astro_vs_fundamental_quant":
                    eff["astro"] = eff.get("astro", 0.25) * (1 - ASTRO_REDUCTION)
                    eff["fundamental"] = eff.get("fundamental", 0.15) * (
                        1 + FUNDAMENTAL_BOOST
                    )
                    eff["quant"] = eff.get("quant", 0.20) * (1 + QUANT_BOOST)
        return weighted_vote(categories, get_signal_attr, eff)


# ─── Convenience runner ──────────────────────────────────────────────────


async def run_synthesis_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = SynthesisAgent()
    result = await agent.run(state)
    return {"synthesis_signal": result.to_dict()}


def create() -> SynthesisAgent:
    """Factory for 6-fn test contract."""
    return SynthesisAgent()

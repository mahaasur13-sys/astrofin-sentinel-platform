"""
AstroFin Sentinel v5 — Synthesis Agent
AstroCouncil: координатор всех агентов, финальный синтез.
Вес в финальном сигнале = 100% (координатор)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path

import yaml

from agents._impl.ephemeris_decorator import EphemerisUnavailableError
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection
from core.volatility import VolatilityEngine, VolatilityRegime

logger = logging.getLogger(__name__)

# ─── Fallback guard ─────────────────────────────────────────────────────────────
MIN_AGENTS_FALLBACK = 2  # minimum agents needed for a reliable synthesis
# If fewer agents produced signals, fallback is triggered

# ─── Load weights from config (R-02: single source of truth) ──────────────────


def _load_weights() -> dict:
    """
    Load and normalize weights from config/agent_weights.yaml.
    Performs runtime validation: raises ValueError if weights don't sum to 1.0.
    """
    config_path = Path(__file__).parent.parent / "config" / "agent_weights.yaml"
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
    else:
        data = {}

    def _normalize(d, name: str):
        """Scale dict values to sum to 1.0 + runtime validation."""
        if not d:
            return d
        total = sum(v for v in d.values() if isinstance(v, (int, float)))  # noqa: UP038
        if total <= 0:
            return d
        normalized = {k: v / total for k, v in d.items()}
        # Runtime validation: sum must be 1.0 (within epsilon)
        actual = sum(normalized.values())
        if abs(actual - 1.0) > 0.001:
            raise ValueError(f"{name} sum = {actual:.4f} (expected 1.0). Check config/agent_weights.yaml — all weight values must sum to 1.0.")
        return normalized

    if "category_weights" in data:
        data["category_weights"] = _normalize(data["category_weights"], "category_weights")
    if "agent_weights" in data:
        data["agent_weights"] = _normalize(data["agent_weights"], "agent_weights")

    return data


_CONFIG = _load_weights()

# Fallback defaults (used only if config is absent/corrupt)
_DEFAULT_CATEGORY_WEIGHTS = {
    "astro": 0.22,
    "fundamental": 0.15,
    "macro": 0.15,
    "quant": 0.18,
    "options": 0.12,
    "sentiment": 0.09,
    "technical": 0.09,
}

_DEFAULT_AGENT_WEIGHTS = {
    "FundamentalAgent": 0.20,
    "QuantAgent": 0.20,
    "MacroAgent": 0.15,
    "OptionsFlowAgent": 0.15,
    "SentimentAgent": 0.10,
    "TechnicalAgent": 0.10,
    "BullResearcher": 0.05,
    "BearResearcher": 0.05,
}

CATEGORY_WEIGHTS = _CONFIG.get("category_weights", _DEFAULT_CATEGORY_WEIGHTS)
AGENT_WEIGHTS = _CONFIG.get("agent_weights", _DEFAULT_AGENT_WEIGHTS)

# Guards
MAX_CONFIDENCE = _CONFIG.get("guards", {}).get("max_confidence", 92)
MIN_CONFIDENCE = _CONFIG.get("guards", {}).get("min_confidence", 30)
VOLATILITY_DROP = _CONFIG.get("guards", {}).get("volatility_drop", 15)

# Conflict resolution
_CONFLICT_CFG = _CONFIG.get("conflict_resolution", {}).get("astro_vs_fundamental_quant", {})
ASTRO_REDUCTION = _CONFLICT_CFG.get("astro_reduction", 0.30)
FUNDAMENTAL_BOOST = _CONFLICT_CFG.get("fundamental_boost", 0.18)
QUANT_BOOST = _CONFLICT_CFG.get("quant_boost", 0.12)


class SynthesisAgent(BaseAgent[AgentResponse]):
    """
    SynthesisAgent = Координатор финального синтеза.

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
        """Public entry point. Wraps analyze() with the latency histogram
        and defensive error handling so a single agent can never crash
        the orchestrator."""
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    async def analyze(self, state: dict) -> AgentResponse:
        """
        Финальный синтез всех агентов.

        Args:
            state: SentinelState с all_signals

        Returns:
            AgentResponse с финальным сигналом
        """
        all_signals = state.get("all_signals", [])
        thompson_selections = state.get("thompson_selections", {})
        called_agents = thompson_selections.get("technical", []) + thompson_selections.get("astro", []) + thompson_selections.get("electoral", [])

        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")

        # ── FALLBACK: insufficient agents produced signals ─────────────────────────
        if len(all_signals) < MIN_AGENTS_FALLBACK:
            reason_detail = (
                f"Fallback triggered: only {len(all_signals)} agent(s) produced signals "
                f"(minimum required: {MIN_AGENTS_FALLBACK}). "
                f"Agents selected: {called_agents or 'none'}. "
                f"Signals received: {[self._get_signal_attr(s, 'agent_name', '?') for s in all_signals] or 'none'}."
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
        # Compute dynamic risk_pct before synthesis so levels are volatility-aware
        vol_risk = None
        if symbol:
            try:
                vol_engine = VolatilityEngine.from_price_atr(current_price, atr=None)
                # Try to get ATR from any agent that computed it
                for sig in all_signals:
                    meta = self._get_signal_attr(sig, "metadata", {})
                    if meta.get("atr"):
                        vol_engine = VolatilityEngine.from_price_atr(current_price, meta["atr"])
                        break
                vol_risk = vol_engine.analyze(symbol=symbol, price=current_price)
            except Exception:
                pass

        regime = vol_risk.regime if vol_risk else VolatilityRegime.NORMAL
        risk_pct = vol_risk.risk_pct if vol_risk else 0.02

        # ─── 1. Группируем по категориям ────────────────────────────────
        categories = self._group_by_category(all_signals)

        # ─── 2. Проверяем конфликты ────────────────────────────────────
        conflicts = self._detect_conflicts(categories)

        # ─── 2.1 CompromiseAgent: explicit trade-off resolver ─────────
        # Replaces the hard-coded ASTRO_REDUCTION whenever Astro and
        # Fundamental+Quant disagree. Run the agent; if it produced an
        # active compromise at sufficient confidence, defer to it.
        compromise_signal = None
        try:
            from agents._impl.compromise_agent import CompromiseAgent

            compromise = CompromiseAgent()
            compromise_response = await compromise.run(state)
            compromise_meta = compromise_response.metadata or {}
            if compromise_meta.get("compromise_active") and compromise_response.confidence >= 60:
                compromise_signal = compromise_response
        except Exception as e:  # noqa: BLE001 — non-fatal
            logger.warning("[SYNTHESIS] CompromiseAgent failed, falling back: %r", e)

        # ─── 3. Считаем взвешенные оценки ───────────────────────────────
        direction, confidence, reasoning = self._synthesize(categories, conflicts, symbol)

        # Apply compromise override (PR1) — takes precedence over vote.
        if compromise_signal is not None:
            direction = compromise_signal.signal
            confidence = compromise_signal.confidence
            reasoning = f"[COMPROMISE] {compromise_signal.reasoning}"

        # ── V-07: EXTREME regime → force AVOID ──────────────────────────
        if regime == VolatilityRegime.EXTREME:
            direction = SignalDirection.AVOID
            confidence = max(30, confidence - 25)
            reasoning = f"V-07 [EXTREME VOLATILITY] — trade blocked. Original: {reasoning}"

        # ── V-06: Volatility confidence drop ────────────────────────────
        if vol_risk and vol_risk.confidence_drop > 0:
            confidence = max(30, confidence - vol_risk.confidence_drop)
            reasoning += f" [V-06 drop={vol_risk.confidence_drop}]"

        # ── KARL-AMRE Control Loop ─────────────────────────────────────────
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
                signal=direction.value if hasattr(direction, "value") else str(direction),
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
        breakdown = self._format_breakdown(categories)

        # ─── 5. Entry zones, targets, stop (dynamic risk_pct) ──────────
        meta = self._calculate_levels(direction, current_price, risk_pct)

        # Attach volatility risk info to metadata
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
            sources=self._collect_sources(all_signals),
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
                        "expected_utility": compromise_signal.metadata.get("expected_utility"),
                        "drift_triggers": compromise_signal.metadata.get("drift_triggers", []),
                    }
                    if compromise_signal is not None
                    else None
                ),
                **meta,
            },
        )

    def _get_signal_attr(self, sig, key: str, default=None):
        """Get attribute or dict key from signal (handles both AgentResponse and dict)."""
        if hasattr(sig, key):
            return getattr(sig, key)
        if isinstance(sig, dict):
            return sig.get(key, default)
        return default

    def _group_by_category(self, signals: list) -> dict[str, list]:
        """Группирует сигналы по категориям."""
        category_map = {
            # AstroCouncil sub-agents — все "astro"
            "AstroCouncil": "astro",
            "ElectoralAgent": "astro",
            "BradleyAgent": "astro",
            "TimeWindowAgent": "astro",
            "GannAgent": "astro",
            "ElliotWaveAgent": "astro",  # Fixed: was "ElliotAgent" (typo)
            "CycleAgent": "astro",
            "SolarAgent": "astro",
            "LunarAgent": "astro",
            "PlanetaryAgent": "astro",
            "MuhurtaAgent": "astro",
            "ElectionAgent": "astro",
            "DignityAgent": "astro",
            # Other categories
            "FundamentalAgent": "fundamental",
            "InsiderAgent": "fundamental",
            "MacroAgent": "macro",
            "QuantAgent": "quant",
            "MLPredictorAgent": "quant",
            "OptionsFlowAgent": "options",
            "BullResearcher": "sentiment",
            "BearResearcher": "sentiment",
            "SentimentAgent": "sentiment",
            "TechnicalAgent": "technical",
            "MarketAnalyst": "technical",
        }

        categories = {
            "astro": [],
            "fundamental": [],
            "macro": [],
            "quant": [],
            "options": [],
            "sentiment": [],
            "technical": [],
        }

        for sig in signals:
            agent = self._get_signal_attr(sig, "agent_name", "")
            cat = category_map.get(agent, "other")
            if cat in categories:
                categories[cat].append(sig)

        return categories

    def _detect_conflicts(self, categories: dict[str, list]) -> list:
        """Определяет конфликты между категориями."""
        conflicts = []

        def get_direction(signals):
            if not signals:
                return "NEUTRAL"
            votes = [self._get_signal_attr(s, "signal", "NEUTRAL").upper() for s in signals]
            long_v = votes.count("LONG") + votes.count("BUY") + votes.count("STRONG_BUY")
            short_v = votes.count("SHORT") + votes.count("SELL") + votes.count("STRONG_SELL")
            return "LONG" if long_v > short_v else "SHORT" if short_v > long_v else "NEUTRAL"

        astro_dir = get_direction(categories.get("astro", []))
        fund_dir = get_direction(categories.get("fundamental", []))
        quant_dir = get_direction(categories.get("quant", []))

        # Конфликт Astro vs Fundamental+Quant
        if astro_dir != "NEUTRAL":
            other = [fund_dir, quant_dir]
            non_neutral = [d for d in other if d != "NEUTRAL"]
            if non_neutral and astro_dir != non_neutral[0]:
                conflicts.append(
                    {
                        "type": "astro_vs_fundamental_quant",
                        "astro": astro_dir,
                        "fundamental": fund_dir,
                        "quant": quant_dir,
                        "resolution": "reduce_astro_weight_by_30pct",
                    }
                )

        return conflicts

    def _synthesize(self, categories: dict[str, list], conflicts: list, symbol: str) -> tuple:
        """Финальный синтез."""
        eff = {k: v for k, v in CATEGORY_WEIGHTS.items()}
        if conflicts:
            for c in conflicts:
                if c["type"] == "astro_vs_fundamental_quant":
                    eff["astro"] = eff.get("astro", 0.25) * (1 - ASTRO_REDUCTION)
                    eff["fundamental"] = eff.get("fundamental", 0.15) * (1 + FUNDAMENTAL_BOOST)
                    eff["quant"] = eff.get("quant", 0.20) * (1 + QUANT_BOOST)
        direction, confidence, reasoning = self._vote(categories, eff)
        return direction, confidence, reasoning

    def _vote(self, categories: dict[str, list], eff: dict[str, float] = None) -> tuple:
        """Простое голосование по категориям с EC-01/V-06 guards."""

        cat_weights = eff if eff else CATEGORY_WEIGHTS

        long_w = 0.0
        short_w = 0.0
        neutral_w = 0.0

        for cat, signals in categories.items():
            if not signals:
                continue
            w = cat_weights.get(cat, 0.10)

            for sig in signals:
                conf = self._get_signal_attr(sig, "confidence", 50)
                direction = self._get_signal_attr(sig, "signal", "NEUTRAL").upper()

                if direction in ("LONG", "BUY", "STRONG_BUY"):
                    long_w += conf * w
                elif direction in ("SHORT", "SELL", "STRONG_SELL"):
                    short_w += conf * w
                else:
                    neutral_w += conf * w

        total = long_w + short_w + neutral_w
        if total > 0:
            long_pct = long_w / total
            short_pct = short_w / total
        else:
            long_pct = short_pct = 0.5

        if long_pct > 0.55:
            direction = SignalDirection.LONG
            confidence = min(MAX_CONFIDENCE, 50 + int(long_pct * 40))  # EC-01 cap
            reasoning = f"Long consensus: {long_pct * 100:.0f}% weighted votes"
        elif short_pct > 0.55:
            direction = SignalDirection.SHORT
            confidence = min(MAX_CONFIDENCE, 50 + int(short_pct * 40))  # EC-01 cap
            reasoning = f"Short consensus: {short_pct * 100:.0f}% weighted votes"
        else:
            direction = SignalDirection.NEUTRAL
            confidence = 50
            reasoning = f"No strong consensus: Long {long_pct * 100:.0f}% | Short {short_pct * 100:.0f}%"

        # Apply guards
        confidence, guard_applied = self._apply_guards(direction, confidence)
        if guard_applied:
            reasoning += f" [{guard_applied}]"

        return direction, confidence, reasoning

    def _apply_guards(self, direction: SignalDirection, confidence: int) -> tuple:
        """
        Apply EC-01 (hubris cap) — V-06 is handled in run() via vol_risk.
        Returns: (adjusted_confidence, guard_label_or_None)
        """
        adjusted = min(confidence, MAX_CONFIDENCE)

        if adjusted < MIN_CONFIDENCE:
            return MIN_CONFIDENCE, "GUARD-TRIGGERED-NEUTRAL"

        return adjusted, None

    def _format_breakdown(self, categories: dict[str, list]) -> str:
        """Форматирует breakdown."""
        lines = []

        for cat, signals in categories.items():
            w = CATEGORY_WEIGHTS.get(cat, 0.0)
            if not signals:
                lines.append(f"  [{cat.upper():12s}] NEUTRAL    [░░░░░░░░░░]   0.0% w={w:.2f} (no signals)")
                continue

            conf_avg = sum(self._get_signal_attr(s, "confidence", 50) for s in signals) / len(signals)
            votes = [self._get_signal_attr(s, "signal", "NEUTRAL").upper() for s in signals]
            long_v = votes.count("LONG") + votes.count("BUY")
            short_v = votes.count("SHORT") + votes.count("SELL")

            direction = "LONG ▲" if long_v > short_v else "SHORT ▼" if short_v > long_v else "NEUT"

            bar = "█" * int(conf_avg / 10) + "░" * (10 - int(conf_avg / 10))
            agents = ", ".join(self._get_signal_attr(s, "agent_name", "?") for s in signals)

            lines.append(f"  [{cat.upper():12s}] {direction:12s} [{bar}] {conf_avg:5.1f}% w={w:.2f} ({agents})")

        return "\n".join(lines)

    def _collect_sources(self, signals: list) -> list:
        """Собирает источники."""
        sources = []
        for sig in signals:
            for src in self._get_signal_attr(sig, "sources", []):
                if src and isinstance(src, str):
                    sources.append(src)
        return list(set(sources))

    def _calculate_levels(self, direction: SignalDirection, price: float, risk_pct: float) -> dict:
        """
        Рассчитывает entry zones, targets, stop.
        Uses dynamic risk_pct from VolatilityEngine (R-07):
          - stop_distance = risk_pct * 1.5  (slightly wider than risk for buffer)
          - targets       = risk_pct * 3.0  (3:1 risk-reward)
          - position      = risk_pct / 2    (half the risk as position size)
        """
        rr_ratio = 2.5  # risk-reward ratio
        stop_dist = risk_pct * 1.5  # 1.5× risk = stop distance
        tp_dist = risk_pct * rr_ratio  # 2.5× risk = first target

        if direction == SignalDirection.LONG:
            entry_low = price * (1 - risk_pct * 0.5)
            entry_high = price * (1 + risk_pct * 0.5)
            stop = price * (1 - stop_dist)
            targets = [price * (1 + tp_dist * i) for i in [1, 2, 3]]
            position = risk_pct / 2

        elif direction == SignalDirection.SHORT:
            entry_low = price * (1 - risk_pct * 0.5)
            entry_high = price * (1 + risk_pct * 0.5)
            stop = price * (1 + stop_dist)
            targets = [price * (1 - tp_dist * i) for i in [1, 2, 3]]
            position = risk_pct / 2

        else:
            entry_low = price * (1 - risk_pct * 0.25)
            entry_high = price * (1 + risk_pct * 0.25)
            stop = price * (1 - stop_dist * 0.5)
            targets = [
                price * (1 + risk_pct * 0.5),
                price * (1 + risk_pct),
                price * (1 + risk_pct * 1.5),
            ]
            position = risk_pct / 3

        return {
            "entry_zone": (round(entry_low, 2), round(entry_high, 2)),
            "stop_loss": round(stop, 2),
            "targets": [round(t, 2) for t in targets],
            "position_size": round(position, 4),
            "risk_pct_used": risk_pct,
        }


# ─── Convenience runner ──────────────────────────────────────────────────


async def run_synthesis_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = SynthesisAgent()
    result = await agent.run(state)
    return {"synthesis_signal": result.to_dict()}


def create() -> SynthesisAgent:
    """Factory for 6-fn test contract."""
    return SynthesisAgent()

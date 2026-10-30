"""
AstroFin Sentinel v5 — AstroCouncil Agent
Главный координатор всех аналитических агентов.
Астро-совет (ASTRO_POOL): взвешенное голосование _weighted_vote, веса из synthesis/weights.

Все суб-агенты запускаются параллельно.
Финальный сигнал = взвешенная комбинация всех голосов.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from agents._impl.ephemeris_decorator import (
    EphemerisUnavailableError,
    require_ephemeris,
)
from agents._impl.synthesis.weights import get_agent_weight
from agents.base_agent import AgentResponse, BaseAgent
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, SignalDirection

logger = logging.getLogger(__name__)


# Weights: single source is agents/_impl/synthesis/weights.get_agent_weight().
# This module must not define its own weight numbers.

# Council members = core.thompson.ASTRO_POOL (variant A, as release/v1 94f3544a).
ASTRO_MEMBERS: tuple[str, ...] = ("GannAgent", "BradleyAgent", "ElliotAgent", "CycleAgent", "TimeWindowAgent")
# At least this many members must have real data, otherwise the council is NEUTRAL.
MIN_MEMBERS_WITH_DATA = 3


def _has_no_data(resp: Any) -> bool:
    meta = getattr(resp, "metadata", None) or {}
    return bool(meta.get("no_data") or meta.get("degraded") or meta.get("error"))

_SIGNAL_ALIASES = {
    "BUY": SignalDirection.LONG,
    "STRONG_BUY": SignalDirection.LONG,
    "SELL": SignalDirection.SHORT,
    "STRONG_SELL": SignalDirection.SHORT,
}


def _to_direction(raw: Any) -> SignalDirection:
    if isinstance(raw, SignalDirection):
        return raw
    key = str(getattr(raw, "value", raw)).upper()
    if key in _SIGNAL_ALIASES:
        return _SIGNAL_ALIASES[key]
    try:
        return SignalDirection(key)
    except (ValueError, TypeError):
        return SignalDirection.NEUTRAL


class AstroCouncilAgent(BaseAgent):
    """
    AstroCouncil — координатор всех агентов.

    Получает данные от всех аналитических агентов и объединяет
    через _weighted_vote; веса — synthesis/weights.get_agent_weight.

    Критично: всегда вызывает Swiss Ephemeris.
    """

    def __init__(self):
        super().__init__(
            name="AstroCouncil",
            instructions_path=None,
            domain=None,
            weight=1.0,
        )
        # Optional explicit override (tests / experiments). None -> synthesis weights.
        self._weights: dict[str, float] | None = None
        self._sub_agents = {}

    def register_sub_agent(self, name: str, agent) -> None:
        """Register a sub-agent."""
        self._sub_agents[name] = agent

    @track_agent_metrics
    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        """
        Главный метод координации.

        1. Swiss Ephemeris (критично)
        2. Параллельно все суб-агенты
        3. _weighted_vote (веса — synthesis/weights.get_agent_weight, нормированы по ASTRO_MEMBERS)
        """
        try:
            dt = context.get("datetime") or datetime.now(timezone.utc)

            # 1. Критичный вызов Swiss Ephemeris
            eph = self._call_ephemeris(dt)

            # 2. Параллельный запуск всех суб-агентов
            responses = await self._run_sub_agents(context)

            # 3. Взвешенное голосование большинством (release/v1 _weighted_vote)
            resolved_weights = {r.agent_name: self._weight_for(r.agent_name) for r in responses}
            final_signal = self._weighted_vote(responses)

            signal_value = getattr(final_signal.signal, "value", final_signal.signal)
            return AgentResponse(
                agent_name="AstroCouncil",
                signal=signal_value,
                confidence=final_signal.confidence,
                reasoning=final_signal.reasoning,
                sources=[],
                metadata={
                    "astro_yoga": eph.get("yoga", "unknown"),
                    "astro_score": eph.get("score", 50),
                    "ephemeris": {k: v for k, v in eph.items() if k != "error"},
                    "total_agents": len(responses),
                    "weights": resolved_weights,
                    "final_signal": final_signal.to_dict(),
                },
            )
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    def _weight_for(self, name: str) -> float:
        """Weight from the single source (synthesis/weights.py); unknown -> 0.0 + logger.error."""
        if self._weights is not None:
            if name not in self._weights:
                logger.error("astro_council_unknown_agent_weight", extra={"agent_name": name})
            return self._weights.get(name, 0.0)
        if name not in ASTRO_MEMBERS:
            logger.error("astro_council_unknown_agent_weight", extra={"agent_name": name})
            return 0.0
        total = sum(get_agent_weight(n) for n in ASTRO_MEMBERS)
        return get_agent_weight(name) / total if total > 0 else 0.0

    def _weighted_vote(self, responses: list[AgentResponse]) -> AgentResponse:
        """Взвешенное голосование: побеждает сторона с наибольшим весом,
        если её доля > 40% и отрыв от второй > 10%.
        """
        votes = {
            SignalDirection.LONG: 0.0,
            SignalDirection.SHORT: 0.0,
            SignalDirection.NEUTRAL: 0.0,
        }
        total_weight = 0.0
        reasons = []

        with_data = 0
        for resp in responses:
            name = resp.agent_name
            weight = self._weight_for(name)
            if weight == 0:
                continue
            if _has_no_data(resp):
                reasons.append(f"{name}: no_data (abstain)")
                continue  # no market data -> abstain, weight 0
            with_data += 1
            sig = _to_direction(resp.signal)
            if sig not in votes:
                sig = SignalDirection.NEUTRAL
            contribution = weight * (resp.confidence / 100.0)
            votes[sig] += contribution
            total_weight += contribution
            reasons.append(f"{name}: {sig.value} ({resp.confidence:.0f}%)")

        if total_weight == 0 or with_data < MIN_MEMBERS_WITH_DATA:
            return AgentResponse(
                agent_name="AstroCouncil",
                signal=SignalDirection.NEUTRAL,
                confidence=20,
                reasoning=(
                    "All astro agents failed" if total_weight == 0
                    else f"Quorum not met: {with_data}/{MIN_MEMBERS_WITH_DATA} members with data"
                ),
                metadata={"no_data": with_data == 0, "members_with_data": with_data},
            )

        # Нормализуем голоса
        for sig in votes:
            votes[sig] /= total_weight

        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        if sorted_votes[0][1] > 0.4 and (sorted_votes[0][1] - sorted_votes[1][1]) > 0.10:
            final_signal = sorted_votes[0][0]
        else:
            final_signal = SignalDirection.NEUTRAL

        raw_confidence = votes[final_signal] * min(100.0, total_weight * 100.0)
        confidence = max(10.0, min(95.0, raw_confidence))

        reasoning = " | ".join(reasons[:3])
        reasoning = f"[AstroCouncil] {final_signal.value} ({confidence:.0f}%) — {reasoning}"

        return AgentResponse(
            agent_name="AstroCouncil",
            signal=final_signal,
            confidence=int(confidence),
            reasoning=reasoning,
            sources=[],
            metadata={"votes": votes, "total_weight": total_weight},
        )

    async def _run_sub_agents(self, context: dict[str, Any]) -> list[AgentResponse]:
        """Параллельно запускает Thompson-selected суб-агентов.

        If context contains "_thompson_selected_astro" (list of agent names),
        only those agents are called. Otherwise all registered agents are called.
        """
        if not self._sub_agents:
            self._register_sub_agents()

        selected = context.get("_thompson_selected_astro")
        if selected:
            agents_to_run = {
                name: agent
                for name, agent in self._sub_agents.items()
                if name in selected
            }
        else:
            agents_to_run = self._sub_agents

        tasks = []
        names = []
        for name, agent in agents_to_run.items():
            if hasattr(agent, "run"):
                tasks.append(agent.run(context))
                names.append(name)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses = []
        for name, result in zip(names, results, strict=False):
            if isinstance(result, Exception):
                responses.append(
                    AgentResponse(
                        agent_name=name,
                        signal="NEUTRAL",
                        confidence=30,
                        reasoning=f"Agent error: {str(result)[:100]}",
                        sources=[],
                        metadata={"error": True},
                    )
                )
            else:
                responses.append(result)

        return responses

    def _register_sub_agents(self) -> None:
        """Регистрация астро-суб-агентов (AstroCouncil = координатор астро-блока, ASTRO_POOL)."""
        try:
            from agents._impl.bradley_agent import BradleyAgent
            from agents._impl.cycle_agent import CycleAgent
            from agents._impl.elliot_agent import ElliotAgent
            from agents._impl.gann_agent import GannAgent
            from agents._impl.time_window_agent import TimeWindowAgent

            self._sub_agents = {
                "GannAgent": GannAgent(),
                "BradleyAgent": BradleyAgent(),
                "ElliotAgent": ElliotAgent(),
                "CycleAgent": CycleAgent(),
                "TimeWindowAgent": TimeWindowAgent(),
            }
        except ImportError:
            logger.exception("astro_council_register_failed")
            self._sub_agents = {}

    def _call_ephemeris(self, dt: datetime) -> dict[str, Any]:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import (
                HAS_SWISS_EPHEMERIS,
                _julian_day,
                calculate_planet,
            )

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            jupiter = calculate_planet("jupiter", jd)
            venus = calculate_planet("venus", jd)
            mercury = calculate_planet("mercury", jd)
            mars = calculate_planet("mars", jd)
            saturn = calculate_planet("saturn", jd)
            moon = calculate_planet("moon", jd)

            score = 50
            yoga = "neutral"

            # Jupiter-Moon = expansion
            jup_moon = abs(jupiter.longitude - moon.longitude) % 360
            if jup_moon < 30 or jup_moon > 330:
                score += 15
                yoga = "jupiter_moon_trine"
            elif 85 < jup_moon < 95:
                score -= 10
                yoga = "jupiter_moon_square"

            # Venus-Moon = favor
            ven_moon = abs(venus.longitude - moon.longitude) % 360
            if ven_moon < 30 or ven_moon > 330:
                score += 10
                yoga = f"{yoga}_venus"

            # Saturn caution
            sat_moon = abs(saturn.longitude - moon.longitude) % 360
            if 85 < sat_moon < 95:
                score -= 15
                yoga = f"{yoga}_saturn_square"

            return {
                "yoga": yoga,
                "score": max(0, min(100, score)),
                "jupiter": round(jupiter.longitude, 2),
                "venus": round(venus.longitude, 2),
                "mercury": round(mercury.longitude, 2),
                "mars": round(mars.longitude, 2),
                "saturn": round(saturn.longitude, 2),
                "moon": round(moon.longitude, 2),
            }
        except Exception as e:
            return {"yoga": "error", "score": 50, "error": str(e)}


# ─── Convenience runner ────────────────────────────────────────────────────────


async def run_astro_council(context: dict[str, Any]) -> dict[str, Any]:
    """Runner для оркестратора."""
    agent = AstroCouncilAgent()
    result = await agent.run(context)
    return {"astro_council_signal": result.to_dict()}

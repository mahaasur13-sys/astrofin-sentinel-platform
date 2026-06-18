"""
AstroFin Sentinel v5 — AstroCouncil Agent
Главный координатор всех аналитических агентов.
Гибридное взвешивание через TradingSignal.from_agents.

Все суб-агенты запускаются параллельно.
Финальный сигнал = взвешенная комбинация всех голосов.
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents._impl.synthesis_agent import AGENT_WEIGHTS, CATEGORY_WEIGHTS
from agents._impl.types import TradingSignal
from agents.base_agent import AgentResponse, BaseAgent
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, SignalDirection

logger = logging.getLogger(__name__)


# Map agent short name → category → weight
# Agents in ASTRO_POOL / TECHNICAL_POOL use short names as agent_name.
# TradingSignal.from_agents looks up weights by agent_name.
# CATEGORY_WEIGHTS keys are categories; AGENT_WEIGHTS keys are full class names.
_AGENT_CATEGORY_MAP = {
    "Fundamental": "fundamental",
    "Macro": "macro",
    "Quant": "quant",
    "OptionsFlow": "options",
    "Sentiment": "sentiment",
    "Technical": "technical",
    "BullResearcher": "sentiment",
    "BearResearcher": "sentiment",
}


def _build_agent_weights() -> dict[str, float]:
    """Derive agent-name → weight mapping from CATEGORY_WEIGHTS + AGENT_WEIGHTS.

    Priority: agent name in AGENT_WEIGHTS > category weight from CATEGORY_WEIGHTS.
    Result is normalized to sum to 1.0.
    """
    weights = {}
    for agent_short, category in _AGENT_CATEGORY_MAP.items():
        if agent_short in AGENT_WEIGHTS:
            weights[agent_short] = AGENT_WEIGHTS[agent_short]
        else:
            weights[agent_short] = CATEGORY_WEIGHTS.get(category, 0.10)
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    return weights


HYBRID_WEIGHTS = _build_agent_weights()


class AstroCouncilAgent(BaseAgent):
    """
    AstroCouncil — координатор всех агентов.

    Получает данные от всех аналитических агентов и объединяет
    через гибридное взвешивание TradingSignal.from_agents.

    Критично: всегда вызывает Swiss Ephemeris.
    """

    def __init__(self):
        super().__init__(
            name="AstroCouncil",
            instructions_path=None,
            domain=None,
            weight=1.0,
        )
        self._weights = HYBRID_WEIGHTS
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
        3. TradingSignal.from_agents для финального взвешивания
        """
        try:
            dt = context.get("datetime") or datetime.utcnow()
            symbol = context.get("symbol", "BTC")
            price = context.get("price") or context.get("current_price") or 100.0

            # 1. Критичный вызов Swiss Ephemeris
            eph = self._call_ephemeris(dt)

            # 2. Параллельный запуск всех суб-агентов
            responses = await self._run_sub_agents(context)

            # 3. Гибридное взвешивание
            final_signal = TradingSignal.from_agents(
                symbol=symbol,
                responses=responses,
                entry_price=price,
                weights=self._weights,
            )

            return AgentResponse(
                agent_name="AstroCouncil",
                signal=final_signal.signal.value,
                confidence=final_signal.confidence,
                reasoning=final_signal.summary,
                sources=[],
                metadata={
                    "astro_yoga": eph.get("yoga", "unknown"),
                    "astro_score": eph.get("score", 50),
                    "ephemeris": {k: v for k, v in eph.items() if k != "error"},
                    "total_agents": len(responses),
                    "weights": self._weights,
                    "final_signal": final_signal.to_dict(),
                },
            )
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    async def _run_sub_agents(self, context: dict[str, Any]) -> list[AgentResponse]:
        """Параллельно запускает Thompson-selected суб-агентов.

        If context contains "_thompson_selected_astro" (list of agent names),
        only those agents are called. Otherwise all registered agents are called.
        """
        if not self._sub_agents:
            self._register_sub_agents()

        selected = context.get("_thompson_selected_astro")
        if selected:
            agents_to_run = {name: agent for name, agent in self._sub_agents.items() if name in selected}
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
        """Регистрация всех суб-агентов."""
        try:
            from agents._impl.bear_researcher import BearResearcherAgent
            from agents._impl.bull_researcher import BullResearcherAgent
            from agents._impl.fundamental_agent import FundamentalAgent
            from agents._impl.macro_agent import MacroAgent
            from agents._impl.options_flow_agent import OptionsFlowAgent
            from agents._impl.quant_agent import QuantAgent
            from agents._impl.sentiment_agent import SentimentAgent
            from agents._impl.technical_agent import TechnicalAgent

            self._sub_agents = {
                "Fundamental": FundamentalAgent(),
                "Macro": MacroAgent(),
                "Quant": QuantAgent(),
                "OptionsFlow": OptionsFlowAgent(),
                "Sentiment": SentimentAgent(),
                "Technical": TechnicalAgent(),
                "BullResearcher": BullResearcherAgent(),
                "BearResearcher": BearResearcherAgent(),
            }
        except ImportError:
            # Если агенты не найдены, используем пустой dict
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

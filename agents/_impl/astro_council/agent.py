"""
AstroCouncilAgent — координационный слой астро-домена.

Агрегирует сигналы от BradleyAgent, GannAgent, CycleAgent, ElectoralAgent, TimeWindowAgent.
Применяет взвешенный консенсус с защитой от противоречий.
"""

import logging

from agents.metrics import track_agent_metrics
from core.base_agent import AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)

AGENT_WEIGHTS = {
    "BradleyAgent": 0.20,
    "GannAgent": 0.20,
    "CycleAgent": 0.20,
    "ElectoralAgent": 0.20,
    "TimeWindowAgent": 0.20,
}


class AstroCouncilAgent(BaseAgent[AgentResponse]):
    """Совет астро-агентов с взвешенным голосованием."""

    def __init__(self):
        super().__init__(name="AstroCouncil", domain="astro", weight=0.10)
        from agents._impl.bradley_agent import BradleyAgent
        from agents._impl.cycle_agent import CycleAgent
        from agents._impl.electoral_agent import ElectoralAgent
        from agents._impl.gann_agent import GannAgent
        from agents._impl.time_window_agent import TimeWindowAgent

        self.agents = {
            "BradleyAgent": BradleyAgent(),
            "GannAgent": GannAgent(),
            "CycleAgent": CycleAgent(),
            "ElectoralAgent": ElectoralAgent(),
            "TimeWindowAgent": TimeWindowAgent(),
        }

    @track_agent_metrics
    async def run(self, state: dict) -> dict:
        """Pattern A compliant run() with graceful degradation."""
        try:
            response = await self.aggregate(state)
            return {"astro_council_signal": response.to_dict()}
        except Exception as e:  # noqa: BLE001 - last-resort guard
            logger.exception("AstroCouncilAgent degraded")
            degraded_inner = {
                "signal": "NEUTRAL",
                "confidence": 0.0,
                "reason": f"degraded: {type(e).__name__} - {e!r}",
                "metadata": {"source": "astro_council_fallback"},
            }
            return {"astro_council_signal": degraded_inner}

    async def aggregate(self, state: dict) -> AgentResponse:
        responses = {}
        for name, agent in self.agents.items():
            try:
                resp = await agent.run(state)
                if isinstance(resp, dict):
                    resp = AgentResponse(**resp)
                responses[name] = resp
            except Exception as e:
                logger.warning("AstroCouncil: agent %s failed: %s", name, e)
                responses[name] = AgentResponse(
                    agent_name=name,
                    signal=SignalDirection.NEUTRAL,
                    confidence=10,
                    reasoning=f"Agent {name} failed: {str(e)}",
                )
        return self._weighted_vote(responses)

    def _weighted_vote(self, responses: dict) -> AgentResponse:
        votes = {
            SignalDirection.LONG: 0.0,
            SignalDirection.SHORT: 0.0,
            SignalDirection.NEUTRAL: 0.0,
        }
        total_weight = 0.0
        reasons = []

        for name, resp in responses.items():
            weight = AGENT_WEIGHTS.get(name, 0.0)
            if weight == 0:
                continue
            contribution = weight * (resp.confidence / 100.0)
            votes[resp.signal] += contribution
            total_weight += contribution
            reasons.append(f"{name}: {resp.signal.value} ({resp.confidence:.0f}%)")

        if total_weight == 0:
            return AgentResponse(
                agent_name="AstroCouncil",
                signal=SignalDirection.NEUTRAL,
                confidence=20,
                reasoning="All astro agents failed",
            )

        # Нормализуем голоса
        for sig in votes:
            votes[sig] /= total_weight

        # Итоговая уверенность: доля большинства × доступный вес
        raw_confidence = max(votes.values()) * min(100.0, total_weight * 100.0)
        confidence = max(10.0, min(95.0, raw_confidence))

        # Большинство > 40% И отрыв от второго > 15%
        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        if sorted_votes[0][1] > 0.4 and (sorted_votes[0][1] - sorted_votes[1][1]) > 0.10:
            final_signal = sorted_votes[0][0]
        else:
            final_signal = SignalDirection.NEUTRAL

        reasoning = " | ".join(reasons[:3])
        reasoning = f"[AstroCouncil] {final_signal.value} ({confidence:.0f}%) — {reasoning}"

        return AgentResponse(
            agent_name="AstroCouncil",
            signal=final_signal,
            confidence=confidence,
            reasoning=reasoning,
        )

"""CouncilOrchestrator — Agent → KARL → RiskEngine → Execution pipeline."""

import logging
from typing import List

from core.base_agent import AgentResponse, SignalDirection
from agents.karl_synthesis import resolve_conflict

logger = logging.getLogger(__name__)


class CouncilOrchestrator:
    """Замыкает контур: сбор сигналов → KARL-арбитраж → RiskEngine → исполнение.

    Поддерживает полный lifecycle агентов и пробрасывает метаданные HMM
    через всю цепочку принятия решений.
    """

    def __init__(self, risk_engine, config: dict | None = None):
        self.risk_engine = risk_engine
        self.config = config or {}

    def _apply_karl_arbitration(self, responses: List[AgentResponse]) -> List[AgentResponse]:
        """Применяет правила KARL к конфликтующим агентам (QuantAgent ↔ HMMRegimeAgent)."""
        quant_resp = next((r for r in responses if r.agent_name == "QuantAgent"), None)
        hmm_resp = next((r for r in responses if r.agent_name == "HMMRegimeAgent"), None)
        if quant_resp and hmm_resp:
            resolve_conflict(quant_resp, hmm_resp)
        return responses

    def adjust_through_risk(
        self,
        base_size: float,
        agent_responses: List[AgentResponse],
    ) -> tuple[float, str]:
        """Пропускает размер через RiskEngine.adjust_position_size().

        Returns:
            (adjusted_size, risk_reason). adjusted_size=0 означает STOP.
        """
        return self.risk_engine.adjust_position_size(
            base_size=base_size,
            agent_responses=agent_responses,
        )

    async def execute_trading_cycle(
        self,
        agent_responses: List[AgentResponse],
        final_signal: AgentResponse,
        config: dict | None = None,
    ) -> dict:
        """Полный торговый цикл: KARL → RiskEngine → validation → execution result.

        Args:
            agent_responses: сырые ответы всех агентов (включая HMM)
            final_signal: сигнал Astro-Council consensus
            config: переопределения конфига (base_position_size и т.д.)

        Returns:
            dict с ключами: action, size, risk_reason, blocked
        """
        cfg = {**self.config, **(config or {})}

        # 1. KARL arbitration
        processed = self._apply_karl_arbitration(agent_responses)

        # 2. RiskEngine wire-up
        base_size = cfg.get("base_position_size", 1.0)
        adjusted_size, risk_reason = self.adjust_through_risk(base_size, processed)

        # 3. STOP check (hard block)
        if adjusted_size <= 0.0:
            logger.warning("🛑 [RISK STOP] Trade blocked. Reason: %s", risk_reason)
            return {"action": "STOP", "size": 0.0, "risk_reason": risk_reason, "blocked": True}

        # 4. NEUTRAL check
        if final_signal.signal == SignalDirection.NEUTRAL:
            logger.info("Council consensus is NEUTRAL. No action.")
            return {"action": "NEUTRAL", "size": 0.0, "risk_reason": "consensus NEUTRAL", "blocked": False}

        # 5. Execution artifact (broker call site)
        logger.info(
            "✅ [EXECUTE] signal=%s size=%s risk=%s",
            final_signal.signal.name,
            adjusted_size,
            risk_reason,
        )
        return {
            "action": "EXECUTED",
            "size": adjusted_size,
            "signal": final_signal.signal.name,
            "risk_reason": risk_reason,
            "blocked": False,
        }

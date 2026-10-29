# ⚠️ DEAD MODULE (v1) — не используется live-путём run_sentinel_v5 / run_astro_council.
# Импортируется только scripts/backtest/tools/tests. Канон голосования astro:
# agents/astro_council_agent._weighted_vote + synthesis/voter; канон весов:
# agents/_impl/synthesis/weights.py. НЕ удалять — оставлен для будущего product-трека.

"""CouncilOrchestrator — Agent → KARL → RiskEngine → Execution pipeline."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import List

from core.base_agent import AgentResponse, SignalDirection
from agents.karl_synthesis import resolve_conflict

try:
    from utils.telegram_notifier import send_telegram_message
except ImportError:
    send_telegram_message = None  # Optional: not available in test/CI

logger = logging.getLogger(__name__)


from trading.factory import get_broker
from trading.broker.base import OrderSide, OrderType
from trading.safety_gate import SafetyGate


def compute_order_quantity(equity: float, position_fraction: float, price: float) -> float:
    """Order quantity in ASSET UNITS.

    qty = (equity × position_fraction) / price

    equity            — account equity in quote currency (e.g. USDT)
    position_fraction — share of equity to allocate after RiskEngine/SafetyGate (0..1)
    price             — current asset price in quote currency

    Raises ValueError on non-positive / non-finite inputs (caller must deny the trade).
    """
    import math

    for name, v in (("equity", equity), ("position_fraction", position_fraction), ("price", price)):
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v <= 0:
            raise ValueError(f"invalid {name}={v!r}")
    return round((equity * position_fraction) / price, 8)

class CouncilOrchestrator:
    """Замыкает контур: сбор сигналов → KARL-арбитраж → RiskEngine → исполнение.

    Поддерживает полный lifecycle агентов и пробрасывает метаданные HMM
    через всю цепочку принятия решений.
    """

    def __init__(self, risk_engine, config: dict | None = None, safety_gate: SafetyGate | None = None):
        self.risk_engine = risk_engine
        self.config = config or {}
        self.safety_gate = safety_gate or SafetyGate()

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
        is_backtest: bool = False,
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

            symbol = cfg.get("symbol", "UNKNOWN")
            alert_msg = (
                f"🛑 *RISK STOP BLOCKED TRADE*\n"
                f"Symbol: `{symbol}`\n"
                f"Reason: {risk_reason}\n"
                f"Time: {datetime.now(timezone.utc).isoformat()}"
            )
            if not is_backtest and send_telegram_message is not None:
                asyncio.create_task(send_telegram_message(alert_msg))

            return {
                "action": "STOP",
                "size": 0.0,
                "risk_reason": risk_reason,
                "blocked": True,
                "signal": final_signal.signal.name,
            }

        # 4. NEUTRAL check
        if final_signal.signal == SignalDirection.NEUTRAL:
            logger.info("Council consensus is NEUTRAL. No action.")
            return {
                "action": "NEUTRAL",
                "size": 0.0,
                "risk_reason": "consensus NEUTRAL",
                "blocked": False,
                "signal": final_signal.signal.name,
            }

        # 5. Execution — broker dispatch (Sprint 8.1 Paper Trading)
        #    Order reaches the broker ONLY after SafetyGate.check() approves it.
        symbol = cfg.get("symbol", "BTCUSDT")
        signal_name = final_signal.signal.name
        side = OrderSide.BUY if signal_name in ("LONG", "STRONG_BUY") else OrderSide.SELL

        def _deny(code: str, reason: str, status: str) -> dict:
            # status: REJECTED (policy violation) | BLOCKED (check impossible / error)
            logger.warning("🚫 [SAFETY %s] signal=%s code=%s reason=%s", status, signal_name, code, reason)
            return {
                "action": "DENIED",
                "status": status,
                "size": 0.0,
                "qty": 0.0,
                "signal": signal_name,
                "risk_reason": risk_reason,
                "blocked": True,
                "blocked_reason": code,
                "safety_reason": reason,
            }

        broker = get_broker()

        try:
            price = cfg.get("current_price")
            if price is None:
                price = broker.get_market_price(symbol)
            equity = cfg.get("equity")
            if equity is None:
                equity = broker.get_account_balance().total_equity
        except Exception as e:
            logger.exception("[EXECUTE] price/equity lookup failed — deny")
            return _deny("market_data_error", f"{type(e).__name__}", "BLOCKED")

        default_mode = "BACKTEST" if is_backtest else os.getenv("TRADING_MODE", "PAPER").upper()
        gate_state = {
            "trading_mode": cfg.get("trading_mode", default_mode),
            "signal": final_signal,
            "order_type": "market",
        }
        if isinstance(cfg.get("market"), dict):
            # Real market data for ExecutionSanityChecker (spread_bps, adv_24h_quote | volume_24h_base,
            # current_vol_regime, ...). Nothing is invented here: missing → gate BLOCKS.
            gate_state["market"] = cfg["market"]

        try:
            qty = compute_order_quantity(equity, adjusted_size, price)
        except ValueError as e:
            return _deny("invalid_quantity", str(e), "BLOCKED")

        decision = self.safety_gate.check(
            final_signal,
            gate_state,
            current_price=price,
            symbol=symbol,
            suggested_position_pct=adjusted_size,
            order_qty=qty,
        )
        if not (decision.is_approved or decision.is_reduced):
            status = decision.status.value if decision.status.value in ("REJECTED", "BLOCKED") else "BLOCKED"
            return _deny(decision.blocked_reason or "safety_denied", decision.reason, status)

        position_fraction = min(adjusted_size, decision.reduced_position_pct)
        try:
            qty = compute_order_quantity(equity, position_fraction, price)
        except ValueError as e:
            return _deny("invalid_quantity", str(e), "BLOCKED")
        scaled_from = None
        if decision.adjusted_qty is not None:
            if not (isinstance(decision.adjusted_qty, (int, float)) and decision.adjusted_qty > 0):
                return _deny("invalid_quantity", f"scaled qty={decision.adjusted_qty!r}", "BLOCKED")
            if decision.adjusted_qty < qty:
                scaled_from, qty = qty, round(decision.adjusted_qty, 8)
                logger.info("[EXECUTE] qty scaled by sanity: %s -> %s (%s)", scaled_from, qty, decision.reason)

        order = broker.place_order(symbol, side, OrderType.MARKET, qty)

        logger.info(
            "✅ [EXECUTE] signal=%s size=%s qty=%s price=%s risk=%s broker=%s status=%s",
            signal_name, adjusted_size, qty, price, risk_reason,
            broker.name, order.status.name,
        )

        return {
            "action": "EXECUTED",
            "status": decision.status.value,
            "size": adjusted_size,
            "qty": qty,
            "qty_scaled_from": scaled_from,
            "slippage_bps": decision.slippage_bps,
            "slippage_source": decision.slippage_source,
            "signal": signal_name,
            "risk_reason": risk_reason,
            "blocked": False,
            "safety_reason": decision.reason,
            "order_id": order.order_id,
            "order_status": order.status.name,
            "executed_price": order.avg_fill_price,
            "commission": order.commission,
            "broker": broker.name,
        }

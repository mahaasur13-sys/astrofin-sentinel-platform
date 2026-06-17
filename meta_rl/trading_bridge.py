META_RL_TRADING_ENABLED = False  # F821 fix (TODO: move to config)
"""meta_rl/trading_bridge.py — Live/Paper Trading Bridge for Meta-RL"""

import logging
from dataclasses import dataclass

from meta_rl.config import (
    LIVE_TRADING_ENABLED,
    PAPER_TRADING_ENABLED,
)
from trading.execution.sanity import ExecutionSanityChecker
from trading.mode import ModeEnforcer
from trading.risk_v2 import RiskEngineV2

logger = logging.getLogger(__name__)


@dataclass
class TradingExecutionResult:
    status: str  # APPROVED / REDUCED / REJECTED / ERROR / DISABLED
    reason: str
    adjusted_signal: dict | None = None
    order_id: str | None = None


class MetaRLTradingBridge:
    def __init__(self):
        self.mode_enforcer = ModeEnforcer()
        self.risk_engine = RiskEngineV2()
        self.sanity_checker = ExecutionSanityChecker()

    def execute(self, strategy, market_data: dict, mode: str = "PAPER") -> TradingExecutionResult:
        if not META_RL_TRADING_ENABLED:
            logger.warning("[META-RL-TRADING] Bridge disabled by feature flag")
            return TradingExecutionResult(status="DISABLED", reason="Bridge disabled")
        if mode == "LIVE" and not LIVE_TRADING_ENABLED:
            logger.warning("[META-RL-TRADING] LIVE trading not enabled")
            return TradingExecutionResult(status="DISABLED", reason="LIVE trading not enabled")
        if mode == "PAPER" and not PAPER_TRADING_ENABLED:
            logger.warning("[META-RL-TRADING] PAPER trading not enabled")
            return TradingExecutionResult(status="DISABLED", reason="PAPER not enabled")
        try:
            # 1) Mode gate
            mode_result = self.mode_enforcer.apply(market_data)
            if not mode_result.get("allowed", True):
                return TradingExecutionResult(
                    status="REJECTED",
                    reason=mode_result.get("reason", "Mode gate rejected"),
                )
            # 2) Pre-trade risk
            risk_pre = self.risk_engine.pre_trade_check(strategy, market_data)
            if not risk_pre.get("approved", True):
                return TradingExecutionResult(status="REJECTED", reason=risk_pre.get("reason", "Risk rejected"))
            # 3) Build order request
            order_req = {
                "symbol": market_data.get("symbol", "BTCUSDT"),
                "direction": risk_pre.get("signal", "NEUTRAL"),
                "size_pct": risk_pre.get("adjusted_size_pct", 0.02),
                "order_type": "MARKET",
                "mode": mode,
            }
            # 4) Execution sanity
            sanity = self.sanity_checker.validate(order_req, market_data)
            if not sanity.get("passed", True):
                return TradingExecutionResult(
                    status="REJECTED",
                    reason=sanity.get("reason", "Sanity check failed"),
                )
            # 5) Log
            logger.info(
                f"[META-RL-TRADING] {mode} approved: {order_req['symbol']} signal={order_req['direction']} size={order_req['size_pct']:.2%}"
            )
            return TradingExecutionResult(status="APPROVED", reason=f"{mode} approved", adjusted_signal=order_req)
        except Exception as e:
            logger.error(f"[META-RL-TRADING] Execution failed: {e}")
            return TradingExecutionResult(status="ERROR", reason=str(e))


_bridge = None


def get_bridge():
    global _bridge
    if _bridge is None:
        _bridge = MetaRLTradingBridge()
    return _bridge

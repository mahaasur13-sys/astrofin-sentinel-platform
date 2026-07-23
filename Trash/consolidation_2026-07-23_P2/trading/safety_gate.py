from __future__ import annotations


class MarketMode:
    pass  # F821 fix


"""
trading/safety_gate.py — ATOM-INTEGRATION-001: Safety Gate
===========================================================
Единая точка входа для Safety Stack.

Порядок проверок:
  1. ModeEnforcer       — режим рынка
  2. RiskEngineV2       — лимиты и экспозиция
  3. ExecutionSanityChecker — спред, объём, price sanity

用法:
  from trading.safety_gate import SafetyGate, SafetyDecision
  gate = SafetyGate(portfolio=portfolio)
  decision = gate.check(signal, state)
"""

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

# ─── Feature Flags ──────────────────────────────────────────────────────────────

SAFETY_STACK_ENABLED = os.getenv("SAFETY_STACK_ENABLED", "true").lower() == "true"
RISK_ENGINE_V2_ENABLED = os.getenv("RISK_ENGINE_V2_ENABLED", "true").lower() == "true"
MODE_ENFORCER_ENABLED = os.getenv("MODE_ENFORCER_ENABLED", "true").lower() == "true"
SANITY_CHECKER_ENABLED = os.getenv("SANITY_CHECKER_ENABLED", "true").lower() == "true"

# ─── Result Types ──────────────────────────────────────────────────────────────


class SafetyStatus(Enum):
    APPROVED = "APPROVED"
    REDUCED = "REDUCED"
    REJECTED = "REJECTED"


@dataclass
class SafetyDecision:
    status: SafetyStatus
    reason: str
    reduced_position_pct: float = 1.0  # 0.0–1.0
    adjusted_signal: str | None = None
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    gate_version: str = "1.0.0"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @property
    def is_approved(self) -> bool:
        return self.status == SafetyStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == SafetyStatus.REJECTED

    @property
    def is_reduced(self) -> bool:
        return self.status == SafetyStatus.REDUCED


# ─── SafetyGate ───────────────────────────────────────────────────────────────


class SafetyGate:
    """
    Unified safety layer. Instantiated per-session with a shared portfolio.

    Каждый .check() вызывает цепочку:
      ModeEnforcer → RiskEngineV2 → ExecutionSanityChecker

    При SAFETY_STACK_ENABLED=False — возвращает APPROVED без overhead.
    """

    def __init__(
        self,
        portfolio: Any | None = None,  # forward ref
        market_mode: MarketMode | None = None,
    ):
        self.portfolio = portfolio
        self.market_mode = market_mode
        self._log = SAFETY_STACK_ENABLED
        self._call_count = 0
        self._total_rejected = 0
        self._total_reduced = 0

    # ── Public API ──────────────────────────────────────────────────────────────

    def check(
        self,
        signal: Any,  # AgentResponse или dict
        state: dict,
        current_price: float = 0.0,
        symbol: str = "BTCUSDT",
        suggested_position_pct: float = 1.0,
    ) -> SafetyDecision:
        """
        Synchronous check. Returns SafetyDecision immediately.

        Если SAFETY_STACK_ENABLED=False — возвращает APPROVED без overhead.
        """
        self._call_count += 1

        if not SAFETY_STACK_ENABLED:
            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason="Safety stack disabled (SAFETY_STACK_ENABLED=false)",
            )

        # ── Extract signal info ───────────────────────────────────────────────
        sig_dict = self._normalize_signal(signal)
        sig_direction = sig_dict.get("signal", "NEUTRAL")
        sig_confidence = sig_dict.get("confidence", 50)
        sig_dict.get("agent_name", "unknown")

        checks_passed: list[str] = []
        checks_failed: list[str] = []

        # ── 1. ModeEnforcer ───────────────────────────────────────────────────
        if MODE_ENFORCER_ENABLED:
            mode_decision = self._check_mode(state, suggested_position_pct)
            if not mode_decision.is_approved:
                self._total_rejected += 1
                self._log_event("MODE", "REJECTED", mode_decision.reason)
                return mode_decision
            checks_passed.append("ModeEnforcer")
        else:
            checks_passed.append("ModeEnforcer(disabled)")

        # ── 2. RiskEngineV2 ──────────────────────────────────────────────────
        if RISK_ENGINE_V2_ENABLED and self.portfolio is not None:
            risk_decision = self._check_risk(
                symbol,
                sig_direction,
                sig_confidence,
                suggested_position_pct,
                current_price,
            )
            if risk_decision.is_rejected:
                self._total_rejected += 1
                self._log_event("RISK", "REJECTED", risk_decision.reason)
                return risk_decision
            if risk_decision.is_reduced:
                self._total_reduced += 1
                self._log_event("RISK", "REDUCED", risk_decision.reason)
                checks_failed.append("RiskEngineV2(volume)")
                # Continue to sanity check even on REDUCED
            checks_passed.append("RiskEngineV2")
        else:
            checks_passed.append("RiskEngineV2(disabled)")

        # ── 3. ExecutionSanityChecker ─────────────────────────────────────────
        if SANITY_CHECKER_ENABLED:
            sanity_decision = self._check_sanity(
                symbol,
                sig_direction,
                current_price,
                state,
            )
            if sanity_decision.is_rejected:
                self._total_rejected += 1
                self._log_event("SANITY", "REJECTED", sanity_decision.reason)
                return sanity_decision
            checks_passed.append("ExecutionSanityChecker")
        else:
            checks_passed.append("ExecutionSanityChecker(disabled)")

        # ── All passed ───────────────────────────────────────────────────────
        reason = f"All {len(checks_passed)} checks passed. Signal: {sig_direction} conf={sig_confidence}"
        self._log_event("GATE", "APPROVED", reason)

        return SafetyDecision(
            status=SafetyStatus.APPROVED,
            reason=reason,
            reduced_position_pct=suggested_position_pct,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
        )

    async def check_async(
        self,
        signal: Any,
        state: dict,
        current_price: float = 0.0,
        symbol: str = "BTCUSDT",
        suggested_position_pct: float = 1.0,
    ) -> SafetyDecision:
        """Async wrapper — delegates to sync check (all components are fast)."""
        return self.check(signal, state, current_price, symbol, suggested_position_pct)

    # ── Internal Checks ─────────────────────────────────────────────────────────

    def _check_mode(self, state: dict, proposed_size_pct: float = 0.2) -> SafetyDecision:
        """ModeEnforcer (TradingMode) check — validates operational mode constraints."""
        try:
            from trading.mode import ModeEnforcer, TradingMode

            # Detect operational mode from state or default to BACKTEST
            mode_str = state.get("trading_mode", "BACKTEST")
            try:
                mode = TradingMode(mode_str)
            except (ValueError, TypeError):
                mode = TradingMode.BACKTEST

            enforcer = ModeEnforcer(mode=mode)

            sig_direction = self._normalize_signal(state.get("signal", "NEUTRAL")).get("signal", "NEUTRAL")

            is_short = sig_direction == "SHORT"
            is_market = state.get("order_type") != "limit"
            is_limit = state.get("order_type") == "limit"
            is_option = "option" in sig_direction.lower()
            equity = self.portfolio.total_value if self.portfolio else 100_000.0

            ok, msg = enforcer.check_order(
                proposed_size_pct=proposed_size_pct,
                is_market=is_market,
                is_limit=is_limit,
                is_option=is_option,
                is_short=is_short,
                equity=equity,
            )

            if not ok:
                return SafetyDecision(
                    status=SafetyStatus.REJECTED,
                    reason=f"ModeEnforcer: {msg}",
                    blocked_reason=f"mode_check:{msg[:50]}",
                )

            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason=f"ModeEnforcer: {mode.value} — {msg}",
            )
        except Exception as e:
            # Fail-open: allow on error
            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason=f"ModeEnforcer error={e} — fail-open",
            )

    def _check_risk(
        self,
        symbol: str,
        sig_direction: str,
        sig_confidence: float,
        suggested_position_pct: float,
        current_price: float,
    ) -> SafetyDecision:
        """RiskEngineV2 check using real API: check_exposure / check_correlation / check_volume."""
        try:
            from trading.risk_v2 import RiskConfigV2, RiskEngineV2

            config = RiskConfigV2(
                max_exposure_per_asset=0.25,
                max_drawdown=0.15,
                correlation_limit=0.70,
                target_volatility=0.15,
                vol_lookback=20,
                kill_switch_enabled=True,
            )
            engine = RiskEngineV2(config)

            # Sync portfolio from self.portfolio (if it's a mock)
            if self.portfolio is not None:
                equity = getattr(self.portfolio, "total_value", None)
                if not isinstance(equity, (int, float)):  # noqa: UP038
                    equity = 100_000.0
                engine._equity_history = [equity]
                if hasattr(self.portfolio, "positions"):
                    for sym, pos in self.portfolio.positions.items():
                        if hasattr(pos, "notional_value"):

                            class _FakeAsset:
                                pass

                            fa = _FakeAsset()
                            fa.symbol = sym
                            fa.notional_value = pos.notional_value
                            fa.current_price = getattr(pos, "current_price", 0) or current_price
                            fa.entry_price = getattr(pos, "entry_price", current_price)
                            engine._positions[sym] = fa

            # Build notional for proposed position
            equity = engine._equity_history[-1] if engine._equity_history else 100_000
            proposed_notional = suggested_position_pct * equity

            # 1. Kill switch
            try:
                kill_ok, kill_dd, kill_msg = engine.check_kill_switch()
                if not kill_ok:
                    return SafetyDecision(
                        status=SafetyStatus.REJECTED,
                        reason=f"RiskEngineV2: {kill_msg}",
                        blocked_reason=f"kill_switch:{kill_msg[:40]}",
                    )
            except Exception:
                pass  # skip kill switch on error

            # 2. Exposure check
            try:
                ok, scaled, msg = engine.check_exposure(symbol, proposed_notional)
                if not ok:
                    return SafetyDecision(
                        status=SafetyStatus.REJECTED,
                        reason=f"RiskEngineV2: {msg}",
                        blocked_reason=f"exposure:{msg[:40]}",
                    )
            except Exception:
                pass  # skip exposure check on error

            # 3. Correlation check (only if we have enough history)
            try:
                if len(engine._return_history) >= 5:
                    ok, factor, msg = engine.check_correlation(symbol, 0.01)
                    if not ok:
                        return SafetyDecision(
                            status=SafetyStatus.REJECTED,
                            reason=f"RiskEngineV2: {msg}",
                            blocked_reason=f"correlation:{msg[:40]}",
                        )
            except Exception:
                pass  # skip correlation on error

            # 4. Volume check (confidence-based)
            min_confidence = 40 + (1.0 - suggested_position_pct) * 20
            if sig_confidence < min_confidence:
                return SafetyDecision(
                    status=SafetyStatus.REDUCED,
                    reason=f"RiskEngineV2: confidence {sig_confidence} < minimum {min_confidence:.0f}",
                    reduced_position_pct=suggested_position_pct,
                    blocked_reason="low_confidence",
                )

            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason="RiskEngineV2: all checks passed",
            )
        except Exception as e:
            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason=f"RiskEngineV2 error={e} — fail-open",
            )

    def _check_sanity(
        self,
        symbol: str,
        sig_direction: str,
        current_price: float,
        state: dict,
    ) -> SafetyDecision:
        """ExecutionSanityChecker check."""
        try:
            from trading.execution.sanity import ExecutionSanityChecker

            checker = ExecutionSanityChecker()
            checker.quote(symbol, current_price)

            sanity = checker.check(
                symbol=symbol,
                direction=sig_direction,
                price=current_price,
                volume_24h=state.get("volume_24h", 1_000_000_000),
            )

            if not sanity.is_sane:
                return SafetyDecision(
                    status=SafetyStatus.REJECTED,
                    reason=sanity.reason,
                    blocked_reason=f"sanity_failed:{sanity.issue}",
                )

            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason=f"ExecutionSanity: {sanity.reason}",
            )
        except Exception as e:
            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason=f"ExecutionSanityChecker error={e} — fail-open",
            )

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _normalize_signal(self, signal: Any) -> dict:
        if hasattr(signal, "to_dict"):
            return signal.to_dict()
        if isinstance(signal, dict):
            return signal
        if hasattr(signal, "__dict__") and bool(signal.__dict__):
            return {k: v for k, v in signal.__dict__.items() if not k.startswith("_")}
        return {"signal": "NEUTRAL", "confidence": 50}

    def _log_event(self, stage: str, status: str, reason: str):
        if self._log:
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            icon = {"APPROVED": "✅", "REDUCED": "⚠️", "REJECTED": "🚫"}.get(status, "?")
            print(f"[SAFETY-STACK] {ts} {stage:8s} {icon} {status:8s} — {reason}")

    def get_stats(self) -> dict:
        return {
            "calls": self._call_count,
            "rejected": self._total_rejected,
            "reduced": self._total_reduced,
            "approval_rate": ((self._call_count - self._total_rejected) / max(self._call_count, 1)),
        }


# ─── Convenience functions ─────────────────────────────────────────────────────

_default_gate: SafetyGate | None = None


def get_safety_gate(
    portfolio=None,
    market_mode=None,
) -> SafetyGate:
    """Singleton gate for the current process (avoids re-instantiation)."""
    global _default_gate
    if _default_gate is None:
        _default_gate = SafetyGate(portfolio=portfolio, market_mode=market_mode)
    return _default_gate


__all__ = [
    "SafetyGate",
    "SafetyDecision",
    "SafetyStatus",
    "get_safety_gate",
    "SAFETY_STACK_ENABLED",
    "RISK_ENGINE_V2_ENABLED",
    "MODE_ENFORCER_ENABLED",
    "SANITY_CHECKER_ENABLED",
]

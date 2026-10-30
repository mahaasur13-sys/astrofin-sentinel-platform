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

import logging
import math
log = logging.getLogger(__name__)

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

# Fraction of the suggested position kept when RiskEngineV2 returns REDUCED
# (low confidence). Conservative default: half size. Override with
# RISK_REDUCED_POSITION_FACTOR in (0, 1]; anything else falls back to the
# default so a bad value can never keep or increase the size.
DEFAULT_REDUCED_POSITION_FACTOR = 0.5


def reduced_position_factor() -> float:
    raw = os.getenv("RISK_REDUCED_POSITION_FACTOR")
    if raw is None or raw.strip() == "":
        return DEFAULT_REDUCED_POSITION_FACTOR
    try:
        value = float(raw)
    except ValueError:
        value = float("nan")
    if not math.isfinite(value) or not (0.0 < value < 1.0):
        log.warning("[SAFETY-STACK] invalid RISK_REDUCED_POSITION_FACTOR — using %s", DEFAULT_REDUCED_POSITION_FACTOR)
        return DEFAULT_REDUCED_POSITION_FACTOR
    return value

# ─── Result Types ──────────────────────────────────────────────────────────────


class SafetyStatus(Enum):
    APPROVED = "APPROVED"
    REDUCED = "REDUCED"
    REJECTED = "REJECTED"  # policy violation on valid data (mode/kill switch/exposure/sanity)
    BLOCKED = "BLOCKED"  # check could not be performed (error / missing data) — fail-closed


@dataclass
class SafetyDecision:
    status: SafetyStatus
    reason: str
    reduced_position_pct: float = 1.0  # 0.0–1.0
    adjusted_signal: str | None = None
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    adjusted_qty: float | None = None  # set when sanity SCALED the order (asset units)
    slippage_bps: float | None = None  # slippage estimate used by sanity
    slippage_source: str | None = None  # 'market' (provided) | 'model' (SlippageModel)
    gate_version: str = "1.1.0"

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

    @property
    def is_blocked(self) -> bool:
        return self.status == SafetyStatus.BLOCKED

    @property
    def is_denied(self) -> bool:
        """REJECTED or BLOCKED — execution must stop, no order."""
        return self.status in (SafetyStatus.REJECTED, SafetyStatus.BLOCKED)


def _blocked(reason: str, code: str) -> SafetyDecision:
    return SafetyDecision(status=SafetyStatus.BLOCKED, reason=reason, blocked_reason=code)


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
        portfolio: Optional[Any] = None,  # forward ref
        market_mode: Optional["MarketMode"] = None,
        slippage_model: Optional[Any] = None,
    ):
        self.portfolio = portfolio
        # Used when market data has no slippage_bp_estimate. None → SlippageModel
        # (trading/execution/slippage.py) with its configured slippage_bps and the
        # REAL spread_bps from market data.
        self.slippage_model = slippage_model
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
        order_qty: float | None = None,
    ) -> SafetyDecision:
        """
        Synchronous check. Returns SafetyDecision immediately.

        Если SAFETY_STACK_ENABLED=False — возвращает APPROVED без overhead.

        Fail-closed: любое исключение внутри проверки → BLOCKED (safety_gate_error).
        REJECTED — нарушение политики; BLOCKED — проверку выполнить не удалось.
        Оба статуса останавливают исполнение.
        """
        self._call_count += 1
        try:
            return self._check_impl(signal, state, current_price, symbol, suggested_position_pct, order_qty)
        except Exception as e:
            log.exception("[SAFETY-STACK] check() failed — fail-closed BLOCK")
            self._total_rejected += 1
            return _blocked(f"SafetyGate error={type(e).__name__} — fail-closed", "safety_gate_error")

    def _check_impl(
        self,
        signal: Any,
        state: dict,
        current_price: float,
        symbol: str,
        suggested_position_pct: float,
        order_qty: float | None = None,
    ) -> SafetyDecision:

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
        scaled_qty: float | None = None
        scaled_reason = ""
        risk_reduced: SafetyDecision | None = None
        sanity_slippage: tuple[float | None, str | None] = (None, None)

        # ── 1. ModeEnforcer ───────────────────────────────────────────────────
        if MODE_ENFORCER_ENABLED:
            mode_decision = self._check_mode(state, suggested_position_pct)
            if not mode_decision.is_approved:
                self._total_rejected += 1
                self._log_event("MODE", mode_decision.status.value, mode_decision.reason)
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
            if risk_decision.is_denied:
                self._total_rejected += 1
                self._log_event("RISK", risk_decision.status.value, risk_decision.reason)
                return risk_decision
            if risk_decision.is_reduced:
                self._total_reduced += 1
                self._log_event("RISK", "REDUCED", risk_decision.reason)
                checks_failed.append("RiskEngineV2(volume)")
                risk_reduced = risk_decision
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
                order_qty=order_qty,
                suggested_position_pct=suggested_position_pct,
            )
            if sanity_decision.is_denied:
                self._total_rejected += 1
                self._log_event("SANITY", sanity_decision.status.value, sanity_decision.reason)
                return sanity_decision
            sanity_slippage = (sanity_decision.slippage_bps, sanity_decision.slippage_source)
            if sanity_decision.is_reduced:
                self._total_reduced += 1
                self._log_event("SANITY", "REDUCED", sanity_decision.reason)
                checks_failed.append("ExecutionSanityChecker(scaled)")
                scaled_qty = sanity_decision.adjusted_qty
                scaled_reason = sanity_decision.reason
            checks_passed.append("ExecutionSanityChecker")
        else:
            checks_passed.append("ExecutionSanityChecker(disabled)")

        # ── All passed ───────────────────────────────────────────────────────
        final_pct = suggested_position_pct
        if risk_reduced is not None:
            # Never larger than suggested, even if the risk decision is odd.
            final_pct = min(suggested_position_pct, risk_reduced.reduced_position_pct)
        if scaled_qty is not None or risk_reduced is not None:
            reasons = [r for r in (risk_reduced.reason if risk_reduced else "", scaled_reason) if r]
            codes = [c for c in (risk_reduced.blocked_reason if risk_reduced else None,
                                 "sanity_scaled" if scaled_qty is not None else None) if c]
            self._log_event("GATE", "REDUCED", "; ".join(reasons))
            return SafetyDecision(
                status=SafetyStatus.REDUCED,
                reason=f"{len(checks_passed)} checks passed; {'; '.join(reasons)}",
                reduced_position_pct=final_pct,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                blocked_reason=",".join(codes),
                adjusted_qty=scaled_qty,
                slippage_bps=sanity_slippage[0],
                slippage_source=sanity_slippage[1],
            )
        reason = f"All {len(checks_passed)} checks passed. Signal: {sig_direction} conf={sig_confidence}"
        self._log_event("GATE", "APPROVED", reason)

        return SafetyDecision(
            status=SafetyStatus.APPROVED,
            reason=reason,
            reduced_position_pct=suggested_position_pct,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            slippage_bps=sanity_slippage[0],
            slippage_source=sanity_slippage[1],
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
        return self.check(signal, state, current_price, symbol, suggested_position_pct)  # order_qty: sync API

    # ── Internal Checks ─────────────────────────────────────────────────────────

    def _check_mode(
        self, state: dict, proposed_size_pct: float = 0.2
    ) -> SafetyDecision:
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

            sig_direction = self._normalize_signal(state.get("signal", "NEUTRAL")).get(
                "signal", "NEUTRAL"
            )

            is_short = str(getattr(sig_direction, "value", sig_direction)).upper() in (
                "SHORT", "SELL", "STRONG_SELL"
            )
            is_market = state.get("order_type") != "limit"
            is_limit = state.get("order_type") == "limit"
            is_option = "option" in sig_direction.lower()
            # Same equity resolution as _check_risk: portfolio may be any object
            # (e.g. RiskEngineV2) without a numeric total_value.
            equity = getattr(self.portfolio, "total_value", None) if self.portfolio else None
            if not isinstance(equity, (int, float)):  # noqa: UP038
                equity = 100_000.0

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
            # Fail-closed: deny on error
            log.exception("[SAFETY-STACK] ModeEnforcer check failed — fail-closed BLOCK")
            return _blocked(
                f"ModeEnforcer error={type(e).__name__} — fail-closed",
                "mode_check_error",
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
                            fa.current_price = (
                                getattr(pos, "current_price", 0) or current_price
                            )
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
            except Exception as e:
                log.exception("[SAFETY-STACK] kill switch check failed — fail-closed BLOCK")
                return _blocked(
                    f"RiskEngineV2: kill switch check error={type(e).__name__} — fail-closed",
                    "kill_switch_error",
                )

            # 2. Exposure check
            try:
                ok, scaled, msg = engine.check_exposure(symbol, proposed_notional)
                if not ok:
                    return SafetyDecision(
                        status=SafetyStatus.REJECTED,
                        reason=f"RiskEngineV2: {msg}",
                        blocked_reason=f"exposure:{msg[:40]}",
                    )
            except Exception as e:
                log.exception("[SAFETY-STACK] exposure check failed — fail-closed BLOCK")
                return _blocked(
                    f"RiskEngineV2: exposure check error={type(e).__name__} — fail-closed",
                    "exposure_error",
                )

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
            except Exception as e:
                log.exception("[SAFETY-STACK] correlation check failed — fail-closed BLOCK")
                return _blocked(
                    f"RiskEngineV2: correlation check error={type(e).__name__} — fail-closed",
                    "correlation_error",
                )

            # 4. Volume check (confidence-based)
            min_confidence = 40 + (1.0 - suggested_position_pct) * 20
            if sig_confidence < min_confidence:
                return SafetyDecision(
                    status=SafetyStatus.REDUCED,
                    reason=f"RiskEngineV2: confidence {sig_confidence} < minimum {min_confidence:.0f}",
                    reduced_position_pct=suggested_position_pct * reduced_position_factor(),
                    blocked_reason="low_confidence",
                )

            return SafetyDecision(
                status=SafetyStatus.APPROVED,
                reason="RiskEngineV2: all checks passed",
            )
        except Exception as e:
            log.exception("[SAFETY-STACK] RiskEngineV2 check failed — fail-closed BLOCK")
            return _blocked(
                f"RiskEngineV2 error={type(e).__name__} — fail-closed",
                "risk_check_error",
            )

    # Required real market inputs for ExecutionSanityChecker.validate().
    # Values are NEVER invented: a missing field → BLOCKED sanity_missing_data:<fields>.
    SANITY_REQUIRED_FIELDS = ("last_price", "spread_bps", "adv_24h", "current_vol_regime", "order_qty")

    @staticmethod
    def _finite_pos(v: Any) -> bool:
        import math

        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0

    def _build_market_state(self, symbol: str, current_price: float, market: dict) -> tuple[Any, list[str]]:
        """Build MarketState from provided data only. Returns (MarketState|None, missing_fields).

        market keys (all real, caller-provided):
          last_price            — else current_price argument if > 0
          spread_bps            — else computed from bid_price/ask_price if both given
          adv_24h_quote         — 24h volume in QUOTE currency (e.g. USDT)
          volume_24h_base       — 24h volume in BASE currency → × last_price
          current_vol_regime    — LOW | NORMAL | HIGH | EXTREME
          bid_price, ask_price, realized_vol_20d — optional (NaN if unknown; validate() does not read them)
        """
        import math

        from trading.execution.sanity import MarketState

        missing: list[str] = []
        last_price = market.get("last_price")
        if not self._finite_pos(last_price) and self._finite_pos(current_price):
            last_price = current_price
        if not self._finite_pos(last_price):
            missing.append("last_price")

        bid, ask = market.get("bid_price"), market.get("ask_price")
        spread_bps = market.get("spread_bps")
        if spread_bps is None and self._finite_pos(bid) and self._finite_pos(ask) and ask >= bid:
            spread_bps = (ask - bid) / ((ask + bid) / 2) * 10_000
        if not (isinstance(spread_bps, (int, float)) and math.isfinite(spread_bps) and spread_bps >= 0):
            missing.append("spread_bps")

        adv = market.get("adv_24h_quote")
        if adv is None and market.get("volume_24h_base") is not None and self._finite_pos(last_price):
            base = market.get("volume_24h_base")
            adv = base * last_price if self._finite_pos(base) else None
        if not self._finite_pos(adv):
            missing.append("adv_24h")

        regime = market.get("current_vol_regime")
        if regime not in ("LOW", "NORMAL", "HIGH", "EXTREME"):
            missing.append("current_vol_regime")

        if missing:
            return None, missing
        nan = float("nan")
        return (
            MarketState(
                symbol=symbol,
                last_price=float(last_price),
                bid_price=float(bid) if self._finite_pos(bid) else nan,
                ask_price=float(ask) if self._finite_pos(ask) else nan,
                spread_bps=float(spread_bps),
                adv_24h=float(adv),
                realized_vol_20d=float(market.get("realized_vol_20d", nan)),
                current_vol_regime=regime,
            ),
            [],
        )

    def _resolve_order_qty(self, order_qty: float | None, suggested_position_pct: float, price: float) -> float | None:
        if self._finite_pos(order_qty):
            return float(order_qty)
        equity = getattr(self.portfolio, "total_value", None) if self.portfolio is not None else None
        if self._finite_pos(equity) and self._finite_pos(suggested_position_pct) and self._finite_pos(price):
            return equity * suggested_position_pct / price
        return None

    def _estimate_slippage(self, market: dict, market_state: Any, side: str, qty: float) -> tuple[float | None, str]:
        """Return (slippage_bps, source). source: 'market' | 'model'. None → cannot estimate."""
        import math

        provided = market.get("slippage_bp_estimate")
        if provided is not None:
            ok = isinstance(provided, (int, float)) and not isinstance(provided, bool) and math.isfinite(provided)
            return (float(provided) if ok and provided >= 0 else None), "market"
        try:
            from trading.execution.slippage import SlippageModel

            model = self.slippage_model or SlippageModel(spread_bps=market_state.spread_bps)
            res = model.calculate(side.lower(), qty, market_state.last_price)
            bps = getattr(res, "slippage_bps", None)
            if isinstance(bps, (int, float)) and math.isfinite(bps) and bps >= 0:
                return float(bps), "model"
        except Exception:
            log.exception("[SAFETY-STACK] SlippageModel failed")
        return None, "model"

    def _check_sanity(
        self,
        symbol: str,
        sig_direction: str,
        current_price: float,
        state: dict,
        order_qty: float | None = None,
        suggested_position_pct: float = 1.0,
    ) -> SafetyDecision:
        """ExecutionSanityChecker.validate(OrderRequest, MarketState) on real provided data."""
        try:
            from trading.execution.sanity import ExecutionSanityChecker, OrderRequest, ValidationStatus

            market = state.get("market") or {}
            if not isinstance(market, dict):
                market = {}
            market_state, missing = self._build_market_state(symbol, current_price, market)
            if market_state is not None:
                price = market_state.last_price
            elif self._finite_pos(market.get("last_price")):
                price = market["last_price"]
            else:
                price = current_price if self._finite_pos(current_price) else None
            qty = self._resolve_order_qty(order_qty, suggested_position_pct, price) if price else None
            if qty is None and "last_price" not in missing:
                missing.append("order_qty")
            if missing:
                fields = ",".join(missing)
                return _blocked(f"ExecutionSanity: missing market data: {fields}", f"sanity_missing_data:{fields}")

            side = "SELL" if str(sig_direction).upper() in ("SHORT", "SELL", "STRONG_SELL") else "BUY"
            slip_bps, slip_src = self._estimate_slippage(market, market_state, side, qty)
            if slip_bps is None:
                d = _blocked(f"ExecutionSanity: no slippage estimate (source={slip_src})", "sanity_missing_data:slippage")
                d.slippage_source = slip_src
                return d
            extra = {"slippage_bps": slip_bps, "slippage_source": slip_src}
            order = OrderRequest(
                symbol=symbol,
                side=side,
                qty=qty,
                price=market_state.last_price,
                order_type=str(state.get("order_type", "market")).upper(),
                slippage_bp_estimate=slip_bps,
            )
            result = ExecutionSanityChecker().validate(order, market_state)

            if result.status == ValidationStatus.REJECTED:
                code = result.reason.split(":", 1)[0]
                return SafetyDecision(
                    status=SafetyStatus.REJECTED,
                    reason=f"ExecutionSanity: {result.reason}",
                    blocked_reason=f"sanity_failed:{code}",
                    **extra,
                )
            if result.status == ValidationStatus.SCALED:
                return SafetyDecision(
                    status=SafetyStatus.REDUCED,
                    reason=f"ExecutionSanity: {result.reason} qty {qty:.8f}->{result.adjusted_qty:.8f}",
                    blocked_reason="sanity_scaled",
                    adjusted_qty=result.adjusted_qty,
                    **extra,
                )
            return SafetyDecision(status=SafetyStatus.APPROVED, reason=f"ExecutionSanity: {result.reason}", **extra)
        except Exception as e:
            log.exception("[SAFETY-STACK] ExecutionSanityChecker failed — fail-closed BLOCK")
            return _blocked(f"ExecutionSanityChecker error={type(e).__name__} — fail-closed", "sanity_check_error")

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
            icon = {"APPROVED": "✅", "REDUCED": "⚠️", "REJECTED": "🚫", "BLOCKED": "⛔"}.get(
                status, "?"
            )
            log.info(f"[SAFETY-STACK] {ts} {stage:8s} {icon} {status:8s} — {reason}")

    def get_stats(self) -> dict:
        return {
            "calls": self._call_count,
            "rejected": self._total_rejected,
            "reduced": self._total_reduced,
            "approval_rate": (
                (self._call_count - self._total_rejected) / max(self._call_count, 1)
            ),
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

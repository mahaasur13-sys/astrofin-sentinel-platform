"""trading/risk_v2.py — ATOM-PRODUCTION: Risk Engine V2
==============================================================
Production-grade risk management with:
  - Drawdown kill switch
  - Exposure control per asset
  - Correlation limit
  - Volatility targeting (Kelly-inspired)
  - Position size clamping
  - Full NaN protection
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class RiskConfigV2:
    max_drawdown: float = 0.10
    max_exposure_per_asset: float = 0.30
    correlation_limit: float = 0.80
    target_volatility: float = 0.15
    vol_lookback: int = 20
    kill_switch_enabled: bool = True
    close_on_kill: bool = True

    def __post_init__(self):
        assert 0 < self.max_drawdown <= 1.0, f"max_drawdown={self.max_drawdown} out of range"
        assert 0 < self.max_exposure_per_asset <= 1.0
        assert 0 < self.correlation_limit <= 1.0
        assert self.target_volatility > 0


@dataclass
class AssetPosition:
    symbol: str
    notional_value: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_volatility: float = 0.0


@dataclass
class RiskState:
    total_equity: float
    cash: float
    peak_equity: float
    current_drawdown: float
    kill_switch_active: bool = False


class RiskEngineV2:
    def __init__(self, config: RiskConfigV2 | None = None):
        self.config = config or RiskConfigV2()
        self._positions: dict = {}
        self._equity_history: list = []
        self._return_history: list = []

    def update_position(self, pos: AssetPosition) -> None:
        pos.unrealized_pnl = pos.notional_value - pos.entry_price * abs(pos.notional_value) / max(pos.current_price, 1e-10)
        self._positions[pos.symbol] = pos

    def update_equity(self, equity: float) -> None:
        equity = float(equity)
        if math.isnan(equity) or math.isinf(equity):
            equity = self._equity_history[-1] if self._equity_history else 100_000.0
        self._equity_history.append(equity)

    def get_state(self) -> RiskState:
        equity = self._equity_history[-1] if self._equity_history else 100_000.0
        peak = max(self._equity_history) if self._equity_history else equity
        dd = max(0.0, (peak - equity) / peak) if peak > 0 else 0.0
        kill = dd >= self.config.max_drawdown if self.config.kill_switch_enabled else False
        return RiskState(
            total_equity=equity,
            cash=equity,
            peak_equity=peak,
            current_drawdown=dd,
            kill_switch_active=kill,
        )

    def check_kill_switch(self):
        state = self.get_state()
        if state.kill_switch_active:
            return (
                False,
                state.current_drawdown,
                f"DRAWDOWN KILL: {state.current_drawdown:.2%} >= {self.config.max_drawdown:.2%}",
            )
        return True, state.current_drawdown, "OK"

    def check_exposure(self, symbol, proposed_notional):
        state = self.get_state()
        if state.total_equity <= 0:
            return False, 0.0, "Invalid equity"
        current_notional = abs(self._positions.get(symbol, AssetPosition(symbol, 0, 0, 0, 0, 0)).notional_value)
        total_exposure = sum(abs(p.notional_value) for p in self._positions.values())
        new_total = total_exposure + proposed_notional
        new_asset_exposure = (current_notional + proposed_notional) / state.total_equity
        if new_asset_exposure > self.config.max_exposure_per_asset:
            scaled = self.config.max_exposure_per_asset * state.total_equity - current_notional
            return (
                False,
                max(0.0, scaled),
                f"EXPOSURE CAP: {new_asset_exposure:.2%} > limit",
            )
        if new_total > state.total_equity:
            scaled = state.total_equity - total_exposure + proposed_notional
            return False, max(0.0, scaled), "TOTAL EXPOSURE > 100%"
        return True, proposed_notional, "OK"

    def check_correlation(self, symbol, proposed_return):
        if len(self._return_history) < 5:
            return True, 1.0, "OK"
        symbols = list(self._positions.keys())
        if symbol not in symbols:
            symbols.append(symbol)
        returns_matrix = []
        valid_symbols = []
        for sym in symbols:
            rets = [r.get(sym, 0.0) for r in self._return_history[-20:]]
            if len(rets) >= 5:
                returns_matrix.append(rets)
                valid_symbols.append(sym)
        if len(returns_matrix) < 2:
            return True, 1.0, "OK"
        try:
            corr_matrix = np.corrcoef(returns_matrix)
        except Exception:
            return True, 1.0, "OK"
        if symbol not in valid_symbols:
            return True, 1.0, "OK"
        sym_idx = valid_symbols.index(symbol)
        max_corr = 0.0
        for i, s in enumerate(valid_symbols):
            if s != symbol and i < len(corr_matrix) and sym_idx < len(corr_matrix):
                cv = float(corr_matrix[i][sym_idx])
                if not math.isnan(cv):
                    max_corr = max(max_corr, cv)
        if max_corr > self.config.correlation_limit:
            reduction = max(0.1, min(1.0, 1.0 - (max_corr - self.config.correlation_limit)))
            return False, reduction, f"CORRELATION REDUCE: {max_corr:.3f} > limit"
        return True, 1.0, "OK"

    def compute_vol_adjusted_size(self, base_size, realized_vol, regime="NORMAL"):
        target_vol = self.config.target_volatility
        kelly_map = {"LOW": 1.0, "NORMAL": 0.75, "HIGH": 0.50, "EXTREME": 0.20}
        kelly = kelly_map.get(regime.upper(), 0.75)
        if realized_vol <= 0 or math.isnan(realized_vol) or math.isinf(realized_vol):
            realized_vol = target_vol
        vol_scalar = target_vol / realized_vol
        vol_scalar = max(0.1, min(vol_scalar, 5.0))
        size = base_size * vol_scalar * kelly
        return self._clamp_size(size)

    def pre_trade_check(self, symbol, proposed_notional, realized_vol=0.0, regime="NORMAL"):
        ok, dd, msg = self.check_kill_switch()
        if not ok:
            return "REJECTED", 0.0, f"KILL_SWITCH: {msg}"
        vol_size = self.compute_vol_adjusted_size(proposed_notional, realized_vol, regime)
        ok, capped, msg = self.check_exposure(symbol, vol_size)
        if not ok:
            return "REDUCED" if capped > 0 else "REJECTED", capped, f"EXPOSURE: {msg}"
        proposed_ret = vol_size / max(self.get_state().total_equity, 1.0)
        ok, reduction, msg = self.check_correlation(symbol, proposed_ret)
        if not ok:
            adjusted = self._clamp_size(vol_size * reduction)
            return (
                "REDUCED" if adjusted > 0 else "REJECTED",
                adjusted,
                f"CORRELATION: {msg}",
            )
        return "APPROVED", vol_size, "OK"

    def record_return(self, symbol, ret):
        if self._return_history and symbol in self._return_history[-1]:
            self._return_history[-1][symbol] = ret
        else:
            if not self._return_history:
                self._return_history.append({})
            self._return_history[-1][symbol] = ret
        if len(self._return_history) > 50:
            self._return_history.pop(0)

    def adjust_pnl(
        self,
        raw_pnl: float,
        max_drawdown: float,
        vol_regime: str = "NORMAL",
    ) -> float:
        """
        Adjust raw PnL by volatility regime and drawdown.

        This is the core post-trade risk adjustment. It applies:
        1. Kelly-derived position scaling by regime
        2. Drawdown penalty (quadratic)
        3. Volatility regime multiplier

        Returns the risk-adjusted PnL (float).

        Args:
            raw_pnl:       raw portfolio return (e.g. 0.05 = 5%)
            max_drawdown:  maximum drawdown observed (e.g. 0.12 = 12%)
            vol_regime:    one of LOW / NORMAL / HIGH / EXTREME

        Returns:
            risk_adjusted_pnl (float, always finite)
        """
        import math

        if math.isnan(raw_pnl) or math.isinf(raw_pnl):
            raw_pnl = 0.0
            return 0.0  # fail-safe: no reward when pnl is undefined

        if math.isnan(max_drawdown) or math.isinf(max_drawdown):
            max_drawdown = 0.0

        # ── 1. Kelly-derived regime multiplier ───────────────────────────
        kelly_map = {"LOW": 1.0, "NORMAL": 0.75, "HIGH": 0.50, "EXTREME": 0.20}
        kelly_mult = kelly_map.get(vol_regime.upper(), 0.75)

        # ── 2. Drawdown penalty (quadratic) ────────────────────────────
        dd_penalty = max_drawdown**2 * 2.0  # 0.10^2 * 2 = 0.02

        # ── 3. Combine ─────────────────────────────────────────────────
        adjusted = raw_pnl * kelly_mult - dd_penalty

        # Kill-switch: EXTREME regime caps negative PnL
        if vol_regime.upper() == "EXTREME" and adjusted < 0:
            adjusted = adjusted * 0.5  # additional 50% penalty in EXTREME

        return float(adjusted)

    @staticmethod
    def _clamp_size(size):
        if math.isnan(size) or math.isinf(size) or size < 0:
            return 0.0
        return min(size, 10_000_000.0)

    def get_positions(self):
        return dict(self._positions)

    def get_realized_vol(self, symbol, lookback=20):
        rets = [r.get(symbol, 0.0) for r in self._return_history[-lookback:]]
        if len(rets) < 2:
            return self.config.target_volatility
        try:
            vol = float(np.std(rets, ddof=0))
            return vol if not (math.isnan(vol) or vol <= 0) else self.config.target_volatility
        except Exception:
            return self.config.target_volatility


if __name__ == "__main__":
    print("RiskEngineV2 self-test...")
    engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    engine.update_equity(100_000)
    engine.update_equity(88_000)
    ok, dd, msg = engine.check_kill_switch()
    assert not ok
    print(f"  Test 1 (Kill Switch): TRIGGERED at {dd:.2%}")
    engine2 = RiskEngineV2(RiskConfigV2(max_exposure_per_asset=0.30))
    engine2.update_equity(100_000)
    engine2.update_position(AssetPosition("BTC", 35_000, 50_000, 48_000))
    ok, size, msg = engine2.check_exposure("ETH", 20_000)
    assert not ok
    print("  Test 2 (Exposure Cap): REJECTED")
    engine3 = RiskEngineV2(RiskConfigV2(target_volatility=0.15))
    size = engine3.compute_vol_adjusted_size(10_000, 0.30, "HIGH")
    expected = 10_000 * (0.15 / 0.30) * 0.50
    assert abs(size - expected) < 1
    print(f"  Test 3 (Vol Targeting): size={size:.0f}")
    engine4 = RiskEngineV2(RiskConfigV2())
    engine4.update_equity(float("nan"))
    state = engine4.get_state()
    assert not math.isnan(state.total_equity)
    print(f"  Test 4 (NaN Safety): equity={state.total_equity:.2f}")
    engine5 = RiskEngineV2(RiskConfigV2(max_drawdown=0.05))
    engine5.update_equity(100_000)
    engine5.update_equity(92_000)
    status, size, msg = engine5.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    assert status == "APPROVED"
    print(f"  Test 5 (Pre-Trade APPROVED): {status}")
    engine5.update_equity(88_000)
    status2, _, _ = engine5.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    assert status2 == "REJECTED"
    print(f"  Test 6 (Pre-Trade Kill): {status2}")
    print("\nRiskEngineV2: all tests passed")

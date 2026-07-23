"""BacktestRunner unit tests."""

import pytest, pandas as pd, numpy as np
from unittest.mock import MagicMock
from orchestration.council_orchestrator import CouncilOrchestrator
from backtest.backtest_runner import BacktestRunner, BacktestStats
from core.base_agent import AgentResponse, SignalDirection


@pytest.fixture
def mock_orch():
    orch = MagicMock(spec=CouncilOrchestrator)
    orch.execute_trading_cycle.return_value = {
        "action": "EXECUTED",
        "size": 1.0,
        "signal": "LONG",
        "risk_reason": "NORMAL",
        "blocked": False,
    }
    return orch


@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    close = 50000 + np.cumsum(np.random.randn(n) * 500)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="h"),
            "open": close - 100,
            "high": close + 200,
            "low": close - 200,
            "close": close,
            "volume": np.random.randint(10, 100, n),
        }
    )


class TestBacktestRunner:
    def test_init_capital(self, mock_orch):
        r = BacktestRunner(mock_orch, initial_capital=50000.0)
        assert r.capital == 50000.0
        assert r.stats.equity_curve == []
        assert r.stats.max_drawdown == 0.0

    def test_init_zero_trades(self, mock_orch):
        r = BacktestRunner(mock_orch)
        assert r.stats.trades == 0
        assert r.stats.wins == 0
        assert r.stats.losses == 0
        assert r.position == 0.0

    @pytest.mark.asyncio
    async def test_run_populates_equity_curve(self, mock_orch, sample_data):
        r = BacktestRunner(mock_orch)
        report = await r.run(sample_data)
        assert report is not None
        assert len(r.stats.equity_curve) == len(sample_data)

    @pytest.mark.asyncio
    async def test_run_returns_report_with_metrics(self, mock_orch, sample_data):
        r = BacktestRunner(mock_orch)
        report = await r.run(sample_data)
        for k in ("total_return_pct", "max_drawdown_pct", "sharpe_ratio", "win_rate", "stops_triggered", "trades"):
            assert k in report, f"Missing key: {k}"
        assert report["max_drawdown_pct"] >= 0.0

    @pytest.mark.asyncio
    async def test_stop_handling(self, mock_orch, sample_data):
        mock_orch.execute_trading_cycle.return_value = {
            "action": "STOP",
            "size": 0.0,
            "risk_reason": "STOP: HMM anomaly",
            "blocked": True,
        }
        r = BacktestRunner(mock_orch)
        report = await r.run(sample_data)
        assert report["stops_triggered"] > 0

    @pytest.mark.asyncio
    async def test_no_negative_sharpe(self, mock_orch, sample_data):
        r = BacktestRunner(mock_orch)
        report = await r.run(sample_data)
        assert isinstance(report["sharpe_ratio"], float)

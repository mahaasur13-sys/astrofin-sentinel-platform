"""backtest/test_metrics_agent.py — TDD tests for metrics_agent.py fixes

Tests:
  C1: MetricsDB.list() returns list[BacktestRun] with correct fields
  C2: MetricsDB.summary() calculates avg_win_rate, avg_sharpe correctly
  C3: record() round-trip save → load preserves all fields
  C4: record_run() with BacktestRun directly returns session_id
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backtest.metrics_agent import (
    BacktestRun,
    MetricsDB,
    load_results,
    record,
    record_run,
)


@pytest.fixture
def tmp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    db = MetricsDB(db_path=db_path)
    yield db
    db_path.unlink(missing_ok=True)


# ─── C1: MetricsDB.list() ─────────────────────────────────────────────────────


def test_list_returns_backtest_run_objects(tmp_db):
    run = BacktestRun(
        session_id="test001",
        symbol="BTCUSDT",
        start_date="2025-01-01",
        end_date="2025-01-31",
        timeframe="SWING",
        win_rate=60.0,
        sharpe_ratio=1.5,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        avg_win_pct=3.0,
        avg_loss_pct=-2.0,
        total_return_pct=12.5,
        max_drawdown_pct=5.0,
        avg_confidence=72.0,
        initial_capital=10000.0,
        final_capital=11250.0,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    tmp_db.save(run)

    results = tmp_db.list(symbol="BTCUSDT", limit=50)

    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], BacktestRun)
    assert results[0].session_id == "test001"
    assert results[0].win_rate == 60.0
    assert results[0].sharpe_ratio == 1.5


def test_list_respects_symbol_filter(tmp_db):
    tmp_db.save(_make_run("sym1", "BTCUSDT"))
    tmp_db.save(_make_run("sym2", "ETHUSDT"))
    tmp_db.save(_make_run("sym3", "BTCUSDT"))

    results = tmp_db.list(symbol="BTCUSDT")
    assert len(results) == 2
    assert all(r.symbol == "BTCUSDT" for r in results)


def test_list_respects_limit(tmp_db):
    for i in range(5):
        tmp_db.save(_make_run(f"run{i}", "BTCUSDT"))

    results = tmp_db.list(limit=3)
    assert len(results) == 3


# ─── C2: MetricsDB.summary() ──────────────────────────────────────────────────


def test_summary_avg_win_rate(tmp_db):
    tmp_db.save(_make_run("s1", "BTCUSDT", win_rate=50.0))
    tmp_db.save(_make_run("s2", "BTCUSDT", win_rate=60.0))
    tmp_db.save(_make_run("s3", "BTCUSDT", win_rate=70.0))

    summary = tmp_db.summary(symbol="BTCUSDT", days=90)

    assert summary is not None
    assert summary.avg_win_rate == pytest.approx(60.0, abs=0.1)


def test_summary_avg_sharpe(tmp_db):
    tmp_db.save(_make_run("s1", "BTCUSDT", sharpe_ratio=1.0))
    tmp_db.save(_make_run("s2", "BTCUSDT", sharpe_ratio=2.0))
    tmp_db.save(_make_run("s3", "BTCUSDT", sharpe_ratio=3.0))

    summary = tmp_db.summary(symbol="BTCUSDT", days=90)

    assert summary is not None
    assert summary.avg_sharpe == pytest.approx(2.0, abs=0.01)
    assert summary.best_sharpe == pytest.approx(3.0, abs=0.01)
    assert summary.worst_sharpe == pytest.approx(1.0, abs=0.01)


def test_summary_trending_improving(tmp_db):
    tmp_db.save(_make_run("s1", "BTCUSDT", win_rate=40.0))
    tmp_db.save(_make_run("s2", "BTCUSDT", win_rate=50.0))
    tmp_db.save(_make_run("s3", "BTCUSDT", win_rate=60.0))
    tmp_db.save(_make_run("s4", "BTCUSDT", win_rate=70.0))

    summary = tmp_db.summary(days=90)
    assert summary.trending == "improving"


def test_summary_trending_declining(tmp_db):
    tmp_db.save(_make_run("s1", "BTCUSDT", win_rate=70.0))
    tmp_db.save(_make_run("s2", "BTCUSDT", win_rate=60.0))
    tmp_db.save(_make_run("s3", "BTCUSDT", win_rate=50.0))
    tmp_db.save(_make_run("s4", "BTCUSDT", win_rate=40.0))

    summary = tmp_db.summary(days=90)
    assert summary.trending == "declining"


def test_summary_returns_none_when_empty():
    tmp_db2 = MetricsDB(db_path=Path(tempfile.mktemp(suffix=".db")))
    summary = tmp_db2.summary(symbol="NONEXISTENT", days=90)
    assert summary is None
    tmp_db2.db_path.unlink(missing_ok=True)


# ─── C3: record() round-trip ─────────────────────────────────────────────────


def test_record_roundtrip(tmp_db):
    sid = record(
        symbol="BTCUSDT",
        win_rate=65.0,
        sharpe_ratio=1.75,
        total_trades=50,
        winning_trades=33,
        losing_trades=17,
        total_return_pct=25.0,
        max_drawdown_pct=8.0,
        avg_confidence=70.0,
        initial_capital=10000.0,
        final_capital=12500.0,
    )

    results = load_results(symbol="BTCUSDT", limit=10)
    found = next((r for r in results if r.session_id == sid), None)
    assert found is not None
    assert found.win_rate == 65.0
    assert found.sharpe_ratio == 1.75
    assert found.total_trades == 50


# ─── C4: record_run() with BacktestRun ───────────────────────────────────────


def test_record_run_with_backtest_run(tmp_db):
    run = _make_run("cr001", "ETHUSDT", win_rate=55.0, sharpe_ratio=1.2)
    sid = record_run(run)

    assert sid == "cr001"
    results = load_results(symbol="ETHUSDT")
    assert len(results) >= 1
    assert any(r.session_id == "cr001" for r in results)


# ─── Helper ───────────────────────────────────────────────────────────────────


def _make_run(session_id: str, symbol: str, **overrides) -> BacktestRun:
    defaults = dict(
        symbol=symbol,
        start_date="2025-01-01",
        end_date="2025-01-31",
        timeframe="SWING",
        win_rate=50.0,
        sharpe_ratio=1.0,
        total_trades=10,
        winning_trades=5,
        losing_trades=5,
        avg_win_pct=2.5,
        avg_loss_pct=-1.5,
        total_return_pct=10.0,
        max_drawdown_pct=5.0,
        avg_confidence=60.0,
        initial_capital=10000.0,
        final_capital=11000.0,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return BacktestRun(session_id=session_id, **defaults)

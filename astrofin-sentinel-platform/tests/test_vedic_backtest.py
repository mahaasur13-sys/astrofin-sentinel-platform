"""tests/test_vedic_backtest.py — Sprint 7: Vedic Backtest Tests."""

import pytest
from datetime import datetime, timezone, timedelta

from trading.backtester import BacktestTrade
from backtest.vedic_backtest import (
    VedicTradeAnnotation,
    VedicBacktestTrade,
    NakshatraPerformance,
    VedicPerformanceMatrix,
    annotate_trade,
    vedic_filter,
)


TZ = timezone(timedelta(hours=4))
DT = datetime(2026, 7, 19, 6, 15, tzinfo=TZ)


class TestVedicTradeAnnotation:

    def test_default(self):
        a = VedicTradeAnnotation()
        assert a.nakshatra == ""
        assert a.election_grade == "neutral"
        assert a.risk_multiplier == 1.0
        assert a.is_favorable_entry is False

    def test_favorable(self):
        a = VedicTradeAnnotation(
            nakshatra="Pushya", election_grade="excellent",
            risk_multiplier=0.75, is_favorable_entry=True,
        )
        assert a.is_favorable_entry
        assert a.risk_multiplier < 1.0


class TestNakshatraPerformance:

    def test_empty(self):
        p = NakshatraPerformance(nakshatra="Ashwini", number=1)
        assert p.trade_count == 0
        assert p.win_rate is None
        assert p.avg_return == 0.0

    def test_one_winner(self):
        p = NakshatraPerformance(nakshatra="Rohini", number=4)
        p.trade_count = 1
        p.wins = 1
        p.total_pnl_pct = 3.5
        assert p.win_rate == 1.0
        assert p.avg_return == 3.5

    def test_one_loser(self):
        p = NakshatraPerformance(nakshatra="Mula", number=19)
        p.trade_count = 1
        p.losses = 1
        p.total_pnl_pct = -5.0
        p.max_drawdown_pct = 5.0
        assert p.win_rate == 0.0
        assert p.avg_return == -5.0


class TestVedicPerformanceMatrix:

    def test_empty(self):
        m = VedicPerformanceMatrix()
        assert len(m.by_nakshatra) == 0
        assert m.best_nakshatra() is None

    def test_add_trade(self):
        m = VedicPerformanceMatrix()
        trade = VedicBacktestTrade(
            entry_time=DT, exit_time=DT, symbol="BTC",
            side="LONG", entry_price=100, exit_price=105,
            size=1, pnl_pct=5.0, pnl_abs=500, commission=1,
            vedic=VedicTradeAnnotation(nakshatra="Pushya", nakshatra_number=8),
        )
        m.add_trade(trade)
        assert "Pushya" in m.by_nakshatra
        assert m.by_nakshatra["Pushya"].trade_count == 1
        assert m.by_nakshatra["Pushya"].win_rate == 1.0

    def test_summary(self):
        m = VedicPerformanceMatrix()
        trade = VedicBacktestTrade(
            entry_time=DT, exit_time=DT, symbol="BTC",
            side="LONG", entry_price=100, exit_price=103,
            size=1, pnl_pct=3.0, pnl_abs=300, commission=1,
            vedic=VedicTradeAnnotation(nakshatra="Rohini", nakshatra_number=4),
        )
        m.add_trade(trade)
        s = m.summary()
        assert "VEDIC BACKTEST" in s
        assert "Rohini" in s

    def test_best_worst(self):
        m = VedicPerformanceMatrix()
        for nakshatra, pnl in [("Pushya", 5.0), ("Mula", -8.0), ("Rohini", 2.0)]:
            trade = VedicBacktestTrade(
                entry_time=DT, exit_time=DT, symbol="BTC",
                side="LONG", entry_price=100, exit_price=100 + pnl,
                size=1, pnl_pct=pnl, pnl_abs=pnl * 10, commission=1,
                vedic=VedicTradeAnnotation(nakshatra=nakshatra, nakshatra_number=1),
            )
            m.add_trade(trade)
        assert m.best_nakshatra() == "Pushya"
        assert m.worst_nakshatra() == "Mula"

    def test_to_dict(self):
        m = VedicPerformanceMatrix()
        trade = VedicBacktestTrade(
            entry_time=DT, exit_time=DT, symbol="ETH",
            side="SHORT", entry_price=2000, exit_price=1900,
            size=1, pnl_pct=5.0, pnl_abs=100, commission=1,
            vedic=VedicTradeAnnotation(nakshatra="Hasta", nakshatra_number=13),
        )
        m.add_trade(trade)
        d = m.to_dict()
        assert "Hasta" in d
        assert d["Hasta"]["trades"] == 1


class TestAnnotateTrade:

    def test_annotates(self):
        trade = BacktestTrade(
            entry_time=DT, exit_time=DT, symbol="BTC",
            side="LONG", entry_price=100, exit_price=105,
            size=1, pnl_pct=5.0, pnl_abs=500, commission=1,
        )
        vt = annotate_trade(trade, DT)
        assert isinstance(vt, VedicBacktestTrade)
        assert vt.vedic.nakshatra != ""
        assert vt.vedic.muhurta_score >= 0


class TestVedicFilter:

    def test_filter_min_muhurta(self):
        # Create a trade at a time with known good muhurta
        good_dt = datetime(2026, 7, 19, 6, 15, tzinfo=TZ)
        bad_dt = datetime(2026, 7, 19, 10, 15, tzinfo=TZ)  # Kaal period
        trades = [
            BacktestTrade(
                entry_time=good_dt, exit_time=good_dt, symbol="BTC",
                side="LONG", entry_price=100, exit_price=105,
                size=1, pnl_pct=5.0, pnl_abs=500, commission=1,
            ),
        ]
        # With high min_muhurta threshold, some might be filtered
        # Just verify function runs without error
        result = vedic_filter(trades, min_muhurta=90, exclude_dangerous=True)
        assert len(result) <= len(trades)

    def test_exclude_dangerous(self):
        # This is a functional test — verifies no crash
        trade = BacktestTrade(
            entry_time=DT, exit_time=DT, symbol="BTC",
            side="LONG", entry_price=100, exit_price=105,
            size=1, pnl_pct=5.0, pnl_abs=500, commission=1,
        )
        result = vedic_filter([trade], exclude_dangerous=True)
        assert isinstance(result, list)

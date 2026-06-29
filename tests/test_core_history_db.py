"""
test_core_history_db.py — Tests for core/history_db.py (SQLite session history)

Phase 1 (R9): Add coverage for persistent session history (R-08).
Tests cover:
  • HistoryDB construction + schema init (idempotent)
  • save() with full and minimal dicts (UPSERT behavior)
  • get() including miss path
  • list() with symbol/signal filters, limit + offset
  • stats() aggregate (win_rate, avg_confidence, signal distribution)
  • clear() with age filter
  • isolation per test via tmp_path
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from core.history_db import (
    HistoryDB,
    save_session,
    get_session,
    list_sessions,
    session_stats,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────


def _make_result(
    session_id: str = "test_001",
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    signal: str = "LONG",
    confidence: int = 75,
    agent_count: int = 5,
    price: float = 50000.0,
) -> dict:
    return {
        "session_id": session_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "query_type": "analysis",
        "current_price": price,
        "flows_run": {"technical": True, "astro": True, "macro": True},
        "agent_count": agent_count,
        "started_at": "2026-06-29T00:00:00Z",
        "timestamp": "2026-06-29T00:01:00Z",
        "final_recommendation": {
            "signal": signal,
            "confidence": confidence,
            "reasoning": "Test reasoning text",
        },
    }


@pytest.fixture
def db(tmp_path: Path) -> HistoryDB:
    """Fresh isolated DB per test."""
    return HistoryDB(db_path=tmp_path / "test_history.db")


# ─── Schema + init ─────────────────────────────────────────────────────────────


class TestHistoryDBSchema:
    def test_init_creates_table(self, db, tmp_path):
        # Connection to the same path should reveal the table
        conn = sqlite3.connect(str(tmp_path / "test_history.db"))
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        assert cur.fetchone() is not None
        conn.close()

    def test_init_is_idempotent(self, tmp_path):
        HistoryDB(db_path=tmp_path / "idem.db")
        # Second init should not fail
        HistoryDB(db_path=tmp_path / "idem.db")

    def test_init_creates_indexes(self, db, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "test_history.db"))
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='sessions'"
        ).fetchall()
        index_names = {r[0] for r in rows}
        assert "idx_sessions_symbol" in index_names
        assert "idx_sessions_timeframe" in index_names
        assert "idx_sessions_signal" in index_names
        conn.close()


# ─── save / get ────────────────────────────────────────────────────────────────


class TestHistoryDBSaveGet:
    def test_save_returns_session_id(self, db):
        result = _make_result(session_id="save_001")
        assert db.save(result) == "save_001"

    def test_save_then_get_roundtrip(self, db):
        result = _make_result(session_id="rt_001", confidence=82)
        db.save(result)
        loaded = db.get("rt_001")
        assert loaded is not None
        assert loaded["session_id"] == "rt_001"
        assert loaded["symbol"] == "BTCUSDT"
        assert loaded["final_signal"] == "LONG"
        assert loaded["final_confidence"] == 82

    def test_save_upserts_on_conflict(self, db):
        db.save(_make_result(session_id="upsert_001", signal="LONG"))
        db.save(_make_result(session_id="upsert_001", signal="SHORT", confidence=60))
        loaded = db.get("upsert_001")
        assert loaded["final_signal"] == "SHORT"
        assert loaded["final_confidence"] == 60

    def test_get_returns_none_when_missing(self, db):
        assert db.get("never_saved") is None

    def test_save_handles_missing_recommendation(self, db):
        # Without final_recommendation, default to NEUTRAL/50
        result = _make_result(session_id="no_rec")
        result.pop("final_recommendation")
        db.save(result)
        loaded = db.get("no_rec")
        assert loaded["final_signal"] == "NEUTRAL"
        assert loaded["final_confidence"] == 50

    def test_save_truncates_long_reasoning(self, db):
        result = _make_result(session_id="long_reasoning")
        result["final_recommendation"]["reasoning"] = "x" * 1000
        db.save(result)
        loaded = db.get("long_reasoning")
        # Column is truncated to 500 chars
        assert len(loaded["final_reasoning"]) == 500


# ─── list / filter ─────────────────────────────────────────────────────────────


class TestHistoryDBList:
    def test_list_returns_recent_first(self, db):
        for i in range(5):
            db.save(_make_result(session_id=f"seq_{i:03d}"))
        rows = db.list(limit=10)
        assert len(rows) == 5
        # Default ordering is created_at DESC; we just verify all present
        session_ids = {r["session_id"] for r in rows}
        assert session_ids == {f"seq_{i:03d}" for i in range(5)}

    def test_list_filters_by_symbol(self, db):
        db.save(_make_result(session_id="btc_1", symbol="BTCUSDT"))
        db.save(_make_result(session_id="eth_1", symbol="ETHUSDT"))
        btc_rows = db.list(symbol="BTCUSDT")
        assert len(btc_rows) == 1
        assert btc_rows[0]["symbol"] == "BTCUSDT"

    def test_list_filters_by_signal(self, db):
        db.save(_make_result(session_id="long_1", signal="LONG"))
        db.save(_make_result(session_id="short_1", signal="SHORT"))
        longs = db.list(signal="LONG")
        assert all(r["final_signal"] == "LONG" for r in longs)

    def test_list_respects_limit_and_offset(self, db):
        for i in range(10):
            db.save(_make_result(session_id=f"page_{i:03d}"))
        page1 = db.list(limit=3, offset=0)
        page2 = db.list(limit=3, offset=3)
        assert len(page1) == 3
        assert len(page2) == 3
        # Pages should not overlap
        ids1 = {r["session_id"] for r in page1}
        ids2 = {r["session_id"] for r in page2}
        assert ids1.isdisjoint(ids2)


# ─── stats ─────────────────────────────────────────────────────────────────────


class TestHistoryDBStats:
    def test_stats_empty_db(self, db):
        s = db.stats()
        assert s["total_sessions"] == 0

    def test_stats_with_mixed_signals(self, db):
        db.save(_make_result(session_id="long_a", signal="LONG", confidence=80))
        db.save(_make_result(session_id="long_b", signal="LONG", confidence=70))
        db.save(_make_result(session_id="short_c", signal="SHORT", confidence=60))
        s = db.stats()
        assert s["total_sessions"] == 3
        assert s["avg_confidence"] == pytest.approx(70.0, abs=0.1)
        # LONG is treated as "win" in win_rate calculation
        assert 0 < s["win_rate_long"] <= 1.0

    def test_stats_signal_distribution(self, db):
        db.save(_make_result(session_id="d1", signal="LONG"))
        db.save(_make_result(session_id="d2", signal="LONG"))
        db.save(_make_result(session_id="d3", signal="NEUTRAL"))
        s = db.stats()
        assert "signal_distribution" in s
        assert s["signal_distribution"]["LONG"] >= 2


# ─── clear (vacuum) ────────────────────────────────────────────────────────────


class TestHistoryDBClear:
    def test_clear_keeps_recent_rows(self, db):
        db.save(_make_result(session_id="keep"))
        db.clear(older_than_days=999)  # very old threshold → keep all
        assert db.get("keep") is not None

    def test_clear_removes_old_rows(self, db, tmp_path):
        db.save(_make_result(session_id="old_one"))
        # Insert a row with very old created_at directly
        conn = sqlite3.connect(str(tmp_path / "test_history.db"))
        conn.execute(
            "UPDATE sessions SET created_at = datetime('now', '-30 days') WHERE session_id = ?",
            ("old_one",),
        )
        conn.commit()
        conn.close()
        db.clear(older_than_days=7)
        assert db.get("old_one") is None


# ─── Module-level helpers ──────────────────────────────────────────────────────


class TestModuleLevelHelpers:
    def test_save_session_helper(self, tmp_path, monkeypatch):
        # Use a custom DB path through get_db cache reset
        from core import history_db as mod

        monkeypatch.setattr(mod, "_db_path", lambda: tmp_path / "helper.db")
        # Reset module singleton
        mod._db_instance = None
        sid = save_session(_make_result(session_id="helper_001"))
        assert sid == "helper_001"
        assert get_session("helper_001") is not None

    def test_list_sessions_module_helper(self, tmp_path, monkeypatch):
        from core import history_db as mod

        monkeypatch.setattr(mod, "_db_path", lambda: tmp_path / "list_helper.db")
        mod._db_instance = None
        save_session(_make_result(session_id="list_h1", symbol="BTCUSDT"))
        save_session(_make_result(session_id="list_h2", symbol="ETHUSDT"))
        all_sessions = list_sessions()
        assert len(all_sessions) >= 2

    def test_session_stats_module_helper(self, tmp_path, monkeypatch):
        from core import history_db as mod

        monkeypatch.setattr(mod, "_db_path", lambda: tmp_path / "stats_helper.db")
        mod._db_instance = None
        save_session(_make_result(session_id="stats_h1"))
        s = session_stats()
        assert "total_sessions" in s
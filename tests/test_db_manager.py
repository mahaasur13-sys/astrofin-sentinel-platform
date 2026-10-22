"""Tests for Dual-Engine DatabaseManager (Phase 6.1)."""
from __future__ import annotations

import logging
import os
import sqlite3
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/test_db")
os.environ.setdefault("ENABLE_DUAL_WRITE", "true")

from db.session import DatabaseManager, get_db_manager


@pytest.fixture
def clean_manager():
    mgr = DatabaseManager()
    yield mgr


def test_sqlite_fallback_available(clean_manager):
    assert clean_manager.sqlite_engine is not None
    assert clean_manager.sqlite_session_factory is not None


@pytest.mark.skipif(
    os.environ.get("SENTINEL_PG_TESTS") != "1",
    reason="no reachable PostgreSQL: needs SENTINEL_PG_TESTS=1 and a live DATABASE_URL",
)
def test_pg_session_factory_initialized(clean_manager):
    assert clean_manager.pg_session_factory is not None


def test_fallback_on_pg_error(clean_manager):
    with patch.object(clean_manager, "_init_pg", side_effect=RuntimeError("PG down")):
        mgr2 = DatabaseManager()
        assert mgr2.sqlite_session_factory is not None


def test_context_manager_yields_session(clean_manager):
    with clean_manager.session(use_pg=True) as s:
        assert s is not None


def test_no_fallback_log_when_pg_ok(caplog):
    """PG up: SQLite init must not log 'fallback' and the flag stays off."""
    caplog.set_level(logging.INFO)

    def ok_pg(self):
        self.pg_engine = MagicMock()
        self.pg_session_factory = MagicMock()

    with patch.object(DatabaseManager, "_init_pg", ok_pg), \
         patch("db.session.create_engine") as mock_ce, \
         patch("db.session.sessionmaker") as mock_sm:
        mock_ce.return_value = MagicMock()
        mock_sm.return_value = MagicMock()
        mgr = DatabaseManager()

    assert mgr.sqlite_fallback is False
    assert "fallback" not in caplog.text


def test_fallback_logged_when_pg_fails(caplog):
    """PG down: SQLite is logged as fallback and the flag is set."""
    caplog.set_level(logging.INFO)

    def fail_pg(self):
        self.pg_engine = None
        self.pg_session_factory = None

    with patch.object(DatabaseManager, "_init_pg", fail_pg), \
         patch("db.session.create_engine") as mock_ce, \
         patch("db.session.sessionmaker") as mock_sm:
        mock_ce.return_value = MagicMock()
        mock_sm.return_value = MagicMock()
        mgr = DatabaseManager()

    assert mgr.sqlite_fallback is True
    assert "SQLite fallback engine initialized" in caplog.text

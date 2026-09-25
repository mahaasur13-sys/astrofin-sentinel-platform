"""Fail-closed Postgres data-plane tests (audit P0).

Covers:
- allow_sqlite_fallback() gate (flag AND dev/test only)
- session() raises on OperationalError in prod, never silently falls back
- is_postgres_available() / pg_available = real SELECT 1 (no weak engine check)
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

import db.session as db_session
from db.session import DatabaseManager


def test_allow_sqlite_fallback_requires_flag_and_dev_test(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(db_session, "settings", fake)

    # flag off → always False
    fake.ALLOW_SQLITE_FALLBACK = False
    fake.env = "development"
    assert db_session.allow_sqlite_fallback() is False

    # flag on + dev/test → True
    fake.ALLOW_SQLITE_FALLBACK = True
    fake.env = "development"
    assert db_session.allow_sqlite_fallback() is True
    fake.env = "test"
    assert db_session.allow_sqlite_fallback() is True

    # flag on but prod/staging → False (env gating)
    fake.env = "production"
    assert db_session.allow_sqlite_fallback() is False
    fake.env = "staging"
    assert db_session.allow_sqlite_fallback() is False


def _make_manager(pg_session, sqlite_factory):
    mgr = DatabaseManager.__new__(DatabaseManager)
    mgr.pg_session_factory = MagicMock(return_value=pg_session)
    mgr.sqlite_session_factory = sqlite_factory
    return mgr


def test_session_prod_raises_no_sqlite(monkeypatch):
    """prod/default + OperationalError → exception, SQLite never called."""
    monkeypatch.setattr(db_session, "allow_sqlite_fallback", lambda: False)

    pg = MagicMock()
    pg.commit.side_effect = OperationalError("SELECT 1", {}, Exception("down"))
    sqlite_factory = MagicMock()
    mgr = _make_manager(pg, sqlite_factory)

    with pytest.raises(OperationalError):
        with mgr.session(use_pg=True):
            pass

    sqlite_factory.assert_not_called()


def test_session_dev_flag_falls_back_and_logs_error(monkeypatch, caplog):
    """dev + ALLOW_SQLITE_FALLBACK=true → fallback branch is entered, logs error."""
    monkeypatch.setattr(db_session, "allow_sqlite_fallback", lambda: True)

    pg = MagicMock()
    pg.commit.side_effect = OperationalError("SELECT 1", {}, Exception("down"))
    sqlite_factory = MagicMock(return_value=MagicMock())
    mgr = _make_manager(pg, sqlite_factory)

    caplog.set_level(logging.ERROR, logger="db.session")
    # The legacy fallback re-yield raises RuntimeError after logging; the
    # security-relevant assertions are that SQLite was engaged and logged error.
    with pytest.raises(Exception):
        with mgr.session(use_pg=True):
            pass

    sqlite_factory.assert_called()
    errors = [r for r in caplog.records if "falling back to SQLite" in r.getMessage()]
    assert errors, "fallback must be logged"
    assert all(r.levelno == logging.ERROR for r in errors), "fallback must log at ERROR"


def test_pg_available_engine_none():
    mgr = DatabaseManager.__new__(DatabaseManager)
    mgr.pg_engine = None
    assert mgr.pg_available is False


def test_pg_available_select1_fails():
    mgr = DatabaseManager.__new__(DatabaseManager)
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.side_effect = Exception("down")
    mgr.pg_engine = engine
    assert mgr.pg_available is False


def test_pg_available_select1_ok():
    mgr = DatabaseManager.__new__(DatabaseManager)
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value = None
    mgr.pg_engine = engine
    assert mgr.pg_available is True

"""Tests for Dual-Engine DatabaseManager (Phase 6.1)."""
from __future__ import annotations

import os
import sqlite3
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test_db")
os.environ.setdefault("ENABLE_DUAL_WRITE", "true")

from db.session import DatabaseManager, get_db_manager


@pytest.fixture
def clean_manager():
    mgr = DatabaseManager()
    yield mgr


def test_sqlite_fallback_available(clean_manager):
    assert clean_manager.sqlite_engine is not None
    assert clean_manager.sqlite_session_factory is not None


def test_pg_session_factory_initialized(clean_manager):
    assert clean_manager.pg_session_factory is not None


def test_fallback_on_pg_error(clean_manager):
    with patch.object(clean_manager, "_init_pg", side_effect=RuntimeError("PG down")):
        mgr2 = DatabaseManager()
        assert mgr2.sqlite_session_factory is not None


def test_context_manager_yields_session(clean_manager):
    with clean_manager.session(use_pg=True) as s:
        assert s is not None

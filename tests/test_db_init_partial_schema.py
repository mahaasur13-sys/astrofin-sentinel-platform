"""Regression test: partial schema completion on init.

Live smoke showed a fresh volume where ``sessions`` (and a few others) existed
but ``karl_decision_records`` did not. ``init_db_if_needed()`` returned
``tables_created=True`` anyway because ``init_schema_if_needed()`` treated
"any table exists" as "schema is ready".

This test drives the real ``init_schema_if_needed()`` against an in-memory
SQLite engine seeded with only the ``sessions`` table (no docker, no faiss) and
asserts the missing tables — including ``karl_decision_records`` — are created
by the checkfirst ``Base.metadata.create_all`` path.
"""

from __future__ import annotations

import os

os.environ.setdefault("DB_BACKEND", "postgresql")

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from db.models import Session
from db.init import init_schema_if_needed


@pytest.fixture()
def partial_schema_engine(monkeypatch):
    """In-memory SQLite with ONLY the sessions table (partial schema)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Seed just the sessions table — simulate a partially-initialized schema.
    Session.__table__.create(engine)

    inspector = inspect(engine)
    assert "sessions" in inspector.get_table_names()
    assert "karl_decision_records" not in inspector.get_table_names()

    # Redirect the db.session helpers to our SQLite engine so init_schema_if_needed
    # exercises the create_all path without a live Postgres.
    monkeypatch.setattr("db.session.is_postgres_available", lambda: True)
    monkeypatch.setattr("db.session.get_engine", lambda: engine)
    return engine


def test_init_creates_missing_tables_on_partial_schema(partial_schema_engine):
    engine = partial_schema_engine

    assert init_schema_if_needed() is True

    tables = set(inspect(engine).get_table_names())
    assert "sessions" in tables
    assert "karl_decision_records" in tables, (
        "partial schema must be completed by Base.metadata.create_all"
    )

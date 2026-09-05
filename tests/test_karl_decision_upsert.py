"""Upsert regression test for KARL decision records.

Live PG produced::

    UniqueViolation karl_decision_records_pkey
    Key (decision_id)=(KARL_0000_BTCUSDT) already exists
    → falling back to SQLite

The stable ``decision_id`` (``KARL_{counter}_{symbol}``) collides on a repeat
cycle for the same symbol, so the repository must UPSERT on ``decision_id``
rather than plain-INSERT. This test exercises the real PostgreSQL-branch
``DecisionRecordRepository.save()`` against an in-memory SQLite engine (no
docker, no faiss) and asserts the second save updates the row instead of
raising a PK violation.
"""

from __future__ import annotations

import contextlib
import os

# Force the PostgreSQL repository branch (default, but explicit for clarity).
os.environ["DB_BACKEND"] = "postgresql"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import repositories as repo
from db.models import Base, KARLDecisionRecord


@pytest.fixture()
def pg_backed_sqlite(monkeypatch):
    """Patch ``pg_session`` to a shared in-memory SQLite engine.

    This keeps the PostgreSQL-branch ``DecisionRecordRepository`` under test
    while avoiding any real Postgres/docker dependency.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)

    @contextlib.contextmanager
    def fake_pg_session():
        s = session_factory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    monkeypatch.setattr(repo, "pg_session", fake_pg_session)
    return session_factory


def _record(**overrides: object) -> dict:
    record: dict = {
        "decision_id": "KARL_0000_BTCUSDT",
        "session_id": None,
        "symbol": "BTCUSDT",
        "price": 67000.0,
        "timeframe": "SWING",
        "regime": "NORMAL",
        "state_hash": "deadbeef",
        "top_trajectories": [],
        "selected_ensemble": [],
        "q_values": [0.5],
        "q_star": 0.5,
        "advantage": 0.0,
        "uncertainty_aleatoric": 0.1,
        "uncertainty_epistemic": 0.2,
        "uncertainty_total": 0.3,
        "confidence_raw": 50,
        "confidence_final": 55,
        "confidence_adjustments": [],
        "final_action": "LONG",
        "position_pct": 0.02,
        "kpi_snapshot": {},
        "metadata": {},
    }
    record.update(overrides)
    return record


def test_save_same_decision_id_upserts_instead_of_raising(pg_backed_sqlite):
    session_factory = pg_backed_sqlite

    first = repo.DecisionRecordRepository.save(_record(confidence_final=55))
    # Repeat cycle for the same symbol reuses the stable decision_id.
    second = repo.DecisionRecordRepository.save(_record(confidence_final=80))

    assert first == "KARL_0000_BTCUSDT"
    assert second == "KARL_0000_BTCUSDT"

    s = session_factory()
    try:
        rows = s.query(KARLDecisionRecord).all()
        assert len(rows) == 1, "repeated save must UPDATE, not INSERT a second row"
        assert rows[0].confidence_final == 80, "latest decision must win"
    finally:
        s.close()

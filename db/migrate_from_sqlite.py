#!/usr/bin/env python3
"""db/migrate_from_sqlite.py — ATOM-DB-MIGRATION: SQLite → PostgreSQL Migration

Usage:
    python -m db.migrate_from_sqlite

This script migrates existing session data from SQLite (core/history.db)
to PostgreSQL. It is idempotent: re-running is safe (skips existing records).

Prerequisites:
    1. PostgreSQL running with schema applied
    2. DB_BACKEND=postgresql
    3. All tables created via init_db_if_needed()
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_sqlite_sessions(sqlite_path: Path):
    """Read all sessions from SQLite history.db."""
    import sqlite3

    if not sqlite_path.exists():
        logger.warning(f"SQLite DB not found: {sqlite_path}")
        return []

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in cur.fetchall()}

    if "sessions" not in tables:
        logger.warning("No 'sessions' table in SQLite")
        conn.close()
        return []

    cur.execute("SELECT * FROM sessions ORDER BY created_at ASC")
    rows = cur.fetchall()
    conn.close()

    # Convert rows to dicts
    sessions = []
    for row in rows:
        sessions.append({k: row[k] for k in row.keys()})

    return sessions


def migrate_sessions(sessions: list) -> dict:
    """Migrate sessions to PostgreSQL via DecisionRecordRepository."""
    try:
        from db.repositories import DecisionRecordRepository

        migrated = 0
        skipped = 0

        for session in sessions:
            try:
                # Convert session to decision record format
                record = {
                    "decision_id": session.get("session_id", session.get("id")),
                    "session_id": session.get("session_id", session.get("id")),
                    "symbol": session.get("symbol", "BTCUSDT"),
                    "price": session.get("current_price", 0) or 0,
                    "timeframe": session.get("timeframe", "SWING"),
                    "regime": session.get("regime", "NORMAL"),
                    "state_hash": None,
                    "top_trajectories": session.get("signals", []) or [],
                    "selected_ensemble": [],
                    "q_values": [],
                    "q_star": session.get("reward", 0.5),
                    "advantage": 0,
                    "uncertainty_aleatoric": 0.5,
                    "uncertainty_epistemic": 0.5,
                    "uncertainty_total": 0.5,
                    "confidence_raw": session.get("final_confidence", 50),
                    "confidence_final": session.get("final_confidence", 50),
                    "confidence_adjustments": [],
                    "final_action": session.get("final_signal", "NEUTRAL"),
                    "position_pct": session.get("position_pct", 0.02),
                    "kpi_snapshot": {},
                    "metadata": {
                        "migrated_from": "sqlite",
                        "migrated_at": datetime.now(timezone.utc).isoformat(),
                        "original_created_at": session.get("created_at"),
                    },
                }

                DecisionRecordRepository.save(record)
                migrated += 1

            except Exception as e:
                skipped += 1
                logger.debug(f"Skipped session {session.get('session_id')}: {e}")

        return {"migrated": migrated, "skipped": skipped}

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {"migrated": 0, "skipped": 0, "error": str(e)}


def main():
    logger.info("=" * 60)
    logger.info("ATOM-DB-MIGRATION: SQLite → PostgreSQL")
    logger.info("=" * 60)

    # Set backend to PostgreSQL
    import os

    os.environ["DB_BACKEND"] = "postgresql"

    # Check PostgreSQL availability
    from db.session import is_postgres_available

    if not is_postgres_available():
        logger.error("PostgreSQL not available. Start it with: docker-compose up -d postgres")
        sys.exit(1)

    logger.info("PostgreSQL: AVAILABLE")

    # Initialize schema if needed
    from db.init import init_schema_if_needed

    if not init_schema_if_needed():
        logger.error("Schema initialization failed")
        sys.exit(1)

    logger.info("Schema: READY")

    # Read from SQLite
    sqlite_path = Path(__file__).parent.parent / "core" / "history.db"
    sessions = get_sqlite_sessions(sqlite_path)

    if not sessions:
        logger.info("No sessions found in SQLite — nothing to migrate")
        return

    logger.info(f"Found {len(sessions)} sessions in SQLite")

    # Migrate
    result = migrate_sessions(sessions)

    logger.info("=" * 60)
    logger.info("Migration complete:")
    logger.info(f"  Migrated: {result.get('migrated', 0)}")
    logger.info(f"  Skipped:  {result.get('skipped', 0)}")
    if result.get("error"):
        logger.error(f"  Error: {result['error']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

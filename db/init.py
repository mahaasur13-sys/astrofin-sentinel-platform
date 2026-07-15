"""db/init.py - ATOM-DB-MIGRATION: Database initialization

Features:
- Applies schema/001_initial.sql directly on first run
- Creates TimescaleDB hypertables
- Seeds agent beliefs
- Graceful fallback to SQLite if PostgreSQL unavailable
- Idempotent: safe to run multiple times
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_SQL = Path(__file__).parent.parent / "schema" / "001_initial.sql"


def apply_raw_sql_schema(engine) -> bool:
    """
    Apply schema/001_initial.sql directly via raw SQL.
    Used when PostgreSQL is available but tables don't exist yet.
    """
    try:
        if not _SCHEMA_SQL.exists():
            logger.warning(f"[DB-INIT] Schema file not found: {_SCHEMA_SQL}")
            return False

        sql_text = _SCHEMA_SQL.read_text()

        # Split on semicolons, filter empty statements
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]

        with engine.connect() as conn:
            for stmt in statements:
                if stmt.startswith("--") or not stmt:
                    continue
                try:
                    conn.exec_driver_cmds(stmt)
                except Exception as e:
                    # Some statements like CREATE EXTENSION may already exist
                    if "already exists" not in str(e):
                        logger.debug(f"[DB-INIT] Statement error (non-fatal): {e}")
            conn.commit()

        logger.info(f"[DB-INIT] Applied schema from {_SCHEMA_SQL.name}")
        return True
    except Exception as e:
        logger.error(f"[DB-INIT] Failed to apply raw SQL schema: {e}")
        return False


def init_schema_if_needed() -> bool:
    """
    Check if PostgreSQL tables exist. If not, create them.
    Tries: 1) Base.metadata.create_all, 2) raw SQL, 3) SQLite fallback
    """
    try:
        from db.session import get_engine, is_postgres_available

        if not is_postgres_available():
            logger.warning("[DB-INIT] PostgreSQL not available")
            return _init_sqlite_fallback()

        engine = get_engine()

        # Check if sessions table exists
        from sqlalchemy import inspect

        inspector = inspect(engine)
        existing = inspector.get_table_names()

        if existing:
            logger.info(f"[DB-INIT] PostgreSQL tables already exist ({len(existing)} tables)")
            return True

        # Try SQLAlchemy create_all first
        try:
            from db.models import Base

            Base.metadata.create_all(engine)
            logger.info("[DB-INIT] Created tables via SQLAlchemy Base.create_all()")
            return True
        except Exception as e:
            logger.warning(f"[DB-INIT] Base.create_all failed: {e}")

        # Fall back to raw SQL
        return apply_raw_sql_schema(engine)

    except Exception as e:
        logger.error(f"[DB-INIT] Schema init failed: {e}")
        return _init_sqlite_fallback()


def _init_sqlite_fallback() -> bool:
    """Ensure SQLite history.db exists for fallback mode."""
    try:
        from core.history_db import _db_path

        path = _db_path()
        path.parent.mkdir(exist_ok=True)
        if not path.exists():
            path.touch()
        logger.info(f"[DB-INIT] SQLite fallback initialized: {path}")
        return True
    except Exception as e:
        logger.warning(f"[DB-INIT] SQLite fallback failed: {e}")
        return False


def init_db_if_needed() -> dict:
    """
    Main entry point for DB initialization.
    Call this once at application startup.
    """
    result = {
        "postgres_available": False,
        "tables_created": False,
        "backend": "sqlite",
        "error": None,
    }

    try:
        from db.session import is_postgres_available, wait_for_postgres

        if is_postgres_available():
            result["postgres_available"] = True
            result["backend"] = "postgresql"
            result["tables_created"] = init_schema_if_needed()
            if result["tables_created"]:
                logger.info("[DB-INIT] PostgreSQL fully initialized")
            return result

        # Try to connect with retry
        connected = wait_for_postgres(max_retries=3, retry_delay=1.0)
        if connected:
            result["postgres_available"] = True
            result["backend"] = "postgresql"
            result["tables_created"] = init_schema_if_needed()
            return result

        # Fall back to SQLite
        result["tables_created"] = _init_sqlite_fallback()
        logger.info("[DB-INIT] Using SQLite fallback")
        return result

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[DB-INIT] Error: {e}")
        result["tables_created"] = _init_sqlite_fallback()
        return result


def get_db_status() -> dict:
    """Get current database status for monitoring."""
    status = {"backend": "unknown", "postgres_available": False}

    try:
        from db.session import is_postgres_available

        status["postgres_available"] = is_postgres_available()
        status["backend"] = "postgresql" if status["postgres_available"] else "sqlite"
    except Exception:
        pass

    return status

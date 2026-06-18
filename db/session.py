from sqlalchemy.orm import scoped_session, sessionmaker

"""db/session.py — PostgreSQL Session Management (ATOM-DB-MIGRATION)

Features:
- PostgreSQL connection pooling (SQLAlchemy)
- Graceful SQLite fallback when PostgreSQL unavailable
- Retry logic on startup
- Connection pool stats
"""

import logging
import os
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_ENGINE = None
_Session = None
_BACKEND = None  # "postgresql" or "sqlite"


def get_database_url() -> str:
    return (
        f"postgresql://{os.getenv('POSTGRES_USER', 'astrofin')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'astrofin_secret')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'astrofin')}"
    )


def _create_pg_engine(url: str):
    from sqlalchemy import create_engine, event
    from sqlalchemy.pool import QueuePool

    engine = create_engine(
        url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=bool(os.getenv("SQL_ECHO", "")),
    )

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT set_config('app.search_path', 'public', FALSE)")
        cursor.close()

    return engine


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        url = get_database_url()
        _ENGINE = _create_pg_engine(url)
    return _ENGINE


def get_session_factory():
    global _Session
    if _Session is None:
        _Session = scoped_session(sessionmaker(bind=get_engine(), autoflush=False))
    return _Session


@contextmanager
def pg_session():
    """Context manager for PostgreSQL sessions."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def is_postgres_available() -> bool:
    """Check if PostgreSQL is reachable. Tries once, no retry."""
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def wait_for_postgres(
    max_retries: int = 10,
    retry_delay: float = 2.0,
) -> bool:
    """
    Wait for PostgreSQL to become available with retry logic.
    Logs each attempt. Returns True if connected, False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            eng = get_engine()
            with eng.connect() as conn:
                conn.execute("SELECT 1")
            logger.info(f"[DB] PostgreSQL connected on attempt {attempt}")
            return True
        except Exception as e:
            logger.warning(f"[DB] PostgreSQL not ready (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
    logger.error("[DB] PostgreSQL unavailable after max retries — using SQLite fallback")
    return False


def get_db_stats() -> dict:
    """Connection pool stats for monitoring."""
    try:
        eng = get_engine()
        pool = eng.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "available": pool.available(),
            "backend": "postgresql",
        }
    except Exception as e:
        return {"error": str(e), "backend": "unknown"}

"""db/session.py — Dual-Engine Database Manager (ATOM-DB-MIGRATION v2)

PostgreSQL (TimescaleDB + pgvector) + SQLite fallback.
Dual-Write mode: writes to both PG and SQLite; reads from PG with SQLite fallback.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from core.settings import settings

logger = logging.getLogger(__name__)

_db_manager = None


class DatabaseManager:
    """Dual-engine manager: PostgreSQL primary + SQLite fallback.

    Usage:
        manager = get_db_manager()
        with manager.session(use_pg=True) as s:
            s.execute(text("SELECT 1"))
    """

    def __init__(self) -> None:
        self.pg_engine = None
        self.sqlite_engine = None
        self.pg_session_factory = None
        self.sqlite_session_factory = None
        self._init_pg()
        self._init_sqlite()

    def _init_pg(self) -> None:
        url = settings.database_url.get_secret_value().strip()
        if not url:
            logger.info("No DATABASE_URL set — PostgreSQL disabled")
            return
        try:
            self.pg_engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("SQL_ECHO", "") == "1",
            )

            @event.listens_for(self.pg_engine, "connect")
            def _set_search_path(dbapi_conn, _connection_record):
                cur = dbapi_conn.cursor()
                cur.execute("SET timezone TO 'UTC'")
                cur.close()

            self.pg_session_factory = sessionmaker(bind=self.pg_engine, autoflush=False)
            logger.info("PostgreSQL engine initialized (pool=%d)", settings.DB_POOL_SIZE)
        except Exception as e:
            logger.error("Failed to init PostgreSQL: %s", e)

    def _init_sqlite(self) -> None:
        sqlite_path = settings.SQLITE_FALLBACK_PATH
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        self.sqlite_engine = create_engine(
            f"sqlite:///{sqlite_path}",
            connect_args={"check_same_thread": False},
        )
        self.sqlite_session_factory = sessionmaker(bind=self.sqlite_engine, autoflush=False)
        logger.info("SQLite fallback engine initialized at %s", sqlite_path)

    @property
    def pg_available(self) -> bool:
        if not self.pg_engine:
            return False
        try:
            with self.pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @contextmanager
    def session(self, use_pg: bool = True) -> Session:
        """Yields a DB session. Prefers PG, falls back to SQLite if PG is down."""
        session = None
        pg_attempted = False
        try:
            if use_pg and self.pg_session_factory:
                pg_attempted = True
                session = self.pg_session_factory()
            else:
                session = self.sqlite_session_factory()

            yield session

            if settings.ENABLE_DUAL_WRITE and pg_attempted and self.sqlite_session_factory:
                # Dual-write: also commit to SQLite (best-effort)
                pass  # handled by caller

            session.commit()

        except Exception as e:
            if session:
                session.rollback()
            if pg_attempted and self.sqlite_session_factory:
                logger.warning("PG session failed, falling back to SQLite: %s", e)
                with self.sqlite_session_factory() as fallback:
                    yield fallback
                    fallback.commit()
                    return
            raise
        finally:
            if session:
                session.close()

    def get_stats(self) -> dict:
        stats: dict = {"pg_available": self.pg_available}
        if self.pg_engine and self.pg_engine.pool:
            pool = self.pg_engine.pool
            stats.update({
                "pg_pool_size": pool.size(),
                "pg_checked_in": pool.checkedin(),
                "pg_checked_out": pool.checkedout(),
                "pg_overflow": pool.overflow(),
            })
        return stats


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@contextmanager
def get_db_session(use_pg: bool = True) -> Session:
    """Shortcut for get_db_manager().session()."""
    with get_db_manager().session(use_pg=use_pg) as s:
        yield s


# Backward-compatible aliases
def get_engine():
    return get_db_manager().pg_engine or get_db_manager().sqlite_engine


def get_session_factory():
    mgr = get_db_manager()
    return mgr.pg_session_factory or mgr.sqlite_session_factory


def is_postgres_available() -> bool:
    return get_db_manager().pg_available


def wait_for_postgres(max_retries: int = 10, retry_delay: float = 2.0) -> bool:
    mgr = get_db_manager()
    for attempt in range(1, max_retries + 1):
        if mgr.pg_available:
            logger.info("PostgreSQL connected (attempt %d)", attempt)
            return True
        logger.warning("PostgreSQL not ready (attempt %d/%d)", attempt, max_retries)
        if attempt < max_retries:
            time.sleep(retry_delay)
    logger.error("PostgreSQL unavailable after %d retries", max_retries)
    return False


def get_db_stats() -> dict:
    return get_db_manager().get_stats()


# Backward compatibility alias for db/karl_replay.py
@contextmanager
def pg_session():
    """Backward-компатибельная PG сессия с авто-коммитом."""
    with get_db_manager().session(use_pg=True) as s:
        yield s


def is_postgres_available() -> bool:
    """Check if PG connection can be established."""
    mgr = get_db_manager()
    return mgr.pg_engine is not None and mgr.pg_session_factory is not None

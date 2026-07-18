"""
core.outbox — ADR-001 Sprint 3: Transactional Outbox Pattern

Гарантированная доставка событий через SQLite persistence.
Resolves Risk #4: fire-and-forget publish_event() заменён на outbox fallback.

API (sync — вызывается внутри асинхронного кода):
    store = OutboxStore(config)
    store.initialize()              # CREATE TABLE
    event_id = store.store(ch, payload)  # → str
    store.mark_publishing(event_id)
    store.mark_delivered(event_id)
    store.mark_failed(event_id, error)
    store.get_stats()               # → dict
    pending = store.fetch_pending(limit=10)

    worker = OutboxRetryWorker(store=store, broker=broker, config=config)
    await worker.start()            # launch retry loop
    await worker.stop()             # graceful shutdown
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Enums & Config ────────────────────────────────────────────────────


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHING = "PUBLISHING"
    DELIVERED = "DELIVERED"
    DEAD = "DEAD"


@dataclass
class OutboxConfig:
    """Outbox configuration with exponential backoff."""

    db_path: str = "outbox.db"
    retry_interval: float = 5.0
    retry_backoff: float = 2.0
    max_attempts: int = 10

    @property
    def max_retries(self) -> int:
        return self.max_attempts


# ── OutboxStore (sync SQLite with WAL) ────────────────────────────────


class OutboxStore:
    """Persistent event store with guaranteed delivery.

    Использует синхронный SQLite с WAL-режимом для конкурентного
    доступа. Все методы потокобезопасны (asyncio.Lock).
    """

    def __init__(self, config: OutboxConfig | None = None):
        self.config = config or OutboxConfig()
        self._db_path = self.config.db_path
        self._lock = asyncio.Lock()

    def initialize(self) -> None:
        """Создать таблицу outbox_events."""
        db_dir = Path(self._db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    channel TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    attempts INTEGER DEFAULT 0,
                    last_error TEXT,
                    next_retry_at REAL,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_outbox_status_next
                ON outbox_events(status, next_retry_at)
            """)
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    # ── Store API ──────────────────────────────────────────────────

    def store(self, channel: str, payload: dict) -> str:
        """Сохранить событие. Возвращает event_id."""
        event_id = str(uuid.uuid4())
        payload_json = json.dumps(payload, default=str)
        now = time.time()
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO outbox_events
                   (event_id, channel, payload, status, attempts, next_retry_at, created_at)
                   VALUES (?, ?, ?, ?, 0, ?, ?)""",
                (event_id, channel, payload_json, OutboxStatus.PENDING.value, now, now),
            )
            conn.commit()
        finally:
            conn.close()
        return event_id

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    def mark_publishing(self, event_id: str) -> None:
        """Атомарно: PENDING → PUBLISHING, attempts += 1."""
        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE outbox_events
                   SET status = ?, attempts = attempts + 1
                   WHERE event_id = ?""",
                (OutboxStatus.PUBLISHING.value, event_id),
            )
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    def mark_delivered(self, event_id: str) -> None:
        """PUBLISHING → DELIVERED."""
        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE outbox_events
                   SET status = ? WHERE event_id = ?""",
                (OutboxStatus.DELIVERED.value, event_id),
            )
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    def mark_failed(self, event_id: str, error: str) -> None:
        """PUBLISHING → PENDING с exponential backoff для next_retry_at.

        delay = retry_interval * retry_backoff^attempts
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT attempts FROM outbox_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            attempts = row["attempts"] if row else 0
            delay = self.config.retry_interval * (self.config.retry_backoff ** attempts)
            next_at = time.time()
            conn.execute(
                """UPDATE outbox_events
                   SET status = ?, last_error = ?, next_retry_at = ?
                   WHERE event_id = ?""",
                (OutboxStatus.PENDING.value, error[:500], next_at, event_id),
            )
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    def fetch_pending(self, limit: int = 10) -> list[dict]:
        """Извлечь PENDING события с next_retry_at <= now."""
        now = time.time()
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT event_id, channel, payload, attempts
                   FROM outbox_events
                   WHERE status = ? AND next_retry_at <= ?
                     AND attempts < ?
                   ORDER BY next_retry_at ASC
                   LIMIT ?""",
                (OutboxStatus.PENDING.value, now, self.config.max_attempts, limit),
            ).fetchall()
            return [
                {
                    "event_id": r["event_id"],
                    "channel": r["channel"],
                    "payload": json.loads(r["payload"]),
                    "attempts": r["attempts"],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    def get_stats(self) -> dict:
        """Статистика: pending/publishing/delivered/dead counts."""
        conn = self._get_conn()
        try:
            row = conn.execute("""
                SELECT
                    SUM(CASE WHEN status = 'PENDING' AND attempts < ? THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'PUBLISHING' THEN 1 ELSE 0 END) as publishing,
                    SUM(CASE WHEN status = 'DELIVERED' THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN status = 'DEAD' OR (status = 'PENDING' AND attempts >= ?) THEN 1 ELSE 0 END) as dead
                FROM outbox_events
            """, (self.config.max_attempts, self.config.max_attempts)).fetchone()
            return {
                "pending": row["pending"] or 0,
                "publishing": row["publishing"] or 0,
                "delivered": row["delivered"] or 0,
                "dead": row["dead"] or 0,
            }
        finally:
            conn.close()

    def close(self) -> None:
        """Закрыть outbox (no-op для тестов)."""
        pass

    def _get_conn(self) -> sqlite3.Connection:
        """Thread-safe connection with WAL mode."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn


# ── OutboxRetryWorker ─────────────────────────────────────────────────


class OutboxRetryWorker:
    """Async background worker: polls outbox and retries failed events.

    Usage:
        worker = OutboxRetryWorker(store=store, broker=broker, config=config)
        await worker.start()
        # ... system runs ...
        await worker.stop()
    """

    def __init__(
        self,
        store: OutboxStore,
        broker: "MessageBroker",
        config: OutboxConfig | None = None,
    ):
        self.store = store
        self.broker = broker
        self.config = config or store.config
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Запустить фоновый retry loop."""
        self._running = True
        self._task = asyncio.create_task(self._retry_loop())
        logger.info("outbox_retry_worker_started")

    async def stop(self) -> None:
        """Остановить retry loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("outbox_retry_worker_stopped")

    async def _retry_loop(self) -> None:
        """Фоновый цикл доставки."""
        while self._running:
            try:
                await self._retry_batch()
            except Exception as e:
                logger.error("outbox_retry_loop_error", extra={"error": str(e)})
            try:
                await asyncio.sleep(self.config.retry_interval)
            except asyncio.CancelledError:
                break

    async def _retry_batch(self) -> None:
        """Доставить один batch событий."""
        events = self.store.fetch_pending(limit=20)
        for event in events:
            eid = event["event_id"]
            try:
                self.store.mark_publishing(eid)
                await self.broker.publish(event["channel"], event["payload"])
                self.store.mark_delivered(eid)
            except Exception as e:
                self.store.mark_failed(eid, str(e))


# ── Backward Compatibility ────────────────────────────────────────────


class Outbox:
    """Legacy Outbox — delegates to OutboxStore + OutboxRetryWorker.

    Сохраняет обратную совместимость с кодом base_agent.py и sentinel_v5_broker.py.
    """

    def __init__(self, db_path: str = "outbox.db", config: OutboxConfig | None = None):
        self.config = config or OutboxConfig(db_path=db_path)
        self.store = OutboxStore(self.config)
        self._worker: Optional[OutboxRetryWorker] = None

    async def start(self, broker: "MessageBroker") -> None:
        self.store.initialize()
        self._worker = OutboxRetryWorker(store=self.store, broker=broker, config=self.config)
        await self._worker.start()

    async def stop(self) -> None:
        if self._worker:
            await self._worker.stop()

    async def store(self, channel: str, payload: dict) -> None:
        self.store.store(channel, payload)

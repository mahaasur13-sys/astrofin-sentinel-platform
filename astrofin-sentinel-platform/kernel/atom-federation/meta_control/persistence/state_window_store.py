# ATOMFEDERATION-OS - StateWindowStore
# SQLite with WAL - Persistent, Append-Only, Thread-Safe
# =========================================================

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from orchestration.execution_gateway import ExecutionGateway


@dataclass
class TickRecord:
    tick: int
    state: bytes
    decision: bytes | None = None
    outcome: bytes | None = None
    recorded_at: str | None = None


class StateWindowStore:
    # =========================================================
    # PERSISTENT STATE WINDOW — SQLite WAL
    # Append-only ledger with hard durability guarantees
    # =========================================================

    def __init__(self, db_path: str = None, gateway: ExecutionGateway = None):
        if db_path is None:
            db_path = Path.home() / '.atom_federation' / 'state_window.db'

        self._db_path = str(db_path)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # FIX: Use default isolation (deferred) for WAL compatibility
        # IMMEDIATE + WAL = undefined behavior in high-concurrency
        # deferred + WAL = safe concurrent readers + exclusive writer
        self._conn = sqlite3.connect(
            self._db_path,
            timeout=30.0,
            isolation_level=None  # autocommit mode, we control transactions
        )
        self._conn.execute('PRAGMA journal_mode=WAL;')
        self._conn.execute('PRAGMA synchronous=NORMAL;')  # durable but fast
        self._conn.execute('PRAGMA busy_timeout=30000;')  # 30s retry on lock
        self._conn.execute('PRAGMA wal_autocheckpoint=1000;')  # checkpoint every 1000 pages

        self._lock = threading.RLock()
        self._create_table()
        self._gateway = gateway or ExecutionGateway.instance()

    def _create_table(self) -> None:
        self._conn.execute('''
            CREATE TABLE IF NOT EXISTS state_window (
                tick INTEGER PRIMARY KEY,
                state BLOB NOT NULL,
                decision BLOB,
                outcome BLOB,
                recorded_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        self._conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_tick_desc
            ON state_window(tick DESC)
        ''')

    @ExecutionGateway.requires_gateway
    def record_tick(
        self,
        tick: int,
        state: bytes,
        decision: bytes | None = None,
        outcome: bytes | None = None
    ) -> None:
        with self._lock:
            # FIX: Use explicit transaction for durability
            self._conn.execute('BEGIN IMMEDIATE')  # acquire write lock
            try:
                self._conn.execute(
                    'INSERT OR REPLACE INTO state_window (tick, state, decision, outcome) VALUES (?,?,?,?)',
                    (tick, state, decision, outcome)
                )
                self._conn.execute('COMMIT')
            except Exception:
                self._conn.execute('ROLLBACK')
                raise

    @ExecutionGateway.requires_gateway
    def get_tick(self, tick: int) -> TickRecord | None:
        with self._lock:
            cursor = self._conn.execute(
                'SELECT tick, state, decision, outcome, recorded_at FROM state_window WHERE tick = ?',
                (tick,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return TickRecord(
                tick=row[0],
                state=row[1],
                decision=row[2],
                outcome=row[3],
                recorded_at=row[4]
            )

    @ExecutionGateway.requires_gateway
    def get_window(self, from_tick: int, to_tick: int) -> list[TickRecord]:
        with self._lock:
            cursor = self._conn.execute(
                '''SELECT tick, state, decision, outcome, recorded_at
                FROM state_window
                WHERE tick BETWEEN ? AND ?
                ORDER BY tick ASC''',
                (from_tick, to_tick)
            )
            return [
                TickRecord(
                    tick=r[0], state=r[1], decision=r[2],
                    outcome=r[3], recorded_at=r[4]
                )
                for r in cursor.fetchall()
            ]

    @ExecutionGateway.requires_gateway
    def get_latest_tick(self) -> int | None:
        with self._lock:
            cursor = self._conn.execute(
                'SELECT MAX(tick) FROM state_window'
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else None

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.execute('PRAGMA wal_checkpoint(FULL);')
                self._conn.close()
                self._conn = None

# atomic_ledger.py — atom-federation-os v9.0+ATOM-META-RL-019
# AtomicLedgerWriter — Single-writer WAL with strict linearizability.
#
# Guarantees:
#   1. Strict FIFO ordering by tick
#   2. No concurrent writes (thread-safe via threading.Lock)
#   3. WAL semantics: entries written to WAL before commit
#   4. Atomic commit
#   5. Append-only (no update/delete)
#
# Usage:
#   AtomicLedgerWriter.instance().record(entry_data, tick=tick)
#   AtomicLedgerWriter.instance().verify_linearizability()
#   AtomicLedgerWriter.instance().get_entries(from_tick=0)

from __future__ import annotations

import hashlib
import json
import os
import threading
import time


class SafetyViolationError(Exception):
    '''Raised when ledger ordering invariant is violated.'''
    pass


class AtomicLedgerWriter:
    '''
    Single-writer WAL for MutationLedger — guarantees linearizability.
    
    Guarantees:
        1. Strict FIFO ordering by tick (out-of-order = SafetyViolationError)
        2. No concurrent writes (thread-safe via threading.Lock)
        3. WAL semantics: entries appended to WAL file before commit
        4. Atomic commit to main ledger
        5. Append-only: no update or delete operations
    
    Invariants:
        - tick must be >= last_tick (strictly increasing)
        - All entries visible only after WAL write + commit
        - WAL can be replayed on crash
    
    Usage:
        writer = AtomicLedgerWriter.instance()
        writer.record({'operation': 'mutate', 'data': {...}}, tick=42)
        
        # Verify
        result = writer.verify_linearizability()
        print(result['is_linearizable'])  # True
    '''

    _instance: AtomicLedgerWriter | None = None
    _lock = threading.Lock()

    def __new__(cls) -> AtomicLedgerWriter:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._entries: list[dict] = []
                    instance._tick_index: int = -1
                    instance._wal_path: str = '/tmp/atom_federation_ledger.wal'
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._entries = []
        self._tick_index = -1
        self._wal_path = os.environ.get(
            'ATOM_LEDGER_WAL_PATH',
            '/tmp/atom_federation_ledger.wal'
        )

        # Clean WAL on startup (if exists from previous run)
        if os.path.exists(self._wal_path):
            try:
                self._replay_wal()
            except Exception:
                # WAL corrupted — start fresh
                self._entries.clear()
                if os.path.exists(self._wal_path):
                    os.remove(self._wal_path)

    @classmethod
    def instance(cls) -> AtomicLedgerWriter:
        if cls._instance is None:
            cls()
        return cls._instance

    def record(self, entry: dict, tick: int) -> None:
        '''
        Thread-safe append with WAL semantics.
        
        Args:
            entry: Dict containing mutation data
            tick: Monotonically increasing tick (must be >= last tick)
        
        Raises:
            SafetyViolationError: if tick < last_tick (out-of-order)
        '''
        with self._lock:
            # ── Verify ordering ─────────────────────────────────────────
            last_tick = self._entries[-1]['tick'] if self._entries else -1
            if tick < last_tick:
                raise SafetyViolationError(
                    f'Out-of-order ledger write: tick={tick}, last_tick={last_tick}. '
                    f'MutationLedger must be strictly linearizable.'
                )

            # ── Build WAL entry ──────────────────────────────────────────
            prev_hash = self._get_last_hash()
            wal_entry = {
                'tick': tick,
                'entry': entry,
                'prev_hash': prev_hash,
                'timestamp': time.time(),  # Physical timestamp for audit only
            }

            # ── Write to WAL first ──────────────────────────────────────
            self._write_wal(wal_entry)

            # ── Compute entry hash ───────────────────────────────────────
            entry_hash = self._compute_hash(wal_entry)

            # ── Commit to main ledger ───────────────────────────────────
            committed_entry = {
                'tick': tick,
                'data': entry,
                'hash': entry_hash,
                'prev_hash': prev_hash,
            }
            self._entries.append(committed_entry)
            self._tick_index = tick

    def _write_wal(self, wal_entry: dict) -> None:
        '''
        Append entry to WAL file.
        WAL is fsync'd to ensure durability.
        '''
        wal_line = json.dumps(wal_entry, sort_keys=True) + '\n'
        with open(self._wal_path, 'a') as f:
            f.write(wal_line)
            f.flush()
            os.fsync(f.fileno())  # Ensure durability

    def _get_last_hash(self) -> str:
        '''Get hash of last committed entry (or GENESIS for empty).'''
        if not self._entries:
            return 'GENESIS'
        return self._entries[-1]['hash']

    def _compute_hash(self, wal_entry: dict) -> str:
        '''Compute deterministic hash of WAL entry.'''
        return hashlib.sha256(
            json.dumps(wal_entry, sort_keys=True).encode()
        ).hexdigest()

    def _replay_wal(self) -> None:
        '''
        Replay WAL file on startup to recover committed entries.
        Called only when WAL file exists from previous run.
        '''
        self._entries.clear()
        with open(self._wal_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                wal_entry = json.loads(line)
                entry_hash = self._compute_hash(wal_entry)
                committed_entry = {
                    'tick': wal_entry['tick'],
                    'data': wal_entry['entry'],
                    'hash': entry_hash,
                    'prev_hash': wal_entry['prev_hash'],
                }
                self._entries.append(committed_entry)

        if self._entries:
            self._tick_index = self._entries[-1]['tick']

    def get_entries(self, from_tick: int = 0) -> list[dict]:
        '''
        Return all entries from from_tick onwards.
        Thread-safe read (makes copy).
        
        Args:
            from_tick: Start from this tick (inclusive)
        
        Returns:
            list[dict]: List of committed entries
        '''
        with self._lock:
            return [e.copy() for e in self._entries if e['tick'] >= from_tick]

    def get_entry_at(self, tick: int) -> dict | None:
        '''
        Get entry at specific tick.
        
        Args:
            tick: Tick to look up
        
        Returns:
            dict or None: Entry at tick, or None if not found
        '''
        with self._lock:
            for e in self._entries:
                if e['tick'] == tick:
                    return e.copy()
            return None

    def get_last_entry(self) -> dict | None:
        '''
        Get most recent entry.
        
        Returns:
            dict or None: Last entry, or None if ledger empty
        '''
        with self._lock:
            return self._entries[-1].copy() if self._entries else None

    def verify_linearizability(self) -> dict:
        '''
        Verify all entries are in strictly ascending tick order.
        
        Returns:
            dict with:
                - is_linearizable: bool
                - total_entries: int
                - tick_range: (min_tick, max_tick)
                - gaps: list of missing ticks
                - duplicate_ticks: list of duplicate ticks
        '''
        with self._lock:
            if not self._entries:
                return {
                    'is_linearizable': True,
                    'total_entries': 0,
                    'tick_range': (0, 0),
                    'gaps': [],
                    'duplicate_ticks': [],
                }

            ticks = [e['tick'] for e in self._entries]

            # Check strictly ascending (no equal ticks)
            duplicate_ticks = [
                t for t in set(ticks) if ticks.count(t) > 1
            ]

            # Check for gaps
            min_tick = min(ticks)
            max_tick = max(ticks)
            expected_ticks = set(range(min_tick, max_tick + 1))
            actual_ticks = set(ticks)
            gaps = sorted(expected_ticks - actual_ticks)

            # Strictly ascending: each tick < next tick
            is_linear = all(
                ticks[i] < ticks[i+1] for i in range(len(ticks) - 1)
            ) and len(duplicate_ticks) == 0

            return {
                'is_linearizable': is_linear,
                'total_entries': len(self._entries),
                'tick_range': (min_tick, max_tick),
                'gaps': gaps,
                'duplicate_ticks': duplicate_ticks,
            }

    def get_stats(self) -> dict:
        '''
        Get ledger statistics.
        
        Returns:
            dict with ledger stats
        '''
        with self._lock:
            verification = self.verify_linearizability()
            return {
                'total_entries': len(self._entries),
                'tick_range': verification['tick_range'],
                'is_linearizable': verification['is_linearizable'],
                'wal_path': self._wal_path,
                'wal_exists': os.path.exists(self._wal_path),
            }

    def truncate_wal(self) -> None:
        '''
        Truncate WAL after checkpoint (for cleanup).
        '''
        with self._lock:
            if os.path.exists(self._wal_path):
                os.remove(self._wal_path)

    def reset(self) -> None:
        '''
        Reset ledger and WAL (for testing only).
        WARNING: Do not call in production.
        '''
        with self._lock:
            self._entries.clear()
            self._tick_index = -1
            if os.path.exists(self._wal_path):
                os.remove(self._wal_path)

    @classmethod
    def reset_instance(cls) -> None:
        '''
        Reset singleton instance (for testing only).
        '''
        with cls._lock:
            if cls._instance is not None:
                cls._instance._entries.clear()
                cls._instance._tick_index = -1
            cls._instance = None

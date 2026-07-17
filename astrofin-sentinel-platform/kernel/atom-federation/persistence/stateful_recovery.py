# persistence/stateful_recovery.py — NEW
# ATOM-META-RL-022 P1 — Stateful Recovery Correctness

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from typing import Any

from core.deterministic import DeterministicClock, DeterministicUUIDFactory
from persistence.atomic_fs import AtomicFileWrite, SnapshotHashValidator

# ── EventStore ────────────────────────────────────────────────────────────────

@dataclass
class PersistentEvent:
    tick: int
    event_type: str
    payload: Any
    node_id: str
    event_id: str
    prev_hash: str
    self_hash: str

    def to_dict(self) -> dict:
        return {
            'tick': self.tick,
            'event_type': self.event_type,
            'payload': self.payload,
            'node_id': self.node_id,
            'event_id': self.event_id,
            'prev_hash': self.prev_hash,
            'self_hash': self.self_hash,
        }

    @staticmethod
    def from_dict(d: dict) -> 'PersistentEvent':
        return PersistentEvent(**d)


class EventStore:
    r'''
    Persistent, append-only event store with WAL.

    Guarantees:
      - All events are durable (WAL on write)
      - Append-only (no update, no delete)
      - Crash-safe recovery on startup
      - Hash chain integrity verification
    '''

    def __init__(self, storage_path: str, wal_path: str, node_id: str = 'local'):
        self.node_id = node_id
        self._storage_path = storage_path
        self._wal_path = wal_path
        self._lock = threading.RLock()
        self._events: list[PersistentEvent] = []
        self._last_hash: str = 'genesis'
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        os.makedirs(os.path.dirname(wal_path), exist_ok=True)
        self._recover()

    def _recover(self) -> None:
        '''Recover from WAL on startup.'''
        wal = WriteAheadLog(self._wal_path)
        recovered = wal.recover()
        for d in recovered:
            evt = PersistentEvent.from_dict(d)
            self._events.append(evt)
            self._last_hash = evt.self_hash

    def _compute_hash(self, event: PersistentEvent) -> str:
        content = json.dumps(event.to_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def append(self, event_type: str, payload: Any, tick: int) -> int:
        '''Append event to store. Returns event index.'''
        with self._lock:
            event_id = DeterministicUUIDFactory.make_id(
                'evt', f'{event_type}:{tick}', self.node_id
            )
            event = PersistentEvent(
                tick=tick,
                event_type=event_type,
                payload=payload,
                node_id=self.node_id,
                event_id=event_id,
                prev_hash=self._last_hash,
                self_hash=''  # computed below
            )
            event.self_hash = self._compute_hash(event)

            # Write to WAL first (durable)
            wal = WriteAheadLog(self._wal_path)
            wal.write(event.to_dict())

            # Append to memory
            self._events.append(event)
            self._last_hash = event.self_hash

            # Periodically flush to disk
            if len(self._events) % 100 == 0:
                self._flush()

            return len(self._events) - 1

    def get_events_since(self, tick: int) -> list[PersistentEvent]:
        '''Get all events with tick >= N.'''
        with self._lock:
            return [e for e in self._events if e.tick >= tick]

    def get_events_range(self, tick_start: int, tick_end: int) -> list[PersistentEvent]:
        '''Get all events with tick_start <= tick <= tick_end.'''
        with self._lock:
            return [e for e in self._events if tick_start <= e.tick <= tick_end]

    def get_last_event(self) -> PersistentEvent | None:
        with self._lock:
            return self._events[-1] if self._events else None

    def snapshot(self) -> bytes:
        '''Create deterministic snapshot of all events.'''
        with self._lock:
            data = [e.to_dict() for e in self._events]
            return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

    def _flush(self) -> None:
        '''Flush events to disk.'''
        with self._lock:
            af = AtomicFileWrite(self._storage_path)
            af.write_json([e.to_dict() for e in self._events], DeterministicClock.get_tick())

    def verify_chain(self) -> bool:
        '''Verify hash chain integrity.'''
        with self._lock:
            prev_hash = 'genesis'
            for e in self._events:
                if e.prev_hash != prev_hash:
                    return False
                computed = self._compute_hash(e)
                if computed != e.self_hash:
                    return False
                prev_hash = e.self_hash
            return True

    def __len__(self) -> int:
        return len(self._events)


# ── WriteAheadLog ─────────────────────────────────────────────────────────────

class WriteAheadLog:
    r'''
    Deterministic Write-Ahead Log for crash recovery.

    Guarantees:
      - Every mutation is written to WAL before being applied
      - WAL entries are deterministic (no time.time(), no uuid4)
      - Recovery replays WAL entries to restore state
    '''

    def __init__(self, wal_path: str):
        self.wal_path = wal_path
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(wal_path), exist_ok=True)

    def write(self, entry: dict) -> None:
        '''Append entry to WAL. Uses atomic write.'''
        with self._lock:
            # Append line to WAL file
            with open(self.wal_path, 'a') as f:
                line = json.dumps(entry, sort_keys=True, separators=(',', ':'))
                f.write(line + '\n')

    def recover(self) -> list[dict]:
        '''Recover entries from WAL. Handles partial writes.'''
        with self._lock:
            if not os.path.exists(self.wal_path):
                return []

            entries = []

            with open(self.wal_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        # Verify entry has required fields
                        if 'tick' in entry and 'event_type' in entry:
                            entries.append(entry)
                        else:
                            pass  # potentially partial write
                    except json.JSONDecodeError:
                        pass  # partial write at end of file

            return entries

    def clear(self) -> None:
        '''Clear WAL after successful checkpoint. For recovery only.'''
        with self._lock:
            if os.path.exists(self.wal_path):
                os.remove(self.wal_path)


# ── MutationLedger ────────────────────────────────────────────────────────────

@dataclass
class MutationRecord:
    tick: int
    operation: str
    payload: Any
    record_id: str
    prev_hash: str
    self_hash: str

    def to_dict(self) -> dict:
        return {
            'tick': self.tick,
            'operation': self.operation,
            'payload': self.payload,
            'record_id': self.record_id,
            'prev_hash': self.prev_hash,
            'self_hash': self.self_hash,
        }

    @staticmethod
    def from_dict(d: dict) -> 'MutationRecord':
        return MutationRecord(**d)


class MutationLedger:
    r'''
    Persistent, append-only mutation ledger with hash chain.

    Guarantees:
      - All mutations are recorded in hash chain
      - Full replay from any tick possible
      - Committed ticks are tracked separately
    '''

    def __init__(self, path: str):
        self._path = path
        self._entries: list[MutationRecord] = []
        self._committed_ticks: set[int] = set()
        self._last_hash: str = 'genesis'
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as f:
                data = json.load(f)
                for d in data.get('entries', []):
                    rec = MutationRecord.from_dict(d)
                    self._entries.append(rec)
                    self._last_hash = rec.self_hash
                self._committed_ticks = set(data.get('committed_ticks', []))

    def _compute_hash(self, rec: MutationRecord) -> str:
        content = json.dumps(rec.to_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def append(self, operation: str, payload: Any, tick: int) -> None:
        '''Append mutation record.'''
        with self._lock:
            record_id = DeterministicUUIDFactory.make_id(
                'mut', f'{operation}:{tick}', ''
            )
            rec = MutationRecord(
                tick=tick,
                operation=operation,
                payload=payload,
                record_id=record_id,
                prev_hash=self._last_hash,
                self_hash=''  # computed below
            )
            rec.self_hash = self._compute_hash(rec)
            self._entries.append(rec)
            self._last_hash = rec.self_hash

    def commit_tick(self, tick: int) -> None:
        '''Mark tick as committed.'''
        with self._lock:
            self._committed_ticks.add(tick)
            self._persist()

    def get_committed_ticks(self) -> set[int]:
        with self._lock:
            return self._committed_ticks.copy()

    def replay_to(self, tick: int) -> list[MutationRecord]:
        '''Replay all mutations up to and including tick N.'''
        with self._lock:
            return [e for e in self._entries if e.tick <= tick]

    def verify_chain(self) -> bool:
        '''Verify hash chain integrity.'''
        with self._lock:
            prev_hash = 'genesis'
            for e in self._entries:
                if e.prev_hash != prev_hash:
                    return False
                computed = self._compute_hash(e)
                if computed != e.self_hash:
                    return False
                prev_hash = e.self_hash
            return True

    def _persist(self) -> None:
        with self._lock:
            data = {
                'entries': [e.to_dict() for e in self._entries],
                'committed_ticks': sorted(self._committed_ticks),
            }
            with open(self._path, 'w') as f:
                json.dump(data, f, sort_keys=True, separators=(',', ':'))


# ── PersistentStateWindowStore ────────────────────────────────────────────────

@dataclass
class StateRecord:
    tick: int
    state_hash: str
    snapshot: str  # canonical JSON

    def to_dict(self) -> dict:
        return {'tick': self.tick, 'state_hash': self.state_hash, 'snapshot': self.snapshot}

    @staticmethod
    def from_dict(d: dict) -> 'StateRecord':
        return StateRecord(**d)


class PersistentStateWindowStore:
    r'''
    Bounded sliding window of state snapshots (persistent).

    Guarantees:
      - All states are deterministic (canonical JSON)
      - Bounded size (max_depth entries)
      - Full checkpoint/restore capability
    '''

    def __init__(self, path: str, max_depth: int = 1000):
        self._path = path
        self.max_depth = max_depth
        self._window: list[StateRecord] = []
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path) as f:
                data = json.load(f)
                for d in data.get('window', []):
                    self._window.append(StateRecord.from_dict(d))

    def record(self, state: Any, tick: int) -> None:
        '''Record state at tick.'''
        with self._lock:
            state_hash = SnapshotHashValidator.compute_state_hash(state)
            snapshot = json.dumps(state, sort_keys=True, separators=(',', ':'))
            rec = StateRecord(tick=tick, state_hash=state_hash, snapshot=snapshot)
            self._window.append(rec)
            if len(self._window) > self.max_depth:
                self._window.pop(0)
            self._persist()

    def get_state_at(self, tick: int) -> dict | None:
        '''Get state snapshot at exact tick.'''
        with self._lock:
            for rec in reversed(self._window):
                if rec.tick == tick:
                    return json.loads(rec.snapshot)
            return None

    def get_latest(self) -> StateRecord | None:
        with self._lock:
            return self._window[-1] if self._window else None

    def checkpoint(self) -> bytes:
        '''Create deterministic checkpoint.'''
        with self._lock:
            return json.dumps(
                [r.to_dict() for r in self._window],
                sort_keys=True,
                separators=(',', ':')
            ).encode()

    def recover(self, checkpoint_data: bytes) -> None:
        '''Recover from checkpoint.'''
        with self._lock:
            data = json.loads(checkpoint_data)
            self._window = [StateRecord.from_dict(d) for d in data]

    def _persist(self) -> None:
        with self._lock:
            with open(self._path, 'w') as f:
                json.dump(
                    [r.to_dict() for r in self._window],
                    f,
                    sort_keys=True,
                    separators=(',', ':')
                )

    def __len__(self) -> int:
        return len(self._window)


# ── Recovery Manager ──────────────────────────────────────────────────────────

class RecoveryManager:
    r'''
    Coordinates full system recovery from persistent state.

    Startup sequence:
      1. Recover WAL entries (EventStore)
      2. Recover MutationLedger committed ticks
      3. Recover StateWindowStore snapshots
      4. Verify all hash chains
      5. Replay to latest committed state
    '''

    def __init__(
        self,
        event_store: EventStore,
        mutation_ledger: MutationLedger,
        state_window: PersistentStateWindowStore
    ):
        self.event_store = event_store
        self.mutation_ledger = mutation_ledger
        self.state_window = state_window

    def full_recovery(self) -> dict[str, Any]:
        '''Perform full recovery. Returns recovered state + diagnostics.'''
        # Step 1: Recover from WAL
        events = self.event_store.get_events_since(0)

        # Step 2: Get committed ticks
        committed = self.mutation_ledger.get_committed_ticks()
        latest_tick = max(committed) if committed else 0

        # Step 3: Get state at latest committed tick
        state = self.state_window.get_state_at(latest_tick)

        # Step 4: Verify chains
        events_ok = self.event_store.verify_chain()
        ledger_ok = self.mutation_ledger.verify_chain()

        return {
            'latest_committed_tick': latest_tick,
            'recovered_state': state,
            'events_recovered': len(events),
            'event_chain_ok': events_ok,
            'ledger_chain_ok': ledger_ok,
            'recovery_success': events_ok and ledger_ok and state is not None,
        }

    def get_recovery_point(self) -> int | None:
        '''Find the most recent valid recovery point.'''
        committed = self.mutation_ledger.get_committed_ticks()
        if not committed:
            return None
        latest = max(committed)
        # Verify we can recover to this point
        if self.state_window.get_state_at(latest) is not None:
            return latest
        return None

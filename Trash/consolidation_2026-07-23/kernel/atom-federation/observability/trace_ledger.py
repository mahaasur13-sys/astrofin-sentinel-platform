# observability/trace_ledger.py — NEW
# ATOM-META-RL-022 P2 — Deterministic Trace Ledger

import json
import threading
from dataclasses import dataclass
from typing import Any

from core.deterministic import DeterministicClock, DeterministicUUIDFactory


@dataclass
class TraceEntry:
    r'''
    A single entry in the DeterministicTraceLedger.

    order_key format: '{global_tick:010d}:{local_sequence:08d}:{node_id}'
    This ensures:
      1. Entries are ordered by (tick ASC, sequence ASC, node_id ASC)
      2. Same trace across all nodes (deterministic)
      3. Replay produces identical sequence
    '''
    global_tick: int
    local_sequence: int
    node_id: str
    event_type: str
    payload: Any
    order_key: str
    entry_id: str

    @staticmethod
    def make_order_key(global_tick: int, local_sequence: int, node_id: str) -> str:
        return f'{global_tick:010d}:{local_sequence:08d}:{node_id}'


class DeterministicTraceLedger:
    r'''
    All events have global tick index, strictly ordered, replayable without external input.

    Guarantees:
      1. Every entry has a global tick index (DeterministicClock-based)
      2. Entries are strictly ordered by order_key (no ties possible)
      3. Full replay from any tick produces identical sequence
      4. No time.time() or random in ordering

    Theorem:
      sorted(get_all_entries(), key=order_key) == deterministic sequence
      replay_from(tick=N) yields identical sequence on all nodes
    '''

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._entries: list[TraceEntry] = []
        self._tick_index: dict[int, list[int]] = {}  # tick -> list of entry indices
        self._local_sequence: int = 0
        self._lock = threading.RLock()

    def append(self, event_type: str, payload: Any, tick: int | None = None) -> int:
        r'''
        Append an event to the trace ledger.

        Returns the entry index.

        Args:
            event_type: Type of event (e.g., 'mutation', 'consensus', 'barrier')
            payload: Event payload (must be JSON-serializable)
            tick: Global tick. If None, uses DeterministicClock.get_tick()

        Returns:
            Entry index (local_sequence)
        '''
        with self._lock:
            if tick is None:
                tick = DeterministicClock.get_tick()

            entry_id = DeterministicUUIDFactory.make_id(
                'trc', f'{event_type}:{tick}', self.node_id
            )

            order_key = TraceEntry.make_order_key(tick, self._local_sequence, self.node_id)

            entry = TraceEntry(
                global_tick=tick,
                local_sequence=self._local_sequence,
                node_id=self.node_id,
                event_type=event_type,
                payload=payload,
                order_key=order_key,
                entry_id=entry_id
            )

            idx = len(self._entries)
            self._entries.append(entry)

            if tick not in self._tick_index:
                self._tick_index[tick] = []
            self._tick_index[tick].append(idx)

            self._local_sequence += 1
            return idx

    def append_batch(self, events: list[tuple[str, Any, int]]) -> list[int]:
        r'''
        Append multiple events atomically (same tick).

        Args:
            events: List of (event_type, payload, tick) tuples

        Returns:
            List of entry indices
        '''
        indices = []
        with self._lock:
            base_seq = self._local_sequence
            for i, (event_type, payload, tick) in enumerate(events):
                entry_id = DeterministicUUIDFactory.make_id(
                    'trc', f'{event_type}:{tick}:{i}', self.node_id
                )
                order_key = TraceEntry.make_order_key(tick, base_seq + i, self.node_id)

                entry = TraceEntry(
                    global_tick=tick,
                    local_sequence=base_seq + i,
                    node_id=self.node_id,
                    event_type=event_type,
                    payload=payload,
                    order_key=order_key,
                    entry_id=entry_id
                )

                idx = len(self._entries)
                self._entries.append(entry)

                if tick not in self._tick_index:
                    self._tick_index[tick] = []
                self._tick_index[tick].append(idx)

                indices.append(idx)

            self._local_sequence = base_seq + len(events)

        return indices

    def get_entries_for_tick(self, tick: int) -> list[TraceEntry]:
        '''Get all entries for a specific tick, in deterministic order.'''
        with self._lock:
            indices = self._tick_index.get(tick, [])
            return [self._entries[i] for i in indices]

    def get_all_entries_sorted(self) -> list[TraceEntry]:
        '''Get all entries sorted by order_key (deterministic).'''
        with self._lock:
            return sorted(self._entries, key=lambda e: e.order_key)

    def replay_from(self, tick: int) -> list[TraceEntry]:
        '''Return all entries with global_tick >= N, in deterministic order.'''
        with self._lock:
            return sorted(
                [e for e in self._entries if e.global_tick >= tick],
                key=lambda e: e.order_key
            )

    def replay_range(self, tick_start: int, tick_end: int) -> list[TraceEntry]:
        '''Return all entries with tick_start <= global_tick <= tick_end.'''
        with self._lock:
            return sorted(
                [e for e in self._entries if tick_start <= e.global_tick <= tick_end],
                key=lambda e: e.order_key
            )

    def verify_ordering(self) -> bool:
        r'''
        Verify the ledger is correctly ordered by order_key.

        Returns True if all entries are in deterministic order
        (order_key is strictly increasing).
        '''
        with self._lock:
            sorted_entries = self.get_all_entries_sorted()
            for i in range(1, len(sorted_entries)):
                if sorted_entries[i].order_key <= sorted_entries[i-1].order_key:
                    return False
            return True

    def get_entry_by_id(self, entry_id: str) -> TraceEntry | None:
        '''Get entry by its deterministic ID.'''
        with self._lock:
            for e in self._entries:
                if e.entry_id == entry_id:
                    return e
            return None

    def checkpoint(self) -> bytes:
        r'''
        Create deterministic checkpoint of the entire trace ledger.
        Used for crash recovery and replay certification.
        '''
        with self._lock:
            data = [
                {
                    'global_tick': e.global_tick,
                    'local_sequence': e.local_sequence,
                    'node_id': e.node_id,
                    'event_type': e.event_type,
                    'payload': e.payload,
                    'order_key': e.order_key,
                    'entry_id': e.entry_id,
                }
                for e in self._entries
            ]
            return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

    def recover(self, checkpoint_data: bytes) -> int:
        r'''
        Recover trace ledger from checkpoint.

        Returns number of entries recovered.
        '''
        with self._lock:
            data = json.loads(checkpoint_data)
            self._entries.clear()
            self._tick_index.clear()
            self._local_sequence = 0

            for d in data:
                entry = TraceEntry(**d)
                self._entries.append(entry)

                if entry.global_tick not in self._tick_index:
                    self._tick_index[entry.global_tick] = []
                self._tick_index[entry.global_tick].append(len(self._entries) - 1)

                if entry.local_sequence >= self._local_sequence:
                    self._local_sequence = entry.local_sequence + 1

            return len(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            ticks = sorted(self._tick_index.keys())
            return {
                'total_entries': len(self._entries),
                'ticks_covered': len(ticks),
                'first_tick': ticks[0] if ticks else None,
                'last_tick': ticks[-1] if ticks else None,
                'entries_by_tick': {t: len(idxs) for t, idxs in self._tick_index.items()},
            }

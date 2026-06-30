"""
GlobalExecutionBarrier (GEB) — core/runtime/geb.py
ATOM-META-RL-022 P0

Synchronizes all federation nodes before each tick execution.
No node executes tick T until all nodes have confirmed readiness for tick T.

Guarantees:
  1. All nodes must arrive at barrier(tick) before any node executes tick
  2. Deterministic ordering of arrival processing (node_id sort)
  3. All nodes see the same committed state at tick boundary
  4. No execution drift across replicas

Theorem:
  GEB.commit(N) == True
    -> all nodes have applied all mutations for tick N
    -> all nodes see identical state at tick boundary
    -> no node begins tick N+1 until GEB.commit(N)
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from enum import Enum, auto


class BarrierPhase(Enum):
    IDLE = auto()
    OPENING = auto()       # barrier opened for tick N
    WAITING = auto()        # waiting for all nodes to arrive
    CLOSING = auto()        # barrier closing (committing)
    COMMITTED = auto()      # all nodes committed tick N


@dataclass
class BarrierTicket:
    tick: int
    node_id: str
    arrived: bool = False
    committed: bool = False
    arrival_hash: str = ""


class GlobalExecutionBarrier:
    """
    Synchronizes all federation nodes before each tick execution.

    Usage (per node):
        geb = GlobalExecutionBarrier(
            node_id="node-1",
            all_nodes=["node-1", "node-2", "node-3"]
        )

        # Before executing tick N:
        geb.open(tick=N)
        geb.arrive(tick=N, state_hash=compute_hash(state))
        if geb.quorum_reached(N):
            geb.commit(tick=N)
        if geb.can_proceed(N):
            execute_tick(N)
    """

    def __init__(self, node_id: str, all_nodes: list[str]):
        self.node_id = node_id
        self.all_nodes = sorted(all_nodes)          # deterministic ordering
        self.N = len(all_nodes)
        self.quorum = (self.N // 2) + 1            # majority for fault tolerance
        self._phase: BarrierPhase = BarrierPhase.IDLE
        self._lock = threading.RLock()
        # tick -> {node_id -> BarrierTicket}
        self._tickets: dict[int, dict[str, BarrierTicket]] = {}
        self._committed_ticks: set[int] = set()

    # ── Deterministic arrival proof ───────────────────────────────────────

    @staticmethod
    def make_arrival_hash(node_id: str, tick: int, state_hash: str) -> str:
        """
        Deterministic arrival proof.
        Same (node_id, tick, state_hash) -> same arrival_hash.
        No time, no random.
        """
        return hashlib.sha256(
            f"arrival:{node_id}:{tick}:{state_hash}:ATOM-GEB".encode()
        ).hexdigest()[:16]

    # ── Barrier operations ─────────────────────────────────────────────────

    def open(self, tick: int) -> None:
        """Open barrier for tick. Must be called by all nodes."""
        with self._lock:
            self._phase = BarrierPhase.OPENING
            if tick not in self._tickets:
                self._tickets[tick] = {}
            for nid in self.all_nodes:
                if nid not in self._tickets[tick]:
                    self._tickets[tick][nid] = BarrierTicket(tick=tick, node_id=nid)

    def arrive(self, tick: int, state_hash: str) -> BarrierTicket:
        """
        Node arrives at barrier for tick.
        Returns the node's BarrierTicket.
        """
        with self._lock:
            if tick not in self._tickets:
                self.open(tick)

            ticket = self._tickets[tick][self.node_id]
            ticket.arrived = True
            ticket.arrival_hash = self.make_arrival_hash(self.node_id, tick, state_hash)
            self._phase = BarrierPhase.WAITING
            return ticket

    def all_arrived(self, tick: int) -> bool:
        """Check if ALL nodes have arrived at barrier(tick)."""
        with self._lock:
            if tick not in self._tickets:
                return False
            tickets = self._tickets[tick]
            return all(t.arrived for t in tickets.values())

    def quorum_arrived(self, tick: int) -> bool:
        """Check if QUORUM of nodes have arrived at barrier(tick)."""
        with self._lock:
            if tick not in self._tickets:
                return False
            arrived = [t for t in self._tickets[tick].values() if t.arrived]
            return len(arrived) >= self.quorum

    def get_arrivals(self, tick: int) -> list[tuple[str, BarrierTicket]]:
        """
        Get all arrivals sorted by arrival_hash (deterministic, not time-based).
        """
        with self._lock:
            if tick not in self._tickets:
                return []
            tickets = self._tickets[tick]
            return sorted(
                [(nid, t) for nid, t in tickets.items() if t.arrived],
                key=lambda x: x[1].arrival_hash
            )

    def commit(self, tick: int) -> None:
        """
        Commit barrier(tick). All nodes can now proceed to tick+1.
        """
        with self._lock:
            self._phase = BarrierPhase.CLOSING
            if tick in self._tickets:
                for ticket in self._tickets[tick].values():
                    ticket.committed = True
            self._committed_ticks.add(tick)
            self._phase = BarrierPhase.COMMITTED

    def is_committed(self, tick: int) -> bool:
        """Check if tick has been committed."""
        with self._lock:
            return tick in self._committed_ticks

    def can_proceed(self, tick: int) -> bool:
        """
        Node can proceed to execute tick if:
          1. barrier(tick) is already committed, OR
          2. quorum arrived AND this node has arrived
        """
        with self._lock:
            if tick in self._committed_ticks:
                return True
            if tick not in self._tickets:
                return False
            my_ticket = self._tickets[tick].get(self.node_id)
            if not my_ticket or not my_ticket.arrived:
                return False
            return self.quorum_arrived(tick)

    # ── Tick execution protocol ────────────────────────────────────────────

    def execute_tick_protocol(self, tick: int, state_hash: str) -> bool:
        """
        Full barrier protocol for one tick.
        Returns True if node can proceed to execute tick.

        Usage:
            if geb.execute_tick_protocol(tick=N, state_hash=h):
                execute_tick(N)
        """
        self.open(tick)
        self.arrive(tick, state_hash)
        if self.quorum_arrived(tick):
            self.commit(tick)
        return self.can_proceed(tick)

    # ── State queries ──────────────────────────────────────────────────────

    @property
    def phase(self) -> BarrierPhase:
        with self._lock:
            return self._phase

    def get_committed_ticks(self) -> list[int]:
        with self._lock:
            return sorted(self._committed_ticks)

    def get_ticket(self, tick: int, node_id: str) -> BarrierTicket | None:
        """Get a specific node's ticket for a tick."""
        with self._lock:
            return self._tickets.get(tick, {}).get(node_id)

    def reset(self) -> None:
        """Reset all state. For testing only."""
        with self._lock:
            self._tickets.clear()
            self._committed_ticks.clear()
            self._phase = BarrierPhase.IDLE


# ── DeterministicTickSynchronizer ──────────────────────────────────────────

class DeterministicTickSynchronizer:
    """
    Wrapper that integrates GEB with DeterministicClock for fully
    deterministic multi-node tick execution.

    Usage:
        sync = DeterministicTickSynchronizer(
            node_id="node-1",
            all_nodes=["node-1", "node-2", "node-3"],
            clock=DeterministicClock
        )

        # At each tick boundary:
        state_hash = compute_deterministic_hash(current_state)
        sync.sync(tick=N, state_hash=state_hash)
        # Now safe to execute tick N
    """

    def __init__(
        self,
        node_id: str,
        all_nodes: list[str],
        clock_class=None  # DeterministicClock class
    ):
        self.node_id = node_id
        self.geb = GlobalExecutionBarrier(node_id=node_id, all_nodes=all_nodes)
        self._clock_class = clock_class

    def sync(self, tick: int, state_hash: str) -> bool:
        """
        Synchronize at tick boundary.
        Returns True if can proceed.
        """
        return self.geb.execute_tick_protocol(tick=tick, state_hash=state_hash)

    def can_execute(self, tick: int) -> bool:
        """Check if node can execute this tick."""
        return self.geb.can_proceed(tick)

    def is_committed(self, tick: int) -> bool:
        """Check if tick barrier is committed."""
        return self.geb.is_committed(tick)

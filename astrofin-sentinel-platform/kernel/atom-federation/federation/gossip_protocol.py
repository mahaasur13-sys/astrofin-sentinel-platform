"""GossipProtocol — partial async state exchange between nodes.

No blocking RPC. Each node periodically pushes its StateVector to a subset
of peers and pulls their vectors. Merge is done by the caller via
ConsensusResolver.
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from core.deterministic import DeterministicClock
from federation.state_vector import StateVector


@dataclass
class GossipConfig:
    fanout: int = 3           # max peers per push
    push_interval_ms: int = 2000
    pull_interval_ms: int = 5000
    stale_threshold_ms: int = 30_000
    max_history: int = 100    # per node


@dataclass
class PeerRecord:
    node_id: str
    last_push_ns: int = 0
    last_pull_ns: int = 0
    vector: StateVector | None = None
    vector_history: deque = field(default_factory=lambda: deque(maxlen=100))


class GossipProtocol:
    """Async partial-sync gossip. Callbacks on new vector arrival."""

    def __init__(
        self,
        node_id: str,
        config: GossipConfig | None = None,
        on_vector: Callable[[StateVector], None] | None = None,
    ):
        self.node_id = node_id
        self.config = config or GossipConfig()
        self._on_vector = on_vector
        self._peers: dict[str, PeerRecord] = {}
        self._running = False
        self._push_task: asyncio.Task | None = None
        self._pull_task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    # peer management                                                     #
    # ------------------------------------------------------------------ #

    def register_peer(self, node_id: str) -> None:
        if node_id not in self._peers:
            self._peers[node_id] = PeerRecord(node_id=node_id)

    def unregister_peer(self, node_id: str) -> None:
        self._peers.pop(node_id, None)

    @property
    def peer_ids(self) -> list[str]:
        return list(self._peers.keys())

    # ------------------------------------------------------------------ #
    # manual sync (called by external scheduler)                         #
    # ------------------------------------------------------------------ #

    def push(self, my_vector: StateVector) -> list[tuple[str, StateVector | None]]:
        """Push my_vector to a random subset of peers. Returns [(peer_id, their_vector)]."""
        available = [pid for pid in self._peers if pid != self.node_id]
        if not available:
            return []
        k = min(self.config.fanout, len(available))
        selected = sorted(available)[:k]
        results = []
        for pid in selected:
            self._peers[pid].last_push_ns = DeterministicClock.get_tick_ns()
            # Simulate network delivery — peer updates their state
            # caller is responsible for invoking receive_push
            results.append((pid, self._peers[pid].vector))
        return results

    def receive_push(
        self, remote_vector: StateVector
    ) -> StateVector | None:
        """Merge incoming push. Returns merged vector for local application."""
        peer = self._peers.get(remote_vector.node_id)
        if peer is None:
            return None

        now_ns = DeterministicClock.get_tick_ns()
        peer.last_push_ns = now_ns

        # History tracking — always append for audit trail
        peer.vector_history.append(remote_vector)

        # Only update current vector if incoming is fresher
        if (
            peer.vector is None
            or remote_vector.timestamp_ns > peer.vector.timestamp_ns
        ):
            peer.vector = remote_vector

        if self._on_vector:
            self._on_vector(remote_vector)

        return peer.vector

    def pull(self, peer_id: str) -> StateVector | None:
        """Pull latest from a specific peer."""
        peer = self._peers.get(peer_id)
        if peer is None:
            return None
        peer.last_pull_ns = DeterministicClock.get_tick_ns()
        return peer.vector

    def receive_pull_response(
        self, remote_vector: StateVector
    ) -> StateVector | None:
        """Handle peer's response to our pull request."""
        peer = self._peers.get(remote_vector.node_id)
        if peer is None:
            return None

        peer.last_pull_ns = DeterministicClock.get_tick_ns()
        peer.vector_history.append(remote_vector)
        peer.vector = remote_vector

        if self._on_vector:
            self._on_vector(remote_vector)

        return remote_vector

    # ------------------------------------------------------------------ #
    # lifecycle                                                          #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        self._running = True
        self._push_task = asyncio.create_task(self._push_loop())
        self._pull_task = asyncio.create_task(self._pull_loop())

    async def stop(self) -> None:
        self._running = False
        for t in self._push_task, self._pull_task:
            if t:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass

    async def _push_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.config.push_interval_ms / 1000)

    async def _pull_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.config.pull_interval_ms / 1000)

    # ------------------------------------------------------------------ #
    # query                                                              #
    # ------------------------------------------------------------------ #

    def get_all_vectors(self) -> list[StateVector]:
        return [p.vector for p in self._peers.values() if p.vector is not None]

    def get_fresh_vectors(self, max_age_ms: int | None = None) -> list[StateVector]:
        max_age_ms = max_age_ms or self.config.stale_threshold_ms
        cutoff_ns = DeterministicClock.get_tick_ns() - (max_age_ms * 1_000_000)
        return [
            p.vector
            for p in self._peers.values()
            if p.vector is not None and p.vector.timestamp_ns >= cutoff_ns
        ]

    def is_stale_peer(self, peer_id: str) -> bool:
        peer = self._peers.get(peer_id)
        if not peer or not peer.vector:
            return True
        return peer.vector.is_stale(self.config.stale_threshold_ms)

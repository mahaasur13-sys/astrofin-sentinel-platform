"""
DeltaRouter — delta routing and sequence tracking.

Tracks per-peer fingerprint sequences for selective propagation.
Key insight: routing decisions use root_hash equality, not full state.

Routing table:
  node_id → { root_hash → { seq, changed_ids, ttl, last_seen_ns } }

On push:
  1. Compute my root_hash
  2. For each peer, check if peer.last_root_hash == my_root_hash
  3. If equal → skip (peer already has this state)
  4. If not equal → send delta only (changed node IDs + hashes)

This turns O(n·k) full-state fanout into O(k) routing decisions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RouteEntry:
    """Single routing entry for a node's fingerprint."""
    node_id: str
    root_hash: str
    seq: int
    changed_ids: list[str]
    ts_ns: int = field(default_factory=lambda: time.time_ns())
    ttl_ms: int = 60_000

    def is_expired(self) -> bool:
        return (time.time_ns() - self.ts_ns) // 1_000_000 > self.ttl_ms


@dataclass
class RoutePeerSummary:
    """Summarises what a peer knows about all nodes."""
    node_id: str
    latest_seq: int
    latest_root_hash: str
    entry_count: int


class DeltaRouter:
    """
    Routing index for delta gossip.

    Provides O(1) lookup: given my root_hash, which peers need this delta?

    Routing logic:
      - If peer.last_root_hash == my_root_hash → peer is in sync, skip
      - If peer.last_root_hash != my_root_hash → peer diverged, send delta

    This eliminates full-state fanout: we only push deltas to out-of-sync peers.
    """

    def __init__(self):
        # node_id → root_hash → RouteEntry
        self._table: dict[str, dict[str, RouteEntry]] = {}
        # node_id → latest (seq, root_hash) for quick comparison
        self._latest: dict[str, tuple[int, str]] = {}

    # ── registration ─────────────────────────────────────────────

    def register_node(self, node_id: str, root_hash: str, seq: int, changed_ids: list[str]) -> None:
        """Register or update what a node knows about itself."""
        if node_id not in self._table:
            self._table[node_id] = {}

        entry = RouteEntry(
            node_id=node_id,
            root_hash=root_hash,
            seq=seq,
            changed_ids=list(changed_ids),
        )
        self._table[node_id][root_hash] = entry
        self._latest[node_id] = (seq, root_hash)

    def update_peer_fingerprint(
        self,
        peer_id: str,
        root_hash: str,
        seq: int,
        changed_ids: list[str] | None = None,
    ) -> None:
        """
        Update what we know about a peer's DAG fingerprint.

        Called when we receive a DeltaGossipMessage from a peer.
        """
        if changed_ids is None:
            changed_ids = []
        self.register_node(peer_id, root_hash, seq, changed_ids)

    # ── routing decisions ─────────────────────────────────────────

    def peers_needing_delta(self, my_root_hash: str, exclude: list[str] | None = None) -> list[str]:
        """
        Return list of peer IDs whose latest fingerprint differs from my_root_hash.

        This is the core O(n) → O(1) routing optimization:
          - OLD: push to ALL fanout peers regardless of state
          - NEW: push only to peers where root_hash differs
        """
        exclude = set(exclude or [])
        result = []

        for node_id, (seq, root_hash) in self._latest.items():
            if node_id in exclude:
                continue
            if node_id == my_root_hash:   # self
                continue
            if root_hash != my_root_hash:
                result.append(node_id)

        return result

    def peer_fingerprint(self, peer_id: str) -> tuple[int, str] | None:
        """Return (seq, root_hash) for a peer, or None if unknown."""
        return self._latest.get(peer_id)

    # ── stale detection ──────────────────────────────────────────

    def mark_stale(self, node_id: str) -> None:
        """Mark a peer as stale (no updates recently)."""
        if node_id in self._latest:
            seq, rh = self._latest[node_id]
            if node_id in self._table and rh in self._table[node_id]:
                self._table[node_id][rh].stale = True

    def get_stale_peers(self, max_idle_ms: int = 60_000) -> list[str]:
        """Return peer IDs with no update in max_idle_ms."""
        cutoff_ns = time.time_ns() - (max_idle_ms * 1_000_000)
        stale = []
        for nid, entries in self._table.items():
            for entry in entries.values():
                if entry.ts_ns < cutoff_ns:
                    stale.append(nid)
                    break
        return stale

    # ── query ────────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "tracked_nodes": len(self._latest),
            "latest": {
                nid: {"seq": s, "root_hash": rh[:8]}
                for nid, (s, rh) in self._latest.items()
            },
        }

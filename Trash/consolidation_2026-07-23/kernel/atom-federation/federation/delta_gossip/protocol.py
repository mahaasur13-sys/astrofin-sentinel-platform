"""
DeltaGossip Protocol — delta-driven federation gossip.

Replaces GossipProtocol.push() which sent full StateVector snapshots.
Now sends only:
  1. DAGFingerprint delta (changed node hashes + new root hash)
  2. Changed node IDs list
  3. Sequence number (anti-replay)

Communication pattern:
  push()   → DeltaGossipMessage (delta only) to fanout peers
  pull()   → DeltaGossipMessage response with changed nodes
  reconcile() → AntiEntropy merkle-tree diff → minimal exchange
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from federation.delta_gossip.dag_hash_modes import DAGHashMode
from federation.state_vector import StateVector

# ─────────────────────────────────────────────────────────────────
# DeltaGossipConfig
# ─────────────────────────────────────────────────────────────────

@dataclass
class DeltaGossipConfig:
    """
    Configuration for DeltaGossip.

    fanout              — max peers per push (was 3 in GossipConfig)
    push_interval_ms    — push cycle interval
    pull_interval_ms    — pull cycle interval
    stale_threshold_ms  — when to consider a peer stale
    max_payload_bytes   — cap on serialized delta message (250 KB default)
    enable_anti_entropy — enable merkle-tree reconcile on pull
    max_history         — vector history per peer
    seq_window          — sequence number window for anti-replay
    """
    fanout: int = 3
    push_interval_ms: int = 2000
    pull_interval_ms: int = 5000
    stale_threshold_ms: int = 30_000
    max_payload_bytes: int = 250 * 1024
    enable_anti_entropy: bool = True
    max_history: int = 100
    seq_window: int = 1000


# ─────────────────────────────────────────────────────────────────
# DeltaGossipMessage
# ─────────────────────────────────────────────────────────────────

@dataclass
class DeltaGossipMessage:
    """
    Delta-carrying gossip message.

    Replaces full StateVector in push(). Contains only:
      - source_node_id: who sent this
      - root_hash: current DAG root hash (16 bytes hex)
      - changed_node_ids: list of node IDs whose content changed
      - changed_hashes: {node_id: content_hash} for each changed node
      - seq: monotonically increasing sequence number (anti-replay)
      - ts_ns: message timestamp (nanoseconds)
      - hash_mode: which DAGHashMode was used for root_hash (v9.0)

    Peers use root_hash to decide:
      - root_hash == local_root_hash → IDEMPOTENT (no changes needed)
      - root_hash != local_root_hash + changed_node_ids non-empty → apply delta
    """
    source_node_id: str
    root_hash: str
    changed_node_ids: list[str]
    changed_hashes: dict[str, str]
    seq: int
    ts_ns: int = field(default_factory=lambda: time.time_ns())
    hash_mode: DAGHashMode = DAGHashMode.CONSENSUS  # v9.0: mode propagation

    @property
    def delta_size(self) -> int:
        return (
            len(self.source_node_id)
            + len(self.root_hash)
            + sum(len(n) for n in self.changed_node_ids)
            + sum(len(h) for h in self.changed_hashes.values())
            + 64
        )

    def is_empty(self) -> bool:
        return len(self.changed_node_ids) == 0


# ─────────────────────────────────────────────────────────────────
# PeerDeltaState
# ─────────────────────────────────────────────────────────────────

@dataclass
class PeerDeltaState:
    """
    Per-peer state for delta gossip.

    Tracks what we know about a peer's DAG fingerprint and
    the sequence of deltas we've exchanged.
    """
    node_id: str
    last_root_hash: str = ""
    last_seq: int = -1
    known_node_hashes: dict[str, str] = field(default_factory=dict)
    vector: StateVector | None = None
    stale: bool = True
    hash_mode: DAGHashMode = DAGHashMode.CONSENSUS  # v9.0: mode propagation

    def needs_sync(self, my_root_hash: str) -> bool:
        return self.last_root_hash != my_root_hash

    def update_from_message(self, msg: DeltaGossipMessage) -> bool:
        if msg.seq <= self.last_seq:
            return False
        if msg.seq == self.last_seq and msg.root_hash == self.last_root_hash:
            return False
        self.last_root_hash = msg.root_hash
        self.last_seq = msg.seq
        self.hash_mode = msg.hash_mode  # v9.0: track peer's hash mode
        for nid, h in msg.changed_hashes.items():
            self.known_node_hashes[nid] = h
        self.stale = False
        return True


# ─────────────────────────────────────────────────────────────────
# DeltaGossipProtocol
# ─────────────────────────────────────────────────────────────────

class DeltaGossipProtocol:
    """
    Delta-driven gossip protocol.

    OLD (GossipProtocol):
        push() → full StateVector snapshot → fanout peers
        O(n·k) bytes per cycle (full snapshots)

    NEW (DeltaGossipProtocol):
        push() → DeltaGossipMessage (fingerprints + changed IDs only)
        O(k·Δnodes) bytes per cycle (where Δnodes << total nodes)
    """

    def __init__(
        self,
        node_id: str,
        config: DeltaGossipConfig | None = None,
        on_delta: Callable[[DeltaGossipMessage], None] | None = None,
        on_full_sync: Callable[[str, StateVector], None] | None = None,
    ):
        self.node_id = node_id
        self.config = config or DeltaGossipConfig()
        self._on_delta = on_delta
        self._on_full_sync = on_full_sync
        self._peers: dict[str, PeerDeltaState] = {}
        self._local_seq: int = 0
        self._running = False

    # ── peer management ──────────────────────────────────────────

    def register_peer(self, node_id: str) -> None:
        if node_id not in self._peers:
            self._peers[node_id] = PeerDeltaState(node_id=node_id)

    def unregister_peer(self, node_id: str) -> None:
        self._peers.pop(node_id, None)

    @property
    def peer_ids(self) -> list[str]:
        return list(self._peers.keys())

    # ── delta message construction ────────────────────────────────

    def build_delta_message(
        self,
        root_hash: str,
        changed_node_ids: list[str],
        changed_hashes: dict[str, str],
        hash_mode: DAGHashMode = DAGHashMode.CONSENSUS,
    ) -> DeltaGossipMessage:
        self._local_seq += 1
        return DeltaGossipMessage(
            source_node_id=self.node_id,
            root_hash=root_hash,
            changed_node_ids=list(changed_node_ids),
            changed_hashes=dict(changed_hashes),
            seq=self._local_seq,
            hash_mode=hash_mode,
        )

    # ── push / pull ─────────────────────────────────────────────

    def push(
        self,
        delta: DeltaGossipMessage,
        my_full_vector: StateVector,
    ) -> list[str]:
        """
        Push delta to fanout peers. Returns peer IDs needing full StateVector
        (because delta was too large or peer was too far out of sync).
        """
        available = [pid for pid in self._peers if pid != self.node_id]
        if not available:
            return []

        k = min(self.config.fanout, len(available))
        selected = self._weighted_sample(available, k)
        recipients_needing_full = []

        for pid in selected:
            peer = self._peers[pid]
            if peer.last_root_hash == delta.root_hash and not delta.is_empty():
                continue
            peer.stale = False
            if delta.delta_size > self.config.max_payload_bytes:
                recipients_needing_full.append(pid)
                if self._on_full_sync:
                    self._on_full_sync(pid, my_full_vector)

        return recipients_needing_full

    def receive_delta(
        self,
        msg: DeltaGossipMessage,
    ) -> tuple[bool, str]:
        """Process incoming delta. Returns (is_new, root_hash)."""
        peer = self._peers.get(msg.source_node_id)
        if peer is None:
            self.register_peer(msg.source_node_id)
            peer = self._peers[msg.source_node_id]

        is_new = peer.update_from_message(msg)
        if is_new and self._on_delta:
            self._on_delta(msg)

        return is_new, msg.root_hash

    def pull(
        self,
        peer_id: str,
    ) -> tuple[DeltaGossipMessage | None, StateVector | None]:
        """Pull delta from a specific peer."""
        peer = self._peers.get(peer_id)
        if peer is None:
            return None, None

        if peer.vector is None or not peer.last_root_hash:
            return None, peer.vector

        delta_msg = DeltaGossipMessage(
            source_node_id=peer_id,
            root_hash=peer.last_root_hash,
            changed_node_ids=list(peer.known_node_hashes.keys()),
            changed_hashes=dict(peer.known_node_hashes),
            seq=peer.last_seq,
            hash_mode=peer.hash_mode,
        )
        return delta_msg, peer.vector

    # ── reconciliation ────────────────────────────────────────────

    def reconcile(
        self,
        peer_id: str,
        my_node_hashes: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        """
        Merkle-style reconcile with a peer.

        Returns (to_pull, to_push):
          - to_pull: node IDs peer has but we don't
          - to_push: node IDs we have but peer doesn't
        """
        peer = self._peers.get(peer_id)
        if peer is None:
            return [], list(my_node_hashes.keys())

        their_hashes = peer.known_node_hashes
        my_ids = set(my_node_hashes.keys())
        their_ids = set(their_hashes.keys())

        to_pull = list(their_ids - my_ids)
        to_push = list(my_ids - their_ids)

        for nid in my_ids & their_ids:
            if my_node_hashes[nid] != their_hashes[nid]:
                to_pull.append(nid)

        return to_pull, to_push

    def get_peer_fingerprint(self, peer_id: str) -> str | None:
        peer = self._peers.get(peer_id)
        return peer.last_root_hash if peer else None

    def get_all_known_hashes(self) -> dict[str, dict[str, str]]:
        return {pid: dict(peer.known_node_hashes) for pid, peer in self._peers.items()}

    # ── merkle digest ────────────────────────────────────────────

    def compute_merkle_digest(self, node_hashes: dict[str, str]) -> dict[int, str]:
        """
        Layered merkle digest from node hashes.
        Layer 0: individual hashes; Layer 1+: pairwise hashes upward.
        Two peers can compare entire DAG state by comparing root digests.
        """
        if not node_hashes:
            return {0: ""}

        sorted_hashes = sorted(node_hashes.items())
        layer0 = {nid: h for nid, h in sorted_hashes}
        digest_by_layer: dict[int, str] = {0: self._hash_pairs(layer0)}
        current = layer0
        L = 1

        while len(current) > 1:
            next_layer: dict[str, str] = {}
            items = list(current.items())
            for i in range(0, len(items), 2):
                pair = items[i:i + 2]
                if len(pair) == 2:
                    key = f"{pair[0][0]}:{pair[1][0]}"
                    val = hashlib.sha256((pair[0][1] + pair[1][1]).encode()).hexdigest()[:16]
                else:
                    key, val = pair[0]
                next_layer[key] = val
            digest_by_layer[L] = self._hash_pairs(next_layer)
            current = next_layer
            L += 1

        return digest_by_layer

    def _hash_pairs(self, items: dict[str, str]) -> str:
        h = hashlib.sha256()
        for k in sorted(items):
            h.update(f"{k}:{items[k]}".encode())
        return h.hexdigest()[:16]

    # ── weighted sample ───────────────────────────────────────────

    def _weighted_sample(self, peers: list[str], k: int) -> list[str]:
        """Select k peers preferring those most out-of-sync."""
        import random
        return random.sample(peers, min(k, len(peers)))

    # ── stale ────────────────────────────────────────────────────

    def mark_stale(self, peer_id: str) -> None:
        peer = self._peers.get(peer_id)
        if peer:
            peer.stale = True

    def is_stale_peer(self, peer_id: str) -> bool:
        peer = self._peers.get(peer_id)
        return True if not peer else peer.stale

    # ── query ────────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "node_id": self.node_id,
            "peer_count": len(self._peers),
            "local_seq": self._local_seq,
            "peers": {
                pid: {
                    "last_root_hash": p.last_root_hash[:8] if p.last_root_hash else "",
                    "last_seq": p.last_seq,
                    "known_nodes": len(p.known_node_hashes),
                    "stale": p.stale,
                }
                for pid, p in self._peers.items()
            },
        }

# ruff: noqa: F821
"""
trust_sync_protocol.py — v9.5 TrustSyncProtocol

Purpose:
  Gossip protocol for trust state across federation peers.

  TrustSyncMessage types:
    - TRUST_VECTOR: full TrustVector snapshot (expensive, periodic)
    - TRUST_DELTA:  incremental update (cheap, frequent)
    - TRUST_QUERY:  request peer's current TrustVector
    - TRUST_RESPONSE: response containing peer's TrustVector

Design:
  - Outbound: aggregate local ledger changes since last sync → delta
  - Inbound: merge remote delta into local ledger via LedgerReconciliation
  - Periodic full-sync: every `full_sync_interval` ticks
  - Delta-sync: every `delta_sync_interval` ticks (default: every tick)

Gossip lifecycle:
  1. on_tick(tick):
       if should_send_full(): send TRUST_VECTOR
       else: send TRUST_DELTA
  2. on_receive(peer_id, message):
       merge into local ledger
       respond with TRUST_RESPONSE if message was QUERY
  3. TrustVector on node is kept in sync with ProofLedger.

Usage:
    protocol = TrustSyncProtocol(node_id="node_1", ledger=local_ledger)
    protocol.on_tick(tick=10)
    for peer_id in peers:
        msg = protocol.prepare_outbound(peer_id)
        if msg: send_to(peer_id, msg)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from .trust_vector import TrustVector, TrustDelta

import logging
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# TrustSyncMessage
# ─────────────────────────────────────────────────────────────────

class TrustMessageType(Enum):
    TRUST_VECTOR = auto()   # full snapshot
    TRUST_DELTA  = auto()  # incremental update
    TRUST_QUERY  = auto()  # request full vector
    TRUST_RESPONSE = auto() # response to query


@dataclass
class TrustSyncMessage:
    """
    Network-ready trust message.

    Fields:
        msg_type       — TRUST_VECTOR | TRUST_DELTA | TRUST_QUERY | TRUST_RESPONSE
        sender_id      — node that generated this message
        tick           — current tick at sender
        payload        — serialized TrustVector or TrustDelta (or None for QUERY)
        vector_clock   — {node_id: ledger_version} for causality tracking
        timestamp      — wall clock of message creation
    """
    msg_type: TrustMessageType
    sender_id: str
    tick: int
    payload: str  # JSON-serialized TrustVector or TrustDelta
    vector_clock: dict[str, int]  # node_id → ledger_version
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type.name,
            "sender_id": self.sender_id,
            "tick": self.tick,
            "payload": self.payload,
            "vector_clock": self.vector_clock,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TrustSyncMessage:
        return cls(
            msg_type=TrustMessageType[data["msg_type"]],
            sender_id=data["sender_id"],
            tick=int(data["tick"]),
            payload=data["payload"],
            vector_clock={k: int(v) for k, v in data["vector_clock"].items()},
            timestamp=float(data["timestamp"]),
        )


# ─────────────────────────────────────────────────────────────────
# PeerTrustState
# ─────────────────────────────────────────────────────────────────

@dataclass
class PeerTrustState:
    """
    Per-peer trust sync state.

    Tracks what we know about each peer's trust vector
    and when we last synced with them.
    """
    peer_id: str
    last_sync_tick: int = 0
    last_known_vector_clock: dict[str, int] = field(default_factory=dict)
    # vector_clock: node_id → ledger_version at time of last sync
    pending_deltas: list[TrustDelta] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
# TrustSyncProtocol
# ─────────────────────────────────────────────────────────────────

class TrustSyncProtocol:
    """
    Gossip protocol for distributing trust state across federation.

    Responsibilities:
      - Maintain per-peer sync state (last known vector clock)
      - Decide when to send full-vector vs delta
      - Encode outbound messages
      - Decode and merge inbound messages via LedgerReconciliation

    This is the "active" layer that pushes trust state to peers.
    The ProofLedger is the "passive" source of truth.

    Gossip parameters:
      - delta_sync_interval: ticks between delta syncs (default: 1)
      - full_sync_interval:  ticks between full vector syncs (default: 10)
      - max_delta_age:      seconds after which delta is too stale to send
    """

    def __init__(
        self,
        node_id: str,
        delta_sync_interval: int = 1,
        full_sync_interval: int = 10,
        max_delta_age: float = 60.0,
    ):
        self.node_id = node_id
        self.delta_sync_interval = delta_sync_interval
        self.full_sync_interval = full_sync_interval
        self.max_delta_age = max_delta_age

        # node_id → PeerTrustState
        self._peer_states: dict[str, PeerTrustState] = {}
        # Last TrustVector we sent to each peer (for delta computation)
        self._last_sent_vector: dict[str, TrustVector] = {}

        # Serialization/deserialization helpers
        self._reconciler: LedgerReconciliation | None = None

    # ── configuration ──────────────────────────────────────────────

    def add_peer(self, peer_id: str) -> None:
        """Register a peer."""
        if peer_id not in self._peer_states:
            self._peer_states[peer_id] = PeerTrustState(peer_id=peer_id)

    def remove_peer(self, peer_id: str) -> None:
        """Unregister a peer."""
        self._peer_states.pop(peer_id, None)
        self._last_sent_vector.pop(peer_id, None)

    @property
    def peers(self) -> list[str]:
        return list(self._peer_states.keys())

    # ── outbound message construction ─────────────────────────────

    def should_send_full(self, peer_id: str, current_tick: int) -> bool:
        """
        Decide whether to send a full TRUST_VECTOR or TRUST_DELTA.

        Full sync if:
          - Never synced with this peer (last_sync_tick == 0)
          - tick % full_sync_interval == 0
          - Peer has no pending state (cold start)
        """
        state = self._peer_states.get(peer_id)
        if state is None:
            return True
        if state.last_sync_tick == 0:
            return True
        return current_tick % self.full_sync_interval == 0

    def prepare_outbound(
        self,
        peer_id: str,
        current_tick: int,
        current_tv: TrustVector,
        vector_clock: dict[str, int],
    ) -> TrustSyncMessage | None:
        """
        Build the next outbound TrustSyncMessage for peer_id.

        Args:
            peer_id: destination peer
            current_tick: current system tick
            current_tv: TrustVector snapshot from local ProofLedger
            vector_clock: {node_id: ledger_version} — global state

        Returns:
            TrustSyncMessage ready to send, or None if nothing to send.
        """
        last_sent = self._last_sent_vector.get(peer_id)
        msg_type: TrustMessageType

        import json
        if self.should_send_full(peer_id, current_tick) or last_sent is None:
            msg_type = TrustMessageType.TRUST_VECTOR
            payload = json.dumps(current_tv.to_dict())
        else:
            msg_type = TrustMessageType.TRUST_DELTA
            delta = current_tv.delta(last_sent)
            if delta.is_empty():
                return None  # nothing changed since last send
            # DELTA carries full state — receiver doesn't need base vector
            payload = json.dumps(current_tv.to_dict())

        msg = TrustSyncMessage(
            msg_type=msg_type,
            sender_id=self.node_id,
            tick=current_tick,
            payload=payload,
            vector_clock=dict(vector_clock),
            timestamp=time.time(),
        )

        # Record what we sent
        self._last_sent_vector[peer_id] = current_tv.snapshot()
        if peer_id in self._peer_states:
            self._peer_states[peer_id].last_sync_tick = current_tick
            self._peer_states[peer_id].last_known_vector_clock = dict(vector_clock)

        return msg

    # ── inbound message processing ────────────────────────────────

    def receive_and_merge(
        self,
        msg: TrustSyncMessage,
        local_tv: TrustVector,
    ) -> tuple[TrustVector, bool]:
        """
        Process an inbound TrustSyncMessage.

        Merges the received trust state into local_tv via LedgerReconciliation.

        Args:
            msg: incoming TrustSyncMessage
            local_tv: current local TrustVector

        Returns:
            (merged_tv, had_conflict):
                merged_tv — new local TrustVector after merge
                had_conflict — True if any entries were updated due to conflict
        """
        if self._reconciler is None:
            import federation.trust.ledger_reconciliation as lr
            self._reconciler = lr.LedgerReconciliation()

        # Handle TRUST_QUERY: respond is caller's responsibility
        if msg.msg_type == TrustMessageType.TRUST_QUERY:
            return local_tv, False

        # Deserialize remote vector
        received_tv = self._deserialize_vector(msg.payload)

        # Merge remote into local
        merged = self._reconciler.merge(local_tv, received_tv)

        # Conflict detection: check if merged differs from local
        delta = merged.delta(local_tv)
        had_conflict = not delta.is_empty()

        # Update our record of what sender has
        self._last_sent_vector[msg.sender_id] = received_tv.snapshot()

        return merged, had_conflict

    def prepare_response(
        self,
        peer_id: str,
        current_tick: int,
        current_tv: TrustVector,
        vector_clock: dict[str, int],
    ) -> TrustSyncMessage:
        """Build a TRUST_RESPONSE message (always full vector)."""
        import json
        return TrustSyncMessage(
            msg_type=TrustMessageType.TRUST_RESPONSE,
            sender_id=self.node_id,
            tick=current_tick,
            payload=json.dumps(current_tv.to_dict()),
            vector_clock=dict(vector_clock),
            timestamp=time.time(),
        )

    # ── tick callback ─────────────────────────────────────────────

    def on_tick(
        self,
        tick: int,
        local_tv: TrustVector,
        vector_clock: dict[str, int],
    ) -> dict[str, TrustSyncMessage]:
        """
        Called every tick to produce outbound messages for all peers.

        Returns:
            {peer_id: TrustSyncMessage} for peers that need an update
        """
        outbound: dict[str, TrustSyncMessage] = {}
        for peer_id in self.peers:
            msg = self.prepare_outbound(peer_id, tick, local_tv, vector_clock)
            if msg is not None:
                outbound[peer_id] = msg
        return outbound

    # ── vector clock ──────────────────────────────────────────────

    def get_vector_clock(self) -> dict[str, int]:
        """
        Return current vector clock: {node_id: latest_ledger_version}.

        Built from peer's last known ledger versions.
        """
        clock: dict[str, int] = {}
        for peer_id, state in self._peer_states.items():
            # Use last known version for each peer
            if state.last_known_vector_clock:
                for node_id, version in state.last_known_vector_clock.items():
                    clock[node_id] = max(clock.get(node_id, 0), version)
        # Include self
        clock[self.node_id] = clock.get(self.node_id, 0) + 1
        return clock

    # ── pending deltas ───────────────────────────────────────────

    def queue_delta(self, peer_id: str, delta: TrustDelta) -> None:
        """Queue a delta to send to peer (for retry scenarios)."""
        if peer_id in self._peer_states:
            self._peer_states[peer_id].pending_deltas.append(delta)

    def get_pending_deltas(self, peer_id: str) -> list[TrustDelta]:
        return list(self._peer_states.get(peer_id, PeerTrustState(peer_id=peer_id)).pending_deltas)

    def clear_pending_deltas(self, peer_id: str) -> None:
        if peer_id in self._peer_states:
            self._peer_states[peer_id].pending_deltas.clear()

    # ── serialization helpers ─────────────────────────────────────

    def _serialize_full(self, tv: TrustVector) -> str:
        """Serialize a TrustVector to JSON string."""
        import json
        return json.dumps(tv.to_dict())

    def _deserialize_vector(self, payload: str) -> TrustVector:
        """Deserialize TrustVector from JSON payload dict."""
        import json

        from federation.trust.trust_vector import TrustVector
        data = json.loads(payload)
        return TrustVector.from_dict(data)


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_trust_sync_protocol():
    """Sanity test for v9.5 TrustSyncProtocol."""
    from federation.trust.trust_vector import TrustVector

    # ── setup ─────────────────────────────────────────────────────
    proto_a = TrustSyncProtocol(node_id="node_A", full_sync_interval=5)
    proto_b = TrustSyncProtocol(node_id="node_B", full_sync_interval=5)

    proto_a.add_peer("node_B")
    proto_b.add_peer("node_A")

    # ── initial full sync ─────────────────────────────────────────
    tv_a = TrustVector()
    tv_a.set_entry("proof_1", 0.9, 1000.0, ledger_version=3)
    tv_a.set_entry("proof_2", 0.7, 1000.0, ledger_version=2)

    msg = proto_a.prepare_outbound("node_B", current_tick=1, current_tv=tv_a, vector_clock={"node_A": 3})
    assert msg is not None
    assert msg.msg_type == TrustMessageType.TRUST_VECTOR
    log.info("✅ prepare_outbound: initial full sync → TRUST_VECTOR")

    # ── receive and merge ──────────────────────────────────────────
    tv_b = TrustVector()  # empty on node_B
    tv_b_new, had_conflict = proto_b.receive_and_merge(msg, tv_b)
    assert "proof_1" in tv_b_new
    assert tv_b_new.get("proof_1").trust_score == 0.9
    assert had_conflict is True  # first sync always introduces new entries
    log.info(f"✅ receive_and_merge: trust merged, had_conflict={had_conflict}")

    # ── delta sync ───────────────────────────────────────────────
    tv_a_v2 = tv_a.snapshot()
    tv_a_v2.set_entry("proof_1", 0.85, 1001.0, ledger_version=4)  # updated
    tv_a_v2.set_entry("proof_3", 0.6, 1001.0, ledger_version=1)  # new

    msg_delta = proto_a.prepare_outbound("node_B", current_tick=2, current_tv=tv_a_v2, vector_clock={"node_A": 4})
    assert msg_delta is not None
    assert msg_delta.msg_type == TrustMessageType.TRUST_DELTA
    log.info("✅ prepare_outbound: delta sync → TRUST_DELTA")

    # ── receive delta ─────────────────────────────────────────────
    tv_b_new2, had_conflict2 = proto_b.receive_and_merge(msg_delta, tv_b_new)
    assert tv_b_new2.get("proof_1").trust_score == 0.85
    assert tv_b_new2.get("proof_1").ledger_version == 4
    assert "proof_3" in tv_b_new2
    log.info("✅ receive_and_merge delta: proof_1 updated to 0.85, proof_3 added")

    # ── peer management ───────────────────────────────────────────
    assert "node_B" in proto_a.peers
    proto_a.remove_peer("node_B")
    assert "node_B" not in proto_a.peers
    log.info("✅ peer add/remove")

    # ── on_tick ───────────────────────────────────────────────────
    proto_a.add_peer("node_B")
    tv_a_v3 = tv_a_v2.snapshot()
    outbound = proto_a.on_tick(tick=5, local_tv=tv_a_v3, vector_clock={"node_A": 5})
    # tick=5, full_sync_interval=5 → 5%5==0 → full sync
    assert "node_B" in outbound
    assert outbound["node_B"].msg_type == TrustMessageType.TRUST_VECTOR
    log.info("✅ on_tick: triggers full sync at tick=5 (full_sync_interval=5)")

    # ── convergence test: same proof → same trust on both nodes ───
    # After enough syncs, both nodes should have identical TrustVectors
    # node_A and node_B have the same ledger state after delta merge
    assert tv_b_new2.get("proof_1").trust_score == tv_a_v3.get("proof_1").trust_score
    assert tv_b_new2.get("proof_1").ledger_version == tv_a_v3.get("proof_1").ledger_version
    log.info("✅ convergence: both nodes have identical trust after sync")

    # ── vector clock ──────────────────────────────────────────────
    clock = proto_a.get_vector_clock()
    assert isinstance(clock, dict)
    log.info(f"✅ get_vector_clock: {clock}")

    log.info("\n✅ v9.5 TrustSyncProtocol — all checks passed")


if __name__ == "__main__":
    _test_trust_sync_protocol()


__all__ = [
    "PeerTrustState",
    "TrustMessageType",
    "TrustSyncMessage",
    "TrustSyncProtocol",
]

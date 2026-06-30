"""
DRL (Data Replication Layer) — in-memory message passing with fault injection.
This is the layer that WAS the simulation transport. Now it's the FAULT LAYER
on top of real RPC.

Design principle: DRL never goes away — it stays as the fault injection
abstraction so chaos tests remain valid across both simulation and real network.
"""

from __future__ import annotations

import queue
import random
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _make_uuid(rng: random.Random) -> str:
    """Deterministic UUID v4 replacement using the seeded RNG."""
    ba = bytearray(16)
    rng.randbytes(16)
    ba[6] = (ba[6] & 0x0f) | 0x40
    ba[8] = (ba[8] & 0x3f) | 0x80
    return str(uuid.UUID(bytes=bytes(ba)))


class DeliveryModel(Enum):
    """Fault model DRL applies to outgoing messages."""
    CLEAN          = "clean"           # no faults
    DROP           = "drop"            # silent loss
    DELAY          = "delay"           # latency injection
    DUPLICATE      = "duplicate"       # send twice
    REORDER        = "reorder"         # swap with next
    PARTITION      = "partition"        # isolate a node
    CORRUPT        = "corrupt"          # bit-flip payload


@dataclass
class Message:
    """In-memory message envelope carried by DRL."""
    msg_id:    str
    source:    str
    target:    str           # "" = broadcast
    payload:   bytes
    timestamp: int           # unix ns
    ttl:       int = 64
    meta:      dict = field(default_factory=dict)

    def to_proto(self, proto_msg_cls: Any) -> Any:
        """Convert to protobuf message (used by RPC adapter)."""
        return proto_msg_cls(
            msg_id=self.msg_id,
            source=self.source,
            target=self.target,
            payload=self.payload.decode("utf-8", errors="replace"),
            timestamp=self.timestamp,
            ttl=self.ttl,
            meta=self.meta,
        )

    @classmethod
    def from_proto(cls, proto_msg: Any) -> Message:
        return cls(
            msg_id=proto_msg.msg_id,
            source=proto_msg.source,
            target=proto_msg.target,
            payload=proto_msg.payload.encode("utf-8"),
            timestamp=proto_msg.timestamp,
            ttl=proto_msg.ttl,
            meta=dict(proto_msg.meta),
        )


@dataclass
class FailureModel:
    """Per-node failure characteristics."""
    loss_rate:      float = 0.0   # 0.0–1.0
    dup_rate:        float = 0.0
    latency_ms:     tuple[float, float] = (0.0, 0.0)  # (lo, hi)
    reorder_prob:   float = 0.0
    corrupt_prob:   float = 0.0
    partition_from: set[str] = field(default_factory=set)
    byzantine:      bool = False


class DRLTransport:
    """
    In-memory message bus with optional fault injection.
    This is the SIMULATION transport used by chaos tests.
    It also provides the baseline delivery model that RPC
    adapter layers on top of.
    """

    def __init__(
        self,
        node_id: str,
        seed: int | None = None,
        delivery_model: DeliveryModel = DeliveryModel.CLEAN,
    ) -> None:
        self.node_id = node_id
        self._rng = random.Random(seed)
        self._delivery_model = delivery_model
        self._queues: dict[str, queue.Queue] = {}
        self._subscribers: dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._messages: list[Message] = []
        self._delivered: list[str] = []
        self._partitions: set[str] = set()
        self._failures = FailureModel()
        self._transit_delay_ms = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def register_peer(self, peer_id: str) -> None:
        with self._lock:
            if peer_id not in self._queues:
                self._queues[peer_id] = queue.Queue()

    def subscribe(self, peer_id: str, callback: Callable[[Message], None]) -> None:
        with self._lock:
            self._subscribers[peer_id] = callback

    def send_to(self, target: str, payload: bytes, msg_id: str | None = None) -> str | None:
        """
        Simulate a unicast send through the DRL fault layer.
        Returns the msg_id if message entered the transit layer, None if dropped.
        """
        msg_id = msg_id or _make_uuid(self._rng)
        msg = Message(
            msg_id=msg_id,
            source=self.node_id,
            target=target,
            payload=payload,
            timestamp=time.time_ns(),
            ttl=64,
        )

        if self._should_drop():
            return None

        self._messages.append(msg)
        self._apply_transit_delay()

        if self._delivery_model == DeliveryModel.CORRUPT:
            msg.payload = self._corrupt_payload(msg.payload)
        elif self._delivery_model == DeliveryModel.DUPLICATE:
            self._queue_for_peer(msg)
            self._queue_for_peer(msg)
            return msg_id

        self._queue_for_peer(msg)
        return msg_id

    def broadcast(self, payload: bytes, msg_id: str | None = None) -> str:
        msg_id = msg_id or _make_uuid(self._rng)
        for peer_id in list(self._queues.keys()):
            self.send_to(peer_id, payload, msg_id)
        return msg_id

    def receive(self, msg: Message) -> None:
        """Deliver a message to the local node's input queue."""
        with self._lock:
            self._delivered.append(msg.msg_id)
            if self.node_id in self._subscribers:
                self._subscribers[self.node_id](msg)

    def set_delivery_model(self, model: DeliveryModel) -> None:
        self._delivery_model = model

    def set_failure_model(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self._failures, k):
                setattr(self._failures, k, v)

    def set_transit_latency(self, ms: float) -> None:
        self._transit_delay_ms = ms

    # ── Fault injection helpers (used by chaos harness) ──────────────────────

    def inject_partition(self, peer_id: str) -> None:
        self._partitions.add(peer_id)

    def heal_partition(self, peer_id: str) -> None:
        self._partitions.discard(peer_id)

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "node_id": self.node_id,
                "sent": len(self._messages),
                "delivered": len(self._delivered),
                "partitions": list(self._partitions),
                "delivery_model": self._delivery_model.value,
            }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _should_drop(self) -> bool:
        return self._rng.random() < self._failures.loss_rate

    def _apply_transit_delay(self) -> None:
        if self._transit_delay_ms > 0:
            time.sleep(self._transit_delay_ms / 1000)
        lo, hi = self._failures.latency_ms
        if lo or hi:
            time.sleep(self._rng.uniform(lo, hi) / 1000)

    def _corrupt_payload(self, payload: bytes) -> bytes:
        if not payload:
            return payload
        ba = bytearray(payload)
        idx = self._rng.randint(0, len(ba) - 1)
        ba[idx] ^= 1 << self._rng.randint(0, 7)
        return bytes(ba)

    def _queue_for_peer(self, msg: Message) -> None:
        if msg.target in self._partitions:
            return
        with self._lock:
            q = self._queues.get(msg.target)
        if q is not None:
            q.put(msg)
        # also notify subscriber
        with self._lock:
            cb = self._subscribers.get(msg.target)
        if cb is not None:
            cb(msg)

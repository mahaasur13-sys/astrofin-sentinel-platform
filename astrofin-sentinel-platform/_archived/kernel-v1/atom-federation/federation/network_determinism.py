"""
Network Determinism Abstraction — federation/network_determinism.py
ATOM-META-RL-022 P0

Components:
  1. LogicalClock   — Lamport-style logical clock for message ordering
  2. OrderedMessage — message with deterministic order key
  3. ReplayableMessageQueue — deterministic message queue with replay support
  4. DeterministicFanoutOrder — deterministic message fanout ordering

Guarantees:
  - All nodes agree on message ordering (happened-before relation)
  - Messages can be replayed from any tick in deterministic order
  - Fanout order is deterministic (hash-based, no time/random)
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from typing import Any

# ── LogicalClock ─────────────────────────────────────────────────────────────

class LogicalClock:
    """
    Lamport-style logical clock for deterministic message ordering.

    Guarantees:
      - If message m1 happened-before m2, then LogicalClock(m1) < LogicalClock(m2)
      - All nodes agree on total ordering of messages (via order_key)
      - No physical time used (deterministic)

    Usage:
        lc = LogicalClock(node_id="node-1")
        lc.tick()                # advance own clock
        lc.observe(remote_lc)    # observe remote clock (happened-before)
        lc.value()              # get current clock value
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._counter: int = 0
        self._lock = threading.RLock()

    def tick(self) -> int:
        """Advance own clock. Returns new value."""
        with self._lock:
            self._counter += 1
            return self._counter

    def observe(self, remote_clock: int) -> None:
        """
        Observe remote clock value (happened-before relationship).
        Updates local clock to max(local, remote) + 1.
        """
        with self._lock:
            self._counter = max(self._counter, remote_clock) + 1

    def value(self) -> int:
        """Get current clock value (read-only)."""
        with self._lock:
            return self._counter

    def make_order_key(self, tick: int) -> str:
        """
        Create deterministic order key for a message.
        Format: '{clock:010d}:{tick:010d}:{node_id}'
        Sorted lexicographically = sorted by (clock, tick, node_id).
        """
        with self._lock:
            return f"{self._counter:010d}:{tick:010d}:{self.node_id}"


# ── OrderedMessage ───────────────────────────────────────────────────────────

@dataclass
class OrderedMessage:
    """
    Message with deterministic ordering metadata.

    order_key format: '{logical_clock:010d}:{tick:010d}:{node_id}'
    This ensures:
      1. Messages are ordered by happened-before relationship
      2. Same messages across all nodes produce identical order_key
      3. Lexicographic sort == causal order
    """
    msg: Any
    logical_clock: int
    tick: int
    node_id: str
    order_key: str
    payload_hash: str = ""

    @staticmethod
    def make_order_key(logical_clock: int, tick: int, node_id: str) -> str:
        return f"{logical_clock:010d}:{tick:010d}:{node_id}"

    @staticmethod
    def compute_payload_hash(payload: Any) -> str:
        """Deterministic hash of message payload."""
        import json
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ── ReplayableMessageQueue ───────────────────────────────────────────────────

class ReplayableMessageQueue:
    """
    Deterministic message queue with full replay support.

    Guarantees:
      - All messages ordered by order_key (logical_clock, tick, node_id)
      - Messages can be replayed from any tick in deterministic order
      - No time.time(), no random in ordering

    Usage:
        q = ReplayableMessageQueue(node_id="node-1")

        # Send a message:
        ordered = q.send({"type": "state_update", "data": {...}}, tick=42)

        # Receive a message from another node:
        q.receive(incoming_ordered_msg)

        # Replay all messages from tick N onwards:
        for msg in q.replay_from(tick=N):
            process(msg)
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._queue: list[OrderedMessage] = []
        self._logical_clock = LogicalClock(node_id=node_id)
        self._lock = threading.RLock()
        self._sent_count: int = 0
        self._received_count: int = 0

    def send(self, msg: Any, tick: int) -> OrderedMessage:
        """
        Send a message (add to local queue with deterministic ordering).
        Returns the OrderedMessage.
        """
        with self._lock:
            lc = self._logical_clock.tick()
            order_key = OrderedMessage.make_order_key(lc, tick, self.node_id)
            payload_hash = OrderedMessage.compute_payload_hash(msg)

            ordered = OrderedMessage(
                msg=msg,
                logical_clock=lc,
                tick=tick,
                node_id=self.node_id,
                order_key=order_key,
                payload_hash=payload_hash
            )
            self._queue.append(ordered)
            self._sent_count += 1
            # Maintain sorted order
            self._queue.sort(key=lambda x: x.order_key)
            return ordered

    def receive(self, ordered_msg: OrderedMessage) -> None:
        """
        Receive a message from another node.
        Updates logical clock and inserts in deterministic order.
        """
        with self._lock:
            self._logical_clock.observe(ordered_msg.logical_clock)
            self._received_count += 1
            # Insert in order
            self._queue.append(ordered_msg)
            self._queue.sort(key=lambda x: x.order_key)

    def replay_from(self, tick: int) -> list[OrderedMessage]:
        """
        Return all messages with tick >= N, in deterministic order.
        Used for deterministic replay.
        """
        with self._lock:
            return [m for m in self._queue if m.tick >= tick]

    def replay_range(self, tick_start: int, tick_end: int) -> list[OrderedMessage]:
        """Return all messages with tick_start <= tick <= tick_end."""
        with self._lock:
            return [m for m in self._queue if tick_start <= m.tick <= tick_end]

    def get_all_sorted(self) -> list[OrderedMessage]:
        """Return all messages in deterministic order."""
        with self._lock:
            return list(self._queue)

    def peek_next(self) -> OrderedMessage | None:
        """Peek at next message without removing."""
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None

    def pop_next(self) -> OrderedMessage | None:
        """Pop and return next message."""
        with self._lock:
            if self._queue:
                return self._queue.pop(0)
            return None

    @property
    def logical_clock_value(self) -> int:
        return self._logical_clock.value()

    @property
    def sent_count(self) -> int:
        return self._sent_count

    @property
    def received_count(self) -> int:
        return self._received_count

    def verify_ordering(self) -> bool:
        """Verify queue is correctly ordered by order_key."""
        with self._lock:
            keys = [m.order_key for m in self._queue]
            return keys == sorted(keys)

    def clear(self) -> None:
        """Clear queue. For testing."""
        with self._lock:
            self._queue.clear()


# ── DeterministicFanoutOrder ─────────────────────────────────────────────────

class DeterministicFanoutOrder:
    """
    Computes deterministic ordering for message fanout (1-to-N).

    Guarantees:
      - Same sender + same targets + same tick -> same fanout order
      - No random, no time in ordering
      - Order determined by hash(sender + target + tick)

    Usage:
        order = DeterministicFanoutOrder.compute(
            sender="node-1",
            targets=["node-2", "node-3", "node-4"],
            tick=42
        )
        # Returns: ["node-3", "node-1", "node-4"] — deterministic
    """

    @staticmethod
    def compute_fanout_order(
        sender: str,
        targets: list[str],
        tick: int
    ) -> list[str]:
        """
        Compute deterministic fanout order.
        Returns targets sorted by hash(sender + target + tick).
        """
        if not targets:
            return []

        def fanout_key(target: str) -> str:
            return hashlib.sha256(
                f"fanout:{sender}:{target}:{tick}:ATOM-FANOUT".encode()
            ).hexdigest()

        return sorted(targets, key=fanout_key)

    @staticmethod
    def compute_recipients_for_round(
        sender: str,
        all_nodes: list[str],
        tick: int,
        round_num: int = 0
    ) -> list[str]:
        """
        Compute which nodes receive message in this round.
        Deterministic round-robin via hash.
        """
        recipients = [n for n in all_nodes if n != sender]
        if not recipients:
            return []

        def round_key(node: str) -> str:
            return hashlib.sha256(
                f"round:{sender}:{node}:{tick}:{round_num}:ATOM-ROUND".encode()
            ).hexdigest()

        return sorted(recipients, key=round_key)


# ── DeterministicMessageEnvelope ─────────────────────────────────────────────

@dataclass
class DeterministicMessageEnvelope:
    """
    Wraps any message with deterministic metadata for federation transport.
    """
    sender: str
    recipients: list[str]  # in deterministic fanout order
    tick: int
    logical_clock: int
    order_key: str
    payload: Any
    payload_hash: str
    fanout_sequence: list[str]  # deterministic recipient order

    @staticmethod
    def create(
        sender: str,
        recipients: list[str],
        tick: int,
        logical_clock: int,
        payload: Any
    ) -> DeterministicMessageEnvelope:
        order_key = OrderedMessage.make_order_key(logical_clock, tick, sender)
        payload_hash = OrderedMessage.compute_payload_hash(payload)
        fanout_sequence = DeterministicFanoutOrder.compute_fanout_order(
            sender=sender,
            targets=recipients,
            tick=tick
        )
        return DeterministicMessageEnvelope(
            sender=sender,
            recipients=recipients,
            tick=tick,
            logical_clock=logical_clock,
            order_key=order_key,
            payload=payload,
            payload_hash=payload_hash,
            fanout_sequence=fanout_sequence
        )

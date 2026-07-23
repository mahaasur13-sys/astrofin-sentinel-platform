"""
replay_protection.py — v9.9 NonceSequenceValidator

Provides replay attack protection via a sliding window of accepted
sequence numbers per sender.

Design:
  - Each sender gets a NonceWindow tracking (seq → timestamp_ns)
  - New message accepted only if: seq > local_highest_seq AND seq not in window
  - Window is truncated to max_size to bound memory
  - seq ≤ local_highest_seq → REPLAYED (old duplicate)
  - seq in window (but > highest) → REPLAYED (recent duplicate within window)

Usage:
    validator = NonceSequenceValidator(window_size=100, max_age_ns=60_000_000_000)
    validator.record("node_A", seq=1, ts_ns=time.time_ns())
    # Next message from node_A
    result = validator.check_and_record("node_A", seq=2, ts_ns=time.time_ns())
    assert result.status == NonceStatus.ACCEPTED
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto

import logging
log = logging.getLogger(__name__)



class ReplayProtectionError(Exception):
    """Raised when replay protection check fails."""


class NonceStatus(Enum):
    ACCEPTED = auto()   # seq is new, within window, timestamp valid
    REPLAYED = auto()   # duplicate of recent message
    TOO_OLD  = auto()   # seq predates window (outside retention range)
    FUTURE   = auto()   # seq is suspiciously far ahead (possible loop/attack)


@dataclass
class NonceCheckResult:
    status: NonceStatus
    sender_id: str
    seq: int
    gap: int          # seq difference from previous highest
    age_ns: int       # message age in nanoseconds (0 if accepted)


@dataclass
class NonceWindow:
    """
    Per-sender sliding window of recent sequence numbers.

    Fields:
        received_seqs   — ordered list of (seq, ts_ns) seen within window
        highest_seq     — highest accepted seq for this sender
        last_ts_ns      — timestamp of highest_seq message
    """
    sender_id: str
    received_seqs: list[tuple[int, int]] = field(default_factory=list)  # (seq, ts_ns)
    highest_seq: int = -1
    last_ts_ns: int = 0

    def add(self, seq: int, ts_ns: int) -> None:
        self.received_seqs.append((seq, ts_ns))
        if seq > self.highest_seq:
            self.highest_seq = seq
            self.last_ts_ns = ts_ns

    def trim(self, max_size: int) -> None:
        """Keep only the most recent max_size entries."""
        if len(self.received_seqs) > max_size:
            self.received_seqs = self.received_seqs[-max_size:]


@dataclass
class NonceSequenceValidator:
    """
    Sliding-window anti-replay validator.

    Accepts a new message (sender, seq) only if:
      1. seq > sender's highest known seq
      2. seq has not been seen within the sliding window
      3. message timestamp is not too old (max_age_ns)

    Security properties:
      - Memory-bounded: old entries are trimmed
      - Timestamp-bounded: messages older than max_age_ns are rejected
      - Gap detection: large gaps raise FUTURE flag (potential replay via wrapping)
    """

    def __init__(
        self,
        window_size: int = 100,
        max_age_ns: int = 60_000_000_000,   # 60 seconds in nanoseconds
        max_seq_gap: int = 50,              # max acceptable seq gap before FUTURE flag
    ):
        self.window_size = window_size
        self.max_age_ns = max_age_ns
        self.max_seq_gap = max_seq_gap

        # sender_id → NonceWindow
        self._windows: dict[str, NonceWindow] = {}
        # sender_id → highest_seq (fast lookup)
        self._highest: dict[str, int] = {}

    def _get_or_create_window(self, sender_id: str) -> NonceWindow:
        if sender_id not in self._windows:
            self._windows[sender_id] = NonceWindow(sender_id=sender_id)
        return self._windows[sender_id]

    def check_and_record(
        self,
        sender_id: str,
        seq: int,
        ts_ns: int,
    ) -> NonceCheckResult:
        """
        Check whether (sender_id, seq) is a replay, then record it.

        Args:
            sender_id:  node that sent this message
            seq:        monotonic sequence number from message
            ts_ns:      message creation timestamp (nanoseconds)

        Returns:
            NonceCheckResult with status, gap, and age
        """
        now_ns = time.time_ns()
        age_ns = now_ns - ts_ns

        # ── 1. Timestamp bound: message too old ─────────────────────
        if age_ns > self.max_age_ns:
            return NonceCheckResult(
                status=NonceStatus.TOO_OLD,
                sender_id=sender_id,
                seq=seq,
                gap=0,
                age_ns=age_ns,
            )

        window = self._get_or_create_window(sender_id)

        # ── 2. Already in window (duplicate within window) ───────────
        seqs_in_window = {s for s, _ in window.received_seqs}
        if seq in seqs_in_window:
            return NonceCheckResult(
                status=NonceStatus.REPLAYED,
                sender_id=sender_id,
                seq=seq,
                gap=0,
                age_ns=age_ns,
            )

        # ── 3. seq ≤ highest_seq (old duplicate) ─────────────────────
        highest = self._highest.get(sender_id, -1)
        if seq <= highest:
            return NonceCheckResult(
                status=NonceStatus.REPLAYED,
                sender_id=sender_id,
                seq=seq,
                gap=0,
                age_ns=age_ns,
            )

        # ── 4. Gap detection ─────────────────────────────────────────
        gap = seq - highest if highest >= 0 else seq
        if gap > self.max_seq_gap:
            # Suspiciously large gap — could be seq wrapping attack
            return NonceCheckResult(
                status=NonceStatus.FUTURE,
                sender_id=sender_id,
                seq=seq,
                gap=gap,
                age_ns=age_ns,
            )

        # ── 5. ACCEPTED ──────────────────────────────────────────────
        window.add(seq, ts_ns)
        window.trim(self.window_size)
        self._highest[sender_id] = seq

        return NonceCheckResult(
            status=NonceStatus.ACCEPTED,
            sender_id=sender_id,
            seq=seq,
            gap=gap,
            age_ns=age_ns,
        )

    def reset_sender(self, sender_id: str) -> None:
        """Clear all state for a sender (used after view change or key rotation)."""
        self._windows.pop(sender_id, None)
        self._highest.pop(sender_id, None)

    def reset_all(self) -> None:
        """Clear all state for all senders."""
        self._windows.clear()
        self._highest.clear()

    def get_highest_seq(self, sender_id: str) -> int:
        return self._highest.get(sender_id, -1)

    def window_summary(self) -> dict:
        return {
            sender_id: {
                "highest_seq": w.highest_seq,
                "window_size": len(w.received_seqs),
            }
            for sender_id, w in self._windows.items()
        }


# ─── Tests ────────────────────────────────────────────────────────────────

def _test_nonce_sequence_validator():
    now = time.time_ns()

    # ── basic accept ─────────────────────────────────────────────────
    v = NonceSequenceValidator(window_size=5, max_age_ns=60_000_000_000)
    r = v.check_and_record("node_A", seq=1, ts_ns=now)
    assert r.status == NonceStatus.ACCEPTED, f"Expected ACCEPTED, got {r.status}"
    log.info(f"✅ seq=1 ACCEPTED (gap={r.gap}, age={r.age_ns}ns)")

    r2 = v.check_and_record("node_A", seq=2, ts_ns=now)
    assert r2.status == NonceStatus.ACCEPTED
    log.info(f"✅ seq=2 ACCEPTED (gap={r2.gap})")

    # ── exact duplicate → REPLAYED ────────────────────────────────────
    r3 = v.check_and_record("node_A", seq=2, ts_ns=now)
    assert r3.status == NonceStatus.REPLAYED
    log.info("✅ seq=2 REPLAYED (same message duplicate)")

    # ── old seq ──────────────────────────────────────────────────────
    r4 = v.check_and_record("node_A", seq=1, ts_ns=now)
    assert r4.status == NonceStatus.REPLAYED
    log.info("✅ seq=1 REPLAYED (seq ≤ highest_seq)")

    # ── future seq (large gap) ──────────────────────────────────────
    r5 = v.check_and_record("node_A", seq=99, ts_ns=now)
    assert r5.status == NonceStatus.FUTURE
    log.info(f"✅ seq=99 FUTURE (gap={r5.gap} > max_seq_gap=50)")

    # ── accept FUTURE after intermediate seqs ─────────────────────────
    r6 = v.check_and_record("node_A", seq=50, ts_ns=now)
    assert r6.status == NonceStatus.ACCEPTED
    log.info("✅ seq=50 ACCEPTED (fills gap, now highest=50)")

    r7 = v.check_and_record("node_A", seq=99, ts_ns=now)
    assert r7.status == NonceStatus.ACCEPTED, f"Expected ACCEPTED, got {r7.status}"
    log.info("✅ seq=99 ACCEPTED after intermediate gap was filled")

    # ── TOO_OLD (timestamp expired) ─────────────────────────────────
    v2 = NonceSequenceValidator(window_size=5, max_age_ns=1_000_000_000)  # 1 second
    old_ts = time.time_ns() - 2_000_000_000  # 2 seconds ago
    r8 = v2.check_and_record("node_B", seq=1, ts_ns=old_ts)
    assert r8.status == NonceStatus.TOO_OLD
    log.info(f"✅ seq=1 TOO_OLD (age={r8.age_ns}ns > max_age_ns=1s)")

    # ── per-sender isolation ─────────────────────────────────────────
    v3 = NonceSequenceValidator(window_size=5)
    v3.check_and_record("node_A", seq=1, ts_ns=now)
    v3.check_and_record("node_B", seq=1, ts_ns=now)
    assert v3.get_highest_seq("node_A") == 1
    assert v3.get_highest_seq("node_B") == 1
    v3.check_and_record("node_C", seq=1, ts_ns=now)
    assert v3.get_highest_seq("node_C") == 1
    log.info("✅ per-sender isolation (A=1, B=1, C=1)")

    # ── window trim ──────────────────────────────────────────────────
    v4 = NonceSequenceValidator(window_size=3)
    for i in range(1, 6):
        v4.check_and_record("node_X", seq=i, ts_ns=now)
    summary = v4.window_summary()["node_X"]
    assert summary["window_size"] == 3
    assert summary["highest_seq"] == 5
    log.info(f"✅ window trim: size={summary['window_size']}, highest={summary['highest_seq']}")

    # ── reset_sender ─────────────────────────────────────────────────
    v5 = NonceSequenceValidator(window_size=3)
    v5.check_and_record("node_A", seq=5, ts_ns=now)
    v5.reset_sender("node_A")
    assert v5.get_highest_seq("node_A") == -1
    log.info("✅ reset_sender clears state")

    log.info("\n✅ v9.9 NonceSequenceValidator — all checks passed")


if __name__ == "__main__":
    _test_nonce_sequence_validator()

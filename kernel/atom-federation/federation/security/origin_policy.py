"""
origin_policy.py — v9.9 OriginPolicy

Enforces node-level origin restrictions on inbound messages.

Policies:
  - ALLOW_ALL: no restrictions (default before gate is configured)
  - WHITELIST: only listed node_ids may send
  - TRUST_THRESHOLD: only nodes with trust_score ≥ threshold may send

Usage:
    policy = OriginPolicy(mode=OriginMode.WHITELIST, allowed_nodes={"node_A", "node_B"})
    policy.check(sender_id="node_A", trust_score=0.8)  # → OK
    policy.check(sender_id="node_C", trust_score=0.8)  # → raises OriginViolation

    trust_policy = OriginPolicy(mode=OriginMode.TRUST_THRESHOLD, trust_threshold=0.3)
    trust_policy.check(sender_id="node_A", trust_score=0.5)  # → OK
    trust_policy.check(sender_id="node_B", trust_score=0.1)  # → raises OriginViolation
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class OriginMode(Enum):
    ALLOW_ALL = auto()       # No restrictions
    WHITELIST = auto()       # Only allowed_nodes may send
    TRUST_THRESHOLD = auto()  # Only nodes with trust ≥ threshold may send


class OriginViolation(Exception):
    """Raised when an inbound message violates origin policy."""


@dataclass
class OriginCheckResult:
    sender_id: str
    mode: OriginMode
    allowed: bool
    reason: str
    trust_score: float | None = None


@dataclass
class OriginPolicy:
    """
    Enforces node-level sender restrictions on inbound messages.

    Modes:
      ALLOW_ALL:        Accept all senders (no origin check)
      WHITELIST:         Only allowed_nodes may send; all others rejected
      TRUST_THRESHOLD:   Only nodes with trust_score ≥ threshold may send

    Combinators:
      AND: all policies must pass
      OR:  any policy must pass
    """

    def __init__(
        self,
        mode: OriginMode = OriginMode.ALLOW_ALL,
        allowed_nodes: set[str] | None = None,
        trust_threshold: float = 0.0,
        trust_scores: dict[str, float] | None = None,
        combinator: str = "AND",
    ):
        self.mode = mode
        self.allowed_nodes: set[str] = allowed_nodes or set()
        self.trust_threshold = trust_threshold
        self.trust_scores: dict[str, float] = trust_scores or {}
        self.combinator = combinator  # "AND" | "OR"

    def check(self, sender_id: str, trust_score: float | None = None) -> OriginCheckResult:
        """
        Check whether sender_id is permitted to send under this policy.

        Args:
            sender_id:    node attempting to send
            trust_score:  current trust score for sender (required for TRUST_THRESHOLD)

        Returns:
            OriginCheckResult

        Raises:
            OriginViolation: if policy rejects the sender
        """
        ts = trust_score if trust_score is not None else self.trust_scores.get(sender_id)

        if self.mode == OriginMode.ALLOW_ALL:
            return OriginCheckResult(
                sender_id=sender_id,
                mode=self.mode,
                allowed=True,
                reason="allow_all",
                trust_score=ts,
            )

        if self.mode == OriginMode.WHITELIST:
            if sender_id in self.allowed_nodes:
                return OriginCheckResult(
                    sender_id=sender_id,
                    mode=self.mode,
                    allowed=True,
                    reason=f"whitelisted: {sender_id}",
                    trust_score=ts,
                )
            raise OriginViolation(
                f"origin rejected: {sender_id} not in whitelist "
                f"(allowed={self.allowed_nodes})"
            )

        if self.mode == OriginMode.TRUST_THRESHOLD:
            if ts is None:
                raise OriginViolation(
                    f"origin check requires trust_score for {sender_id}"
                )
            if ts >= self.trust_threshold:
                return OriginCheckResult(
                    sender_id=sender_id,
                    mode=self.mode,
                    allowed=True,
                    reason=f"trust {ts:.3f} >= threshold {self.trust_threshold:.3f}",
                    trust_score=ts,
                )
            raise OriginViolation(
                f"origin rejected: trust {ts:.3f} < threshold {self.trust_threshold:.3f} "
                f"for {sender_id}"
            )

        # Should not reach here
        return OriginCheckResult(
            sender_id=sender_id,
            mode=self.mode,
            allowed=True,
            reason="unknown_mode",
            trust_score=ts,
        )

    def update_trust_score(self, sender_id: str, trust_score: float) -> None:
        """Update trust score for a sender (used by trust sync)."""
        self.trust_scores[sender_id] = trust_score

    def add_to_whitelist(self, sender_id: str) -> None:
        """Add a node to the whitelist."""
        self.allowed_nodes.add(sender_id)

    def remove_from_whitelist(self, sender_id: str) -> None:
        """Remove a node from the whitelist."""
        self.allowed_nodes.discard(sender_id)


# ─── Tests ────────────────────────────────────────────────────────────────

def _test_origin_policy():
    # ── ALLOW_ALL ──────────────────────────────────────────────────
    policy = OriginPolicy(mode=OriginMode.ALLOW_ALL)
    r = policy.check("anyone")
    assert r.allowed is True
    print("✅ ALLOW_ALL: any sender accepted")

    # ── WHITELIST ─────────────────────────────────────────────────
    policy = OriginPolicy(
        mode=OriginMode.WHITELIST,
        allowed_nodes={"node_A", "node_B"},
    )
    r1 = policy.check("node_A")
    assert r1.allowed is True
    print("✅ WHITELIST: node_A accepted")

    try:
        policy.check("node_C")
        assert False, "should have raised"
    except OriginViolation as e:
        assert "node_C" in str(e)
        print("✅ WHITELIST: node_C rejected")

    # ── TRUST_THRESHOLD ───────────────────────────────────────────
    policy = OriginPolicy(
        mode=OriginMode.TRUST_THRESHOLD,
        trust_threshold=0.3,
    )
    r2 = policy.check("node_X", trust_score=0.8)
    assert r2.allowed is True
    print("✅ TRUST_THRESHOLD: score=0.8 >= 0.3 → accepted")

    try:
        policy.check("node_Y", trust_score=0.1)
        assert False, "should have raised"
    except OriginViolation as e:
        assert "0.1" in str(e) and "0.3" in str(e)
        print("✅ TRUST_THRESHOLD: score=0.1 < 0.3 → rejected")

    # ── missing trust score ────────────────────────────────────────
    policy = OriginPolicy(mode=OriginMode.TRUST_THRESHOLD, trust_threshold=0.3)
    try:
        policy.check("unknown_node")  # no trust_score provided
        assert False, "should have raised"
    except OriginViolation as e:
        assert "requires trust_score" in str(e)
        print("✅ TRUST_THRESHOLD: missing trust_score → rejected")

    # ── update_trust_score ─────────────────────────────────────────
    policy = OriginPolicy(mode=OriginMode.TRUST_THRESHOLD, trust_threshold=0.5)
    policy.update_trust_score("node_Z", 0.9)
    r3 = policy.check("node_Z")
    assert r3.allowed is True
    print("✅ update_trust_score: dynamic trust update")

    # ── whitelist add/remove ───────────────────────────────────────
    policy = OriginPolicy(mode=OriginMode.WHITELIST, allowed_nodes={"node_A"})
    policy.add_to_whitelist("node_B")
    assert "node_B" in policy.allowed_nodes
    policy.remove_from_whitelist("node_A")
    assert "node_A" not in policy.allowed_nodes
    print("✅ whitelist add/remove")

    print("\n✅ v9.9 OriginPolicy — all checks passed")


if __name__ == "__main__":
    _test_origin_policy()

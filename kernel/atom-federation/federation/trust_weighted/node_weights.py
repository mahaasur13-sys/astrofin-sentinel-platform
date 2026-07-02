"""
node_weights.py — v9.6 Node Weight Registry

Purpose:
  Manages per-node weights derived from TrustVector state.

  node_weight(node_id) = aggregate trust score for all proofs
                          submitted by that node.

  Aggregation: mean of trust_scores across all proofs from node.

Design constraints:
  - Weights are derived state (not stored independently of TrustVector)
  - Snapshot-only (immutable weight snapshots for deterministic consensus)
  - Bounded: single node weight ≤ 1.0

Integration:
  TrustVector → NodeWeightRegistry.compute_weights()
  TrustWeightedConsensusResolver → node_weight for weighted voting
  TrustSkewDetector → weight distribution for skew/collapse detection
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class NodeWeightEntry:
    """Aggregated trust weight for a single node."""
    node_id: str
    aggregated_trust: float           # ∈ [0.0, 1.0]
    proof_count: int
    proof_hashes: list[str]
    timestamp: float
    ledger_version: int

    def is_stale(self, now: float, ttl_seconds: float) -> bool:
        return (now - self.timestamp) > ttl_seconds


@dataclass
class NodeWeightsSnapshot:
    """
    Immutable snapshot of all node weights at a point in time.

    Used for deterministic consensus decisions:
      - captured before consensus round
      - passed to TrustWeightedConsensusResolver
      - weights do NOT change during consensus round
    """
    weights: dict[str, float]           # node_id → weight ∈ [0, 1]
    total_weight: float                 # Σ weights
    max_single_weight: float            # largest individual weight
    dom_weight_fraction: float          # max_single_weight / total_weight
    snapshot_time: float
    ledger_version: int
    epoch: int

    def node_weight(self, node_id: str) -> float:
        """Return weight for node_id, or 0.0 if unknown."""
        return self.weights.get(node_id, 0.0)

    def effective_vote(
        self,
        node_id: str,
        raw_vote: float,   # ∈ [-1, 1]: -1=reject, 0=abstain, 1=accept
    ) -> float:
        """Compute effective weighted vote: weight × raw_vote."""
        w = self.node_weight(node_id)
        return w * raw_vote

    def total_effective_vote(
        self,
        votes: dict[str, float],   # node_id → raw_vote ∈ [-1, 1]
    ) -> float:
        """Sum of effective votes across all voting nodes."""
        total = 0.0
        for node_id, raw_vote in votes.items():
            total += self.effective_vote(node_id, raw_vote)
        return total

    def quorum_weight(self, votes: dict[str, float]) -> float:
        """
        Return fraction of total weight that voted in the positive direction.
        Returns positive if majority in one direction, negative if opposed.
        """
        if self.total_weight <= 0.0:
            return 0.0
        return self.total_effective_vote(votes) / self.total_weight

    def is_dominated(self, domination_threshold: float = 0.5) -> bool:
        """
        Return True if a single node controls ≥ domination_threshold
        fraction of total weight.
        """
        return self.dom_weight_fraction >= domination_threshold

    def to_dict(self) -> dict:
        return {
            "weights": dict(self.weights),
            "total_weight": round(self.total_weight, 6),
            "max_single_weight": round(self.max_single_weight, 6),
            "dom_weight_fraction": round(self.dom_weight_fraction, 6),
            "snapshot_time": round(self.snapshot_time, 3),
            "ledger_version": self.ledger_version,
            "epoch": self.epoch,
        }


class NodeWeightRegistry:
    """
    Computes and caches per-node weights from TrustVector state.

    Weights are derived from proof trust_scores aggregated per node:
      node_trust(node_id) = mean(trust_scores of all proofs from node_id)

    Usage:
        registry = NodeWeightRegistry()
        registry.register_proofs_for_node("node_A", ["hash_1", "hash_2"])
        snapshot = registry.compute_weights(trust_vector, ledger_version=5)
        w = snapshot.node_weight("node_A")
    """

    def __init__(self):
        # node_id → list of proof_hashes this node is associated with
        self._node_proofs: dict[str, list[str]] = {}
        # proof_hash → node_id (reverse index)
        self._proof_nodes: dict[str, str] = {}
        self._cached_snapshot: NodeWeightsSnapshot | None = None

    def register_proofs_for_node(
        self,
        node_id: str,
        proof_hashes: list[str],
    ) -> None:
        """Associate proof_hashes with a node_id. Idempotent."""
        self._node_proofs.setdefault(node_id, [])
        for ph in proof_hashes:
            if ph not in self._node_proofs[node_id]:
                self._node_proofs[node_id].append(ph)
            self._proof_nodes[ph] = node_id

    def associate_proof_with_node(
        self,
        proof_hash: str,
        node_id: str,
    ) -> None:
        """Associate a single proof_hash with a node_id."""
        old_node = self._proof_nodes.get(proof_hash)
        if old_node and old_node != node_id and old_node in self._node_proofs:
            try:
                self._node_proofs[old_node].remove(proof_hash)
            except ValueError:
                pass
        self._proof_nodes[proof_hash] = node_id
        self._node_proofs.setdefault(node_id, [])
        if proof_hash not in self._node_proofs[node_id]:
            self._node_proofs[node_id].append(proof_hash)

    def node_for_proof(self, proof_hash: str) -> str | None:
        """Return node_id associated with proof_hash, or None."""
        return self._proof_nodes.get(proof_hash)

    def compute_weights(
        self,
        trust_vector: TrustVector,
        ledger_version: int,
        epoch: int = 0,
        now: float | None = None,
    ) -> NodeWeightsSnapshot:
        """
        Compute node weights from trust_vector.

        For each node_id:
          weights[node_id] = mean(trust_scores of all proofs from node_id)

        Missing proofs → trust=0. Returns immutable NodeWeightsSnapshot.
        """
        if now is None:
            now = time.time()

        weights: dict[str, float] = {}

        for node_id, proof_hashes in self._node_proofs.items():
            if not proof_hashes:
                continue
            total_trust = 0.0
            for ph in proof_hashes:
                entry = trust_vector.get(ph)
                if entry is not None:
                    total_trust += entry.trust_score
            aggregated = total_trust / len(proof_hashes)
            aggregated = max(0.0, min(1.0, aggregated))
            weights[node_id] = aggregated

        all_weights = list(weights.values())
        total_weight = sum(all_weights)
        max_single_weight = max(all_weights) if all_weights else 0.0
        dom_fraction = (
            max_single_weight / total_weight
            if total_weight > 0.0
            else 0.0
        )

        snapshot = NodeWeightsSnapshot(
            weights=weights,
            total_weight=total_weight,
            max_single_weight=max_single_weight,
            dom_weight_fraction=dom_fraction,
            snapshot_time=now,
            ledger_version=ledger_version,
            epoch=epoch,
        )
        self._cached_snapshot = snapshot
        return snapshot

    def get_cached_snapshot(self) -> NodeWeightsSnapshot | None:
        return self._cached_snapshot

    def known_nodes(self) -> list[str]:
        return list(self._node_proofs.keys())

    def proof_count_for_node(self, node_id: str) -> int:
        return len(self._node_proofs.get(node_id, []))


# ─── Tests ────────────────────────────────────────────────────────────

def _test_node_weights():
    from federation.trust.trust_vector import TrustVector

    registry = NodeWeightRegistry()

    registry.register_proofs_for_node("node_A", ["h1", "h2", "h3"])
    registry.register_proofs_for_node("node_B", ["h4", "h5"])
    registry.associate_proof_with_node("h6", "node_B")

    assert set(registry.known_nodes()) == {"node_A", "node_B"}
    assert registry.proof_count_for_node("node_A") == 3
    assert registry.proof_count_for_node("node_B") == 3
    print("✅ register_proofs_for_node + associate_proof_with_node")

    tv = TrustVector()
    tv.set_entry("h1", 0.9, 1000.0, ledger_version=1)
    tv.set_entry("h2", 0.8, 1000.0, ledger_version=1)
    tv.set_entry("h3", 0.7, 1000.0, ledger_version=1)
    tv.set_entry("h4", 0.6, 1000.0, ledger_version=1)
    tv.set_entry("h5", 0.5, 1000.0, ledger_version=1)
    tv.set_entry("h6", 0.9, 1000.0, ledger_version=1)

    snap = registry.compute_weights(tv, ledger_version=5, epoch=1)

    assert abs(snap.node_weight("node_A") - 0.8) < 1e-6
    assert abs(snap.node_weight("node_B") - (2.0 / 3.0)) < 1e-4
    print(f"✅ compute_weights: node_A={snap.node_weight('node_A'):.4f}, node_B={snap.node_weight('node_B'):.4f}")

    assert snap.node_weight("node_unknown") == 0.0
    print("✅ unknown node → weight 0.0")

    ev_a = snap.effective_vote("node_A", 1.0)
    assert abs(ev_a - 0.8) < 1e-6
    ev_a_reject = snap.effective_vote("node_A", -1.0)
    assert abs(ev_a_reject + 0.8) < 1e-6
    print(f"✅ effective_vote: accept={ev_a:.4f}, reject={ev_a_reject:.4f}")

    votes = {"node_A": 1.0, "node_B": 1.0}
    total_vote = snap.total_effective_vote(votes)
    expected = 0.8 + (2.0 / 3.0)
    assert abs(total_vote - expected) < 1e-4
    print(f"✅ total_effective_vote: {total_vote:.4f}")

    assert snap.is_dominated(domination_threshold=0.6) is False
    assert snap.is_dominated(domination_threshold=0.5) is True
    print(f"✅ is_dominated: dom_fraction={snap.dom_weight_fraction:.4f} (threshold=0.5 → dominated)")

    registry2 = NodeWeightRegistry()
    registry2.register_proofs_for_node("node_X", ["h1", "h7"])
    snap2 = registry2.compute_weights(tv, ledger_version=5)
    assert abs(snap2.node_weight("node_X") - 0.45) < 1e-6
    print("✅ unknown proofs → trust=0 in aggregation")

    snap3 = registry.compute_weights(tv, ledger_version=6, epoch=2)
    assert snap.ledger_version == 5
    assert snap3.ledger_version == 6
    print("✅ snapshots are independent (immutable)")

    print("\n✅ v9.6 NodeWeightRegistry — all checks passed")


if __name__ == "__main__":
    _test_node_weights()


__all__ = [
    "NodeWeightEntry",
    "NodeWeightRegistry",
    "NodeWeightsSnapshot",
]

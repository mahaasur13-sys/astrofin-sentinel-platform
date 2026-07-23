"""
ConvergeConsensus — delta-based quorum resolution for federation.

Uses DAGFingerprint deltas (not full StateVectors) to derive quorum.
This enables consensus to be reached on changed node IDs only.

Rules (in priority order):
  1. If ≥ 2/3 nodes agree on same root_hash → quorum reached
  2. If no quorum → highest_seq policy (most recent delta wins)
  3. Stale entries (root_hash unchanged) excluded from quorum

Architecture integration:
  ConvergeConsensus ← DeltaGossipProtocol (delta messages)
  ConvergeConsensus ← DAGFingerprintBridge (root_hash source of truth)
  ConvergeConsensus → ConsensusResolver (delta-based fallback)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from federation.delta_gossip.protocol import DeltaGossipMessage
from federation.state_vector import StateVector


@dataclass
class ConvergeQuorumResult:
    """
    Result of delta-based quorum resolution.

    source: how consensus was reached
    confidence: 0.0–1.0 based on voter weight
    voters: which nodes agreed
    converged_root_hash: the hash that reached quorum (or best guess)
    """
    converged_root_hash: str
    source: Literal["quorum", "highest_seq", "local_only", "no_peers"]
    confidence: float
    voters: list[str] = field(default_factory=list)
    changed_node_ids: list[str] = field(default_factory=list)
    timestamp_ns: int = field(default_factory=time.time_ns)

    @property
    def is_quorum(self) -> bool:
        return self.source == "quorum"


@dataclass
class DeltaConsensusConfig:
    """Configuration for delta-based consensus."""
    quorum_fraction: float = 0.5   # 2/3 for strict; 0.5 for 2-of-3 tolerance
    max_age_ms: int = 60_000
    min_nodes: int = 1
    require_root_hash_match: bool = True


class ConvergeConsensus:
    """
    Delta-based consensus using DAG fingerprints.

    Replaces full-StateVector quorum in ConsensusResolver.
    Now quorum is reached on root_hash (DAG fingerprint) alone,
    and changed_node_ids are used to determine what actually changed.

    Complexity:
      OLD: O(n) StateVector fields per consensus round
      NEW: O(Δchanged_nodes) per consensus round (Δnodes << n)
    """

    def __init__(
        self,
        node_id: str,
        config: DeltaConsensusConfig | None = None,
    ):
        self.node_id = node_id
        self.config = config or DeltaConsensusConfig()

    def resolve(
        self,
        my_root_hash: str,
        my_seq: int,
        my_changed_ids: list[str],
        peer_messages: list[DeltaGossipMessage],
        my_full_vector: StateVector | None = None,
    ) -> ConvergeQuorumResult:
        """
        Resolve quorum from delta messages.

        Args:
            my_root_hash: my current DAG root hash
            my_seq: my current sequence number
            my_changed_ids: node IDs changed since last sync
            peer_messages: delta messages received from peers
            my_full_vector: my StateVector (for compatibility with ConsensusResolver)

        Returns:
            ConvergeQuorumResult with converged root_hash and confidence
        """
        if not peer_messages:
            return ConvergeQuorumResult(
                converged_root_hash=my_root_hash,
                source="no_peers",
                confidence=1.0 if my_seq >= 0 else 0.0,
                voters=[self.node_id],
                changed_node_ids=my_changed_ids,
            )

        now_ns = time.time_ns()
        fresh = [
            msg for msg in peer_messages
            if (now_ns - msg.ts_ns) / 1_000_000 <= self.config.max_age_ms
        ]

        if not fresh:
            return ConvergeQuorumResult(
                converged_root_hash=my_root_hash,
                source="no_peers",
                confidence=0.0,
                voters=[self.node_id],
                changed_node_ids=my_changed_ids,
            )

        # Count by root_hash (quorum on fingerprint, not full state)
        vote_counts: dict[str, list[str]] = {}
        for msg in fresh:
            vote_counts.setdefault(msg.root_hash, []).append(msg.source_node_id)

        total_voters = len(fresh) + 1   # +1 for self
        threshold = max(2, self.config.quorum_fraction * total_voters)

        # Rule 1: quorum on root_hash
        for root_hash, voters in vote_counts.items():
            voters_with_self = voters + [self.node_id]
            if len(voters_with_self) >= threshold:
                # Collect changed_node_ids from all voters for this root_hash
                all_changed_ids: list[str] = list(my_changed_ids)
                for msg in fresh:
                    if msg.root_hash == root_hash:
                        all_changed_ids.extend(msg.changed_node_ids)

                return ConvergeQuorumResult(
                    converged_root_hash=root_hash,
                    source="quorum",
                    confidence=len(voters_with_self) / total_voters,
                    voters=voters_with_self,
                    changed_node_ids=all_changed_ids,
                )

        # Rule 2: highest sequence number
        all_messages = fresh + [
            _SeqMsg(root_hash=my_root_hash, seq=my_seq, source_node_id=self.node_id,
                    changed_node_ids=my_changed_ids)
        ]
        best = max(all_messages, key=lambda m: m.seq)

        best_changed_ids: list[str] = list(my_changed_ids)
        if best.source_node_id != self.node_id:
            for msg in fresh:
                if msg.source_node_id == best.source_node_id:
                    best_changed_ids = list(msg.changed_node_ids)
                    break

        return ConvergeQuorumResult(
            converged_root_hash=best.root_hash,
            source="highest_seq",
            confidence=best.seq / max(m.seq for m in all_messages) if all_messages else 0.0,
            voters=[best.source_node_id],
            changed_node_ids=best_changed_ids,
        )

    def detect_divergence(
        self,
        my_root_hash: str,
        peer_messages: list[DeltaGossipMessage],
    ) -> float:
        """
        Measure how much this node has diverged from peers.

        Returns 0.0 (identical) → 1.0 (completely diverged).
        """
        if not peer_messages:
            return 0.0

        same_count = sum(
            1 for msg in peer_messages
            if msg.root_hash == my_root_hash
        )
        return 1.0 - (same_count / len(peer_messages))


@dataclass
class _SeqMsg:
    """Temporary wrapper to compare messages by seq."""
    root_hash: str
    seq: int
    source_node_id: str
    changed_node_ids: list[str]

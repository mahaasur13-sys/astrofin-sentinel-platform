from typing import Dict, List, Optional
import time

from .models import ConsensusResult


class QuorumConfig:
    def __init__(self, max_age_ms: int = 60_000):
        self.max_age_ms = max_age_ms


class ConsensusResolver:
    def __init__(self, node_id: str, config: Optional[QuorumConfig] = None):
        self.node_id = node_id
        self.config = config or QuorumConfig()

    # ---------------------------
    # SAFE CHECK
    # ---------------------------
    def is_safe_remote_theta(self, policy: Dict, vec) -> bool:
        # envelope_state safety
        if getattr(vec, "envelope_state", None) == "collapse":
            return False

        # drift safety
        if getattr(vec, "drift_score", 0) > 0.9:
            return False

        # stale check
        now = time.time_ns()
        max_age_ns = self.config.max_age_ms * 1_000_000
        if (now - getattr(vec, "timestamp_ns", now)) > max_age_ns:
            return False

        return True

    # ---------------------------
    # CORE RESOLVE
    # ---------------------------
    def resolve(self, my, peers: List, local_theta: str) -> ConsensusResult:
        all_nodes = [my] + list(peers)

        now = time.time_ns()
        max_age_ns = self.config.max_age_ms * 1_000_000

        # filter stale
        fresh = [
            v for v in all_nodes
            if (now - getattr(v, "timestamp_ns", now)) <= max_age_ns
        ]

        # group by theta_hash
        groups: Dict[str, List] = {}
        for v in fresh:
            groups.setdefault(v.theta_hash, []).append(v)

        total = len(fresh)
        quorum_threshold = (total // 2) + 1 if total > 0 else 1

        # find best group
        best_theta = None
        best_group = []

        for theta, group in groups.items():
            if len(group) > len(best_group):
                best_group = group
                best_theta = theta

        # ---------------------------
        # QUORUM SUCCESS
        # ---------------------------
        if best_group and len(best_group) >= quorum_threshold:
            voters = [v.node_id for v in best_group]
            confidence = len(best_group) / max(total, 1)

            return ConsensusResult(
                theta_hash=best_theta,
                source="quorum",
                is_quorum=True,
                voters=voters,
                confidence=confidence,
            )

        # ---------------------------
        # FALLBACK: highest stability
        # ---------------------------
        best = max(
            all_nodes,
            key=lambda v: (
                getattr(v, "stability_score", 0.0),
                -getattr(v, "drift_score", 0.0),
            ),
        )

        voters = [best.node_id]

        confidence = len(voters) / max(total, 1)

        return ConsensusResult(
            theta_hash=best.theta_hash,
            source="highest_stability",
            is_quorum=False,
            voters=voters,
            confidence=confidence,
        )

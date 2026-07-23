from dataclasses import dataclass
from typing import List, Dict, Optional
import time


@dataclass
class QuorumConfig:
    max_age_ms: int = 30_000


@dataclass
class ConsensusResult:
    is_quorum: bool
    source: str
    theta_hash: str
    confidence: float
    voters: List[str]


class ConsensusResolver:
    def __init__(self, node_id: str, config: Optional[QuorumConfig] = None):
        self.node_id = node_id
        self.config = config or QuorumConfig()

    # -------------------------
    # SAFE ACCESS HELPERS
    # -------------------------
    def _is_fresh(self, vec) -> bool:
        if not hasattr(vec, "timestamp_ns"):
            return True
        age_ms = (time.time_ns() - vec.timestamp_ns) / 1e6
        return age_ms <= self.config.max_age_ms

    def _get(self, vec, key, default=None):
        return getattr(vec, key, default)

    # -------------------------
    # SAFETY CHECK
    # -------------------------
    def is_safe_remote_theta(self, policy: Dict, vec) -> bool:
        if getattr(vec, "envelope_state", None) == "collapse":
            return False

        if not self._is_fresh(vec):
            return False

        if getattr(vec, "drift_score", 0) > 0.9:
            return False

        return True

    # -------------------------
    # MAIN RESOLUTION LOGIC
    # -------------------------
    def resolve(self, my, peers: List, local_theta: str) -> ConsensusResult:
        all_nodes = [my] + peers

        # filter fresh + safe
        valid = [
            v for v in all_nodes
            if self._is_fresh(v) and self.is_safe_remote_theta({}, v)
        ]

        # -------------------------
        # group by theta_hash
        # -------------------------
        groups: Dict[str, List] = {}
        for v in valid:
            groups.setdefault(v.theta_hash, []).append(v)

        # quorum threshold
        total = len(valid)
        quorum_threshold = 2 if total <= 3 else (total // 2 + 1)

        best_theta = None
        best_group = []

        for theta, group in groups.items():
            if len(group) > len(best_group):
                best_theta = theta
                best_group = group

        # -------------------------
        # QUORUM CASE
        # -------------------------
        if best_group and len(best_group) >= quorum_threshold:
            return ConsensusResult(
                is_quorum=True,
                source="quorum",
                theta_hash=best_theta,
                confidence=1.0,
                voters=[v.node_id for v in best_group],
            )

        # -------------------------
        # FALLBACK: highest stability
        # -------------------------
        best = max(
            valid,
            key=lambda v: (
                getattr(v, "stability_score", 0),
                -getattr(v, "drift_score", 0),
            ),
            default=my
        )

        return ConsensusResult(
            is_quorum=False,
            source="highest_stability",
            theta_hash=best.theta_hash,
            confidence=getattr(best, "stability_score", 1.0),
            voters=[best.node_id],
        )

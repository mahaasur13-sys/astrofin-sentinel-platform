from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time


# =========================
# CONFIG (missing in tests)
# =========================
@dataclass
class QuorumConfig:
    max_age_ms: int = 60_000


# =========================
# RESULT MODEL
# =========================
@dataclass
class ConsensusResult:
    is_quorum: bool
    source: str
    theta_hash: str
    confidence: float
    voters: List[str]


# =========================
# RESOLVER
# =========================
class ConsensusResolver:
    def __init__(self, node_id: str, config: Optional[QuorumConfig] = None):
        self.node_id = node_id
        self.config = config or QuorumConfig()

    # -------------------------
    # helpers
    # -------------------------
    def _hash(self, vec) -> str:
        return getattr(vec, "theta_hash", None) or getattr(vec, "hash", "")

    def _stale(self, vec) -> bool:
        ts = getattr(vec, "timestamp_ns", 0)
        age = time.time_ns() - ts
        return age > self.config.max_age_ms * 1_000_000

    def _stability(self, vec) -> float:
        return getattr(vec, "stability_score", 0.0)

    def _drift(self, vec) -> float:
        return getattr(vec, "drift_score", 0.0)

    # -------------------------
    # main resolve
    # -------------------------
    def resolve(self, my, peers, local_hash: str) -> ConsensusResult:
        nodes = [my] + list(peers)

        fresh = [v for v in nodes if not self._stale(v)]

        # group by hash
        groups: Dict[str, List] = {}
        for v in fresh:
            h = self._hash(v)
            groups.setdefault(h, []).append(v)

        total = len(fresh)
        quorum_threshold = max(2, (total // 2) + 1)

        winner_hash = None
        winner_group = []

        for h, vecs in groups.items():
            if len(vecs) >= quorum_threshold:
                winner_hash = h
                winner_group = vecs

        # QUORUM
        if winner_hash:
            return ConsensusResult(
                is_quorum=True,
                source="quorum",
                theta_hash=winner_hash,
                confidence=len(winner_group) / total if total else 0.0,
                voters=[getattr(v, "node_id", "") for v in winner_group],
            )

        # FALLBACK: highest stability
        best = max(fresh, key=self._stability)

        tied = [v for v in fresh if self._stability(v) == self._stability(best)]
        if len(tied) > 1:
            best = min(tied, key=self._drift)

        return ConsensusResult(
            is_quorum=False,
            source="highest_stability",
            theta_hash=self._hash(best),
            confidence=self._stability(best),
            voters=[getattr(best, "node_id", "")],
        )

    # -------------------------
    # safety check
    # -------------------------
    def is_safe_remote_theta(self, policy: Dict[str, Any], vec) -> bool:
        if self._stale(vec):
            return False

        if getattr(vec, "envelope_state", None) == "collapse":
            return False

        if getattr(vec, "drift_score", 0.0) > 0.9:
            return False

        return True

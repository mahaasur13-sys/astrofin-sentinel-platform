"""StateVector — core unit of exchange between federation nodes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Literal

from core.deterministic import DeterministicClock
from orchestration.v8_2b_controlled_autocorrection.severity_mapper import SeverityLevel


@dataclass(slots=True)
class StateVector:
    """Immutable snapshot of a node's control state for gossip exchange."""

    node_id: str
    theta_hash: str
    envelope_state: Literal["stable", "warning", "critical", "collapse"]
    drift_score: float
    stability_score: float
    timestamp_ns: int = field(default_factory=lambda: DeterministicClock.get_tick_ns())

    # --- derived fields --------------------------------------------------
    @property
    def severity(self) -> SeverityLevel:
        if self.envelope_state == "collapse":
            return SeverityLevel.CRITICAL
        if self.envelope_state == "critical":
            return SeverityLevel.HIGH
        if self.envelope_state == "warning":
            return SeverityLevel.MEDIUM
        return SeverityLevel.NEGLIGIBLE

    @property
    def age_ms(self) -> float:
        return (DeterministicClock.get_tick_ns() - self.timestamp_ns) / 1_000_000

    def is_stale(self, max_age_ms: float = 30_000) -> bool:
        return self.age_ms > max_age_ms

    # --- utility ---------------------------------------------------------
    @staticmethod
    def hash_theta(theta: dict) -> str:
        """Stable hash of a theta dict."""
        import json
        canonical = json.dumps(theta, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def __str__(self) -> str:
        return (
            f"StateVector(node={self.node_id} "
            f"θ_hash={self.theta_hash} "
            f"envelope={self.envelope_state} "
            f"drift={self.drift_score:.3f} "
            f"stability={self.stability_score:.3f} "
            f"age={self.age_ms:.1f}ms)"
        )

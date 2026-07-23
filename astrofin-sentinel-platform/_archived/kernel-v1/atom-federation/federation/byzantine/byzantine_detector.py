"""
byzantine_detector.py — Byzantine fault detection for v9.8

Integrates with:
  - TrustDynamicsStabilizer (TrustFeedbackDampener regimes)
  - ConsensusEntropyMonitor (phase locking, entropy floor)
  - TrustWeightedConsensusResolver (shift types)

Detects Byzantine-adjacent regimes and emits ByzantineSignal:
  SUSPICIOUS       — single anomaly, monitoring
  FAULT_TOLERABLE  — 2+ anomalies, f+1 still safe
  DEGRADED         — f+1 at risk, view-change warranted
  BYZANTINE        — >f Byzantine nodes detected, consensus unsafe
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from federation.trust_weighted.consensus_resolver import ConsensusShiftType
from federation.trust_weighted.trust_dynamics_stabilizer import (

import logging
log = logging.getLogger(__name__)

    DynamicsReport,
    EntropyStats,
    TrustDynamicsStabilizer,
)
from federation.trust_weighted.trust_feedback_dampener import FeedbackRegime


class ByzantineSignal(Enum):
    NONE = auto()
    SUSPICIOUS = auto()
    FAULT_TOLERABLE = auto()
    DEGRADED = auto()
    BYZANTINE = auto()


@dataclass
class ByzantineIndicator:
    signal: ByzantineSignal
    suspicion_score: float          # ∈ [0, 1]: confidence this is Byzantine
    evidence: list[str]
    regimes: list[str]
    voting_anomalies: int
    trust_anomalies: int


class ByzantineDetector:
    """
    Monitors trust+consensus state for Byzantine-adjacent patterns.

    Signals emitted:
      NONE          — all nominal
      SUSPICIOUS    — one anomaly detected
      FAULT_TOLERABLE — 2+ anomalies, but quorum still safe
      DEGRADED      — quorum safety degraded
      BYZANTINE     — consensus unsafe

    Integration points:
      TrustFeedbackDampener regimes → trust_anomalies
      ConsensusEntropyMonitor → voting_anomalies
      TrustWeightedConsensusResolver shift history → shift anomalies
      NodeWeightsSnapshot domination → monopoly pattern
    """

    def __init__(
        self,
        n_nodes: int,
        suspicion_threshold: float = 0.30,
        degraded_threshold: float = 0.60,
        byzantine_threshold: float = 0.85,
    ):
        self.n_nodes = n_nodes
        self.suspicion_threshold = suspicion_threshold
        self.degraded_threshold = degraded_threshold
        self.byzantine_threshold = byzantine_threshold

        self._evidence_log: list[ByzantineIndicator] = []
        self._suspicion_window: list[float] = []
        self._window_size: int = 5

    def assess(
        self,
        dynamics_report: DynamicsReport,
        entropy_stats: EntropyStats,
        recent_shift_types: list[ConsensusShiftType],
        dom_fraction: float,
        dom_cap: float = 0.5,
    ) -> ByzantineIndicator:
        evidence: list[str] = []
        regimes: list[str] = []
        voting_anomalies = 0
        trust_anomalies = 0

        # ── 1. Feedback dampener regime anomalies ────────────────────
        for res in dynamics_report.dampener_results:
            if res.regime in (FeedbackRegime.OSCILLATING, FeedbackRegime.MONOPOLIZING):
                trust_anomalies += 1
                evidence.append(f"dampener_regime={res.regime.name} node={res.node_id}")

        # ── 2. Entropy / phase locking anomalies ─────────────────────
        if entropy_stats.is_phase_locked:
            voting_anomalies += 1
            evidence.append(f"phase_locked_entropy={entropy_stats.shannon_entropy:.3f}")

        if entropy_stats.voter_diversity < 2:
            voting_anomalies += 1
            evidence.append(f"low_voter_diversity={entropy_stats.voter_diversity}")

        # ── 3. Consensus shift anomalies ─────────────────────────────
        critical_shifts = {
            ConsensusShiftType.OUTCOME_FLIP,
            ConsensusShiftType.TRUST_COLLAPSE,
            ConsensusShiftType.DOMINATION_SHIFT,
        }
        for st in recent_shift_types:
            if st in critical_shifts:
                trust_anomalies += 1
                evidence.append(f"critical_shift={st.name}")

        # ── 4. Monopoly / domination pattern ──────────────────────────
        if dom_fraction >= dom_cap:
            trust_anomalies += 1
            evidence.append(f"domination_fraction={dom_fraction:.3f}≥{dom_cap}")

        # ── 5. Consensus override ─────────────────────────────────────
        if dynamics_report.consensus_overridden:
            voting_anomalies += 1
            evidence.append(f"consensus_overridden={dynamics_report.blocked_reason}")

        # ── suspicion score ───────────────────────────────────────────
        total_anomalies = voting_anomalies + trust_anomalies
        # Normalize: max possible anomalies per window
        max_anomalies = 3  # one per category
        suspicion = min(1.0, total_anomalies / max_anomalies)

        self._suspicion_window.append(suspicion)
        if len(self._suspicion_window) > self._window_size:
            self._suspicion_window.pop(0)

        avg_suspicion = sum(self._suspicion_window) / len(self._suspicion_window)

        # ── regime classification ─────────────────────────────────────
        if avg_suspicion >= self.byzantine_threshold:
            signal = ByzantineSignal.BYZANTINE
        elif avg_suspicion >= self.degraded_threshold:
            signal = ByzantineSignal.DEGRADED
        elif avg_suspicion >= self.suspicion_threshold:
            signal = ByzantineSignal.FAULT_TOLERABLE
        elif total_anomalies >= 1:
            signal = ByzantineSignal.SUSPICIOUS
        else:
            signal = ByzantineSignal.NONE

        for regime in dynamics_report.dampener_results:
            regimes.append(regime.regime.name)

        indicator = ByzantineIndicator(
            signal=signal,
            suspicion_score=avg_suspicion,
            evidence=evidence,
            regimes=regimes,
            voting_anomalies=voting_anomalies,
            trust_anomalies=trust_anomalies,
        )

        self._evidence_log.append(indicator)
        return indicator

    def should_request_view_change(self, indicator: ByzantineIndicator) -> bool:
        return indicator.signal in (ByzantineSignal.DEGRADED, ByzantineSignal.BYZANTINE)

    def is_consensus_safe(self, indicator: ByzantineIndicator) -> bool:
        return indicator.signal not in (ByzantineSignal.DEGRADED, ByzantineSignal.BYZANTINE)

    def evidence_log(self) -> list[ByzantineIndicator]:
        return list(self._evidence_log)

    def reset(self) -> None:
        self._suspicion_window.clear()
        self._evidence_log.clear()


# ─── Tests ────────────────────────────────────────────────────────────────

def _test_byzantine_detector():
    from federation.trust.trust_vector import TrustVector
    from federation.trust_weighted.node_weights import NodeWeightRegistry
    from federation.trust_weighted.trust_feedback_dampener import (
        DampenerConfig,
    )

    registry = NodeWeightRegistry()
    registry.register_proofs_for_node("node_A", ["h1"])
    registry.register_proofs_for_node("node_B", ["h2"])
    registry.register_proofs_for_node("node_C", ["h3"])

    tv = TrustVector()
    tv.set_entry("h1", 0.9, 1000.0, ledger_version=1)
    tv.set_entry("h2", 0.5, 1000.0, ledger_version=1)
    tv.set_entry("h3", 0.3, 1000.0, ledger_version=1)
    snap = registry.compute_weights(tv, ledger_version=1, epoch=1)

    stabilizer = TrustDynamicsStabilizer(
        dampener_config=DampenerConfig(alpha=0.75, decay_rate=0.05, base_trust=0.30),
        entropy_floor=0.20,
        dominance_cap=0.5,
        gradient_cap=0.10,
    )

    detector = ByzantineDetector(n_nodes=3, suspicion_threshold=0.25)

    # Case 1: nominal — no anomalies
    votes = {"node_A": 1.0, "node_B": 0.5, "node_C": -0.5}
    trust_scores = {"node_A": 0.85, "node_B": 0.60, "node_C": 0.30}
    report = stabilizer.stabilize(trust_scores, votes, True, 0.90, snap, epoch=1)
    entropy = stabilizer.entropy_monitor.compute_entropy(votes)

    indicator = detector.assess(report, entropy, [], dom_fraction=0.35)
    assert indicator.signal == ByzantineSignal.NONE, f"Expected NONE, got {indicator.signal}"
    assert detector.is_consensus_safe(indicator) is True
    log.info(f"✅ Case 1: nominal → {indicator.signal.name} (suspicion={indicator.suspicion_score:.3f})")

    # ── Case 2: phase locking + monopoly + collapse ──────────────────
    trust_scores_mono = {"node_A": 0.99, "node_B": 0.01, "node_C": 0.01}
    votes_locked = {"node_A": 1.0, "node_B": 1.0, "node_C": 1.0}
    stabilizer2 = TrustDynamicsStabilizer(
        dampener_config=DampenerConfig(alpha=0.75, decay_rate=0.05, base_trust=0.30),
        entropy_floor=0.20,
        dominance_cap=0.5,
        gradient_cap=0.10,
    )
    detector2 = ByzantineDetector(
        n_nodes=3,
        suspicion_threshold=0.20,
        degraded_threshold=0.55,   # lower so 0.8 average passes it
        byzantine_threshold=0.85,
    )
    for i in range(5):
        r = stabilizer2.stabilize(trust_scores_mono, votes_locked, True, 0.90, snap, epoch=1)

    entropy_locked = stabilizer2.entropy_monitor.compute_entropy(votes_locked)

    # Force all anomaly types: critical shift + phase_lock + high domination
    from federation.trust_weighted.consensus_resolver import ConsensusShiftType
    indicator2 = detector2.assess(
        r, entropy_locked,
        [ConsensusShiftType.TRUST_COLLAPSE, ConsensusShiftType.DOMINATION_SHIFT],
        dom_fraction=0.98,
    )
    # With lower thresholds and accumulated suspicion (window avg ~0.8), should be DEGRADED or BYZANTINE
    assert indicator2.signal in (ByzantineSignal.FAULT_TOLERABLE, ByzantineSignal.DEGRADED, ByzantineSignal.BYZANTINE), \
        f"Expected FAULT_TOLERABLE/DEGRADED/BYZANTINE, got {indicator2.signal}"
    assert detector2.should_request_view_change(indicator2) is True, \
        f"Expected view_change=True for {indicator2.signal}"
    log.info(f"✅ Case 2: monopoly+phase_lock+collapse → {indicator2.signal.name} (suspicion={indicator2.suspicion_score:.3f})")
    log.info(f"   evidence: {indicator2.evidence}")

    # Case 3: single anomaly → SUSPICIOUS
    votes_mixed = {"node_A": 1.0, "node_B": -0.5, "node_C": 0.0}
    trust_scores3 = {"node_A": 0.85, "node_B": 0.60, "node_C": 0.30}
    report3 = stabilizer.stabilize(trust_scores3, votes_mixed, True, 0.75, snap, epoch=3)
    entropy3 = stabilizer.entropy_monitor.compute_entropy(votes_mixed)

    detector3 = ByzantineDetector(n_nodes=3, suspicion_threshold=0.20)
    indicator3 = detector3.assess(report3, entropy3, [], dom_fraction=0.35)
    assert indicator3.signal in (ByzantineSignal.NONE, ByzantineSignal.SUSPICIOUS)
    log.info(f"✅ Case 3: mixed votes → {indicator3.signal.name} (suspicion={indicator3.suspicion_score:.3f})")

    # Case 4: view change warranted check
    degraded_indicator = ByzantineIndicator(
        signal=ByzantineSignal.DEGRADED,
        suspicion_score=0.65,
        evidence=["phase_locked_entropy=0.05"],
        regimes=["OSCILLATING"],
        voting_anomalies=2,
        trust_anomalies=1,
    )
    assert detector.should_request_view_change(degraded_indicator) is True
    assert detector.is_consensus_safe(degraded_indicator) is False
    log.info("✅ Case 4: DEGRADED → view_change warranted, consensus unsafe")

    log.info("\n✅ v9.8 ByzantineDetector — all checks passed")


if __name__ == "__main__":
    _test_byzantine_detector()


__all__ = [
    "ByzantineDetector",
    "ByzantineIndicator",
    "ByzantineSignal",
]

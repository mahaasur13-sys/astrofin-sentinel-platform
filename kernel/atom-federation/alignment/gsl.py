"""
gsl.py — v10.9 Global Soundness Layer
Validates internal convergence against observable reality.
Extends v10.8 UST with real-world boundary model.

S(t) = α·GCPL_C + β·BCIL_Safety + γ·ADLR_Liveness − δ·RealityDrift
S(t) ∈ [0,1]; thresholds: SAFE≥0.7, DEGRADED[0.4,0.7), FAILURE<0.4

Failure modes detected:
  F1: Reality Divergence Collapse — GCPL converges but RealityDrift grows
  F2: False Convergence — S high but L2 mismatch high
  F3: Observation Lag Trap — internal stable, external stale
  F4: Branch-Observation Split — multiple branches map to same observed state
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import logging
log = logging.getLogger(__name__)


THRESHOLD_SAFE = 0.70
THRESHOLD_DEGRADED = 0.40
MAX_DRIFT = 1.0


@dataclass
class InternalState:
    gcpl_convergence: float
    bc_safety_score: float
    adlr_liveness: float
    bcil_veto_active: bool
    bc_branch_count: int = 1
    bc_oscillation_detected: bool = False
    adlr_stage: str = "NOMINAL"


@dataclass
class ObservedState:
    external_snapshot: dict = field(default_factory=dict)
    sensor_view: dict = field(default_factory=dict)
    timestamp_ns: int = 0
    is_stale: bool = False
    lag_ms: float = 0.0
    branch_observations: dict = field(default_factory=dict)
    observed_node_ids: set = field(default_factory=set)


@dataclass
class SoundnessReport:
    score: float
    region: Literal["SAFE", "DEGRADED", "FAILURE"]
    drift: float
    actions: list
    gcpl_c: float
    bc_safety: float
    adlr_live: float
    reality_alignment: float
    observation_latency: float
    branch_observation_entropy: float
    false_convergence_rate: float
    f1_divergence_collapse: bool = False
    f2_false_convergence: bool = False
    f3_lag_trap: bool = False
    f4_branch_split: bool = False
    vetoed: bool = False
    description: str = ""


def _kl(p: float, q: float, eps: float = 1e-9) -> float:
    p_clamped = max(eps, min(1 - eps, p))
    q_clamped = max(eps, min(1 - eps, q))
    return p_clamped * math.log(p_clamped / q_clamped) + (1 - p_clamped) * math.log((1 - p_clamped) / (1 - q_clamped))


class RealityDriftComputer:
    """Computes RealityDrift = KL(Model||Observed) + L1 + L2 mismatches."""

    def compute(self, internal: InternalState, observed: ObservedState, gcpl_metrics=None):
        # KL divergence: model convergence vs observed alignment
        if observed.is_stale:
            obs_align = 0.20
        elif not observed.observed_node_ids:
            obs_align = 0.50
        else:
            obs_align = 0.85
        kl = min(1.0, _kl(internal.gcpl_convergence, obs_align))

        # L1: structural mismatch via branch count vs observation diversity
        obs_div = len(observed.branch_observations) if observed.branch_observations else 1
        ratio = internal.bc_branch_count / max(obs_div, 1)
        if ratio > 2.0:
            l1 = 1.0
        elif ratio > 1.5:
            l1 = 0.60
        else:
            l1 = 0.0

        # L2: causal mismatch via oscillation + observation lag
        lag_score = min(observed.lag_ms / 5000.0, 1.0) if observed.lag_ms else 0.0
        osc_score = 1.0 if internal.bc_oscillation_detected else 0.0
        if internal.bc_oscillation_detected and observed.is_stale:
            l2 = 1.0
        else:
            l2 = max(lag_score, osc_score)

        total = min(1.0, 0.40 * kl + 0.30 * l1 + 0.30 * l2)
        return min(1.0, total), kl, l1, l2


class GSL:
    """
    Global Soundness Layer.

    Reads: GCPL convergence, BCIL safety, ADLR liveness.
    Writes: SoundnessReport with actions.
    Does NOT: change GCPL state, violate BCIL quorum, call ADLR TERMINAL directly.
    """

    def __init__(
        self,
        alpha: float = 0.30,
        eta: float = 0.25,
        gamma: float = 0.25,
        delta: float = 0.20,
        drift_threshold: float = 0.35,
        lag_threshold_ms: float = 2000.0,
    ):
        self.alpha = alpha
        self.eta = eta
        self.gamma = gamma
        self.delta = delta
        self.drift_threshold = drift_threshold
        self.lag_threshold_ms = lag_threshold_ms
        self._dc = RealityDriftComputer()
        self._history: list[SoundnessReport] = []

    def evaluate(
        self,
        internal: InternalState,
        observed: ObservedState,
        gcpl_metrics=None,
    ) -> SoundnessReport:
        # 1. Compute RealityDrift
        drift, kl, l1, l2 = self._dc.compute(internal, observed)

        # 2. Compute global score S(t)
        internal_score = (
            self.alpha * internal.gcpl_convergence
            + self.eta * internal.bc_safety_score
            + self.gamma * internal.adlr_liveness
        )
        score = min(1.0, max(0.0, internal_score - self.delta * (drift / MAX_DRIFT)))

        # 3. Determine region
        if score >= THRESHOLD_SAFE:
            region: Literal["SAFE", "DEGRADED", "FAILURE"] = "SAFE"
        elif score >= THRESHOLD_DEGRADED:
            region = "DEGRADED"
        else:
            region = "FAILURE"

        # 4. Detect failure modes
        f1 = self._detect_f1(internal, drift)
        f2 = self._detect_f2(score, l2)
        f3 = self._detect_f3(internal, observed)
        f4 = self._detect_f4(internal, observed)

        # 5. Generate actions
        actions = self._generate_actions(region, drift, f1, f2, f3, f4, internal)

        # 6. Build report
        report = SoundnessReport(
            score=score,
            region=region,
            drift=drift,
            actions=actions,
            gcpl_c=internal.gcpl_convergence,
            bc_safety=internal.bc_safety_score,
            adlr_live=internal.adlr_liveness,
            reality_alignment=1.0 - drift,
            observation_latency=observed.lag_ms,
            branch_observation_entropy=self._branch_entropy(internal, observed),
            false_convergence_rate=self._false_convergence_rate(),
            f1_divergence_collapse=f1,
            f2_false_convergence=f2,
            f3_lag_trap=f3,
            f4_branch_split=f4,
            vetoed=internal.bcil_veto_active,
            description=f"[{region}] drift={drift:.3f} actions={actions}",
        )
        self._history.append(report)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        return report

    # ── Failure mode detectors ─────────────────────────────────────────────

    def _detect_f1(self, internal: InternalState, drift: float) -> bool:
        """F1: GCPL converges but RealityDrift increases."""
        if not self._history:
            return False
        prev = self._history[-1]
        return (
            internal.gcpl_convergence >= 0.75
            and drift > 0.30
            and drift > prev.drift
        )

    def _detect_f2(self, score: float, l2: float) -> bool:
        """F2: S(t) high but L2 mismatch high."""
        return score >= 0.65 and l2 >= 0.60

    def _detect_f3(self, internal: InternalState, observed: ObservedState) -> bool:
        """F3: internal stable but external snapshot is stale."""
        return (
            internal.adlr_liveness >= 0.70
            and (
                observed.is_stale
                or observed.lag_ms > self.lag_threshold_ms
            )
        )

    def _detect_f4(self, internal: InternalState, observed: ObservedState) -> bool:
        """F4: multiple branches map to same observed state."""
        if not observed.branch_observations:
            return False
        obs_count = len(observed.branch_observations)
        return obs_count < internal.bc_branch_count and internal.bc_branch_count > 2

    # ── Action generation ───────────────────────────────────────────────────

    def _generate_actions(
        self,
        region: str,
        drift: float,
        f1: bool,
        f2: bool,
        f3: bool,
        f4: bool,
        internal: InternalState,
    ) -> list:
        actions: list = []

        if region == "FAILURE" or drift > self.drift_threshold:
            if not internal.bcil_veto_active:
                actions.extend(["request_reconciliation", "EPOCH_RESET"])

        if f1:
            actions.append("monitor_reality_drift_alert")
        if f2:
            actions.append("force_L2_recheck")
        if f3:
            actions.append("refresh_observation")
        if f4:
            actions.append("branch_separation")

        # Soft veto via BCIL (never hard override)
        if drift > 0.40 and not internal.bcil_veto_active:
            actions.append("request_BCIL_soft_veto")

        return actions if actions else ["none"]

    # ── Utility metrics ───────────────────────────────────────────────────

    def _branch_entropy(self, internal: InternalState, observed: ObservedState) -> float:
        """Branch-observation entropy: how many branches share observations."""
        if internal.bc_branch_count <= 1:
            return 0.0
        obs_pb = len(observed.branch_observations) if observed.branch_observations else 1
        ratio = internal.bc_branch_count / max(obs_pb, 1)
        if ratio <= 1.0:
            return 0.0
        return math.log(ratio)

    def _false_convergence_rate(self) -> float:
        """Fraction of recent SAFE reports where drift was actually high."""
        if len(self._history) < 3:
            return 0.0
        recent = self._history[-10:]
        false_positives = sum(
            1 for r in recent if r.region == "SAFE" and r.drift > 0.25
        )
        return false_positives / len(recent)


# ─── Tests ─────────────────────────────────────────────────────────────────

def _run_tests():
    log.info("=== v10.9 GSL Tests ===")

    def check(name: str, cond: bool, detail: str = "") -> bool:
        log.info(f"  {'✅' if cond else '❌'} {name}" + (f": {detail}" if detail else ""))
        return cond

    ok = True
    gsl = GSL()

    # T1: SAFE — stable GCPL + low drift
    r = gsl.evaluate(
        InternalState(gcpl_convergence=0.90, bc_safety_score=0.95,
                      adlr_liveness=0.85, bcil_veto_active=False),
        ObservedState(lag_ms=100.0, observed_node_ids={"a", "b", "c"}),
    )
    ok &= check("T1 SAFE region", r.region == "SAFE", f"score={r.score:.3f}")
    ok &= check("T1 low drift", r.drift < 0.30, f"drift={r.drift:.3f}")
    ok &= check("T1 no failure modes",
                not (r.f1_divergence_collapse or r.f2_false_convergence
                     or r.f3_lag_trap or r.f4_branch_split))
    ok &= check("T1 no actions needed", r.actions == ["none"])

    # T2: DEGRADED — GCPL converges + drift detected
    r2 = gsl.evaluate(
        InternalState(gcpl_convergence=0.85, bc_safety_score=0.90,
                      adlr_liveness=0.80, bcil_veto_active=False),
        ObservedState(lag_ms=3000.0, is_stale=True,
                      branch_observations={0: {}, 1: {}}),
    )
    ok &= check("T2 DEGRADED region", r2.region == "DEGRADED", f"score={r2.score:.3f}")
    ok &= check("T2 drift detected", r2.drift > 0.25, f"drift={r2.drift:.3f}")
    ok &= check("T2 actions generated", r2.actions != ["none"])

    # T3: high drift → rollback
    r3 = gsl.evaluate(
        InternalState(gcpl_convergence=0.80, bc_safety_score=0.85,
                      adlr_liveness=0.75, bcil_veto_active=False,
                      bc_oscillation_detected=True),
        ObservedState(lag_ms=4000.0, is_stale=True,
                      branch_observations={0: {}}),
    )
    ok &= check("T3 rollback triggered", "request_reconciliation" in r3.actions,
                f"actions={r3.actions}")
    ok &= check("T3 EPOCH_RESET", "EPOCH_RESET" in r3.actions)

    # T4: branch-observation split → F4 + branch_separation
    r4 = gsl.evaluate(
        InternalState(gcpl_convergence=0.78, bc_safety_score=0.88,
                      adlr_liveness=0.72, bcil_veto_active=False,
                      bc_branch_count=5),
        ObservedState(lag_ms=100.0, branch_observations={0: {}, 1: {}}),
    )
    ok &= check("T4 F4 branch split detected", r4.f4_branch_split)
    ok &= check("T4 branch_separation action", "branch_separation" in r4.actions)

    # T5: BCIL veto blocks reconciliation
    r5 = gsl.evaluate(
        InternalState(gcpl_convergence=0.95, bc_safety_score=0.99,
                      adlr_liveness=0.90, bcil_veto_active=True),
        ObservedState(lag_ms=0.0, observed_node_ids={"a", "b"}),
    )
    ok &= check("T5 veto active", r5.vetoed)
    ok &= check("T5 no reconciliation on veto",
                "request_reconciliation" not in r5.actions)

    # T6: lagging observer → F3, refresh action, not FAILURE
    gsl6 = GSL()
    r6 = gsl6.evaluate(
        InternalState(gcpl_convergence=0.88, bc_safety_score=0.92,
                      adlr_liveness=0.85, bcil_veto_active=False),
        ObservedState(lag_ms=2500.0, is_stale=True,
                      observed_node_ids={"a", "b"}),
    )
    ok &= check("T6 F3 lag trap detected", r6.f3_lag_trap)
    ok &= check("T6 refresh_observation action", "refresh_observation" in r6.actions)
    ok &= check("T6 not FAILURE region", r6.region != "FAILURE")

    log.info("")
    log.info(f"{'='*50}")
    log.info(f"RESULT: {'ALL PASSED ✅' if ok else 'SOME TESTS FAILED ❌'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if _run_tests() else 1)

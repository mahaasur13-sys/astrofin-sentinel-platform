"""v6.8 — Meta-Coherence Controller."""

from __future__ import annotations

import time
from dataclasses import dataclass

# v6.8 coherence layer
from coherence.drift_controller import DriftController
from coherence.invariant import CoherenceViolation, SystemCoherenceInvariant
from coherence.objective_stabilizer import GlobalObjectiveStabilizer, StabilizerSnapshot
from coherence.temporal_smoother import SmootherSnapshot, TemporalCoherenceSmoother
from resilience.closed_loop import ClosedLoopResilienceController
from resilience.compute_budget_controller import (
    BudgetDecision,
    ComputeBudgetController,
    Subsystem,
)
from resilience.decision_lattice import DecisionLattice, LatticeDecision
from resilience.eigenstate_detector import EigenstateDetector, EigenstateSnapshot
from resilience.model_reality_aligner import AlignmentSnapshot, ModelRealityAligner
from resilience.objective_stability_governor import (
    GovernorDecision,
    GovernorMode,
    ObjectiveStabilityGovernor,
)
from resilience.optimizer import OptimizationResult, SystemOptimizer
from resilience.predictive_controller import PredictiveController
from resilience.self_model import NodeRole, SystemState

try:
    from resilience.compute_budget_controller import ComputeBudgetSnapshot
except ImportError:
    ComputeBudgetSnapshot = object


@dataclass
class CoherenceMetrics:
    coherence_score: float
    model_version: int
    current_eigenstate_id: str | None
    eigenstate_type: str | None
    J_raw: float
    J_governed: float
    J_allowed: bool
    oscillation_detected: bool
    compute_used_ms: float
    drift_status: str
    eigenstate_transition_pending: bool
    total_coherence_loops: int
    drift_score: float = 0.0
    lattice_oscillation_strength: float = 0.0
    trajectory_ok: bool = True
    sci_violated: bool = False


@dataclass
class MetaCoherenceSnapshot:
    timestamp: float
    tick_number: int
    metrics: CoherenceMetrics
    alignment: AlignmentSnapshot
    eigenstate: EigenstateSnapshot
    governor_decision: GovernorDecision
    compute: ComputeBudgetSnapshot
    raw_decision: LatticeDecision | None
    final_action: str | None
    drift_snap: object | None = None
    smoother_snap: SmootherSnapshot | None = None
    stabilizer_snap: StabilizerSnapshot | None = None


class MetaCoherenceController:
    """Master v6.8 controller — adds GLOBAL COHERENCE ENGINE.

    Tick flow:
      1. begin_tick()
      2. ModelRealityAligner.observe()
      3. DriftController.observe()           # v6.8
      4. TemporalCoherenceSmoother.ingest() # v6.8
      5. EigenstateDetector.detect_current()
      6. PredictiveController.tick()
      7. SystemOptimizer.compute_J() + Governor
      8. DecisionLattice.decide()
      9. TemporalCoherenceSmoother.smooth() # v6.8
     10. GlobalObjectiveStabilizer.compute_J() # v6.8
     11. SystemCoherenceInvariant.check()    # v6.8 HARD GATE
     12. end_tick()
    """

    def __init__(
        self,
        cluster_nodes: int = 5,
        tick_budget_ms: float = 50.0,
        governor_mode: GovernorMode = GovernorMode.DAMPED,
        sci_fail_fast: bool = True,
        drift_threshold: float = 0.15,
        stabilizer_alpha: float = 0.50,
        stabilizer_beta: float = 0.30,
        stabilizer_gamma: float = 0.20,
    ):
        self.aligner = ModelRealityAligner()
        self.eigenstate_detector = EigenstateDetector(n_features=8, learning_window=200)
        self.governor = ObjectiveStabilityGovernor(mode=governor_mode)
        self.compute = ComputeBudgetController(total_budget_ms=tick_budget_ms)

        self._ctrl = ClosedLoopResilienceController(
            node_id="meta-coherence-ctrl",
            peers=[f"node-{i}" for i in range(cluster_nodes)],
        )
        self.predictive = PredictiveController(self._ctrl, forecast_horizon_s=30.0)
        self.optimizer = SystemOptimizer()
        self.lattice = DecisionLattice()

        # v6.8 GLOBAL COHERENCE ENGINE
        self.drift_ctrl = DriftController(drift_threshold=drift_threshold)
        self.smoother = TemporalCoherenceSmoother(base_window=5, max_window=30)
        self.stabilizer = GlobalObjectiveStabilizer(
            alpha=stabilizer_alpha,
            beta=stabilizer_beta,
            gamma=stabilizer_gamma,
            trajectory_tolerance=0.05,
            trajectory_window=10,
            optimizer=self.optimizer,
        )
        self.sci = SystemCoherenceInvariant(fail_fast=sci_fail_fast)
        self.sci.begin_window()

        self._tick_count = 0
        self._last_snapshot: MetaCoherenceSnapshot | None = None
        self._previous_J = 0.5
        self._drl_drop_rate = 0.0
        self._latency_history_ms = [10.0]
        self._violation_count = 0

    def begin_tick(self) -> None:
        self.compute.begin_tick()
        self._tick_count += 1

    def tick(
        self,
        observed_state: dict,
        predicted_state: dict,
        node_roles: dict[str, NodeRole],
        drl_drop_rate: float = 0.0,
        latency_ms: float = 10.0,
        violation_count: int = 0,
    ) -> MetaCoherenceSnapshot:
        now = time.time()

        # 1. Alignment
        self.compute.enter_subsystem(Subsystem.MODEL_ALIGNER)
        t0 = time.monotonic()
        alignment = self.aligner.observe(observed_state, predicted_state)
        elapsed = (time.monotonic() - t0) * 1000.0
        self.compute.exit_subsystem(Subsystem.MODEL_ALIGNER, elapsed)

        # 2. v6.8: DriftController
        drift_snap = self.drift_ctrl.observe(observed_state, predicted_state)

        # Update DRL metrics for smoother
        self._drl_drop_rate = drl_drop_rate
        self._latency_history_ms.append(latency_ms)
        if len(self._latency_history_ms) > 20:
            self._latency_history_ms = self._latency_history_ms[-20:]
        self._violation_count = violation_count

        # 3. v6.8: TemporalCoherenceSmoother ingest
        self.smoother.ingest(
            drl_drop_rate=self._drl_drop_rate,
            latency_ms=latency_ms,
            latency_history_ms=self._latency_history_ms,
            violation_count=self._violation_count,
        )

        # 4. Eigenstate detection
        self.eigenstate_detector.ingest(observed_state)
        self.compute.enter_subsystem(Subsystem.EIGENSTATE_DETECTOR)
        t0 = time.monotonic()
        eigenstate_snap = self.eigenstate_detector.detect_current()
        elapsed = (time.monotonic() - t0) * 1000.0
        self.compute.exit_subsystem(Subsystem.EIGENSTATE_DETECTOR, elapsed)

        # 5. Predictive forecast
        self.compute.enter_subsystem(Subsystem.PREDICTIVE_CONTROLLER)
        adaptive_horizon = self.compute.get_adaptive_horizon(30.0, Subsystem.PREDICTIVE_CONTROLLER)
        self.predictive.forecast_horizon = adaptive_horizon
        t0 = time.monotonic()
        SystemState(
            node_count_total=len(node_roles),
            node_count_healthy=sum(1 for r in node_roles.values() if r == NodeRole.HEALTHY),
            stability_score=1.0 - alignment.drift_score,
            quorum_health=1.0 - alignment.drift_score,
            leader_count=1,
            node_roles=node_roles,
        )
        self.predictive.tick()
        elapsed = (time.monotonic() - t0) * 1000.0
        self.compute.exit_subsystem(Subsystem.PREDICTIVE_CONTROLLER, elapsed)

        # 6. J computation
        self.compute.enter_subsystem(Subsystem.GOVERNORS)
        t0 = time.monotonic()
        try:
            snap = self._ctrl.get_snapshot()
            J_result: OptimizationResult = self.optimizer.compute_J(snap)
            J_raw = J_result.J
        except Exception:
            J_raw = self._previous_J
        governor_decision = self.governor.evaluate(J_raw, confidence=0.8)
        elapsed = (time.monotonic() - t0) * 1000.0
        self.compute.exit_subsystem(Subsystem.GOVERNORS, elapsed)
        self._previous_J = J_raw

        # 7. Decision lattice
        self.compute.enter_subsystem(Subsystem.DECISION_LATTICE)
        t0 = time.monotonic()
        full_state = SystemState(
            node_count_total=len(node_roles),
            node_count_healthy=sum(1 for r in node_roles.values() if r == NodeRole.HEALTHY),
            stability_score=1.0 - alignment.drift_score,
            quorum_health=1.0 - alignment.drift_score,
            leader_count=1,
            node_roles=node_roles,
        )
        raw_decision = self.lattice.decide(full_state)
        elapsed = (time.monotonic() - t0) * 1000.0
        prune_happened = self.compute.should_prune(Subsystem.DECISION_LATTICE, raw_decision.branch_count)
        self.compute.exit_subsystem(Subsystem.DECISION_LATTICE, elapsed,
                                   nodes_visited=raw_decision.branch_count, pruned=prune_happened)

        # 8. v6.8: TemporalCoherenceSmoother — EMA smoothing
        smoother_snap = self.smoother.smooth(raw_decision.primary_action.name)
        final_action_name = (
            smoother_snap.smoothed_action
            if smoother_snap.oscillation_strength > 0.3
            else raw_decision.primary_action.name
        )

        # 9. v6.8: GlobalObjectiveStabilizer — J_new formula
        stability_score = 1.0 - drift_snap.drift_score
        consistency_score = smoother_snap.lattice_stability_score
        control_cost = self.compute.snapshot().utilization_pct / 100.0
        stabilizer_snap = self.stabilizer.compute_J(
            stability_score=stability_score,
            consistency_score=consistency_score,
            control_cost=control_cost,
            J_compat=J_raw,
        )

        # 10. v6.8: SystemCoherenceInvariant — HARD GATE
        sci_violated = False
        osc_amp = (governor_decision.oscillation_report.amplitude
                   if governor_decision.oscillation_report else 0.0)
        try:
            self.sci.check(
                drift_score=drift_snap.drift_score,
                lattice_divergence=smoother_snap.oscillation_strength,
                oscillation_strength=smoother_snap.oscillation_strength,
                coherence_score=self._compute_coherence(
                    alignment.drift_score,
                    eigenstate_snap.trajectory_variance,
                    osc_amp,
                ),
                model_version=self.drift_ctrl._model_version,
            )
        except CoherenceViolation:
            sci_violated = True
            final_action_name = "BLOCKED"

        # 11. Final action gating
        final_allowed = governor_decision.allowed and J_raw > 0.0 and not sci_violated
        final_action = final_action_name if final_allowed else "BLOCKED"

        # 12. Coherence score
        osc_detected = (governor_decision.oscillation_report.detected
                        if governor_decision.oscillation_report else False)
        eigenstate_id = (eigenstate_snap.current_eigenstate.id
                         if eigenstate_snap.current_eigenstate else None)
        eigenstate_type_val = (eigenstate_snap.current_eigenstate.type.value
                               if eigenstate_snap.current_eigenstate else None)

        metrics = CoherenceMetrics(
            coherence_score=self._compute_coherence(
                alignment.drift_score,
                eigenstate_snap.trajectory_variance,
                osc_amp,
            ),
            model_version=self.aligner._model_version,
            current_eigenstate_id=eigenstate_id,
            eigenstate_type=eigenstate_type_val,
            J_raw=J_raw,
            J_governed=governor_decision.enforced_J,
            J_allowed=governor_decision.allowed,
            oscillation_detected=osc_detected,
            compute_used_ms=self.compute.snapshot().spent_ms,
            drift_status=alignment.drift_status.value,
            eigenstate_transition_pending=eigenstate_snap.transition_pending is not None,
            total_coherence_loops=self._tick_count,
            drift_score=drift_snap.drift_score,
            lattice_oscillation_strength=smoother_snap.oscillation_strength,
            trajectory_ok=stabilizer_snap.trajectory_ok,
            sci_violated=sci_violated,
        )

        snap = MetaCoherenceSnapshot(
            timestamp=now,
            tick_number=self._tick_count,
            metrics=metrics,
            alignment=alignment,
            eigenstate=eigenstate_snap,
            governor_decision=governor_decision,
            compute=self.compute.snapshot(),
            raw_decision=raw_decision,
            final_action=final_action,
            drift_snap=drift_snap,
            smoother_snap=smoother_snap,
            stabilizer_snap=stabilizer_snap,
        )
        self._last_snapshot = snap
        return snap

    def _compute_coherence(
        self,
        drift_score: float,
        trajectory_variance: float,
        oscillation_amplitude: float,
    ) -> float:
        d = 1.0 - min(drift_score / 0.4, 1.0)
        v = 1.0 - min(trajectory_variance / 0.5, 1.0)
        o = 1.0 - min(oscillation_amplitude / 0.3, 1.0)
        return d * 0.4 + v * 0.3 + o * 0.3

    def end_tick(self) -> BudgetDecision:
        return self.compute.snapshot()

    def force_model_rebuild(self, reason: str = "manual") -> AlignmentSnapshot:
        return self.aligner.force_correction(reason)

    def force_drift_correction(self, reason: str = "manual"):
        """Force a drift correction (v6.8)."""
        return self.drift_ctrl.force_correction(reason)

    def set_governor_mode(self, mode: GovernorMode) -> None:
        self.governor.set_mode(mode)

    def reset_sci_window(self) -> None:
        """Start a new S-CI convergence window."""
        self.sci.begin_window()

    def summary(self) -> dict:
        snap = self._last_snapshot
        return {
            "tick": self._tick_count,
            "coherence_score": snap.metrics.coherence_score if snap else 0.0,
            "drift_status": snap.metrics.drift_status if snap else "none",
            "governor_mode": self.governor.mode.value,
            "compute_utilization_pct": snap.compute.utilization_pct if snap else 0.0,
            "model_version": self.aligner._model_version,
            "eigenstate_count": self.eigenstate_detector.summary()["eigenstate_count"],
            "last_action": snap.final_action if snap else "none",
            "sci_violated": snap.metrics.sci_violated if snap else False,
            "drift_score": snap.metrics.drift_score if snap else None,
            "trajectory_ok": snap.metrics.trajectory_ok if snap else None,
            "lattice_oscillation": snap.metrics.lattice_oscillation_strength if snap else None,
        }

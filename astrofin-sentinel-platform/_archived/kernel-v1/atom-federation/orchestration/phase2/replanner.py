"""
replanner.py — v8.0 Phase 2
Triggers replanning based on persistence_drift and proof drift thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass

from meta_control.integration.persistence_bridge import IntegrationReport
from orchestration.phase2.goal_memory import GoalMemory
from orchestration.phase2.plan_evaluator import PlanEvaluation, PlanEvaluator


@dataclass
class ReplanTrigger:
    reason: str
    tick: int
    drift_magnitude: float
    evaluation_before: PlanEvaluation | None = None
    evaluation_after: PlanEvaluation | None = None


@dataclass
class ReplanConfig:
    persistence_drift_threshold: float = 0.15
    coherence_drop_threshold: float = 0.10
    proof_reliability_threshold: float = 0.60
    stability_threshold: float = 0.50
    window_depth_min: int = 3


class Replanner:
    """
    Decides when to replan based on:
      - persistence_drift: how much stability ledger drifted from plan-time
      - coherence_drop: enriched_coherence fell below plan-time level
      - proof_reliability: DecisionMemory proof prediction accuracy
      - stability_score: PlanEvaluator stability dimension

    Uses GoalMemory to record replan triggers for later analysis.
    """

    def __init__(
        self,
        goal_memory: GoalMemory,
        evaluator: PlanEvaluator,
        config: ReplanConfig | None = None,
    ) -> None:
        self.memory = goal_memory
        self.evaluator = evaluator
        self.config = config or ReplanConfig()

    def should_replan(
        self,
        current_report: IntegrationReport,
        plan_time_coherence: float,
        plan_time_evaluation: PlanEvaluation | None,
        source_statuses: dict[str, dict],
        proof_reliability: float,
    ) -> tuple[bool, ReplanTrigger]:
        """
        Returns (should_replan, trigger).
        trigger.reason describes why replan was or wasn't triggered.
        """
        cfg = self.config
        tick = current_report.tick

        drift_magnitude = 0.0
        reasons: list[str] = []

        # 1. Persistence drift (negative trend)
        trend = current_report.coherence.trend
        depth = current_report.coherence.window_depth
        if trend < -0.3:
            drift_magnitude += abs(trend)
            reasons.append(f"negative_trend({trend:.2f})")

        # 2. Window depth too shallow
        if depth < cfg.window_depth_min:
            drift_magnitude += 0.1
            reasons.append(f"shallow_window({depth})")

        # 3. Coherence drop
        enriched_now = current_report.coherence.enriched_coherence
        coherence_drop = plan_time_coherence - enriched_now
        if coherence_drop > cfg.coherence_drop_threshold:
            drift_magnitude += coherence_drop
            reasons.append(f"coherence_drop({coherence_drop:.3f})")

        # 4. Proof reliability degradation
        if proof_reliability < cfg.proof_reliability_threshold:
            drift_magnitude += cfg.proof_reliability_threshold - proof_reliability
            reasons.append(f"proof_reliability({proof_reliability:.2f})")

        # 5. Stability score drop
        eval_now = self.evaluator.evaluate(
            plan_id="replan_check",
            report=current_report,
            source_statuses=source_statuses,
        )
        if (plan_time_evaluation is not None
                and eval_now.stability_score < cfg.stability_threshold):
            drift_magnitude += cfg.stability_threshold - eval_now.stability_score
            reasons.append(f"stability_score_drop({eval_now.stability_score:.3f})")

        # Decision
        should_replan = drift_magnitude > cfg.persistence_drift_threshold
        reason = "; ".join(reasons) if reasons else "no_trigger"

        trigger = ReplanTrigger(
            reason=reason if should_replan else "no_trigger",
            tick=tick,
            drift_magnitude=drift_magnitude,
            evaluation_before=plan_time_evaluation,
            evaluation_after=eval_now,
        )
        return should_replan, trigger

    def record_replan(
        self,
        goal_id: int,
        trigger: ReplanTrigger,
        new_plan_id: str,
    ) -> None:
        self.memory.mark_replan(goal_id)
        self.memory.record_drift(goal_id, trigger.drift_magnitude)

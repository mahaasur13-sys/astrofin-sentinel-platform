"""MutationExecutor — applies θ transformation under the v8.2a safety substrate."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

import numpy as np

from .policy_selector import MutationPolicy, PolicySelector
from .severity_mapper import MutationClass, SeverityActionMapper


class ExecutionStatus(Enum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable record of a mutation execution attempt."""

    execution_id: str
    mutation_class: MutationClass
    status: ExecutionStatus
    theta_before: tuple[float, ...]
    theta_after: tuple[float, ...]
    delta_norm_l2: float
    policy_violated: bool
    error_message: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status in (ExecutionStatus.SUCCESS, ExecutionStatus.DEGRADED)

    @property
    def rolled_back(self) -> bool:
        return self.status == ExecutionStatus.ROLLED_BACK


class HealthAwareUpdateFn(Protocol):
    """Contract for the adaptive update function supplied by the controller."""

    def update_theta(
        self, theta: np.ndarray, delta: np.ndarray, health: float
    ) -> np.ndarray: ...


@dataclass
class ExecutorConfig:
    """Runtime configuration for MutationExecutor."""

    # v8.2a integration
    use_safety_gate: bool = True
    use_invariants: bool = True
    allow_degradation: bool = False

    # Override policy constraints (None = use policy defaults)
    override_retune_epsilon: float | None = None
    override_reweight_clip: float | None = None
    override_replan_horizon: float | None = None
    override_reset_blend: float | None = None

    # Callbacks
    on_success: Callable[[ExecutionResult], None] | None = None
    on_rollback: Callable[[ExecutionResult], None] | None = None


class MutationExecutor:
    """
    Applies parameter-space transformations (RETUNE / REWEIGHT / REPLAN / RESET)
    under the v8.2a safety substrate.

    Design goals:
      - Every mutation is logged to MutationLedger (audit trail)
      - Invariants are checked post-delta; violations trigger rollback
      - Health-aware update function allows controller to scale deltas by health
      - Callbacks allow external consumers (dashboard, alerts, etc.)
    """

    def __init__(
        self,
        theta: np.ndarray,
        severity_mapper: SeverityActionMapper,
        policy_selector: PolicySelector,
        safety_gate,           # StabilityGovernor from v8.2a
        invariant_checker,      # InvariantChecker from v8.2a
        mutation_ledger,       # MutationLedger from v8.2a
        rollback_engine,       # RollbackEngine from v8.2a
        config: ExecutorConfig | None = None,
        update_fn: HealthAwareUpdateFn | None = None,
    ):
        self._theta = theta.copy()
        self._severity_mapper = severity_mapper
        self._policy_selector = policy_selector
        self._safety_gate = safety_gate
        self._invariant_checker = invariant_checker
        self._ledger = mutation_ledger
        self._rollback = rollback_engine
        self._config = config or ExecutorConfig()
        self._update_fn = update_fn or self._default_update_fn
        self._exec_counter = 0
        self._tick: int = 0  # deterministic tick counter

    # ── Public API ─────────────────────────────────────────────────────────

    def apply_mutation(
        self,
        drift_score: float,
        health_score: float,
        mutation_density: float,
        coherence_drop: float,
        oscillation_detected: bool,
        recent_outcome: str | None = None,
        pre_check_passed: bool = False,
        tick: int = 0,
    ) -> ExecutionResult:
        """
        Gateway-facing mutation API — called by ExecutionGateway ACT stage.

        Replaces the old execute() entry point which is now deleted.
        All safety checks (G1–G6, G8–G10) are handled by the Gateway;
        this method performs ONLY the parameter-space delta application.

        Raises:
            SystemIntegrityViolation: if called outside ExecutionGateway
        """
        # ── P4: Runtime Self-Verification ────────────────────────────────────
        # This is UNDISABLEABLE. Even if Gateway entry is bypassed somehow,
        # MutationExecutor refuses to act outside ExecutionGateway context.
        from core.runtime.runtime_guard import RuntimeExecutionGuard
        RuntimeExecutionGuard.assert_in_gateway_context()

        self._tick = tick
        return self._execute_internal(
            drift_score=drift_score,
            health_score=health_score,
            mutation_density=mutation_density,
            coherence_drop=coherence_drop,
            oscillation_detected=oscillation_detected,
            recent_outcome=recent_outcome,
            pre_check_passed=pre_check_passed,
        )

    def current_theta(self) -> np.ndarray:
        return self._theta.copy()

    # ── Stage functions (called ONLY from ExecutionGateway ACT stage) ───────

    # ── Delta generation ───────────────────────────────────────────────────

    def _generate_delta(
        self, mutation_class: MutationClass, policy: MutationPolicy, theta: np.ndarray
    ) -> np.ndarray:
        rng = np.random.default_rng(seed=self._tick)

        if mutation_class == MutationClass.RETUNE:
            max_eps = (
                self._config.override_retune_epsilon
                or policy.max_retune_epsilon
            )
            # Random direction, ε-magnitude
            direction = rng.choice([-1, 1], size=theta.shape)
            magnitude = rng.uniform(0.1, 1.0) * max_eps
            return direction * magnitude * np.abs(theta.clip(min=1e-8))

        elif mutation_class == MutationClass.REWEIGHT:
            clip = self._config.override_reweight_clip or policy.reweight_clip_ratio
            return rng.uniform(-clip, clip, size=theta.shape)

        elif mutation_class == MutationClass.REPLAN:
            horizon_frac = policy.replan_horizon_fraction
            horizon_n = max(1, int(len(theta) * horizon_frac))
            delta = np.zeros_like(theta)
            delta[:horizon_n] = rng.uniform(-0.5, 0.5, size=horizon_n)
            return delta

        else:  # RESET
            blend = policy.reset_ref_weight
            ref = rng.standard_normal(size=theta.shape) * 0.5
            return blend * ref - (1 - blend) * theta

    @staticmethod
    def _default_update_fn(
        theta: np.ndarray, delta: np.ndarray, health: float
    ) -> np.ndarray:
        scale = max(health, 0.1)
        return theta + scale * delta

    # ── Result factories ────────────────────────────────────────────────────

    def _blocked_result(
        self, mutation_class: MutationClass, ctx, policy
    ) -> ExecutionResult:
        self._exec_counter += 1
        return ExecutionResult(
            execution_id=f"exec_{self._exec_counter:04d}_{mutation_class.value}",
            mutation_class=mutation_class,
            status=ExecutionStatus.BLOCKED,
            theta_before=tuple(self._theta),
            theta_after=tuple(self._theta),
            delta_norm_l2=0.0,
            policy_violated=False,
            error_message="Safety gate blocked mutation",
        )

    def _failed_result(
        self, mutation_class: MutationClass, policy, theta_before, exc: Exception
    ) -> ExecutionResult:
        self._exec_counter += 1
        return ExecutionResult(
            execution_id=f"exec_{self._exec_counter:04d}_{mutation_class.value}",
            mutation_class=mutation_class,
            status=ExecutionStatus.FAILED,
            theta_before=tuple(theta_before),
            theta_after=tuple(self._theta),
            delta_norm_l2=0.0,
            policy_violated=False,
            error_message=str(exc),
        )

    def _rollback_result(
        self,
        mutation_class: MutationClass,
        policy: MutationPolicy,
        theta_before: np.ndarray,
        theta_after: np.ndarray,
        delta_norm: float,
    ) -> ExecutionResult:
        self._exec_counter += 1
        return ExecutionResult(
            execution_id=f"exec_{self._exec_counter:04d}_{mutation_class.value}_rb",
            mutation_class=mutation_class,
            status=ExecutionStatus.ROLLED_BACK,
            theta_before=tuple(theta_before),
            theta_after=tuple(theta_after),
            delta_norm_l2=delta_norm,
            policy_violated=policy.rollback_on_violation,
            error_message="Invariant violation — rolled back",
        )

    def _fire_callback(self, result: ExecutionResult):
        if result.status == ExecutionStatus.SUCCESS and self._config.on_success:
            self._config.on_success(result)
        if result.status == ExecutionStatus.ROLLED_BACK and self._config.on_rollback:
            self._config.on_rollback(result)

    # ── Internal implementation (called by Gateway ACT stage) ─────────────

    def _execute_internal(
        self,
        drift_score: float,
        health_score: float,
        mutation_density: float,
        coherence_drop: float,
        oscillation_detected: bool,
        recent_outcome: str | None = None,
        pre_check_passed: bool = False,
    ) -> ExecutionResult:
        """
        End-to-end mutation execution pipeline.

        Steps:
          1. Build PolicyContext (classify + select policy)
          2. Safety gate (v8.2a) — BLOCK if unhealthy
          3. Generate delta (per mutation class)
          4. Apply health-aware update
          5. Invariant check post-apply
          6. Commit or rollback
          7. Log to ledger
          8. Return ExecutionResult
        """
        severity, mutation_class = self._severity_mapper.resolve(drift_score)

        from .policy_selector import PolicyContext  # delayed to avoid circular
        ctx = PolicyContext(
            drift_score=drift_score,
            health_score=health_score,
            mutation_density=mutation_density,
            coherence_drop=coherence_drop,
            oscillation_detected=oscillation_detected,
            severity=severity,
            mutation_class=mutation_class,
            recent_outcome=recent_outcome,
        )

        policy = self._policy_selector.select(ctx)

        # Step 2: Safety gate (v8.2a)
        if self._config.use_safety_gate and not pre_check_passed:
            from orchestration.v8_2a_safety_foundations import (
                GovernorDecision,
                GovernorSignal,
            )
            sig = GovernorSignal(
                health_score=health_score,
                plan_stability_index=1.0 - drift_score,
                coherence_drop_rate=coherence_drop,
                drift_severity=drift_score,
                oscillation_detected=oscillation_detected,
                recent_mutation_density=mutation_density,
            )
            if self._safety_gate.evaluate(sig) in (
                GovernorDecision.BLOCK,
                GovernorDecision.ESCALATE,
            ):
                return self._blocked_result(mutation_class, ctx, policy)

        # Step 3: Generate delta
        delta = self._generate_delta(mutation_class, policy, self._theta)

        # Step 4: Apply update
        theta_before = self._theta.copy()
        try:
            self._theta = self._update_fn(self._theta, delta, health_score)
        except Exception as exc:
            return self._failed_result(mutation_class, policy, theta_before, exc)

        delta_norm = float(np.linalg.norm(delta))

        # Step 5: Invariant check
        if self._config.use_invariants:
            try:
                self._invariant_checker.validate(theta_before, self._theta)
            except Exception:
                # Rollback
                theta_after = self._theta.copy()
                self._theta = theta_before
                result = self._rollback_result(
                    mutation_class, policy, theta_before, theta_after, delta_norm
                )
                self._fire_callback(result)
                return result

        # Step 6: Commit to ledger
        self._exec_counter += 1
        self._ledger.record(
            theta_old=theta_before,
            theta_new=self._theta,
            trigger_source="drift_autocorrect",
            trigger_metadata={
                "drift_score": drift_score,
                "mutation_class": mutation_class.value,
                "policy_mode": policy.mode.value,
            },
            governor_decision="ALLOW",
            invariants_passed=["param_drift"],
        )

        status = ExecutionStatus.SUCCESS
        if self._config.allow_degradation and not ctx.is_safe_to_mutate:
            status = ExecutionStatus.DEGRADED

        result = ExecutionResult(
            execution_id=f"exec_{self._exec_counter:04d}_{mutation_class.value}",
            mutation_class=mutation_class,
            status=status,
            theta_before=tuple(theta_before),
            theta_after=tuple(self._theta),
            delta_norm_l2=delta_norm,
            policy_violated=False,
        )

        self._fire_callback(result)
        return result

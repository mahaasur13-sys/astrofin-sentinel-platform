# ATOMFEDERATION-OS - AtomOperator Reconciler
# DI + ExecutionGateway — hard safety boundary
# =========================================================

import threading
from dataclasses import dataclass, field

from orchestration.execution_gateway import ExecutionGateway


@dataclass
class ClusterState:
    nodes: list[str] = field(default_factory=list)
    healthy: list[str] = field(default_factory=list)
    unhealthy: list[str] = field(default_factory=list)
    pending_recovery: list[str] = field(default_factory=list)


@dataclass
class ReconciliationResult:
    success: bool
    healed_nodes: list[str] = field(default_factory=list)
    throttled_nodes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class DriftProfiler:
    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway

    def scan(self, cluster: ClusterState) -> dict:
        with self._gateway.mutation_context(can_mutate=False):
            return {
                'unhealthy': cluster.unhealthy,
                'divergence_score': len(cluster.unhealthy) / max(len(cluster.nodes), 1)
            }


class CircuitBreaker:
    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway
        self._open = False

    def allow(self, node: str) -> bool:
        with self._gateway.mutation_context(can_mutate=False):
            return not self._open

    def trip(self) -> None:
        with self._gateway.mutation_context(can_mutate=True):
            self._open = True


class InvariantChecker:
    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway
        self._invariants = []

    def check(self, cluster: ClusterState) -> list[str]:
        with self._gateway.mutation_context(can_mutate=False):
            violations = []
            for inv in self._invariants:
                if not inv(cluster):
                    violations.append(inv.__name__)
            return violations


class StabilityGovernor:
    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway
        self._stability_threshold = 0.8

    def evaluate(self, cluster: ClusterState) -> dict:
        with self._gateway.mutation_context(can_mutate=False):
            healthy_ratio = len(cluster.healthy) / max(len(cluster.nodes), 1)
            return {
                'stable': healthy_ratio >= self._stability_threshold,
                'score': healthy_ratio
            }

    def signal(self, action: str) -> None:
        with self._gateway.mutation_context(can_mutate=True):
            pass


class AtomOperatorReconciler:
    # =========================================================
    # ATOM OPERATOR RECONCILER — DI + GATEWAY ENFORCEMENT
    # All mutations MUST go through gateway.mutation_context()
    # =========================================================

    def __init__(
        self,
        gateway: ExecutionGateway,
        drift_profiler: DriftProfiler | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        invariant_checker: InvariantChecker | None = None,
        stability_governor: StabilityGovernor | None = None
    ):
        self._gateway = gateway
        self._drift_profiler = drift_profiler or DriftProfiler(gateway)
        self._circuit_breaker = circuit_breaker or CircuitBreaker(gateway)
        self._invariant_checker = invariant_checker or InvariantChecker(gateway)
        self._stability_governor = stability_governor or StabilityGovernor(gateway)
        self._lock = threading.RLock()

    @ExecutionGateway.requires_gateway
    def reconcile(self, cluster: ClusterState) -> ReconciliationResult:
        with self._lock:
            result = ReconciliationResult(success=True)

            # Pre-flight: invariant check (read-only)
            violations = self._invariant_checker.check(cluster)
            if violations:
                result.success = False
                result.errors.extend(violations)
                return result

            # Step 1: Scan for drift
            drift_report = self._drift_profiler.scan(cluster)

            # Step 2: Decision via StabilityGovernor
            stability = self._stability_governor.evaluate(cluster)
            if not stability['stable']:
                self._stability_governor.signal('throttle')

            # Step 3: Heal unhealthy nodes (ONLY inside mutation_context)
            for node in cluster.unhealthy:
                if self._circuit_breaker.allow(node):
                    healed = self._heal_node(node)
                    if healed:
                        result.healed_nodes.append(node)

            # Step 4: Throttle problematic nodes
            for node in cluster.pending_recovery:
                throttled = self._throttle_node(node)
                if throttled:
                    result.throttled_nodes.append(node)

            return result

    def _heal_node(self, node: str) -> bool:
        # Real implementation: kubectl exec, restart pod, etc.
        return True

    def _throttle_node(self, node: str) -> bool:
        # Real implementation: reduce quota, block traffic, etc.
        return True

    def get_status(self) -> dict:
        with self._gateway.mutation_context(can_mutate=False):
            return {
                'gateway_safe': self._gateway.is_safe(),
                'circuit_breaker_open': self._circuit_breaker._open,
            }

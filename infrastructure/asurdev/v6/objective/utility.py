#!/usr/bin/env python3
"""
Global Objective Function — cluster-wide utility maximization.
U = alpha * throughput + beta * reliability + gamma * migration_cost
    + delta * SLA_violation + epsilon * load_variance
"""
from dataclasses import dataclass, field


@dataclass
class UtilityWeights:
    alpha_throughput: float = 1.0  # Jobs completed per time window
    beta_reliability: float = 2.0  # Failure penalty weight
    gamma_migration: float = 0.3  # Migration cost weight
    delta_sla: float = 5.0  # SLA violation penalty
    epsilon_variance: float = 0.5  # Load variance (stability)
    epsilon_exploration: float = 0.1  # Exploration bonus


@dataclass
class ClusterSnapshot:
    node_states: dict  # node_id -> {cpu, gpu, memory, jobs}
    job_queue: list  # pending jobs
    active_jobs: dict  # job_id -> {node, start_time, cost}
    completed_window: int = 0  # jobs completed in window
    failed_window: int = 0  # failures in window
    sla_violations: int = 0
    migrations: int = 0

    # Aggregated metrics
    cpu_variance: float = 0.0
    gpu_variance: float = 0.0
    memory_variance: float = 0.0
    predicted_failures: dict = field(default_factory=dict)  # node_id -> P(failure)


@dataclass
class ScheduleAction:
    action_id: str
    action_type: str  # "place", "migrate", "evict", "defer"
    job_id: str | None
    node_id: str | None
    expected_utility_delta: float


class UtilityFunction:
    """
    Global utility U(S, T) for cluster state S over horizon T.
    Components:
      U = alpha * throughput
        + beta * (1 - E[P(failure)])
        - gamma * migration_cost
        - delta * SLA_violations
        - epsilon * load_variance
        + exploration_bonus
    """

    def __init__(self, weights: UtilityWeights | None = None):
        self.w = weights or UtilityWeights()

    def throughput_component(self, snapshot: ClusterSnapshot) -> float:
        """Jobs completed per time window (higher = better)."""
        return snapshot.completed_window

    def reliability_component(self, snapshot: ClusterSnapshot) -> float:
        """
        Expected reliability = 1 - sum(P(failure) * job_cost) for all nodes.
        Penalty increases with predicted failure probability and job cost.
        """
        total_risk = 0.0
        for node_id, p_failure in snapshot.predicted_failures.items():
            node_jobs = [j for j in snapshot.active_jobs.values() if j.get("node") == node_id]
            job_costs = sum(j.get("cost", 1.0) for j in node_jobs)
            total_risk += p_failure * job_costs
        return 1.0 - total_risk

    def migration_cost_component(self, snapshot: ClusterSnapshot) -> float:
        """
        Migration cost = number_of_migrations * (cpu_switch + memory_realloc + network_transfer).
        We MINIMIZE this, so we return the raw cost (optimizer subtracts).
        """
        migrations = snapshot.migrations
        cpu_switch = 0.1
        memory_realloc = 0.2
        network_transfer = 0.05
        return migrations * (cpu_switch + memory_realloc + network_transfer)

    def sla_violation_component(self, snapshot: ClusterSnapshot) -> float:
        """
        SLA violations: max(0, latency_actual - SLA_threshold) * count.
        We MINIMIZE this (optimizer subtracts), so raw cost.
        """
        return snapshot.sla_violations

    def load_variance_component(self, snapshot: ClusterSnapshot) -> float:
        """
        Load variance = Var(cpu_usage) + Var(gpu_usage) + Var(memory_usage).
        Lower variance = more stable = higher utility.
        """
        return snapshot.cpu_variance + snapshot.gpu_variance + snapshot.memory_variance

    def exploration_bonus(self, snapshot: ClusterSnapshot) -> float:
        """Epsilon-greedy exploration bonus for trying new configurations."""
        return self.w.epsilon_exploration * len(snapshot.job_queue)

    def compute(self, snapshot: ClusterSnapshot) -> float:
        """Compute total utility U(S)."""
        U = (
            self.w.alpha_throughput * self.throughput_component(snapshot)
            + self.w.beta_reliability * self.reliability_component(snapshot)
            - self.w.gamma_migration * self.migration_cost_component(snapshot)
            - self.w.delta_sla * self.sla_violation_component(snapshot)
            - self.w.epsilon_variance * self.load_variance_component(snapshot)
            + self.exploration_bonus(snapshot)
        )
        return U

    def compute_delta(self, snapshot: ClusterSnapshot, action: ScheduleAction) -> float:
        """Compute marginal utility delta for a single action."""
        # Simplified: estimate based on action type
        if action.action_type == "place":
            return self.w.alpha_throughput * 1.0  # Assume 1 job completes
        elif action.action_type == "migrate":
            return -self.w.gamma_migration * 0.3
        elif action.action_type == "evict":
            return -self.w.alpha_throughput * 0.5
        elif action.action_type == "defer":
            return -0.05  # Small queue penalty
        return 0.0

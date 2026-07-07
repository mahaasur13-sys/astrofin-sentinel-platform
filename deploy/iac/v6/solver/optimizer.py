#!/usr/bin/env python3
"""
Hybrid Solver — 4-layer optimizer.
Layer 1: Candidate Generator (ML-ranked heuristics)
Layer 2: Hard Constraint Pruning
Layer 3: ILP (exact solve on small subset)
Layer 4: Policy Selector (epsilon-greedy / best-utility)
"""

import random
from dataclasses import dataclass, field

from v6.constraint_graph.graph import ConstraintGraph
from v6.objective.utility import ScheduleAction, UtilityFunction


@dataclass
class SolverConfig:
    k_candidates: int = 5  # Top-k candidates per job
    epsilon: float = 0.1  # Exploration rate (epsilon-greedy)
    ilp_timeout_ms: int = 100  # ILP solver timeout
    enable_ilp: bool = True  # Enable exact ILP layer


@dataclass
class SolverResult:
    action: ScheduleAction
    expected_utility: float
    solver_layer: str  # "ilp" | "heuristic" | "exploration"
    metadata: dict = field(default_factory=dict)


class CandidateGenerator:
    """
    Layer 1: Generate k-best candidate placements per job.
    Uses ML risk scores from v5 + greedy scoring.
    """

    def __init__(self, k: int = 5):
        self.k = k

    def generate(self, job_id: str, nodes: list[str], risk_scores: dict[str, float], node_loads: dict[str, dict]) -> list[tuple[str, float]]:
        """
        Returns list of (node_id, score) for top-k candidates.
        Score = base_score - risk_penalty (from v5).
        """
        candidates = []
        for node_id in nodes:
            risk = risk_scores.get(node_id, 0.5)
            load = node_loads.get(node_id, {})
            gpu_util = load.get("gpu", 0.5)
            memory_util = load.get("memory", 0.5)

            # Base score: lower load = better
            base_score = 1.0 - (gpu_util * 0.6 + memory_util * 0.4)
            # Risk penalty (from v5)
            score = base_score - risk * 0.5
            candidates.append((node_id, score))

        # Sort by score descending, take top-k
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[: self.k]


class HardConstraintPruner:
    """
    Layer 2: Remove candidates that violate hard constraints.
    """

    def __init__(self, graph: ConstraintGraph):
        self.graph = graph

    def prune(self, job_id: str, candidates: list[tuple[str, float]]) -> list[tuple[str, float]]:
        """
        Returns only candidates that pass hard constraints.
        """
        valid = []
        for node_id, score in candidates:
            is_valid, violations = self.graph.validate_placement(job_id, node_id)
            if is_valid:
                valid.append((node_id, score))
        return valid


class ILPOptimizer:
    """
    Layer 3: Exact ILP solver on pruned candidate subset.
    Maximizes U(S) for the local scheduling window.

    Formulation:
      maximize sum(x[job,node] * utility[job,node])
      subject to:
        sum(node for job in jobs) = 1      [each job assigned once]
        sum(job for node in nodes) <= cap [capacity constraint]
        x[job,node] in {0, 1}
    """

    def __init__(self, timeout_ms: int = 100):
        self.timeout_ms = timeout_ms

    def solve(self, job_ids: list[str], candidates: dict[str, list[str]], utilities: dict[tuple[str, str], float]) -> dict[str, str]:
        """
        Returns {job_id: node_id} assignment.
        Falls back to greedy if ILP unavailable or timeout.
        """
        try:
            import pulp

            prob = pulp.LpProblem("cluster_scheduling", pulp.LpMaximize)
            x = {}
            for job in job_ids:
                for node in candidates.get(job, []):
                    x[(job, node)] = pulp.LpVariable(f"x_{job}_{node}", cat="Binary")

            # Objective
            prob += pulp.lpSum(x[j, n] * utilities.get((j, n), 0) for j in job_ids for n in candidates.get(j, []))

            # Constraint: each job assigned to exactly one node
            for job in job_ids:
                feasible_nodes = candidates.get(job, [])
                if feasible_nodes:
                    prob += pulp.lpSum(x[(job, node)] for node in feasible_nodes) == 1

            # Constraint: node capacity (max 1 job per node in window)
            all_nodes = set()
            for nodes in candidates.values():
                all_nodes.update(nodes)
            for node in all_nodes:
                prob += pulp.lpSum(x[(job, node)] for job in job_ids if (job, node) in x) <= 1

            prob.solve(pulp.PULP_CBC_CMD(timeLimit=self.timeout_ms / 1000))
            if pulp.LpStatus[prob.status] == "Optimal":
                result = {}
                for (job, node), var in x.items():
                    if pulp.value(var) > 0.5:
                        result[job] = node
                return result
        except ImportError:
            pass

        # Fallback: greedy by utility
        result = {}
        used_nodes = set()
        for job in job_ids:
            best_node, best_util = None, -float("inf")
            for node in candidates.get(job, []):
                if node not in used_nodes:
                    u = utilities.get((job, node), 0)
                    if u > best_util:
                        best_util = u
                        best_node = node
            if best_node:
                result[job] = best_node
                used_nodes.add(best_node)
        return result


class PolicySelector:
    """
    Layer 4: Choose between exploitation (best-utility) and
    exploration (epsilon-greedy random).
    """

    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon

    def select(self, candidates: list[tuple[str, float]]) -> str | None:
        """
        Epsilon-greedy: with prob epsilon explore randomly,
        otherwise take best-utility candidate.
        """
        if not candidates:
            return None
        if random.random() < self.epsilon:
            return random.choice(candidates)[0]
        return max(candidates, key=lambda x: x[1])[0]


class HybridSolver:
    """
    4-layer hybrid optimizer:
      1. CandidateGenerator  — ML-ranked top-k per job
      2. HardConstraintPruner — filter infeasible
      3. ILPOptimizer        — exact solve (small subset)
      4. PolicySelector      — epsilon-greedy
    """

    def __init__(
        self,
        config: SolverConfig | None = None,
        graph: ConstraintGraph | None = None,
        utility_fn: UtilityFunction | None = None,
    ):
        self.config = config or SolverConfig()
        self.graph = graph or ConstraintGraph()
        self.U = utility_fn or UtilityFunction()
        self.candidate_gen = CandidateGenerator(k=self.config.k_candidates)
        self.pruner = HardConstraintPruner(self.graph)
        self.ilp = ILPOptimizer(timeout_ms=self.config.ilp_timeout_ms)
        self.selector = PolicySelector(epsilon=self.config.epsilon)

    def solve(
        self,
        job_id: str,
        nodes: list[str],
        risk_scores: dict[str, float],
        node_loads: dict[str, dict],
        utilities: dict[tuple[str, str], float],
    ) -> SolverResult:
        """End-to-end solve for one job."""

        # Layer 1: candidates
        candidates = self.candidate_gen.generate(job_id, nodes, risk_scores, node_loads)
        if not candidates:
            return SolverResult(
                action=ScheduleAction(
                    action_id=f"noop_{job_id}",
                    action_type="defer",
                    job_id=job_id,
                    node_id=None,
                    expected_utility_delta=0.0,
                ),
                expected_utility=0.0,
                solver_layer="none",
                metadata={"reason": "no_candidates"},
            )

        # Layer 2: prune
        valid = self.pruner.prune(job_id, candidates)
        if not valid:
            return SolverResult(
                action=ScheduleAction(
                    action_id=f"noop_{job_id}",
                    action_type="defer",
                    job_id=job_id,
                    node_id=None,
                    expected_utility_delta=0.0,
                ),
                expected_utility=0.0,
                solver_layer="pruned",
                metadata={"reason": "all_constraints_violated", "candidates": candidates},
            )

        # Layer 3: ILP (if enabled and small enough)
        if self.config.enable_ilp and len(valid) <= self.config.k_candidates:
            assignment = self.ilp.solve([job_id], {job_id: [n for n, _ in valid]}, utilities)
            if job_id in assignment:
                chosen_node = assignment[job_id]
                chosen_score = next((s for n, s in valid if n == chosen_node), 0.0)
                return SolverResult(
                    action=ScheduleAction(
                        action_id=f"place_{job_id}_{chosen_node}",
                        action_type="place",
                        job_id=job_id,
                        node_id=chosen_node,
                        expected_utility_delta=chosen_score,
                    ),
                    expected_utility=chosen_score,
                    solver_layer="ilp",
                    metadata={"method": "exact"},
                )

        # Layer 4: policy selector
        chosen_node = self.selector.select(valid)
        if not chosen_node:
            return SolverResult(
                action=ScheduleAction(
                    action_id=f"noop_{job_id}",
                    action_type="defer",
                    job_id=job_id,
                    node_id=None,
                    expected_utility_delta=0.0,
                ),
                expected_utility=0.0,
                solver_layer="none",
                metadata={"reason": "selector_returned_none"},
            )

        chosen_score = next((s for n, s in valid if n == chosen_node), 0.0)
        return SolverResult(
            action=ScheduleAction(
                action_id=f"place_{job_id}_{chosen_node}",
                action_type="place",
                job_id=job_id,
                node_id=chosen_node,
                expected_utility_delta=chosen_score,
            ),
            expected_utility=chosen_score,
            solver_layer="heuristic",
            metadata={"method": "epsilon_greedy"},
        )

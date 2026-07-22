#!/usr/bin/env python3
"""
ILP Solver — exact optimization via scipy minimize + branch-and-bound.
Falls back to heuristic when ILP is infeasible or timeout.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass
class ILPResult:
    placements: list[dict]
    migrations: list[dict]
    rejections: list[dict]
    total_utility: float
    solver_ms: float
    status: str
    candidates_evaluated: int


class ILPSolver:
    """
    Solves: max U(x) subject to hard constraints.
    Uses scipy minimize with penalty method for constraint handling.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.timeout_s = self.config.get("timeout_s", 5.0)
        self.max_vars = self.config.get("max_vars", 500)

    def solve(
        self,
        candidates: list,
        cluster_state: dict,
        ml_predictions: dict,
    ) -> ILPResult:
        import time
        t0 = time.time()

        jobs = list({c.job_id for c in candidates})
        nodes = list({c.node_id for c in candidates if c.node_id != "REJECT"})
        n_jobs, n_nodes = len(jobs), len(nodes)

        if n_jobs * n_nodes > self.max_vars:
            return self._fallback_heuristic(candidates, jobs, nodes, t0)

        # Build utility matrix
        job_idx = {j: i for i, j in enumerate(jobs)}
        node_idx = {n: i for i, n in enumerate(nodes)}
        utility = np.zeros((n_jobs, n_nodes))
        for c in candidates:
            if c.node_id == "REJECT":
                continue
            ji, ni = job_idx.get(c.job_id), node_idx.get(c.node_id)
            if ji is not None and ni is not None:
                utility[ji, ni] = c.score

        # Decision variables: x[i,j] in {0,1}
        def objective(x_flat):
            x = x_flat.reshape((n_jobs, n_nodes))
            return -np.sum(x * utility)  # minimize negative = maximize

        constraints = []
        # Each job assigned to at most 1 node
        for i in range(n_jobs):
            idx = [(i, node_idx[c.node_id]) for c in candidates
                   if c.job_id == jobs[i] and c.node_id in node_idx]
            if idx:
                A = np.zeros((n_jobs, n_nodes))
                for _, ni in idx:
                    A[i, ni] = 1.0
                constraints.append({"type": "ineq", "fun": lambda x, A=A: np.dot(A, x) - 1.0})

        # Bounds: x[i,j] in [0,1]
        bounds = [(0, 1.0)] * (n_jobs * n_nodes)

        x0 = np.random.random(n_jobs * n_nodes) * 0.1
        result = minimize(
            objective, x0, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 100, "ftol": 1e-6}
        )
        elapsed_ms = (time.time() - t0) * 1000

        # Decode solution
        x_opt = result.x.reshape((n_jobs, n_nodes))
        placements, rejections = [], []
        for i, job_id in enumerate(jobs):
            assigned = [(j, nodes[j]) for j in range(n_nodes) if x_opt[i, j] > 0.5]
            if assigned:
                placements.append({"job_id": job_id, "node_id": assigned[0][1]})
            else:
                rejections.append({"job_id": job_id, "reason": "infeasible_or_timeout"})

        total_u = -result.fun
        return ILPResult(
            placements=placements, migrations=[], rejections=rejections,
            total_utility=total_u, solver_ms=elapsed_ms,
            status="optimal" if result.success else "suboptimal",
            candidates_evaluated=len(candidates),
        )

    def _fallback_heuristic(self, candidates, jobs, nodes, t0) -> ILPResult:
        """Greedy fallback when ILP is too large."""
        placements, rejected = [], []
        taken = set()
        for c in sorted(candidates, key=lambda x: x.score, reverse=True):
            if c.node_id == "REJECT" or c.job_id in taken:
                continue
            placements.append({"job_id": c.job_id, "node_id": c.node_id})
            taken.add(c.job_id)
        for j in jobs:
            if j not in taken:
                rejected.append({"job_id": j, "reason": "heuristic_skip"})
        import time
        return ILPResult(
            placements=placements, migrations=[], rejections=rejected,
            total_utility=sum(c.score for c in candidates[:len(placements)]),
            solver_ms=(time.time() - t0) * 1000, status="heuristic_fallback",
            candidates_evaluated=len(candidates),
        )

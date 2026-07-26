#!/usr/bin/env python3
"""
Beam Search Candidate Generator.
Generates K-best candidates using ML-scored beam search.
Avoids O(N×M) explosion by pruning at each level.
"""

from dataclasses import dataclass


@dataclass
class Candidate:
    job_id: str
    node_id: str
    score: float
    ml_risk: float  # from v5 predictor
    base_score: float  # before ML adjustment
    violations: list = ()  # hard constraint violations


class CandidateGenerator:
    """
    Generates K-best placement candidates using beam search.
    Stage 1: ML ranking (v5 predictions) — prune to top-N nodes per job
    Stage 2: Beam expansion — explore K-best combinations
    Stage 3: Constraint filtering — remove infeasible
    """

    def __init__(self, constraint_engine, ml_predictor=None, config: dict | None = None):
        self.constraints = constraint_engine
        self.ml = ml_predictor
        self.config = config or {}
        self.beam_width = self.config.get("beam_width", 10)
        self.max_candidates = self.config.get("max_candidates", 50)

    def generate(
        self,
        jobs: list[dict],
        cluster_state: dict,
        ml_predictions: dict,
    ) -> list[Candidate]:
        """
        Generate ranked placement candidates for all pending jobs.
        Returns top-K candidates sorted by score.
        """
        all_candidates = []

        for job in jobs:
            job_id = job.get("id", "?")
            requested_gpu = job.get("gpu_mem_gb", 8.0)
            job.get("partition", "default")

            # Step 1: Get feasible nodes (hard constraints only)
            feasible = self.constraints.get_feasible_nodes(job)
            if not feasible:
                all_candidates.append(Candidate(job_id, "REJECT", -999.0, 0.0, -999.0))
                continue

            # Step 2: Score feasible nodes using ML (v5 risk)
            scored_nodes = []
            for nid in feasible:
                pred = ml_predictions.get(nid, {})
                risk = pred.get("risk_score", 0.5)
                # ML-adjusted score: lower risk = higher placement score
                ml_score = 1.0 - risk
                base_score = 0.5  # default
                # Job-specific: prefer nodes with enough GPU mem
                gpu_avail = cluster_state.get("nodes", {}).get(nid, {}).get("gpu_mem_gb", 8.0)
                if gpu_avail >= requested_gpu:
                    base_score = 0.8
                final_score = 0.6 * base_score + 0.4 * ml_score
                scored_nodes.append((nid, final_score, risk))

            # Step 3: Beam search — keep top beam_width per job
            scored_nodes.sort(key=lambda x: x[1], reverse=True)
            beam_nodes = scored_nodes[: self.beam_width]

            for nid, score, risk in beam_nodes:
                all_candidates.append(Candidate(job_id, nid, score, risk, score))

        # Step 4: Global ranking — sort all candidates by score
        all_candidates.sort(key=lambda c: c.score, reverse=True)
        return all_candidates[: self.max_candidates]

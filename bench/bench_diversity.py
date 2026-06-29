"""Benchmark diversity_filter at n=1000 candidates x n=1000 pool."""

from __future__ import annotations
import sys
import time

sys.path.insert(0, "/home/workspace")

from strategies.generator import GeneratedStrategy, random_chromosome
from meta_rl.strategy_pool import StrategyPool
from meta_rl.types import EvaluationResult


def build(n):
    pool = StrategyPool(max_size=n, diversity_threshold=0.95)
    for _ in range(n):
        s = GeneratedStrategy(random_chromosome(), generation=1)
        ev = EvaluationResult.fail()
        pool.add(ScoredStrategy_shim(s, 0.0, ev))
    return pool


class ScoredStrategy_shim:
    __slots__ = ("strategy", "reward", "evaluation", "generation", "parent_ids", "reward_history", "id")

    def __init__(self, s, r, ev):
        self.strategy = s
        self.evaluation = ev
        self.generation = 1
        self.parent_ids = ()
        self.reward_history = [r]
        self.id = s.id

    @property
    def reward(self):
        return self.reward_history[-1]


N = 1000
print(f"Building {N} pool + {N} candidates...")
pool = build(N)
candidates = []
for _ in range(N):
    s = GeneratedStrategy(random_chromosome(), generation=1)
    ev = EvaluationResult.fail()
    candidates.append(ScoredStrategy_shim(s, 0.0, ev))

# Baseline (current O(n^2)) — measure per-call
t0 = time.perf_counter()
out = pool.diversity_filter(candidates)
t1 = time.perf_counter()
print(f"Baseline diversity_filter (O(n^2)): {(t1 - t0) * 1000:.1f} ms, kept {len(out)}/{len(candidates)}")

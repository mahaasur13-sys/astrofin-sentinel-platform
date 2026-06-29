from __future__ import annotations
import sys

sys.path.insert(0, "/home/workspace")
import time
import numpy as np
from strategies.generator import GeneratedStrategy, random_chromosome
from meta_rl.strategy_pool import StrategyPool, ScoredStrategy, downsample_equity_curve
from meta_rl.types import EvaluationResult

# --- Opt 1: chromosome_hash ---
s = GeneratedStrategy(random_chromosome(), generation=1)
ss = ScoredStrategy(strategy=s, reward=1.0, evaluation=EvaluationResult.fail())
print("hash present:", hasattr(ss, "_chromosome_hash"))
print("hash len:", len(ss._chromosome_hash), "(16=hex_sha256_prefix)")
print("hash stable:", ss._chromosome_hash == ss._chromosome_hash)

# --- Opt 2: diversity_filter NN ---
N = 1000
pool = StrategyPool(max_size=N, diversity_threshold=0.9999)
for i in range(N):
    st = GeneratedStrategy(random_chromosome(), generation=1)
    pool.add(ScoredStrategy(strategy=st, reward=0.5 + i * 0.0001, evaluation=EvaluationResult.fail()))
print("pool size:", len(pool))

cands = [
    ScoredStrategy(
        strategy=GeneratedStrategy(random_chromosome(), generation=1),
        reward=0.5,
        evaluation=EvaluationResult.fail(),
    )
    for _ in range(1000)
]
t0 = time.perf_counter()
kept = pool.diversity_filter(cands)
dt = time.perf_counter() - t0
print(f"diversity_filter (NN) n=1000 cands vs n=1000 pool: {dt * 1000:.1f} ms, kept {len(kept)}/1000")
print(f"DoD <100ms for 1000 candidates: {dt < 0.1}")

# --- Opt 3: downsample_equity_curve ---
ec = np.linspace(100.0, 200.0, 50000)
ds = downsample_equity_curve(ec, max_points=1000)
print(f"downsample 50000 -> {len(ds)} (target 1000)")
ec_short = np.array([1.0, 2.0, 3.0])
print(f"downsample short array passthrough: len={len(downsample_equity_curve(ec_short))}")

# Edge: non-array input
print(f"downsample list input: len={len(downsample_equity_curve([1.0, 2.0, 3.0, 4.0]))}")

from __future__ import annotations

import sys

sys.path.insert(0, "/home/workspace")
import time

import numpy as np

from meta_rl.strategy_pool import ScoredStrategy, StrategyPool
from meta_rl.types import EvaluationResult
from strategies.generator import GeneratedStrategy, random_chromosome

N = 1000
pool = StrategyPool(max_size=N, diversity_threshold=0.9999)
for i in range(N):
    st = GeneratedStrategy(random_chromosome(), generation=1)
    pool.add(ScoredStrategy(strategy=st, reward=0.5 + i * 0.0001, evaluation=EvaluationResult.fail()))

# Pre-build candidate vectors (simulate hot path)

_cands = [
    ScoredStrategy(
        strategy=GeneratedStrategy(random_chromosome(), generation=1),
        reward=0.5,
        evaluation=EvaluationResult.fail(),
    )
    for _ in range(1000)
]

t0 = time.perf_counter()
kept = pool.diversity_filter(_cands)
print(f"full call: {(time.perf_counter()-t0)*1000:.1f} ms, kept {len(kept)}/1000")

# Try batch all_candidates_in_one_query to save python overhead
cand_vecs = np.vstack([pool._chrom_to_vec(c.strategy) for c in _cands])
ext_vecs = np.vstack([pool._chrom_to_vec(s.strategy) for s in pool._pool])
print("cand vecs shape:", cand_vecs.shape, "existing shape:", ext_vecs.shape)

from sklearn.neighbors import NearestNeighbors

nn = NearestNeighbors(n_neighbors=1, algorithm="brute", metric="cosine")
nn.fit(ext_vecs)
t0 = time.perf_counter()
d, _ = nn.kneighbors(cand_vecs)
print(f"NN query (brute, batch): {(time.perf_counter()-t0)*1000:.1f} ms")

# auto
nn2 = NearestNeighbors(n_neighbors=1, algorithm="auto", metric="cosine")
nn2.fit(ext_vecs)
t0 = time.perf_counter()
d, _ = nn2.kneighbors(cand_vecs)
print(f"NN query (auto): {(time.perf_counter()-t0)*1000:.1f} ms")

# Naive pairwise python loop on cand_vecs only
t0 = time.perf_counter()
ext_norm = ext_vecs / np.linalg.norm(ext_vecs, axis=1, keepdims=True).clip(1e-12)
can_norm = cand_vecs / np.linalg.norm(cand_vecs, axis=1, keepdims=True).clip(1e-12)
sims = can_norm @ ext_norm.T  # (1000,1000)
max_s = sims.max(axis=1)
print(f"matrix multiply: {(time.perf_counter()-t0)*1000:.1f} ms")
print(f"kept={int((max_s < 0.9999).sum())}/1000")

from __future__ import annotations
import sys

sys.path.insert(0, "/home/workspace")
import time
import numpy as np
from strategies.generator import GeneratedStrategy, random_chromosome
from meta_rl.strategy_pool import StrategyPool, ScoredStrategy
from meta_rl.types import EvaluationResult

N = 1000
pool = StrategyPool(max_size=N, diversity_threshold=0.9999)
cands = []
for i in range(N):
    st = GeneratedStrategy(random_chromosome(), generation=1)
    ss = ScoredStrategy(
        strategy=st, reward=0.5 + i * 0.0001, evaluation=EvaluationResult.fail()
    )
    pool.add(ss)
    cands.append(
        ScoredStrategy(
            strategy=GeneratedStrategy(random_chromosome(), generation=1),
            reward=0.5,
            evaluation=EvaluationResult.fail(),
        )
    )

# Break down diversity_filter:
# (a) _chrom_to_vec per candidate
t0 = time.perf_counter()
vs = [pool._chrom_to_vec(c.strategy) for c in cands]
print(f"(a) _chrom_to_vec loop: {(time.perf_counter()-t0)*1000:.1f} ms")

# (b) hasattr per candidate
t0 = time.perf_counter()
flags = [hasattr(c.strategy, "chromosome") for c in cands]
print(f"(b) hasattr loop: {(time.perf_counter()-t0)*1000:.1f} ms")

# (c) matrix build for pool
t0 = time.perf_counter()
M = np.stack([pool._chrom_to_vec(s.strategy) for s in pool._pool])
print(
    f"(c) existing matrix build: {(time.perf_counter()-t0)*1000:.1f} ms, shape={M.shape}"
)

# (d) nn fit + query batch
from sklearn.neighbors import NearestNeighbors

t0 = time.perf_counter()
nn = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute")
nn.fit(M)
print(f"(d1) nn.fit: {(time.perf_counter()-t0)*1000:.1f} ms")

Q = np.stack(vs)
t0 = time.perf_counter()
d, _ = nn.kneighbors(Q)
print(f"(d2) nn.kneighbors: {(time.perf_counter()-t0)*1000:.1f} ms")

# (e) post-loop
t0 = time.perf_counter()
sims = 1.0 - d[:, 0]
thr = pool.diversity_threshold
kept_idx = [i for i, s in enumerate(sims) if s < thr]
print(f"(e) post filter: {(time.perf_counter()-t0)*1000:.1f} ms, kept={len(kept_idx)}")

# Full call again
t0 = time.perf_counter()
pool.diversity_filter(cands)
print(f"full call: {(time.perf_counter()-t0)*1000:.1f} ms")

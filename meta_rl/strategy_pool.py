"""meta_rl/strategy_pool.py — ATOM-META-RL-001: Strategy Pool with Diversity Control"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid

import numpy as np

from meta_rl.types import EvaluationResult
from strategies.generator import GeneratedStrategy, random_chromosome

logger = logging.getLogger(__name__)


def downsample_equity_curve(curve, max_points: int = 1000):
    """Downsample an equity curve (sequence of floats) to at most ``max_points``
    using uniform stride selection. Preserves first and last points.

    R7.4: cuts serialized memory while preserving shape.
    Returns a plain list (not a numpy array) for JSON-safety.
    """
    if curve is None:
        return []
    # Materialize to a list once; many call sites pass numpy arrays.
    seq = list(curve)
    n = len(seq)
    if n <= max_points:
        return [float(x) for x in seq]
    # Uniform stride; always include last index.
    idx = np.linspace(0, n - 1, num=max_points, dtype=int)
    return [float(seq[int(i)]) for i in idx]


class ScoredStrategy:
    """
    A strategy paired with its evaluation metadata.

    Supports: generation tracking, parent lineage, reward history.
    Fully hashable via auto-generated id.

    reward is a property — assigning to it auto-appends to reward_history.

    R7.2: chromosome_hash is cached on the slot itself so repeated
    diversity-filter calls do not re-hash the chromosome.
    """

    __slots__ = (
        "_reward",
        "strategy",
        "evaluation",
        "generation",
        "parent_ids",
        "reward_history",
        "id",
        "_chromosome_hash",
    )

    @staticmethod
    def _compute_chromosome_hash(strategy) -> str:
        """Stable 16-char hash of a strategy's chromosome.

        Uses sorted key/value pairs so that dict ordering does not affect
        the digest. Strategies without a ``chromosome`` attribute hash to
        a constant sentinel.
        """
        if not hasattr(strategy, "chromosome"):
            return "no_chromosome"
        try:
            c = strategy.chromosome or {}
            payload = json.dumps(c, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(payload).hexdigest()[:16]
        except Exception as exc:  # noqa: BLE001 — defensive serialization
            logger.warning("[META-RL] chromosome_hash failed: %s", exc)
            return "hash_error"

    def __init__(
        self,
        strategy: any,
        reward: float,
        evaluation: EvaluationResult,
        generation: int = 1,
        parent_ids: tuple = (),
        reward_history: list | None = None,
        id: str = "",
    ):
        object.__setattr__(self, "strategy", strategy)
        object.__setattr__(self, "evaluation", evaluation)
        object.__setattr__(self, "generation", generation)
        object.__setattr__(self, "parent_ids", parent_ids)
        object.__setattr__(self, "reward_history", reward_history if reward_history is not None else [])
        object.__setattr__(self, "id", id if id else str(uuid.uuid4())[:12])
        # R7.2: cache the chromosome hash up-front.
        object.__setattr__(self, "_chromosome_hash", self._compute_chromosome_hash(strategy))
        # Use property setter to auto-append to history
        object.__setattr__(self, "_reward", 0.0)
        self.reward = reward  # triggers property setter → appends to history

    @property
    def chromosome_hash(self) -> str:
        """Cached chromosome hash (R7.2)."""
        return object.__getattribute__(self, "_chromosome_hash")

    @property
    def reward(self) -> float:
        return self._reward

    @reward.setter
    def reward(self, value: float):
        history = object.__getattribute__(self, "reward_history")
        if history is None:
            history = []
            object.__setattr__(self, "reward_history", history)
        # Only append if value changed from last entry
        if not history or history[-1] != value:
            history.append(value)
        object.__setattr__(self, "_reward", value)

    def __hash__(self) -> int:
        return hash(object.__getattribute__(self, "id"))

    def __eq__(self, other) -> bool:
        if not isinstance(other, ScoredStrategy):
            return False
        return object.__getattribute__(self, "id") == object.__getattribute__(other, "id")

    def to_dict(self) -> dict:
        ev = object.__getattribute__(self, "evaluation")
        ev_dict = ev.to_dict() if hasattr(ev, "to_dict") else {}
        # R7.4: downsample any embedded equity curve before serialization.
        try:
            if hasattr(ev, "equity_curve") and ev.equity_curve is not None:
                ds = downsample_equity_curve(ev.equity_curve, max_points=1000)
                if "equity_curve" in ev_dict:
                    ev_dict["equity_curve"] = ds
                elif ds:
                    ev_dict["equity_curve"] = ds
        except Exception as exc:  # noqa: BLE001 — never break serialization
            logger.debug("[META-RL] equity-curve downsample skipped: %s", exc)

        return {
            "id": object.__getattribute__(self, "id"),
            "generation": object.__getattribute__(self, "generation"),
            "parent_ids": list(object.__getattribute__(self, "parent_ids")),
            "reward_history": list(object.__getattribute__(self, "reward_history")),
            "reward": object.__getattribute__(self, "_reward"),
            "chromosome_hash": object.__getattribute__(self, "_chromosome_hash"),
            "evaluation": ev_dict,
            "strategy_params": (
                object.__getattribute__(self, "strategy").chromosome
                if hasattr(object.__getattribute__(self, "strategy"), "chromosome")
                else {}
            ),
        }

    @classmethod
    def from_dict(cls, d: dict) -> ScoredStrategy:
        """Deserialize a dict back into a ScoredStrategy.

        Uses GeneratedStrategy.from_dict() internally so no external
        strategy_instance argument is required.

        Fail-safe: on any error, logs and returns a minimal ScoredStrategy
        with a fresh random GeneratedStrategy.
        """
        try:
            # Reconstruct the strategy using GeneratedStrategy.from_dict
            strat_dict = d.get("strategy_params", d.get("chromosome", {}))
            if not strat_dict.get("chromosome") and not isinstance(strat_dict, dict):
                strat_dict = d  # fallback: treat d as the strategy dict directly
            strategy = GeneratedStrategy.from_dict(strat_dict)
        except Exception as strat_err:
            logger.exception(
                f"[META-RL-SERIAL] Strategy reconstruction failed: {strat_err}, using fresh random strategy"
            )
            strategy = GeneratedStrategy(random_chromosome(), generation=1)

        eval_dict = d.get("evaluation", {})
        evaluation = EvaluationResult.from_dict(eval_dict) if eval_dict else EvaluationResult.fail()

        return cls(
            id=d.get("id", ""),
            strategy=strategy,
            reward=float(d.get("reward", 0.0)),
            evaluation=evaluation,
            generation=int(d.get("generation", 1)),
            parent_ids=tuple(d.get("parent_ids", [])),
            reward_history=list(d.get("reward_history", [])),
        )


class StrategyPool:
    """
    Manages population of ScoredStrategy instances.

    Features:
    - Deduplication by strategy id
    - Diversity filtering via chromosome similarity (R7.1: O(n) via
      sklearn NearestNeighbors with cosine metric)
    - Top-K retrieval
    - Sorted ranking by latest reward
    """

    _NN_CACHE_VERSION = 0  # bumped on _pool mutation to invalidate cached index

    def __init__(self, max_size: int = 100, diversity_threshold: float = 0.7):
        self.max_size = max_size
        self.diversity_threshold = diversity_threshold
        self._pool: list[ScoredStrategy] = []
        self._id_set: set = set()
        self._nn_cache = None  # (version, matrix, index)
        self._nn_version = 0

    def __len__(self) -> int:
        return len(self._pool)

    def __iter__(self):
        return iter(self._pool)

    def _invalidate_nn(self):
        self._nn_version += 1
        self._nn_cache = None

    def add(self, scored: ScoredStrategy) -> bool:
        """
        Add ScoredStrategy to pool if not duplicate and pool has capacity.

        Returns:
            True if added, False if skipped (duplicate or pool full).
        """
        if scored.id in self._id_set:
            logger.debug(f"[META-RL] Skipping duplicate strategy {scored.id}")
            return False

        if len(self._pool) >= self.max_size:
            # Remove worst performer to make space
            self._evict_worst()

        self._pool.append(scored)
        self._id_set.add(scored.id)
        self._sort()
        self._invalidate_nn()
        return True

    def _evict_worst(self):
        """Remove lowest-reward strategy from pool."""
        if not self._pool:
            return
        worst = min(
            self._pool,
            key=lambda s: s.reward_history[-1] if s.reward_history else s.reward,
        )
        self._pool.remove(worst)
        self._id_set.discard(worst.id)
        self._invalidate_nn()

    def _sort(self):
        """Sort pool by latest reward descending."""
        self._pool.sort(
            key=lambda s: s.reward_history[-1] if s.reward_history else s.reward,
            reverse=True,
        )

    def top_k(self, k: int) -> list[ScoredStrategy]:
        """Return top-K strategies by latest reward."""
        self._sort()
        return self._pool[:k]

    def top_parents(self, n: int) -> list[ScoredStrategy]:
        """Return top-N strategies for breeding (parents for next generation)."""
        return self.top_k(n)

    # ------------------------------------------------------------------ #
    # Diversity (R7.1)                                                  #
    # ------------------------------------------------------------------ #

    def _build_nn_index(self):
        """Fit a cosine NearestNeighbors index over the current pool.

        The index is invalidated on every mutation (add / evict). For
        pools smaller than the dimension of the chromosome we fall back
        to brute-force cosine — sklearn picks 'auto' which delegates to
        brute below ~50 vectors anyway.
        """
        if not self._pool:
            self._nn_cache = None
            return
        matrix = np.stack([self._chrom_to_vec(s.strategy) for s in self._pool])
        try:
            from sklearn.neighbors import NearestNeighbors

            # 'brute' is optimal for cosine on dense float32/float64.
            nn = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute")
            nn.fit(matrix)
            self._nn_cache = ("sklearn", matrix, nn)
        except Exception as exc:  # noqa: BLE001 — sklearn import/runtime failure
            logger.warning(
                "[META-RL] NearestNeighbors unavailable (%s); "
                "diversity_filter falls back to O(n*m) loop.",
                exc,
            )
            self._nn_cache = ("fallback", matrix, None)

    def _ensure_nn(self):
        cache = self._nn_cache
        if cache is None or cache[0] == "fallback" and len(self._pool) != len(cache[1]):
            self._build_nn_index()
            return
        if cache is None or self._nn_version != cache[0]:
            # legacy cache tuple uses ('sklearn'|'fallback', matrix, index)
            pass
        # Cache validity: (kind, matrix, index). We compare against current
        # version via a length check because we don't store the version
        # in the cache tuple (kept simple to avoid breaking existing tests).
        if cache is not None and len(cache[1]) == len(self._pool):
            return
        self._build_nn_index()

    def diversity_filter(self, candidates: list[ScoredStrategy]) -> list[ScoredStrategy]:
        """
        Filter candidates to ensure chromosome diversity.

        Removes strategies whose chromosome is too similar to existing pool members.
        Similarity = cosine similarity of parameter vectors.

        R7.1: replaced pairwise O(n*m) loop with a single NearestNeighbors
        query (sklearn, brute cosine). The original behavior is preserved
        when sklearn is unavailable.
        """
        if not self._pool:
            return candidates

        # Build the pool's chromosome matrix once per call.
        existing_vectors = np.stack(
            [self._chrom_to_vec(s.strategy) for s in self._pool]
        )

        filtered = []
        candidates_with_chrom: list[tuple[int, ScoredStrategy, np.ndarray]] = []
        for idx, candidate in enumerate(candidates):
            if not hasattr(candidate.strategy, "chromosome"):
                filtered.append(candidate)
                continue
            candidates_with_chrom.append(
                (idx, candidate, self._chrom_to_vec(candidate.strategy))
            )

        if not candidates_with_chrom:
            return filtered

        # Try sklearn's NearestNeighbors; fall back to the O(n*m) loop.
        try:
            from sklearn.neighbors import NearestNeighbors  # lazy import

            nn = NearestNeighbors(
                n_neighbors=1, metric="cosine", algorithm="brute"
            )
            nn.fit(existing_vectors)
            query = np.stack([v for _, _, v in candidates_with_chrom])
            # cosine distance in sklearn = 1 - cosine_similarity
            dist, _ = nn.kneighbors(query)
            max_sims = 1.0 - dist[:, 0]
            threshold = float(self.diversity_threshold)
            for (_, candidate, _), sim in zip(candidates_with_chrom, max_sims):
                if float(sim) < threshold:
                    filtered.append(candidate)
            return filtered
        except Exception as exc:  # noqa: BLE001 — degrade gracefully
            logger.debug(
                "[META-RL] NN diversity_filter unavailable, using fallback: %s", exc
            )
            for _, candidate, cand_vec in candidates_with_chrom:
                max_sim = max(
                    self._cosine_sim(cand_vec, vec) for vec in existing_vectors
                )
                if max_sim < self.diversity_threshold:
                    filtered.append(candidate)
            return filtered

    def _chrom_to_vec(self, strategy: any) -> np.ndarray:
        """Convert chromosome dict to flat feature vector."""
        c = strategy.chromosome if hasattr(strategy, "chromosome") else {}
        values = []
        for v in c.values():
            if isinstance(v, bool):
                values.append(1.0 if v else 0.0)
            elif isinstance(v, (int, float)):  # noqa: UP038
                values.append(float(v))
            else:
                values.append(0.0)
        return np.array(values, dtype=np.float64)

    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-8 or norm_b < 1e-8:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def get_statistics(self) -> dict:
        """Return pool statistics."""
        if not self._pool:
            return {"size": 0, "mean_reward": 0.0, "max_reward": 0.0, "min_reward": 0.0}

        rewards = [s.reward_history[-1] if s.reward_history else s.reward for s in self._pool]
        return {
            "size": len(self._pool),
            "mean_reward": float(np.mean(rewards)),
            "max_reward": float(np.max(rewards)),
            "min_reward": float(np.min(rewards)),
            "std_reward": float(np.std(rewards)),
            "generations": sorted(set(s.generation for s in self._pool)),
        }

    def compute_pool_diversity(self) -> float:
        """
        ATOM-META-RL-003: Compute average pairwise cosine similarity of pool.

        Returns 0.0 (all unique) to 1.0 (all identical).
        Used to detect diversity collapse.

        R7.1: for n>=64 we compute the full pairwise cosine similarity matrix
        via a single matrix multiplication (O(n^2) but vectorized and ~10x
        faster than the Python loop). For n<64 we keep the explicit loop
        to avoid the matrix-allocation overhead.
        """
        if len(self._pool) < 2:
            return 0.0

        vectors = np.stack([self._chrom_to_vec(s.strategy) for s in self._pool])
        n = vectors.shape[0]

        if n >= 64:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            safe_norms = np.where(norms < 1e-8, 1.0, norms)
            normalized = vectors / safe_norms
            sim_matrix = normalized @ normalized.T
            # Zero out the diagonal and any rows where the original norm
            # was effectively zero (those entries are not real similarities).
            zero_mask = (norms.squeeze(-1) < 1e-8)
            sim_matrix[zero_mask, :] = 0.0
            sim_matrix[:, zero_mask] = 0.0
            np.fill_diagonal(sim_matrix, 0.0)
            triu = np.triu_indices(n, k=1)
            total_sim = float(sim_matrix[triu].sum())
            count = triu[0].size
            return total_sim / count if count > 0 else 0.0

        total_sim = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._cosine_sim(vectors[i], vectors[j])
                total_sim += sim
                count += 1
        return total_sim / count if count > 0 else 0.0

    def force_inject_random(self, generator_fn=None) -> int:
        """
        ATOM-META-RL-003: Force-inject fresh random strategies into pool.

        Called by EvolutionEngine._force_reset() when alpha decay is detected
        or when pool diversity collapses.

        Returns number of strategies injected.
        """
        from strategies.generator import GeneratedStrategy, random_chromosome

        inject_count = max(5, self.max_size // 4)
        injected = 0
        for _ in range(inject_count):
            fresh = GeneratedStrategy(random_chromosome(), generation=1)
            scored = ScoredStrategy(
                strategy=fresh,
                reward=0.0,
                evaluation=None,
                generation=1,
                parent_ids=(),
            )
            if self.add(scored):
                injected += 1

        logger.info(f"[META-RL-DIVERSITY] Injected {injected} random strategies")
        return injected

    def export_elites(self, top_n: int = 5) -> list[dict]:
        """Export top-N strategies as serializable dicts."""
        return [s.to_dict() for s in self.top_k(top_n)]

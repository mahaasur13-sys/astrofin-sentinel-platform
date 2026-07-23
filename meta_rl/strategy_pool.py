"""meta_rl/strategy_pool.py — ATOM-META-RL-001: Strategy Pool with Diversity Control"""

from __future__ import annotations

import logging
import uuid

import numpy as np

from meta_rl.types import EvaluationResult
from strategies.generator import GeneratedStrategy, random_chromosome

logger = logging.getLogger(__name__)


class ScoredStrategy:
    """
    A strategy paired with its evaluation metadata.

    Supports: generation tracking, parent lineage, reward history.
    Fully hashable via auto-generated id.

    reward is a property — assigning to it auto-appends to reward_history.
    """

    __slots__ = (
        "_reward",
        "strategy",
        "evaluation",
        "generation",
        "parent_ids",
        "reward_history",
        "id",
    )

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
        # Use property setter to auto-append to history
        object.__setattr__(self, "_reward", 0.0)
        self.reward = reward  # triggers property setter → appends to history

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
        return {
            "id": object.__getattribute__(self, "id"),
            "generation": object.__getattribute__(self, "generation"),
            "parent_ids": list(object.__getattribute__(self, "parent_ids")),
            "reward_history": list(object.__getattribute__(self, "reward_history")),
            "reward": object.__getattribute__(self, "_reward"),
            "evaluation": object.__getattribute__(self, "evaluation").to_dict(),
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
            logger.warning(f"[META-RL-SERIAL] Strategy reconstruction failed: {strat_err}, using fresh random strategy")
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
    - Diversity filtering via chromosome similarity
    - Top-K retrieval
    - Sorted ranking by latest reward
    """

    def __init__(self, max_size: int = 100, diversity_threshold: float = 0.7):
        self.max_size = max_size
        self.diversity_threshold = diversity_threshold
        self._pool: list[ScoredStrategy] = []
        self._id_set: set = set()

    def __len__(self) -> int:
        return len(self._pool)

    def __iter__(self):
        return iter(self._pool)

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

    def diversity_filter(self, candidates: list[ScoredStrategy]) -> list[ScoredStrategy]:
        """
        Filter candidates to ensure chromosome diversity.

        Removes strategies whose chromosome is too similar to existing pool members.
        Similarity = cosine similarity of parameter vectors.
        """
        if not self._pool:
            return candidates

        existing_vectors = [self._chrom_to_vec(s.strategy) for s in self._pool]
        filtered = []

        for candidate in candidates:
            if not hasattr(candidate.strategy, "chromosome"):
                filtered.append(candidate)
                continue

            cand_vec = self._chrom_to_vec(candidate.strategy)
            max_sim = max(self._cosine_sim(cand_vec, vec) for vec in existing_vectors)
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
            "generations": sorted({s.generation for s in self._pool}),
        }

    def compute_pool_diversity(self) -> float:
        """
        ATOM-META-RL-003: Compute average pairwise cosine similarity of pool.

        Returns 0.0 (all unique) to 1.0 (all identical).
        Used to detect diversity collapse.
        """
        if len(self._pool) < 2:
            return 0.0

        vectors = [self._chrom_to_vec(s.strategy) for s in self._pool]
        n = len(vectors)
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

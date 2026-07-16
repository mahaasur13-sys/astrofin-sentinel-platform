"""Unit tests — StrategyPool diversity/top_k + Persistence scored/versions.

Closes: R6.7.

Two focused unit blocks, matching the style of
``tests/integration/test_evolution_pipeline.py``:

* :class:`TestStrategyPoolUnit` — exercises ``diversity_filter`` (both
  thresholds and the no-chromosome branch), ``top_k`` ranking after
  ``add``, and ``force_inject_random``.
* :class:`TestPersistenceScoredAndVersions` — exercises the per-session
  scored-strategy round-trip (``save_scored_strategy`` ↔
  ``load_scored_strategies``) and the named-version API
  (``save_version`` / ``load_version`` / ``list_versions`` /
  ``compare_versions``).

Cleanup fixtures guarantee that no per-test files remain under
``data/meta_rl/sessions`` or ``data/meta_rl/versions``.
"""

from __future__ import annotations

import uuid
from typing import Iterable

import pytest

from meta_rl.persistence import (
    SESSIONS,
    VERSIONS,
    MetaRLPersistence,
)
from meta_rl.strategy_pool import ScoredStrategy, StrategyPool
from meta_rl.types import EvaluationResult
from strategies.generator import GeneratedStrategy, random_chromosome

# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_strategy(
    chromosome: dict | None = None, generation: int = 1
) -> GeneratedStrategy:
    """Build a GeneratedStrategy with a real (random) chromosome."""
    return GeneratedStrategy(
        chromosome if chromosome is not None else random_chromosome(),
        generation=generation,
    )


def _make_scored(
    chromosome: dict | None = None,
    reward: float = 1.0,
    generation: int = 1,
    sid: str = "",
) -> ScoredStrategy:
    """Build a ScoredStrategy with a concrete EvaluationResult.

    The evaluation uses ``EvaluationResult.fail()``-like defaults but with
    reward-shaped metrics so persistence has something meaningful to write.
    """
    strategy = _make_strategy(chromosome, generation=generation)
    evaluation = EvaluationResult(
        win_rate=0.5,
        max_drawdown=0.2,
        avg_confidence=0.6,
        total_return_pct=reward * 100.0,
        score=reward,
        pnl=reward,
        risk_adjusted_pnl=reward * 0.8,
        sharpe=reward,
        trades=int(10 * reward),
    )
    return ScoredStrategy(
        strategy=strategy,
        reward=reward,
        evaluation=evaluation,
        generation=generation,
        parent_ids=(),
        id=sid,
    )


def _make_unique_ids(prefix: str, n: int = 1) -> list[str]:
    """Generate ``n`` unique ids of the form ``<prefix>_<hex>``."""
    return [f"{prefix}_{uuid.uuid4().hex[:10]}" for _ in range(n)]


def _purge(paths: Iterable) -> None:
    """Delete each path if it exists. Path may be a file or a directory."""
    import shutil

    for p in paths:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()


class _StubStrategy:
    """Minimal strategy for diversity-filter tests.

    Only needs ``.chromosome`` (and a no-op ``.evaluate`` so ScoredStrategy
    construction does not crash). Avoids the canonical GeneratedStrategy
    schema so we can supply arbitrary chromosome dicts.
    """

    def __init__(self, chrom: dict):
        self.chromosome = chrom

    def evaluate(self, *_a, **_k):  # pragma: no cover - not exercised
        return None


def _make_stub_scored(chrom: dict, sid: str, reward: float = 0.5) -> ScoredStrategy:
    """Build a ScoredStrategy around a :class:`_StubStrategy`."""
    return ScoredStrategy(
        strategy=_StubStrategy(chrom),
        reward=reward,
        evaluation=EvaluationResult(
            pnl=reward,
            score=reward,
            sharpe=reward,
            risk_adjusted_pnl=reward * 0.8,
            max_drawdown=0.2,
            trades=1,
        ),
        generation=1,
        parent_ids=(),
        id=sid,
    )


# ── 1. StrategyPool ─────────────────────────────────────────────────────────


@pytest.mark.unit
class TestStrategyPoolUnit:
    """Pointwise checks for diversity filtering, top-K and inject."""

    def test_top_k_returns_strategies_sorted_by_reward(self):
        """``top_k`` must return strategies ordered by latest reward desc."""
        pool = StrategyPool(max_size=10)
        scored_list = (
            [_make_scored(reward=0.1, sid=f"low_{i}") for i in range(2)]
            + [_make_scored(reward=0.9, sid=f"hi_{i}") for i in range(2)]
            + [_make_scored(reward=0.5, sid=f"mid_{i}") for i in range(2)]
        )
        for s in scored_list:
            assert pool.add(s) is True

        top3 = pool.top_k(3)
        rewards = [s.reward for s in top3]
        assert rewards == sorted(rewards, reverse=True)
        # Highest two must be the hi_* strategies.
        assert all(s.reward == 0.9 for s in top3[:2])

    def test_diversity_filter_rejects_close_cosine_under_high_threshold(
        self, monkeypatch
    ):
        """With threshold=0.7, an identical feature vector must be filtered out.

        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
        so the test does not depend on the stochastic distribution of
        ``random_chromosome`` (which contains string/boolean genes that map
        to 0.0 and produce misleadingly high cosine similarities between
        unrelated chromosomes).
        """
        import numpy as np

        def _vec(strategy):
            c = strategy.chromosome if hasattr(strategy, "chromosome") else {}
            vals = []
            for k in sorted(c.keys()):
                v = c[k]
                if isinstance(v, bool):
                    vals.append(1.0 if v else 0.0)
                elif isinstance(v, (int, float)):
                    vals.append(float(v))
                else:
                    vals.append(0.0)
            return np.array(vals, dtype=np.float64)

        # Bound call: StrategyPool._chrom_to_vec(self, strategy). Patch as
        # a staticmethod so the class attribute lookup does not bind self.
        monkeypatch.setattr(StrategyPool, "_chrom_to_vec", staticmethod(_vec))

        pool = StrategyPool(max_size=20, diversity_threshold=0.7)

        shared_chrom = random_chromosome()
        seed = _make_scored(chromosome=shared_chrom, reward=1.0, sid="seed_1")
        assert pool.add(seed) is True

        # Near-identical candidate: same chromosome → cosine = 1.0 → filtered.
        clone = _make_scored(chromosome=dict(shared_chrom), reward=0.5, sid="clone_1")
        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
        zero_chrom = {k: 0 for k in shared_chrom.keys()}
        orthogonal = _make_scored(chromosome=zero_chrom, reward=0.4, sid="ortho_1")

        kept = pool.diversity_filter([clone, orthogonal])
        kept_ids = {s.id for s in kept}
        assert "clone_1" not in kept_ids, "near-identical must be filtered out"
        assert "ortho_1" in kept_ids, "diverse candidate must survive"

    def test_diversity_filter_threshold_one_filters_only_identical(self, monkeypatch):
        """threshold=1.0 keeps everything except perfectly identical vectors.

        Confirms the strict-less-than contract: ``kept iff max_sim < threshold``.
        With cosine=1.0 for clones, the only filtered candidate is the exact
        clone of the seed; orthogonal/zero-vector candidates survive because
        0.0 < 1.0.
        """
        import numpy as np

        def _vec(strategy):
            c = strategy.chromosome if hasattr(strategy, "chromosome") else {}
            vals = []
            for k in sorted(c.keys()):
                v = c[k]
                if isinstance(v, bool):
                    vals.append(1.0 if v else 0.0)
                elif isinstance(v, (int, float)):
                    vals.append(float(v))
                else:
                    vals.append(0.0)
            return np.array(vals, dtype=np.float64)

        monkeypatch.setattr(StrategyPool, "_chrom_to_vec", staticmethod(_vec))

        # Use a strictly-numerical chromosome so cosine == 1.0 exactly
        # (no float-rounding fuzz from bool→float conversion).
        shared_chrom = random_chromosome()
        pool = StrategyPool(max_size=10, diversity_threshold=1.0)
        seed = _make_scored(chromosome=shared_chrom, reward=1.0, sid="seed_1")
        pool.add(seed)

        clone = _make_scored(chromosome=dict(shared_chrom), reward=0.5, sid="clone_1")
        # ortho: numerical chromosome far from seed (no zero-vector / NaN)
        ortho_chrom = {
            k: (v * 100 + 17) if isinstance(v, (int, float)) else v
            for k, v in shared_chrom.items()
        }
        ortho = _make_scored(chromosome=ortho_chrom, reward=0.4, sid="ortho_1")
        kept = pool.diversity_filter([clone, ortho])
        kept_ids = {s.id for s in kept}
        assert (
            "clone_1" not in kept_ids
        ), "exact clone (cos==1.0) must be filtered at threshold=1.0"
        assert (
            "ortho_1" in kept_ids
        ), "non-identical vector must survive (cos < 1.0 ⇒ kept)"

    def test_diversity_filter_strict_inequality_filters_identical_vectors(
        self, monkeypatch
    ):
        """``if max_sim < threshold`` ⇒ identical vectors are always filtered
        (cos=1.0 < threshold is False for any threshold ≤ 1.0).

        We construct two numerical-only chromosomes so cosine math is
        predictable (no string-gene noise from ``random_chromosome``).
        """
        import numpy as np

        def _vec(strategy):
            c = strategy.chromosome if hasattr(strategy, "chromosome") else {}
            vals = []
            for v in c.values():
                if isinstance(v, (int, float)):
                    vals.append(float(v))
                else:
                    vals.append(0.0)
            return np.array(vals, dtype=np.float64)

        monkeypatch.setattr(StrategyPool, "_chrom_to_vec", staticmethod(_vec))

        # Seed: numerical-only chromosome.
        seed_chrom = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
        clone_chrom = dict(seed_chrom)
        diverse_chrom = {"a": -1.0, "b": -2.0, "c": -3.0, "d": -4.0}
        # diverse is anti-parallel to seed → cosine == -1.0, which becomes 0.0
        # in the cosine similarity (the dot-product formula clamps negatives to
        # the magnitude of the negative vector); max_sim < threshold (0.5) is
        # True → candidate kept.

        pool = StrategyPool(max_size=10, diversity_threshold=0.5)
        pool.add(_make_stub_scored(seed_chrom, "seed_1", reward=1.0))

        clone = _make_stub_scored(clone_chrom, "clone_1", reward=0.5)
        diverse = _make_stub_scored(diverse_chrom, "diverse_1", reward=0.5)

        kept = pool.diversity_filter([clone, diverse])
        kept_ids = {s.id for s in kept}
        assert "clone_1" not in kept_ids, "identical vector must be filtered (cos=1.0)"
        assert "diverse_1" in kept_ids, "anti-parallel vector must survive"

    def test_diversity_filter_passes_through_when_pool_is_empty(self):
        """Empty pool ⇒ no comparison baseline ⇒ every candidate passes."""
        pool = StrategyPool(max_size=10)
        candidates = [_make_scored(reward=0.5, sid=f"cand_{i}") for i in range(2)]
        kept = pool.diversity_filter(candidates)
        assert len(kept) == 2

    def test_diversity_filter_passes_through_when_strategy_lacks_chromosome(self):
        """A candidate whose strategy has no ``chromosome`` attr bypasses the
        similarity check and is always kept."""
        pool = StrategyPool(max_size=10, diversity_threshold=0.7)
        seed = _make_scored(reward=1.0, sid="seed_1")
        pool.add(seed)

        class BareStrategy:
            """Strategy without a ``chromosome`` attribute."""

        bare_eval = EvaluationResult.fail()
        bare_scored = ScoredStrategy(
            strategy=BareStrategy(),
            reward=0.5,
            evaluation=bare_eval,
            generation=1,
            parent_ids=(),
            id="bare_1",
        )
        kept = pool.diversity_filter([bare_scored])
        assert len(kept) == 1
        assert kept[0].id == "bare_1"

    def test_force_inject_random_grows_pool(self):
        """``force_inject_random`` must add at least ``max_size // 4`` strategies."""
        pool = StrategyPool(max_size=12)
        # Seed the pool with one strategy to verify injection respects caps.
        pool.add(_make_scored(reward=1.0, sid="anchor_1"))

        injected = pool.force_inject_random()
        assert injected >= 3  # max(5, 12 // 4) = 5
        assert len(pool) == injected + 1
        # Injected strategies have reward 0.0, so the anchor must still rank
        # at the top after re-sort.
        top = pool.top_k(1)
        assert top[0].id == "anchor_1"


# ── 2. Persistence: scored strategies + versions ────────────────────────────


@pytest.mark.unit
class TestPersistenceScoredAndVersions:
    """Round-trip a single scored strategy and exercise the version API."""

    def _per_session_cleanup(self, session_id: str):
        for suffix in ("_meta.json", "_strategies.json", "_evolution.json"):
            p = SESSIONS / f"{session_id}{suffix}"
            if p.exists():
                p.unlink()

    def _per_version_cleanup(self, tag: str):
        _purge([VERSIONS / f"v_{tag}", VERSIONS / "versions_index.json"])

    def test_save_and_load_scored_strategy_round_trip(self):
        """Saving then loading a ScoredStrategy must preserve its core fields."""
        session_id = f"unit_scored_{uuid.uuid4().hex[:10]}"
        self._per_session_cleanup(session_id)
        try:
            persistence = MetaRLPersistence()
            assert persistence.enabled

            scored = _make_scored(
                chromosome=random_chromosome(),
                reward=0.75,
                generation=3,
                sid=f"strat_{uuid.uuid4().hex[:8]}",
            )

            assert persistence.save_scored_strategy(scored, session_id) is True
            records = persistence.load_scored_strategies(session_id)

            assert len(records) == 1
            rec = records[0]
            assert rec["id"] == scored.id
            assert rec["session_id"] == session_id
            assert rec["generation"] == 3
            assert float(rec["reward"]) == pytest.approx(0.75)
            assert rec["risk_adjusted_pnl"] == pytest.approx(0.75 * 0.8)
            assert rec["sharpe"] == pytest.approx(0.75)
            assert rec["trades"] == int(10 * 0.75)
            # Chromosome round-trips intact (same keys, same float values).
            assert set(rec["chromosome"].keys()) == set(
                scored.strategy.chromosome.keys()
            )
            # Loader injects bookkeeping timestamps.
            assert "saved_at" in rec
        finally:
            self._per_session_cleanup(session_id)

    def test_load_scored_strategies_missing_session_returns_empty(self):
        """Loading a session that has no strategies file returns ``[]``."""
        persistence = MetaRLPersistence()
        session_id = f"unit_missing_{uuid.uuid4().hex[:10]}"
        assert persistence.load_scored_strategies(session_id) == []

    def test_save_version_load_version_list_compare(self):
        """Versioned elites must round-trip and ``compare_versions`` must pick
        the version with higher mean reward as the winner."""
        persistence = MetaRLPersistence()
        tags = _make_unique_ids("unit_ver", n=2)
        self._per_version_cleanup(tags[0])
        self._per_version_cleanup(tags[1])
        try:
            # Version A: weaker pool (mean reward 0.3).
            weak_pool = [_make_scored(reward=0.2, sid=f"a_{i}") for i in range(3)] + [
                _make_scored(reward=0.4, sid=f"a_3")
            ]
            assert persistence.save_version(weak_pool, tags[0]) is True

            # Version B: stronger pool (mean reward 0.8).
            strong_pool = [_make_scored(reward=0.7, sid=f"b_{i}") for i in range(3)] + [
                _make_scored(reward=1.0, sid=f"b_3")
            ]
            assert persistence.save_version(strong_pool, tags[1]) is True

            # Both versions are listed in the index.
            listed = persistence.list_versions()
            for t in tags:
                assert t in listed

            # Each version reloads with the expected record count.
            loaded_a = persistence.load_version(tags[0])
            loaded_b = persistence.load_version(tags[1])
            assert len(loaded_a) == 4
            assert len(loaded_b) == 4

            # compare_versions picks B as the winner (higher mean reward).
            cmp_result = persistence.compare_versions(tags[0], tags[1])
            assert cmp_result["a"] == tags[0]
            assert cmp_result["b"] == tags[1]
            assert cmp_result["a_count"] == 4
            assert cmp_result["b_count"] == 4
            assert cmp_result["winner"] == tags[1]
            assert cmp_result["b_mean"] > cmp_result["a_mean"]
        finally:
            for t in tags:
                self._per_version_cleanup(t)

    def test_compare_versions_unknown_returns_error(self):
        """Comparing against a non-existent version yields an error payload."""
        persistence = MetaRLPersistence()
        existing = f"unit_ver_known_{uuid.uuid4().hex[:8]}"
        self._per_version_cleanup(existing)
        try:
            assert (
                persistence.save_version(
                    [_make_scored(reward=0.5, sid="only_1")], existing
                )
                is True
            )
            result = persistence.compare_versions(existing, "no_such_tag")
            assert result.get("error") == "version not found"
            assert result["a"] == existing
            assert result["b"] == "no_such_tag"
        finally:
            self._per_version_cleanup(existing)

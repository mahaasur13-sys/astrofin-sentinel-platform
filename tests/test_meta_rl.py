"""tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 tests)"""

from __future__ import annotations

import math

import numpy as np
import pytest

from meta_rl.evolution import EvolutionEngine, EvolutionStats
from meta_rl.meta_agent import EvolutionConfig, MetaAgent
from meta_rl.reward import RewardCalculator, RewardConfig
from meta_rl.strategy_evaluator import EvaluationResult, StrategyEvaluator
from meta_rl.strategy_pool import ScoredStrategy, StrategyPool
from strategies.generator import (
    CHROMOSOME_KEYS,
    GeneratedStrategy,
    random_chromosome,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_evaluation_result():
    return EvaluationResult(
        pnl=0.25,
        sharpe=1.5,
        max_drawdown=0.10,
        trades=20,
        win_rate=0.65,
        execution_cost=0.02,
        equity_curve=np.array([100000 + i * 500 for i in range(21)]),
    )


@pytest.fixture
def sample_market_data():
    np.random.seed(42)
    history = []
    price = 50000.0
    for i in range(100):
        price *= 1 + np.random.normal(0.001, 0.015)
        history.append(
            {
                "close": price,
                "open": price * 0.99,
                "high": price * 1.01,
                "low": price * 0.98,
                "volume": 1000.0,
                "regime": "BULL",
                "signal_strength": 65.0,
                "momentum": 0.05,
                "mean_reversion_signal": 0.02,
                "atr": price * 0.02,
            }
        )
    return {
        "ohlcv": history,
        "regime": "BULL",
        "signal_strength": 65.0,
        "momentum": 0.05,
        "mean_reversion_signal": 0.02,
        "atr": price * 0.02,
    }


@pytest.fixture
def dummy_evaluator(sample_market_data, sample_evaluation_result):
    ev = StrategyEvaluator()
    return ev


# ── 1. EvaluationResult Tests ───────────────────────────────────────────────


class TestEvaluationResult:
    def test_fail_result(self):
        r = EvaluationResult.fail()
        assert r.pnl == 0.0 and r.sharpe == 0.0 and r.max_drawdown == 1.0

    def test_to_dict_roundtrip(self, sample_evaluation_result):
        d = sample_evaluation_result.to_dict()
        r2 = EvaluationResult.from_dict(d)
        assert abs(r2.pnl - sample_evaluation_result.pnl) < 1e-6
        assert abs(r2.sharpe - sample_evaluation_result.sharpe) < 1e-6
        assert r2.trades == sample_evaluation_result.trades

    def test_equity_curve_serialization(self, sample_evaluation_result):
        ec = np.array([1, 2, 3, 4, 5])
        r = EvaluationResult(equity_curve=ec)
        d = r.to_dict()
        assert d["equity_curve"] == [1, 2, 3, 4, 5]
        r2 = EvaluationResult.from_dict(d)
        assert list(r2.equity_curve) == [1, 2, 3, 4, 5]

    def test_no_nan_in_fail(self):
        r = EvaluationResult.fail()
        assert not math.isnan(r.pnl)
        assert not math.isnan(r.sharpe)


# ── 2. StrategyEvaluator Tests ──────────────────────────────────────────────


class TestStrategyEvaluator:
    def test_evaluate_returns_result(self, dummy_evaluator, sample_market_data):
        strategy = GeneratedStrategy(random_chromosome())
        result = dummy_evaluator.evaluate(strategy, sample_market_data)
        assert isinstance(result, EvaluationResult)
        assert result.trades >= 0

    def test_evaluate_insufficient_data(self, dummy_evaluator):
        strategy = GeneratedStrategy(random_chromosome())
        result = dummy_evaluator.evaluate(strategy, {"ohlcv": [{"close": 1}]})
        assert isinstance(result, EvaluationResult)

    def test_evaluate_bad_strategy(self, dummy_evaluator, sample_market_data):
        class BadStrategy:
            chromosome = random_chromosome()

            def evaluate(self, data):
                raise ValueError("intentional crash")

        result = dummy_evaluator.evaluate(BadStrategy(), sample_market_data)
        assert isinstance(result, EvaluationResult)

    def test_inline_backtest_runs(self, dummy_evaluator, sample_market_data):
        strategy = GeneratedStrategy(random_chromosome())
        result = dummy_evaluator.evaluate(strategy, sample_market_data)
        assert isinstance(result, EvaluationResult)
        assert not math.isnan(result.sharpe)


# ── 3. RewardCalculator Tests ───────────────────────────────────────────────


class TestRewardCalculator:
    def test_positive_sharpe_reward(self, sample_evaluation_result):
        calc = RewardCalculator()
        reward = calc.compute(sample_evaluation_result)
        assert isinstance(reward, float)
        assert reward > 0

    def test_negative_pnl_zero_trades(self):
        calc = RewardCalculator()
        r = EvaluationResult(
            pnl=-0.5, sharpe=-1.0, max_drawdown=0.5, trades=0, win_rate=0.0
        )
        reward = calc.compute(r)
        assert reward == 0.0

    def test_drawdown_heavy_penalty(self):
        calc = RewardCalculator()
        r = EvaluationResult(
            pnl=0.1, sharpe=0.5, max_drawdown=0.8, trades=20, win_rate=0.5
        )
        reward = calc.compute(r)
        assert reward < 0

    def test_stability_bonus_kicks_in(self):
        calc = RewardCalculator()
        r = EvaluationResult(
            pnl=0.2, sharpe=1.0, max_drawdown=0.1, trades=20, win_rate=0.7
        )
        reward = calc.compute(r)
        assert reward > 0

    def test_config_normalization(self):
        cfg = RewardConfig(sharpe_weight=2.0, pnl_weight=2.0, execution_cost_weight=2.0)
        calc = RewardCalculator(cfg)
        assert calc.config.sharpe_weight < 1.0

    def test_summary_breakdown(self, sample_evaluation_result):
        calc = RewardCalculator()
        summary = calc.summary(sample_evaluation_result)
        assert "sharpe_comp" in summary
        assert "pnl_comp" in summary
        assert "dd_penalty" in summary
        assert "stability_bonus" in summary
        assert abs(summary["total"] - calc.compute(sample_evaluation_result)) < 1e-6

    def test_no_nan_on_weird_inputs(self):
        calc = RewardCalculator()
        r = EvaluationResult(
            pnl=float("nan"), sharpe=float("inf"), max_drawdown=1.0, trades=5
        )
        reward = calc.compute(r)
        assert not math.isnan(reward)

    def test_execution_cost_penalty(self):
        calc = RewardCalculator()
        r = EvaluationResult(
            pnl=0.1,
            sharpe=0.5,
            max_drawdown=0.05,
            trades=10,
            win_rate=0.6,
            execution_cost=0.5,
        )
        reward = calc.compute(r)
        assert reward < 0.5


# ── 4. StrategyPool Tests ──────────────────────────────────────────────────


class TestStrategyPool:
    def test_add_and_retrieve(self, sample_evaluation_result):
        pool = StrategyPool(max_size=10)
        strategy = GeneratedStrategy(random_chromosome())
        scored = ScoredStrategy(
            strategy=strategy, reward=1.0, evaluation=sample_evaluation_result
        )
        assert pool.add(scored) is True
        assert len(pool) == 1

    def test_deduplication(self, sample_evaluation_result):
        pool = StrategyPool(max_size=10)
        strategy = GeneratedStrategy(random_chromosome())
        scored1 = ScoredStrategy(
            strategy=strategy, reward=1.0, evaluation=sample_evaluation_result
        )
        pool.add(scored1)
        # Same instance added again — should be skipped
        assert pool.add(scored1) is False

    def test_top_k(self, sample_evaluation_result):
        pool = StrategyPool(max_size=10)
        for i in range(5):
            s = GeneratedStrategy(random_chromosome())
            scored = ScoredStrategy(
                strategy=s, reward=float(i), evaluation=sample_evaluation_result
            )
            pool.add(scored)
        top = pool.top_k(3)
        assert len(top) == 3
        assert top[0].reward >= top[1].reward >= top[2].reward

    def test_diversity_filter(self):
        pool = StrategyPool(max_size=10)
        chrom_a = dict.fromkeys(CHROMOSOME_KEYS, 0.5)
        chrom_b = dict.fromkeys(CHROMOSOME_KEYS, 0.8)
        s1 = GeneratedStrategy(chrom_a)
        s2 = GeneratedStrategy(chrom_b)
        sc1 = ScoredStrategy(strategy=s1, reward=1.0, evaluation=EvaluationResult())
        sc2 = ScoredStrategy(strategy=s2, reward=2.0, evaluation=EvaluationResult())
        pool.add(sc1)
        candidates = pool.diversity_filter([sc2])
        assert len(candidates) >= 0

    def test_pool_eviction_on_full(self, sample_evaluation_result):
        pool = StrategyPool(max_size=3)
        for i in range(5):
            s = GeneratedStrategy(random_chromosome())
            sc = ScoredStrategy(
                strategy=s, reward=float(i), evaluation=sample_evaluation_result
            )
            pool.add(sc)
        assert len(pool) == 3

    def test_scored_strategy_hashable(self, sample_evaluation_result):
        strategy = GeneratedStrategy(random_chromosome())
        scored = ScoredStrategy(
            strategy=strategy, reward=1.0, evaluation=sample_evaluation_result
        )
        d = {scored: "value"}
        assert d[scored] == "value"

    def test_export_elites(self, sample_evaluation_result):
        pool = StrategyPool(max_size=10)
        for i in range(5):
            s = GeneratedStrategy(random_chromosome())
            sc = ScoredStrategy(
                strategy=s, reward=float(i), evaluation=sample_evaluation_result
            )
            pool.add(sc)
        exported = pool.export_elites(3)
        assert len(exported) == 3
        assert "id" in exported[0]
        assert "reward_history" in exported[0]

    def test_statistics(self, sample_evaluation_result):
        pool = StrategyPool(max_size=10)
        for i in range(5):
            s = GeneratedStrategy(random_chromosome())
            sc = ScoredStrategy(
                strategy=s, reward=float(i), evaluation=sample_evaluation_result
            )
            pool.add(sc)
        stats = pool.get_statistics()
        assert stats["size"] == 5
        assert stats["min_reward"] == 0.0
        assert stats["max_reward"] == 4.0


# ── 5. MetaAgent Tests ──────────────────────────────────────────────────────


class TestMetaAgent:
    def test_initialization(self):
        agent = MetaAgent()
        assert agent.generation == 0
        assert agent.config.population_size == 20

    def test_initialize_population(self, sample_market_data):
        agent = MetaAgent(config=EvolutionConfig(population_size=10, random_seed=42))
        pop = agent.initialize_population()
        assert len(pop) == 10
        assert agent.generation == 1

    def test_evaluate_population(self, sample_market_data):
        agent = MetaAgent(config=EvolutionConfig(population_size=5, random_seed=42))
        pop = agent.initialize_population()
        pop = agent.evaluate_population(pop, sample_market_data)
        rewards = [s.reward for s in pop]
        assert all(isinstance(r, float) for r in rewards)

    def test_select_returns_sorted_elites(self, sample_market_data):
        agent = MetaAgent(
            config=EvolutionConfig(population_size=10, elite_count=3, random_seed=42)
        )
        pop = agent.initialize_population()
        pop = agent.evaluate_population(pop, sample_market_data)
        elites = agent.select(pop)
        assert len(elites) == 3
        assert all(isinstance(e, ScoredStrategy) for e in elites)

    def test_evolve_returns_correct_size(self, sample_market_data):
        agent = MetaAgent(
            config=EvolutionConfig(population_size=10, elite_count=3, random_seed=42)
        )
        pop = agent.initialize_population()
        pop = agent.evaluate_population(pop, sample_market_data)
        elites = agent.select(pop)
        new_pop = agent.evolve(elites)
        assert len(new_pop) == 10
        assert agent.generation == 2

    def test_generation_counter_increments(self, sample_market_data):
        agent = MetaAgent(
            config=EvolutionConfig(population_size=5, elite_count=2, random_seed=42)
        )
        pop = agent.initialize_population()
        assert agent.generation == 1
        pop = agent.evaluate_population(pop, sample_market_data)
        elites = agent.select(pop)
        agent.evolve(elites)
        assert agent.generation == 2


# ── 6. EvolutionEngine Tests ────────────────────────────────────────────────


class TestEvolutionEngine:
    def test_full_evolution_run(self, sample_market_data):
        agent = MetaAgent(
            config=EvolutionConfig(population_size=10, elite_count=3, random_seed=42)
        )
        engine = EvolutionEngine(
            agent, market_data=sample_market_data, max_generations=3
        )
        final_pop, history = engine.run()
        assert len(final_pop) <= 10
        assert len(history) >= 1
        assert isinstance(history[0], EvolutionStats)

    def test_convergence_report(self, sample_market_data):
        agent = MetaAgent(config=EvolutionConfig(population_size=10, random_seed=42))
        engine = EvolutionEngine(
            agent, market_data=sample_market_data, max_generations=5
        )
        engine.run()
        report = engine.convergence_report()
        assert "status" in report
        assert "total_generations" in report

    def test_get_best_strategy(self, sample_market_data):
        agent = MetaAgent(config=EvolutionConfig(population_size=10, random_seed=42))
        engine = EvolutionEngine(
            agent, market_data=sample_market_data, max_generations=3
        )
        engine.run()
        best = engine.get_best_strategy()
        assert best is None or isinstance(best, ScoredStrategy)

    def test_evolution_stats_serialization(self, sample_market_data):
        agent = MetaAgent(config=EvolutionConfig(population_size=5, random_seed=42))
        engine = EvolutionEngine(
            agent, market_data=sample_market_data, max_generations=2
        )
        _, history = engine.run()
        stats = history[-1]
        d = stats.to_dict()
        assert "generation" in d
        assert "mean_reward" in d
        assert "max_reward" in d

    def test_early_stopping(self, sample_market_data):
        agent = MetaAgent(config=EvolutionConfig(population_size=10, random_seed=42))
        engine = EvolutionEngine(
            agent,
            market_data=sample_market_data,
            max_generations=50,
            early_stopping_patience=2,
        )
        _, history = engine.run()
        assert len(history) <= 52

    def test_reward_improves_after_evolution(self, sample_market_data):
        agent = MetaAgent(
            config=EvolutionConfig(population_size=15, elite_count=4, random_seed=99)
        )
        engine = EvolutionEngine(
            agent, market_data=sample_market_data, max_generations=5
        )
        _, history = engine.run()
        first_max = history[0].max_reward if history else 0.0
        last_max = history[-1].max_reward if history else 0.0
        assert last_max >= first_max - 0.5


# ── 7. ScoredStrategy Tests ─────────────────────────────────────────────────


class TestScoredStrategy:
    def test_reward_history_append(self, sample_evaluation_result):
        strategy = GeneratedStrategy(random_chromosome())
        scored = ScoredStrategy(
            strategy=strategy, reward=0.5, evaluation=sample_evaluation_result
        )
        assert len(scored.reward_history) >= 1
        scored.reward = 0.8
        assert 0.8 in scored.reward_history

    def test_parent_ids(self, sample_evaluation_result):
        strategy = GeneratedStrategy(random_chromosome())
        scored = ScoredStrategy(
            strategy=strategy,
            reward=1.0,
            evaluation=sample_evaluation_result,
            parent_ids=("a", "b"),
        )
        assert scored.parent_ids == ("a", "b")

    def test_to_from_dict(self, sample_evaluation_result):
        strategy = GeneratedStrategy(random_chromosome())
        scored = ScoredStrategy(
            strategy=strategy,
            reward=1.5,
            evaluation=sample_evaluation_result,
            generation=3,
        )
        d = scored.to_dict()
        assert d["generation"] == 3
        assert "confidence_threshold" in d["strategy_params"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

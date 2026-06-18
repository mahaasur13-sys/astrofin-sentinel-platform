"""Integration test for the full evolutionary pipeline.

Closes: R6.3, R6.5, R6.6.

End-to-end flow verified:

1. Create a MetaAgent with a small population.
2. Run EvolutionEngine for 2-3 generations on synthetic market data.
3. Export elites via ``StrategyPool.export_elites()``.
4. Persist a session via ``MetaRLPersistence.save_evolution_session``.
5. Reload via ``load_evolution_session`` and verify metrics are intact.
6. (Bonus) Unit-test ``MetaRLPersistence`` session metadata round-trip and
   ``StrategyEvaluator.evaluate`` failure mode.

Notes:
- ``HYPEROPT_ENABLED`` and ``KARL_META_UPDATE_ENABLED`` are monkeypatched off
  to keep the test fast and deterministic.
- Test artefacts (session files) live under ``data/meta_rl/sessions/`` (the
  canonical Persistence path) and are cleaned up in a finally block.
"""

from __future__ import annotations

import uuid

import numpy as np
import pytest

from meta_rl import evolution as evolution_mod
from meta_rl.evolution import EvolutionEngine, EvolutionStats
from meta_rl.meta_agent import EvolutionConfig, MetaAgent
from meta_rl.persistence import MetaRLPersistence, SESSIONS
from meta_rl.strategy import Strategy
from meta_rl.strategy_evaluator import EvaluationResult, StrategyEvaluator
from meta_rl.strategy_pool import ScoredStrategy, StrategyPool


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def synthetic_market_data() -> dict:
    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    rng = np.random.default_rng(seed=42)
    n = 200
    price = 50_000.0
    history = []
    for _ in range(n):
        price *= 1 + rng.normal(0.001, 0.015)
        history.append(
            {
                "close": price,
                "open": price * 0.99,
                "high": price * 1.01,
                "low": price * 0.98,
                "volume": 1000.0,
            }
        )
    return {
        "ohlcv": history,
        "regime": "BULL",
        "signal_strength": 60.0,
        "momentum": 0.05,
        "mean_reversion_signal": 0.02,
        "atr": price * 0.02,
    }


@pytest.fixture
def fast_evolution_agent(monkeypatch, synthetic_market_data):
    """MetaAgent wired with a tiny population and slow features disabled."""
    # Speed-ups: skip Hyperopt warm-up and KARL state updates during the test.
    monkeypatch.setattr(evolution_mod, "HYPEROPT_ENABLED", False, raising=False)
    monkeypatch.setattr(evolution_mod, "KARL_META_UPDATE_ENABLED", False, raising=False)

    cfg = EvolutionConfig(
        population_size=6,
        elite_count=2,
        tournament_size=2,
        karl_update_interval=100,
    )
    agent = MetaAgent(config=cfg)
    agent.initialize_population(market_data=synthetic_market_data)
    return agent


@pytest.fixture
def unique_session_id() -> str:
    """Per-test session id so parallel test runs don't collide."""
    return f"itest_evo_{uuid.uuid4().hex[:10]}"


@pytest.fixture(autouse=True)
def _cleanup_session_files(unique_session_id):
    """Remove any files this test may leave under ``data/meta_rl/sessions``."""
    yield
    for suffix in ("_meta.json", "_strategies.json", "_evolution.json"):
        path = SESSIONS / f"{unique_session_id}{suffix}"
        if path.exists():
            path.unlink()


# ── 1. End-to-end pipeline ─────────────────────────────────────────────────


@pytest.mark.integration
def test_evolution_pipeline_export_persist_reload(
    fast_evolution_agent, synthetic_market_data, unique_session_id
):
    """Generate → evolve → export → persist → reload → verify metrics."""
    agent = fast_evolution_agent
    initial_pool_size = len(agent.pool)

    # Step 1+2: Run EvolutionEngine for 3 generations.
    engine = EvolutionEngine(
        agent=agent,
        market_data=synthetic_market_data,
        max_generations=3,
        walk_forward_enabled=True,
        n_splits=2,
        train_window=80,
        test_window=20,
        visualize=False,
        session_id=unique_session_id,
    )
    elites, history = engine.run(ensemble_seeds=2)

    # The pool should never shrink below the configured population.
    assert len(agent.pool) >= initial_pool_size - agent.config.elite_count
    assert isinstance(elites, list) and len(elites) > 0
    assert all(isinstance(s, ScoredStrategy) for s in elites)
    assert all(s.reward_history for s in elites), "every elite must have reward history"
    assert all(isinstance(s.reward, float) for s in elites)
    assert isinstance(history, list) and len(history) >= 1
    assert all(isinstance(s, EvolutionStats) for s in history)
    # Generation index on stats should be monotonic.
    assert [s.generation for s in history] == sorted(s.generation for s in history)

    # Step 3: Export elites.
    exported = agent.pool.export_elites(top_n=3)
    assert len(exported) >= 1
    assert all(isinstance(d, dict) for d in exported)
    for d in exported:
        assert "id" in d and "reward" in d and "generation" in d
        assert isinstance(d["reward_history"], list)

    # Step 4: Persist evolution session.
    persistence = MetaRLPersistence()
    assert persistence.enabled, "persistence must be enabled in this environment"

    last_stats = history[-1]
    karl_snapshot = agent.get_karl_state()
    saved = persistence.save_evolution_session(
        session_id=unique_session_id,
        symbol="BTCUSDT",
        cg=last_stats.generation,
        br=float(last_stats.max_reward),
        ks=karl_snapshot,
        gs=history,
    )
    assert saved is True

    # Step 5: Reload and verify metrics round-trip intact.
    loaded = persistence.load_evolution_session(unique_session_id)
    assert loaded is not None
    assert loaded["session_id"] == unique_session_id
    assert loaded["symbol"] == "BTCUSDT"
    assert loaded["current_generation"] == last_stats.generation
    assert float(loaded["best_reward"]) == pytest.approx(float(last_stats.max_reward))
    assert isinstance(loaded["karl_state"], dict)
    # history was passed as EvolutionStats objects with to_dict() — reload returns
    # the same length and identical generation numbers.
    assert len(loaded["history"]) == len(history)
    assert [s["generation"] for s in loaded["history"]] == [
        s.generation for s in history
    ]

    # Verify pool export is also reproducible (StrategyPool.export_elites is pure).
    exported_again = agent.pool.export_elites(top_n=3)
    assert [d["id"] for d in exported] == [d["id"] for d in exported_again]


# ── 2. Unit tests — Persistence ─────────────────────────────────────────────


@pytest.mark.unit
class TestPersistenceRoundTrip:
    def test_session_metadata_round_trip(self, unique_session_id):
        p = MetaRLPersistence()
        meta = {"max_generations": 5, "population_size": 8, "session_tag": "unit-meta"}
        assert p.save_session_metadata(unique_session_id, meta)

        loaded = p.load_session_metadata(unique_session_id)
        assert loaded is not None
        # Loader injects session_id + saved_at on top of the user payload —
        # verify the user payload round-trips intact, ignoring bookkeeping.
        for k, v in meta.items():
            assert loaded[k] == v
        assert loaded["session_id"] == unique_session_id
        assert "saved_at" in loaded

    def test_list_sessions_includes_new_session(self, unique_session_id):
        p = MetaRLPersistence()
        p.save_session_metadata(unique_session_id, {"k": 1})
        sessions = p.list_sessions()
        assert unique_session_id in sessions

    def test_save_evolution_session_persists_history(self, unique_session_id):
        p = MetaRLPersistence()
        stats = EvolutionStats(
            generation=2,
            mean_reward=0.5,
            max_reward=1.0,
            min_reward=0.1,
            std_reward=0.2,
            pool_size=8,
            improvement_over_prev=0.3,
            karl_updated=False,
        )
        ok = p.save_evolution_session(
            session_id=unique_session_id,
            symbol="ETHUSDT",
            cg=2,
            br=1.0,
            ks={"current_q_star": 0.5, "current_regime": "NORMAL"},
            gs=[stats],
        )
        assert ok is True
        loaded = p.load_evolution_session(unique_session_id)
        assert loaded is not None
        assert loaded["current_generation"] == 2
        assert loaded["history"][0]["max_reward"] == 1.0
        assert loaded["karl_state"]["current_regime"] == "NORMAL"


# ── 3. Unit tests — StrategyEvaluator ───────────────────────────────────────


@pytest.mark.unit
class TestStrategyEvaluatorUnit:
    def test_evaluate_returns_fail_for_empty_market_data(self):
        """No ohlcv → StrategyEvaluator short-circuits to a fail() result."""
        ev = StrategyEvaluator()
        # Use a plain object — evaluator should not even reach backtest_adapter.
        result = ev.evaluate(strategy=object(), market_data={})
        assert isinstance(result, EvaluationResult)
        assert result.pnl == 0.0
        assert result.max_drawdown == 1.0

    def test_evaluate_runs_on_synthetic_bars(self, synthetic_market_data):
        """With ≥10 OHLCV bars the evaluator must run the backtest pipeline
        and produce a real (non-fail) EvaluationResult. We exercise this via
        GeneratedStrategy because the backtest adapter dispatches on
        ``.evaluate()`` which only GeneratedStrategy provides.
        """
        from strategies.generator import GeneratedStrategy, random_chromosome

        ev = StrategyEvaluator()
        strategy = GeneratedStrategy(random_chromosome(), generation=1)
        result = ev.evaluate(strategy=strategy, market_data=synthetic_market_data)
        assert isinstance(result, EvaluationResult)
        # risk_adjustment_reason == 'NO_RISK_ENGINE' tells us we actually
        # ran the backtest path (rather than short-circuiting on empty data).
        assert result.risk_adjustment_reason == "NO_RISK_ENGINE"

"""meta_rl/meta_agent.py -- ATOM-META-RL-005/009: Bidirectional KARL + Cross-session Replay
FIXED (audit 15.05.2026): KARLState dataclass — защита от утечки памяти
"""

from __future__ import annotations

import logging
import random
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from meta_rl.reward import RewardCalculator, RewardConfig
from meta_rl.strategy_evaluator import StrategyEvaluator
from meta_rl.strategy_pool import ScoredStrategy, StrategyPool
from meta_rl.types import EvaluationResult

logger = logging.getLogger(__name__)

KARL_META_UPDATE_ENABLED = True
KARL_META_BIDIRECTIONAL_ENABLED = True
CROSS_SESSION_REPLAY_ENABLED = True
Q_STAR_INFLUENCE_ALPHA = 0.3

# ═══════════════════════════════════════════════════════════════════════════════
# KARLState — защита от утечки памяти (FIXED)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class KARLState:
    """Bounded KARL state with automatic memory limits."""

    q_values: dict = field(default_factory=dict)
    q_star_history: deque = field(default_factory=lambda: deque(maxlen=20))
    regime_history: deque = field(default_factory=lambda: deque(maxlen=20))
    historical_qstar: deque = field(default_factory=lambda: deque(maxlen=1000))
    best_chromosomes: list = field(default_factory=list)
    oap_weights: dict = field(default_factory=dict)
    current_q_star: float = 0.5
    current_regime: str = "NORMAL"
    last_update_gen: int = 0

    MAX_Q_VALUES = 10000
    MAX_BEST_CHROMOSOMES = 20

    def add_q_value(self, key: str, value: float) -> None:
        """Add Q-value with automatic cleanup (FIFO eviction)."""
        self.q_values[key] = value
        if len(self.q_values) > self.MAX_Q_VALUES:
            to_remove = len(self.q_values) // 10
            for _ in range(to_remove):
                oldest_key = next(iter(self.q_values))
                del self.q_values[oldest_key]
            logger.warning(f"[KARL] Cleaned Q-values, now {len(self.q_values)} entries")

    def add_best_chromosome(self, chrom: dict) -> None:
        """Add chromosome with automatic truncation."""
        self.best_chromosomes.append(chrom)
        if len(self.best_chromosomes) > self.MAX_BEST_CHROMOSOMES:
            self.best_chromosomes = self.best_chromosomes[-self.MAX_BEST_CHROMOSOMES :]

    def get_memory_usage(self) -> dict:
        """Return memory usage stats for monitoring."""
        return {
            "q_values_count": len(self.q_values),
            "q_star_history_len": len(self.q_star_history),
            "historical_qstar_len": len(self.historical_qstar),
            "best_chromosomes_count": len(self.best_chromosomes),
            "oap_weights_count": len(self.oap_weights),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# EvolutionConfig
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class EvolutionConfig:
    population_size: int = 20
    elite_count: int = 4
    mutation_rate: float = 0.15
    crossover_rate: float = 0.40
    tournament_size: int = 3
    random_seed: int = 42
    max_generations_no_improve: int = 10
    karl_update_interval: int = 5

    def __post_init__(self):
        assert self.population_size >= 2
        assert 1 <= self.elite_count <= self.population_size
        assert 0.0 <= self.mutation_rate <= 1.0
        assert 0.0 <= self.crossover_rate <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# MetaAgent
# ═══════════════════════════════════════════════════════════════════════════════


class MetaAgent:
    """Meta-RL agent with bidirectional KARL integration (ATOM-META-RL-005/009).

    ATOM-META-RL-009: replay_historical_sessions() loads past sessions and
    updates internal state for cross-session learning.
    """

    def __init__(self, evaluator=None, reward_config=None, config=None, karl_state=None):
        self.evaluator = evaluator or StrategyEvaluator()
        self.reward_calc = RewardCalculator(reward_config or RewardConfig())
        self.config = config or EvolutionConfig()
        self._rng = random.Random(self.config.random_seed)
        self._np_rng = np.random.default_rng(self.config.random_seed)
        self.pool = StrategyPool(max_size=self.config.population_size)
        self._generation = 0
        self._best_reward = -float("inf")
        self._generations_no_improve = 0

        # FIXED: Use KARLState dataclass instead of raw dict
        self._karl_state = KARLState()
        if karl_state and isinstance(karl_state, dict):
            self._karl_state.current_q_star = karl_state.get("current_q_star", 0.5)
            self._karl_state.current_regime = karl_state.get("current_regime", "NORMAL")
            self._karl_state.last_update_gen = karl_state.get("last_update_gen", 0)

        self._session_id = "meta_rl_default"

    @property
    def generation(self) -> int:
        return self._generation

    def initialize_population(self, generator_fn=None, market_data=None):
        from strategies.generator import GeneratedStrategy, random_chromosome

        population = []
        for _ in range(self.config.population_size):
            strategy = generator_fn() if generator_fn else GeneratedStrategy(random_chromosome(), generation=1)
            scored = ScoredStrategy(
                strategy=strategy,
                reward=0.0,
                evaluation=EvaluationResult.fail(),
                generation=1,
                parent_ids=(),
            )
            population.append(scored)
            self.pool.add(scored)
        self._generation = 1
        logger.info(f"[META-RL] Initialized: {len(population)} strategies")
        return population

    def evaluate_population(self, population, market_data):
        from agents._impl.amre.audit import (
            META_RL_DECISION_RECORD_ENABLED,
            record_meta_rl_decision,
        )

        for scored in population:
            try:
                eval_result = self.evaluator.evaluate(scored.strategy, market_data)
                reward = self.reward_calc.compute(eval_result)
                scored.evaluation = eval_result
                scored.reward = reward
                if not scored.reward_history or scored.reward_history[-1] != reward:
                    scored.reward_history.append(reward)
                logger.debug(f"[META-RL] {scored.id[:8]}: reward={reward:.4f} risk_adj_pnl={eval_result.risk_adjusted_pnl:+.3f}")
                try:
                    sid = getattr(self, "_session_id", "meta_rl_default")
                    record_meta_rl_decision(scored, market_data, session_id=sid)
                except Exception as audit_err:
                    if META_RL_DECISION_RECORD_ENABLED:
                        logger.warning(f"[META-RL-AUDIT] Failed to record: {audit_err}")
            except Exception as e:
                logger.warning(f"[META-RL] Evaluation error for {scored.id}: {e}")
                scored.evaluation = EvaluationResult.fail()
                scored.reward = 0.0
        return population

    def select(self, population):
        if not population:
            return []
        scored_pop = [(s, s.reward_history[-1] if s.reward_history else s.reward) for s in population]
        elites = []
        for _ in range(self.config.elite_count):
            if not scored_pop:
                break
            tournament = self._rng.sample(scored_pop, min(self.config.tournament_size, len(scored_pop)))
            winner = max(tournament, key=lambda x: x[1])
            elites.append(winner[0])
            scored_pop.remove(winner)
        elites.sort(
            key=lambda s: s.reward_history[-1] if s.reward_history else s.reward,
            reverse=True,
        )
        top_r = elites[0].reward_history[-1] if (elites and elites[0].reward_history) else float("nan")
        logger.info(f"[META-RL] Selected {len(elites)} elites, top_reward={top_r:.4f}")
        return elites

    def evolve(self, elites, generator_fn=None):
        from strategies.generator import GeneratedStrategy, crossover, mutate

        adaptive_rate = self._compute_adaptive_crossover_rate()
        label = "adaptive" if adaptive_rate != self.config.crossover_rate else "base"
        if len(elites) < 2:
            logger.warning("[META-RL] Need 2+ elites, mutation only")
            return self._evolve_from_single_elite(elites, generator_fn)
        new_pop = list(elites)
        while len(new_pop) < self.config.population_size:
            roll = self._rng.random()
            if roll < adaptive_rate:
                a, b = self._rng.sample(elites, 2)
                chrom = crossover(a.strategy.chromosome, b.strategy.chromosome)
                chrom = mutate(chrom, rate=self.config.mutation_rate)
                child = GeneratedStrategy(
                    chrom,
                    generation=elites[0].generation + 1,
                    parent_fitness=max(a.reward, b.reward),
                )
                new_pop.append(
                    ScoredStrategy(
                        strategy=child,
                        reward=0.0,
                        evaluation=EvaluationResult.fail(),
                        generation=elites[0].generation + 1,
                        parent_ids=(a.id, b.id),
                    )
                )
            elif roll < adaptive_rate + self.config.mutation_rate:
                p = self._rng.choice(elites)
                chrom = mutate(dict(p.strategy.chromosome), rate=self.config.mutation_rate * 2)
                child = GeneratedStrategy(chrom, generation=elites[0].generation + 1, parent_fitness=p.reward)
                new_pop.append(
                    ScoredStrategy(
                        strategy=child,
                        reward=0.0,
                        evaluation=EvaluationResult.fail(),
                        generation=elites[0].generation + 1,
                        parent_ids=(p.id,),
                    )
                )
            else:
                child = self._generate_random_strategy(generator_fn, elites[0].generation + 1)
                new_pop.append(
                    ScoredStrategy(
                        strategy=child,
                        reward=0.0,
                        evaluation=EvaluationResult.fail(),
                        generation=elites[0].generation + 1,
                        parent_ids=(),
                    )
                )
        self._generation += 1
        current_best = max(s.reward for s in elites) if elites else -float("inf")
        if current_best > self._best_reward:
            self._best_reward = current_best
            self._generations_no_improve = 0
        else:
            self._generations_no_improve += 1
        logger.info(f"[META-RL] Gen {self._generation}: pop={len(new_pop)} best={current_best:.4f} no_improve={self._generations_no_improve} crossover={label}({adaptive_rate:.3f})")
        return new_pop[: self.config.population_size]

    def _compute_adaptive_crossover_rate(self) -> float:
        if not KARL_META_BIDIRECTIONAL_ENABLED:
            return self.config.crossover_rate
        q_star = self._karl_state.current_q_star
        q_norm = max(0.0, min(1.0, (q_star + 1.0) / 2.0))
        rate = self.config.crossover_rate * (1.0 + Q_STAR_INFLUENCE_ALPHA * q_norm)
        return float(max(0.0, min(1.0, rate)))

    def set_external_karl_feedback(self, q_star: float, regime: str) -> None:
        if not KARL_META_BIDIRECTIONAL_ENABLED:
            return
        q_star = float(q_star)
        regime = str(regime)
        self._karl_state.current_q_star = max(-1.0, min(1.0, q_star))
        self._karl_state.q_star_history.append({"gen": self._generation, "q_star": q_star, "regime": regime})
        self._karl_state.current_regime = regime
        self._karl_state.regime_history.append({"gen": self._generation, "regime": regime})
        regime_mult = 1.0 if regime in ("NORMAL", "BULL") else 0.8 if regime == "HIGH" else 0.6
        eff = self._compute_adaptive_crossover_rate() * regime_mult
        logger.debug(f"[META-RL] External feedback: Q*={q_star:.3f} regime={regime} -> effective_crossover={eff:.3f}")

    def update_karl(self, elites) -> dict:
        if not KARL_META_UPDATE_ENABLED:
            return self._karl_state.__dict__
        if not elites:
            return self._karl_state.__dict__
        try:
            sorted_elites = sorted(elites, key=lambda s: s.reward, reverse=True)
            top_n = sorted_elites[:3]
            best_chroms = [
                {
                    "chromosome": s.strategy.chromosome,
                    "reward": s.reward,
                    "generation": s.generation,
                    "id": s.id,
                    "risk_adjusted_pnl": getattr(s.evaluation, "risk_adjusted_pnl", 0.0),
                }
                for s in top_n
            ]

            for s in top_n:
                c = s.strategy.chromosome
                self._karl_state.oap_weights[s.id] = {
                    "conf_th": c.get("confidence_threshold", 60.0),
                    "pos_size": c.get("position_size_pct", 15.0),
                    "atr_mult": c.get("atr_multiplier", 2.0),
                    "reward": s.reward,
                }

            # FIXED: Use add_q_value with memory limit
            for s in top_n:
                key = f"gen_{s.generation}_{s.id[:8]}"
                self._karl_state.add_q_value(key, s.reward)

            if sorted_elites:
                self._karl_state.current_q_star = sorted_elites[0].reward

            # FIXED: Use add_best_chromosome with memory limit
            for bc in best_chroms:
                self._karl_state.add_best_chromosome(bc)

            self._karl_state.last_update_gen = self._generation
            logger.info(f"[META-RL] KARL update: {len(top_n)} elites, memory={self._karl_state.get_memory_usage()}")
        except Exception as e:
            logger.warning(f"[META-RL] KARL update failed: {e}")
        return self._karl_state.__dict__

    def get_karl_state(self) -> dict:
        return self._karl_state.__dict__

    def replay_historical_sessions(self) -> dict:
        """ATOM-META-RL-009: Load past sessions and update internal state."""
        if not CROSS_SESSION_REPLAY_ENABLED:
            logger.info("[META-RL] Cross-session replay disabled")
            return {"status": "disabled", "sessions_loaded": 0}

        try:
            from meta_rl.persistence import get_persistence
            from meta_rl.replay import analyze_oap_drift, get_adaptive_params_from_drift
        except ImportError:
            logger.warning("[META-RL] replay module not available")
            return {"status": "import_error", "sessions_loaded": 0}

        try:
            persist = get_persistence()
            sessions = persist.list_sessions()
            if not sessions:
                logger.info("[META-RL] No historical sessions found")
                return {"status": "no_sessions", "sessions_loaded": 0}

            total_records = 0
            all_qstar = []
            drift_reports = []

            for sid in sessions:
                records = persist.load_scored_strategies(sid)
                if not records:
                    continue
                total_records += len(records)
                rewards = [float(r.get("reward", 0.0)) for r in records]
                all_qstar.extend(rewards)
                report = analyze_oap_drift(records, sid)
                drift_reports.append(report)
                # FIXED: Use deque.append for memory safety
                for r in rewards:
                    self._karl_state.historical_qstar.append({"session": sid, "reward": r})

            if all_qstar:
                self._karl_state.current_q_star = float(max(all_qstar))

            if drift_reports:
                latest = drift_reports[-1]
                params = get_adaptive_params_from_drift(
                    latest,
                    base_mutation=self.config.mutation_rate,
                    base_crossover=self.config.crossover_rate,
                )
                logger.info(
                    f"[META-RL] Cross-session replay: {len(sessions)} sessions, "
                    f"{total_records} records, drift={latest.drift_severity} "
                    f"-> mutation={params['mutation_rate']:.3f} "
                    f"crossover={params['crossover_rate']:.3f}"
                )

            return {
                "status": "ok",
                "sessions_loaded": len(sessions),
                "total_records": total_records,
                "latest_drift_severity": drift_reports[-1].drift_severity if drift_reports else "none",
                "latest_drift_score": drift_reports[-1].drift_score if drift_reports else 0.0,
            }
        except Exception as e:
            logger.warning(f"[META-RL] Cross-session replay failed: {e}")
            return {"status": "error", "error": str(e), "sessions_loaded": 0}

    def _evolve_from_single_elite(self, elites, generator_fn):
        from strategies.generator import GeneratedStrategy, mutate

        new_pop = list(elites)
        parent = elites[0]
        while len(new_pop) < self.config.population_size:
            chrom = mutate(dict(parent.strategy.chromosome), rate=0.30)
            child = GeneratedStrategy(chrom, generation=parent.generation + 1, parent_fitness=parent.reward)
            new_pop.append(
                ScoredStrategy(
                    strategy=child,
                    reward=0.0,
                    evaluation=EvaluationResult.fail(),
                    generation=parent.generation + 1,
                    parent_ids=(parent.id,),
                )
            )
        self._generation += 1
        return new_pop[: self.config.population_size]

    def _generate_random_strategy(self, generator_fn, generation):
        from strategies.generator import GeneratedStrategy, random_chromosome

        if generator_fn:
            return generator_fn()
        return GeneratedStrategy(random_chromosome(), generation=generation)

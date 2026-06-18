"""meta_rl/evolution.py -- ATOM-META-RL-002/011"""

from __future__ import annotations

import logging
from meta_rl.config import HYPEROPT_ENABLED
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from meta_rl.config import (
    ALPHA_DECAY_DETECTION,
    ALPHA_DECAY_REWARD_DROP_PCT,
    ALPHA_DECAY_WINDOW_GENS,
    DECAY_KILL_THRESHOLD,
    MIN_DIVERSITY_POPULATION,
)
from meta_rl.meta_agent import KARL_META_UPDATE_ENABLED, MetaAgent
from meta_rl.persistence import get_persistence
from meta_rl.strategy_pool import ScoredStrategy
from meta_rl.metrics import (
    EVOLUTION_RUNS,
    GENERATION_CURRENT,
    BEST_REWARD,
    MEAN_REWARD,
    REWARD_STD,
    POPULATION_SIZE,
    STRATEGIES_CREATED,
    STRATEGIES_EVALUATED,
    STRATEGY_EVALUATED_TOTAL,
    GENERATIONS_TOTAL,
    GENERATION_DURATION,
)

logger = logging.getLogger(__name__)


@dataclass
class EvolutionStats:
    generation: int
    mean_reward: float
    max_reward: float
    min_reward: float
    std_reward: float
    pool_size: int
    improvement_over_prev: float
    top_strategy_id: str = ""
    elapsed_seconds: float = 0.0
    karl_updated: bool = False

    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "mean_reward": round(self.mean_reward, 4),
            "max_reward": round(self.max_reward, 4),
            "min_reward": round(self.min_reward, 4),
            "std_reward": round(self.std_reward, 4),
            "pool_size": self.pool_size,
            "improvement": round(self.improvement_over_prev, 4),
            "top_strategy_id": self.top_strategy_id,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "karl_updated": self.karl_updated,
        }


class EvolutionEngine:
    def __init__(
        self,
        agent: MetaAgent,
        market_data: dict[str, Any] | None = None,
        max_generations: int = 50,
        early_stopping_patience: int = 10,
        on_generation: Callable[[EvolutionStats], None] | None = None,
        walk_forward_enabled: bool = True,
        n_splits: int = 5,
        train_window: int = 100,
        test_window: int = 20,
        session_id: str | None = None,
        visualize: bool = True,
    ):
        self.agent = agent
        self.market_data = market_data or {}
        self.max_generations = max_generations
        self.early_stopping_patience = early_stopping_patience
        self.on_generation = on_generation
        self.walk_forward_enabled = walk_forward_enabled
        self.n_splits = n_splits
        self.train_window = train_window
        self.test_window = test_window
        self.visualize = visualize
        self._history: list[EvolutionStats] = []
        self._start_time: float = 0.0
        self._prev_best: float = -float("inf")
        self._karl_state_history: list[dict] = []
        self.session_id = session_id
        if self.session_id:
            self._load_session()

    @property
    def stats_history(self) -> list[EvolutionStats]:
        return list(self._history)

    def run(self, ensemble_seeds: int = 3) -> tuple[list[ScoredStrategy], list[EvolutionStats]]:
        logger.info(
            f"[META-RL-INTEGRATION] Starting: {self.max_generations} gens, "
            f"population={self.agent.config.population_size}, walk_forward={self.walk_forward_enabled}"
        )
        self._start_time = time.time()
        self._history = []
        self._prev_best = -float("inf")
        self._karl_state_history = []
        GENERATION_CURRENT.set(0)
        BEST_REWARD.set(0.0)

        # 1. Initialize
        EVOLUTION_RUNS.inc()
        # HyperOptimizer warm‑up (если включён)
        if HYPEROPT_ENABLED:
            from meta_rl.hyperopt import HyperOptimizer

            logger.info("[META-RL] HyperOptimizer warm‑up…")
            opt = HyperOptimizer(self.agent, self.market_data)
            best_params = opt.optimize(n_trials=10)
            logger.info(f"[META-RL] HyperOptimizer best params: {best_params}")
            # Применяем найденные параметры к конфигу агента
            self.agent.config.population_size = best_params.get("population_size", self.agent.config.population_size)
            self.agent.config.mutation_rate = best_params.get("mutation_rate", self.agent.config.mutation_rate)
            self.agent.config.crossover_rate = best_params.get("crossover_rate", self.agent.config.crossover_rate)

        population = self.agent.initialize_population()
        for scored in population:
            self.agent.pool.add(scored)
            STRATEGIES_CREATED.inc()

        # 2. Initial evaluation
        eval_market = self._get_walk_forward_data(generation=0)
        population = self.agent.evaluate_population(population, eval_market)
        for scored in population:
            STRATEGY_EVALUATED_TOTAL.inc()
        stats = self._compute_stats(population, karl_updated=False)
        self._history.append(stats)
        self._log_stats(stats)
        if self.on_generation:
            self.on_generation(stats)

        # 3. Evolution loop
        for gen_idx in range(1, self.max_generations + 1):
            try:
                GENERATIONS_TOTAL.inc()
                elites = self.agent.select(population)
                if self._should_stop(elites):
                    logger.info(f"[META-RL-INTEGRATION] Early stopping at gen {gen_idx}")
                    break

                karl_updated = False
                if KARL_META_UPDATE_ENABLED and gen_idx % self.agent.config.karl_update_interval == 0:
                    karl_state = self.agent.update_karl(elites)
                    self._karl_state_history.append(karl_state)
                    karl_updated = True

                population = self.agent.evolve(elites)
                eval_market = self._get_walk_forward_data(generation=gen_idx)
                population = self.agent.evaluate_population(population, eval_market)

                stats = self._compute_stats(population, karl_updated=karl_updated)
                stats.elapsed_seconds = time.time() - self._start_time
                self._history.append(stats)
                self._log_stats(stats)

                # ATOM-META-RL-007: Persist
                self._save_generation(elites)

                if self.on_generation:
                    self.on_generation(stats)
            except Exception as e:
                logger.warning(f"[META-RL-INTEGRATION] Gen {gen_idx} failed: {e}")
                continue

        # 4. Final selection
        final_elites = self.agent.select(population)
        self._final_elites = final_elites  # store for get_best_strategy()
        logger.info(
            f"[META-RL-INTEGRATION] Complete: {len(self._history)} gens, "
            f"best_reward={self._history[-1].max_reward if self._history else 'N/A':.4f}"
        )

        # ATOM-META-RL-011: Auto-visualization
        if self.visualize:
            self._generate_visualizations(final_elites)

        return final_elites, list(self._history)

    def _get_walk_forward_data(self, generation: int) -> dict:
        if not self.walk_forward_enabled:
            return self.market_data
        try:
            ohlcv = self.market_data.get("ohlcv", [])
            if len(ohlcv) < self.train_window + self.test_window:
                return self.market_data
            idx = (generation % self.n_splits) * self.test_window
            train_end = min(idx + self.train_window, len(ohlcv) - self.test_window)
            train_start = max(0, train_end - self.train_window)
            test_start = min(train_end, len(ohlcv) - self.test_window)
            test_end = min(test_start + self.test_window, len(ohlcv))
            train_data = ohlcv[train_start:train_end] if train_start < train_end else ohlcv[: self.train_window]
            wf = dict(self.market_data)
            wf["ohlcv"] = train_data
            wf["test_ohlcv"] = ohlcv[test_start:test_end] if test_start < test_end else ohlcv[-self.test_window :]
            return wf
        except Exception as e:
            logger.warning(f"[META-RL-INTEGRATION] Walk-forward failed: {e}")
            return self.market_data

    def _compute_stats(self, population: list[ScoredStrategy], karl_updated: bool = False) -> EvolutionStats:
        if not population:
            return EvolutionStats(
                generation=self.agent.generation,
                mean_reward=0.0,
                max_reward=0.0,
                min_reward=0.0,
                std_reward=0.0,
                pool_size=0,
                improvement_over_prev=0.0,
                karl_updated=karl_updated,
            )
        rewards = [s.reward_history[-1] if s.reward_history else s.reward for s in population]
        improvement = 0.0
        if self._history:
            prev_best = self._history[-1].max_reward
            improvement = max(rewards) - prev_best
        best_s = max(
            population,
            key=lambda s: s.reward_history[-1] if s.reward_history else s.reward,
        )
        mean_r = sum(rewards) / len(rewards)
        std_r = (sum((r - mean_r) ** 2 for r in rewards) / len(rewards)) ** 0.5 if len(rewards) > 1 else 0.0

        # Emit Prometheus metrics
        GENERATION_CURRENT.set(self.agent.generation)
        BEST_REWARD.set(float(max(rewards)))
        MEAN_REWARD.set(float(mean_r))
        REWARD_STD.set(float(std_r))
        POPULATION_SIZE.set(len(population))
        STRATEGIES_CREATED.inc(len(population))
        STRATEGIES_EVALUATED.inc(len(population))
        GENERATIONS_TOTAL.inc()
        GENERATION_DURATION.observe(time.time() - self._start_time)

        return EvolutionStats(
            generation=self.agent.generation,
            mean_reward=float(mean_r),
            max_reward=float(max(rewards)),
            min_reward=float(min(rewards)),
            std_reward=float(std_r),
            pool_size=len(population),
            improvement_over_prev=improvement,
            top_strategy_id=best_s.id,
            karl_updated=karl_updated,
        )

    def _should_stop(self, elites: list[ScoredStrategy]) -> bool:
        if not elites:
            return False
        current_best = max(s.reward for s in elites)
        if current_best > self._prev_best:
            self._prev_best = current_best
            self.agent._generations_no_improve = 0
        else:
            self.agent._generations_no_improve += 1

        # ATOM-META-RL-003: Alpha Decay detection — check kill signal
        if ALPHA_DECAY_DETECTION and len(self._history) >= ALPHA_DECAY_WINDOW_GENS:
            decay_signal = self._check_alpha_decay()
            if decay_signal:
                logger.warning(
                    f"[META-RL-ALPHA-DECAY] {decay_signal['reason']} "
                    f"→ forcing reset (reward={decay_signal['reward']:.4f})"
                )
                self._force_reset()
                return False  # don't stop, continue with reset population

        return self.agent._generations_no_improve >= self.early_stopping_patience

    def _check_alpha_decay(self) -> dict | None:
        """
        ATOM-META-RL-003: Detect alpha decay.

        Alpha decay = reward is dropping consistently across N generations.
        Detection: rolling mean reward over ALPHA_DECAY_WINDOW_GENS shows
        continuous decline > ALPHA_DECAY_REWARD_DROP_PCT.

        Returns dict with 'reason', 'reward' if decay detected, else None.
        """
        window = ALPHA_DECAY_WINDOW_GENS
        if len(self._history) < window + 1:
            return None

        recent = [s.max_reward for s in self._history[-window:]]
        baseline = self._history[-window - 1].max_reward if len(self._history) > window else recent[0]

        # Check: is reward in a continuous downward trend?
        if not all(recent[i] <= recent[i - 1] for i in range(1, len(recent))):
            return None  # not monotonic decline

        drop_pct = (baseline - recent[-1]) / abs(baseline) if baseline != 0 else 0

        if drop_pct >= ALPHA_DECAY_REWARD_DROP_PCT:
            return {
                "reason": f"reward dropped {drop_pct:.1%} over {window} gens (threshold={ALPHA_DECAY_REWARD_DROP_PCT:.0%})",
                "reward": recent[-1],
                "drop_pct": drop_pct,
                "baseline_reward": baseline,
            }

        # Also check absolute floor: if reward falls below kill threshold
        if recent[-1] < DECAY_KILL_THRESHOLD:
            return {
                "reason": f"reward {recent[-1]:.4f} below kill floor {DECAY_KILL_THRESHOLD}",
                "reward": recent[-1],
                "drop_pct": drop_pct,
                "baseline_reward": baseline,
            }

        return None

    def _force_reset(self) -> None:
        """
        ATOM-META-RL-003: Force-reset the evolution.

        When alpha decay is detected:
        1. Save current best chromosome to KARL memory
        2. Inject fresh random strategies into pool
        3. Reset no_improve counter
        4. Log the reset event
        """
        try:
            # Save best to KARL before reset
            if self.agent.pool:
                best = max(self.agent.pool, key=lambda s: s.reward)
                self.agent.update_karl([best])

            # Inject random strategies to restore diversity
            from strategies.generator import GeneratedStrategy, random_chromosome

            inject_count = max(
                MIN_DIVERSITY_POPULATION,
                self.agent.config.population_size // 4,
            )
            for _ in range(inject_count):
                fresh = GeneratedStrategy(
                    random_chromosome(),
                    generation=self.agent.generation + 1,
                )
                scored = ScoredStrategy(
                    strategy=fresh,
                    reward=0.0,
                    evaluation=None,
                    generation=self.agent.generation + 1,
                    parent_ids=(),
                )
                self.agent.pool.add(scored)

            self.agent._generations_no_improve = 0
            self.agent._best_reward = max(s.reward for s in self.agent.pool) if self.agent.pool else 0.0

            logger.warning(
                f"[META-RL-ALPHA-DECAY] Force-reset complete: "
                f"injected {inject_count} random strategies, "
                f"pool_size={len(self.agent.pool)}"
            )
        except Exception as e:
            logger.warning(f"[META-RL-ALPHA-DECAY] Force-reset failed: {e}")

    def _log_stats(self, stats: EvolutionStats):
        flag = " [KARL-UPDATED]" if stats.karl_updated else ""
        logger.info(
            f"[META-RL-INTEGRATION] Gen {stats.generation:3d}: "
            f"mean={stats.mean_reward:+.4f} max={stats.max_reward:+.4f} "
            f"std={stats.std_reward:.4f} improve={stats.improvement_over_prev:+.4f}{flag}"
        )

    def get_best_strategy(self) -> ScoredStrategy | None:
        """Loopcraft-compatible best strategy getter."""
        # Приоритет: final elites после завершения run()
        candidates = getattr(self, "_final_elites", None) or list(self.agent.pool or [])

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda s: s.reward_history[-1] if getattr(s, 'reward_history', None) else s.reward,
        )

    def convergence_report(self) -> dict:
        if len(self._history) < 2:
            return {"status": "insufficient_data", "generations": len(self._history)}
        max_rewards = [s.max_reward for s in self._history]
        mean_rewards = [s.mean_reward for s in self._history]
        half = len(max_rewards) // 2
        first = sum(max_rewards[:half]) / max(half, 1)
        second = sum(max_rewards[half:]) / max(len(max_rewards) - half, 1)
        return {
            "status": "converged" if second <= first else "improving",
            "total_generations": len(self._history),
            "best_overall": max(max_rewards),
            "final_mean": mean_rewards[-1],
            "improvement_rate": (max_rewards[-1] - max_rewards[0]) / max(len(max_rewards) - 1, 1),
            "karl_updates": sum(1 for s in self._history if s.karl_updated),
            "first_half_avg": round(first, 4),
            "second_half_avg": round(second, 4),
        }

    # ATOM-META-RL-007: Persistence
    def _save_generation(self, elites: list[ScoredStrategy]) -> None:
        try:
            sid = self.session_id or f"gen_{self.agent.generation}"
            if not self.session_id:
                self.session_id = sid
            persist = get_persistence()
            best = max(elites, key=lambda s: s.reward) if elites else None
            br = best.reward if best else 0.0
            bg = best.generation if best else self.agent.generation
            symbol = self.market_data.get("symbol", "BTCUSDT") if self.market_data else "BTCUSDT"
            gs = [s.to_dict() for s in self._history]
            persist.save_evolution_session(
                session_id=sid,
                symbol=symbol,
                cg=bg,
                br=br,
                ks=self.agent.get_karl_state(),
                gs=gs,
            )
            persist.save_elite_chromosomes(elites, sid)
        except Exception as e:
            logger.warning(f"[META-RL-PERSISTENCE] _save_generation failed: {e}")

    def _load_session(self) -> None:
        try:
            loaded = get_persistence().load_evolution_session(self.session_id)
            if not loaded:
                logger.info(f"[META-RL-PERSISTENCE] No session: {self.session_id}")
                return
            self.agent._generation = loaded.get("current_generation", 0)
            self.agent._best_reward = loaded.get("best_reward", -float("inf"))
            for k, v in loaded.get("karl_state", {}).items():
                self.agent._karl_state[k] = v
            logger.info(
                f"[META-RL-PERSISTENCE] Loaded {self.session_id[:8]}: "
                f"gen={loaded['current_generation']} best={loaded['best_reward']:.4f}"
            )
        except Exception as e:
            logger.warning(f"[META-RL-PERSISTENCE] _load_session failed: {e}")

    # ATOM-META-RL-011: Visualization
    def _generate_visualizations(self, elites: list[ScoredStrategy]) -> None:
        try:
            from meta_rl.visualization import VISUALIZATION_ENABLED, generate_all_charts

            if not VISUALIZATION_ENABLED:
                return
            from meta_rl.types import BasketMetrics

            bm = BasketMetrics(symbols=["BTCUSDT"])
            charts = generate_all_charts(
                history=self._history,
                elites=elites,
                karl_state_history=self._karl_state_history,
                basket_metrics=bm,
                session_id=self.session_id or "no_session",
                output_dir=None,
            )
            saved = [k for k, v in charts.items() if v]
            logger.info(f"[META-RL-VIS] Saved {len(saved)}/5 charts: {saved}")
        except Exception as e:
            logger.warning(f"[META-RL-VIS] Visualization failed: {e}")

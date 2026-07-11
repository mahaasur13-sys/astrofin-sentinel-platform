"""meta_rl/hyperopt.py — ATOM-META-RL-015: Hyperparameter Optimization"""
from __future__ import annotations

import logging
import os

# Feature flag
HYPEROPT_ENABLED = os.getenv("HYPEROPT_ENABLED", "false").lower() == "true"

logger = logging.getLogger(__name__)


class HyperOptimizer:
    """ATOM-META-RL-015: Bayesian optimization of Meta-RL hyperparameters."""

    def __init__(self, agent_cls=None, market_data=None, seed=42):
        self.agent_cls = agent_cls
        self.market_data = market_data or {}
        self.seed = seed

    def objective(self, **params) -> float:
        """Run a short evolution and return best reward."""
        if not HYPEROPT_ENABLED:
            return 0.0
        try:
            from meta_rl.evolution import EvolutionEngine
            from meta_rl.meta_agent import MetaAgent

            agent = self.agent_cls or MetaAgent
            engine = EvolutionEngine(
                agent=agent(),
                market_data=self.market_data,
                max_generations=8,
                early_stopping_patience=3,
            )
            elites, history = engine.run()
            if not elites:
                return -999.0
            best = max(elites, key=lambda s: s.reward)
            return best.reward + best.sharpe
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[HYPEROPT] Trial failed: {e}")
            return -999.0

    def optimize(self, n_trials=20, timeout=300) -> dict:
        if not HYPEROPT_ENABLED:
            return {"status": "disabled"}
        try:
            import optuna

            study = optuna.study.create_study(direction="maximize")
            study.optimize(self.objective, n_trials=n_trials, timeout=timeout)
            return {
                "best_params": study.best_params,
                "best_value": study.best_value,
                "trials": n_trials,
                "study": study,
            }
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[HYPEROPT] Optimize failed: {e}")
            return {"error": str(e)}


_meta_optimizer = None


def get_hyper_optimizer(market_data=None, seed=42):
    global _meta_optimizer
    if _meta_optimizer is None:
        _meta_optimizer = HyperOptimizer(market_data=market_data, seed=seed)
    return _meta_optimizer

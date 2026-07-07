"""meta_rl/ranking.py -- ATOM-META-RL-008: Composite Strategy Ranking (P1.2)"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from meta_rl.config import COMPOSITE_RANKING_ENABLED, COMPOSITE_WEIGHTS

logger = logging.getLogger(__name__)


@dataclass
class StrategyScore:
    """Ranked strategy with composite score breakdown."""

    reward: float
    composite_score: float
    sharpe_score: float
    win_rate_score: float
    pnl_score: float
    dd_penalty_score: float
    stability_score: float
    diversity_score: float
    generation: int
    reward_history: list[float]
    evaluation: dict | None
    session_id: str
    chromosome: dict


class CompositeRankingEngine:
    """
    ATOM-META-RL-006: Composite ranking across 5 dimensions.
    Accepts both ScoredStrategy dataclass objects and plain dicts.
    """

    SHARPE_MIN, SHARPE_MAX = -2.0, 5.0
    WINRATE_MIN, WINRATE_MAX = 0.0, 1.0
    PNL_MIN, PNL_MAX = -1.0, 3.0
    DD_MAX_TOLERABLE = 0.5
    WIN_MAX_TOLERABLE = 50

    def __init__(self, weights: dict[str, float] | None = None):
        self.enabled = COMPOSITE_RANKING_ENABLED
        self.weights = weights or dict(COMPOSITE_WEIGHTS)

    def _norm(self, val: float, vmin: float, vmax: float) -> float:
        if vmax <= vmin:
            return 0.5
        n = (val - vmin) / (vmax - vmin)
        return float(np.clip(n, 0.0, 1.0))

    def _get(self, s: Any, key: str, default=None):
        if isinstance(s, dict):
            return s.get(key, default)
        return getattr(s, key, default)

    def rank_strategies(self, strategies: list) -> list[StrategyScore]:
        if not strategies:
            logger.info("[RANKING] No strategies to rank")
            return []

        scored = []
        for s in strategies:
            try:
                reward = float(self._get(s, "reward", 0.0))
                ev = self._get(s, "evaluation")
                pnl = float(ev.get("pnl", 0.0)) if ev else 0.0
                sharpe = float(ev.get("sharpe", 0.0)) if ev else 0.0
                max_dd = float(ev.get("max_drawdown", 0.0)) if ev else 0.0
                win_rate = float(ev.get("win_rate", 0.0)) if ev else 0.0
                trades = int(ev.get("trades", 0)) if ev else 0

                # Per-component scores (0-1, higher = better)
                sharpe_score = self._norm(sharpe, self.SHARPE_MIN, self.SHARPE_MAX)
                win_rate_score = self._norm(win_rate, self.WINRATE_MIN, self.WINRATE_MAX)
                pnl_score = self._norm(pnl, self.PNL_MIN, self.PNL_MAX)
                dd_penalty_score = 1.0 - self._norm(max_dd, 0.0, self.DD_MAX_TOLERABLE)

                # Stability: how flat is reward history
                rh = self._get(s, "reward_history", [])
                stability_score = 0.5
                if len(rh) >= 3:
                    stability_score = 1.0 - float(np.std(rh) / (abs(np.mean(rh)) + 1e-8))

                # Diversity: favor strategies with more trades (liquid)
                diversity_score = self._norm(trades, 0, self.WIN_MAX_TOLERABLE)

                composite_score = (
                    self.weights.get("sharpe", 0.35) * sharpe_score
                    + self.weights.get("win_rate", 0.20) * win_rate_score
                    + self.weights.get("risk_adjusted_pnl", 0.25) * pnl_score
                    + self.weights.get("stability", 0.10) * stability_score
                    + self.weights.get("diversity", 0.10) * diversity_score
                )

                scored.append(
                    StrategyScore(
                        reward=reward,
                        composite_score=composite_score,
                        sharpe_score=sharpe_score,
                        win_rate_score=win_rate_score,
                        pnl_score=pnl_score,
                        dd_penalty_score=dd_penalty_score,
                        stability_score=stability_score,
                        diversity_score=diversity_score,
                        generation=self._get(s, "generation", 0),
                        reward_history=rh,
                        evaluation=ev,
                        session_id=self._get(s, "session_id", ""),
                        chromosome=self._get(s, "chromosome", {}),
                    )
                )
            except Exception as e:
                logger.warning(f"[RANKING] Strategy scoring failed: {e}")
                continue

        scored.sort(key=lambda x: x.composite_score, reverse=True)
        top = scored[0] if scored else None
        if top:
            logger.info(f"[RANKING] Top: score={top.composite_score:.3f} sharpe={top.sharpe_score:.2f} win={top.win_rate_score:.2f} dd={top.dd_penalty_score:.2f}")
        return scored

    def top_n(self, strategies: list, n: int = 5) -> list[StrategyScore]:
        return self.rank_strategies(strategies)[:n]

    def summary(self) -> dict:
        return {
            "enabled": self.enabled,
            "weights": {k: round(v, 3) for k, v in self.weights.items()},
            "total_weight": round(sum(self.weights.values()), 3),
        }


def rank_all_sessions(n_top: int = 20) -> list[dict]:
    """Load all sessions and return top-n globally-ranked strategies."""
    try:
        from meta_rl.persistence import get_persistence

        persist = get_persistence()
        sessions = persist.list_sessions()
        all_strategies = []
        for sid in sessions:
            chroms = persist.load_elite_chromosomes(sid)
            for c in chroms:
                c["session_id"] = sid
                all_strategies.append(c)

        engine = CompositeRankingEngine()
        ranked = engine.rank_strategies(all_strategies)
        return ranked[:n_top] if ranked else []
        return ranked[:n_top] if ranked else []
    except Exception as e:
        logger.warning(f"[RANKING] rank_all_sessions failed: {e}")
        return []

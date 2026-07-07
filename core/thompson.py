from __future__ import annotations
import logging
import random
import threading
from dataclasses import dataclass
import numpy as np
from core.belief import get_belief_tracker

"""
AstroFin Sentinel v5 — Thompson Sampling Agent Selector
FIXED: thread-safe singleton, guaranteed minimum agents, structured logging
"""


logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════
# Agent Pools
# ═════════════════════════════════════════════════


@dataclass
class AgentPool:
    """Defines which agents participate in Thompson sampling."""

    name: str
    agents: list
    min_select: int = 1
    max_select: int | None = None
    min_usefulness: float = 0.30
    k: int | None = None
    description: str = ""


TECHNICAL_POOL = AgentPool(
    name="technical",
    agents=["MarketAnalyst", "BullResearcher", "BearResearcher", "TechnicalAgent"],
    min_select=2,
    max_select=4,
    min_usefulness=0.25,
    description="Technical analysis team",
)

MACRO_POOL = AgentPool(
    name="macro",
    agents=[
        "FundamentalAgent",
        "MacroAgent",
        "QuantAgent",
        "OptionsFlowAgent",
        "SentimentAgent",
    ],
    min_select=2,
    max_select=4,
    min_usefulness=0.30,
    description="Fundamental, macro, and sentiment analysis",
)

ASTRO_POOL = AgentPool(
    name="astro",
    agents=[
        "GannAgent",
        "BradleyAgent",
        "ElliotAgent",
        "CycleAgent",
        "TimeWindowAgent",
        "MuhurtaAgent",
        "ElectionAgent",
    ],
    min_select=4,
    max_select=7,
    min_usefulness=0.25,
    description="Astrological timing pool",
)

ELECTORAL_POOL = AgentPool(
    name="electoral",
    agents=["ElectionAgent", "MuhurtaAgent"],
    min_select=1,
    max_select=2,
    min_usefulness=0.20,
    description="Electional timing",
)

ALL_POOLS = [TECHNICAL_POOL, MACRO_POOL, ELECTORAL_POOL, ASTRO_POOL]

# ═════════════════════════════════════════════════
# Thompson Sampler
# ═════════════════════════════════════════════════


class ThompsonSampler:
    """Thompson sampling selector using Beta distribution per agent."""

    CONFIDENCE_THRESHOLD = 0.30
    DEFAULT_PRIOR_ALPHA = 1.0
    DEFAULT_PRIOR_BETA = 1.0

    def __init__(
        self,
        belief_tracker=None,
        default_k=4,
        random_seed=None,
        min_usefulness=0.30,
        exploration_bonus=0.0,
    ):
        self.belief = belief_tracker or get_belief_tracker()
        self.default_k = default_k
        self.min_usefulness = min_usefulness
        self.exploration_bonus = exploration_bonus
        if random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)

    def _sample_beta(self, alpha: float, beta: float) -> float:
        return float(np.random.beta(alpha, beta))

    def _apply_oap_weighting(self, eligible: list, oap_adjustments=None) -> list:
        if not oap_adjustments:
            return eligible
        weighted = []
        for agent_name, sample, belief in eligible:
            adj = oap_adjustments.get(agent_name, 0.0)
            new_sample = max(0.1, sample * (1.0 + adj))
            if adj != 0.0:
                logger.debug(f"[OAP] {agent_name}: {sample:.3f} → {new_sample:.3f}")
            weighted.append((agent_name, new_sample, belief))
        return weighted

    def select(self, pool: AgentPool, k=None, oap_adjustments=None) -> list:
        """Thompson sampling — GUARANTEED to never return empty list."""
        if not pool.agents:
            raise ValueError(f"Empty pool: {pool.name}")

        threshold = pool.min_usefulness or self.min_usefulness
        if k is None:
            k = pool.k if pool.k is not None else self.default_k
        k = min(k, len(pool.agents))
        k = max(k, pool.min_select)

        eligible = []
        below_threshold = []

        for agent_name in pool.agents:
            belief = self.belief.get(agent_name)
            if belief is not None:
                if belief.mean < threshold:
                    below_threshold.append(agent_name)
                    continue
                alpha, beta = belief.alpha, belief.beta
            else:
                alpha = self.DEFAULT_PRIOR_ALPHA + self.exploration_bonus
                beta = self.DEFAULT_PRIOR_BETA
            sample = self._sample_beta(alpha, beta)
            eligible.append((agent_name, sample, belief))

        if not eligible:
            logger.warning(f"[Thompson] All agents below threshold for '{pool.name}'")
            for agent_name in pool.agents:
                belief = self.belief.get(agent_name)
                if belief is not None:
                    alpha, beta = belief.alpha, belief.beta
                else:
                    alpha = self.DEFAULT_PRIOR_ALPHA + self.exploration_bonus
                    beta = self.DEFAULT_PRIOR_BETA
                sample = self._sample_beta(alpha, beta)
                eligible.append((agent_name, sample, belief))
            below_threshold = []

        eligible = self._apply_oap_weighting(eligible, oap_adjustments)
        eligible.sort(key=lambda x: x[1], reverse=True)
        selected = eligible[:k]

        # FIXED: Guaranteed minimum
        if not selected:
            logger.warning(f"[Thompson] Fallback random for '{pool.name}'")
            fallback_agent = random.choice(pool.agents)
            fallback_sample = self._sample_beta(1.0, 1.0)
            selected = [(fallback_agent, fallback_sample)]

        names = [name for name, _, _ in selected]
        logger.info(f"[Thompson] '{pool.name}': {len(selected)}/{len(pool.agents)} → {names}")
        return [(name, score) for name, score, _ in selected]

    def select_with_exclusions(self, pool, excluded, k=None, oap_adjustments=None) -> list:
        candidates = [a for a in pool.agents if a not in excluded]
        if not candidates:
            return []
        tmp_pool = AgentPool(
            name=pool.name,
            agents=candidates,
            min_select=pool.min_select,
            max_select=pool.max_select,
            min_usefulness=pool.min_usefulness,
        )
        return self.select(tmp_pool, k=k, oap_adjustments=oap_adjustments)

    def scores(self, pool: AgentPool) -> list:
        threshold = pool.min_usefulness or self.min_usefulness
        result = []
        for agent_name in pool.agents:
            belief = self.belief.get(agent_name)
            if belief is not None:
                alpha, beta = belief.alpha, belief.beta
                below = belief.mean < threshold
            else:
                alpha = self.DEFAULT_PRIOR_ALPHA + self.exploration_bonus
                beta = self.DEFAULT_PRIOR_BETA
                below = False
            sample = self._sample_beta(alpha, beta)
            result.append((agent_name, sample, belief, below))
        result.sort(key=lambda x: x[1], reverse=True)
        return result


# ═════════════════════════════════════════════════
# THREAD-SAFE singleton ✅
# ═════════════════════════════════════════════════

_sampler = None
_sampler_lock = threading.Lock()


def get_thompson_sampler() -> ThompsonSampler:
    """Get or create Thompson sampler — THREAD-SAFE."""
    global _sampler
    if _sampler is None:
        with _sampler_lock:
            if _sampler is None:
                _sampler = ThompsonSampler()
    return _sampler


def thompson_select(pool, k=None) -> list:
    return get_thompson_sampler().select(pool, k=k)

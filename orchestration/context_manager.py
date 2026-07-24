"""orchestration/context_manager.py — State building, Thompson/OAP helpers.

Extracted from sentinel_v5.py (P2-04 refactoring).
"""

from __future__ import annotations

import logging

from core.thompson import AgentPool, get_thompson_sampler

logger = logging.getLogger(__name__)

OAP_WEIGHTING_ENABLED = True


def _compute_oap_adjustments(oap_state, agents: list) -> dict:
    if not hasattr(oap_state, "agent_stats") or not oap_state.agent_stats:
        if not agents:
            return {}
        entropy = getattr(oap_state, "entropy_avg", 0.5) or 0.5
        sharpe = getattr(oap_state, "sharpe_ratio", 0.0) or 0.0
        oap_score = 0.5 * entropy + 0.5 * max(0.0, sharpe)
        adjustment = (oap_score - 0.5) * 0.4
        logger.debug(f"[OAP] no per-agent stats — uniform adj={adjustment:+.3f}")
        return dict.fromkeys(agents, adjustment)
    adjustments = {}
    for agent_name in agents:
        stats = oap_state.agent_stats.get(agent_name)
        if stats is None:
            adjustments[agent_name] = 0.0
            continue
        try:
            entropy = getattr(stats, "entropy_contribution", 0.5) or 0.5
            sharpe = max(0.0, getattr(stats, "sharpe_contribution", 0.0) or 0.0)
            recent_q = getattr(stats, "recent_decision_quality", 0.5) or 0.5
            agent_score = entropy * 0.4 + sharpe * 0.4 + recent_q * 0.2
            adjustment = max(-0.25, min(0.25, (agent_score - 0.5) * 0.5))
            adjustments[agent_name] = adjustment
        except Exception:
            adjustments[agent_name] = 0.0
    return adjustments


def _select_for_flow(
    pool: AgentPool,
    excluded: list | None = None,
    k: int | None = None,
    oap_adjustments: dict | None = None,
) -> list:
    adj = oap_adjustments if OAP_WEIGHTING_ENABLED else None
    sampler = get_thompson_sampler()
    if excluded:
        selected = sampler.select_with_exclusions(
            pool, excluded=excluded, k=k, oap_adjustments=adj
        )
    else:
        selected = sampler.select(pool, k=k, oap_adjustments=adj)
    return [name for name, _ in selected]

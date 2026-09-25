"""Verify ASTRO_POOL matches the canonical #303 council weights (5 agents)."""

from __future__ import annotations

from core.thompson import ASTRO_POOL, ELECTORAL_POOL

CANONICAL_ASTRO_AGENTS = {
    "GannAgent",
    "BradleyAgent",
    "ElliotAgent",
    "CycleAgent",
    "TimeWindowAgent",
}


def test_astro_pool_has_exactly_canonical_five() -> None:
    agents = list(ASTRO_POOL.agents)
    assert set(agents) == CANONICAL_ASTRO_AGENTS
    assert len(agents) == 5
    assert "MuhurtaAgent" not in agents
    assert "ElectionAgent" not in agents


def test_muhurta_election_live_in_electoral_pool() -> None:
    """Muhurta/Election are a separate track, not dropped from the repo."""
    assert "MuhurtaAgent" in ELECTORAL_POOL.agents
    assert "ElectionAgent" in ELECTORAL_POOL.agents

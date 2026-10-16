"""Веса агентов: единственный источник — agents/_impl/synthesis/weights.py.

Остальные модули (core/council, core/ensemble_voting, agents/astro_council_agent,
agents/_impl/astro_council) обязаны брать числа оттуда, а не держать свои копии.
"""

from __future__ import annotations

import pytest

from agents._impl.astro_council.agent import AGENT_WEIGHTS as ASTRO_WEIGHTS
from agents._impl.synthesis.weights import AGENT_WEIGHTS, CATEGORY_WEIGHTS
from core.council.types import AGENT_WEIGHTS as COUNCIL_WEIGHTS
from core.ensemble_voting import HYBRID_WEIGHTS


def _total(weights: dict[str, float]) -> float:
    return round(sum(weights.values()), 9)


def test_canonical_tables_sum_to_one() -> None:
    assert _total(AGENT_WEIGHTS) == 1.0
    assert _total(CATEGORY_WEIGHTS) == 1.0


def test_council_weights_come_from_canonical() -> None:
    assert _total(COUNCIL_WEIGHTS) == 1.0
    assert COUNCIL_WEIGHTS["fundamental"] == pytest.approx(CATEGORY_WEIGHTS["fundamental"])
    assert COUNCIL_WEIGHTS["optionsflow"] == pytest.approx(CATEGORY_WEIGHTS["options"])
    assert COUNCIL_WEIGHTS["astro"] == pytest.approx(CATEGORY_WEIGHTS["astro"])


def test_astro_block_uses_canonical_proportions() -> None:
    assert _total(ASTRO_WEIGHTS) == 1.0
    block_total = sum(AGENT_WEIGHTS[name] for name in ASTRO_WEIGHTS)
    for name, weight in ASTRO_WEIGHTS.items():
        assert weight == pytest.approx(AGENT_WEIGHTS[name] / block_total)


def test_ensemble_weights_are_proportional_to_canonical() -> None:
    voting = {k: v for k, v in HYBRID_WEIGHTS.items() if v >= 0}
    assert HYBRID_WEIGHTS["market_analyst"] < 0  # sentinel: информационный, не голосует
    assert _total(voting) == 1.0
    assert voting["fundamental"] / voting["macro"] == pytest.approx(
        AGENT_WEIGHTS["FundamentalAgent"] / AGENT_WEIGHTS["MacroAgent"]
    )
    assert voting["cycle"] / voting["bradley"] == pytest.approx(
        AGENT_WEIGHTS["CycleAgent"] / AGENT_WEIGHTS["BradleyAgent"]
    )


def test_astro_council_agent_weights_proportional_to_canonical() -> None:
    """AstroCouncil HYBRID_WEIGHTS — та же логика, что в _build_agent_weights:
    полное имя агента из AGENT_WEIGHTS, иначе вес категории из CATEGORY_WEIGHTS."""
    from agents.astro_council_agent import HYBRID_WEIGHTS as COUNCIL_HYBRID
    from agents.astro_council_agent import _AGENT_CATEGORY_MAP

    assert _total(COUNCIL_HYBRID) == 1.0
    raw = {
        name: (AGENT_WEIGHTS[name] if name in AGENT_WEIGHTS else CATEGORY_WEIGHTS[category])
        for name, category in _AGENT_CATEGORY_MAP.items()
    }
    raw_total = sum(raw.values())
    for name, weight in raw.items():
        assert COUNCIL_HYBRID[name] == pytest.approx(weight / raw_total)

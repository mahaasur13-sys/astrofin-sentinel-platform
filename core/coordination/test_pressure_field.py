"""test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests + Constraints"""

from __future__ import annotations

import pytest

from core.coordination.pressure_field import (
    AgentSignal,
    apply_pressure_field,
    compute_similarity,
    signal_to_direction,
)


class TestSignalMapping:
    """7.1 Конфликт: BUY vs SELL."""

    def test_contradiction_both_lose_confidence(self):
        """
        Противоречие: оба теряют уверенность.
        A(BUY, eff=70) ← B(SELL, eff=60): score = -0.60 → A: 70 + 0.15×(-0.60) = 69.91
        B(SELL, eff=60) ← A(BUY, eff=70): score = -0.70 → B: 60 + 0.15×(-0.70) = 59.895
        """
        agents = [
            AgentSignal("A", "BUY", 80, 70, 1.0),
            AgentSignal("B", "SELL", 60, 60, 1.0),
        ]
        result = apply_pressure_field(agents, enabled=True)

        a_after = next(a.eff_conf for a in result if a.name == "A")
        b_after = next(a.eff_conf for a in result if a.name == "B")

        assert a_after < 70, f"A should lose confidence, got {a_after}"
        assert b_after < 60, f"B should lose confidence, got {b_after}"


class TestConsensus:
    """7.2 Консенсус: BUY + BUY усиливают друг друга."""

    def test_consensus_both_amplify(self):
        """
        Консенсус: оба усиливаются.
        A(BUY, eff=60) ← B(BUY, eff=75): score = +0.75 → A: 60 + 0.15×0.75 = 60.1125
        B(BUY, eff=75) ← A(BUY, eff=60): score = +0.60 → B: 75 + 0.15×0.60 = 75.09
        """
        agents = [
            AgentSignal("A", "BUY", 70, 60, 1.0),
            AgentSignal("B", "BUY", 80, 75, 1.0),
        ]
        result = apply_pressure_field(agents, enabled=True)

        a_after = next(a.eff_conf for a in result if a.name == "A")
        b_after = next(a.eff_conf for a in result if a.name == "B")

        assert a_after > 60, f"A should gain confidence, got {a_after}"
        assert b_after > 75, f"B should gain confidence, got {b_after}"


class TestOutlier:
    """7.3 Outlier: SELL не игнорируется."""

    def test_outlier_not_ignored(self):
        """
        SELL не игнорируется, BUY теряет confidence.

        A(BUY, eff=70) ← B(BUY, eff=65): +0.65, C(SELL, eff=85): -0.85
        → A net: +0.65 - 0.85 = -0.20 → 70 + 0.15×(-0.20) = 69.97 (теряет)

        B(BUY, eff=65) ← A(BUY, eff=70): +0.70, C(SELL, eff=85): -0.85
        → B net: +0.70 - 0.85 = -0.15 → 65 + 0.15×(-0.15) = 64.98 (теряет)

        C(SELL, eff=85) ← A(BUY, eff=70): -0.70, B(BUY, eff=65): -0.65
        → C net: -0.70 - 0.65 = -1.35 → 85 + 0.15×(-1.35) = 84.80 (теряет!)
        """
        agents = [
            AgentSignal("A", "BUY", 80, 70, 1.0),
            AgentSignal("B", "BUY", 75, 65, 1.0),
            AgentSignal("C", "SELL", 90, 85, 1.0),
        ]
        result = apply_pressure_field(agents, enabled=True)

        a_after = next(a.eff_conf for a in result if a.name == "A")
        c_after = next(a.eff_conf for a in result if a.name == "C")

        # BUY agents теряют от давления SELL outlier
        assert a_after < 70, f"A (BUY) should lose confidence, got {a_after}"

        # C (SELL) тоже теряет (несогласных x2 = больше негатива для SELL)
        assert c_after < 85, f"C (SELL) should lose confidence, got {c_after}"


class TestSignalDirection:
    """Направления сигналов."""

    def test_strong_signals(self):
        assert signal_to_direction("BUY") == 1
        assert signal_to_direction("SELL") == -1
        assert signal_to_direction("LONG") == 1
        assert signal_to_direction("SHORT") == -1
        assert signal_to_direction("STRONG_BUY") == 1
        assert signal_to_direction("STRONG_SELL") == -1
        assert signal_to_direction("NEUTRAL") == 0
        assert signal_to_direction("HOLD") == 0
        assert signal_to_direction("AVOID") == 0


class TestSimilarity:
    """Similarity function."""

    def test_same_signal(self):
        a = AgentSignal("A", "BUY", 80, 70, 1.0)
        b = AgentSignal("B", "BUY", 60, 60, 1.0)
        assert compute_similarity(a, b) == 1.0

    def test_opposite_signal(self):
        """Non-neutral agents always have magnitude 1.0."""
        a = AgentSignal("A", "BUY", 80, 70, 1.0)
        b = AgentSignal("B", "SELL", 60, 60, 1.0)
        # similarity magnitude = 1.0 for non-neutral agents
        assert compute_similarity(a, b) == 1.0

    def test_neutral_signal(self):
        a = AgentSignal("A", "BUY", 80, 70, 1.0)
        b = AgentSignal("B", "NEUTRAL", 60, 60, 1.0)
        assert compute_similarity(a, b) == 0.0


class TestConstraints:
    """8. Ограничения: не менять signal."""

    def test_signal_unchanged(self):
        """Signal не меняется после apply_pressure_field."""
        agents = [
            AgentSignal("A", "BUY", 80, 70, 1.0),
            AgentSignal("B", "SELL", 60, 60, 1.0),
        ]
        result = apply_pressure_field(agents, enabled=True)

        for orig, upd in zip(agents, result, strict=False):
            assert orig.signal == upd.signal, f"Signal changed from {orig.signal} to {upd.signal}"


class TestRegimeDiscount:
    """Regime discount в EXTREME."""

    def test_extreme_regime_reduces_influence(self):
        """
        В EXTREME regime agent получает ×0.4 influence.
        A(BUY, EXTREME) и B(BUY, NORMAL) согласны.
        Оба получают +conf от B и A соответственно.
        Но A получает ×0.4 → меньше усиления.
        """
        agents = [
            AgentSignal("A", "BUY", 80, 70, 1.0, regime="EXTREME"),
            AgentSignal("B", "BUY", 80, 70, 1.0, regime="NORMAL"),
        ]
        result = apply_pressure_field(agents, enabled=True)

        a_delta = result[0].eff_conf - agents[0].eff_conf
        b_delta = result[1].eff_conf - agents[1].eff_conf

        # A (EXTREME) должен усилиться МЕНЬШЕ чем B (NORMAL)
        assert abs(b_delta) >= abs(a_delta), f"NORMAL agent should have stronger influence boost, got B_delta={b_delta:.4f}, A_delta={a_delta:.4f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

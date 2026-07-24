"""tests/test_council.py — AstroCouncil Tests"""

from __future__ import annotations

import pytest

from core.council.agents import AGENT_FACTORIES
from core.council.council import (
    AstroCouncil,
)
from core.council.types import CouncilMember, CouncilResult, Signal


class TestAstroCouncil:
    def test_majority_long(self):
        council = AstroCouncil()
        for _ in range(4):
            council.add_member(
                CouncilMember(
                    name="a",
                    domain="x",
                    vote=Signal.LONG,
                    confidence=60,
                    reasoning="",
                    weight=0.1,
                    aligned=False,
                )
            )
        for _ in range(2):
            council.add_member(
                CouncilMember(
                    name="b",
                    domain="y",
                    vote=Signal.SHORT,
                    confidence=60,
                    reasoning="",
                    weight=0.1,
                    aligned=False,
                )
            )
        result = council.vote("TEST", "test deliberation")
        assert result.final_signal == Signal.LONG
        assert result.consensus == pytest.approx(2 / 3)

    def test_majority_short(self):
        council = AstroCouncil()
        for _ in range(3):
            council.add_member(
                CouncilMember(
                    name="a",
                    domain="x",
                    vote=Signal.SHORT,
                    confidence=70,
                    reasoning="",
                    weight=0.1,
                    aligned=False,
                )
            )
        for _ in range(3):
            council.add_member(
                CouncilMember(
                    name="b",
                    domain="y",
                    vote=Signal.NEUTRAL,
                    confidence=60,
                    reasoning="",
                    weight=0.1,
                    aligned=False,
                )
            )
        result = council.vote("TEST", "test")
        assert result.final_signal == Signal.SHORT

    def test_neutral_tie(self):
        council = AstroCouncil()
        council.add_member(
            CouncilMember(
                name="a",
                domain="x",
                vote=Signal.LONG,
                confidence=60,
                reasoning="",
                weight=0.1,
                aligned=False,
            )
        )
        council.add_member(
            CouncilMember(
                name="b",
                domain="y",
                vote=Signal.SHORT,
                confidence=60,
                reasoning="",
                weight=0.1,
                aligned=False,
            )
        )
        result = council.vote("TEST", "test")
        assert result.final_signal == Signal.NEUTRAL
        assert len(result.dissent) == 2

    def test_weighted_signal(self):
        council = AstroCouncil()
        council.add_member(
            CouncilMember(
                name="a",
                domain="x",
                vote=Signal.LONG,
                confidence=100,
                reasoning="",
                weight=0.5,
                aligned=False,
            )
        )
        council.add_member(
            CouncilMember(
                name="b",
                domain="y",
                vote=Signal.LONG,
                confidence=60,
                reasoning="",
                weight=0.3,
                aligned=False,
            )
        )
        council.add_member(
            CouncilMember(
                name="c",
                domain="z",
                vote=Signal.SHORT,
                confidence=70,
                reasoning="",
                weight=0.2,
                aligned=False,
            )
        )
        result = council.vote("TEST", "test")
        # weighted = (0.5*1.0 + 0.3*1.0 + 0.2*-1.0) / 1.0 = 0.6
        # confidence = 60 * 0.6 + 40 = 76
        assert result.final_signal == Signal.LONG

    def test_all_agents(self):
        agents = [
            AGENT_FACTORIES["fundamental"](price=100, fair_value=110, catalyst=""),
            AGENT_FACTORIES["quant"](predicted_return=0.05, uncertainty=0.02),
            AGENT_FACTORIES["macro"](vix=15, dxy=100, geopolitical=0.0),
            AGENT_FACTORIES["technical"](rsi=30, macd_bullish=True, price=100),
            AGENT_FACTORIES["sentiment"](vix=60, fear_greed=60, news_score=0.3),
            AGENT_FACTORIES["optionsflow"](
                predicted_return=0.0, ul_trailing=500000, gamma_exp=0.1, unusual=False
            ),
            AGENT_FACTORIES["astro"](
                price=100,
                predicted_return=0.02,
                moon_long=120,
                jupiter_long=200,
                saturn_long=300,
                nakshatra=14,
                choghadiya="Shubh",
                retrograde=[],
            ),
        ]
        for a in agents:
            assert hasattr(a, "vote")
            assert hasattr(a, "confidence")
            assert a.vote is not None

    def test_run_council(self):
        from core.council.runner import run_council

        result = run_council(
            "BTCUSDT",
            price=48000,
            fair_value=52000,
            predicted_return=0.05,
            uncertainty=0.02,
            rsi=30,
            macd_bullish=True,
        )
        assert isinstance(result, CouncilResult)
        assert hasattr(result, "final_signal")
        assert hasattr(result, "confidence")
        assert result.final_signal in (Signal.LONG, Signal.SHORT, Signal.NEUTRAL)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

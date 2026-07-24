"""tests/test_ensemble_voting.py — Sprint 6: Ensemble Voting Engine Tests."""

import pytest
from core.ensemble_voting import (
    EnsembleVotingEngine,
    AgentVote,
    EnsembleResult,
    Signal,
    HYBRID_WEIGHTS,
    REGIME_MULTIPLIER,
    ensemble_from_13_agents,
)


class TestEnums:
    def test_signal_values(self):
        assert Signal.LONG.value == "LONG"
        assert Signal.SHORT.value == "SHORT"
        assert Signal.NEUTRAL.value == "NEUTRAL"

    def test_regime_multipliers(self):
        assert REGIME_MULTIPLIER["LOW"] == 1.2
        assert REGIME_MULTIPLIER["NORMAL"] == 1.0
        assert REGIME_MULTIPLIER["HIGH"] == 0.7
        assert REGIME_MULTIPLIER["EXTREME"] == 0.4


class TestAgentVote:
    def test_vote_creation(self):
        vote = AgentVote("bull", Signal.LONG, 0.85, "Strong buy")
        assert vote.agent_name == "bull"
        assert vote.signal == Signal.LONG
        assert vote.confidence == 0.85
        assert vote.reasoning == "Strong buy"

    def test_default_reasoning(self):
        vote = AgentVote("bear", Signal.NEUTRAL, 0.5)
        assert vote.reasoning == ""


class TestEnsembleVotingEngine:
    def test_empty_votes(self):
        engine = EnsembleVotingEngine()
        result = engine.vote({})
        assert result.signal == Signal.NEUTRAL
        assert result.score == 0.0
        assert len(result.votes) == 0

    def test_unanimous_long(self):
        engine = EnsembleVotingEngine()
        result = engine.vote({
            "fundamental": {"signal": "LONG", "confidence": 80, "reasoning": "bullish"},
            "quant": {"signal": "LONG", "confidence": 85, "reasoning": "momentum up"},
            "sentiment": {"signal": "LONG", "confidence": 70, "reasoning": "positive"},
        })
        assert result.signal == Signal.LONG
        assert result.score > 0

    def test_unanimous_short(self):
        engine = EnsembleVotingEngine()
        result = engine.vote({
            "fundamental": {"signal": "SHORT", "confidence": 75, "reasoning": "overvalued"},
            "macro": {"signal": "SHORT", "confidence": 82, "reasoning": "tightening"},
        })
        assert result.signal == Signal.SHORT
        assert result.score < 0

    def test_split_votes_neutral(self):
        engine = EnsembleVotingEngine()
        result = engine.vote({
            "bull": {"signal": "LONG", "confidence": 60, "reasoning": ""},
            "bear": {"signal": "SHORT", "confidence": 60, "reasoning": ""},
        })
        assert result.confidence < 70
        assert -0.3 <= result.score <= 0.3

    def test_nakshatra_hold_override(self):
        engine = EnsembleVotingEngine()
        result = engine.vote(
            {
                "fundamental": {"signal": "LONG", "confidence": 95, "reasoning": "strong"},
                "quant": {"signal": "LONG", "confidence": 90, "reasoning": "bullish"},
            },
            nakshatra="Mula",
            regime="NORMAL",
        )
        assert result.nakshatra == "Mula"
        assert result.nakshatra_risk > 1.0
        assert len(result.veto_reason) > 0
        assert result.confidence < 90

    def test_ensemble_from_13_agents(self):
        results = {
            "fundamental": {"signal": "LONG", "confidence": 75, "reasoning": "good fundamentals"},
            "macro": {"signal": "NEUTRAL", "confidence": 50, "reasoning": "mixed macro"},
            "quant": {"signal": "LONG", "confidence": 80, "reasoning": "momentum"},
            "sentiment": {"signal": "SHORT", "confidence": 65, "reasoning": "bearish sentiment"},
            "options_flow": {"signal": "LONG", "confidence": 70, "reasoning": "call buying"},
            "bull": {"signal": "LONG", "confidence": 85, "reasoning": "bull thesis"},
            "bear": {"signal": "SHORT", "confidence": 80, "reasoning": "bear thesis"},
            "market_analyst": {"signal": "NEUTRAL", "confidence": 55, "reasoning": "ranging"},
            "technical": {"signal": "SHORT", "confidence": 60, "reasoning": "breakdown"},
            "electoral": {"signal": "LONG", "confidence": 70, "reasoning": "muhurta window"},
            "bradley": {"signal": "NEUTRAL", "confidence": 50, "reasoning": "seasonal"},
            "gann": {"signal": "LONG", "confidence": 65, "reasoning": "1x1 angle"},
            "cycle": {"signal": "LONG", "confidence": 72, "reasoning": "cycle bottom"},
        }
        result = ensemble_from_13_agents(results, regime="NORMAL")
        assert isinstance(result, EnsembleResult)
        assert len(result.votes) == 13
        assert result.regime == "NORMAL"

    def test_weighted_score_range(self):
        engine = EnsembleVotingEngine()
        result = engine.vote({
            "bull": {"signal": "LONG", "confidence": 50, "reasoning": ""},
        })
        assert -1.0 <= result.score <= 1.0

    def test_risky_nakshatra_caps_confidence(self):
        engine = EnsembleVotingEngine()
        result = engine.vote(
            {
                "bull": {"signal": "LONG", "confidence": 95, "reasoning": ""},
                "fundamental": {"signal": "LONG", "confidence": 90, "reasoning": ""},
            },
            nakshatra="Jyeshtha",
            regime="NORMAL",
        )
        assert result.nakshatra_risk > 1.0
        assert result.confidence < 95

    def test_hybrid_weights_are_valid(self):
        valid_signal_weights = {k: v for k, v in HYBRID_WEIGHTS.items() if v >= 0}
        total = sum(valid_signal_weights.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

    def test_concat_99(self):
        """Boundary test: 99% confidence with LONG signal."""
        engine = EnsembleVotingEngine()
        result = engine.vote(
            {
                "bull": {"signal": "LONG", "confidence": 99, "reasoning": "max confidence"},
                "fundamental": {"signal": "LONG", "confidence": 99, "reasoning": ""},
                "quant": {"signal": "LONG", "confidence": 99, "reasoning": ""},
            },
            nakshatra="Pushya",
            regime="LOW",
        )
        assert result.signal == Signal.LONG
        assert result.nakshatra_risk < 1.0

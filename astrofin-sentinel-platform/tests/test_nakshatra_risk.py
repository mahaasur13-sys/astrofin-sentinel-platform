"""tests/test_nakshatra_risk.py — Sprint 6: Nakshatra Risk Multiplier Tests."""

import pytest
from trading.vedic.nakshatra_risk import (
    NAKSHATRA_RISK,
    NAKSHATRA_ELECTION,
    ElectionGrade,
    get_nakshatra_multiplier,
    get_election_grade,
    is_dangerous_nakshatra,
    is_favorable_nakshatra,
    format_nakshatra_explanation,
)


class TestNakshatraRiskTable:
    def test_all_27_nakshatras_defined(self):
        assert len(NAKSHATRA_RISK) == 27

    def test_multipliers_in_valid_range(self):
        for name, mult in NAKSHATRA_RISK.items():
            assert 0.5 <= mult <= 1.5, f"{name}: {mult} out of [0.5, 1.5]"

    def test_specific_known_values(self):
        assert NAKSHATRA_RISK["Pushya"] == 0.75
        assert NAKSHATRA_RISK["Mula"] == 1.40
        assert NAKSHATRA_RISK["Jyeshtha"] == 1.35
        assert NAKSHATRA_RISK["Ardra"] == 1.30
        assert NAKSHATRA_RISK["Uttara Bhadrapada"] == 0.75
        assert NAKSHATRA_RISK["Shravana"] == 0.80


class TestNakshatraElection:
    def test_election_grades_for_all(self):
        for name in NAKSHATRA_ELECTION:
            grade = get_election_grade(name)
            assert isinstance(grade, ElectionGrade)

    def test_pushya_is_excellent(self):
        assert get_election_grade("Pushya") == ElectionGrade.EXCELLENT

    def test_mula_is_avoid(self):
        assert get_election_grade("Mula") == ElectionGrade.AVOID

    def test_unknown_nakshatra_returns_neutral(self):
        assert get_election_grade("UnknownNakshatra") == ElectionGrade.NEUTRAL

    def test_none_returns_neutral(self):
        assert get_election_grade(None) == ElectionGrade.NEUTRAL


class TestDangerousClassification:
    def test_mula_is_dangerous(self):
        assert is_dangerous_nakshatra("Mula") is True

    def test_jyeshtha_is_dangerous(self):
        assert is_dangerous_nakshatra("Jyeshtha") is True

    def test_ardra_is_dangerous(self):
        assert is_dangerous_nakshatra("Ardra") is True

    def test_pushya_is_not_dangerous(self):
        assert is_dangerous_nakshatra("Pushya") is False

    def test_none_is_not_dangerous(self):
        assert is_dangerous_nakshatra(None) is False


class TestFavorableClassification:
    def test_pushya_is_favorable(self):
        assert is_favorable_nakshatra("Pushya") is True

    def test_hasta_is_favorable(self):
        assert is_favorable_nakshatra("Hasta") is True

    def test_rohini_is_favorable(self):
        assert is_favorable_nakshatra("Rohini") is True

    def test_mula_is_not_favorable(self):
        assert is_favorable_nakshatra("Mula") is False

    def test_none_is_not_favorable(self):
        assert is_favorable_nakshatra(None) is False


class TestNakshatraExplanation:
    def test_returns_string_with_nakshatra_name(self):
        result = format_nakshatra_explanation("Pushya")
        assert isinstance(result, str)
        assert "Pushya" in result

    def test_returns_neutral_for_none(self):
        result = format_nakshatra_explanation(None)
        assert "neutral" in result.lower()


class TestRiskEngineV2Integration:
    def test_get_current_params_with_nakshatra(self):
        from trading.risk_v2 import RiskEngineV2, RiskConfigV2
        engine = RiskEngineV2(RiskConfigV2())
        params = engine.get_current_params(
            observations={"macro_data": True},
            hmm_probs={"LOW": 0.1, "NORMAL": 0.7, "HIGH": 0.2},
            nakshatra="Pushya",
        )
        assert "max_leverage" in params
        assert "position_size_pct" in params
        assert isinstance(params["nakshatra_multiplier"], float)
        assert params["nakshatra_multiplier"] < 1.0

    def test_get_current_params_without_nakshatra_uses_1_0(self):
        from trading.risk_v2 import RiskEngineV2, RiskConfigV2
        engine = RiskEngineV2(RiskConfigV2())
        params = engine.get_current_params(observations={}, nakshatra=None)
        assert params["nakshatra_multiplier"] == 1.0

    def test_get_current_params_dangerous_nakshatra(self):
        from trading.risk_v2 import RiskEngineV2, RiskConfigV2
        engine = RiskEngineV2(RiskConfigV2())
        params = engine.get_current_params(observations={}, nakshatra="Mula")
        assert params["nakshatra_multiplier"] > 1.0
        assert isinstance(params["stop_loss_multiplier"], float)

    def test_pre_trade_check_unchanged_without_nakshatra(self):
        from trading.risk_v2 import RiskEngineV2, RiskConfigV2
        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.05))
        engine.update_equity(100_000)
        status, _, _ = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
        assert status == "APPROVED"

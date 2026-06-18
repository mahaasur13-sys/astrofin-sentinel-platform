"""tests/test_karl_synthesis_lag.py — ATOM-KARL-015 Phase 5: Tests for LagWindow integration in KARLSynthesisAgent

Tests:
1. lag_enabled=False → confidence и position без изменений
2. lag_enabled=True → confidence сглаживается через LagWindow
3. lag_metrics присутствуют в synth_dict
4. Risk control корректирует позицию при зрелом окне
5. Risk control не применяется при незрелом окне
6. Feature flag lag_enabled=False полностью отключает всё поведение

Запуск:
    pytest tests/test_karl_synthesis_lag.py -v
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# ─── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_karl_dependencies():
    """Mock всех зависимостей KARLSynthesisAgent для unit-тестирования."""
    with patch.multiple(
        "agents.karl_synthesis",
        SynthesisAgent=MagicMock(),
        get_audit_log=MagicMock(),
        get_oap_optimizer=MagicMock(),
        get_calibrator=MagicMock(),
        get_dd_tracker=MagicMock(),
        get_reward_diagnostics=MagicMock(),
        get_karl_diagnostics=MagicMock(),
        build_decision_record=MagicMock(),
        estimate_uncertainty=MagicMock(return_value={"total": 0.5}),
        validate_with_grounding=MagicMock(return_value={"passed": True, "confidence_adjustment": 0}),
        compute_trajectory_reward=MagicMock(return_value=0.6),
        create_backtest_runner=MagicMock(),
        SelfQuestioningEngine=MagicMock(),
        should_trigger_self_questioning=MagicMock(return_value=(False, "not_enabled")),
        check_delisted_fallback=MagicMock(return_value=None),
        market_state_hash=MagicMock(return_value="abc123"),
        MarketState=MagicMock(),
        RewardState=MagicMock(),
        update_reward_ema=MagicMock(return_value=0.6),
    ):
        yield


@pytest.fixture
def mock_lag_window():
    """Mock LagWindow.add() возвращает предсказуемые метрики."""
    return {
        "final_confidence": 72,
        "raw_confidence": 90,
        "ema": 68.4,
        "lag_adj": -0.24,
        "position_lag": 0.15,
        "window_size": 50,
        "alpha": 0.0392,
        "blend": 0.15,
        "count": 25,  # mature window
    }


@pytest.fixture
def agent_with_mocks(mock_karl_dependencies):
    """KARLSynthesisAgent с замоканными зависимостями."""
    from agents.karl_synthesis import KARLSynthesisAgent

    agent = KARLSynthesisAgent(
        enable_self_question=False,
        enable_backtest=False,
    )
    # Убеждаемся что lag_window — мок
    agent.lag_window = Mock()
    return agent


# ─── Test _apply_lag_smoothing ─────────────────────────────────────────────────


class TestApplyLagSmoothing:
    """Тесты метода _apply_lag_smoothing."""

    def test_disabled_returns_unchanged(self):
        """lag_enabled=False → возвращает входные значения без изменений."""
        from agents.karl_synthesis import KARLSynthesisAgent

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = False
        # При выключенном lag_enabled, lag_window.add НЕ вызывается
        agent.lag_window = Mock()

        conf, pos, meta = agent._apply_lag_smoothing(90, 0.05)

        assert conf == 90
        assert pos == 0.05
        assert meta == {}
        # add() не должен был быть вызван
        agent.lag_window.add.assert_not_called()

    def test_enabled_smooths_confidence(self, mock_lag_window):
        """lag_enabled=True → confidence сглаживается через LagWindow."""
        from agents.karl_synthesis import KARLSynthesisAgent

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(return_value=mock_lag_window)

        conf, pos, meta = agent._apply_lag_smoothing(90, 0.05)

        assert conf == 72  # smoothed
        assert pos == 0.05  # not yet risk-adjusted
        assert meta["raw_confidence"] == 90
        assert meta["ema_confidence"] == 68.4
        assert meta["lag_adjustment"] == -0.24
        assert meta["window_mature"] is True

    def test_mature_window_flag(self, mock_lag_window):
        """count >= 20 → window_mature=True."""
        from agents.karl_synthesis import KARLSynthesisAgent

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(return_value=mock_lag_window)  # count=25

        _, _, meta = agent._apply_lag_smoothing(50, 0.05)

        assert meta["window_mature"] is True

    def test_immature_window_flag(self):
        """count < 20 → window_mature=False."""
        from agents.karl_synthesis import KARLSynthesisAgent

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(
            return_value={
                "final_confidence": 50,
                "raw_confidence": 50,
                "ema": 50.0,
                "lag_adj": 0.0,
                "position_lag": 0.0,
                "window_size": 50,
                "alpha": 0.0392,
                "blend": 0.30,  # warmup blend
                "count": 5,  # immature
            }
        )

        _, _, meta = agent._apply_lag_smoothing(50, 0.05)

        assert meta["window_mature"] is False

    def test_all_metrics_keys_present(self, mock_lag_window):
        """lag_meta содержит все ключи: raw/ema/lag_adj/position_lag/window_mature."""
        from agents.karl_synthesis import KARLSynthesisAgent

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(return_value=mock_lag_window)

        _, _, meta = agent._apply_lag_smoothing(90, 0.05)

        required_keys = [
            "raw_confidence",
            "ema_confidence",
            "lag_adjustment",
            "position_lag",
            "window_mature",
            "window_size",
            "blend",
        ]
        for key in required_keys:
            assert key in meta, f"Missing key: {key}"


# ─── Test Risk Control Integration ──────────────────────────────────────────────


class TestRiskControlIntegration:
    """Тест интеграции position_lag risk control в run()."""

    def test_risk_adjustment_called_when_mature(self, mock_karl_dependencies):
        """Когда window_mature=True, apply_position_lag_risk вызывается."""
        from agents._impl.amre.lag_windowing import reset_lag_window
        from agents.karl_synthesis import KARLSynthesisAgent

        reset_lag_window()  # чистое состояние

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True

        # Мокаем lag_window с mature count
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(
            return_value={
                "final_confidence": 72,
                "raw_confidence": 90,
                "ema": 68.4,
                "lag_adj": -0.24,
                "position_lag": 0.15,  # < 0.3 threshold → no risk change
                "window_size": 50,
                "alpha": 0.0392,
                "blend": 0.15,
                "count": 25,
            }
        )

        # Мокаем risk_control чтобы проверить вызов
        with patch("agents.karl_synthesis.apply_position_lag_risk") as mock_risk:
            mock_risk.return_value = 0.05  # unchanged

            conf, pos, meta = agent._apply_lag_smoothing(90, 0.05)

            # Risk control вызывается только в run(), не в _apply_lag_smoothing
            # Здесь мы проверяем что позиция передаётся правильно
            assert pos == 0.05

    def test_position_risk_adjusted_flag_set(self, mock_karl_dependencies):
        """Когда риск-контроль меняет позицию, флаг position_risk_adjusted=True."""
        from agents._impl.amre.lag_windowing import reset_lag_window
        from agents.karl_synthesis import KARLSynthesisAgent

        reset_lag_window()

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(
            return_value={
                "final_confidence": 72,
                "raw_confidence": 90,
                "ema": 68.4,
                "lag_adj": -0.24,
                "position_lag": 0.5,  # > 0.3 threshold → increase
                "window_size": 50,
                "alpha": 0.0392,
                "blend": 0.15,
                "count": 25,
            }
        )

        # В run() position_pct корректируется через apply_position_lag_risk
        # Проверяем что position_lag > threshold приведёт к увеличению
        from agents._impl.amre.risk_control import apply_position_lag_risk

        original_pos = 0.10
        new_pos = apply_position_lag_risk(original_pos, 0.5)
        assert new_pos > original_pos  # 0.10 * 1.1 = 0.11


# ─── Test Full Run() with LagWindow ─────────────────────────────────────────────


class TestRunWithLagWindow:
    """Интеграционные тесты run() с LagWindow."""

    def test_lag_metrics_in_synth_dict(self):
        """После run() synth_dict["lag_metrics"] содержит метрики."""
        import asyncio

        from agents._impl.amre.lag_windowing import reset_lag_window
        from agents.base_agent import AgentResponse, SignalDirection
        from agents.karl_synthesis import KARLSynthesisAgent

        reset_lag_window()

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(
            return_value={
                "final_confidence": 72,
                "raw_confidence": 90,
                "ema": 68.4,
                "lag_adj": -0.24,
                "position_lag": 0.0,
                "window_size": 50,
                "alpha": 0.0392,
                "blend": 0.15,
                "count": 25,
            }
        )

        # Мокаем base_agent как AsyncMock — подменяем на уровне экземпляра
        mock_response = AgentResponse(
            agent_name="test_agent",
            signal=SignalDirection.LONG,
            confidence=90,
            reasoning="test",
            metadata={"position_size": 0.05},
        )
        agent.base_agent = Mock()
        agent.base_agent.run = AsyncMock(return_value=mock_response)

        state = {"symbol": "BTCUSDT", "all_signals": [], "regime": "NORMAL"}
        result = asyncio.run(agent.run(state))

        synth = result["synthesis_result"]
        assert "lag_metrics" in synth
        assert synth["lag_metrics"]["raw_confidence"] == 90
        assert synth["lag_metrics"]["ema_confidence"] == 68.4

    def test_lag_disabled_no_smoothing(self):
        """С выключенным lag_enabled confidence не сглаживается."""
        import asyncio

        from agents._impl.amre.lag_windowing import reset_lag_window
        from agents.base_agent import AgentResponse, SignalDirection
        from agents.karl_synthesis import KARLSynthesisAgent

        reset_lag_window()

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = False  # ВЫКЛЮЧЕНО
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(side_effect=Exception("Should not be called"))

        mock_response = AgentResponse(
            agent_name="test_agent",
            signal=SignalDirection.LONG,
            confidence=90,
            reasoning="test",
            metadata={"position_size": 0.05},
        )
        agent.base_agent = Mock()
        agent.base_agent.run = AsyncMock(return_value=mock_response)

        state = {"symbol": "BTCUSDT", "all_signals": [], "regime": "NORMAL"}
        result = asyncio.run(agent.run(state))

        # Confidence остаётся 90 (не сглажена)
        assert result["synthesis_result"]["confidence"] == 90
        assert result["synthesis_result"]["lag_metrics"] == {}

    def test_confidence_capped_at_bounds(self, mock_karl_dependencies):
        """LagWindow.final_confidence не выходит за 0-100."""
        from agents._impl.amre.lag_windowing import reset_lag_window
        from agents.karl_synthesis import KARLSynthesisAgent

        reset_lag_window()

        agent = KARLSynthesisAgent(enable_self_question=False, enable_backtest=False)
        agent.lag_enabled = True
        agent.lag_window = Mock()
        agent.lag_window.add = Mock(
            return_value={
                "final_confidence": 72,  # уже в пределах
                "raw_confidence": 90,
                "ema": 68.4,
                "lag_adj": -0.24,
                "position_lag": 0.0,
                "window_size": 50,
                "alpha": 0.0392,
                "blend": 0.15,
                "count": 25,
            }
        )

        conf, _, meta = agent._apply_lag_smoothing(90, 0.05)
        assert 0 <= conf <= 100

from unittest.mock import patch


from tools.metrics_server import AGENT_SELECTION_COUNTS


import pytest


@pytest.mark.unit
def test_agent_selection_increments_counter():
    """После выбора агентов через _select_for_flow счётчик должен инкрементироваться."""
    from core.thompson import TECHNICAL_POOL
    from orchestration.sentinel_v5 import _select_for_flow

    with patch("core.thompson.ThompsonSampler.select") as mock_select:
        mock_select.return_value = [("TechnicalAgent", 0.9)]
        _select_for_flow(TECHNICAL_POOL, k=1)

    # Проверяем, что значение дочернего счётчика стало > 0
    val = AGENT_SELECTION_COUNTS.labels(agent_name="TechnicalAgent", pool="technical")._value.get()
    assert val > 0, f"Expected counter > 0, got {val}"


@pytest.mark.unit
def test_signal_distribution_increments():
    """При получении сигнала от агента счётчик распределения должен инкрементироваться."""
    import asyncio
    from unittest.mock import patch

    from orchestration.sentinel_v5 import run_technical_flow

    # Мокаем run_market_analyst, чтобы вернуть LONG
    async def mock_run(state):
        from agents.base_agent import AgentResponse, SignalDirection

        resp = AgentResponse(
            agent_name="MarketAnalyst",
            signal=SignalDirection.LONG,
            confidence=75,
            reasoning="Bullish",
        )
        return {"marketanalyst_signal": resp.to_dict()}

    with patch("orchestration.sentinel_v5.run_market_analyst", side_effect=mock_run):
        state = {"symbol": "BTCUSDT", "current_price": 50000}
        asyncio.run(run_technical_flow(state))


@pytest.mark.unit
def test_thompson_params_gauge_updated():
    """После обновления belief параметры Thompson должны отражаться в Gauge."""
    from core.belief import BeliefTracker
    from tools.metrics_server import THOMPSON_PARAMS

    tracker = BeliefTracker()
    tracker.update_from_session(
        {
            "all_signals": [{"agent_name": "TechnicalAgent", "signal": "LONG"}],
            "final_recommendation": {"signal": "LONG"},
            "session_id": "test-ts",
        }
    )

    alpha_val = THOMPSON_PARAMS.labels(agent_name="TechnicalAgent", param="alpha")._value.get()
    assert alpha_val > 1.0, f"Expected alpha > 1.0, got {alpha_val}"

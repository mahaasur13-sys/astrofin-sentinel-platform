import pytest
from unittest.mock import AsyncMock, Mock, patch

# Список агентов: (модуль, класс)
AGENTS = [
    ("agents._impl.quant_agent", "QuantAgent"),
    ("agents._impl.bradley_agent", "BradleyAgent"),
    ("agents._impl.elliot_agent", "ElliotAgent"),
    ("agents._impl.technical_agent", "TechnicalAgent"),
    ("agents._impl.time_window_agent", "TimeWindowAgent"),
    ("agents._impl.gann_agent", "GannAgent"),
    ("agents._impl.risk_agent", "RiskAgent"),
    ("agents._impl.cycle_agent", "CycleAgent"),
    ("agents._impl.ml_predictor_agent", "MLPredictorAgent"),
    ("agents._impl.fundamental_agent", "FundamentalAgent"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("module_name,class_name", AGENTS)
async def test_agent_uses_async_http(module_name, class_name):
    # Динамически импортируем класс агента
    import importlib

    module = importlib.import_module(module_name)
    agent_cls = getattr(module, class_name)
    agent = agent_cls()
    symbol = "BTCUSDT"

    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(
                return_value={
                    "data": [
                        ["1672531200000", "45000", "46000", "44000", "45500", "100.5"],
                        ["1672617600000", "45500", "46500", "45000", "46000", "200.3"],
                    ]
                }
            ),
        )
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Проверяем, что метод _fetch_ohlcv существует
        if not hasattr(agent, "_fetch_ohlcv"):
            pytest.skip(f"{class_name} has no _fetch_ohlcv")

        data = await agent._fetch_ohlcv(symbol, "1d", 60)

        # Проверяем, что асинхронный GET был вызван
        mock_get.assert_called()
        assert isinstance(data, list)
        assert len(data) == 2
        # Проверяем структуру: [close, volume] (как в MarketAnalyst)
        assert data[0][0] == 45500.0
        assert data[0][1] == 100.5

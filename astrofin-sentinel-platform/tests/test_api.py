"""Integration tests for FastAPI endpoint /api/v1/agent/run."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_run_agent_returns_200():
    with patch("api.main.BaseAgent") as mock_agent_cls:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Mocked LLM response"
        mock_agent_cls.return_value = mock_instance

        response = client.post(
            "/api/v1/agent/run",
            json={"agentId": "test-agent", "prompt": "What is BTC?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"] == "Mocked LLM response"
    mock_instance.generate.assert_called_once()


def test_run_agent_with_empty_prompt():
    with patch("api.main.BaseAgent") as mock_agent_cls:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Empty prompt acknowledged"
        mock_agent_cls.return_value = mock_instance

        response = client.post(
            "/api/v1/agent/run",
            json={"agentId": "test-agent", "prompt": ""},
        )

    assert response.status_code == 200


def test_run_agent_missing_fields_returns_422():
    response = client.post(
        "/api/v1/agent/run",
        json={"agentId": "test-agent"},
    )
    assert response.status_code == 422


def test_run_agent_forwards_prompt_to_llm():
    with patch("api.main.BaseAgent") as mock_agent_cls:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "LLM response for complex query"
        mock_agent_cls.return_value = mock_instance

        client.post(
            "/api/v1/agent/run",
            json={"agentId": "synthesis", "prompt": "Analyze BTC trend"},
        )

    mock_instance.generate.assert_called_once()
    call_kwargs = mock_instance.generate.call_args.kwargs
    assert call_kwargs["prompt"] == "Analyze BTC trend"


def test_cors_headers_present():
    response = client.options(
        "/api/v1/agent/run",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code in (200, 405)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

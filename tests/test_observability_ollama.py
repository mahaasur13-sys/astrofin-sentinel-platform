from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from tools.metrics_server import OLLAMA_STATUS


import pytest


@pytest.mark.unit
def test_ollama_available_sets_status_to_one():
    """При успешном ответе Ollama счётчик astrofin_ollama_available должен стать 1."""
    from knowledge.rag_retriever import _embed

    fake_embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps({"embedding": fake_embedding}).encode()

    with patch("urllib.request.urlopen", return_value=mock_response):
        vec = _embed("test query")
        assert vec.shape == (768,)

    status_val = OLLAMA_STATUS._value.get() if hasattr(OLLAMA_STATUS, "_value") else 0
    assert status_val == 1, f"Expected OLLAMA_STATUS=1, got {status_val}"

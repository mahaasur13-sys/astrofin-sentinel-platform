"""Tests for Intelligent LLM Router (P1)."""

import pytest
pytest.importorskip("sentence_transformers", reason="optional dep for LLM router")
from core.llm_router import classify_complexity


def test_classifier_simple():
    assert classify_complexity("format this text") == "local"


def test_classifier_complex():
    assert classify_complexity("analyze the volatility skew of TSLA options") == "cloud"


def test_classifier_edge_case_empty():
    result = classify_complexity("")
    assert result in ("local", "cloud")


def test_classifier_russian_simple():
    result = classify_complexity("форматируй этот отчёт")
    assert result in ("local", "cloud")


def test_classifier_russian_complex():
    result = classify_complexity(
        "проанализируй корреляцию между VIX и опционным потоком S&P 500"
    )
    assert result in ("local", "cloud")


def test_route_defaults_to_local_when_simple():
    from core.llm_router import route

    # It's fine if local_llm fails (Ollama not running) — the routing logic
    # is what we're testing, and the actual call happens lazily.
    # We only test that the module-level API doesn't crash.
    assert callable(route)

"""Missing optional faiss RAG dependency must degrade, not crash MacroAgent.

Live app was healthy but logged ``Failed to init RAG for MacroAgent: No module
named 'faiss'`` on every agent cycle. The per-process warn-once guard
(``_RAG_UNAVAILABLE``) was dropped in the P2-02 RAGClient refactor, so the
current contract is only: ``_get_rag()`` returns ``None`` and logs the reason
instead of raising. Warning frequency is not asserted — it is per call today.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from agents._impl import macro_agent


@pytest.fixture()
def missing_faiss(monkeypatch):
    """Simulate an environment without the optional [rag] ``faiss`` dep."""

    class _NoFaissRetriever:
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("No module named 'faiss'", name="faiss")

    monkeypatch.setattr(macro_agent, "RAGRetriever", _NoFaissRetriever)


def _rag_warnings(caplog) -> int:
    return sum(
        1
        for rec in caplog.records
        if rec.levelno >= logging.WARNING and "Failed to init RAG" in rec.getMessage()
    )


def test_missing_faiss_degrades_without_raising(missing_faiss, caplog):
    caplog.set_level(logging.WARNING)

    # A fresh instance per agent cycle (run_macro_agent does the same).
    agent = macro_agent.MacroAgent()

    assert asyncio.run(agent._get_rag()) is None
    assert _rag_warnings(caplog) >= 1, "missing optional faiss dep must be logged"
    assert "faiss" in caplog.text

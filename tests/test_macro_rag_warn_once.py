"""Test that a missing optional faiss RAG dependency is logged once per process.

Live app was healthy but logged ``Failed to init RAG for MacroAgent: No module
named 'faiss'`` on every agent cycle, because ``run_macro_agent`` re-instantiates
MacroAgent each cycle and ``_get_rag`` retried the lazy import every time.
"""

from __future__ import annotations

import asyncio
import builtins
import logging
import sys

import pytest

from agents._impl import macro_agent


@pytest.fixture()
def missing_faiss(monkeypatch):
    """Simulate an environment without the optional [rag] ``faiss`` dep."""
    monkeypatch.setattr(macro_agent, "_RAG_UNAVAILABLE", False)

    # Force knowledge.rag_retriever to re-import so the fake faiss failure fires.
    for mod in list(sys.modules):
        if mod == "knowledge.rag_retriever" or mod.startswith("knowledge.rag_retriever."):
            monkeypatch.delitem(sys.modules, mod)

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faiss":
            raise ModuleNotFoundError("No module named 'faiss'", name="faiss")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def _rag_warnings(caplog) -> int:
    return sum(
        1
        for rec in caplog.records
        if rec.levelno >= logging.WARNING and "Failed to init RAG" in rec.getMessage()
    )


def test_missing_faiss_warns_once_across_instances(missing_faiss, caplog):
    caplog.set_level(logging.WARNING)

    # Two separate instances simulate two agent cycles (run_macro_agent
    # re-instantiates MacroAgent per call).
    first = macro_agent.MacroAgent()
    second = macro_agent.MacroAgent()

    assert asyncio.run(first._get_rag()) is None
    assert asyncio.run(second._get_rag()) is None

    assert _rag_warnings(caplog) == 1, (
        "missing optional faiss dep must be warned about exactly once per process"
    )

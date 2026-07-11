"""tests.error_handling — local fixtures.

The root ``tests/conftest.py`` sets ``API_KEY=test-key-123`` so the broader
auth test suite has a stable key. The error-handling HTTP tests, however,
were written against ``test-key`` and assert envelope shape for 4xx/5xx
responses. Force the legacy key here so those assertions keep passing.
"""

from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture(autouse=True)
def _override_api_key(monkeypatch: pytest.MonkeyPatch):
    """Force ``API_KEY=test-key`` for every test in this directory."""
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("API_KEY_AUTH_DISABLED", "false")

    # Drop any cached settings / wsgi modules so the new env is honoured.
    for mod in ("web.wsgi", "core.auth", "core.settings"):
        if mod in sys.modules:
            importlib.sys.modules.pop(mod, None)
    yield

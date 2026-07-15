"""Phase 1 cleanup validation tests."""

import importlib
import pytest


@pytest.mark.unit
def test_core_auth_importable():
    """Проверяем, что core.auth импортируется без ошибок."""
    try:
        importlib.import_module("core.auth")
    except ImportError as e:
        pytest.fail(f"core.auth should be importable: {e}")

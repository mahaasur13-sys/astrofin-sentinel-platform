from __future__ import annotations

import importlib
import pytest


@pytest.mark.unit
def test_db_init_importable():
    try:
        importlib.import_module("db.init")
    except ImportError as e:
        pytest.fail(f"db.init should be importable: {e}")

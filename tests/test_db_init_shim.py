"""Test that `python -m db.init` is a runnable shim delegating to db.__main__.

Regression: `python -m db.init` used to be a no-op because db/init.py had no
``__main__`` block — runpy only imported the module. The shim now delegates to
the real CLI (``db.__main__.main``) so flags and behaviour stay identical to
``python -m db``.
"""

from __future__ import annotations

import runpy
import warnings


def test_db_init_module_delegates_to_db_main(monkeypatch):
    from db import __main__ as db_main

    calls: list[str] = []
    monkeypatch.setattr(db_main, "main", lambda: calls.append("main"))

    # run_name="__main__" reproduces `python -m db.init` (db/init.py as __main__).
    # The known benign runpy RuntimeWarning about a module already in sys.modules
    # is expected here because db/__init__.py eagerly imports db.init.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("db.init", run_name="__main__")

    assert calls == ["main"], (
        "python -m db.init must delegate to db.__main__.main exactly once"
    )

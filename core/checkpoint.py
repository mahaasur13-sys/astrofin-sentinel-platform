"""
AstroFin Sentinel v5 — Project Root Utility
Provides the absolute path to the project root directory.
"""

from __future__ import annotations

from pathlib import Path

_PROJECT_ROOT: Path | None = None


def get_project_root() -> Path:
    """
    Returns the absolute path to the AstroFinSentinelV5 project root.

    Resolves once per process, caching the result.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # This file lives at: <project_root>/core/checkpoint.py
    # Therefore project root is its parent parent
    _PROJECT_ROOT = Path(__file__).parent.parent.resolve()
    return _PROJECT_ROOT

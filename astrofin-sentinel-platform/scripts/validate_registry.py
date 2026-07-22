#!/usr/bin/env python3
"""
scripts/validate_registry.py
============================
Pre-commit hook target: ensure that whenever agents/_impl/ changes, either
the registry (AGENT_AGENTS) or docs/ also changes in the same commit.

Warns (does not fail) — but emits a colored "⚠" line so the developer
notices during `git commit`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_IMPL = "agents/_impl"
_REGISTRY = "agents/gitagent_registry.py"
_DOCS = "docs/"


def _changed_files(scope: str) -> list[str]:
    """Return files changed in the working tree under `scope`."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return [f for f in out.stdout.splitlines() if f.startswith(scope)]


def main() -> int:
    impl_changed = _changed_files(_IMPL)
    registry_changed = _changed_files(_REGISTRY)
    docs_changed = _changed_files(_DOCS)

    if not impl_changed:
        return 0  # nothing under _impl/ changed; no constraint applies

    if registry_changed or docs_changed:
        return 0  # OK: change in _impl/ is accompanied by an update

    impls = "\n    ".join(impl_changed)
    msg = f"⚠  You changed files under {_IMPL}/:\n    {impls}\n  but did not change {_REGISTRY} or {_DOCS}.\n  Did you forget to update AGENT_AGENTS or docs/STATUS.md?"
    if sys.stdout.isatty():
        msg = f"\033[33;1m{msg}\033[0m"
    print(msg)
    return 0  # warn, not fail


if __name__ == "__main__":
    sys.exit(main())

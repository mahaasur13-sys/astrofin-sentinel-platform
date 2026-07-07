"""
tests/architecture/test_architecture_linter.py
==============================================
Tests for the architecture linter.

The linter has two surfaces:
  1. The CLI (`architecture_linter.py`).
  2. The library API (`ArchitectureLinter(ast, src, path).run()`).

We test the library API. The CLI is exercised in CI by running the
script directly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LINTER = REPO_ROOT / "scripts" / "architecture_linter.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def test_linter_passes_on_template():
    """The template is hand-written to be conformant:"""
    rc = subprocess.run(
        [sys.executable, str(LINTER), "agents/_impl/_template_agent.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "R" not in (rc.stdout + rc.stderr) or "Ready" in (rc.stdout + rc.stderr), f"linter should pass on template, got:\n{rc.stdout}\n{rc.stderr}"
    # Either exit 0 (no violations) or non-zero with only warnings.
    # We accept exit 0 in any case.
    assert rc.returncode == 0, f"unexpected exit: {rc.returncode}\n{rc.stdout}"


def test_linter_flags_ephemeris_without_decorator():
    """If a module imports ephemeris but no method has @require_ephemeris, fail."""
    from architecture_linter import ArchitectureLinter, R2_REQUIRE_EPHEMERIS

    src = """
import core.ephemeris as ephemeris

class MyAgent:
    name = "MyAgent"
    domain = "fundamental"
    def run(self, state):
        return ephemeris.get_planetary_positions(...)
"""
    import ast

    tree = ast.parse(src)
    linter = ArchitectureLinter(tree, src, "test.py")
    linter.run()
    codes = {f.code for f in linter.failures}
    assert R2_REQUIRE_EPHEMERIS in codes


def test_linter_flags_orphan_agent():
    """A class with name ending in 'Agent' must inherit BaseAgent."""
    from architecture_linter import ArchitectureLinter, R1_MUST_INHERIT_BASE

    src = """
class OrphanAgent:
    pass
"""
    import ast

    tree = ast.parse(src)
    linter = ArchitectureLinter(tree, src, "test.py")
    linter.run()
    codes = {f.code for f in linter.failures}
    assert R1_MUST_INHERIT_BASE in codes


def test_linter_passes_for_archived_file():
    """Archived files are exempt from the inherit check."""
    from architecture_linter import ArchitectureLinter, R1_MUST_INHERIT_BASE

    src = """
class ArchivedAgent:
    pass
"""
    import ast

    tree = ast.parse(src)
    linter = ArchitectureLinter(tree, src, "agents/_archived/old.py")
    linter.run()
    codes = {f.code for f in linter.failures}
    assert R1_MUST_INHERIT_BASE not in codes


def test_linter_cli_help():
    """CLI --help works."""
    rc = subprocess.run(
        [sys.executable, str(LINTER), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode == 0
    assert "AstroFin architecture linter" in rc.stdout


def test_linter_cli_exit_code_with_violations(tmp_path):
    """When hard rules fail, the script returns non-zero."""
    bad = tmp_path / "bad_agent.py"
    bad.write_text("""
import core.ephemeris as ephemeris
class BadAgent:
    name = "BadAgent"
    domain = "fundamental"
    def run(self, state):
        return ephemeris.get_planetary_positions(...)
""")
    rc = subprocess.run(
        [sys.executable, str(LINTER), str(bad)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode != 0

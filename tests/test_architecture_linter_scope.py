"""Regression tests for architecture rules' intended agent-only scope."""

import ast
from pathlib import Path

from scripts.architecture_linter import (
    REPO_ROOT,
    Report,
    check_base_agent_inheritance,
    check_require_ephemeris,
)


def _path(relative: str) -> Path:
    return REPO_ROOT / relative


def test_r1_ignores_api_schema_named_dashboard_agent() -> None:
    report = Report()
    tree = ast.parse("class DashboardAgent(BaseModel):\n    pass\n")
    check_base_agent_inheritance(tree, _path("api/main.py"), report)
    assert not report.findings


def test_r1_ignores_meta_rl_coordinator_named_meta_agent() -> None:
    report = Report()
    tree = ast.parse("class MetaAgent:\n    pass\n")
    check_base_agent_inheritance(tree, _path("meta_rl/meta_agent.py"), report)
    assert not report.findings


def test_r1_still_checks_agent_implementations() -> None:
    report = Report()
    tree = ast.parse("class ExampleAgent:\n    pass\n")
    check_base_agent_inheritance(
        tree, _path("agents/_impl/architecture_linter_fixture.py"), report
    )
    assert any(f.rule == "R1" for f in report.findings)


def test_r2_ignores_api_handler_using_ephemeris_service() -> None:
    report = Report()
    source = "def get_astro_aspects():\n    get_planetary_positions()\n"
    check_require_ephemeris(
        ast.parse(source), _path("api/main.py"), source, report
    )
    assert not report.findings


def test_r2_still_checks_agent_implementations() -> None:
    report = Report()
    source = (
        "class ExampleAgent:\n"
        "    def analyze(self):\n"
        "        get_planetary_positions()\n"
    )
    check_require_ephemeris(
        ast.parse(source),
        _path("agents/_impl/architecture_linter_fixture.py"),
        source,
        report,
    )
    assert any(f.rule == "R2" for f in report.findings)

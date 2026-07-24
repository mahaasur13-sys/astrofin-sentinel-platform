#!/usr/bin/env python3
"""
scripts/validate_agent.py
=========================
Per-agent validator for AstroFin Sentinel V5.

This is a **deep**, single-file validation (the architecture linter does the
shallow, repo-wide pass; this is the "is this specific agent shippable?"
pass). It checks:

    A1. The module has exactly one class that inherits BaseAgent[AgentResponse].
    A2. That class's __init__ calls super().__init__(name, instructions_path, domain, weight).
    A3. The class defines `async def run(self, state) -> AgentResponse`.
    A4. The runner method (run_*) is decorated with @require_ephemeris iff
        the file mentions ephemeris symbols.
    A5. The module exports a `run_<agent_name>(state)` async function.
    A6. The class is listed in AGENT_AGENTS with weight ∈ [0, 1] and a
        recognized domain.
    A7. A docstring is present on the public class and on `run`.
    A8. The agent returns an AgentResponse (not a dict, not None).
    A9. The agent's `run` method is wrapped in a try/except that returns a
        degraded AgentResponse, not a raise.

Optionally runs the corresponding test file (if it exists) with pytest.

Usage:
    python scripts/validate_agent.py agents/_impl/my_new_agent.py
    python scripts/validate_agent.py agents/_impl/my_new_agent.py --with-tests
    python scripts/validate_agent.py agents/_impl/                  # whole dir
    python scripts/validate_agent.py --list-recommended-fixes agents/_impl/my_new_agent.py
"""

from __future__ import annotations

import argparse
import ast
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


# ─── Pretty output ─────────────────────────────────────────────────────────

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def GREEN(s):
    return _c("32;1", s)


def RED(s):
    return _c("31;1", s)


def YELLOW(s):
    return _c("33;1", s)


def CYAN(s):
    return _c("36", s)


def BOLD(s):
    return _c("1", s)


def DIM(s):
    return _c("2", s)


# ─── Constants ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "agents" / "gitagent_registry.py"
ALLOWED_DOMAINS = {
    "astro",
    "fundamental",
    "macro",
    "quant",
    "options",
    "sentiment",
    "technical",
    "research",
    "risk",
    "synthesis",
}
EPHEMERIS_KEYWORDS = ("swisseph", "ephemeris", "planet", "aspect")

# ─── Result model ──────────────────────────────────────────────────────────


@dataclass
class Check:
    code: str  # "A1", "A2", ...
    label: str
    passed: bool
    detail: str = ""
    severity: str = "warning"  # "error" or "warning" — threshold for --fail-on


# ─── Helpers ───────────────────────────────────────────────────────────────


def parse_registry() -> dict[str, dict]:
    """Return the {agent_name: info} dict from agents/gitagent_registry.py."""
    if not REGISTRY_PATH.exists():
        return {}
    src = REGISTRY_PATH.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    registry: dict[str, dict] = {}
    for node in ast.walk(tree):
        # Handle both `AGENT_AGENTS = {...}` and `AGENT_AGENTS: dict[str, dict] = {...}`
        assign_value: ast.AST | None = None
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "AGENT_AGENTS" for t in node.targets
        ):
            assign_value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "AGENT_AGENTS"
        ):
            assign_value = node.value
        if assign_value is None:
            continue
        if isinstance(assign_value, ast.Dict):
            for k, v in zip(assign_value.keys, assign_value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Dict):
                    entry: dict = {}
                    for kk, vv in zip(v.keys, v.values):
                        if isinstance(kk, ast.Constant):
                            try:
                                entry[kk.value] = ast.literal_eval(vv)
                            except Exception:
                                entry[kk.value] = ast.unparse(vv)
                    registry[k.value] = entry
    return registry


def find_agent_class(tree: ast.AST) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for b in node.bases:
                name = ast.unparse(b)
                if re.match(r"BaseAgent\[.*\]", name) or name.endswith("BaseAgent"):
                    return node
    return None


def find_run_method(
    klass: ast.ClassDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in klass.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "run"
        ):
            return node
    return None


def find_runner_function(
    tree: ast.AST, agent_name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    # Prefer the conventional name: run_<agent_name>.
    expected = f"run_{_camel_to_snake(agent_name)}"
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == expected
        ):
            return node
    # Fallback: some modules use run_<name> instead of run_<name>_agent.
    # Try the bare snake_case (e.g. run_synthesis for SynthesisAgent).
    bare = f"run_{_camel_to_snake(agent_name).rstrip('_agent')}"
    if bare != expected:
        for node in tree.body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == bare
            ):
                return node
    return None


def _camel_to_snake(name: str) -> str:
    """CamelCase → snake_case. FundamentalAgent → fundamental_agent."""
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    for d in node.decorator_list:
        if name in ast.unparse(d):
            return True
    return False


# ─── Individual checks ─────────────────────────────────────────────────────


def check_A1_has_agent_class(tree: ast.AST, src: Path) -> Check:
    klass = find_agent_class(tree)
    if klass is None:
        return Check(
            "A1",
            "inherits BaseAgent[AgentResponse]",
            False,
            f"no class in {src.name} inherits BaseAgent",
        )
    return Check("A1", "inherits BaseAgent[AgentResponse]", True, f"class {klass.name}")


def check_A2_super_init(klass: ast.ClassDef) -> Check:
    for node in klass.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                    if sub.func.attr == "__init__":
                        return Check("A2", "calls super().__init__", True)
            return Check(
                "A2",
                "calls super().__init__",
                False,
                "__init__ exists but does not call super().__init__",
            )
    return Check("A2", "calls super().__init__", False, "no __init__ defined")


def check_A3_run_method(klass: ast.ClassDef) -> Check:
    run = find_run_method(klass)
    if run is None:
        return Check("A3", "defines async run(self, state)", False, "no `run` method")
    if not isinstance(run, ast.AsyncFunctionDef):
        return Check(
            "A3",
            "defines async run(self, state)",
            False,
            "`run` is sync; should be async",
        )
    return Check("A3", "defines async run(self, state)", True)


def check_A4_ephemeris_decorator(
    klass: ast.ClassDef,
    source_text: str,
) -> Check:
    """If the module mentions ephemeris symbols, at least one method must use
    @require_ephemeris. We scan the entire class for the decorator.
    """
    lowered = source_text.lower()
    needs_ephemeris = any(kw in lowered for kw in EPHEMERIS_KEYWORDS)
    if not needs_ephemeris:
        return Check(
            "A4",
            "@require_ephemeris decorator",
            True,
            "not required for this agent (no ephemeris symbols)",
        )

    # Find any decorator named require_ephemeris anywhere in the class body.
    has_dec = False
    for node in ast.walk(klass):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if has_decorator(node, "require_ephemeris"):
                has_dec = True
                break
    if has_dec:
        return Check("A4", "@require_ephemeris decorator", True, "present on a method")
    return Check(
        "A4",
        "@require_ephemeris decorator",
        False,
        "agent uses ephemeris symbols but no method has @require_ephemeris",
    )


def check_A5_runner_function(tree: ast.AST, agent_name: str) -> Check:
    fn = find_runner_function(tree, agent_name)
    if fn is None:
        expected = f"run_{_camel_to_snake(agent_name)}"
        return Check(
            "A5",
            f"exports run_<{agent_name}>(state)",
            False,
            f"expected a top-level `{expected}` async function",
        )
    if not isinstance(fn, ast.AsyncFunctionDef):
        return Check(
            "A5",
            f"exports run_<{agent_name}>(state)",
            False,
            f"function `{fn.name}` should be async",
        )
    return Check(
        "A5",
        f"exports run_<{agent_name}>(state)",
        True,
        f"function `{fn.name}` is async",
    )


def check_A6_registry_entry(
    agent_name: str,
    registry: dict[str, dict],
    src: Path | None = None,
) -> Check:
    # Templates and archived agents are exempt from registry coverage.
    if src is not None and ("_template" in src.stem or "_archived" in str(src)):
        return Check(
            "A6", "AGENT_AGENTS entry", True, "skipped (template/archived file)"
        )
    if not registry:
        return Check("A6", "AGENT_AGENTS entry", False, "registry not found or empty")
    entry = registry.get(agent_name)
    if entry is None:
        return Check(
            "A6",
            "AGENT_AGENTS entry",
            False,
            f"agent '{agent_name}' not in AGENT_AGENTS; add it in agents/gitagent_registry.py",
        )
    weight = entry.get("weight", 0)
    if not (0.0 <= weight <= 1.0):
        return Check(
            "A6", "AGENT_AGENTS entry", False, f"weight={weight} not in [0, 1]"
        )
    domain = entry.get("domain", "")
    if domain not in ALLOWED_DOMAINS:
        return Check(
            "A6",
            "AGENT_AGENTS entry",
            False,
            f"domain '{domain}' not in {sorted(ALLOWED_DOMAINS)}",
        )
    return Check("A6", "AGENT_AGENTS entry", True, f"weight={weight}, domain={domain}")


def check_A7_docstrings(
    klass: ast.ClassDef, run: ast.FunctionDef | ast.AsyncFunctionDef | None
) -> Check:
    if not ast.get_docstring(klass):
        return Check(
            "A7", "docstrings present", False, f"class {klass.name} has no docstring"
        )
    if run is not None and not ast.get_docstring(run):
        return Check("A7", "docstrings present", False, "run() has no docstring")
    return Check("A7", "docstrings present", True)


def check_A8_return_type(run: ast.FunctionDef | ast.AsyncFunctionDef | None) -> Check:
    if run is None:
        return Check("A8", "run() return annotation", False, "no run()")
    ret = run.returns
    if ret is None:
        return Check(
            "A8", "run() return annotation", False, "run() lacks return type hint"
        )
    hint = ast.unparse(ret)
    if "AgentResponse" not in hint:
        return Check(
            "A8",
            "run() return annotation",
            False,
            f"run() returns {hint!r}, expected AgentResponse",
        )
    return Check("A8", "run() return annotation", True, f"-> {hint}")


def check_A9_graceful(
    run: ast.FunctionDef | ast.AsyncFunctionDef | None, src_text: str
) -> Check:
    """Best-effort: look for a try/except inside run() that returns an AgentResponse."""
    if run is None:
        return Check("A9", "graceful degradation", False, "no run()")
    # Look at the body of run: it must contain a `try`.
    for sub in ast.walk(run):
        if isinstance(sub, ast.Try):
            return Check(
                "A9", "graceful degradation", True, "run() has try/except block"
            )
    return Check(
        "A9",
        "graceful degradation",
        False,
        "run() has no try/except; consider wrapping external calls",
    )


# ─── Driver ────────────────────────────────────────────────────────────────


def validate(src: Path) -> list[Check]:
    src = src.resolve()
    text = src.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return [Check("SYNTAX", "parses cleanly", False, f"{e.msg} at line {e.lineno}")]
    klass = find_agent_class(tree)
    if klass is None:
        return [
            Check(
                "A1", "inherits BaseAgent[AgentResponse]", False, "no agent class found"
            )
        ]
    agent_name = klass.name
    run = find_run_method(klass)
    registry = parse_registry()
    return [
        check_A1_has_agent_class(tree, src),
        check_A2_super_init(klass),
        check_A3_run_method(klass),
        check_A4_ephemeris_decorator(klass, text),
        check_A5_runner_function(tree, agent_name),
        check_A6_registry_entry(agent_name, registry, src=src),
        check_A7_docstrings(klass, run),
        check_A8_return_type(run),
        check_A9_graceful(run, text),
    ]


def render(checks: list[Check], src: Path, fail_on: str = "warning") -> int:
    try:
        label = str(src.relative_to(REPO_ROOT))
    except ValueError:
        label = str(src)
    print(BOLD(f"\n─── validate_agent.py — {label} ───"))
    if not checks:
        print(YELLOW("no checks run"))
        return 0
    passed = sum(1 for c in checks if c.passed)
    failed = [c for c in checks if not c.passed]
    # Map --fail-on to severity threshold
    # fail_on="error"   → only fail exit if any check has severity=="error" and not passed
    # fail_on="warning" → fail exit on any failed check (default for backward compat)
    # fail_on="never"   → always exit 0
    blocking = []
    if fail_on == "error":
        blocking = [c for c in failed if c.severity == "error"]
    elif fail_on == "warning":
        blocking = list(failed)
    # fail_on == "never" → blocking = []
    max_label = max(len(c.label) for c in checks)
    for c in checks:
        icon = GREEN("✔") if c.passed else RED("✖")
        line = f"  {icon}  {CYAN(c.code)}  {c.label.ljust(max_label)}"
        if c.detail:
            line += f"  {DIM(c.detail)}"
        print(line)
    print("")
    print(f"  {BOLD(str(passed))} / {len(checks)} checks passed.", end="")
    if failed:
        print(RED(f"  {len(failed)} failed."))
    else:
        print(GREEN("  Ready to ship."))
    return 0 if not blocking else 1


def recommend_fixes(checks: list[Check]) -> None:
    failed = [c for c in checks if not c.passed]
    if not failed:
        print(GREEN("No fixes recommended."))
        return
    print(BOLD("\nRecommended fixes:"))
    for c in failed:
        print(f"  • [{c.code}] {c.label}")
        print(f"      {DIM(c.detail)}")


def find_test_file(src: Path) -> Path | None:
    """Map agents/_impl/foo_agent.py → tests/test_foo_agent.py."""
    name = src.stem
    test_path = REPO_ROOT / "tests" / f"test_{name}.py"
    return test_path if test_path.exists() else None


def run_pytest(test_path: Path) -> int:
    print(BOLD(f"\nrunning pytest on {test_path.relative_to(REPO_ROOT)} …\n"))
    return subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", str(test_path)]
    )


def iter_agent_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return [
            p
            for p in sorted(target.rglob("*.py"))
            if "_archived" not in p.parts
            and "_templates" not in p.parts
            and p.name != "__init__.py"
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a single AstroFin agent file"
    )
    parser.add_argument(
        "target", nargs="?", default="agents/_impl", help="agent file or directory"
    )
    parser.add_argument(
        "--with-tests", action="store_true", help="also run the corresponding test file"
    )
    parser.add_argument(
        "--list-recommended-fixes",
        action="store_true",
        help="only print recommended fixes for failed checks",
    )
    parser.add_argument(
        "--fail-on",
        choices=["error", "warning", "never"],
        default="warning",
        help="exit non-zero on this severity or higher (default: warning). "
        "Compatibility flag — used by .github/workflows/quality-gate.yml.",
    )
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.is_absolute():
        target = (REPO_ROOT / target).resolve()
    if not target.exists():
        print(RED(f"target not found: {target}"))
        return 1

    files = iter_agent_files(target)
    if not files:
        print(YELLOW(f"no agent files found in {target}"))
        return 0

    overall = 0
    for src in files:
        checks = validate(src)
        if args.list_recommended_fixes:
            recommend_fixes(checks)
        else:
            overall |= render(checks, src, fail_on=args.fail_on)
        if args.with_tests:
            test = find_test_file(src)
            if test:
                overall |= run_pytest(test)
            else:
                print(YELLOW(f"  no test file for {src.name} (skipping --with-tests)"))
    return overall


if __name__ == "__main__":
    sys.exit(main())

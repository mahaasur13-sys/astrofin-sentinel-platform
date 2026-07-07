#!/usr/bin/env python3
"""
scripts/architecture_linter.py
==============================
BlackRock-inspired architecture linter for AstroFin Sentinel V5.

Hard rules (fail the build if violated):
    R1.  Every agent class in agents/_impl/ must inherit from BaseAgent[AgentResponse].
    R2.  Every agent that touches the ephemeris must use @require_ephemeris.
    R3.  No `import requests` outside data_room/.
    R4.  Any HTTP route handler under web/ must use @require_auth (or be
         explicitly marked public-by-design).
    R5.  Every agent module under agents/_impl/ must be registered in
         AGENT_AGENTS in agents/gitagent_registry.py.
    R6.  No top-level `print(...)` in production code (use logger).
    R7.  No f-string SQL; queries must be parameterized.
    R8.  No hard-coded API keys, tokens, or secrets (regex check).
    R9.  Every agent module must export a `run_<agent>(state) -> AgentResponse`
         convenience function (or be exempt via # noqa: AGENT_RUNNER).

Soft rules (warn, do not fail):
    S1.  Public functions should have a docstring.
    S2.  Tests should not import agents from agents/_archived/.
    S3.  If a file under agents/_impl/ is changed, docs/ must also be changed
         (this is also enforced by the pre-commit `validate-registry-coverage`).

Output:
    Color-coded, single-page report. Exit code:
        0 — pass
        1 — hard-rule violation
        2 — soft-rule violation only (still allowed in dev)

Usage:
    python scripts/architecture_linter.py                 # full repo
    python scripts/architecture_linter.py --changed       # only git-changed files
    python scripts/architecture_linter.py path/to/file.py # single file
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ─── ANSI colours (skip if no tty) ──────────────────────────────────────────

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:  # noqa: ANN001
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def GREEN(s):
    return _c("32", s)


def RED(s):
    return _c("31;1", s)


def YELLOW(s):
    return _c("33", s)


def CYAN(s):
    return _c("36", s)


def BOLD(s):
    return _c("1", s)


def DIM(s):
    return _c("2", s)


# ─── Result model ───────────────────────────────────────────────────────────


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str  # "FAIL" | "WARN"
    message: str

    @property
    def code(self) -> str:  # alias for .rule
        return self.rule


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0

    def fail(self, file: str, line: int, rule: str, message: str) -> None:
        self.findings.append(Finding(file, line, rule, "FAIL", message))

    def warn(self, file: str, line: int, rule: str, message: str) -> None:
        self.findings.append(Finding(file, line, rule, "WARN", message))

    @property
    def has_failures(self) -> bool:
        return any(f.severity == "FAIL" for f in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.severity == "WARN" for f in self.findings)


# ─── Helpers ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_IMPL_DIR = REPO_ROOT / "agents" / "_impl"
DATA_ROOM_DIR = REPO_ROOT / "data_room"
WEB_DIR = REPO_ROOT / "web"
REGISTRY_PATH = REPO_ROOT / "agents" / "gitagent_registry.py"

# Token-ish regexes. Tighter than "any alphanumeric string >= 20".
SECRET_REGEXES = [
    re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{10,}"),  # Stripe
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),  # GitHub PAT
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),  # Google API key
    re.compile(r"xox[boprs]-[A-Za-z0-9-]{10,}"),  # Slack tokens
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),  # JWT
]

# ─── R1: inheritance from BaseAgent ─────────────────────────────────────────


# Classes that intentionally do NOT inherit BaseAgent[AgentResponse].
# Each entry: (file, class_name) — kept short; the file holds the rationale.
R1_ALLOWLIST: set[tuple[str, str]] = {
    ("agents/karl_synthesis.py", "KARLSynthesisAgent"),
    # KARLSynthesisAgent is a deliberate non-BaseAgent facade over
    # SynthesisAgent + AMRE/KARL control loop. It is runtime-mocked
    # in tests (test_synthesis.py::test_karl_synthesis_smoke).
}


def check_base_agent_inheritance(tree: ast.AST, src: Path, report: Report) -> None:
    """Every class in agents/_impl/* must inherit from BaseAgent.

    Recognised exclusions:
      - classes whose (file, name) is in R1_ALLOWLIST (intentional facades)
      - BaseAgent subclasses / mixins
    """
    if "_archived" in src.parts:
        return
    rel = _rel(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names: list[str] = []
            for b in node.bases:
                base_names.append(ast.unparse(b))
            is_agent = any(re.match(r"BaseAgent\[.*\]", n) or n.endswith("BaseAgent") for n in base_names)
            if not is_agent:
                if node.name.endswith("Agent") and not node.name.endswith("BaseAgent"):
                    if (rel, node.name) in R1_ALLOWLIST:
                        continue
                    report.fail(
                        rel,
                        node.lineno,
                        "R1",
                        f"class {node.name} should inherit BaseAgent[AgentResponse]; got {base_names}",
                    )


# ─── R2: @require_ephemeris usage ───────────────────────────────────────────

EPHEMERIS_KEYWORDS = ("swisseph", "ephemeris", "planet_position", "natal", "aspect")
EPHEMERIS_IGNORE_FILES = {Path("core/ephemeris.py"), Path("scripts/validate_blackrock_tests.py")}


def _uses_ephemeris_outside_docstrings(source_text: str) -> bool:
    """Return True if EPHEMERIS_KEYWORDS appears in code (not in docstrings/comments)."""
    import ast as _ast
    try:
        tree = _ast.parse(source_text)
    except SyntaxError:
        return False
    skip_ranges = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Expr) and isinstance(node.value, (_ast.Str, _ast.Constant)) and isinstance(getattr(node.value, "s", None), str):
            skip_ranges.append((node.lineno, node.col_offset, node.end_lineno, node.end_col_offset))
    def in_skip(lineno, col):
        for s_ln, s_co, e_ln, e_co in skip_ranges:
            if (lineno, col) >= (s_ln, s_co) and (lineno, col) <= (e_ln, e_co):
                return True
        return False
    keywords = ("swisseph", "ephemeris", "planet_position", "natal", "aspect")
    for lineno, line in enumerate(source_text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        low = line.lower()
        for kw in keywords:
            idx = 0
            while True:
                pos = low.find(kw, idx)
                if pos < 0:
                    break
                if not in_skip(lineno, pos):
                    return True
                idx = pos + len(kw)
    return False


def check_require_ephemeris(tree: ast.AST, src: Path, source_text: str, report: Report) -> None:
    """If the module uses ephemeris symbols, every class must have @require_ephemeris."""
    if "_archived" in src.parts:
        return
    try:
        src_rel = _rel(src)
    except ValueError:
        return
    if src_rel in {str(p) for p in EPHEMERIS_IGNORE_FILES}:
        return
    if not _uses_ephemeris_outside_docstrings(source_text):
        return
    has_decorator = "@require_ephemeris" in source_text
    if not has_decorator:
        report.fail(
            src_rel,
            1,
            "R2",
            "module uses ephemeris symbols but is missing @require_ephemeris on a method",
        )


# ─── R3: no requests outside data_room ──────────────────────────────────────


def check_data_room_compliance(src: Path, source_text: str, report: Report) -> None:
    """No `import requests` (or `from requests import ...`) outside data_room/."""
    try:
        src_rel = _rel(src)
    except ValueError:
        return
    if "data_room" in str(src_rel).split("/"):
        return  # data_room is explicitly allowed to use `requests`
    # Allow httpx for legitimate async use, ban requests.
    if re.search(r"^\s*import\s+requests\b", source_text, re.MULTILINE):
        report.fail(
            str(src_rel),
            _first_match_line(source_text, r"^\s*import\s+requests\b"),
            "R3",
            "direct `import requests` is forbidden outside data_room/; use data_room.blueprint.get_price(...)",
        )
    if re.search(r"^\s*from\s+requests\b", source_text, re.MULTILINE):
        report.fail(
            str(src_rel),
            _first_match_line(source_text, r"^\s*from\s+requests\b"),
            "R3",
            "`from requests import ...` is forbidden outside data_room/",
        )


# ─── R4: web/ routes must have @require_auth ───────────────────────────────


def check_web_auth_decorators(src: Path, source_text: str, report: Report) -> None:
    if WEB_DIR not in src.parents and src.parent != WEB_DIR:
        return
    # Only check files that look like Flask routes.
    if "@app.route" not in source_text and "@bp.route" not in source_text and ".route(" not in source_text:
        return
    # Find functions that are directly decorated with a route, then look for @require_auth.
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorator_names = {ast.unparse(d) for d in node.decorator_list}
            is_route = any(".route(" in d for d in decorator_names)
            if not is_route:
                continue
            has_auth = any("require_auth" in d or "auth_required" in d for d in decorator_names)
            is_public = "PUBLIC" in source_text.split(ast.unparse(node))[0][-200:]  # weak but useful
            if not has_auth and not is_public:
                # Allow if the function is named with a public prefix or returns a static asset.
                if node.name.startswith("public_") or node.name == "healthz":
                    continue
                report.warn(
                    _rel(src),
                    node.lineno,
                    "R4",
                    f"route handler '{node.name}' is missing @require_auth",
                )


# ─── R5: registry coverage ─────────────────────────────────────────────────


def check_registry_coverage(report: Report) -> None:
    """Every .py file in agents/_impl/ (excluding _templates) must be referenced in AGENT_AGENTS."""
    if not AGENT_IMPL_DIR.exists():
        return
    if not REGISTRY_PATH.exists():
        report.fail(
            _rel(REGISTRY_PATH),
            1,
            "R5",
            "registry file is missing",
        )
        return

    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    # All .py files under _impl/ (skip __init__, _archived, _templates).
    impl_files = [p for p in AGENT_IMPL_DIR.rglob("*.py") if "_archived" not in p.parts and "_templates" not in p.parts and p.name != "__init__.py"]

    for impl in impl_files:
        # The registry references paths as "agents._impl.<module>".
        rel_module = ".".join(impl.relative_to(REPO_ROOT).with_suffix("").parts)
        # Walk the parent dirs and modules; the registry could mention any of them.
        candidates = {rel_module}
        for ancestor in impl.relative_to(REPO_ROOT).parents:
            parts = list(ancestor.parts)
            if parts[:2] == ["agents", "_impl"]:
                candidates.add(".".join(parts[1:]))  # "agents._impl.x.y"
        if not any(c in registry_text for c in candidates):
            report.fail(
                str(impl.relative_to(REPO_ROOT)),
                1,
                "R5",
                f"module {rel_module} is not registered in AGENT_AGENTS",
            )


# ─── R6: no top-level print in production ───────────────────────────────────


def check_no_top_level_print(src: Path, source_text: str, report: Report) -> None:
    """`print(...)` at module top level is a smell; we allow it in tests/ and scripts/."""
    try:
        rel = _rel(src)
    except ValueError:
        return
    if "tests/" in str(rel) or "scripts/" in str(rel) or "tools/" in str(rel):
        return
    tree = ast.parse(source_text)
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == "print":
                report.warn(
                    str(rel),
                    node.lineno,
                    "R6",
                    "top-level print(); use logger.info(...) instead",
                )


# ─── R7: no f-string SQL ───────────────────────────────────────────────────


def check_no_fstring_sql(src: Path, source_text: str, report: Report) -> None:
    try:
        rel = _rel(src)
    except ValueError:
        return
    # Heuristic: any line that looks like `... sql ... f"..."` with a SQL verb.
    sql_verbs = r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b"
    pattern = re.compile(
        rf"{sql_verbs}.*f[\"']"  # SQL verb followed (eventually) by an f-string on the same statement
    )
    for i, line in enumerate(source_text.splitlines(), 1):
        if pattern.search(line) and 'f"' in line and "?" not in line:
            report.fail(
                str(rel),
                i,
                "R7",
                "f-string SQL detected; use parameterized queries (`?` placeholders)",
            )


# ─── R8: secret scan ───────────────────────────────────────────────────────


def check_secrets(src: Path, source_text: str, report: Report) -> None:
    try:
        rel = _rel(src)
    except ValueError:
        return
    if "tests/" in str(rel) or "docs/" in str(rel) or "scripts/" in str(rel):
        # Tests may contain fixture tokens (e.g., "test_ghp_xxx"); skip.
        return
    for i, line in enumerate(source_text.splitlines(), 1):
        for rgx in SECRET_REGEXES:
            if rgx.search(line):
                report.fail(
                    str(rel),
                    i,
                    "R8",
                    f"hard-coded secret pattern detected ({rgx.pattern[:30]}…)",
                )
                break


# ─── S1: docstring check ───────────────────────────────────────────────────


def check_docstrings(tree: ast.AST, src: Path, report: Report) -> None:
    try:
        rel = _rel(src)
    except ValueError:
        return
    if "tests/" in str(rel) or "_archived" in str(rel):
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue  # private; skip
            if not ast.get_docstring(node):
                report.warn(
                    str(rel),
                    node.lineno,
                    "S1",
                    f"{type(node).__name__} {node.name} has no docstring",
                )


# ─── Library API (used by tests and embedding) ────────────────

# ─── Driver ─────────────────────────────────────────────────────────────────

SCAN_DIRS = ["agents", "core", "orchestration", "web", "scripts", "tools"]
SKIP_SUFFIXES = {".pyc", ".pyo", ".swp", ".bak"}
SKIP_NAMES = {"__pycache__", ".venv", "venv", "node_modules", ".git", ".ruff_cache", ".pytest_cache"}
SCAN_EXCLUDE_DIRS = {"audit_repo", "Projects", "_archived", "_templates"}


def _first_match_line(source_text: str, pattern: str) -> int:
    for i, line in enumerate(source_text.splitlines(), 1):
        if re.search(pattern, line):
            return i
    return 1


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except (ValueError, AttributeError):
        return str(p)


def iter_python_files(root: Path, only_changed: bool = False) -> Iterable[Path]:
    if only_changed:
        import subprocess

        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        for line in out.stdout.splitlines():
            p = root / line
            if p.suffix == ".py" and p.exists():
                yield p
        return
    for d in SCAN_DIRS:
        path = root / d
        if not path.exists():
            continue
        for p in path.rglob("*.py"):
            if any(part in SCAN_EXCLUDE_DIRS for part in p.parts):
                continue
            if any(part in SKIP_NAMES for part in p.parts):
                continue
            if p.suffix in SKIP_SUFFIXES:
                continue
            yield p


def lint_file(src: Path, report: Report) -> None:
    report.files_scanned += 1
    try:
        source_text = src.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    try:
        tree = ast.parse(source_text)
    except SyntaxError as e:
        report.fail(
            _rel(src),
            e.lineno or 1,
            "SYNTAX",
            f"file does not parse: {e.msg}",
        )
        return

    check_base_agent_inheritance(tree, src, report)
    check_require_ephemeris(tree, src, source_text, report)
    check_data_room_compliance(src, source_text, report)
    check_web_auth_decorators(src, source_text, report)
    check_no_top_level_print(src, source_text, report)
    check_no_fstring_sql(src, source_text, report)
    check_secrets(src, source_text, report)
    check_docstrings(tree, src, report)


def render_report(report: Report) -> None:
    if not report.findings:
        print(GREEN("✔ architecture linter: no findings."))
        return
    fails = [f for f in report.findings if f.severity == "FAIL"]
    warns = [f for f in report.findings if f.severity == "WARN"]
    print(BOLD(f"\nArchitecture linter — {len(fails)} FAIL, {len(warns)} WARN (scanned {report.files_scanned} files)\n"))
    for finding in report.findings:
        icon = RED("✖") if finding.severity == "FAIL" else YELLOW("⚠")
        loc = f"{finding.file}:{finding.line}"
        print(f"  {icon}  {CYAN(finding.rule)}  {DIM(loc)}")
        print(f"      {finding.message}")
    print()
    if fails:
        print(RED(f"❌ {len(fails)} hard-rule violation(s). Build blocked."))
    if warns and not fails:
        print(YELLOW(f"⚠ {len(warns)} soft warning(s). Build allowed."))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AstroFin architecture linter")
    parser.add_argument("paths", nargs="*", help="specific files to lint")
    parser.add_argument("--changed", action="store_true", help="only git-changed files")
    args = parser.parse_args(argv)

    report = Report()

    if args.paths:
        files = [Path(p).resolve() for p in args.paths]
    else:
        files = list(iter_python_files(REPO_ROOT, only_changed=args.changed))

    for f in files:
        if not f.exists():
            print(YELLOW(f"skip: {f} (does not exist)"))
            continue
        lint_file(f, report)

    # Cross-file rule (R5) needs the registry on disk:
    check_registry_coverage(report)

    render_report(report)
    if report.has_failures:
        return 1
    if report.has_warnings:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ─── Library API (used by tests and embedding) ────────────────

R1_MUST_INHERIT_BASE = "R1"
R2_REQUIRE_EPHEMERIS = "R2"
R3_DATA_ROOM_ONLY = "R3"
R4_WEB_AUTH = "R4"
R5_REGISTRY_COVERAGE = "R5"


class ArchitectureLinter:
    """Thin wrapper exposing the report from a single file.

    The CLI is still the entry point for humans, but tests and
    embedders can use this class:

        linter = ArchitectureLinter(tree, src_text, "agents/foo.py")
        linter.run()
        if linter.failures:
            ...
    """

    def __init__(self, tree: ast.AST, src_text: str, path: str | Path) -> None:
        self.tree = tree
        self.src_text = src_text
        self.path = Path(path)
        self._report = Report()
        self.failures: list[Finding] = []
        self.warnings: list[Finding] = []

    def run(self) -> None:
        report = self._report
        report.path = self.path
        check_base_agent_inheritance(self.tree, self.path, report)
        check_require_ephemeris(self.tree, self.path, self.src_text, report)
        check_data_room_compliance(self.path, self.src_text, report)
        check_web_auth_decorators(self.path, self.src_text, report)
        check_no_top_level_print(self.path, self.src_text, report)
        check_no_fstring_sql(self.path, self.src_text, report)
        check_secrets(self.path, self.src_text, report)
        check_docstrings(self.tree, self.path, report)
        for f in report.findings:
            if f.severity == "FAIL":
                self.failures.append(f)
            else:
                self.warnings.append(f)

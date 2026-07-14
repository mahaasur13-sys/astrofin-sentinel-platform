#!/usr/bin/env python3
"""verify_workspace_root.py — atom-federation-os v9.0 WORKSPACE CONSISTENCY GATE

Diagnoses and enforces: one canonical repo root, consistent sys.path, no shadowed modules.

RUN AS: python scripts/verify_workspace_root.py
EXIT: 0 = clean, 1 = violations, 2 = internal error

Canonical root: /home/workspace/atom-federation-os
"""
from __future__ import annotations

import importlib
import os
import pathlib
import sys

CANONICAL = pathlib.Path("/home/workspace/atom-federation-os").resolve()
SCRIPTS_DIR = CANONICAL / "scripts"
TOOLS_DIR = CANONICAL / "tools"

errors: list[str] = []
warnings: list[str] = []


def diagnose():
    """Print diagnostic info."""
    print("=== WORKSPACE DIAGNOSTIC ===")
    print(f"  canonical root: {CANONICAL}")
    print(f"  cwd:           {pathlib.Path.cwd()}")
    print(f"  canonical exists: {CANONICAL.exists()}")
    print()
    print("  sys.path (first 8 entries):")
    for i, p in enumerate(sys.path[:8]):
        print(f"    [{i}] {p}")
    print()
    print("  canonical children:")
    for d in sorted(CANONICAL.iterdir()):
        if d.name not in ("__pycache__", ".git", "node_modules"):
            print(f"    {d.name}/")
    print()


def _import_with_path(name: str, *extra_paths: str) -> tuple | None:
    """
    Import a module trying extra paths first.
    Returns (module, path_used) or None on failure.
    """
    # Save original path
    orig = sys.path[:]
    hits: list[tuple[str, str]] = []  # (path, module_name)

    for extra in list(extra_paths) + [""]:
        if extra:
            if extra not in sys.path:
                sys.path.insert(0, extra)
        try:
            importlib.import_module(name)
            hits.append((extra or "(sys.path)", name))
        except ImportError:
            pass
        finally:
            sys.path[:] = orig

    if not hits:
        return None
    return hits[0]  # return first successful


def assert_single_root() -> None:
    """Fail if modules load from multiple conflicting roots."""
    # We know these two canonical scripts exist; try to import them
    validators = {
        "execution_algebra_validator": str(SCRIPTS_DIR),
        "symbolic_execution_checker": str(TOOLS_DIR),
    }
    seen_roots: dict[str, list[str]] = {}

    for mod_name, expected_dir in validators.items():
        mod = None
        saved = sys.path[:]
        try:
            if expected_dir not in sys.path:
                sys.path.insert(0, expected_dir)
            mod = importlib.import_module(mod_name)
        except ImportError:
            warnings.append(
                f"  {mod_name}: not importable from {expected_dir} (may be stale)"
            )
        finally:
            sys.path[:] = saved

        if mod is None:
            continue

        mod_file = getattr(mod, "__file__", None)
        if mod_file is None:
            warnings.append(f"  {mod_name}: __file__ is None")
            continue

        mod_root = pathlib.Path(mod_file).resolve().parent
        if "atom-federation-os" not in str(mod_root):
            errors.append(f"  {mod_name}: loaded outside canonical root: {mod_root}")
            continue

        idx = str(mod_root).find("atom-federation-os")
        root_before = str(mod_root)[:idx].rstrip("/") or "/home/workspace"
        if root_before not in seen_roots:
            seen_roots[root_before] = []
        seen_roots[root_before].append(mod_name)

    if len(seen_roots) > 1:
        for root, modules in seen_roots.items():
            for m in modules:
                errors.append(f"  Module '{m}' loaded from alternate root: {root}")
    elif len(seen_roots) == 1:
        root = list(seen_roots.keys())[0]
        if root not in ("/home/workspace", "/home/workspace/"):
            errors.append(f"  All modules load from non-canonical root: {root}")
    elif not seen_roots and not warnings:
        warnings.append("  No tracked modules could be imported")


def check_shadowing() -> None:
    """Detect duplicate .py files across sys.path directories."""
    print("=== SHADOW IMPORT CHECK ===")
    name_to_files: dict[str, list[str]] = {}
    for path_str in sys.path:
        if not path_str or not pathlib.Path(path_str).exists():
            continue
        p = pathlib.Path(path_str)
        if not p.is_dir():
            continue
        for f in p.glob("*.py"):
            key = f.stem
            if key not in name_to_files:
                name_to_files[key] = []
            name_to_files[key].append(str(f))
    for name, files in sorted(name_to_files.items()):
        if len(files) > 1:
            errors.append(f"  SHADOWED: '{name}' in {len(files)} locations: {files}")
    if not errors:
        print("  No shadow imports detected.")


def check_sys_path_order() -> None:
    """Warn if '' (cwd) comes before canonical paths in sys.path."""
    print("=== SYSPATH ORDER CHECK ===")
    canonical = [str(CANONICAL), str(SCRIPTS_DIR), str(TOOLS_DIR)]
    empty_idx = len(sys.path)
    try:
        empty_idx = sys.path.index("")
    except ValueError:
        pass
    first_canon = len(sys.path)
    for cp in canonical:
        if cp in sys.path:
            idx = sys.path.index(cp)
            if idx < first_canon:
                first_canon = idx
    print(f"  First canonical path at: {first_canon}")
    print(f"  Empty string (cwd) at:   {empty_idx if empty_idx < len(sys.path) else 'not found'}")
    if empty_idx < first_canon:
        warnings.append(
            f"  '' (cwd) at [{empty_idx}] before canonical at [{first_canon}]. "
            "Stale modules may shadow real ones. Fix: chdir to repo root before imports."
        )


def check_ci_environment() -> None:
    """Warn if CI env vars are not set."""
    print("=== CI ENVIRONMENT ===")
    checks = [
        ("PYTHONPATH", "/home/workspace/atom-federation-os"),
        ("ATOM_REPO_ROOT", str(CANONICAL)),
    ]
    for var, expected in checks:
        val = os.environ.get(var, "")
        if not val:
            warnings.append(f"  {var} not set (expected: {expected})")
        elif val != expected:
            warnings.append(f"  {var}={val} (expected: {expected})")
        else:
            print(f"  {var}={val} ✓")


def main() -> int:
    print("╔══════════════════════════════════════════════════════╗")
    print("║  atom-federation-os v9.0 — WORKSPACE CONSISTENCY  ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    diagnose()
    check_sys_path_order()
    print()
    check_shadowing()
    print()
    assert_single_root()
    print()
    check_ci_environment()
    print()
    print("═══════════════════════════════════════")
    if errors:
        print(f"❌ FAIL — {len(errors)} error(s):")
        for e in errors:
            print(e)
        if warnings:
            print(f"\n⚠️  {len(warnings)} warning(s):")
            for w in warnings:
                print(w)
        return 1
    if warnings:
        print(f"⚠️  {len(warnings)} warning(s):")
        for w in warnings:
            print(w)
        print("\n✅ PASS — workspace functional")
        return 0
    print("✅ PASS — workspace fully consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())

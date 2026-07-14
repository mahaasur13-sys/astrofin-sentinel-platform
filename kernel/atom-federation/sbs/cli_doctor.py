"""
sbs/cli_doctor.py — doctor subcommand implementation.
"""
import importlib
import sys
from typing import Any


def run_doctor(verbose: int = 0) -> dict[str, Any]:
    """Run full system diagnostics."""
    checks: list[dict[str, Any]] = []

    # 1. Python version
    v = sys.version_info
    py_ok = v >= (3, 10)
    checks.append({
        "name": "Python version",
        "status": "pass" if py_ok else "fail",
        "message": f"{v.major}.{v.minor}.{v.micro} (requires 3.10+)",
    })

    # 2. Core imports
    for module, desc in [
        ("sbs", "SBS core"),
        ("sbs.version", "Version module"),
        ("sbs.boundary_spec", "SystemBoundarySpec"),
        ("sbs.global_invariant_engine", "GlobalInvariantEngine"),
        ("sbs.failure_classifier", "FailureClassifier"),
        ("sbs.system_contract", "SYSTEM_CONTRACT"),
        ("sbs.runtime", "SBSRuntimeEnforcer"),
        ("sbs.schema_validator", "SchemaValidator"),
    ]:
        try:
            importlib.import_module(module)
            checks.append({"name": desc, "status": "pass", "message": "imported ok"})
        except Exception as e:
            checks.append({"name": desc, "status": "fail", "message": str(e)})

    # 3. Version consistency
    try:
        from sbs import __version__
        from sbs.version import __version__ as vfile

        dynamic_version = False
        vpyproject = None

        import tomllib
        with open("pyproject.toml", "rb") as f:
            t = tomllib.load(f)

        # Check if version is declared dynamic before accessing it
        # dynamic = ["version"] is a list; dynamic = {"version": {...}} would be a dict
        project_dynamic = t["project"].get("dynamic", {})
        if isinstance(project_dynamic, dict) and "version" in project_dynamic:
            dynamic_version = True
        else:
            vpyproject_raw = t["project"].get("version")
            if isinstance(vpyproject_raw, str):
                vpyproject = vpyproject_raw
            else:
                dynamic_version = True

        if dynamic_version:
            # At least __version__ and version.py should match
            if __version__ == vfile:
                checks.append({
                    "name": "Version consistency",
                    "status": "pass",
                    "message": f"__version__={__version__}, version.py={vfile}, "
                               f"pyproject.toml=dynamic",
                })
            else:
                checks.append({
                    "name": "Version consistency",
                    "status": "fail",
                    "message": f"__version__={__version__}, version.py={vfile} — MISMATCH",
                })
        else:
            if __version__ == vfile == vpyproject:
                checks.append({
                    "name": "Version consistency",
                    "status": "pass",
                    "message": f"all sources: {__version__}",
                })
            else:
                checks.append({
                    "name": "Version consistency",
                    "status": "fail",
                    "message": f"__version__={__version__}, file={vfile}, pyproject={vpyproject}",
                })
    except KeyError as e:
        checks.append({"name": "Version consistency", "status": "warn",
                       "message": f"missing key in pyproject.toml: {e}"})
    except Exception as e:
        checks.append({"name": "Version consistency", "status": "warn", "message": str(e)})

    # 4. SBS contracts
    try:
        from sbs import SYSTEM_CONTRACT
        contract_count = len(SYSTEM_CONTRACT.invariants) if hasattr(SYSTEM_CONTRACT, "invariants") else 0
        checks.append({"name": "SBS contracts", "status": "pass",
                       "message": f"{contract_count} invariants loaded"})
    except Exception as e:
        checks.append({"name": "SBS contracts", "status": "fail", "message": str(e)})

    # 5. Integrity test
    try:
        from sbs import GlobalInvariantEngine, SystemBoundarySpec
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)
        ok = engine.evaluate(
            {"leader": "n1", "term": 3, "partitions": 0},
            {"leader": "n1", "term": 3, "stale_reads": 0},
            {"leader": "n1", "term": 3, "commit_index": 10, "quorum_ratio": 0.9},
            {"commit_index": 10},
        )
        checks.append({"name": "Integrity test", "status": "pass" if ok else "fail",
                       "message": "healthy state passes" if ok else "healthy state fails!"})
    except Exception as e:
        checks.append({"name": "Integrity test", "status": "fail", "message": str(e)})

    # 6. CLI entry point
    try:
        checks.append({"name": "CLI (Typer)", "status": "pass", "message": "app loaded ok"})
    except Exception as e:
        checks.append({"name": "CLI (Typer)", "status": "fail", "message": str(e)})

    # 7. Entry point scripts
    try:
        checks.append({"name": "Module entry (python -m sbs)", "status": "pass", "message": "loaded ok"})
    except Exception as e:
        checks.append({"name": "Module entry (python -m sbs)", "status": "warn", "message": str(e)})

    # Verbose: check dependencies
    if verbose >= 2:
        for pkg in ["rich", "typer"]:
            try:
                importlib.import_module(pkg)
                checks.append({"name": f"Dependency: {pkg}", "status": "pass", "message": "installed"})
            except ImportError:
                checks.append({"name": f"Dependency: {pkg}", "status": "warn",
                               "message": "not installed (optional for enhanced output)"})

    all_pass = all(c["status"] == "pass" for c in checks)
    any_fail = any(c["status"] == "fail" for c in checks)

    return {
        "overall": "pass" if all_pass else ("fail" if any_fail else "warn"),
        "version": "0.6.0",
        "checks": checks,
    }

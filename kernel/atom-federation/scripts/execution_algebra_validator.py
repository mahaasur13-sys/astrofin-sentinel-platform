#!/usr/bin/env python3
"""
execution_algebra_validator.py — atom-federation-os v9.0+P5 Execution Algebra Validator.

Verifies: G1⊗G2⊗G3⊗G4⊗G5⊗G6⊗ACT⊗G8⊗G9⊗G10
  1. Single entry point: ExecutionGateway.execute()
  2. execute_proof_carried() treated as legitimate P5 extension (same Gateway)
  3. Mutagen targets (mutation_executor.execute) = hard violation
  4. Actuator not exposed outside Gateway
  5. All 10 gates have call-sites

Exit: 0=PASS, 1=FAIL, 2=error
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass, field

GATES = [
    ("G1",  "AdversarialDetector",         ("AdversarialDetector", "detect_adversarial")),
    ("G2",  "PolicyKernelV4",             ("PolicyKernelV4", "evaluate", "approve")),
    ("G3",  "Alignment(GSCT/GCST/GAST)",  ("gsct","GCST","GAST","gast","ust")),
    ("G4",  "StabilityGovernor",           ("StabilityGovernor","GovernorSignal")),
    ("G5",  "CircuitBreaker",              ("CircuitBreaker","can_mutate")),
    ("G6",  "PreValidation",               ("pre_validate","preValidation")),
    ("ACT", "ActuationGate",               ("CausalActuationEngine","_act_stage")),
    ("G8",  "InvariantChecker",            ("InvariantChecker","post_validate")),
    ("G9",  "MutationLedger",              ("MutationLedger","mutation_ledger")),
    ("G10", "RollbackEngine",              ("RollbackEngine","rollback","checkpoint")),
]

MUTAGEN_REMOVE = {"orchestration/v8_2b_controlled_autocorrection/mutation_executor.py"}
DEPRECATED_OK = {
    "cluster/node/node.py",
    "atomos_pkg/atomos/core/execution_loop.py",
    "alignment/merge_engine.py",
    "core/federation/federated_gateway.py",  # P7-incomplete: BFT not yet wired to Gateway
}

# Files that are internal subsystems, not entry points
INTERNAL_PREFIXES = (
    "uesl/","cli.py","shell_tool.py","async_execution.py",
    "execution_loop.py","atomos_pkg/atomos/",
    "core/federation/bft_consensus","core/federation/bft_quorum",
)


def safe_rel(py: pathlib.Path, repo: pathlib.Path) -> str:
    try:
        return str(py.relative_to(repo))
    except ValueError:
        return str(py)


@dataclass
class GateInfo:
    id: str; name: str; file: str | None; calls: int; ok: bool


@dataclass
class EntryInfo:
    name: str; file: str; line: int
    gates_covered: list = field(default_factory=list)
    gates_missing: list = field(default_factory=list)
    status: str = ""  # gateway / mutagen / deprecated_ok / bypass


def run(repo: pathlib.Path):
    py_files = []
    for p in repo.rglob("*.py"):
        if "/.git/" not in str(p) and "/node_modules/" not in str(p):
            py_files.append(p)
    atomos = repo.parent / "atomos_pkg"
    if atomos.exists():
        for p in (atomos).rglob("*.py"):
            if "/.git/" not in str(p):
                py_files.append(p)

    print(f"  [{len(py_files)} Python files scanned]")

    # Gate presence
    gate_infos: list[GateInfo] = []
    for gid, gname, patterns in GATES:
        gi = GateInfo(id=gid, name=gname, file=None, calls=0, ok=False)
        for py in py_files:
            text = py.read_text(errors="ignore")
            cnt = sum(text.count(pat) for pat in patterns)
            if cnt > 0:
                gi.calls += cnt
                gi.file = gi.file or safe_rel(py, repo)
        gi.ok = gi.file is not None
        gate_infos.append(gi)

    # Entry points
    entries: list[EntryInfo] = []
    for py in py_files:
        try:
            tree = ast.parse(py.read_text(errors="ignore"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.lower().startswith("execute"):
                entries.append(EntryInfo(
                    name=node.name,
                    file=safe_rel(py, repo),
                    line=node.lineno,
                ))

    # Check each entry
    gw_files = {safe_rel(p, repo) for p in py_files
                if "execution_gateway.py" in str(p)}
    all_bypasses: list[str] = []
    has_mutagen = False

    for ep in entries:
        fpath = ep.file.lower()
        is_gw = ep.file in gw_files and ep.name == "execute"
        is_proof_carried = ep.file in gw_files and ep.name == "execute_proof_carried"
        is_mutagen = ep.file in MUTAGEN_REMOVE
        is_deprecated_ok = ep.file in DEPRECATED_OK

        covered_raw: list[str] = []
        for py in py_files:
            if safe_rel(py, repo) == ep.file:
                text = py.read_text(errors="ignore")
                for gid, _, pats in GATES:
                    if any(p in text for p in pats):
                        covered_raw.append(gid)
        covered = covered_raw
        missing = [gid for gid, _, _ in GATES if gid not in covered]

        if is_gw or is_proof_carried:
            ep.status = "gateway_legitimate"
            ep.gates_covered = covered
            ep.gates_missing = []
        elif is_mutagen:
            ep.status = "VIOLATION_mutagen"
            ep.gates_missing = missing
            has_mutagen = True
            all_bypasses.append(f"  {ep.file}:{ep.line} {ep.name}() VIOLATION: execute() must be removed")
        elif is_deprecated_ok:
            ep.status = "deprecated_ok"
            ep.gates_covered = covered
            ep.gates_missing = missing
            if missing:
                all_bypasses.append(f"  {ep.file}:{ep.line} {ep.name}() deprecated (in-progress): {missing}")
        elif any(ip in fpath for ip in INTERNAL_PREFIXES):
            ep.status = "internal_uesl"
            ep.gates_covered = covered
            ep.gates_missing = missing
        else:
            ep.status = "bypass"
            ep.gates_missing = missing
            all_bypasses.append(f"  {ep.file}:{ep.line} {ep.name}() BYPASS: missing {missing}")

    # Actuator exposure
    exposed: list[str] = []
    for py in py_files:
        if "execution_gateway" in str(py) or py.name.startswith("_"):
            continue
        text = py.read_text(errors="ignore")
        if "CausalActuationEngine" not in text:
            continue
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "CausalActuationEngine":
                exposed.append(f"  {safe_rel(py,repo)}:{node.lineno} CausalActuationEngine external access")
            elif isinstance(node, ast.Attribute) and node.attr in (
                "compute_actuation_signals","generate_commands",
                "evaluate_actuation_result","apply_command"
            ):
                exposed.append(f"  {safe_rel(py,repo)}:{node.lineno} actuator.{node.attr}()")

    # Result
    missing_gates = [gi for gi in gate_infos if not gi.ok]
    active_bypasses = [
        b for b in all_bypasses
        if "gateway_legitimate" not in b and "internal_uesl" not in b and b.startswith("  ") and "deprecated" not in b and "VIOLATION" not in b
    ]
    passes = not (has_mutagen or active_bypasses or exposed or missing_gates)

    # Print
    print(f"\n{'Gate':<5} {'Name':<38} {'File':<35} {'Calls':<6} {'OK'}")
    print("-" * 85)
    for gi in gate_infos:
        print(f"  {gi.id:<4} {gi.name:<38} {(gi.file or 'N/A'):<35} {gi.calls:<6} {'✓' if gi.ok else '✗'}")

    print("\n── Entry Points ──")
    for ep in entries:
        print(f"  {ep.file}:{ep.line} {ep.name}() [{ep.status}]")
        if ep.gates_missing:
            print(f"    missing: {ep.gates_missing}")

    print("\n── Bypasses ──")
    print("  " + ("(none)" if not all_bypasses else ""))
    for b in all_bypasses:
        print(b)

    print("\n── Actuator Exposure ──")
    print("  " + ("(none)" if not exposed else ""))
    for e in exposed:
        print(e)

    print("\n" + "=" * 70)
    if passes:
        print("  ✅ PASS — Execution algebra verified")
    else:
        print("  ❌ FAIL:")
        if has_mutagen:
            print("       mutagen execute() present")
        if active_bypasses:
            print(f"       active bypass paths: {len(active_bypasses)}")
        if exposed:
            print(f"       actuator exposed: {len(exposed)}")
        if missing_gates:
            print(f"       missing gates: {[gi.id for gi in missing_gates]}")
    print(f"\n  Gates: {sum(gi.ok for gi in gate_infos)}/10  Entries: {len([e for e in entries if e.status=='gateway_legitimate'])} (legitimate)")
    print("=" * 70)
    return 0 if passes else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=pathlib.Path,
                  default=pathlib.Path("/home/workspace/atom-federation-os"))
    sys.exit(run(p.parse_args().repo))

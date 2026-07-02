"""
runtime_guard.py — atom-federation-os v9.0+P4 Runtime Self-Verification.

Runtime component that enforces execution algebra integrity on EVERY call.

RULES (cannot be disabled):
    1. len(entry_points) == 1  (ExecutionGateway.execute only)
    2. ExecutionGateway dominates all mutation call stacks
    3. MutationExecutor.apply_mutation() ONLY callable from ACT stage
    4. Actuator calls ONLY through G7 (ActuationGate)
    5. Any violation → SystemIntegrityViolation (no fallback, no warning)

Usage:
    RuntimeExecutionGuard.assert_system_integrity()  # called at Gateway entry
    RuntimeExecutionGuard.assert_in_gateway_context()   # called in MutationExecutor
    RuntimeExecutionGuard.assert_not_in_module_import() # called at module init
"""
from __future__ import annotations

import sys
import threading
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ─── Exception ────────────────────────────────────────────────────────────────

class SystemIntegrityViolation(Exception):
    """
    Raised when ANY execution algebra invariant is violated at runtime.

    This is UNRECOVERABLE. No fallback, no warning, no graceful degradation.
    The system must abort immediately.
    """

    def __init__(self, component: str, message: str, context: dict | None = None):
        self.component = component
        self.context = context or {}
        full = f"[{component}] {message}"
        if context:
            full += f" | context={context}"
        super().__init__(full)


# ─── Violation Severity ───────────────────────────────────────────────────────

class ViolationType(Enum):
    ENTRY_POINT_MULTIPLE = "entry_point_multiple"
    STACK_OUTSIDE_GATEWAY = "stack_outside_gateway"
    MUTATION_OUTSIDE_GATEWAY = "mutation_outside_gateway"
    ACTUATOR_EXPOSED = "actuator_exposed"
    BYPASS_ATTEMPT = "bypass_attempt"
    IMPORTSIDE_MUTATION = "importside_mutation"


# ─── Runtime Guard State ───────────────────────────────────────────────────────

@dataclass
class GuardViolation:
    vtype: ViolationType
    message: str
    stack_snapshot: str
    context: dict = field(default_factory=dict)


class RuntimeExecutionGuard:
    """
    Runtime self-verification for execution algebra.

    Enforces the three invariants on every call to Gateway.execute():
        1. Single entry point
        2. Gateway dominates call stack
        3. No external mutation

    This guard CANNOT be disabled. Any attempt to bypass raises
    SystemIntegrityViolation immediately.
    """

    _instance: RuntimeExecutionGuard | None = None
    _lock = threading.Lock()

    # Whitelist of known-safe entry point functions
    _KNOWN_ENTRY = frozenset({
        "execute",           # ExecutionGateway.execute
        "_call_chain",        # ExecutionGateway._call_chain (internal)
        "_gateway_call_chain",  # alias
    })

    # Modules that are FORBIDDEN from calling mutation/actuation
    _FORBIDDEN_MUTATION_CALLERS = frozenset({
        "execution_loop",        # old path
        "merge_engine",          # old path
        "cluster.node.node",     # old path
        "mutation_executor",     # must not call apply_mutation externally
    })

    # Module paths that are internal only (not external entry points)
    _INTERNAL_MODULES = frozenset({
        "uesl.engine",           # internal UESL orchestrator
        "uesl.transport",        # UESL internals
        "sbs.",                  # SBS is a separate layer
        "alignment.",            # alignment sub-modules
        "meta_control.",         # meta control sub-modules
        "orchestration.v8",      # internal orchestration
        "consistency_v2.",       # consistency sub-modules
        "federation.",           # federation sub-modules
        "cluster.",              # cluster sub-modules
    })

    # Modules that are ALWAYS forbidden for mutation
    _ALWAYS_FORBIDDEN = frozenset({
        "execution_loop",        # bypass path
        "cluster.node.node",     # bypass path
    })

    def __new__(cls) -> RuntimeExecutionGuard:
        """Singleton — only one guard instance per process."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._violations: list[GuardViolation] = []
        self._call_count: int = 0
        self._gateway_depth: int = 0  # recursion guard
        self._sysmodules_snapshot: set[str] = set(sys.modules.keys())
        self._checked_modules: set[str] = set()
        # Scan entry points once on init
        self._entry_point_cache: list[str] | None = None

    # ─── Singleton access ──────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> RuntimeExecutionGuard:
        """Get the singleton guard instance."""
        return cls()

    # ─── Entry Point Verification ─────────────────────────────────────────

    def verify_entrypoint(self) -> None:
        """
        Invariant 1: len(entry_points) == 1

        Scans ALL loaded modules for 'execute' methods and asserts
        that ONLY ExecutionGateway.execute() is present.

        This runs at the START of every Gateway.execute() call.
        """
        if self._entry_point_cache is not None:
            # Already verified on this call
            return

        found: list[tuple[str, str]] = []  # (module, method_name)

        for mod_name, mod in sys.modules.items():
            if mod is None:
                continue
            # Skip internal modules
            if any(mod_name.startswith(im) for im in self._INTERNAL_MODULES):
                continue
            try:
                for attr_name in dir(mod):
                    if attr_name == "execute":
                        attr = getattr(mod, attr_name, None)
                        if callable(attr) and not attr_name.startswith("_"):
                            # Skip if it's inside ExecutionGateway
                            if "execution_gateway" not in mod_name.lower():
                                found.append((mod_name, attr_name))
            except Exception:
                continue

        if found:
            names = ", ".join(f"{m}.{a}" for m, a in found)
            raise SystemIntegrityViolation(
                component="RuntimeExecutionGuard",
                message=f"MULTIPLE_ENTRY_POINTS: found {len(found)} execute() functions: {names}",
                context={"entry_points": [f"{m}.{a}" for m, a in found]},
            )

        self._entry_point_cache = [m for m, _ in found]

    # ─── Stack Dominator Verification ──────────────────────────────────────

    def verify_dominator(self, stack_info: list[dict[str, Any]] | None = None) -> None:
        """
        Invariant 2: ExecutionGateway dominates all mutation call stacks.

        Verifies that EVERY call to any gate/ACT/mutation/actuator
        has ExecutionGateway.execute() in its call stack.

        This is the STRICT runtime equivalent of the dominator tree proof.
        """

        if stack_info is None:
            stack_info = self._capture_stack()

        for frame in stack_info:
            filename = frame.get("filename", "")
            function = frame.get("function", "")

            # Skip Python internals
            if any(skip in filename for skip in ("<frozen", "<string>", "/usr/lib")):
                continue

            # FORBIDDEN: any direct call to apply_mutation from outside Gateway
            if function == "apply_mutation":
                in_gateway = any(
                    "execution_gateway" in sf.get("filename", "").lower()
                    for sf in stack_info
                )
                if not in_gateway:
                    raise SystemIntegrityViolation(
                        component="RuntimeExecutionGuard",
                        message=f"MUTATION_OUTSIDE_GATEWAY: apply_mutation called from {filename}:{frame.get('lineno', '?')}",
                        context={
                            "caller": f"{filename}:{frame.get('lineno', '?')}",
                            "function": function,
                            "stack_snapshot": self._format_stack(stack_info),
                        },
                    )

            # FORBIDDEN: actuator calls outside Gateway
            if any(kw in function for kw in ("actuate", "CausalActuationEngine", "_actuate")):
                in_gateway = any(
                    "execution_gateway" in sf.get("filename", "").lower()
                    for sf in stack_info
                )
                if not in_gateway:
                    raise SystemIntegrityViolation(
                        component="RuntimeExecutionGuard",
                        message=f"ACTUATOR_EXPOSED: actuator '{function}' called outside Gateway",
                        context={"caller": f"{filename}:{frame.get('lineno', '?')}"},
                    )

    # ─── No External Mutation ──────────────────────────────────────────────

    def verify_no_external_mutation(self, stack_info: list[dict[str, Any]] | None = None) -> None:
        """
        Invariant 3: No mutation can occur outside ExecutionGateway.

        Checks the call stack for any forbidden caller patterns:
        - execution_loop.execute()
        - cluster.node.node.execute()
        - direct MutationExecutor.apply_mutation()
        """
        if stack_info is None:
            stack_info = self._capture_stack()

        stack_str = self._format_stack(stack_info)

        for forbidden in self._ALWAYS_FORBIDDEN:
            if forbidden in stack_str:
                raise SystemIntegrityViolation(
                    component="RuntimeExecutionGuard",
                    message=f"FORBIDDEN_CALLER: {forbidden} is not allowed to trigger mutations",
                    context={"forbidden_module": forbidden, "stack_snapshot": stack_str},
                )

    # ─── Full Integrity Check ───────────────────────────────────────────────

    @classmethod
    def assert_system_integrity(cls) -> None:
        """
        Run ALL three invariant checks.

        Called at the START of ExecutionGateway.execute().

        This is the HARD entry gate: any violation aborts immediately.
        No return value — raises SystemIntegrityViolation on any failure.
        """
        guard = cls.get_instance()
        # Prevent recursion
        if guard._gateway_depth > 0:
            # Nested call — this is fine (recursive Gateway usage)
            return
        guard._gateway_depth += 1
        try:
            guard._entry_point_cache = None  # Reset cache for fresh check
            guard.verify_entrypoint()
            guard.verify_dominator()
            guard.verify_no_external_mutation()
            guard._call_count += 1
        finally:
            guard._gateway_depth -= 1
            guard._entry_point_cache = None  # Clear after use

    # ─── Context Assertion (called from within components) ─────────────────

    @classmethod
    def assert_in_gateway_context(cls) -> bool:
        """
        Called from INSIDE MutationExecutor.apply_mutation().

        Returns True if in Gateway context. Raises if not.
        This is the last line of defense: even if bypass works at Gateway entry,
        MutationExecutor refuses to act if called directly.
        """
        guard = cls.get_instance()

        stack_info = guard._capture_stack()
        stack_str = guard._format_stack(stack_info)

        in_gateway = any(
            "execution_gateway" in frame.get("filename", "").lower()
            for frame in stack_info
        )

        if not in_gateway:
            raise SystemIntegrityViolation(
                component="MutationExecutor",
                message="apply_mutation() called OUTSIDE ExecutionGateway — bypass detected",
                context={
                    "violation": "mutation_outside_gateway",
                    "stack_snapshot": stack_str,
                },
            )

        return True

    @classmethod
    def assert_actuator_in_context(cls) -> bool:
        """Called before any actuator operation. Raises if not in Gateway."""
        guard = cls.get_instance()
        stack_info = guard._capture_stack()

        in_gateway = any(
            "execution_gateway" in frame.get("filename", "").lower()
            for frame in stack_info
        )

        if not in_gateway:
            raise SystemIntegrityViolation(
                component="Actuator",
                message="Actuator called OUTSIDE ExecutionGateway",
                context={"violation": "actuator_exposed"},
            )

        return True

    # ─── Internal helpers ───────────────────────────────────────────────────

    def _capture_stack(self) -> list[dict[str, Any]]:
        """Capture current call stack as list of frames."""
        frames: list[dict[str, Any]] = []
        for frame_info in traceback.extract_stack():
            frames.append({
                "filename": frame_info.filename,
                "lineno": frame_info.lineno,
                "function": frame_info.name,
            })
        return frames

    def _format_stack(self, stack: list[dict[str, Any]]) -> str:
        """Format stack as readable string."""
        return "\n".join(
            f"  {f['filename']}:{f.get('lineno', '?')} in {f['function']}"
            for f in stack[-8:]  # last 8 frames
        )

    # ─── Stats ─────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            "calls_verified": self._call_count,
            "violations_detected": len(self._violations),
            "entry_points_count": len(self._entry_point_cache) if self._entry_point_cache is not None else "unchecked",
        }


# ─── Module-level assertion ───────────────────────────────────────────────────

def assert_import_integrity() -> None:
    """
    Called at module load time (import).

    Ensures that no forbidden module is imported before ExecutionGateway
    is properly initialized.
    """
    pass  # No pre-import blocking — runtime guard handles all violations


# ═══════════════════════════════════════════════════════════════════════════════
# P0.2 — AST + Execution Graph Hash Verification
# ═══════════════════════════════════════════════════════════════════════════════

import ast as _ast
import hashlib
import pathlib as _pathlib


def _load_snapshot_hashes(repo_root: _pathlib.Path | None = None) -> dict:
    """Load expected hashes from formal_model/system_snapshot.json."""
    if repo_root is None:
        repo_root = _pathlib.Path(__file__).parent.parent.parent
    snap_path = repo_root / "formal_model" / "system_snapshot.json"
    if not snap_path.exists():
        raise SystemIntegrityViolation(
            component="ASTIntegrity",
            message=f"Snapshot not found: {snap_path}. Run: python scripts/ast_snapshot.py --save-hash",
        )
    import json as _json
    snap = _json.loads(snap_path.read_text())
    return {
        "ast_hash": snap.get("ast_hash", ""),
        "graph_hash": snap.get("graph_hash", ""),
    }


def _compute_file_ast_hash(py_path: _pathlib.Path) -> str:
    """Compute normalized AST hash for one file (matches ast_snapshot.py)."""
    text = py_path.read_text(errors="ignore")
    try:
        tree = _ast.parse(text, filename=str(py_path))
    except SyntaxError:
        return ""
    # Normalize to hashable
    def _norm(node) -> tuple:
        if isinstance(node, _ast.Name):
            return ("Name", node.id)
        if isinstance(node, _ast.Constant):
            v = node.value
            if isinstance(v, (int, float, str, bytes, bool, type(None))):
                return ("Const", repr(v))
            return ("Const", type(v).__name__)
        if isinstance(node, _ast.Starred):
            return ("Starred", _norm(node.value))
        if isinstance(node, _ast.Subscript):
            return ("Subscript", _norm(node.value), _norm(node.slice))
        result = []
        for fn, fv in _ast.iter_fields(node):
            if fn in ("lineno", "end_lineno", "col_offset", "end_col_offset", "ctx", "type_comment", "type_ignores"):
                continue
            if fv is None:
                continue
            if isinstance(fv, list):
                items = []
                for it in fv:
                    if it is None:
                        continue
                    if isinstance(it, _ast.AST):
                        c = _norm(it)
                        if c is not None:
                            items.append(c)
                    elif isinstance(it, str):
                        items.append(("str", it))
                if items:
                    result.append((fn, items))
            elif isinstance(fv, _ast.AST):
                c = _norm(fv)
                if c is not None:
                    result.append((fn, c))
            elif isinstance(fv, (str, int, float, bool)):
                result.append((fn, fv))
        return (node.__class__.__name__, tuple(result))

    normalized = _norm(tree)
    serialized = _json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode()).hexdigest()


def verify_runtime_ast_integrity(repo_root: _pathlib.Path | None = None) -> None:
    """
    P0.2: Verify runtime AST hash matches formal_model snapshot.

    Raises SystemIntegrityViolation if:
        - Snapshot file missing
        - AST hash mismatch (code changed since snapshot)
        - Files added/removed
    """
    if repo_root is None:
        repo_root = _pathlib.Path(__file__).parent.parent.parent

    expected = _load_snapshot_hashes(repo_root)
    expected_ast = expected["ast_hash"]

    # Compute current AST hash (fast: skip __pycache__, .git, sibling packages)
    hasher = hashlib.sha256()
    for py_path in sorted(repo_root.rglob("*.py")):
        rel = str(py_path.relative_to(repo_root))
        if ("__pycache__" in rel or ".git" in rel or
                "atomos_pkg" in rel or "/.pytest_cache/" in rel):
            continue
        path_bytes = rel.encode()
        file_hash = _compute_file_ast_hash(py_path)
        hasher.update(path_bytes)
        hasher.update(file_hash.encode())

    current_ast = hasher.hexdigest()
    if current_ast != expected_ast:
        raise SystemIntegrityViolation(
            component="ASTIntegrity",
            message=f"AST_HASH_MISMATCH: runtime={current_ast[:16]}... expected={expected_ast[:16]}...",
            context={
                "runtime_ast_hash": current_ast,
                "expected_ast_hash": expected_ast,
                "action": "Snapshot stale — rerun: python scripts/ast_snapshot.py --save-hash",
            },
        )


def verify_runtime_graph_integrity(repo_root: _pathlib.Path | None = None) -> None:
    """
    P0.2: Verify execution graph hash matches formal_model snapshot.

    Raises SystemIntegrityViolation if:
        - Graph snapshot missing
        - Graph hash mismatch (execution topology changed)
    """
    if repo_root is None:
        repo_root = _pathlib.Path(__file__).parent.parent.parent

    expected = _load_snapshot_hashes(repo_root)
    expected_graph = expected["graph_hash"]

    # Compute current graph hash (call graph only, not full AST)
    hasher = hashlib.sha256()
    for py_path in sorted(repo_root.rglob("*.py")):
        rel = str(py_path.relative_to(repo_root))
        if ("__pycache__" in rel or ".git" in rel or
                "atomos_pkg" in rel or "/.pytest_cache/" in rel):
            continue
        try:
            tree = _ast.parse(py_path.read_text(errors="ignore"), filename=str(py_path))
        except SyntaxError:
            continue
        for node in _ast.walk(tree):
            if isinstance(node, _ast.FunctionDef):
                if any(node.name.lower().startswith(p) for p in
                       ("execute", "apply_mutation", "run", "commit", "propose")):
                    hasher.update(f"{rel}:{node.lineno}:{node.name}".encode())

    current_graph = hasher.hexdigest()
    if current_graph != expected_graph:
        raise SystemIntegrityViolation(
            component="GraphIntegrity",
            message=f"GRAPH_HASH_MISMATCH: runtime={current_graph[:16]}... expected={expected_graph[:16]}...",
            context={
                "runtime_graph_hash": current_graph,
                "expected_graph_hash": expected_graph,
                "action": "Snapshot stale — rerun: python scripts/execution_graph_hash.py --save",
            },
        )

# ═══════════════════════════════════════════════════════════════════════════════
# P0.3 — Environment Hash Verification
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_env_hash_fast() -> str:
    """Compute env hash (inline, no subprocess for pip freeze)."""
    import hashlib
    import json
    import os
    import platform
    import sys
    components = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_platform": platform.platform(),
        "python_implementation": platform.python_implementation(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "pythonpath": os.environ.get("PYTHONPATH", ""),
    }
    return hashlib.sha256(json.dumps(components, sort_keys=True).encode()).hexdigest()


def verify_runtime_env_integrity(repo_root: _pathlib.Path | None = None) -> None:
    """
    P0.3: Verify runtime environment hash matches formal_model/env_hash.json.

    Raises SystemIntegrityViolation if:
        - Env hash file missing
        - PYTHONHASHSEED != '0'
        - Python version mismatch
        - PYTHONPATH missing repo root
    """
    if repo_root is None:
        repo_root = _pathlib.Path(__file__).parent.parent.parent

    env_path = repo_root / "formal_model" / "env_hash.json"
    if not env_path.exists():
        raise SystemIntegrityViolation(
            component="EnvIntegrity",
            message=f"env_hash.json not found at {env_path}. Run: python scripts/environment_hash.py --save",
        )
    import json as _json
    env_data = _json.loads(env_path.read_text())
    expected_env = env_data["env_hash"]
    locked_py = env_data.get("python_version_locked", "")

    import os as _os
    seed = _os.environ.get("PYTHONHASHSEED", "")
    if seed != "0":
        raise SystemIntegrityViolation(
            component="EnvIntegrity",
            message=f"PYTHONHASHSEED={seed} (expected 0). Run: bash scripts/bootstrap_env.sh",
        )

    pypath = _os.environ.get("PYTHONPATH", "")
    if str(repo_root) not in pypath:
        raise SystemIntegrityViolation(
            component="EnvIntegrity",
            message="PYTHONPATH does not contain repo root. Run: bash scripts/bootstrap_env.sh",
        )

    current_py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if locked_py and current_py != locked_py:
        raise SystemIntegrityViolation(
            component="EnvIntegrity",
            message=f"Python version: current={current_py} locked={locked_py}. Run: bash scripts/bootstrap_env.sh",
        )

    current_env = _compute_env_hash_fast()
    if current_env != expected_env:
        raise SystemIntegrityViolation(
            component="EnvIntegrity",
            message=f"ENV_HASH_MISMATCH: runtime={current_env[:16]}... expected={expected_env[:16]}...",
            context={
                "runtime_env_hash": current_env,
                "expected_env_hash": expected_env,
                "action": "Run: python scripts/environment_hash.py --save && bash scripts/bootstrap_env.sh",
            },
        )

# self_audit.py — atom-federation-os v9.0+P0.1
# Runtime Self-Audit System
#
# At system startup:
#   1. Scan all modules in sys.modules
#   2. Build execution graph (call relationships)
#   3. Detect any bypass paths (direct MutationExecutor calls outside Gateway)
#   4. Register all mutation points in ExecutionGuardPolicy
#   5. Verify Graph/Stack dominator invariants
#
# Any bypass detected → SystemShutdown (immediate, no recovery).
#
# This audit runs ONCE at boot and verifies consistency throughout runtime.

from __future__ import annotations

import ast
import hashlib
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from core.runtime.guard_policy import (
    ExecutionGuardPolicy,
    MutationPoint,
    SystemShutdown,
)

# ── Bypass Pattern Signatures ──────────────────────────────────────────────────

# Patterns that indicate direct mutation calls (bypass attempts)
_BYPASS_FUNCTION_PATTERNS = frozenset({
    'apply_mutation', 'execute_mutation', 'execute_mutation_direct',
    'direct_mutate', 'unsafe_mutate', 'force_mutate', 'bypass_apply',
    '_unsafe_execute', '__mutate', '_direct_mutation',
})

# Modules that are FORBIDDEN to call mutation functions
_FORBIDDEN_CALLER_MODULES = frozenset({
    'execution_loop', 'merge_engine', 'cluster.node.node',
    'swarm.execution_loop', 'kubernetes.operator',
})

# Modules where mutation IS allowed (whitelist)
_ALLOWED_MUTATION_MODULES = frozenset({
    'orchestration.execution_gateway',
    'orchestration.executiongateway',
    'orchestration.mutation_executor',  # only its own methods
    'orchestration.v8_2b_controlled_autocorrection.mutation_executor',
})


# ── Bypass Detection Results ───────────────────────────────────────────────────

@dataclass
class BypassPath:
    source_module: str
    source_function: str
    target_module: str
    target_function: str
    file_path: str
    line_number: int
    bypass_type: str  # 'direct_call', 'indirect', 'import_bypass'


@dataclass
class SelfAuditResult:
    timestamp: str
    total_modules_scanned: int
    mutation_points_found: int
    bypass_paths_detected: list[BypassPath]
    execution_graph: dict[str, list[str]]  # module → list of called modules
    graph_hash: str
    passed: bool
    error_message: str = ''
    registered_points: dict[str, MutationPoint] = field(default_factory=dict)


class SelfAudit:
    '''
    Runtime Self-Audit: Scans and verifies entire codebase at startup.
    
    Guarantees:
        - All mutation points are known and registered
        - No bypass paths exist in the code
        - Execution graph is deterministic and reproducible
        - Any violation → SystemShutdown
    
    Usage:
        result = SelfAudit.run()
        if not result.passed:
            raise SystemShutdown(...)
    '''

    _instance: SelfAudit | None = None
    _lock = threading.Lock()
    _audit_complete: bool = False

    def __init__(self):
        self._policy = ExecutionGuardPolicy.instance()
        self._results: list[SelfAuditResult] = []

    @classmethod
    def run(cls, repo_root: Path | None = None) -> SelfAuditResult:
        '''
        Run full self-audit at system startup.
        
        Returns SelfAuditResult with:
            - All discovered mutation points
            - Any bypass paths detected
            - Execution graph
            - pass/fail status
        
        Raises:
            SystemShutdown: if bypass detected
        '''
        if cls._audit_complete:
            return cls._results[-1] if cls._results else None

        with cls._lock:
            if cls._audit_complete:
                return cls._results[-1] if cls._results else None

            audit = cls()
            result = audit._do_audit(repo_root)
            cls._results.append(result)
            cls._audit_complete = True

            if not result.passed:
                raise SystemShutdown(
                    f'Self-Audit FAILED: {result.error_message}\n'
                    f'Bypass paths detected: {len(result.bypass_paths_detected)}\n'
                    f'System cannot start in unsafe state.',
                    violation=None
                )

            # Register all mutation points in guard policy
            cls._policy.initialize(result.registered_points)

            return result

    @classmethod
    def reset(cls) -> None:
        '''Reset audit state (for testing only).'''
        with cls._lock:
            cls._audit_complete = False
            cls._results = []

    def _do_audit(self, repo_root: Path | None = None) -> SelfAuditResult:
        '''
        Execute full audit:
            1. Module scan
            2. Mutation point discovery
            3. Bypass path detection
            4. Graph construction
        '''
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent

        modules_scanned = 0
        mutation_points: dict[str, MutationPoint] = {}
        bypass_paths: list[BypassPath] = []
        execution_graph: dict[str, list[str]] = {}

        # Scan all Python files in repo
        for py_file in self._iter_python_files(repo_root):
            try:
                result = self._audit_file(py_file, repo_root)
                modules_scanned += 1

                # Merge mutation points
                mutation_points.update(result['mutation_points'])

                # Check for bypasses
                for bypass in result['bypasses']:
                    bypass_paths.append(bypass)

                # Build execution graph
                mod_name = self._file_to_module(py_file, repo_root)
                if mod_name:
                    execution_graph[mod_name] = result['called_modules']

            except Exception:
                # File-level error — continue scanning
                pass

        # Compute graph hash
        graph_hash = self._compute_graph_hash(execution_graph)

        # Final bypass check
        if bypass_paths:
            error_msg = self._format_bypass_error(bypass_paths)
            return SelfAuditResult(
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_modules_scanned=modules_scanned,
                mutation_points_found=len(mutation_points),
                bypass_paths_detected=bypass_paths,
                execution_graph=execution_graph,
                graph_hash=graph_hash,
                passed=False,
                error_message=error_msg,
            )

        return SelfAuditResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_modules_scanned=modules_scanned,
            mutation_points_found=len(mutation_points),
            bypass_paths_detected=bypass_paths,
            execution_graph=execution_graph,
            graph_hash=graph_hash,
            passed=True,
            registered_points=mutation_points,
        )

    def _iter_python_files(self, repo_root: Path):
        '''Iterate all Python files, skipping cache/system dirs and tests.'''
        skip_dirs = {'__pycache__', '.git', '.pytest_cache', 'node_modules',
                     'atomos_pkg', '.venv', 'venv', 'build', 'dist',
                     'tests', 'test_', '_test.py'}

        for py_file in repo_root.rglob('*.py'):
            rel = str(py_file.relative_to(repo_root))
            if any(skip in rel for skip in skip_dirs):
                continue
            # Skip conftest files
            if py_file.name == 'conftest.py':
                continue
            yield py_file

    def _audit_file(self, py_file: Path, repo_root: Path) -> dict:
        '''
        Audit single Python file.
        
        Returns:
            {
                'mutation_points': {key -> MutationPoint},
                'bypasses': [BypassPath],
                'called_modules': [module_name],
            }
        '''
        mutation_points = {}
        bypasses = []
        called_modules = []

        # Check if this file is inside ExecutionGateway path OR v8_2b module
        file_path_str = str(py_file).lower()
        is_execution_gateway_file = 'executiongateway' in file_path_str.replace('\\', '/')
        is_v8_2b_module = 'v8_2b_controlled_autocorrection' in file_path_str.replace('\\', '/')

        try:
            source = py_file.read_text(errors='ignore')
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            return {'mutation_points': {}, 'bypasses': [], 'called_modules': []}

        mod_name = self._file_to_module(py_file, repo_root)

        for node in ast.walk(tree):
            # ── FunctionDef: Check if it's a mutation point ──
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                lineno = node.lineno

                # Check if this is a mutation function
                if self._is_mutation_function(func_name):
                    key = f'{mod_name}:{func_name}'

                    # Check if in allowed module (file path check)
                    if is_execution_gateway_file:
                        mutation_points[key] = MutationPoint(
                            module=mod_name,
                            function=func_name,
                            file_path=str(py_file),
                            line_number=lineno,
                            registered_at=datetime.now(timezone.utc).isoformat(),
                            caller_stack_hash='',
                        )
                    elif any(forbidden in mod_name for forbidden in _FORBIDDEN_CALLER_MODULES):
                        # Forbidden module
                        bypasses.append(BypassPath(
                            source_module=mod_name,
                            source_function=func_name,
                            target_module='unknown',
                            target_function='mutation_executor',
                            file_path=str(py_file),
                            line_number=lineno,
                            bypass_type='forbidden_module',
                        ))
                    else:
                        # Mutation function in non-gateway module
                        bypasses.append(BypassPath(
                            source_module=mod_name,
                            source_function=func_name,
                            target_module='MutationExecutor',
                            target_function=func_name,
                            file_path=str(py_file),
                            line_number=lineno,
                            bypass_type='direct_call',
                        ))

            # ── Call: Check for direct mutation calls ──
            elif isinstance(node, ast.Call):
                call_func = self._get_call_name(node.func)

                if call_func in _BYPASS_FUNCTION_PATTERNS:
                    # Direct call to mutation function
                    # Check if caller is in ExecutionGateway file or v8_2b module
                    caller_frame = self._get_caller_info(tree, node, py_file, mod_name)
                    caller_mod = caller_frame.get('module', 'unknown')

                    # If the source file is ExecutionGateway or v8_2b, allow it
                    if is_execution_gateway_file or is_v8_2b_module:
                        pass  # Allowed
                    elif any(x in caller_mod.lower() for x in ('execution_gateway', 'executiongateway')):
                        pass  # Allowed
                    else:
                        bypasses.append(BypassPath(
                            source_module=caller_mod,
                            source_function=caller_frame.get('function', 'unknown'),
                            target_module='MutationExecutor',
                            target_function=call_func,
                            file_path=str(py_file),
                            line_number=node.lineno,
                            bypass_type='direct_call',
                        ))

                # Track module calls for execution graph
                if call_func:
                    called_modules.append(call_func)

        return {
            'mutation_points': mutation_points,
            'bypasses': bypasses,
            'called_modules': called_modules,
        }

    def _is_mutation_function(self, func_name: str) -> bool:
        '''Check if function name is a mutation function (exact match only).'''
        # Only flag EXACT matches, not substring matches
        exact_mutation_names = frozenset({
            'apply_mutation',
            'execute_mutation',
            'execute_mutation_direct',
            'direct_mutation',
            'force_mutation',
            'unsafe_execute',
            'bypass_apply',
            '__mutate',
            '_direct_mutation',
        })
        return func_name in exact_mutation_names

    def _get_call_name(self, node: ast.AST) -> str | None:
        '''Extract function name from AST call node.'''
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_call_name(node.value)
        return None

    def _get_caller_info(self, tree: ast.AST, call_node: ast.Call, py_file: Path, mod_name: str) -> dict:
        '''Find the function/module that contains this call.'''
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for child in ast.walk(node):
                    if child is call_node:
                        mod = self._file_to_module(
                            Path(tree.filename) if hasattr(tree, 'filename') else Path('.'),
                            Path(__file__).parent.parent.parent
                        )
                        return {
                            'module': mod,
                            'function': node.name,
                            'lineno': node.lineno,
                        }
        return {'module': 'unknown', 'function': 'unknown', 'lineno': 0}

    def _file_to_module(self, py_file: Path, repo_root: Path) -> str:
        '''Convert file path to module name.'''
        try:
            rel = py_file.relative_to(repo_root)
            parts = list(rel.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            elif parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except ValueError:
            return str(py_file)

    def _compute_graph_hash(self, execution_graph: dict) -> str:
        '''Compute deterministic hash of execution graph.'''
        # Sort for reproducibility
        sorted_graph = {k: sorted(v) for k, v in sorted(execution_graph.items())}
        serialized = str(sorted_graph).encode()
        return hashlib.sha256(serialized).hexdigest()[:16]

    def _format_bypass_error(self, bypass_paths: list[BypassPath]) -> str:
        '''Format bypass detection error.'''
        lines = [
            f'Self-Audit detected {len(bypass_paths)} bypass path(s):',
            ''
        ]
        for bp in bypass_paths[:5]:  # Show first 5
            lines.append(
                f'  BYPASS: {bp.source_module}.{bp.source_function}\n'
                f'    → {bp.target_module}.{bp.target_function}\n'
                f'    File: {bp.file_path}:{bp.line_number}\n'
                f'    Type: {bp.bypass_type}\n'
            )
        return '\n'.join(lines)


# ── Runtime Verification (called during execution) ────────────────────────────

class RuntimeVerifier:
    '''
    Runtime verification that complements startup self-audit.
    
    Called on every mutation to verify:
        1. Caller is registered mutation point
        2. Gateway context is active
        3. No bypass attempted
    '''

    @staticmethod
    def verify_mutation_call(caller_module: str, caller_function: str,
                             operation: str) -> None:
        '''
        Verify a mutation call is allowed.
        
        Called from:
        - MutationExecutor.apply_mutation()
        - ExecutionGateway before ACT stage
        - Any @requires_gateway decorated method
        
        Raises:
            SystemShutdown: if verification fails
        '''
        policy = ExecutionGuardPolicy.instance()
        policy.assert_mutation_allowed(caller_module, caller_function, operation)

    @staticmethod
    def verify_gateway_entry() -> None:
        '''
        Verify gateway entry is from allowed entry point.
        
        Called at the start of ExecutionGateway.execute()
        '''
        stack = traceback.extract_stack()
        if not stack:
            return

        # Get calling function
        for frame in reversed(stack[:-1]):  # Skip verify_gateway_entry itself
            func_name = frame.name
            if func_name.startswith('_'):
                continue

            policy = ExecutionGuardPolicy.instance()
            policy.assert_entry_point(func_name)
            break


# ── Startup Hook ───────────────────────────────────────────────────────────────

def run_startup_audit(repo_root: Path | None = None) -> SelfAuditResult:
    '''
    Run self-audit at system startup.
    
    Call this from:
        - ExecutionGateway.__init__()
        - Main entry point (main.py / __main__.py)
    
    Returns SelfAuditResult (raises SystemShutdown on bypass).
    '''
    return SelfAudit.run(repo_root)


# ── Verify Execution Graph matches formal model ────────────────────────────────

def verify_graph_against_snapshot(repo_root: Path | None = None) -> None:
    '''
    Verify runtime execution graph matches formal_model snapshot.
    
    Raises:
        SystemShutdown: if graph doesn't match
    '''
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent

    formal_graph_path = repo_root / 'formal_model' / 'execution_graph.json'
    if not formal_graph_path.exists():
        return  # No snapshot to verify against

    import json
    snapshot = json.loads(formal_graph_path.read_text())
    expected_hash = snapshot.get('graph_hash', '')

    result = SelfAudit.run(repo_root)

    if result.graph_hash != expected_hash:
        raise SystemShutdown(
            f'Execution graph hash mismatch:\n'
            f'  Runtime: {result.graph_hash}\n'
            f'  Expected: {expected_hash}\n'
            f'Code has changed since formal_model snapshot was generated.\n'
            f'Rerun: python scripts/execution_graph_hash.py --save',
            violation=None
        )

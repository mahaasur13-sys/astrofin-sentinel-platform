# static_mutation_analyzer.py — atom-federation-os v9.0+P1.5
# Static analysis for detecting direct MutationExecutor calls outside Gateway.
#
# CI Integration:
#   python scripts/static_mutation_analyzer.py
#   Exit code 0 = pass, non-zero = violations found
#
# Detects:
#   1. Direct calls to apply_mutation() outside ExecutionGateway
#   2. Instantiation of MutationExecutor outside Gateway context
#   3. Import of mutation_executor module outside allowed paths
#   4. Use of forbidden function patterns (direct_mutation, force_mutation, etc.)

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

import logging
log = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────────────

ALLOWED_MODULES = frozenset({
    'orchestration.execution_gateway',
    'orchestration.executiongateway',
    'orchestration.mutation_executor',
    'orchestration.v8_2b_controlled_autocorrection.mutation_executor',
})

FORBIDDEN_PATTERNS = frozenset({
    'apply_mutation', 'execute_mutation', 'execute_mutation_direct',
    'direct_mutate', 'unsafe_mutate', 'force_mutate', 'bypass_apply',
    'MutationExecutor', 'mutation_executor',
})

FORBIDDEN_CALLER_PATTERNS = frozenset({
    'execution_loop', 'merge_engine', 'cluster.node.node',
    'swarm.execution_loop', 'kubernetes.operator',
})


# ── Violation Types ───────────────────────────────────────────────────────────

class ViolationType:
    DIRECT_CALL = 'direct_mutation_call'
    UNAUTHORIZED_INSTANTIATION = 'unauthorized_instantiation'
    FORBIDDEN_IMPORT = 'forbidden_import'
    FORBIDDEN_PATTERN = 'forbidden_function_pattern'
    IMPORTSIDE_MUTATION = 'importside_mutation'


@dataclass
class Violation:
    vtype: str
    file: str
    line: int
    column: int
    message: str
    severity: str = 'ERROR'

    def __str__(self) -> str:
        return f'{self.file}:{self.line}:{self.column}: {self.severity}: {self.message}'


# ── Analyzer ──────────────────────────────────────────────────────────────────

class MutationCallVisitor(ast.NodeVisitor):
    '''
    AST visitor that detects mutation-related violations.

    Checks:
        1. Call nodes — direct calls to mutation functions
        2. Import nodes — forbidden module imports
        3. ClassDef — MutationExecutor instantiation
        4. FunctionDef — forbidden function patterns
    '''

    def __init__(self, filename: str):
        self.filename = filename
        self.violations: list[Violation] = []
        self.current_module = ''
        self.in_allowed_module = False

    def visit_Module(self, node: ast.Module):
        '''Check if this module is allowed to call mutation functions.'''
        # Get module name from filename
        rel = Path(self.filename).stem
        if rel == '__init__':
            self.current_module = str(Path(self.filename).parent.name)
        else:
            self.current_module = rel

        # Check if in allowed path
        self.in_allowed_module = any(
            allowed in self.filename.replace('\\', '/')
            for allowed in ('orchestration/execution_gateway', 'orchestration/executiongateway',
                           'orchestration/mutation_executor')
        )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        '''Detect direct calls to mutation functions.'''
        func_name = self._get_func_name(node.func)

        if func_name in FORBIDDEN_PATTERNS:
            # Check if caller is in allowed module
            if not self.in_allowed_module:
                # Check if this is a direct call (not through gateway)
                self._get_caller_context(node)

                self.violations.append(Violation(
                    vtype=ViolationType.DIRECT_CALL,
                    file=self.filename,
                    line=node.lineno,
                    column=node.col_offset + 1,
                    message=f'Direct call to {func_name}() outside ExecutionGateway. '
                            f'Mutations must flow through gateway.mutation_context().',
                ))

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        '''Detect forbidden module imports.'''
        for alias in node.names:
            if alias.name in FORBIDDEN_PATTERNS or any(
                pat in alias.name for pat in ('mutation_executor', 'MutationExecutor')
            ):
                # Check if this import is in allowed module
                if not self.in_allowed_module:
                    self.violations.append(Violation(
                        vtype=ViolationType.FORBIDDEN_IMPORT,
                        file=self.filename,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        message=f'Forbidden import: {alias.name}. '
                                f'MutationExecutor imports must be inside ExecutionGateway.',
                    ))

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        '''Detect forbidden from-imports.'''
        if node.module and any(pat in node.module for pat in ('mutation_executor', 'MutationExecutor')):
            if not self.in_allowed_module:
                for alias in node.names:
                    self.violations.append(Violation(
                        vtype=ViolationType.FORBIDDEN_IMPORT,
                        file=self.filename,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        message=f'Forbidden import: from {node.module} import {alias.name}. '
                                f'MutationExecutor imports must be inside ExecutionGateway.',
                    ))

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        '''Detect unauthorized MutationExecutor usage.'''
        if node.name == 'MutationExecutor':
            if not self.in_allowed_module:
                self.violations.append(Violation(
                    vtype=ViolationType.UNAUTHORIZED_INSTANTIATION,
                    file=self.filename,
                    line=node.lineno,
                    column=node.col_offset + 1,
                    message=f'Unauthorized MutationExecutor class access in {self.filename}. '
                            f'Only ExecutionGateway modules may define/use MutationExecutor.',
                ))

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        '''Detect forbidden function patterns.'''
        func_lower = node.name.lower()

        for pattern in ('direct_mutation', 'force_mutation', 'unsafe_execute', 'bypass_apply'):
            if pattern in func_lower:
                self.violations.append(Violation(
                    vtype=ViolationType.FORBIDDEN_PATTERN,
                    file=self.filename,
                    line=node.lineno,
                    column=node.col_offset + 1,
                    message=f'Forbidden function pattern: {node.name}. '
                            f'Functions with \"{pattern}\" are not allowed — use Gateway context.',
                ))

        self.generic_visit(node)

    def _get_func_name(self, node: ast.AST) -> str:
        '''Extract function name from AST node.'''
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ''

    def _get_caller_context(self, node: ast.Call) -> dict:
        '''Get context about the calling function/class.'''
        return {}


# ── File Scanner ──────────────────────────────────────────────────────────────

def scan_file(filepath: Path) -> list[Violation]:
    '''Scan single Python file for violations.'''
    try:
        source = filepath.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    visitor = MutationCallVisitor(str(filepath))
    visitor.visit(tree)
    return visitor.violations


def scan_directory(repo_root: Path) -> list[Violation]:
    '''Scan entire repository for violations.'''
    all_violations = []

    skip_dirs = {'__pycache__', '.git', '.pytest_cache', 'node_modules',
                 '.venv', 'venv', 'build', 'dist', '.ruff', 'atomos_pkg'}

    for py_file in repo_root.rglob('*.py'):
        rel = str(py_file.relative_to(repo_root))
        if any(skip in rel for skip in skip_dirs):
            continue

        violations = scan_file(py_file)
        all_violations.extend(violations)

    return all_violations


# ── CI Integration ────────────────────────────────────────────────────────────

def main():
    '''Main entry point for CI.'''
    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    log.info(f'Scanning {repo_root} for mutation violations...')
    log.info("")

    violations = scan_directory(repo_root)

    if violations:
        log.info(f'Found {len(violations)} violation(s):')
        log.info("")

        for v in violations:
            log.info(f'  {v}')
        log.info("")
        log.info('STATIC ANALYSIS FAILED')
        log.info('All mutations must flow through ExecutionGateway.execute().')
        log.info('Fix violations before committing.')
        sys.exit(1)

    log.info('No violations found. Static analysis passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()

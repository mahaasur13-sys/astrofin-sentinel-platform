# visualize_execution_graph.py — atom-federation-os v9.0+P2.6
# Runtime Execution Graph Visualization
#
# Generates a visual representation of all mutation paths in the system.
# Output formats: text (console), dot (GraphViz), json (debugging)
#
# Usage:
#   python scripts/visualize_execution_graph.py --format=text
#   python scripts/visualize_execution_graph.py --format=dot --output=graph.dot
#   python scripts/visualize_execution_graph.py --format=json --output=graph.json

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass, field
from pathlib import Path

import logging
log = logging.getLogger(__name__)


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class MutationNode:
    module: str
    function: str
    file_path: str
    line_number: int
    node_type: str  # 'entry', 'gateway', 'mutation', 'actuator'
    calls: list[str] = field(default_factory=list)
    called_by: list[str] = field(default_factory=list)


@dataclass
class ExecutionGraph:
    nodes: dict[str, MutationNode] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)


# ── Graph Builder ─────────────────────────────────────────────────────────────

class ExecutionGraphBuilder:
    '''
    Builds execution graph from source code.

    Discovers:
        - Entry points (ExecutionGateway.execute)
        - Gateway nodes (G1-G10 stages)
        - Mutation points (apply_mutation, execute)
        - Call relationships between nodes
    '''

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.graph = ExecutionGraph()
        self._mutation_patterns = frozenset({
            'apply_mutation', 'execute', 'execute_mutation',
            'mutate', '_mutate',
        })
        self._gateway_patterns = frozenset({
            'execution_gateway', 'executiongateway',
        })

    def build(self) -> ExecutionGraph:
        '''Build complete execution graph.'''
        for py_file in self._iter_python_files():
            self._process_file(py_file)

        self._link_nodes()
        return self.graph

    def _iter_python_files(self):
        '''Iterate Python files in repo.'''
        skip_dirs = {'__pycache__', '.git', '.pytest_cache', 'node_modules',
                     '.venv', 'venv', 'build', 'dist', '.ruff', 'atomos_pkg'}

        for py_file in self.repo_root.rglob('*.py'):
            rel = str(py_file.relative_to(self.repo_root))
            if any(skip in rel for skip in skip_dirs):
                continue
            yield py_file

    def _process_file(self, py_file: Path):
        '''Process single file.'''
        try:
            source = py_file.read_text(errors='ignore')
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return

        module = self._file_to_module(py_file)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._process_function(node, module, py_file)
            elif isinstance(node, ast.Call):
                self._process_call(node, module)

    def _process_function(self, node: ast.FunctionDef, module: str, py_file: Path):
        '''Process function definition.'''
        func_name = node.name

        # Determine node type
        node_type = self._classify_function(func_name, module)

        key = f'{module}.{func_name}'

        self.graph.nodes[key] = MutationNode(
            module=module,
            function=func_name,
            file_path=str(py_file),
            line_number=node.lineno,
            node_type=node_type,
        )

        # Find calls within this function
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child)
                if call_name:
                    target_key = self._find_best_matching_node(call_name)
                    if target_key:
                        self.graph.nodes[key].calls.append(target_key)
                        self.graph.edges.append((key, target_key))

    def _process_call(self, node: ast.Call, module: str):
        '''Process function call.'''
        pass  # Handled in _process_function via ast.walk

    def _classify_function(self, func_name: str, module: str) -> str:
        '''Classify function type.'''
        if 'execute' in func_name.lower() and 'gateway' in module.lower():
            return 'gateway'
        if any(p in func_name.lower() for p in self._mutation_patterns):
            return 'mutation'
        if func_name.lower().startswith('g') and func_name[1:].isdigit():
            return 'gate'
        if 'actuate' in func_name.lower():
            return 'actuator'
        if 'apply' in func_name.lower():
            return 'mutation'
        return 'internal'

    def _get_call_name(self, node: ast.AST) -> str | None:
        '''Extract function name from call.'''
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _find_best_matching_node(self, name: str) -> str | None:
        '''Find node that best matches the call name.'''
        for node_key in self.graph.nodes:
            if name in node_key:
                return node_key
        return None

    def _link_nodes(self):
        '''Create reverse links (called_by).'''
        for source, target in self.graph.edges:
            if target in self.graph.nodes:
                if source not in self.graph.nodes[target].called_by:
                    self.graph.nodes[target].called_by.append(source)

    def _file_to_module(self, py_file: Path) -> str:
        '''Convert file path to module name.'''
        try:
            rel = py_file.relative_to(self.repo_root)
            parts = list(rel.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            elif parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except ValueError:
            return str(py_file)


# ── Formatters ────────────────────────────────────────────────────────────────

class TextFormatter:
    '''Format graph as human-readable text.'''

    @staticmethod
    def format(graph: ExecutionGraph) -> str:
        lines = [
            'ATOMFEDERATION-OS Execution Graph',
            '=' * 50,
            '',
            f'Total nodes: {len(graph.nodes)}',
            f'Total edges: {len(graph.edges)}',
            '',
        ]

        # Group by type
        by_type = {}
        for key, node in graph.nodes.items():
            if node.node_type not in by_type:
                by_type[node.node_type] = []
            by_type[node.node_type].append(node)

        for ntype, nodes in sorted(by_type.items()):
            lines.append(f'\n## {ntype.upper()} ({len(nodes)})')
            lines.append('-' * 40)

            for node in sorted(nodes, key=lambda n: n.module):
                key = f'{node.module}.{node.function}'
                lines.append(f'  {key}')
                lines.append(f'    File: {node.file_path}:{node.line_number}')

                if node.calls:
                    lines.append(f'    Calls: {len(node.calls)} → {node.calls[:3]}')
                if node.called_by:
                    lines.append(f'    Called by: {len(node.called_by)} ← {node.called_by[:3]}')

        lines.append('')
        return '\n'.join(lines)


class DotFormatter:
    '''Format graph as GraphViz DOT.'''

    @staticmethod
    def format(graph: ExecutionGraph) -> str:
        lines = [
            'digraph ExecutionGraph {',
            '  rankdir=TB;',
            '  node [shape=box, style=rounded];',
            '  edge [arrowhead=vee];',
            '',
        ]

        # Color by type
        colors = {
            'gateway': '#4CAF50',    # green
            'gate': '#2196F3',       # blue
            'mutation': '#F44336',   # red
            'actuator': '#FF9800',   # orange
            'internal': '#9E9E9E',   # gray
        }

        for key, node in graph.nodes.items():
            color = colors.get(node.node_type, '#9E9E9E')
            label = f'{node.function}\\n({node.module})'
            lines.append(f'  node_{hash(key) & 0xFFFFFFFF:x} [label=\"{label}\" fillcolor={color} style=filled];')

        lines.append('')

        for source, target in graph.edges:
            lines.append(f'  node_{hash(source) & 0xFFFFFFFF:x} -> node_{hash(target) & 0xFFFFFFFF:x};')

        lines.append('}')
        return '\n'.join(lines)


class JsonFormatter:
    '''Format graph as JSON.'''

    @staticmethod
    def format(graph: ExecutionGraph) -> str:
        data = {
            'nodes': [
                {
                    'id': key,
                    'module': node.module,
                    'function': node.function,
                    'file': node.file_path,
                    'line': node.line_number,
                    'type': node.node_type,
                    'calls': node.calls,
                    'called_by': node.called_by,
                }
                for key, node in graph.nodes.items()
            ],
            'edges': [{'from': s, 'to': t} for s, t in graph.edges],
        }
        return json.dumps(data, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Visualize ATOMFEDERATION-OS execution graph')
    parser.add_argument('--format', choices=['text', 'dot', 'json'], default='text',
                        help='Output format')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--repo-root', type=Path, default=None,
                        help='Repository root (default: script directory parent)')

    args = parser.parse_args()

    if args.repo_root is None:
        args.repo_root = Path(__file__).parent.parent

    # Build graph
    builder = ExecutionGraphBuilder(args.repo_root)
    graph = builder.build()

    # Format
    formatter = {
        'text': TextFormatter,
        'dot': DotFormatter,
        'json': JsonFormatter,
    }[args.format]

    output = formatter.format(graph)

    # Write
    if args.output:
        Path(args.output).write_text(output)
        log.info(f'Written to {args.output}')
    else:
        log.info(output)


if __name__ == '__main__':
    main()

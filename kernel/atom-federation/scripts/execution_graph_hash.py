#!/usr/bin/env python3
"""
execution_graph_hash.py — atom-federation-os v9.0+P0.2 Execution Graph Hasher

Builds a deterministic DAG of all execution entry points and their call-sites,
then produces a SHA256 hash binding the entire execution topology.

Scope:
  - All files in repo (excludes __pycache__, .git, atomos_pkg sibling)
  - Entry points: function defs named execute / apply_mutation / run / commit / propose
  - Call-sites: every Call node where the callee is a known execution entry
  - Gates: G1–G10, ACT as defined in execution_algebra_validator.py

Output:
  - graph_hash: hex SHA256 of sorted nodes+edges
  - graph.json: full adjacency list for audit/debug

Usage:
    python scripts/execution_graph_hash.py [--repo /path] [--output hash|json|save]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import sys
from dataclasses import dataclass, field

ENTRY_PATTERNS = (
    "execute", "apply_mutation", "run", "commit", "propose",
    "verify", "enforce", "accept", "commit", "finalize",
)


@dataclass
class ExecNode:
    name: str
    file: str
    line: int
    is_entry: bool
    calls: list[tuple[str, str]] = field(default_factory=list)  # (callee_file, callee_name)


@dataclass
class GraphStats:
    total_nodes: int = 0
    entry_nodes: int = 0
    total_edges: int = 0
    files_scanned: int = 0


def _safe_relative(p: pathlib.Path, root: pathlib.Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _collect_entry_points(tree: ast.AST, src_path: str) -> list[ExecNode]:
    """Find execution entry points in a single file."""
    nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            is_entry = any(
                node.name.lower().startswith(pat)
                for pat in ENTRY_PATTERNS
            )
            if is_entry:
                nodes.append(ExecNode(
                    name=node.name,
                    file=src_path,
                    line=node.lineno,
                    is_entry=is_entry,
                    calls=[],
                ))
    return nodes


def _collect_call_sites(tree: ast.AST, src_path: str, known_entries: list[str]) -> list[tuple[str, str, int]]:
    """
    Find all call-sites where the callee is a known execution entry point.
    Returns: [(callee_name, caller_name, line)]
    """
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = None
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr

            if callee and any(callee.startswith(pat) for pat in ENTRY_PATTERNS):
                calls.append((callee, _extract_caller_name(tree, node), node.lineno))
    return calls


def _extract_caller_name(tree: ast.AST, call_node: ast.Call) -> str:
    """Find the function name containing this call."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is call_node:
                    return node.name
    return "?"


def build_execution_graph(repo_path: pathlib.Path) -> tuple[list[ExecNode], GraphStats]:
    """Walk all .py files, build execution graph."""
    nodes_by_file: dict[str, list[ExecNode]] = {}
    stats = GraphStats()

    all_py = sorted(repo_path.rglob("*.py"))

    for py_path in all_py:
        rel = _safe_relative(py_path, repo_path)
        if ("__pycache__" in rel or ".git" in rel or
                "/.pytest_cache/" in rel or "\\.pytest_cache\\" in rel or
                "atomos_pkg" in rel):
            continue

        stats.files_scanned += 1
        try:
            text = py_path.read_text(errors="ignore")
        except Exception:
            continue

        try:
            tree = ast.parse(text, filename=str(py_path))
        except SyntaxError:
            continue

        nodes = _collect_entry_points(tree, rel)
        for node in nodes:
            node.calls = [(rel, c[0]) for c in _collect_call_sites(tree, rel, [])]

        if nodes:
            nodes_by_file[rel] = nodes

    # Flatten
    all_nodes = []
    for file_nodes in nodes_by_file.values():
        all_nodes.extend(file_nodes)

    stats.total_nodes = len(all_nodes)
    stats.entry_nodes = sum(1 for n in all_nodes if n.is_entry)
    stats.total_edges = sum(len(n.calls) for n in all_nodes)

    return all_nodes, stats


def hash_graph(nodes: list[ExecNode]) -> str:
    """
    Deterministic SHA256 of execution graph.
    Nodes sorted by (file, line, name), edges sorted within each node.
    """
    hasher = hashlib.sha256()

    for node in sorted(nodes, key=lambda n: (n.file, n.line, n.name)):
        hasher.update(f"{node.file}:{node.line}:{node.name}".encode())
        hasher.update(f"entry={node.is_entry}".encode())
        # Sort edges for determinism
        for callee_file, callee_name in sorted(node.calls):
            hasher.update(f"call:{callee_file}:{callee_name}".encode())

    return hasher.hexdigest()


def save_graph(nodes: list[ExecNode], stats: GraphStats, graph_hash: str,
               output_path: pathlib.Path) -> None:
    """Save full graph to formal_model/execution_graph.json"""
    graph_data = {
        "version": "9.0+P0.2",
        "graph_hash": graph_hash,
        "stats": {
            "total_nodes": stats.total_nodes,
            "entry_nodes": stats.entry_nodes,
            "total_edges": stats.total_edges,
            "files_scanned": stats.files_scanned,
        },
        "nodes": [
            {
                "name": n.name,
                "file": n.file,
                "line": n.line,
                "is_entry": n.is_entry,
                "calls": [{"file": cf, "name": cn} for cf, cn in n.calls],
            }
            for n in sorted(nodes, key=lambda x: (x.file, x.line, x.name))
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph_data, indent=2, sort_keys=True))
    print(f"Saved: {output_path}  graph_hash={graph_hash}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Execution Graph Hasher")
    parser.add_argument("--repo", type=pathlib.Path,
                        default=pathlib.Path(__file__).parent.parent,
                        help="Repository root (default: script parent)")
    parser.add_argument("--output", choices=["hash", "json", "save"],
                        default="hash")
    parser.add_argument("--expected-hash",
                        help="Fail if computed hash != expected")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.exists():
        print(f"ERROR: repo not found: {repo}", file=sys.stderr)
        return 1

    nodes, stats = build_execution_graph(repo)
    graph_hash = hash_graph(nodes)

    if args.output == "save":
        save_graph(nodes, stats, graph_hash,
                   repo / "formal_model" / "execution_graph.json")
        return 0

    if args.output == "hash":
        print(graph_hash)

    if args.output == "json":
        result = {
            "graph_hash": graph_hash,
            "stats": {
                "total_nodes": stats.total_nodes,
                "entry_nodes": stats.entry_nodes,
                "total_edges": stats.total_edges,
                "files_scanned": stats.files_scanned,
            },
        }
        print(json.dumps(result, indent=2))

    if args.expected_hash and graph_hash != args.expected_hash:
        print(f"MISMATCH: computed={graph_hash}  expected={args.expected_hash}",
              file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

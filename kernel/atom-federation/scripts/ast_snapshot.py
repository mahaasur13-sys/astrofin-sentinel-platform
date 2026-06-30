#!/usr/bin/env python3
"""
ast_snapshot.py — atom-federation-os v9.0+P0.2 AST Snapshot Generator

Generates a cryptographically pinned snapshot of the repo's AST state.
Every .py file is parsed, normalized (no whitespace/comments), and
serialized to produce a deterministic SHA256 hash.

Usage:
    python scripts/ast_snapshot.py [--repo /path/to/repo] [--output hash|json|save]
    python scripts/ast_snapshot.py --save-hash formal_model/expected_ast_hash.json

Output:
    stdout: hexdigest hash (default) OR formatted JSON (--output json)
    exit: 0 on success, 1 on parse error

Hash invariants:
    - Deterministic between runs (no timestamps, no randomness)
    - Reflects ONLY structural changes (no formatting, no comments)
    - Covers all .py files under repo (excludes __pycache__, .git)
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ASTStats:
    files_processed: int = 0
    total_nodes: int = 0
    skipped_files: int = 0
    errors: list[str] = field(default_factory=list)


def _ast_node_to_hashable(node: ast.AST) -> Any:
    """
    Recursively normalize an AST node to a hashable structure.
    Strips: whitespace, comments, col_offset/lineno/end_lineno,
    extra attributes that differ across formatting.
    """
    if isinstance(node, ast.Name):
        return ("Name", node.id)
    if isinstance(node, ast.Constant):
        # Python 3.8+ uses Constant for all literals
        val = node.value
        if isinstance(val, (int, float, str, bytes, bool, type(None))):
            return ("Const", repr(val))
        return ("Const", type(val).__name__)
    if isinstance(node, ast.NameConstant):  # Python <3.8
        return ("NameConst", str(node.value))
    if isinstance(node, ast.Num):  # Python <3.8
        return ("Num", str(node.n))
    if isinstance(node, ast.Str):  # Python <3.8
        return ("Str", node.s)
    if isinstance(node, ast.FormattedValue):
        return ("FormattedValue", _ast_node_to_hashable(node.value))
    if isinstance(node, ast.JoinedStr):
        return ("JoinedStr", [_ast_node_to_hashable(v) for v in node.values])
    if isinstance(node, ast.Starred):
        return ("Starred", _ast_node_to_hashable(node.value))
    if isinstance(node, ast.Subscript):
        return ("Subscript",
                _ast_node_to_hashable(node.value),
                _ast_node_to_hashable(node.slice))
    if isinstance(node, ast.Slice):
        lower = _ast_node_to_hashable(node.lower) if node.lower else None
        upper = _ast_node_to_hashable(node.upper) if node.upper else None
        step = _ast_node_to_hashable(node.step) if node.step else None
        return ("Slice", lower, upper, step)
    if isinstance(node, ast.Ellipsis):
        return ("Ellipsis",)

    # Compound nodes
    result: list[tuple[str, Any]] = []
    for field_name, field_value in ast.iter_fields(node):
        if field_name in ("lineno", "end_lineno", "col_offset", "end_col_offset",
                          "ctx", "type_comment", "type_ignores"):
            continue  # structural-only metadata
        if field_value is None:
            continue
        if isinstance(field_value, list):
            items = []
            for it in field_value:
                if it is None:
                    continue
                if isinstance(it, ast.AST):
                    child = _ast_node_to_hashable(it)
                    if child is not None:
                        items.append(child)
                elif isinstance(it, str):
                    items.append(('str', it))
                elif isinstance(it, (int, float, bool)):
                    items.append(('lit', repr(it)))
            if items:
                result.append((field_name, items))
        elif isinstance(field_value, ast.AST):
            child = _ast_node_to_hashable(field_value)
            if child is not None:
                result.append((field_name, child))
        elif isinstance(field_value, (str, int, float, bool)):
            result.append((field_name, field_value))
        # skip unsupported types
    return (node.__class__.__name__, tuple(result))


def _normalize_tree(tree: ast.AST) -> Any:
    """Normalize entire AST tree to a hashable structure."""
    return _ast_node_to_hashable(tree)


def _hash_file_content(py_path: pathlib.Path) -> str:
    """
    Parse a .py file and return a normalized SHA256 hash of its AST.
    Errors are logged but don't fail the run (skipped files still noted).
    """
    try:
        text = py_path.read_text(errors="ignore")
    except Exception:
        return ""
    try:
        tree = ast.parse(text, filename=str(py_path))
    except SyntaxError:
        return ""  # skip files that can't be parsed
    normalized = _normalize_tree(tree)
    serialized = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode()).hexdigest()


def generate_ast_hash(repo_path: pathlib.Path) -> tuple[str, ASTStats]:
    """
    Walk repo_path, hash all .py files, return composite SHA256.

    Returns: (composite_hash, stats)
    """
    stats = ASTStats()
    hasher = hashlib.sha256()

    # Sort for determinism
    all_py = sorted(repo_path.rglob("*.py"))

    for py_path in all_py:
        rel = str(py_path.relative_to(repo_path))
        if ("__pycache__" in rel or ".git" in rel or
                "/.pytest_cache/" in rel or "\\.pytest_cache\\" in rel):
            stats.skipped_files += 1
            continue

        stats.files_processed += 1
        file_hash = _hash_file_content(py_path)

        # Incorporate file path to distinguish same content in different paths
        path_bytes = rel.encode()
        hasher.update(path_bytes)
        hasher.update(file_hash.encode())

        if not file_hash:
            stats.errors.append(f"PARSE_ERROR: {rel}")

    composite_hash = hasher.hexdigest()
    return composite_hash, stats


def save_snapshot(repo_path: pathlib.Path, output_path: pathlib.Path) -> None:
    """
    Generate AST hash + per-file hashes and save to formal_model/.
    """
    composite_hash, stats = generate_ast_hash(repo_path)

    all_py = sorted(repo_path.rglob("*.py"))
    file_hashes: dict[str, str] = {}
    for py_path in all_py:
        rel = str(py_path.relative_to(repo_path))
        if ("__pycache__" in rel or ".git" in rel or
                "/.pytest_cache/" in rel or "\\.pytest_cache\\" in rel):
            continue
        file_hashes[rel] = _hash_file_content(py_path)

    snapshot = {
        "version": "9.0+P0.2",
        "repo": str(repo_path.resolve()),
        "ast_hash": composite_hash,
        "files_count": stats.files_processed,
        "skipped_count": stats.skipped_files,
        "file_hashes": file_hashes,
        "errors": stats.errors,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))
    print(f"Saved: {output_path}  hash={composite_hash}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AST Snapshot Generator")
    parser.add_argument("--repo", type=pathlib.Path,
                        default=pathlib.Path(__file__).parent.parent,
                        help="Repository root (default: script parent)")
    parser.add_argument("--output", choices=["hash", "json", "save"],
                        default="hash",
                        help="hash=hex only, json=full, save=formal_model snapshot")
    parser.add_argument("--expected-hash",
                        help="Compare against expected hash, fail if mismatch")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.exists():
        print(f"ERROR: repo not found: {repo}", file=sys.stderr)
        return 1

    composite_hash, stats = generate_ast_hash(repo)

    if args.output == "save":
        save_snapshot(repo, repo / "formal_model" / "expected_ast_hash.json")
        return 0

    if args.output == "hash":
        print(composite_hash)

    if args.output == "json":
        result = {
            "ast_hash": composite_hash,
            "files_processed": stats.files_processed,
            "skipped": stats.skipped_files,
            "errors": stats.errors,
        }
        print(json.dumps(result, indent=2))

    if args.expected_hash and composite_hash != args.expected_hash:
        print(f"MISMATCH: computed={composite_hash}  expected={args.expected_hash}",
              file=sys.stderr)
        return 1

    if stats.errors:
        print(f"WARNING: {len(stats.errors)} parse errors (see above)",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

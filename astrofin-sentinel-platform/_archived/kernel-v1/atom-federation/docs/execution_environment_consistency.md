# Execution Environment Consistency Guide

**atom-federation-os v9.0+P7**

---

## Problem

The execution algebra (P0–P5) operates at two levels simultaneously:
1. **Filesystem level** — AST analysis, static validators
2. **Runtime level** — Python import graph, actual execution

When these diverge, validators pass but runtime fails — or vice versa.

## Canonical Root

```
CANONICAL_ROOT = /home/workspace/atom-federation-os
```

All tools, tests, and CI MUST operate within this root.

## Single Source of Truth Rules

| Rule | Description |
|------|-------------|
| **One root** | All modules load from `CANONICAL_ROOT`. No sibling package imports. |
| **Canonical paths first** | `sys.path` must have `CANONICAL_ROOT` and its subdirs before `''` (cwd) |
| **No shadowing** | A module name must resolve to exactly one `.py` file across all `sys.path` entries |
| **Import order** | `chdir(CANONICAL_ROOT)` before importing any project modules |

## Tool Inventory

| Tool | Location | Purpose |
|------|----------|---------|
| `execution_algebra_validator.py` | `scripts/` | AST-level gate enforcement check |
| `symbolic_execution_checker.py` | `tools/` | Call-site graph + stale nonce verification |
| `verify_workspace_root.py` | `scripts/` | Runtime import graph + sys.path consistency |
| `test_p5_proof_carrying.py` | `tools/` | End-to-end P5 proof system tests |
| `test_p7_bft.py` | `tools/` | BFT consensus layer tests |

## Running Tools

```bash
# Always from canonical root
cd /home/workspace/atom-federation-os

# 1. Workspace consistency (diagnostic + pass/fail)
python scripts/verify_workspace_root.py

# 2. Execution algebra (static AST check)
python scripts/execution_algebra_validator.py --repo .

# 3. Symbolic proof (runtime stale nonce check)
python tools/symbolic_execution_checker.py

# 4. P5 proof-carrying tests
python tools/test_p5_proof_carrying.py

# Full suite
python scripts/verify_workspace_root.py \
  && python scripts/execution_algebra_validator.py --repo . \
  && python tools/symbolic_execution_checker.py \
  && python tools/test_p5_proof_carrying.py
```

## CI Configuration

```yaml
env:
  PYTHONPATH: /home/workspace/atom-federation-os
  ATOM_REPO_ROOT: /home/workspace/atom-federation-os
```

The `workspace-consistency` job runs FIRST. If it fails, no other jobs execute.

## sys.path Order

Correct:
```
[0] /home/workspace/atom-federation-os/scripts
[1] /usr/local/lib/python3.12/...
[2] ...
```

Wrong (shadowing risk):
```
[0] ''                              ← cwd (stale files)
[1] /home/workspace/atom-federation-os  ← canonical AFTER cwd
```

Fix: `cd /home/workspace/atom-federation-os` before running anything.

## Validation Summary

| Phase | Validator | Status |
|-------|-----------|--------|
| P0–P1 | `execution_algebra_validator.py` | ✅ 10/10 gates, 2 entries |
| P3 | `symbolic_execution_checker.py` | ✅ proof valid |
| P4 | `runtime_guard.py` | ✅ runtime enforcement |
| P5 | `test_p5_proof_carrying.py` | ✅ 9/9 tests |
| P6 | `test_p6_federation.py` | ✅ quorum + ledger |
| P7 | `test_p7_bft.py` | ✅ BFT consensus |
| — | `verify_workspace_root.py` | ✅ consistent |

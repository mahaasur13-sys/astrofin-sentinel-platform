# ADR-0010: Legacy Test Exemptions for v1.0.0 GA

**Status:** Accepted — 2026-08-11
**Authors:** Felix (Senior Architect)
**Supersedes:** Sprint 3 dead-skip audit findings (2026-08-08)

## Context

34 unit tests in `tests/conftest.py` KI-125a skip list depend on archived or legacy modules: kernel/atom-federation, v6/v7/v8 agents, pre-contract agent architecture. These modules were moved to `archive/legacy_versions/` during Sprint B cleanup and are not imported in any production code path.

The conftest.py skip-list also contains 57 entries organized into:
- **Category A** (~10): Missing optional imports (ollama, sentence_transformers, faiss, swisseph)
- **Category C** (~5): Async/sync mismatch (0 viable — dead skips from removed tests)
- **Category D** (~3): Data dependency on external files
- **Category F** (34): Legacy/archived modules
- **Dynamic** (~5): Inline pytest.skip() calls with runtime conditions

## Decision

These 34 Category F tests are **formally exempted** from v1.0.0 GA requirements. They are retained in the skip-list with ADR-0010 justification to preserve traceability, but **will not be restored** until v1.1.0 architecture refactoring.

The remaining 23 tests (Categories A, C, D) have:
- Importorskip annotations
- Mock-based fixes in feature branches
- Runtime condition skips (pytest.skip())

## Rationale

1. **Zero production impact**: Archived code has zero callers in `agents/_impl/`, `core/`, or `api/`
2. **Resource allocation**: No developer time on legacy fixes before GA
3. **Risk mitigation**: Archived code cannot activate accidentally—it's not imported by any `__init__.py`
4. **Cost of fix**: Restoring these tests would require full module re-imports, which takes 2+ sprints

## Skip IDs (Category F — Legacy)

All entries under the `# --- legacy/module (X) ---` heading in `tests/conftest.py` SKIP_LIST_KI_125A, including:
- atom-federation test suite
- kernel/federation tests
- v6/v7/v8 legacy agent tests
- roma-execution-bridge tests (archived)

## Consequences

- **Positive**: Clean test report with documented exemptions; no false CI failures
- **Negative**: If archived code is accidentally activated, 0 test coverage
- **Mitigation**: Archive integrity check in `freeze-check.sh` verifies no legacy imports in production paths

## References

- PR #283: KI-125a guard comment — no mass-unskip without `--count=10`
- PR #288: Sprint 4 security review + freeze-ready
- `docs/audit/ki125a-triage-2026-07-26.md` — full triage classification

# ADR-0010: Legacy Test Exemptions for v1.0.0 GA

**Status:** Accepted — 11.08.2026  
**Author:** Sprint 4 — KI-125a Cleanup  
**Supersedes:** _none_  
**Superseded by:** _none_

## Context

KI-125a skip-list contains 71 entries (57 in `conftest.py` + 14 inline). After Sprint 2+3 triage:
- 5 quick wins restored (healthcheck, ralph_safety, types, settings, dual_mode)
- 0 viable async mismatch tests (Batch C — removed)
- 4 http_client tests restored (lifespan-managed AsyncClient, PR #284)

Remaining skip entries fall into these categories:

| Category | Count | Description |
|----------|-------|-------------|
| A (imports) | 10 | Missing optional deps (acos_contracts, hypothesis, flask_limiter, pyswisseph) |
| B (stubs) | 24 | _StubMethod type errors, interface drift in observability/metrics |
| C (async) | 4 | Event loop race — **FIXED** in PR #284, pending merge |
| E (drift) | 7 | Test-to-production naming/interface drift |
| F (legacy) | 6 | `test_compromise_agent.py` — tests pre-contract KARL synthesis agent |
| I (infra) | 16 | Real-mode backtest/integration requiring full pipeline |

## Decision

**Category F (6 tests: `test_compromise_agent.py`)** is formally exempted from v1.0.0 GA requirements.

These tests exercise the pre-contract KARL synthesis pathway (`agents/_impl/compromise_agent.py`), which was superseded by `KARLSynthesisAgent` in ATOM-013. The module is retained for traceability but is not on the active import path in production.

The skip-list entries for these tests are retained until v1.1.0 architecture refactoring, at which point the module and its tests will be evaluated for archival or rewrite.

## Consequences

- **Positive:** No developer time spent on pre-contract legacy tests before GA
- **Negative:** If `compromise_agent.py` is accidentally imported by code paths, no test coverage. Mitigation: the module has no active importers in `api/`, `core/`, or `orchestration/`
- **Risk:** v1.1.0 refactoring may uncover design debt in KARL synthesis. Mitigation: ATOM-013 provides the replacement contract

## Exempted Tests

```python
# conftest.py — KI-125A skip list, Category F (ADR-0010)
"tests/test_compromise_agent.py::test_happy_path",
"tests/test_compromise_agent.py::test_empty_state",
"tests/test_compromise_agent.py::test_malformed_state",
"tests/test_compromise_agent.py::test_data_source_unavailable",
"tests/test_compromise_agent.py::test_missing_ephemeris",
"tests/test_compromise_agent.py::test_large_input",
```

## Review

- **Next review:** v1.1.0 planning (Q4 2026)
- **Trigger:** KARL synthesis refactoring
- **Owner:** @felix (asurdev)

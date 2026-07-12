# Known Issues — astrofin-sentinel-platform

**Last updated:** 2026-07-12
**Master HEAD:** `5248a59` (PR #189 merged)
**Status snapshot:** pytest 551 passed / 4 failed / 68 skipped / 2 xfail; coverage 41.75%

This file is the single source of truth for tracked, accepted technical debt.
Anything not listed here is, by definition, a fresh regression.

---

## KI-125a — Pre-existing test failures (51 tests skipped)

**Tracked in:** #149
**Skipped in:** `tests/conftest.py` via `pytest.skip(..., reason="KI-125a: ...")`
**Originally:** 41 tests, expanded to 51 after the wider Phase 4 sweep

### Skip breakdown (51)

| Bucket | Count | Notes |
|---|---:|---|
| Logic / interface drift (calibration, RAG, observability, types, dual_mode) | ~32 | Tests written against an older interface; production code evolved, tests never updated |
| TypeError: `_StubMethod` / stub object issues | ~13 | Missing test doubles in fixtures; affects `tests/test_observability_*.py`, `tests/test_macro_agent.py`, `tests/test_metrics_endpoint.py`, `tests/test_metrics_cli.py`, `tests/test_rag_metrics.py` |
| Missing dependencies (acos-contracts, hypothesis, flask-limiter) | 3 | `tests/architecture/test_architecture_linter.py`, `tests/test_imports.py`, `tests/test_rate_limit.py` |
| Other (1 test each: test_compromise_agent, test_rate_limit, test_strategy_pool, test_logging, test_macro_agent, test_meta_rl, test_dual_mode, test_ephemeris_decorator) | 8 | Same root cause; tracked together |

### Acceptance criteria

- [ ] All 51 tests removed from `SKIP_LIST` in `tests/conftest.py`
- [ ] Each test either passes or is replaced with a corrected version
- [ ] `quality-gate` job shows 0 collected-skipped (from this bucket) and 0 failures
- [ ] This entry moved to "Resolved" or deleted

### Implementation roadmap (1–4 PRs)

1. **Bucket 1 (deps)** — add `acos-contracts`, `hypothesis`, `flask-limiter` to `requirements-dev.txt`
2. **Bucket 2 (stubs)** — fix or regenerate the `_StubMethod` fixtures
3. **Bucket 3 (drift)** — read the current production-code interface and update test assertions; if the production code is the wrong one, fix it and add a regression comment
4. **Cleanup PR** — remove the 51 skip markers, delete this entry, close #149

Estimated effort: ~150–300 lines of test changes; no production code changes expected unless a real bug surfaces.

---

## KI-125 — Flaky `tests/test_backtest_real_agents.py` (11 tests skipped)

**Tracked in:** #125
**Skipped in:** `tests/test_backtest_real_agents.py` with reason `"flaky test, will be fixed separately — see issue #125"`
**Affected lines:** 19, 45, 68, 103, 123, 145, 167, 194, 214, 234, 254 (11 skips)

These are real-agent backtests that fail intermittently in CI due to timing/network/order-of-execution sensitivity.

### Acceptance criteria

- [ ] Mark `@pytest.mark.flaky` with auto-rerun (e.g. `pytest-rerunfailures`) OR introduce deterministic stub mode for CI
- [ ] Pass rate ≥ 95% over 10 consecutive CI runs

---

## KI-AUTH-01 — Auth decorator regression (4 tests failing)

**Status:** NEW (uncovered by Phase 4 full test run on 2026-07-12)
**Tracked in:** none yet — opens a new issue
**Failing:**
- `tests/test_auth_empty_key.py::test_empty_api_key_returns_500`
- `tests/test_auth_flask_decorator.py::test_require_api_key_missing_key`
- `tests/test_auth_flask_decorator.py::test_require_api_key_wrong_key`
- `tests/test_auth_flask_decorator.py::test_require_api_key_empty_env_key_should_reject_all`

Likely introduced by PR #176/#182 (ERR-01 error envelope) — the new envelope shape changed the assertion surface for the Flask decorator. **Must be fixed before next release** (regression, not a known issue).

### Acceptance criteria

- [ ] All 4 tests pass on master
- [ ] Behaviour preserved: empty env key must reject ALL requests (security-critical)
- [ ] Coverage of `core/auth/*` ≥ 80%

---

## KI-AGENT-01 — `_fetch_ohlcv` not implemented on agents (9 tests skipped)

**Status:** NEW
**Skipped in:** `tests/test_agents_async_mass.py`, `tests/test_options_flow_agent_async.py`
**Affected agents:** QuantAgent, MLPredictorAgent, FundamentalAgent, OptionsFlowAgent

The async HTTP OHLCV path is missing on these agents. The tests were skipped so that the async mass smoke could land.

### Acceptance criteria

- [ ] All 4 agents implement `_fetch_ohlcv` against the same async HTTP client used by other agents
- [ ] Skip markers removed
- [ ] 1 new integration test per agent

---

## KI-EPHE-01 — Ephemeris test for OptionsFlowAgent (1 xfail)

**Status:** tracked via xfail
**Test:** `tests/test_options_flow_agent_async.py::test_options_flow_agent_uses_async_http`
**Reason:** `_fetch_ohlcv not implemented on OptionsFlowAgent`

Subsumed by **KI-AGENT-01**.

---

## KI-AUTH-02 — Constant-time compare order-dependent test (1 xfail)

**Tracked in:** KI-128 followup
**Test:** `tests/auth/test_require_api_key_decorator.py::test_constant_time_compare_used`
**Reason:** order-dependent secrets monkeypatch

### Acceptance criteria

- [ ] Test rewritten to not depend on monkeypatch ordering, or moved to integration tier with isolated env
- [ ] Marked as passed (xfail removed)

---

## KI-EXT-01 — Ralph benchmark external agent (1 test skipped)

**Test:** `tests/ralph_benchmark/test_agent_basic.py`
**Reason:** `Requires external Ralph agent`

This is intentional — Ralph lives in a separate repo. The skip is permanent, but the test remains in the tree as a contract for future integration.

**No action needed.** Documented for traceability.

---

## KI-METRICS-01 — FastAPI metrics endpoint (1 test skipped)

**Test:** `tests/test_auth.py::test_fastapi_metrics_endpoint`
**Reason:** `FastAPI metrics endpoint not yet implemented`
**Tracked in:** overlaps with #173 (ERR-01)

### Acceptance criteria

- [ ] FastAPI metrics endpoint exists at `/metrics` returning Prometheus exposition format
- [ ] Skip removed

---

## Tech-debt overlays (not in CI, not breaking, but expensive)

### OVERLAY-01 — `audit_repo/` historical snapshot (on disk only)

**Status:** Removed from git index in PR #187, archived in docs (PR #188). Directory still present on local disk (not in worktree).
**Action:** When working with a fresh clone, `audit_repo/` is absent — historical reference only. Do not add to fresh clones.

### OVERLAY-02 — `atom-core/` (3 tracked files, marked LIVE)

**Status:** Tracked, README banner says: *«Живой Go‑роутер (packages/atom-router/). Не удалять.»*
**Action:** None. Keep banner; verify the path is consistent with the actual Go module location.

### OVERLAY-03 — `astrofin_sentinel_v5.egg-info/` (untracked)

**Status:** Build artifact, not tracked, in `.gitignore`.
**Action:** None. Will be regenerated on next `uv sync` / `pip install -e .`.

### OVERLAY-04 — `agents/_impl/amre/audit.py.bak-006` (tracked, leaky)

**Status:** Tracked `.bak` artifact; should be deleted.
**Action:** Open chore PR: `git rm agents/_impl/amre/audit.py.bak-006` + commit.

### OVERLAY-05 — `graphify-out/inferred_sample_balanced.jsonl.bak-pre-Aprime` (tracked, leaky)

**Status:** Same as OVERLAY-04.
**Action:** Open chore PR: `git rm graphify-out/inferred_sample_balanced.jsonl.bak-pre-Aprime` + commit.

### OVERLAY-06 — `coverage.xml` at repo root (tracked? untracked?)

**Status:** Coverage report; not in `.gitignore` (verify). 860 KB on disk.
**Action:** Add to `.gitignore` if not already. Run `git check-ignore -v coverage.xml` to confirm.

---

## Open issues referenced from this file

- #125 — Umbrella: tests + coverage gaps
- #126 — Umbrella: arch-lint / code quality
- #128 — Constant-time compare followup
- #149 — **KI-125a** (51 skipped tests)
- #170 — SEC-02: Move hardcoded cluster URLs to ConfigMap/env vars
- #173 — ERR-01: Migrate bare `except:` blocks to logged re-raise
- #130 — P3: Codebase size — audit necessity of 1,490 Python files in `deploy/`

## Recently closed (Phase 4 — 2026-07-12)

- PR #176, #182, #184, #186 — closed as stale (content already in master via #174, #123, #134)
- PR #27, #28, #31, #32, #44, #103, #120, #121, #122 — closed as stale
- PR #189 — merged (artifacts/best_practices)
- PR #188 — merged (audit_repo/ docs as [ARCHIVED])
- PR #187 — merged (audit_repo/ removed from index)
- PR #185 — merged (setup-uv@v3)
- PR #183 — merged (auth tests reload isolation)

## Open PRs after Phase 4

- #181 — ATOM-GITAGENT-002: Phase 2 GitAgent + MCP Tools Integration (real debt; not stale)

---

## How to use this file

- **Before opening a new known-issue** — check this file first; update rather than duplicate.
- **When the issue is fixed** — move the entry to "Recently closed" with the closing PR / commit SHA, then trim after one cycle.
- **When a skip is added to `conftest.py`** — there MUST be a corresponding entry here with a tracked issue number. No anonymous skips.

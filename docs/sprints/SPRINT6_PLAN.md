# Sprint 6 — Plan (2026-08-11 through 2026-08-24)

**Status:** 📋 Planning  
**Branch:** `sprint6/ki125a-batch-a` (to be created)  
**Target:** 25→0 KI-125a entries  
**Freeze:** 2026-08-25

## Batch Breakdown (≤10 tests/PR, guard #283)

| Batch | Categories | Tests | Complexity | Dates |
|-------|-----------|-------|------------|-------|
| A | imports, http_client, strategy_pool, macro_agent/metrics, ralph_safety/types | 9 | Low — drift/stub fixes | 11.08–14.08 |
| B | architecture, dual_mode/ephemeris/logging/meta_rl, pre-existing (3) | 10 | Medium — may need module | 15.08–18.08 |
| C | pre-existing (3), backtest_real_agents (6) | 9 | High — integration/real-mode | 19.08–22.08 |

Buffer: 23.08–24.08

## Architectural Decisions (pre-Sprint)

### AD-01: acos_contracts → DEPRECATE

- **Finding:** 0 production imports of `acos_contracts`
- **Action:** Delete 3 architecture tests. Module is dead code.
- **Rationale:** Same as ADR-0010 — don't restore archaeological artifacts for GA.

### AD-02: hypothesis → DELETE test

- **Finding:** `test_hypothesis_importable` tests import of non-required dependency
- **Action:** Delete the test. Don't add hypothesis to [dev].
- **Rationale:** Not a GA-critical dependency. Adding it just for 1 test increases CI time.

### AD-03: backtest_real_agents (9) → NIGHTLY

- **Finding:** Entire module has `pytestmark = skip(reason="flaky — hangs on agent.run()")`
- **Action:** Move from KI-125a to `tests/integration/backtest/` + `nightly-backtest.yml`
- **Rationale:** Tests require real agent pipeline, hang in CI sandbox. Not PR-gate material.

## Known Risks

| Risk | Mitigation |
|------|------------|
| RAG test isolation | Add fixture teardown in Batch B |
| backtest_real hangs | Nightly job, non-blocking |
| pre-existing failures (6) | Batch A + Batch B timebox 2h/test |

## Plan

1. Create `sprint6/ki125a-batch-a` from `release/v1.0.0`
2. Implement AD-01 (delete 3 architecture tests + acos-contracts dir)
3. Implement AD-02 (delete 1 imports test)
4. Restore 9 sprint6 Batch A tests
5. Implement AD-03 (nightly job) in Batch C

# PR2 — Pattern A uniformity + import order + pytest markers

**Date:** 2026-06-17
**Scope:** 14 agents + 33 test files + pyproject.toml

## Changes

### 1. Pattern A: `from __future__ import annotations` added to 14 agents
All 14 agents now have `from __future__ import annotations` on a line
by itself, immediately after the module docstring, matching the canonical
pattern in `_template_agent.py`.

  - `agents/_impl/technical_agent.py` ✓
  - `agents/_impl/synthesis_agent.py` ✓
  - `agents/_impl/options_flow_agent.py` ✓
  - `agents/_impl/sentiment_agent.py` ✓
  - `agents/_impl/macro_agent.py` ✓
  - `agents/_impl/bear_researcher.py` ✓
  - `agents/_impl/bull_researcher.py` ✓
  - `agents/_impl/market_analyst.py` ✓
  - `agents/_impl/elliot_agent.py` ✓
  - `agents/_impl/ml_predictor_agent.py` ✓
  - `agents/_impl/electoral_agent.py` ✓
  - `agents/_impl/fundamental_agent.py` ✓
  - `agents/_impl/quant_agent.py` ✓
  - `agents/_impl/bradley_agent.py` ✓

### 2. Pytest markers registered + applied to 33 test files
Registered 3 markers in `pyproject.toml` under `[tool.pytest.ini_options]`:
- `unit` — fast unit tests, no external deps (default)
- `integration` — tests hitting network/DB/disk
- `slow` — tests that take >1s

Applied `@pytest.mark.unit` to 74 test functions across 33 test files.

### 3. `meta_rl/basket.py`
**No change needed.** `from __future__ import annotations` is already
on line 3 (correct first-statement position after the module docstring).

### 4. `.bak` files
**None exist** in the repo. Searched via `find . -name '*.bak'`.

## Verification
- All 14 agent files: `python3 -m py_compile` → OK
- Pattern A structural check (`@track_agent_metrics`, `_degraded`, `EPHEMERIS_UNAVAILABLE`, `UNKNOWN`, `EphemerisUnavailableError`): 14/14 already present (no regression)
- PR1 smoke test (`tests/test_compromise_agent.py`): 7/7 pass

## Note on Pattern A in pre-existing code
All 19 pre-existing agents already had `@track_agent_metrics` +
`try/except → _degraded` in their `run()` method. The only missing
piece across the codebase was `from __future__ import annotations`.
14 highest-import-count agents were updated to match the canonical template.

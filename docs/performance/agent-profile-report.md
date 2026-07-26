# Agent Profiling Report — Top-3 Bottlenecks

> **Date:** 2026-07-26  |  **Tool:** cProfile + pstats

## Profiled Agents

| Agent | File | Lines | Avg Time (100 runs) | Top Function |
|-------|------|-------|---------------------|-------------|
| GannAgent | `agents/_impl/gann_agent.py` | 409 | (fill) ms | (fill) |
| BradleyAgent | `agents/_impl/bradley_agent.py` | 277 | (fill) ms | (fill) |
| ElliotAgent | `agents/_impl/elliot_agent.py` | (fill) | (fill) ms | (fill) |

## Top-3 Bottlenecks

### 1. get_planetary_positions (Swiss Ephemeris)

- **Impact:** (fill) % of total time
- **Reason:** C-FFI call to ephemeris library is expensive
- **Recommendation:** Cache for 60 seconds (already has circuit breaker, add `functools.lru_cache` or Redis TTL)
- **Status:** P1 — add cache before GA

### 2. pandas/numpy vectorization

- **Impact:** (fill) % of total time
- **Reason:** Per-row operations instead of vectorized
- **Recommendation:** Replace `.apply()` with `.transform()`, pre-compute indicators once
- **Status:** P2 — v1.1.0 optimization

### 3. Dynamic imports

- **Impact:** (fill) % of total time (if any)
- **Reason:** `importlib.util.spec_from_file_location` in older agent code
- **Recommendation:** Sprint F added pydantic contracts — switch to static imports
- **Status:** P2 — audit all agents for dynamic imports

## Profiling Data

Raw `.prof` files available in `docs/performance/`:
- `profile_gann.prof`
- `profile_bradley.prof`
- `profile_elliot.prof`

## Reproduce

\`\`\`bash
python scripts/profile_agents.py
\`\`\`

## Recommendations for v1.1.0

1. Add ephemeris cache (Redis TTL 60s or functools.lru_cache)
2. Vectorize pandas operations in QuantAgent/MacroAgent
3. Pre-load agent modules at startup (avoid lazy import)
4. Consider Cython/numba for hot paths in technical indicators

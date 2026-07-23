# Release Notes — ACOS SCL v6.0.0

**Commit:** `50afd16`  
**Date:** 2026-04-08  
**Tag:** `v6.0.0`

---

## Overview

ACOS SCL v6 — полностью верифицированная событийно-ориентированная система с детерминированным воспроизведением, неизменяемыми событиями и линейной производительностью O(1) доступа к трассировкам. Все 13 инвариантов и патчей подтверждены тестами.

---

## What's New

### ✅ 10 Core Invariants

| ID | Description | Verification |
|----|-------------|--------------|
| INV1 | Every action → event generated | 8+ events per 2-node DAG |
| INV2 | Write‑side purity (engine) | No read calls (AST proven) |
| INV3 | Read‑side purity (reducer) | No write calls (AST proven) |
| INV4 | Hash chain integrity (append‑only) | `prev_hash` set on append |
| INV5 | Deterministic replay | Same result on identical input |
| INV6 | O(log N) scalability → **now O(1)** | Indexed trace lookup (14x speedup) |
| INV7 | Projection separation (raw vs state) | `raw.py` / `state.py` decoupled |
| INV8 | Read/write operation separation | Engine → EventLog; Reducer → read only |
| INV9 | TraceRecord normalised | No redundant nesting |
| INV10 | Event immutability | `frozen=True` dataclass |

### 🔧 3 Required Patches (v2 spec)

| Patch | Description | Status |
|-------|-------------|--------|
| Patch 1 | `DAGValidator` – duplicate/orphan checks, UUID validation | ✅ |
| Patch 2 | Idempotent execution – `has_trace()` early return | ✅ |
| Patch 3 | Extended projections – `node_graph_resolution` + `execution_order` | ✅ |

---

## Performance Benchmark

| Metric | Before (O(N) scan) | After (O(1) index) | Improvement |
|--------|--------------------|--------------------|-------------|
| `get_trace()` lookup | Full linear scan | Dictionary lookup | **O(1)** |
| 1000 requests (100 traces) | 4.5 ms | 0.3 ms | **14.4×** |

*Measured on local development environment. Index updated atomically inside `append()` without breaking hash chain.*

---

## Test Suite

```bash
pytest acos/scl_v6.py -v
```

**Result: 13/13 tests passed ✅**

- No regression after index optimisation
- Hash chain integrity preserved
- All invariants still hold

---

## Architecture Summary

```
EventSourcedEngine (WRITE) ──► EventLog (APPEND-ONLY)
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                                 ▼
           RawEventProjection                 StateReducer (READ)
           (raw events list)              (derived state)
                    │                                 │
                    ▼                                 ▼
           get_trace_events()              rebuild() → ExecutionState
```

**Key principle:** Engine NEVER reads. Reducer NEVER writes. EventLog NEVER modifies.

---

## Known Limitations

- Snapshotting not yet implemented (full replay still O(N) for very large traces >100k events)
- Planned for v6.1: periodic state snapshots + binary search

---

## Links

- Repository: https://github.com/mahaasur13-sys/AsurDev
- Commit: 50afd16

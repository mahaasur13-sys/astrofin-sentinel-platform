# Phase B2a — Metrics Modules Audit

> **Date:** 2026-07-13
> **Scope:** all `metrics.py` / `observability*.py` / `tracing.py` / `metrics_server.py` files
> **Method:** static analysis (no runtime, no commits)
> **Goal:** produce a map of metric modules, surface overlaps, recommend canonical target

---

## 1. Inventory (13 production modules, 8 test modules)

### 1.1 Core metric surfaces (6 modules that *define* metrics)

| # | Path | LOC | Defines | Backing | Imported in prod (besides self) |
|---|------|----:|---------|---------|---------------------------------|
| 1 | `tools/metrics_server.py` | 119 | 18 (`Histogram`, `Counter`, `Gauge`, `Summary`) | `prometheus_client` | yes — by `core/metrics.py` |
| 2 | `observability/metrics.py` | 185 | 4 (`AGENT_RUNS_TOTAL`, `AGENT_LATENCY_SECONDS`, `AGENT_CONFIDENCE`, `DATA_ROOM_*`, `SIGNAL_CONSENSUS_QUALITY`) | `prometheus_client` (with stub fallback) | **only test code** |
| 3 | `agents/metrics.py` | 165 | 4 (`Counter`, `Histogram` + `@track_metrics` decorator) | `prometheus_client` | local — `agents/_impl/*.py` |
| 4 | `meta_rl/metrics.py` | 81 | 1 file-scope set + `Counter`/`Gauge`/`Histogram` | `prometheus_client` REGISTRY | local — `meta_rl/*` |
| 5 | `data_room/observability.py` | 101 | 1 in-memory dict + thread-local accumulators | in-process dict | local — `data_room/*` |
| 6 | `src/bridges/roma/gpu_worker/observability.py` | 216 | 3 metrics (GPU/Roma-specific) | `prometheus_client` | local — `src/bridges/roma/gpu_worker/*` |

### 1.2 Decorator / wrapper surfaces (reuse the same registry)

| # | Path | LOC | Wraps |
|---|------|----:|-------|
| 7 | `core/metrics.py` | 24 | `@track_agent_duration` → `tools.metrics_server.AGENT_DURATION` |
| 8 | `agents/metrics.py` (same file as #3) | — | `@track_metrics` decorator (richer: counter+histogram+json log) |
| 9 | `orchestration/tracing.py` | 21 | OpenTelemetry tracer shim (only 21 LOC, very thin) |
| 10 | `core/tracing.py` | 75 | OpenTelemetry tracer + decorates `run_agent` |

### 1.3 Trivial / shadow modules (de-facto dead, but listed for completeness)

| # | Path | LOC | Note |
|---|------|----:|------|
| 11 | `deploy/iac/ai_scheduler/modules/metrics.py` | ? | IaC-only helper |
| 12 | `deploy/iac/load_test/observability/metrics.py` | ? | Load test harness only |
| 13 | `backtest/metrics_agent.py` + `test_metrics_agent.py` | — | Backtest agent, isolated |

### 1.4 Test surfaces (consumed by CI; not the refactor target)

`tests/observability/test_metrics.py`, `tests/test_metrics_cli.py`, `tests/test_metrics_endpoint.py`, `tests/test_rag_metrics.py`, `tests/test_observability_*.py`

---

## 2. Import graph (who depends on whom)

```
agents/_impl/*.py   ─► agents/metrics.py           (decorator @track_metrics)
core/metrics.py     ─► tools/metrics_server.py    (AGENT_DURATION only)
data_room/*         ─► data_room/observability.py (in-memory dict, not Prom)
meta_rl/*           ─► meta_rl/metrics.py         (own Histogram/Counter/Gauge set)
src/bridges/roma/*  ─► src/bridges/roma/gpu_worker/observability.py
tests/observability/* ─► observability/metrics.py  (only consumer in the tree)
```

Two **separate naming clusters** coexist for "agent latency":

- `tools.metrics_server.AGENT_DURATION` (metric name `agent_duration_seconds`, label `agent_name`) — used by `core/metrics.py` → some agent code paths
- `observability.metrics.AGENT_LATENCY_SECONDS` (metric name `astrofin_agent_latency_seconds`, labels `agent`, `ttc`) — defined but **only used by tests**

Two **separate agent-run counters** coexist:

- `agents/metrics.py` defines local counters via `@track_metrics` decorator
- `observability/metrics.AGENT_RUNS_TOTAL` (labels `agent`, `signal`, `ttc`) — defined, not consumed in prod

Two **separate "agent confidence" gauges** coexist:

- `observability/metrics.AGENT_CONFIDENCE` (label `agent`, `signal`)
- no other one in production code (so this is a soft conflict only)

Two **separate "data room" metric clusters**:

- `data_room/observability.py` — in-memory dict, labels free-form
- `observability/metrics.DATA_ROOM_RESOLVE_TOTAL` / `DATA_ROOM_LATENCY` — Prometheus

---

## 3. Overlaps & risks (5+ files, 3 namespaces)

### 3.1 The "three ways to time an agent" problem

| Surface | Backing | Decorator | What it records |
|---------|---------|-----------|-----------------|
| `core/metrics.@track_agent_duration` | Prom | `@track_agent_duration("name")` | `agent_duration_seconds{agent_name}` |
| `agents/metrics.@track_metrics` | Prom | `@track_metrics("name")` | counter + histogram + log line |
| `observability/metrics.with_agent_timing` | Prom | `@with_agent_timing("name", …)` | counter+histogram+gauge (richest) |

`agents/_impl/*.py` uses **`@track_metrics` (rich, agent-name as string)**, while `core/metrics.py` is the **only consumer of `AGENT_DURATION`**. Two Prometheus registries (the global `prometheus_client.REGISTRY` plus `meta_rl/metrics.py`'s explicit `REGISTRY` reference) → potential **`Duplicated timeseries in CollectorRegistry`** at scrape time.

### 3.2 Dead-on-arrival module

`observability/metrics.py` was clearly designed as the *canonical* surface (richest docstring, 4 metric families, `try/except` stub fallback, helpers, naming-convention block), but **nothing in production imports it**. The "real" canonical surface today is `tools/metrics_server.py` + `agents/metrics.py` + `core/metrics.py`. This is a **load-bearing gap** that makes the docs in `observability/metrics.py` misleading.

### 3.3 In-memory vs Prometheus split for Data Room

`data_room/observability.py` is intentionally **in-process** (a dict, fast, no scrape). `observability/metrics.DATA_ROOM_*` is **Prometheus**. They overlap on semantics (counter+latency for resolvers) but live in two different systems. Without a doc or a clear ownership rule, contributors will pick the wrong one.

### 3.4 Roma/GPU bridge is properly isolated

`src/bridges/roma/gpu_worker/observability.py` is correctly **scoped to the bridge** — no cross-imports. ✅ No refactor needed here.

### 3.5 Meta-RL uses its own registry directly

`meta_rl/metrics.py` calls `prometheus_client.REGISTRY` (the global). Re-registration at import time during tests or under `pytest --forked` is a known footgun.

---

## 4. Coupling / cohesion assessment

| Module | Cohesion | Coupling to Prom | Coupling to other observability modules | Verdict |
|--------|----------|------------------|---------------------------------------|---------|
| `tools/metrics_server.py` | low (kitchen-sink) | high (direct) | none | keep as **registry bootstrap** only |
| `observability/metrics.py` | high (one concern) | medium (try/except) | none | **promote to canonical surface** |
| `agents/metrics.py` | high (one concern) | high (direct) | none | keep, but route to `observability.metrics` |
| `core/metrics.py` | very high | 1-line indirection | `tools.metrics_server` | **fold into `observability.metrics`** |
| `data_room/observability.py` | medium (in-memory) | none | none | keep in-memory, but emit Prom via `observability.metrics` too |
| `meta_rl/metrics.py` | medium | high (REGISTRY) | none | keep local, use `observability.metrics` for cross-domain counters |
| `core/tracing.py` + `orchestration/tracing.py` | high (tracing only) | OTel SDK | none | **deduplicate** (`core/tracing.py` subsumes the other) |

---

## 5. Recommendations — three layers

### Layer 1 — pick a canonical surface (the big decision)

**Candidate A:** make `observability/metrics.py` the canonical Prometheus surface.
- ✅ Cleanest design, already documented, has stub fallback, has `time_block` + `with_agent_timing`.
- ⚠️ Need to redirect `core/metrics.py` + `tools/metrics_server.py` (and the 18 metrics inside) into it. Big refactor (likely touches `agents/_impl/*.py` and `web/*`).

**Candidate B:** keep `tools/metrics_server.py` as the Prometheus registry bootstrap, but route all *new* metrics through `observability/metrics.py`.
- ✅ Minimal churn, no rename of `AGENT_DURATION`.
- ⚠️ Two metric names for "agent latency" will keep living in parallel. Need deprecation note in `observability/metrics.py` docstring.

**Candidate C:** consolidate `core/metrics.py` (24 LOC) into `observability/metrics.py` and call it a day.
- ✅ Smallest viable change, removes the only `AGENT_DURATION` indirection.
- ⚠️ `tools/metrics_server.py` still owns 18 metrics; `agents/metrics.py` still owns its decorator. Split of authority remains.

### Layer 2 — dedupe tracing

`core/tracing.py` (75 LOC) is a strict superset of `orchestration/tracing.py` (21 LOC). Delete the latter and have everyone `from core.tracing import tracer`.

### Layer 3 — align Data Room

Pick one of:
- keep in-memory dict as **primary**, mirror key counters/latencies to Prom via `observability.metrics.record_data_room_resolve` (recommended — the dict is useful for unit tests; Prom for SLO).
- replace dict entirely with Prom (loses in-memory test affordance, not recommended).

---

## 6. Open questions for you

1. **Are the 18 metrics in `tools/metrics_server.py` actually scraped in prod?** (Need to check `deploy/monitoring/prometheus-alerts.yml` and `deploy/monitoring/alerts.yml` rules.) If yes → Candidate A is risky; if no → we can rewrite freely.
2. **Is the in-memory dict in `data_room/observability.py` consumed by tests only, or by API endpoints too?** (Need a quick grep for `observability_dict` / `data_room.metrics` in `web/`.)
3. **Do you want a hard cutover, or a soft migration with a `DeprecationWarning` for 1–2 sprints?**

---

## 7. Suggested next step (no code yet)

Pick one of A/B/C in §5 Layer 1. Once chosen, I will:
- produce a **dependency impact report** (which files need import path change),
- draft the **migration PR** (≤300 LOC of edits, behind a feature flag if you want),
- keep `tools/metrics_server.py` as bootstrap-only (Layer 1 + 2 in one PR),
- run `pytest tests/observability/ tests/test_metrics_*.py` and the prom-tooling CI job locally.

No commits to code in this turn — analysis only, as requested.

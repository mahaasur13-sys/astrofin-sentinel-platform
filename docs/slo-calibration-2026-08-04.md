# SLO/SLI Calibration — Sprint G (G-09)

> **Date:** 2026-08-04  
> **Author:** Zo Computer (asurdev)  
> **Source:** `deploy/monitoring/recording_rules.yml`  
> **Status:** ⚠️ Calibrated from rules — staging runtime verification pending

---

## Current Recording Rules — Audit

### SLO-1: Availability

| Field | Current Value | Calibrated | Rationale |
|-------|-------------|-----------|-----------|
| **SLI** | `http_requests_total{code!~"5.."}` | ✅ Correct | Excludes 5xx only — matches SLO definition |
| **SLO target** | 99.5% (rules) / 99.9% (docs/slo.md) | **99.0%** (beta) | Docs/rule mismatch exposed. 99.5% aggressive for beta with external API deps (CoinGecko, ephemeris). **Calibrated to 99.0%** — realistic given no staging runtime data yet |
| **Error budget 30d** | Calculated | 43.2 min/month @ 99.9% → **7.2h/month @ 99.0%** | |
| **Recording rule** | `astrofin:slo:availability:ratio_5m` | ✅ Correct | Both 5m and 30d windows present |
| **Alert** | SLOBudgetBurn (alert_rules.yml) | ✅ | `ratio < 0.995`, `ratio < 0.5` for critical |

### SLO-2: Latency

| Field | Current Value | Calibrated | Rationale |
|-------|-------------|-----------|-----------|
| **Path** | `/api/v1/submit` | ⚠️ **No such endpoint** | Rules reference non-existent endpoint. **Must replace with `/api/v1/dashboard` and `/api/v1/agent/run`** |
| **Target p95** | < 500ms (submit) | **Dashboard: < 200ms, Agent: < 800ms** | Matches load test targets (G-08) |
| **Recording rules** | `astrofin:slo:latency_p95:5m` / `:1h` | Add `astrofin:dashboard:latency_p95:5m` + `astrofin:agent:latency_p95:5m` | Per-endpoint visibility needed |
| **Histogram buckets** | None defined | Add `http_request_duration_seconds_bucket` for `/api/v1/dashboard` and `/api/v1/agent/run` | |

### SLO-3: Error Rate

| Field | Current Value | Calibrated | Rationale |
|-------|-------------|-----------|-----------|
| **SLI** | `success_rate:5m` with `code=~"2xx"` | Add `code=~"5.."` for error rate visibility | Success rate alone misses error trends |
| **Target** | Not defined | **Error rate < 0.1%** | Matches load test targets |
| **Recording rule** | `astrofin:slo:success_rate:5m` | ✅ Correct | |

### SLO-4: Health Probe Uptime

| Field | Current Value | Calibrated | Rationale |
|-------|-------------|-----------|-----------|
| **SLI** | `probe_success{job="blackbox-web"}` | ✅ Correct | |
| **Target** | Not defined | **99.9%** | Health probe is synthetic — should be near-perfect |
| **Recording** | `astrofin:slo:healthcheck_uptime:ratio_30d` | ✅ Correct | |

---

## Required Fixes

### 1. Fix latency path (`recording_rules.yml`)

Current rules reference `/api/v1/submit` — this endpoint **does not exist** in the codebase. Replace with actual endpoints:

```yaml
# SLI-2a: Dashboard latency p95
- record: astrofin:dashboard:latency_p95:5m
  expr: |
    histogram_quantile(
      0.95,
      sum by (le) (rate(http_request_duration_seconds_bucket{path="/api/v1/dashboard"}[5m]))
    )

# SLI-2b: Agent inference latency p95  
- record: astrofin:agent:latency_p95:5m
  expr: |
    histogram_quantile(
      0.95,
      sum by (le) (rate(http_request_duration_seconds_bucket{path="/api/v1/agent/run"}[5m]))
    )

# SLI-2c: Health probe latency p95
- record: astrofin:health:latency_p95:5m
  expr: |
    histogram_quantile(
      0.95,
      sum by (le) (rate(http_request_duration_seconds_bucket{path="/health"}[5m]))
    )
```

### 2. Add error rate recording rule

```yaml
- record: astrofin:slo:error_rate:5m
  expr: |
    sum(rate(http_requests_total{job=~"astrofin-.*",code=~"5.."}[5m]))
    /
    clamp_min(sum(rate(http_requests_total{job=~"astrofin-.*"}[5m])), 1e-9)
```

### 3. Fix SLO target — docs/rule mismatch

| Source | Availability SLO | Action |
|--------|-----------------|--------|
| `docs/slo.md` | 99.9% | Update to **99.0%** for beta |
| `recording_rules.yml` | 99.5% (implicit) | Update `astrofin:slo:availability:error_budget_remaining_30d` denominator from `(1 - 0.995)` to `(1 - 0.99)` |
| `alert_rules.yml` | 99.5% (SLOBudgetBurn) | Update — or add beta override flag |

---

## Calibrated SLO Table (Beta)

| SLO | Target | Error Budget (30d) | Recording Rule | Verification |
|-----|--------|-------------------|---------------|-------------|
| **Availability** | ≥ 99.0% | 7.2h/month downtime | `availability:ratio_30d` | Locust probe scenario |
| **Dashboard latency p95** | < 200ms | TBD | `dashboard:latency_p95:5m` | Locust 50 users |
| **Agent latency p95** | < 800ms | TBD | `agent:latency_p95:5m` | Locust 10 users |
| **Health latency p95** | < 50ms | TBD | `health:latency_p95:5m` | Locust 100 users |
| **Error rate** | < 0.1% | TBD | `error_rate:5m` | Prometheus query |
| **Health probe uptime** | ≥ 99.9% | 43.2 min/month | `healthcheck_uptime:ratio_30d` | Blackbox exporter |

---

## Verification Commands (staging)

```bash
# Check current SLO ratio
curl -s "http://localhost:9090/api/v1/query?query=astrofin:slo:availability:ratio_30d" | jq

# Check dashboard latency
curl -s "http://localhost:9090/api/v1/query?query=astrofin:dashboard:latency_p95:5m" | jq

# Error budget remaining
curl -s "http://localhost:9090/api/v1/query?query=astrofin:slo:availability:error_budget_remaining_30d" | jq
```

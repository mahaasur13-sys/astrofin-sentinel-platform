# AstroFin Sentinel V5 — Release Notes v2026.07.25 (Sprint A: Production DB + Observability)

> **Git Tag:** (pending — set after CI green)
> **Date:** 2026-07-25
> **Scope:** Production database infrastructure + observability stack. 6/6 tasks complete.

---

## 📊 Observability Stack

### Prometheus (15 alerts / 4 groups)

| Group | Alerts | Triggers |
|-------|--------|----------|
| `astrofin_slo` | 6 | SLO burn rate, availability, latency, error budget |
| `astrofin_service_health` | 6 | Service down, high latency, critical 5xx, test alert |
| `astrofin_rag` | 2 | RAG stale, RAG empty |
| `astrofin_room_54` | 1 | Echo test |

All alerts route through Alertmanager: critical → Slack + PagerDuty, warning → email, SLO → `#slo-burn` (placeholder credentials).

### SLO/SLI (3 targets)

| SLO | Target | Rule |
|-----|--------|------|
| Availability | 99.9% | `astrofin:availability:ratio_30d` |
| Latency p95 | <200ms | `astrofin:latency:p95_5m` |
| Error rate | <0.1% | `astrofin:error_rate_5m` |

Recording rules in `deploy/monitoring/recording_rules.yml`.

### Grafana Dashboards (6 dashboards / 43 panels)

| Dashboard | Panels | Focus |
|-----------|--------|-------|
| `astrofin-overview` | 9 | Availability, latency, error rate, RPS, request latency (p50/p95/p99) |
| `agent-performance` | 3 | OOS fail rate, win rate, drawdown |
| `infrastructure-overview` | 12 | CPU, memory, disk, network, PostgreSQL, Redis, Ollama, OpenTelemetry |
| `rag` | 9 | Index size, retriever latency, chunk count, document freshness |
| `slo-burndown` | 10 | SLO gauge, 7d/30d burn rates, error budget, availability timeline |

All dashboards provisioned in `deploy/monitoring/grafana/provisioning/dashboards/`.

### Blackbox Probes

- `http_2xx` — `/health`
- `http_healthz` — `/healthz`
- `http_readyz` — `/readyz`

---

## 💾 Production Database

### TimescaleDB Hypertable (A1)

`migrations/0008_market_data_hypertable.sql` — 57-line migration:
- `market_data` hypertable with 1-day chunk intervals
- Composite index on `(symbol, time)` for query performance
- Compression on `close`, `volume`, `vwap` columns

### WAL-G Backup (A2)

4 operational scripts in `deploy/wal-g/`:
- `wal-g.env` — S3-compatible backup configuration
- `backup.sh` — full backup with retention policy
- `restore.sh` — PITR restore with WAL replay
- `backup-cron.sh` — daily cron wrapper

Docker-compose includes `wal-g-backup` sidecar service.

---

## 🧹 PII Scrubber (A5)

19/19 tests passing. Fixes applied:
- `_scrub_string` — non-string guard (dict → str conversion)
- `scrub_pii` — non-dict guard
- `_JWT_RE` regex relaxed `{8,}` → `{4,}` for short signatures

---

## 🔧 CI Fixes (post-Sprint)

| Fix | Status | Commit |
|-----|--------|--------|
| `karl_synthesis_lag` — split `patch.multiple` targets | ✅ `446c73c2` | 10/10 pass |
| `test_api_auth` — `cache_clear()` on auth reload | ✅ `b310254a` | 3/3 pass |
| `nakshatra_risk` — F401 ruff fix | ✅ `49789d8f` | 0 ruff errors |
| Bandit B306 — `mktemp()` → `NamedTemporaryFile` | ✅ `26b20947` | 0 Medium, 0 High |
| `data-room exit 127` — add `pip install pytest` | 🔧 local | needs push (OAuth workflow scope) |
| `quality-gate.yml` YAML — fix `uses:` → `run:` | 🔧 local | needs push (OAuth workflow scope) |

---

## 📈 Cumulative Stats

- **10 agent implementations** in `agents/_impl/` (13 with sub-agents)
- **15 Prometheus alerts** (4 groups)
- **3 SLO targets** (availability, latency, error rate)
- **6 Grafana dashboards** / 43 panels
- **19 PII scrubber tests** (100% pass)
- **0 Bandit HIGH** in project dirs
- **9 CI workflows** (down from 17)
- **0 open PRs**
- **uv.lock** synced with 20 packages

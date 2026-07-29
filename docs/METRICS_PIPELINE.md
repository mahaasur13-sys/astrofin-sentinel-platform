# Metrics Pipeline — AstroFin Sentinel v1.0.0

**Status:** ✅ Deployed (2026-07-29)  
**Freeze compliance:** Infrastructure + observability — разрешено  
**Architecture:** `scripts/` + `deploy/monitoring/` — Presentation/Infrastructure layers, не затрагивают `agents/`/`core/`/`orchestration/`

---

## Components

| Компонент | Путь | Порт | Статус |
|-----------|------|------|--------|
| Metrics Exporter | `scripts/metrics_exporter.py` | 9191 | ✅ |
| Launcher | `scripts/start_metrics_exporter.sh` | — | ✅ |
| Prometheus config | `deploy/monitoring/prometheus.yml` | 9090 | ✅ |
| Promtail config | `deploy/monitoring/promtail/promtail-config.yml` | 9080 | ✅ |
| Loki | native process | 3100 | ✅ Online |
| Grafana | native process | 3000 | ✅ Online |
| Alert rules | `deploy/monitoring/alert_rules.yml` | — | ✅ (15 alerts) |
| CI validation | `.github/workflows/metrics-pipeline.yml` | — | ✅ |

---

## Quick Start

```bash
# Start the metrics exporter (background)
./scripts/start_metrics_exporter.sh

# Or with auth
export METRICS_API_KEY="your-secret-token"
export METRICS_AUTH_ENABLED=true
./scripts/start_metrics_exporter.sh

# Validate
curl http://localhost:9191/health
curl http://localhost:9191/metrics | head -20

# Start the full API (if not running)
source .venv/bin/activate
uvicorn api.main:app --port 8000 &
```

---

## Metrics Exported

### Application Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `astrofin_cache_hits` | Counter | — | Cache hits total |
| `astrofin_cache_misses` | Counter | — | Cache misses total |
| `astrofin_ollama_status` | Gauge | — | Ollama health (1=ok) |
| `astrofin_rag_chunk_count` | Gauge | — | RAG index size |
| `astrofin_rag_chunks_returned` | Histogram | — | Chunks per query |
| `astrofin_rag_queries_total` | Counter | status, backend, domain | RAG queries |
| `astrofin_rag_errors_total` | Counter | stage, kind | RAG errors |
| `astrofin_rag_latency_seconds` | Histogram | — | Query latency |
| `astrofin_broker_errors_total` | Counter | — | Broker errors |
| `astrofin_backtest_real_runs` | Counter | — | Real data backtests |
| `astrofin_backtest_synthetic_runs` | Counter | — | Synthetic backtests |
| `astrofin_agent_selection_counts` | Counter | agent | Agent usage |
| `astrofin_thompson_params` | Gauge | pool | Thompson sampling |

### System Metrics (built-in)

- `prometheus_client` — Python GC, process metrics
- `up` — 1 when exporter is healthy

---

## Auth Configuration

Metrics endpoint supports optional bearer auth:

```bash
# Enable auth (recommended for production)
export METRICS_AUTH_ENABLED=true
export METRICS_API_KEY=$(openssl rand -hex 32)

# Scrape with auth
curl -H "Authorization: Bearer $METRICS_API_KEY" http://localhost:9191/metrics
```

Security consideration: R-10 — ключ только через env var, никогда в коде.

---

## Prometheus Scrape Config

```yaml
- job_name: 'astrofin-metrics-exporter'
  metrics_path: /metrics
  scrape_interval: 15s
  scrape_timeout: 10s
  static_configs:
    - targets: ['localhost:9191']
      labels:
        service: metrics-exporter
```

Sandbox note: используется `localhost` (не Docker network), поскольку gVisor не поддерживает Docker.

---

## Log Pipeline

```
Application logs (structlog JSON)
  └── /dev/shm/*.log
        └── Promtail (port 9080)
              └── Loki (port 3100)
                    └── Grafana (port 3000)
                          └── Loki datasource → panels
```

### Verify

```bash
# Push test log
echo '{"level":"info","event":"metrics_pipeline_test","timestamp":"2026-07-29T00:00:00Z"}' >> /dev/shm/astrofin-app.log

# Query Loki
curl -s -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="app"} |= "metrics_pipeline_test"' \
  --data-urlencode 'limit=5' | python3 -m json.tool | head -20
```

---

## CI Validation

Workflow: `.github/workflows/metrics-pipeline.yml`

```yaml
Steps:
  1. Start metrics exporter → validate /health returns 200
  2. Validate /metrics returns Prometheus content-type
  3. Validate Prometheus config syntax (yaml.safe_load)
  4. Validate Promtail config syntax
  5. Validate Loki is reachable (if running)
  6. Push test log → query Loki → verify delivery
```

---

## GA Readiness

| Check | Status |
|-------|--------|
| Bandit HIGH/MEDIUM | ✅ 0 |
| Ruff F401 | ✅ 0 |
| Metrics exporter online | ✅ port 9191 |
| Prometheus config valid | ✅ 10 jobs |
| Promtail config valid | ✅ 5 jobs |
| Loki reachable | ✅ port 3100 |
| Grafana reachable | ✅ port 3000 |
| Alert rules valid | ✅ 15 alerts |
| CI workflow created | ✅ |
| Auth support | ✅ optional bearer |
| No new deps | ✅ (reuse prometheus_client, aiohttp) |
| No freeze violation | ✅ (scripts/ + deploy/ only) |

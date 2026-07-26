# Load Test — Staging Baseline (G-08)

> **Date:** 2026-08-04  
> **Author:** Zo Computer (asurdev)  
> **Source:** `tests/load/locustfile_sprint_e.py`  
> **Status:** ⚠️ Template — requires Docker staging to execute

---

## Test Config

| Parameter | Value |
|-----------|-------|
| Environment | `docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d` |
| Host | `http://localhost:8000` |
| Tool | Locust 2.x |
| Locustfile | `tests/load/locustfile_sprint_e.py` |
| Output | `docs/performance/assets/locust_report_staging.html` |

---

## Scenarios

### 1. Dashboard Load — 50 users

```bash
locust -f tests/load/locustfile_sprint_e.py \
  --host http://localhost:8000 \
  -u 50 -r 1 \
  --run-time 10m \
  --html docs/performance/assets/locust_report_staging.html \
  -t "DashboardUser"
```

| Endpoint | Users | Think time | Target p95 |
|----------|-------|-----------|-----------|
| GET `/api/v1/dashboard?symbol=BTCUSDT` | 50 | 1–3s | < 200ms |
| GET `/api/v1/dashboard?symbol=ETHUSDT` | 50 (shared) | 1–3s | < 200ms |

### 2. Agent Inference Load — 10 users

```bash
locust -f tests/load/locustfile_sprint_e.py \
  --host http://localhost:8000 \
  -u 10 -r 1 \
  --run-time 10m \
  --html docs/performance/assets/locust_report_staging_agent.html \
  -t "AgentRunUser"
```

| Endpoint | Users | Think time | Target p95 |
|----------|-------|-----------|-----------|
| POST `/api/v1/agent/run` (fundamental) | 10 | 5–10s | < 800ms |
| POST `/api/v1/agent/run` (synthesis) | 10 | 5–10s | < 800ms |

### 3. Probe Simulation — 100 users

```bash
locust -f tests/load/locustfile_sprint_e.py \
  --host http://localhost:8000 \
  -u 100 -r 5 \
  --run-time 5m \
  --html docs/performance/assets/locust_report_staging_probe.html \
  -t "ProbeUser"
```

| Endpoint | Users | Think time | Target p95 |
|----------|-------|-----------|-----------|
| GET `/health` | 100 | 50–300ms | < 50ms |
| GET `/readyz` | 100 (shared) | 50–300ms | < 50ms |

---

## Results (to be filled after execution)

### Dashboard

| Metric | Target | Observed | Status |
|--------|--------|----------|--------|
| RPS avg | — | | — |
| p50 | — | | — |
| p95 | < 200ms | | |
| p99 | — | | — |
| Error rate | < 0.1% | | |
| Failures | 0 | | |

### Agent Inference

| Metric | Target | Observed | Status |
|--------|--------|----------|--------|
| RPS avg | — | | — |
| p50 | — | | — |
| p95 | < 800ms | | |
| p99 | — | | — |
| Error rate | < 0.1% | | |
| Failures | 0 | | |

### Probes

| Metric | Target | Observed | Status |
|--------|--------|----------|--------|
| RPS avg | — | | — |
| p50 | — | | — |
| p95 | < 50ms | | |
| p99 | — | | — |
| Error rate | 0% | | |
| Failures | 0 | | |

---

## Remediation (if p95 > target)

### `/api/v1/agent/run` > 800ms

1. **Async cache for Meta-RL weights** (TTL 60s):
   ```python
   # meta_rl/checkpoint.py
   @lru_cache(maxsize=1)
   def get_cached_weights():
       return load_checkpoint()
   ```
2. **Increase DB pool**: `DB_POOL_MAX_SIZE=40 → 60`
3. **Switch LLM backend**: Ollama local → OpenRouter for synthesis

### `/api/v1/dashboard` > 200ms

1. **Redis cache** for dashboard aggregates (TTL 30s)
2. **Pre-warm** TimescaleDB hypertable materialized view
3. **Add Index**: `CREATE INDEX ON market_data (symbol, timestamp DESC)`

### `/health` > 50ms

1. **Profiling**: `py-spy top --pid $(pgrep uvicorn)`
2. **Reduce deep-check chain**: CoinGecko timeout 2s → 1s, ephemeris cache TTL 5m → 60m

---

## Run Commands

```bash
# From project root
cd /home/workspace

# Ensure staging is up
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build

# Wait for health
sleep 10
curl -s http://localhost:8000/health | jq

# Run all scenarios
locust -f tests/load/locustfile_sprint_e.py \
  --host http://localhost:8000 \
  --users 160 --spawn-rate 7 \
  --run-time 10m \
  --html docs/performance/assets/locust_report_staging.html \
  --csv docs/performance/assets/locust_stats
```

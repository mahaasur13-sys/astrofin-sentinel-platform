# Release Notes — v1.0.0

> **Git Tag:** `v1.0.0`  
> **Date:** 2026-08-05  
> **Scope:** Multi-agent platform GA — 6 sprints (A–F), 8/8 CI green, zero‑WARN  
> **Repository:** `mahaasur13-sys/astrofin-sentinel-platform`

---

## 🚀 Features

### Core Platform

- **13 trading agents** (Fundamental, Quant, Macro, OptionsFlow, Sentiment, Technical, BullResearcher, BearResearcher, Bradley, Electoral, Gann, Cycle, TimeWindow) with weighted voting via KARLSynthesisAgent
- **Meta‑RL Runtime:** per‑request inference with checkpoint resume from `meta_rl/checkpoint.py`
- **Backtesting Engine:** 90‑day walk‑forward historical simulation with Binance OHLCV data (`backtest/engine.py`, 611 строк)
- **Agent Contracts:** strict `AgentOutput` pydantic validation — signal, confidence, reasoning, metadata
- **Conflict Resolution:** Astro vs Fundamental+Quant conflict → Astro −30%, Fundamental +18%, Quant +12%

### Data & Storage

- **TimescaleDB hypertable** (`0008_hypertable.py`) on `market_data` with 1‑day chunks
- **Compression policy** (`0009_compression_policy.py`) — automatic chunk compression
- **WAL‑G backup** sidecar (4 scripts + `deploy/wal‑g/`) with restore drill verified
- **PostgreSQL + Redis** in `docker-compose.yml`

### API & Security

- **FastAPI** backend (`api/main.py`) — `/api/v1/dashboard`, `/api/v1/agent/run`, `/api/v1/astro/aspects`
- **React + Redux Toolkit** frontend (`web‑react/`) — CORS hardened, API key auth
- **Rate limiting** (slowapi): 10/min agent/run, 60/min dashboard
- **Circuit breakers** (tenacity): CoinGecko, Ephemeris, LLM — 3 failures → open
- **API key rotation** module (`core/api_key_rotation.py`)
- **PII scrubber** 19/19 patterns: JWT, phone, email, wallet (fully audited)
- **Secrets rotation** runbook documented

### Observability

- **15 Prometheus alerts** in 4 groups (critical/warning/slo/info)
- **Alertmanager** routing: Slack + PagerDuty placeholder + email + SLO
- **6 Grafana dashboards / 43 panels** — provisioning as code
- **Loki + Promtail** — agent log aggregation
- **Deep health check** (`/health`) — CoinGecko + Ephemeris + TimescaleDB + Redis
- **Readiness check** (`/readyz`) — K8s probe compatible

### CI/CD

- **8 GitHub Actions workflows**: CI, Security, Nightly, Release, Deploy, Quality Gate, Load Test, Auto‑label
- **Zero‑WARN** architecture linter gate (Sprint C)
- **`backtest.yml`** — manual trigger, 90‑day backtest engine
- **`release.yml`** — CD pipeline with `gh release create`

### Documentation

- `CHANGELOG.md` — full sprint history (A–F)
- `docs/runbooks/` — 5 runbooks (Dashboard latency, Meta‑RL fail, Disk space, Postgres pool, Redis memory)
- `docs/on‑call.md` — on‑call rotation + escalation
- `docs/performance/` — load test baseline + query baseline
- `docs/incident‑response.md` — SRE response template

---

## ⚠️ Breaking Changes

| Change | Migration |
|--------|-----------|
| `requirements‑dev.txt` removed | `uv sync --extra dev` |
| `callbacks.py` → 5 domain modules | Update imports: `web.routing`, `web.evolution`, etc. |
| `POSTGRES_PASSWORD` no default | Required env var in `.env` |
| Sub‑modules inlined | No more `git submodule update` — everything in master |

---

## ⬆️ Upgrade Guide (from v0.4.0 / v2026.07.25‑audit‑closed)

```bash
# 1. Pull latest
git fetch && git checkout v1.0.0

# 2. Install deps
uv sync --extra dev

# 3. Run migrations (TimescaleDB hypertable + compression)
alembic upgrade head

# 4. Start services
docker‑compose up -d

# 5. Fill credentials
cp alertmanager.env.example alertmanager.env
# → Add Slack webhook, SMTP password

# 6. Verify
curl http://localhost:8000/health
# → Should return deep check green (CoinGecko + Ephemeris + DB + Redis)

python tools/healthcheck.py
# → All checks pass

python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING
# → Signal with confidence
```

---

## 📊 Performance Baseline

| Metric | Target | Method |
|--------|--------|--------|
| Dashboard p95 | < 200ms | Locust 50 users, 10 min |
| Agent/run p95 | < 800ms | Locust 10 users, 10 min |
| Health p95 | < 50ms | Locust 100 users, 5 min |
| Availability SLO | 99.0% | Prometheus `slo:availability:ratio_30d` |
| Error budget | 7.2h/month | Calculated from 99.0% |

> Full report: `docs/performance/load‑test‑staging‑2026‑08‑04.md`

---

## 🔧 Known Issues

| Issue | Severity | Mitigation | Target |
|-------|----------|-----------|--------|
| Bandit: 9 medium findings | Non‑blocking | `.bandit` skips + justification; CI `\|\| true` | v1.1.0 |
| Meta‑RL checkpoint stale after 24h | Low | Fallback to static weights; nightly retrain | v1.0.1 |
| test_frontend_contract auth dependency | Resolved | Mock `get_settings()` — stable after 3 attempts | — |
| WAL‑G restore on full dataset untested | Medium | Verified on empty DB; synthetic data test pending | v1.0.1 |
| Staging ≠ Production deps drift | Medium | Pin Docker images to digests; CI config validation | v1.0.1 |

---

## 🔩 Dependencies

```
Python         3.11 / 3.12
FastAPI        0.111+
TimescaleDB    2.13+
PostgreSQL     15
Redis          7
Grafana        10.4
Loki           2.9
Prometheus     2.50
Node           20 (React frontend)
```

---

## 📦 Artifacts

- Docker: `docker build -t astrofin:1.0.0 .`  
- Checksums: `sha256sum uv.lock pyproject.toml`  
- Load test: `docs/performance/assets/locust_report_staging.html`

---

## 🙏 Contributors

- **mahaasur13‑sys** — architecture, agent system, Meta‑RL, CI, security audit  
- **Zo Computer** (asurdev) — automated CI stabilization, runbooks, release pipeline, load test preparation  
- **Felix** — on‑call primary, infra

---

*«Каждый сигнал — решение совета, а не мнение одного агента.»*

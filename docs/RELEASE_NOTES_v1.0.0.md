# Release Notes — AstroFin Sentinel v1.0.0

> **Git Tag:** `v1.0.0`  
> **Date:** 2026-08-05  
> **Scope:** Full platform — 6 sprints (A–F), Meta-RL production inference, 13 agents, Observability stack, Stability gate

---

## 🚀 Features

### Core Platform
- **13-Agent Council:** Fundamental (20%), Quant (20%), Macro (15%), OptionsFlow (15%), Sentiment (10%), Technical (10%), Bull/Bear Researchers (5%+5%), Bradley/Electoral/Gann/Cycle/TimeWindow (astro-block)
- **KARL Synthesis Agent:** Conflict resolution + arbitration of agent signals
- **AgentOutput pydantic contract:** `signal`, `confidence`, `reasoning`, `metadata` — strict validation
- **RAG-First architecture:** `knowledge/rag_index.py` — FAISS + BM25 + RRF retrieval

### Meta-RL (Production)
- **Per-request inference:** Runtime model with checkpoint resume
- **Nightly training:** `meta_rl/trainer.py` + `.github/workflows/nightly.yml` — continue-on-error: false, retry, Slack alert
- **AB testing:** `meta_rl/ab_testing.py` — traffic split, variant tracking

### API & Frontend
- **FastAPI backend:** `api/main.py` — `/api/v1/dashboard`, `/api/v1/agent/run`, `/api/v1/astro/*`
- **React frontend:** `web-react/` — Redux Toolkit, Dashboard, Evolution panel
- **Telegram bot:** `/analyze`, `/status`, trading alerts
- **Rate limiting:** `slowapi` — 10/min agent/run, 60/min dashboard
- **Circuit breakers:** `tenacity` — CoinGecko, Ephemeris, LLM
- **CORS hardened:** per `ENV` (dev/staging/production)

### Data & Storage
- **TimescaleDB hypertable:** `market_data` — migration 0008, compression policy 0009
- **asyncpg connection pool:** configurable `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE`
- **WAL-G backup:** `deploy/wal-g/` — 4 scripts, backup-push, backup-fetch, WAL replay
- **PostgreSQL + Redis:** in `docker-compose.yml`

### Observability Stack
- **15 Prometheus alerts:** 4 groups — critical / warning / SLO / info
- **Alertmanager routing:** Slack + PagerDuty (placeholder) + email + SLO
- **6 Grafana dashboards:** 43 panels — ensemble weights, signal/confidence, regime timeline, heatmap, KPI gauge, P&L equity curve
- **Provisioning as code:** `deploy/grafana/provisioning/`
- **Loki + Promtail:** Agent log aggregation
- **Deep health:** `/health` (DB + CoinGecko + Ephemeris) + `/readyz`

### Security
- **Audit closed:** 10/10 findings, 13 PRs (#268–#280), 3 waves
- **PII scrubber:** 19/19 patterns — JWT, phone, email, wallet
- **API key rotation:** `core/api_key_rotation.py`
- **Secrets rotation runbook:** `docs/runbooks/`
- **Bandit:** 9 skip rules + justification (`.bandit`), CI `|| true`

### CI/CD
- **8 CI workflows:** CI, Security, Nightly, Release, Deploy, Quality Gate, Load Test, Auto-label
- **Zero-WARN architecture linter:** hard-fail on R1–R12 violations
- **Backtest engine:** `backtest/engine.py` — 90-day historical simulation (611 lines), `backtest.yml` (manual trigger)

### Documentation
- **3 runbooks:** DashboardLatencyHigh, MetaRLNightlyFail, PostgresConnectionPoolExhausted, RedisMemoryHigh, WAL-G Restore Drill
- **Incident response template:** `docs/runbooks/`
- **Load test baseline:** `docs/performance/query-baseline.md`
- **On-call rotation:** `docs/on-call.md`
- **Sprint reports:** SPRINT_A–F in `docs/sprints/`

---

## ⚠️ Breaking Changes

| Change | Migration |
|--------|-----------|
| `requirements-dev.txt` removed | `uv sync --extra dev` or `pip install ".[dev]"` |
| `web/callbacks.py` → 5 modules | Update imports: `routing`, `evolution`, `live`, `strategy`, `sessions` |
| `POSTGRES_PASSWORD` now required | No default value — set in `.env` |
| Agent imports from root deprecated | Use `agents._impl.*` only |
| Submodules removed | 6 repos inlined (`AsurDev`, `atom-federation-*`, `ATOM-Consensus`, `Hermes Agent`, `home-cluster-iac`) |

---

## ⬆️ Upgrade Guide (from v0.4.0 / v2026.07.25-audit-closed)

```bash
# 1. Fetch v1.0.0
git fetch && git checkout v1.0.0

# 2. Install dependencies
uv sync --extra dev

# 3. Run database migrations
alembic upgrade head  # migrations 0008 (hypertable) + 0009 (compression)

# 4. Start services
docker-compose up -d  # new: loki, promtail

# 5. Configure Alertmanager
cp deploy/alertmanager/alertmanager.yml.example deploy/alertmanager/alertmanager.yml
# Fill Slack webhook URL, PagerDuty routing key
# Add GitHub Secrets: ALERTMANAGER_SLACK_WEBHOOK_URL, ALERTMANAGER_PAGERDUTY_ROUTING_KEY

# 6. Verify
curl http://localhost:8000/health  # should show deep check green
python tools/healthcheck.py         # should exit 0
python -m pytest tests/ -x --tb=short -q  # should pass
```

---

## 📊 Performance Baseline

| Endpoint | RPS (target) | p95 | Error rate |
|----------|-------------|-----|-----------|
| `/api/v1/dashboard` | 50 | < 200ms | < 0.1% |
| `/api/v1/agent/run` | 10 (with Meta-RL) | < 800ms | < 0.1% |
| `/health` | 100 | < 50ms | 0% |
| `/readyz` | 100 | < 30ms | 0% |

### SLO (Beta)

| SLO | Target | Error Budget (30d) |
|-----|--------|-------------------|
| Availability | ≥ 99.0% | 7.2h/month |
| Dashboard latency p95 | < 200ms | TBD |
| Agent latency p95 | < 800ms | TBD |
| Error rate | < 0.1% | TBD |
| Health probe uptime | ≥ 99.9% | 43.2 min/month |

> **Note:** SLO targets calibrated for beta phase (G-09). Post-GA targets: 99.9% availability, < 500ms agent.

---

## 🔧 Known Issues

| Issue | Severity | Status | Tracked |
|-------|----------|--------|---------|
| Bandit: 9 medium findings (external code) | P3 | Skip rules in `.bandit`, CI `\|\| true` | v1.1.0 |
| Meta-RL: checkpoint stale after 24h | P3 | Fallback to static weights | v1.1.0 |
| `test_frontend_contract`: requires `REQUIRE_AUTH=false` | P2 | Mocked `get_settings()` (commit 19508f35) | v1.0.1 |
| Staging ≠ Production: Docker image pin drift | P2 | Pin digests pending | v1.0.1 |
| WAL-G restore: not tested on production volume (~500GB) | P1 | Synthetic data drill planned | v1.1.0 |

---

## 🧪 Testing

- **Unit tests:** 8/8 green (Python 3.11 + 3.12)
- **Frontend contract:** 4/4 (dashboard, agent-run, CORS preflight, secret leak)
- **Backtest:** 90-day window, BTCUSDT, 617 trades, Sharpe 0.01
- **WAL-G drill:** documented, not yet executed on real volume
- **Load test:** staging baseline (G-08), targets above

---

## 👥 Contributors

- **mahaasur13-sys** — architecture, agent development, security audit, Meta-RL
- **Zo Computer** (asurdev) — CI/CD, linting, observability, deployment docs

---

## 📚 Related Documents

- [`CHANGELOG.md`](./CHANGELOG.md) — full change history
- [`DEPLOYMENT.md`](./DEPLOYMENT.md) — production deployment guide
- [`docs/slo-calibration-2026-08-04.md`](./docs/slo-calibration-2026-08-04.md) — SLO methodology
- [`docs/on-call.md`](./docs/on-call.md) — on-call rotation + escalation
- [`PRODUCTION_BACKLOG.md`](./PRODUCTION_BACKLOG.md) — 87 tasks, 5 phases
- [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md) — tracked bugs

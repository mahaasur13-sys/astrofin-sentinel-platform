# Staging Smoke Test Plan — v1.0.0-beta (Sprint G-03)

**Дата:** 2026-07-26 | **Окружение:** Staging (Docker Compose)

---

## Pre-requisites

- Docker daemon running
- `.env` file с валидными credentials (create from `.env.example`)
- GitHub Secrets: `ALERTMANAGER_SLACK_WEBHOOK_URL`, `ALERTMANAGER_SMTP_PASSWORD`

---

## Test Matrix

| # | Сервис | Команда | Expected | Status |
|---|--------|---------|----------|--------|
| 1 | **PostgreSQL** | `docker-compose exec postgres pg_isready` | ✅ accepting connections | ⬜ |
| 2 | **TimescaleDB** | `psql -c "SELECT * FROM timescaledb_information.hypertable"` | hypertable `market_data` exists | ⬜ |
| 3 | **Redis** | `docker-compose exec redis redis-cli ping` | PONG | ⬜ |
| 4 | **App (/health)** | `curl http://localhost:8050/health` | `{"status":"ok"}` + DB check | ⬜ |
| 5 | **App (/readyz)** | `curl http://localhost:8050/readyz` | 200 | ⬜ |
| 6 | **Grafana** | `curl http://localhost:3000/api/health` | 200, datasources provisioned | ⬜ |
| 7 | **Loki** | `curl http://localhost:3100/ready` | "ready" | ⬜ |
| 8 | **Alertmanager** | `curl http://localhost:9093/api/v2/status` | 200, silences configured | ⬜ |
| 9 | **Prometheus** | `curl http://localhost:9090/api/v1/targets` | 200, targets up | ⬜ |
| 10 | **WAL-G backup** | `docker-compose exec postgres wal-g backup-push` | backup created | ⬜ |

---

## Launch

```bash
# Start full stack
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build

# Wait for healthy
sleep 30

# Run healthcheck
python tools/healthcheck.py

# Smoke test
./scripts/staging_smoke_test.sh
```

---

## Result

- **Pass:** 0/10
- **Fail:** 0/10
- **Report:** `docs/staging-smoke-test-2026-07-28.md`

# AstroFin Sentinel V5

RAG-First Multi-Agent Architecture with Thompson Sampling, KARL AMRE, and autonomous development loops.

## Architecture Overview
- **Orchestration:** `orchestration/sentinel_v5.py` — main entry point, routes queries, selects agents via Thompson Sampling, runs synthesis.
- **Agents:** 20+ specialized agents (technical, fundamental, astro, etc.) in `agents/_impl/`.
- **Monitoring:** Prometheus + Grafana (metrics on port 8000), Jaeger (traces on :16686), Alertmanager (alerts to Slack).
- **Infrastructure:** Docker Compose with TimescaleDB, Redis, Jaeger, Prometheus, Grafana, exporters, Alertmanager.
- **Autonomous Dev:** Ralph Loop (`scripts/ralph_loop.sh`) iterates over `docs/tickets.md`, writes tests, commits, and updates progress.

## Quick Start
1. Clone and enter project directory.
2. Create `.env` from `.env.example` and set required variables (see below).
3. Install dependencies: `pip install -r requirements.txt`
4. Start infrastructure: `docker compose up -d`
5. Run health endpoint: `python -m deploy.monitoring.health_endpoints`
6. Execute orchestrator: `python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING`

## Required Environment Variables (.env)
POSTGRES_PASSWORD=...
POSTGRES_USER=astrofin
POSTGRES_DB=astrofin
API_KEY=...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
VSELM_API_KEY=sk-...
text


## Monitoring Links
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- Jaeger: http://localhost:16686
- Health & Metrics: http://localhost:8000/health, /metrics

## Development with Ralph Loop
- Add tasks to `docs/tickets.md`
- Run `./scripts/ralph_loop.sh 3` to autonomously complete up to 3 tasks.
- Review and merge the created branch.

## Documentation
- A/B Testing: `deploy/README.md`
- Autonomous loop instructions: `RALPH_INSTRUCTIONS.md`
- Architecture details: see docstrings in `orchestration/sentinel_v5.py`

## CI/CD
[![CI](https://github.com/m)](https://github.com/m)
GitHub Actions run linting, security scan, and tests on every push. See `.github/workflows/ci.yml`.
compose stack.

### 7 workflow files.
# Changelog

## [1.0.0-beta] — 2026-07-26

### Added
- Meta-RL runtime inference routing (EnsembleAgent with checkpoint weights)
- Backtesting pipeline (90-day historical replay with PnL, Sharpe, win rate)
- Agent contracts (Pydantic models: AgentInput, AgentOutput)
- Deep health check (/health) with DB + CoinGecko + Ephemeris verification
- Readiness probe (/readyz) for k8s/Docker Compose
- Rate limiting (slowapi: 10/min agent/run, 60/min dashboard)
- API key rotation (X-API-Key + X-API-Key-Version)
- Circuit breakers (CoinGecko, Ephemeris, LLM Router)
- Asyncpg connection pool (min 5, max 20)
- TimescaleDB compression policy (market_data after 7 days)
- Secrets encryption at rest (Fernet + HMAC)
- Frontend contract validation test
- SLO validation under load report

### Changed
- CORS: allow_origins from * to FRONTEND_URL env var
- dashboard endpoint: fully async (removed loop.run_until_complete)
- /health: deep check includes DB + external providers
- Prometheus probes: /readyz instead of /health for up metric

### Fixed
- PII scrubber: JWT regex {8,}→{4,}, non-string/non-dict guards
- karl_synthesis_lag: split patch.multiple targets (10/10 pass)
- test_api_auth: Settings lru_cache clear (3/3 pass, no flaky)
- data-room CI: exit 127→0 (pytest-cov, aiohttp added)
- quality-gate.yml: YAML syntax fix
- nakshatra_risk: F401 ruff fix
- tempfile.mktemp→NamedTemporaryFile (B306 Bandit)
- Architecture linter: 3 hard violations→0 (BaseAgent, ephemeris, requests)

### Security
- 35 outdated packages updated (PR #268)
- SQL injection fix (data_room)
- Hardcoded password → env var
- Bandit: 0 HIGH/0 MEDIUM on project directories
- Architecture linter: 674→0 WARN

### Infrastructure
- WAL-G backup sidecar (S3-compatible, 4 scripts)
- Loki + Promtail logging pipeline
- Grafana provisioning: 6 dashboards auto-deploy
- SLO recording rules (3 SLOs: 99.9%, p95<200ms, error<0.1%)
- Alertmanager routing: critical→Slack, warning→email, SLO→channel
- 15 Prometheus alerts in 4 groups
- Blackbox probes: /health, /healthz, /readyz
- Nightly cron: DORA metrics, full tests, Dependabot auto-merge
- Docker Compose: all services with healthchecks, WAL-G sidecar

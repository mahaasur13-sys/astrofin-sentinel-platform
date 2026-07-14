# Security Architecture

## Authentication Flow
1. `REQUIRE_AUTH` env var must be `true` in production.
2. Every request must include `X-API-Key` header.
3. Flask decorator `@require_api_key` enforces this on all protected endpoints.
4. FastAPI dependency `fastapi_require_api_key` enforces on FastAPI routes.
5. If `API_KEY` is empty/unset while `REQUIRE_AUTH=true`, the server returns 500 (misconfiguration).

## Rate Limiting
- Flask-Limiter with Redis backend (fallback to in‑memory if Redis unavailable).
- Default: 100 requests/minute per IP.
- On limit breach: 429 Too Many Requests.

## Safety Gate (execution layer)
- Composition: `ModeEnforcer → RiskEngineV2 → SanityChecker`.
- Kill‑switch triggers on drawdown > configured threshold.

## Monitoring & Alerts
- `/metrics` endpoint optionally protected via `METRICS_AUTH_ENABLED`.
- Critical alerts defined in `deploy/monitoring/alerts.yml`.

## Audit Log
- Audit events are written to `audit_log` table.
- Retention policy: 90 days (configurable).

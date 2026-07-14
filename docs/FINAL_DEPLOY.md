# Final Deploy — Real Images (after submodule cleanup)

## Quick rebuild

```bash
cd ~/astrofin-sentinel-platform
git pull origin master
git submodule update --init --recursive
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up -d
sleep 30
docker compose ps
```

## Health checks (one per service)

```bash
# Web Dashboard (Dash on :8050)
curl -sS -o /dev/null -w "web:8050       HTTP ## Health checks (one per service)

```bash
curl -sS -o /dev/null -w "web:8050        HTTP %{http_code}\n" http://localhost:8050
curl -sS -o /dev/null -w "ml-engine:8081  HTTP %{http_code}\n" http://localhost:8081/health
curl -sS -o /dev/null -w "feature:8090    HTTP %{http_code}\n" http://localhost:8090/health
curl -sS -o /dev/null -w "gpu-worker:8000 HTTP %{http_code}\n" http://localhost:8000/health
docker exec astrofin-postgres pg_isready -U astrofin
docker exec astrofin-redis redis-cli ping
curl -sS -o /dev/null -w "prometheus:9090 HTTP %{http_code}\n" http://localhost:9090/-/ready
```

## What changed

Submodules `push` and `integrations/gitagent` were cleaned up locally; their entries remain in `.gitmodules` as registered paths but contain no gitlink (so `git submodule update` is a no-op for them). The platform runs entirely from the remaining 6 submodules:

- AsurDev (ml_engine)
- home-cluster-iac (feature_pipeline)
- roma-execution-bridge (gpu_worker)
- AstroFinSentinelV5 + astrofin-sentinel-v5 + atom-federation-os (compose orchestration context)

No stale docker-compose.yml edits. All 4 referenced Dockerfiles are real multi-stage slim images pinned at the commit recorded in the parent repo.

## Troubleshooting

- Submodule fails with "No url found": re-run `git submodule sync` then `git submodule update --init <path>`.
- Build fails with "requirements file not found": a submodule was deleted but `docker-compose.yml` still references it — restore the submodule or update compose.
- Containers UP but unhealthy: check `docker compose logs <svc>` — most common is a missing env var in `.env` (copy from `.env.example`).

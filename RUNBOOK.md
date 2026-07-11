# Operational Runbook — AstroFin Sentinel Platform

> **Audience:** On-call engineers, SRE, ops
> **Last reviewed:** 2026-06-26

This runbook covers the most common incident scenarios. Each scenario follows the
same shape: **Detect → Triage → Mitigate → Recover → Post-mortem**.

---

## 0. General triage commands

```bash
# Cluster / pod state
kubectl -n astrofin-sentinel get pods
kubectl -n astrofin-sentinel describe deploy/astrofin-sentinel-web
kubectl -n astrofin-sentinel logs -l app.kubernetes.io/name=astrofin-sentinel-web --tail=200

# Service endpoints
kubectl -n astrofin-sentinel get svc,ep,hpa

# Docker (local dev)
docker ps --filter name=astrofin
docker logs --tail=200 astrofin-sentinel-v5

# Host-level (Zo / dev VM)
ss -tlnp | grep 8050
curl -fsS http://127.0.0.1:8050/healthz
```

---

## 1. PostgreSQL connection failure

**Symptoms**
- `psycopg2.OperationalError: could not connect to server`
- Logs: `FATAL: password authentication failed for user "astrofin"`
- Healthcheck returns `503`.

**Triage**
```bash
# Is postgres up?
docker ps --filter name=postgres
pg_isready -h 127.0.0.1 -p 5432

# From inside the pod
kubectl -n astrofin-sentinel exec deploy/astrofin-sentinel-web -- \
  pg_isready -h $POSTGRES_HOST -p 5432 -U $POSTGRES_USER
```

**Mitigate**
1. If Postgres container is down → `docker compose up -d postgres`.
2. If connection limit hit → check `pg_stat_activity` and kill long-running sessions.
3. If credentials rotated → update the `astrofin-sentinel-secrets` Secret and roll the deployment.

**Recover**
- `kubectl -n astrofin-sentinel rollout restart deploy/astrofin-sentinel-web`
- Confirm `/healthz` returns 200.

---

## 2. Redis down (cache + pubsub)

**Symptoms**
- `redis.exceptions.ConnectionError`
- Web dashboard: missing live data, stale metrics.

**Triage**
```bash
redis-cli -h 127.0.0.1 ping
docker logs --tail=200 astrofin-redis
```

**Mitigate**
1. `docker compose up -d redis` if down.
2. If OOM → `docker inspect astrofin-redis | jq '.[0].HostConfig.Memory'`.
3. Fall back to in-process cache: `CACHE_BACKEND=memory` env override.

**Recover**
- Verify `redis-cli ping` → `PONG`.
- Replay any sessions that depended on Redis pubsub.

---

## 3. Broker disconnect (Alpaca / Tinkoff / Binance)

**Symptoms**
- Logs: `BrokerDisconnected`, repeated `reconnect attempt N/5`.
- `/data-room/conflicts` shows `broker_unavailable` rows.

**Triage**
```bash
curl -fsS https://api.alpaca.markets/v2/clock || echo "alpaca down"
curl -fsS https://api.binance.com/api/v3/ping
```

**Mitigate**
1. The broker clients reconnect with exponential backoff (1s → 30s).
2. If persistent, check whether API keys were rotated.
3. Pause live trading: `TRADING_ENABLED=false` (ConfigMap toggle), then rollout restart.

**Recover**
- Confirm reconnect logs: `broker=alpaca state=connected`.
- Resume trading after `/healthz` is green for 5 consecutive minutes.

---

## 4. High latency / healthcheck failure

**Symptoms**
- `/healthz` > 2s or returns 5xx.
- Prometheus `request_latency_seconds` p99 > 1s.

**Triage**
```bash
# Local
curl -w "%{time_total}\n" -o /dev/null -s http://127.0.0.1:8050/healthz

# Cluster
kubectl -n astrofin-sentinel top pods
kubectl -n astrofin-sentinel logs --previous -l app.kubernetes.io/name=astrofin-sentinel-web | tail -100
```

**Mitigate**
1. If CPU saturated → HPA should already scale; verify `kubectl get hpa`.
2. If downstream (Postgres / Redis / Broker) slow → follow sections 1–3 first.
3. As a last resort: scale manually `kubectl scale deploy/astrofin-sentinel-web --replicas=6`.

**Recover**
- Watch p99 return below 500ms for 10 minutes.
- If HPA did not fire, file an incident — autoscale config may need tuning.

---

## 5. Secret rotation incident

**Symptoms**
- Service returns 401/403 from broker APIs.
- Logs: `auth failed`, `signature mismatch`.

**Triage**
- Compare failing pod's env (sanitised) against the Secret:
  `kubectl -n astrofin-sentinel get secret astrofin-sentinel-secrets -o jsonpath='{.data}' | base64 -d`.

**Mitigate**
1. Rotate the upstream broker key.
2. Update the Secret: `kubectl create secret generic astrofin-sentinel-secrets --from-literal=... -n astrofin-sentinel --dry-run=client -o yaml | kubectl apply -f -`
3. Roll the deployment: `kubectl -n astrofin-sentinel rollout restart deploy/astrofin-sentinel-web`.

**Recover**
- Confirm next healthcheck is 200 and broker API responses are 2xx.

---

## 6. CI / deploy pipeline failure

**Symptoms**
- GitHub Actions red on `master`.
- Image not built / not pushed.

**Triage**
- Inspect `.github/workflows/` run logs.
- Check `ghcr.io/mahaasur13-sys/astrofin-sentinel-web` visibility and tags.

**Mitigate**
- Re-run workflow; if image push fails on permissions, confirm `packages: write` token scope.
- Fall back to manual build:
  ```bash
  docker build -t astrofin-sentinel-web:dev .
  docker run --rm -p 8050:8050 astrofin-sentinel-web:dev
  ```

---

## Appendix: Key URLs / endpoints

| Resource | URL |
|---|---|
| Health (web) | `/healthz` |
| Readiness | `/readyz` |
| Conflict journal | `/data-room/conflicts` |
| Metrics (Prometheus) | `/metrics` |

## Appendix: Escalation

1. Slack `#oncall-astrofin`
2. PagerDuty service `astrofin-sentinel-prod`
3. Platform owner (see `CODEOWNERS`)
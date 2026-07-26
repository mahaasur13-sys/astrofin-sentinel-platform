# 🚀 Deployment Guide — AstroFin Sentinel Platform v1.0.0

> **Audience:** DevOps / SRE / on-call engineers bringing v1.0.0 to production.
> **Stack:** Docker Compose (1-3 nodes) or Kubernetes (≥1.27) + TimescaleDB + Redis + Prometheus + Grafana + Alertmanager.
> **Minimum requirements:** 4 vCPU, 16 GB RAM, 80 GB SSD per app node; 4 vCPU, 16 GB RAM, 200 GB SSD for the DB node.

---

## 0. Pre-flight checklist

## Quickstart — 5 minutes to production

```bash
# 1. Clone
git clone https://github.com/mahaasur13-sys/astrofin-sentinel-platform.git
cd astrofin-sentinel-platform

# 2. Environment
cp .env.example .env
# Edit: POSTGRES_PASSWORD, API_KEYS, ALERTMANAGER_*

# 3. Dependencies
uv sync --extra dev

# 4. Database
docker-compose up -d postgres redis
alembic upgrade head

# 5. App
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 6. Verify
curl http://localhost:8000/health
curl http://localhost:8000/readyz

# 7. Observability (optional)
docker-compose -f docker-compose.yml -f docker-compose.logging.yml up -d
# Grafana: http://localhost:3000 (admin/admin)
```

Full deployment guide below (Docker Compose, Kubernetes, monitoring, WAL-G backup).

---



- [ ] DNS records for `app.<your-domain>`, `api.<your-domain>`, `dash.<your-domain>` pointing to the load balancer.
- [ ] TLS certificates (Let's Encrypt or your CA) in `deploy/tls/`.
- [ ] S3-compatible bucket for backups (e.g. `s3://astrofin-backups-<env>/`).
- [ ] Secrets stored in Vault / SOPS-encrypted `.env.prod` (see §3).
- [ ] Slack/PagerDuty webhook for Alertmanager (optional but recommended).
- [ ] `gh auth status` passes for the deployer account (needs `workflow` scope for CD).

---

## 1. Architecture overview

```
                ┌──────────────┐
                │   Internet   │
                └──────┬───────┘
                       │ TLS
              ┌────────▼─────────┐
              │  Nginx / Envoy   │  (TLS termination, rate-limit, CORS)
              └────────┬─────────┘
        ┌──────────────┼──────────────┐
        │              │              │
  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
  │  web/     │  │ health_   │  │  ml-      │
  │  Dash UI  │  │ endpoints │  │  engine   │
  │  :8050    │  │  :8080    │  │  :8090    │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        └──────────────┼──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
  ┌─────▼──────────┐         ┌───────▼──────┐
  │  TimescaleDB   │         │    Redis      │
  │  :5432         │         │    :6379      │
  │  (hypertable)  │         │  (auth ON)    │
  └────────────────┘         └───────────────┘

  Monitoring (sidecars / separate compose):
  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐
  │Prometheus│  │ Alertmanager │  │ Grafana  │  │ node_exp.  │
  │  :9090   │  │    :9093     │  │  :3000   │  │   :9100    │
  └──────────┘  └──────────────┘  └──────────┘  └────────────┘
```

---

## 2. Quick start — Docker Compose (1 host, staging / dev)

```bash
# 1. Clone
git clone https://github.com/mahaasur13-sys/astrofin-sentinel-platform.git
cd astrofin-sentinel-platform
git checkout v1.0.0

# 2. Secrets
cp .env.prod.example .env.prod
$EDITOR .env.prod   # set all REQUIRED_* keys (see §3)

# 3. Pull images (cosign-verified — see §6)
docker compose -f deploy/docker/docker-compose.yml pull

# 4. Boot
docker compose -f deploy/docker/docker-compose.yml up -d

# 5. Verify
curl -fsS http://localhost:8080/healthz | jq
curl -fsS http://localhost:8080/readyz  | jq
open http://localhost:8050   # Dash UI
open http://localhost:3000   # Grafana (admin / $GRAFANA_ADMIN_PASSWORD)
```

To bring up monitoring only:
```bash
docker compose -f deploy/docker/docker-compose.yml --profile monitoring up -d
```

---

## 3. Required environment variables

The app refuses to start if any `REQUIRED_*` variable is missing. `tools/check_env.py` runs as a preflight.

| Variable | Required | Example | Notes |
|---|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://astrofin:$PG_PASSWORD@db:5432/astrofin` | TimescaleDB ≥ 2.13 with `timescaledb` and `vector` extensions |
| `REDIS_URL` | ✅ | `redis://:$REDIS_PASSWORD@redis:6379/0` | Redis ≥ 7, `requirepass` enabled (PR #124) |
| `API_KEY` | ⚠️ deprecated | — | Use `JWT_PUBLIC_KEY` (RS256). Kept for the dual-mode deprecation window. |
| `JWT_PUBLIC_KEY` | ✅ | `-----BEGIN PUBLIC KEY-----…` | RS256 only, ≥ 2048-bit |
| `JWT_ISSUER` | ✅ | `https://auth.astrofin.example` | Must match `iss` claim |
| `JWT_AUDIENCE` | ✅ | `astrofin-sentinel` | Must match `aud` claim |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | ✅ | `http://otel-collector:4317` | OTLP gRPC |
| `OTEL_SERVICE_NAME` | ✅ | `astrofin-sentinel` | |
| `SENTRY_DSN` | optional | `https://…@sentry.io/123` | PII scrubber is applied before send (PR #133) |
| `S3_BACKUP_BUCKET` | ✅ | `s3://astrofin-backups-prod` | WAL-G target |
| `GRAFANA_ADMIN_PASSWORD` | ✅ | — | ≥ 16 chars, rotated quarterly |
| `ALLOWED_ORIGINS` | ✅ | `https://app.astrofin.example,https://dash.astrofin.example` | Comma-separated, CORS whitelist |
| `LOG_LEVEL` | optional | `INFO` | `DEBUG` only in dev |
| `LOG_PII_SCRUB` | optional | `true` | Default `true` in prod |

Template: `.env.prod.example` (commited, no real secrets).

---

## 4. Kubernetes (production, multi-node)

Manifests live in `home-cluster-iac/` (submodule, planned to migrate to root — see PRODUCTION_BACKLOG P5-13).

```bash
# Apply namespaces + secrets
kubectl apply -f home-cluster-iac/k8s/00-namespace.yaml
sops -d home-cluster-iac/k8s/secrets/astrofin-prod.enc.yaml | kubectl apply -f -

# Storage class + PVCs
kubectl apply -f home-cluster-iac/k8s/10-storage.yaml

# Stateful workloads
kubectl apply -f home-cluster-iac/k8s/20-timescaledb.yaml
kubectl apply -f home-cluster-iac/k8s/21-redis.yaml

# App (Argo Rollouts canary)
kubectl apply -f home-cluster-iac/k8s/30-astrofin-rollout.yaml
kubectl apply -f home-cluster-iac/k8s/31-astrofin-services.yaml

# Ingress + TLS
kubectl apply -f home-cluster-iac/k8s/40-ingress.yaml

# Monitoring
kubectl apply -f home-cluster-iac/k8s/50-monitoring.yaml
```

### Health checks

```bash
# Liveness — process is up
curl -fsS https://api.astrofin.example/livez | jq

# Readiness — DB + Redis + agents reachable
curl -fsS https://api.astrofin.example/readyz | jq

# Component-by-component
curl -fsS https://api.astrofin.example/healthz | jq '.checks'
```

`/readyz` must return 200 for the load balancer to send traffic. If `/readyz` returns 503, the pod is taken out of the service endpoints automatically.

---

## 5. Database migrations

Alembic, run automatically by the app on boot. To run manually:

```bash
docker compose exec api alembic upgrade head
```

For zero-downtime schema changes:
1. Add migration (backward-compatible).
2. Deploy new app version.
3. Wait for full rollout.
4. Add backfill migration (if needed).
5. Remove old columns in a follow-up PR.

See `RUNBOOK.md` §"DB migrations" for rollback procedure.

---

## 6. Image verification (SLSA / cosign)

Images are signed with cosign keyless (OIDC) and tagged `v1.0.0`, `v1.0`, `v1`, `latest`.

```bash
cosign verify \
  --certificate-identity-regexp 'https://github.com/mahaasur13-sys/astrofin-sentinel-platform' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  ghcr.io/mahaasur13-sys/astrofin-sentinel-platform:v1.0.0
```

If verification fails, **do not** pull the image — investigate the build log instead.

---

## 7. Backups & restore

- **Continuous**: WAL-G streams WAL to `S3_BACKUP_BUCKET` every 5 min.
- **Daily full**: `pg_basebackup` to S3, retained 30 days.
- **Restore drill**: scheduled quarterly (PRR acceptance criteria, PRODUCTION_BACKLOG P5-10).

```bash
# Restore to a point in time (example: 30 minutes ago)
wal-g backup-list $S3_BACKUP_BUCKET
wal-g fetch $S3_BACKUP_BUCKET --restore-target-time="$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)"
```

See `RUNBOOK.md` §"Disaster recovery" for the full procedure and quarterly drill checklist.

---

## 8. Monitoring & alerts

Dashboards (auto-provisioned):
- `/d/slo-overview` — SLO burn-rate, error budget remaining.
- `/d/sentinel-health` — agents agreement, RAG hit rate, signal throughput.
- `/d/infra` — DB connections, Redis memory, pod CPU/mem, network.

Key alerts (all routed via Alertmanager → Slack + PagerDuty):
- `SLOErrorBudgetBurn` — 14× burn-rate over 1h → page.
- `PostgresDown` — DB unreachable > 30s → page.
- `HighAgentDisagreement` — council spread > 0.4 for 10 min → Slack.
- `PIILeakSuspected` — PII scrubber detected > 0 raw hits → page (CRITICAL).
- `JwtAuthFailureSpike` — > 10 401/s for 5 min → Slack.

Full list: `deploy/monitoring/alert_rules.yml` (15 alerts: SLO burn, service health, K8s infra, WAL-G backup).

---

## 9. Upgrading from a previous version

1. Read the [CHANGELOG](./CHANGELOG.md) entry for the target version.
2. Check `PRODUCTION_BACKLOG.md` for breaking-change flags.
3. Run `python tools/check_env.py` — fail-fast on missing/renamed env vars.
4. Apply DB migrations (`alembic upgrade head`) before rolling pods.
5. Roll pods via the standard canary pipeline (Argo Rollouts or compose `up -d --no-deps api`).
6. Watch `/readyz` and the SLO dashboard for 30 min.
7. If SLO burn-rate > 14× → auto-rollback fires (Phase 5, P5-02).

---

## 10. Troubleshooting

| Symptom | First check | Docs |
|---|---|---|
| 503 on `/readyz` | `kubectl describe pod`, `docker compose logs api` | `RUNBOOK.md` §"Pod not ready" |
| `psycopg.OperationalError: connection refused` | `pg_isready -h db`, PVC bound? | `RUNBOOK.md` §"DB outage" |
| Agent signals all `NEUTRAL` | `RAG hit rate` dashboard, `redis-cli ping` | `RUNBOOK.md` §"Signal flatline" |
| PagerDuty flood | `kubectl top pods`, check for OOMKilled | `RUNBOOK.md` §"Memory pressure" |
| CI red after deploy | `gh pr checks`, `KNOWN_ISSUES.md` | `CONTRIBUTING.md` §"CI recovery" |

For anything not covered here → Slack `#oncall-astrofin` (P5-08) or `docs/postmortems/`.

---

## 9. TimescaleDB Setup

### 9.1 Hypertable (Migration 0008)

Migration 0008 creates  hypertable:



Verify: 

### 9.2 Compression Policy (Migration 0009)

Chunks >7 days compressed (~90% space savings):



### 9.3 asyncpg Pool



Health: 

---

## 10. WAL-G Backup & Restore

Scripts: , , , 

Full restore drill: see 

Quick restore: 

---

## 11. Loki + Promtail



Query: {"status":"success","data":{"resultType":"streams","result":[],"stats":{"summary":{"bytesProcessedPerSecond":0,"linesProcessedPerSecond":0,"totalBytesProcessed":0,"totalLinesProcessed":0,"execTime":0.009983,"queueTime":0.000059,"subqueries":0,"totalEntriesReturned":0,"splits":2,"shards":2,"totalPostFilterLines":0,"totalStructuredMetadataBytesProcessed":0},"querier":{"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":0,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}}},"ingester":{"totalReached":2,"totalChunksMatched":0,"totalBatches":2,"totalLinesSent":0,"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":251439,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}}},"cache":{"chunk":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"index":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"result":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"statsResult":{"entriesFound":0,"entriesRequested":1,"entriesStored":1,"bytesReceived":0,"bytesSent":0,"requests":2,"downloadTime":6370,"queryLengthServed":0},"volumeResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"seriesResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"labelResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"instantMetricResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0}},"index":{"totalChunks":0,"postFilterChunks":0,"shardsDuration":0,"usedBloomFilters":false}}}}

---

## 12. Meta-RL Checkpoint & Fallback



If checkpoint stale >24h → fallback to static weights in .

Manual update: 

---

## 13. PII Scrubber

 — enabled by default. Patterns: JWT, phone, email, wallet.

Disable: .

---

## 14. Grafana Provisioning

Dashboards auto-loaded from :
- AstroFin Overview, Agent Performance, Redis, PostgreSQL, SLO Burn-Down, Meta-RL Training

No manual import needed.

---

## 15. References

- [`RUNBOOK.md`](./RUNBOOK.md) — operator runbook, top-15 alerts.
- [`SLO.md`](./SLO.md) — SLO/SLI definitions and error-budget policy.
- [`SECURITY.md`](./SECURITY.md) — disclosure policy, supported versions.
- [`PRIVACY.md`](./PRIVACY.md) — data inventory, GDPR.
- [`PRODUCTION_BACKLOG.md`](./PRODUCTION_BACKLOG.md) — known gaps, roadmap.
- [`CHANGELOG.md`](./CHANGELOG.md) — release history.
- [`MIGRATION_GUIDE.md`](./MIGRATION_GUIDE.md) — moving from older snapshots.
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — system architecture.
### 1.1 Docker Buildx fix (required)

If  fails with:





### 1.2 TimescaleDB (migrations 0008 + 0009)

After :



Verify:


### 1.3 asyncpg Connection Pool

Env vars in :



**Monitoring:**



For the full connection pool runbook, see: .

### 1.4 WAL-G Continuous Backup

**Infrastructure:**
- Sidecar container: , , , 
- S3 target:  (e.g. )
- Cron: nightly  + continuous WAL archiving via 

**Disaster recovery drill:** 

**Troubleshooting:**



### 1.5 PII Scrubber

Module:  — 19 patterns (JWT, phone, email, wallet, SSN).
Runs automatically on all log/session output.



### 1.6 Grafana Provisioning (Auto-Load)

Dashboards are provisioned as code in :
- 6 dashboards, 43 panels
- Datasources: Prometheus + Loki (auto-discover)
- Alertmanager UI: 

After deploy, verify in Grafana:
- Datasources → Prometheus + Loki → Test → green
- Dashboards → all 6 appear without manual import

### 1.7 Loki + Promtail (Log Aggregation)

Ingester not ready: waiting for 15s after being ready
{"status":"success","data":["filename","job","service_name"]}

Query logs in Grafana Explore:


### 1.8 Meta-RL Checkpoint (Startup/Warmup)



**Warmup (before load test / production):**



---



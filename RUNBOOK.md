# RUNBOOK — astrofin-sentinel-platform

> Top-level on-call runbook. For service-specific procedures, see `docs/RUNBOOK.md`.
> For SLIs/SLOs, see [`SLO.md`](./SLO.md). For ownership, see [`MAINTAINERS.md`](./MAINTAINERS.md).

## Contacts

| Role | Name | Contact | Time zone |
|---|---|---|---|
| Primary on-call | Felix | `@1022845958` (Telegram) / `mahaasur13@gmail.com` | Europe/Samara |
| Backup          | Felix (solo) | same as primary | — |
| Escalation      | TBD Q3 2026 on-call rotation | — | — |

## Severity definitions

| Sev | Definition | Response time |
|---|---|---|
| SEV-1 | Trading signal generation broken; `run_sentinel_v5` failing | 15 min |
| SEV-2 | Dashboard unreachable; backtest queue stuck | 1 h |
| SEV-3 | Single agent degraded; A/B compare returns stale data | next business day |

## Common procedures

### Restart the web service

```bash
# On the Zo host
systemctl --user restart astrofin-web   # or: docker compose restart web
curl -fsS http://127.0.0.1:8050/healthz | jq .
```

### Restart the ML inference service

```bash
kubectl -n astrofin rollout restart deploy/ml-inference
kubectl -n astrofin rollout status  deploy/ml-inference
```

### Backup & Disaster Recovery (WAL-G)

**Current posture:** base `postgres` runs with `archive_mode=off` (live `pg_data` is
**not** PITR-capable). PITR is only on the optional archive cluster
(`postgres-archive` / `pg_data_archive`). See `docs/RUNBOOK.md` §Backups/PITR.

Backup script: `deploy/wal-g/backup.sh`. Restore is **drill-only**:
`scripts/walg_restore_drill.sh <empty-dest>` (`deploy/wal-g/restore.sh` is a safe
wrapper; it never `pg_ctl stop` / `backup-fetch` into live PGDATA).

#### Take a manual full backup (archive cluster)
```bash
docker compose -f deploy/docker/docker-compose.yml \
  -f deploy/docker/docker-compose.postgres-archive.yml \
  -f deploy/docker/docker-compose.wal-g.yml \
  --profile archive --profile backup \
  run --rm wal-g backup-push /var/lib/postgresql/data
```

#### Restore drill (safe, never into live data)
```bash
scripts/walg_restore_drill.sh /tmp/pg-drill   # LATEST (archive backup)
scripts/walg_restore_drill.sh /tmp/pg-drill base_00000001000000000000000F
```
(refuses `/var/lib/postgresql/data`, `$PGDATA`, `pg_data`, `pg_data_archive`,
`docker_pg_data` with exit 2)

#### Verify backup integrity
```bash
docker compose -f deploy/docker/docker-compose.yml -f deploy/docker/docker-compose.postgres-archive.yml -f deploy/docker/docker-compose.wal-g.yml --profile archive --profile backup run --rm wal-g backup-list --detail
```

#### Schedule
- Full backup: opt-in (manual / `--profile backup`), no cron on live.
- WAL archival: archive cluster only (`archive_mode=on`); base stays **off**.
- Retention: 7 daily + 4 weekly + 6 monthly (see `wal-g.env`)

### Rotate secrets (JWT keys, API tokens)

1. Generate the new key pair: `scripts/issue_jwt.py --rotate --ttl 24h`.
2. Publish public key to `JWT_PUBLIC_KEY_PATH` (atomic write, no in-place edit).
3. Roll all services: `kubectl -n astrofin rollout restart deploy/`.
4. Revoke the old key in the JWKS endpoint.
5. Verify with `curl -H "Authorization: Bearer $NEW_TOKEN" https://.../healthz`.

### Recover from a failed CI release

1. `gh run list --workflow release --limit 5`
2. `gh run rerun <run-id> --failed`
3. If still red, roll back: `git tag v1.0.0-rollback && git push --tags`.
4. Open an incident in `#oncall-astrofin`.

## Dashboards & links

- Grafana: https://grafana.astrofin.internal/d/web-dashboard
- Prometheus: https://prometheus.astrofin.internal
- Loki: https://loki.astrofin.internal (logs)
- Repo: https://github.com/mahaasur13-sys/astrofin-sentinel-platform
- Issue tracker: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues

## Post-incident

- File a postmortem within 48 h: `docs/postmortems/YYYY-MM-DD-<slug>.md`.
- Action items must reference an issue or PR.
- SLO impact: log it in `SLO.md` §"Error budget ledger".

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

### Restore the analytics DB from backup

PITR via WAL-G is not yet configured (issue #131). Until then:

1. `systemctl stop astrofin-web`
2. `cp data/history.db data/history.db.broken-$(date +%s)`
3. Restore from the latest S3 snapshot: `aws s3 cp s3://astrofin-backups/history/latest.db data/history.db`
4. Re-apply migrations forward only: `python -m migrations.migrate up`
5. `systemctl start astrofin-web && curl -fsS http://127.0.0.1:8050/healthz`

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

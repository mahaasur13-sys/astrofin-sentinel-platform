# Production-ready checklist

## 1) Merge done
- PR #15 merged into `master` (squash: `2f2ca96538a5`).

## 2) GitHub environments
Create these in the repository settings (`Settings` → `Environments`):
- `staging` — no protection rules.
- `production` — require at least 1 reviewer.

## 3) Secrets
### staging
- `GHCR_TOKEN` — push/pull images from GHCR.
- `KUBE_CONFIG_STAGING` — kubeconfig for staging cluster.
- `STAGING_HEALTHCHECK_URL` — smoke-test URL for staging.
- `SLACK_WEBHOOK_URL` — staging notifications.

### production
- `KUBE_CONFIG_PROD` — kubeconfig for production cluster.
- `SLACK_WEBHOOK_URL` — production notifications.
- `GHCR_TOKEN` — if production pull policy requires explicit auth.

## 4) Grafana dashboard
Import `deploy/monitoring/grafana-dashboard.json` in Grafana:
- UI: Dashboards → New → Import → paste JSON file contents.
- Or use Grafana HTTP API if you already have auth configured.

## 5) First release
- Create tag `v1.0.0-rc1` (or run `./scripts/first-release.sh`).
- Push tag to `origin`.
- Open GitHub Actions and wait for deploy + smoke test.

## 6) Dependabot
Verify in GitHub:
- Insights → Dependency graph → Dependabot.

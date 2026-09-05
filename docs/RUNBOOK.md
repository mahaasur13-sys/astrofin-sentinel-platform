# Operational Runbook — AstroFin Sentinel Platform

> **Audience:** On-call engineers, SRE, ops
> **Last reviewed:** 2026-06-26

This runbook covers the most common incident scenarios. Each scenario follows the
same shape: **Detect → Triage → Mitigate → Recover → Post-mortem**.

---

## Bootstrap: start the prod stack

The prod compose is `deploy/docker/docker-compose.yml` (app + postgres + redis +
prometheus + grafana). It guards three variables with `${VAR:?}` — set them
before running:

```bash
export POSTGRES_PASSWORD="<real-password>"
export DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/astrofin"
export GF_SECURITY_ADMIN_PASSWORD="<grafana-admin-password>"

# Validate interpolation (no build, no start)
docker compose -f deploy/docker/docker-compose.yml config --quiet
# Start
docker compose -f deploy/docker/docker-compose.yml up -d
```

- No service publishes on `0.0.0.0`. `postgres` (5432), `redis` (6379), `app`
  (8000) and `prometheus` (9090) are internal-only on the compose network
  (#329). The only host binding is Grafana, loopback-only: `127.0.0.1:3000:3000`.
- Grafana reaches Prometheus by service name (`prometheus:9090`); the daemon's
  `app:9191` metrics are likewise internal-only (not host-reachable).
- `GF_SECURITY_ADMIN_PASSWORD` is a hard `${VAR:?}` guard — there is no
  `admin/admin` default in the image or compose, so `grafana` will not start
  unless this env is set.
- Prometheus image is pinned (`prom/prometheus:v2.54.1`); the compose `version:`
  key was removed as obsolete.
- The app image build context is the repo root and is filtered by the root
  `.dockerignore` — it must never ship `.git`, `.venv`, `deploy/docker/secrets`
  or `deploy/docker/certs` into the image.

## Base full smoke

- Required env (4× `${VAR:?}`): `DATABASE_URL`, `POSTGRES_PASSWORD`,
  `GF_SECURITY_ADMIN_USER`, `GF_SERVER_ROOT_URL=http://127.0.0.1:3000`.
- Required files: `deploy/docker/secrets/grafana_admin_password` and
  `grafana_secret_key` (`chmod 644` for uid 472 — see C9).
- Agree the DB password with the URL (host = `postgres` service name):
  `export POSTGRES_PASSWORD=...`
  `export DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/astrofin"`
- Bring up the whole base (not just grafana):
  `docker compose -f deploy/docker/docker-compose.yml up -d`
- Verify:
  - `docker compose ps` → app / postgres / redis / prometheus / grafana
  - Grafana: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/login` → 200
  - Postgres ready: `docker compose exec postgres pg_isready -U postgres`
  - app metrics: `docker compose exec app curl -fsS http://localhost:9191/metrics`
- Grafana login: user from `GF_SECURITY_ADMIN_USER`, password from the
  `grafana_admin_password` file.
- Do not enable C7 / C11 / C12 overlays for this base smoke.
- The app entrypoint runs `python -m db` (idempotent `create_all`, no DROP)
  before the orchestrator; manual `exec python -m db` is no longer needed.
- On an already-populated volume re-running init is a harmless no-op.

Grafana hardening (C2):

- `GF_SECURITY_ADMIN_USER` and `GF_SECURITY_ADMIN_PASSWORD` are both `${VAR:?}`
  guards — grafana won't start in this compose without them.
- The official `grafana/grafana` image still defaults to `admin/admin` if run
  **outside** this compose; this file overrides it, disables signup and anon.
- Rotate the admin password after first login; never expose `:3000` to the
  internet without a reverse-proxy in front.

Grafana hardening (C3):

- `GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD` and
  `GF_SECURITY_SECRET_KEY` are all `${VAR:?}` — grafana won't start in this
  compose without all three.
- The official image ships a known default `GF_SECURITY_SECRET_KEY`
  (`SW2YcwTIb9zpOOhoPsMm`) — never leave it set.
- From the host `:3000` is loopback-only (or via reverse-proxy); don't publish
  it to the internet. Rotating `GF_SECURITY_SECRET_KEY` invalidates session
  cookies.

Grafana hardening (C4):

- `GF_SERVER_ROOT_URL` is the fourth required `${VAR:?}` — set it to the exact
  URL users open the UI with (`http://127.0.0.1:3000`).
- Embedding and org-create are off; `SameSite=strict`.
- `GF_SECURITY_COOKIE_SECURE=false` on purpose while there is no HTTPS (C5).
- Rotating the admin password / secret key resets existing sessions.

Grafana TLS (C5):

- HTTP loopback is unchanged — a single compose file:
  `docker compose -f deploy/docker/docker-compose.yml up -d`.
- TLS is an overlay: `docker compose -f docker-compose.yml -f
  docker-compose.grafana-tls.yml up -d`; it sets `PROTOCOL=https` and
  `COOKIE_SECURE=true`, serving `https://127.0.0.1:3000`.
- Generate self-signed certs with `scripts/gen_grafana_dev_certs.sh`
  (SAN `127.0.0.1`/`localhost`); the browser will warn about self-signed.
- `COOKIE_SECURE=true` only in the TLS profile; certs are gitignored.

Grafana generic OAuth / OIDC (C6):

- Enable: `docker compose -f docker-compose.yml -f
  docker-compose.grafana-oidc.yml up -d` (TLS+OIDC: add the TLS overlay as a
  third file).
- Seven `${VAR:?}` env are required: NAME, CLIENT_ID, CLIENT_SECRET, AUTH_URL,
  TOKEN_URL, API_URL, SCOPES. `ALLOW_SIGN_UP=false`.
- The password login form stays (`DISABLE_LOGIN_FORM=false`) — otherwise you
  get locked out if the IdP is unreachable.
- Don't enable the overlay in prod without a live, reachable IdP.

Grafana edge proxy (C7):

- Profiles (stack with `-f deploy/docker/docker-compose.yml`):
  - `base` → HTTP `http://127.0.0.1:3000`
  - `+ docker-compose.grafana-tls.yml` → HTTPS on 3000
  - `+ docker-compose.grafana-oidc.yml` → generic OAuth
  - `+ docker-compose.grafana-edge.yml` → Caddy edge
  - `+ tls + oidc` → three files combined
- Edge: Grafana drops its host port; Caddy serves `https://127.0.0.1:8443`
  (and `http://127.0.0.1:8080` health), proxying to `grafana:3000`.
- `DOMAIN` and `ACME_EMAIL` are `${VAR:?}`; Let's Encrypt / `0.0.0.0` is NOT
  the default (commented out in the Caddyfile).
- No Keycloak / IdP service in this repo.

Grafana oauth2-proxy (C8):

- Enable: `docker compose -f docker-compose.yml -f
  docker-compose.grafana-oauth2-proxy.yml up -d`; UI: `http://127.0.0.1:4180`.
- Five `${VAR:?}` env required: CLIENT_ID, CLIENT_SECRET, COOKIE_SECRET,
  OIDC_ISSUER_URL, REDIRECT_URL. Don't enable without a reachable IdP.
- C8 ≠ C6 (Grafana Generic OAuth) — don't combine them unless you know why.
- `EMAIL_DOMAINS=*` is dev-only; `COOKIE_SECURE=false` on the HTTP loopback.
- Keycloak / public Let's Encrypt are out of scope.

Grafana secrets from files (C9):

- Admin password and secret key come from `deploy/docker/secrets/` files
  (`grafana_admin_password`, `grafana_secret_key`); without them the stack will
  not start (Compose fails on the missing secret file).
- They are mounted as `/run/secrets/*` and read via `*__FILE` env vars, so
  `docker inspect` / compose config no longer shows the password/key.
- Grafana reads them as **uid 472** inside the container: a host `chmod 600`
  owned by your user fails with
  `run.sh: ... /run/secrets/grafana_secret_key: Permission denied`.
- dev (rootless Docker): `chmod 644`; prod: `chown 472:472 && chmod 440`
  (verify on rootless, else fall back to 644).
- Rotation = rewrite the file + `docker compose up -d --force-recreate grafana`.
- A full `up` of the base stack also needs `DATABASE_URL` and `POSTGRES_PASSWORD`
  (app/postgres services), plus `GF_SECURITY_ADMIN_USER` and `GF_SERVER_ROOT_URL`.
- C10 (Dex) / C11 / C12 are out of scope.

Grafana Dex IdP (C10):

- Enable: `docker compose -f docker-compose.yml -f docker-compose.dex.yml up -d`.
  Grafana UI stays on `:3000`; Dex issuer is `http://127.0.0.1:5556/dex`
  (internal container URL is `http://dex:5556/dex`).
- Wire it to C6 Generic OAuth: `AUTH_URL=http://127.0.0.1:5556/dex/auth`,
  `TOKEN_URL=.../token`, `API_URL=.../userinfo`, `SCOPES=openid email profile`.
- C8 (oauth2-proxy) is a different profile — don't mix without a reason.
- No users/passwords are committed; add a dev user at runtime, not in git.
- C11 (DISABLE_LOGIN_FORM) and C12 (Let's Encrypt) are not included.

Grafana forced SSO (C11):

- Supported profile:
  `docker compose -f docker-compose.yml -f docker-compose.dex.yml -f
  docker-compose.grafana-sso.yml up -d`.
- The login form is hidden (`DISABLE_LOGIN_FORM=true`) and
  `AUTO_LOGIN=true`; `ALLOW_SIGN_UP=false`.
- Break-glass: if Dex is down, start only `base` (+ secret files), without
  `sso.yml`, to regain password login.
- Don't combine with C8 (oauth2-proxy) in the same profile.
- C12 (Let's Encrypt) is out of scope.

Grafana public edge / ACME (C12):

- C7 = dev loopback (`127.0.0.1:8443`), ACME disabled.
- C12 = public: `docker compose -f docker-compose.yml -f
  docker-compose.grafana-edge-public.yml up -d`.
- Grafana has no host port; users reach it only via `:443`.
- Requires DNS A/AAAA pointing at the host and open `80`/`443`; firewall is
  the operator's responsibility.
- Don't run C7 and C12 in the same `up` (two Caddy profiles).
- CI interpolates only — it never requests a Let's Encrypt certificate.

Run modes (orchestrator):

- `--once` — single pass, no metrics server, exits:
  `python -m orchestration.sentinel_v5 --once --query "Analyze BTC" --symbol BTCUSDT --timeframe SWING`
- daemon (no `--once`) — starts the `:9191` metrics server and loops every
  `KARL_SYNC_INTERVAL` (default 10s) until stopped.

## Backups

- Postgres backup is **out of compose** until a real `WALG_S3_PREFIX` and an
  encryption key are provided (Path B). Comment-only S3 / `WALG_LIBSODIUM_KEY`
  in `deploy/wal-g/wal-g.env.example` is **not a backup**.
- To enable: `cp deploy/wal-g/wal-g.env.example deploy/wal-g/wal-g.env`
  (gitignored) and set `WALG_S3_PREFIX` + a libsodium key file; then run
  `deploy/wal-g/backup.sh full`. A pinned wal-g image/digest is a follow-up.
- Not backed up: `grafana_data`, `redis_data`, `prom_data` volumes.
- `backup.sh full` ≠ verified restore — a restore drill is still pending.

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
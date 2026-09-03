# Grafana secret files (Compose secrets)

Create exactly these two files in this directory. They are gitignored and must
**never** be committed.

- `grafana_admin_password` — Grafana admin password (one value, no newline).
- `grafana_secret_key` — Grafana signing secret key (one value, no newline).

Both files must be mode `0600`:

```bash
chmod 600 grafana_admin_password grafana_secret_key
```

The base compose mounts them into the container at
`/run/secrets/grafana_admin_password` and `/run/secrets/grafana_secret_key`
and exposes them to Grafana via the `__FILE` env vars
(`GF_SECURITY_ADMIN_PASSWORD__FILE`, `GF_SECURITY_SECRET_KEY__FILE`).

# Grafana secret files (Compose secrets)

Create exactly these two files in this directory. They are gitignored and must
**never** be committed (and never commit their contents).

- `grafana_admin_password` — Grafana admin password (one value, no newline).
- `grafana_secret_key` — Grafana signing secret key (one value, no newline).

The base compose mounts them into the container at
`/run/secrets/grafana_admin_password` and `/run/secrets/grafana_secret_key`
and exposes them to Grafana via the `__FILE` env vars
(`GF_SECURITY_ADMIN_PASSWORD__FILE`, `GF_SECURITY_SECRET_KEY__FILE`).

## File permissions (uid 472)

The Grafana process inside the container runs as **uid 472**, so it must be
able to read the bind-mounted files. A host `chmod 600` owned by *your* user
produces `run.sh: line N: /run/secrets/grafana_secret_key: Permission denied`.

- **dev (rootless Docker / Pop!_OS):** `chmod 644` on both files.
- **prod (preferred):** make the files readable by uid 472:
  `chown 472:472 grafana_admin_password grafana_secret_key && chmod 440`.
  On rootless Docker, `chown 472` is unreliable — verify, otherwise use `644`.

```bash
printf 'YOUR_PASSWORD'   > grafana_admin_password
printf 'YOUR_SECRET_KEY' > grafana_secret_key
# dev (rootless Docker):
chmod 644 grafana_admin_password grafana_secret_key
# or prod (uid 472):
chown 472:472 grafana_admin_password grafana_secret_key && chmod 440
```

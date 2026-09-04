#!/usr/bin/env bash
# Reproducible base-stack smoke helper (postgres + redis + app + grafana + prometheus).
#
# Default: check env/files, run `docker compose config --quiet`, and print the
# `up` command — it does NOT start containers (so it can't disturb a live stack).
#   --apply   additionally run `docker compose up -d`.
#
# Deterministic: no external network. No hardcoded passwords.

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-deploy/docker/docker-compose.yml}"
SECRETS_DIR="deploy/docker/secrets"

APPLY=0
if [ "${1:-}" = "--apply" ]; then
  APPLY=1
fi

missing=0

# Required env (${VAR:?} in the base compose).
for v in DATABASE_URL POSTGRES_PASSWORD GF_SECURITY_ADMIN_USER GF_SERVER_ROOT_URL; do
  if [ -z "${!v:-}" ]; then
    echo "ERROR: required env ${v} is not set" >&2
    missing=1
  fi
done

# Required secret files.
for f in grafana_admin_password grafana_secret_key; do
  if [ ! -s "$SECRETS_DIR/$f" ]; then
    echo "ERROR: missing/empty secret file $SECRETS_DIR/$f" >&2
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  echo "Set the 4 env vars and create the 2 secret files (chmod 644)." >&2
  exit 1
fi

echo "== compose config check =="
docker compose -f "$COMPOSE_FILE" config --quiet
echo "config OK"

echo "== bring up the base stack =="
echo "docker compose -f $COMPOSE_FILE up -d"

if [ "$APPLY" -eq 1 ]; then
  docker compose -f "$COMPOSE_FILE" up -d
  docker compose -f "$COMPOSE_FILE" ps
fi

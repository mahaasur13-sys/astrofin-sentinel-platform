#!/usr/bin/env bash
# CI guard for Grafana auth defaults (Series C1+C2).
#
# Fail closed (exit 1) if any default/unhardened Grafana credential or auth
# toggle reappears under deploy/docker/. `${VAR:?...}` is allowed; any other
# `${VAR:-...}` / `${VAR-...}` default fallback and hardcoded `admin` are not.
#
# Deterministic: pure grep, no network, no docker daemon.

set -euo pipefail

DIR="${1:-deploy/docker}"

# Fixed-string patterns that must never appear in the prod compose.
forbidden=(
  'GF_SECURITY_ADMIN_PASSWORD=admin'
  'GF_SECURITY_ADMIN_USER=admin'
  '${GF_SECURITY_ADMIN_PASSWORD:-'
  '${GF_SECURITY_ADMIN_PASSWORD-'
  '${GF_SECURITY_ADMIN_USER:-'
  '${GF_SECURITY_ADMIN_USER-'
  'admin/admin'
  'GF_AUTH_ANONYMOUS_ENABLED=true'
  'GF_USERS_ALLOW_SIGN_UP=true'
)

fail=0
for pat in "${forbidden[@]}"; do
  if grep -rnF -- "$pat" "$DIR" 2>/dev/null; then
    echo "::error:: forbidden Grafana default pattern: ${pat}" >&2
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "Grafana auth guard FAILED" >&2
  exit 1
fi

echo "Grafana auth guard OK"

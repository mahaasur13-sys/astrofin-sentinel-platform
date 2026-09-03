#!/usr/bin/env bash
# CI guard for Grafana auth defaults (Series C1+C2+C3).
#
# Fail closed (exit 1) if any default/unhardened Grafana credential, auth
# toggle, default signing key, or public :3000 publish reappears under
# deploy/docker/. `${VAR:?...}` is allowed; any other `${VAR:-...}` /
# `${VAR-...}` default fallback and hardcoded literals are not.
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
  'GF_SECURITY_SECRET_KEY=SW2YcwTIb9zpOOhoPsMm'
  '${GF_SECURITY_SECRET_KEY:-'
  '${GF_SECURITY_SECRET_KEY-'
)

fail=0

for pat in "${forbidden[@]}"; do
  if grep -rnF -- "$pat" "$DIR" 2>/dev/null; then
    echo "::error:: forbidden Grafana default pattern: ${pat}" >&2
    fail=1
  fi
done

# Any literal (non ${VAR}) GF_SECURITY_SECRET_KEY value = hardcoded key/stub.
if grep -rnE 'GF_SECURITY_SECRET_KEY=[^$]' "$DIR" 2>/dev/null; then
  echo "::error:: forbidden hardcoded GF_SECURITY_SECRET_KEY literal" >&2
  fail=1
fi

# Grafana :3000 must not be published on 0.0.0.0 / bare (127.0.0.1 only, or absent).
if grep -rnF '3000:3000' "$DIR" 2>/dev/null | grep -vF '127.0.0.1:3000:3000'; then
  echo "::error:: forbidden Grafana port publish (must be 127.0.0.1 or absent)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "Grafana auth guard FAILED" >&2
  exit 1
fi

echo "Grafana auth guard OK"

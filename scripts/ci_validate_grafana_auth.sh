#!/usr/bin/env bash
# CI guard for Grafana auth defaults (Series C1+C2+C3+C4+C5).
#
# Fail closed (exit 1) if any default/unhardened Grafana credential, auth
# toggle, default signing key, public :3000 publish, permissive cookie/embedding
# setting, ROOT_URL fallback, or TLS misconfiguration reappears under
# deploy/docker/. `${VAR:?...}` is allowed; any other `${VAR:-...}` /
# `${VAR-...}` fallback and hardcoded literals are not. COOKIE_SECURE=false is
# allowed in the BASE compose (HTTP loopback) but not in the TLS overlay.
#
# Deterministic: pure grep + git ls-files, no network, no docker daemon.

set -euo pipefail

DIR="${1:-deploy/docker}"
OVERLAY="$DIR/docker-compose.grafana-tls.yml"

# Fixed-string patterns that must never appear in the prod compose tree.
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
  '${GF_SERVER_ROOT_URL:-'
  '${GF_SERVER_ROOT_URL-'
  'GF_SECURITY_ALLOW_EMBEDDING=true'
  'GF_USERS_ALLOW_ORG_CREATE=true'
  'GF_SECURITY_COOKIE_SAMESITE=none'
  '${GF_SERVER_CERT_FILE:-'
  '${GF_SERVER_CERT_FILE-'
  '${GF_SERVER_CERT_KEY:-'
  '${GF_SERVER_CERT_KEY-'
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

# TLS overlay (if present) must be strictly HTTPS + secure cookies + fail-closed.
if [ -f "$OVERLAY" ]; then
  if grep -nF 'GF_SECURITY_COOKIE_SECURE=false' "$OVERLAY" 2>/dev/null; then
    echo "::error:: TLS overlay must set GF_SECURITY_COOKIE_SECURE=true" >&2
    fail=1
  fi
  if ! grep -qE 'GF_SERVER_PROTOCOL[=:][[:space:]]*"?https' "$OVERLAY" 2>/dev/null; then
    echo "::error:: TLS overlay must set GF_SERVER_PROTOCOL=https" >&2
    fail=1
  fi
  if grep -nF 'GF_SERVER_ROOT_URL=http://' "$OVERLAY" 2>/dev/null; then
    echo "::error:: TLS overlay GF_SERVER_ROOT_URL must be https://" >&2
    fail=1
  fi
fi

# No cert/key material may be committed under deploy/docker/.
if git ls-files -- "$DIR" 2>/dev/null | grep -E '\.(pem|key|crt)$'; then
  echo "::error:: cert/key files must not be committed to git" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "Grafana auth guard FAILED" >&2
  exit 1
fi

echo "Grafana auth guard OK"

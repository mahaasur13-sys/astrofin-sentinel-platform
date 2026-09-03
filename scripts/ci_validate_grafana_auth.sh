#!/usr/bin/env bash
# CI guard for Grafana auth defaults (Series C1+C2+C3+C4+C5+C6).
#
# Fail closed (exit 1) if any default/unhardened Grafana credential, auth
# toggle, default signing key, public :3000 publish, permissive cookie/embedding
# setting, ROOT_URL fallback, TLS misconfiguration, or OIDC misconfiguration
# reappears under deploy/docker/. `${VAR:?...}` is allowed; any other
# `${VAR:-...}` / `${VAR-...}` fallback and hardcoded literals are not.
# COOKIE_SECURE=false is allowed in the BASE compose (HTTP loopback) but not in
# the TLS overlay. DISABLE_LOGIN_FORM=true is never allowed.
#
# Deterministic: pure grep + git ls-files, no network, no docker daemon.

set -euo pipefail

DIR="${1:-deploy/docker}"
TLS_OVERLAY="$DIR/docker-compose.grafana-tls.yml"
OIDC_OVERLAY="$DIR/docker-compose.grafana-oidc.yml"
EDGE_OVERLAY="$DIR/docker-compose.grafana-edge.yml"

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
  '${GF_AUTH_GENERIC_OAUTH_NAME:-'
  '${GF_AUTH_GENERIC_OAUTH_NAME-'
  '${GF_AUTH_GENERIC_OAUTH_CLIENT_ID:-'
  '${GF_AUTH_GENERIC_OAUTH_CLIENT_ID-'
  '${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET:-'
  '${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET-'
  '${GF_AUTH_GENERIC_OAUTH_AUTH_URL:-'
  '${GF_AUTH_GENERIC_OAUTH_AUTH_URL-'
  '${GF_AUTH_GENERIC_OAUTH_TOKEN_URL:-'
  '${GF_AUTH_GENERIC_OAUTH_TOKEN_URL-'
  '${GF_AUTH_GENERIC_OAUTH_API_URL:-'
  '${GF_AUTH_GENERIC_OAUTH_API_URL-'
  '${GF_AUTH_GENERIC_OAUTH_SCOPES:-'
  '${GF_AUTH_GENERIC_OAUTH_SCOPES-'
  '${DOMAIN:-'
  '${DOMAIN-'
  '${ACME_EMAIL:-'
  '${ACME_EMAIL-'
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

# Ports must not be published on 0.0.0.0 / bare (127.0.0.1 only, or absent).
for p in '3000:3000' '80:80' '443:443'; do
  if grep -rnF "$p" "$DIR" 2>/dev/null | grep -vF '127.0.0.1:'; then
    echo "::error:: forbidden port publish (must be 127.0.0.1 or absent): $p" >&2
    fail=1
  fi
done

# TLS overlay (if present) must be strictly HTTPS + secure cookies + fail-closed.
if [ -f "$TLS_OVERLAY" ]; then
  if grep -nF 'GF_SECURITY_COOKIE_SECURE=false' "$TLS_OVERLAY" 2>/dev/null; then
    echo "::error:: TLS overlay must set GF_SECURITY_COOKIE_SECURE=true" >&2
    fail=1
  fi
  if ! grep -qE 'GF_SERVER_PROTOCOL[=:][[:space:]]*"?https' "$TLS_OVERLAY" 2>/dev/null; then
    echo "::error:: TLS overlay must set GF_SERVER_PROTOCOL=https" >&2
    fail=1
  fi
  if grep -nF 'GF_SERVER_ROOT_URL=http://' "$TLS_OVERLAY" 2>/dev/null; then
    echo "::error:: TLS overlay GF_SERVER_ROOT_URL must be https://" >&2
    fail=1
  fi
fi

# OIDC overlay (if present) must be enabled, fail-closed, no sign-up, keep login form.
if [ -f "$OIDC_OVERLAY" ]; then
  if ! grep -qE 'GF_AUTH_GENERIC_OAUTH_ENABLED[=:][[:space:]]*"?true' "$OIDC_OVERLAY" 2>/dev/null; then
    echo "::error:: OIDC overlay must set GF_AUTH_GENERIC_OAUTH_ENABLED=true" >&2
    fail=1
  fi
  if grep -nF 'GF_AUTH_GENERIC_OAUTH_ALLOW_SIGN_UP=true' "$OIDC_OVERLAY" 2>/dev/null; then
    echo "::error:: OIDC overlay must set GF_AUTH_GENERIC_OAUTH_ALLOW_SIGN_UP=false" >&2
    fail=1
  fi
  if grep -nF 'GF_AUTH_DISABLE_LOGIN_FORM=true' "$OIDC_OVERLAY" 2>/dev/null; then
    echo "::error:: OIDC overlay must keep GF_AUTH_DISABLE_LOGIN_FORM=false" >&2
    fail=1
  fi
  if grep -nE 'GF_AUTH_GENERIC_OAUTH_CLIENT_(SECRET|ID)[=:][[:space:]]*"?(admin|secret|changeme|password)' "$OIDC_OVERLAY" 2>/dev/null; then
    echo "::error:: OIDC client secret/id must not be a stub literal" >&2
    fail=1
  fi
fi

# Edge overlay (if present): grafana must drop its host port (proxy is the edge).
if [ -f "$EDGE_OVERLAY" ]; then
  if ! grep -q 'ports: !reset' "$EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: edge overlay grafana must clear its host port (ports: !reset [])" >&2
    fail=1
  fi
  if grep -nF '0.0.0.0' "$EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: edge overlay must not publish on 0.0.0.0" >&2
    fail=1
  fi
fi

# No literal OIDC client secret anywhere under deploy/docker/ (only ${VAR:?} or
# a your_*_here placeholder is allowed).
if grep -rnE 'GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET=[[:space:]]*"?[^$#]' "$DIR" 2>/dev/null | grep -vE 'your_.*_here'; then
  echo "::error:: OIDC client secret must be \${VAR:?} or a placeholder" >&2
  fail=1
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

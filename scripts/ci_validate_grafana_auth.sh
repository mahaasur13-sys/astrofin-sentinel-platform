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
BASE="$DIR/docker-compose.yml"
TLS_OVERLAY="$DIR/docker-compose.grafana-tls.yml"
OIDC_OVERLAY="$DIR/docker-compose.grafana-oidc.yml"
EDGE_OVERLAY="$DIR/docker-compose.grafana-edge.yml"
OAUTH2_PROXY_OVERLAY="$DIR/docker-compose.grafana-oauth2-proxy.yml"
DEX_OVERLAY="$DIR/docker-compose.dex.yml"
DEX_CONFIG="$DIR/dex/config.yaml"
SSO_OVERLAY="$DIR/docker-compose.grafana-sso.yml"
PUBLIC_EDGE_OVERLAY="$DIR/docker-compose.grafana-edge-public.yml"
C7_CADDYFILE="$DIR/edge/Caddyfile"
PUBLIC_CADDYFILE="$DIR/edge/Caddyfile.public"

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
  '${OAUTH2_PROXY_CLIENT_ID:-'
  '${OAUTH2_PROXY_CLIENT_ID-'
  '${OAUTH2_PROXY_CLIENT_SECRET:-'
  '${OAUTH2_PROXY_CLIENT_SECRET-'
  '${OAUTH2_PROXY_COOKIE_SECRET:-'
  '${OAUTH2_PROXY_COOKIE_SECRET-'
  '${OAUTH2_PROXY_OIDC_ISSUER_URL:-'
  '${OAUTH2_PROXY_OIDC_ISSUER_URL-'
  '${OAUTH2_PROXY_REDIRECT_URL:-'
  '${OAUTH2_PROXY_REDIRECT_URL-'
  '${DEX_GRAFANA_CLIENT_ID:-'
  '${DEX_GRAFANA_CLIENT_ID-'
  '${DEX_GRAFANA_CLIENT_SECRET:-'
  '${DEX_GRAFANA_CLIENT_SECRET-'
  '${DEX_ISSUER:-'
  '${DEX_ISSUER-'
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

# Base compose must not set plaintext Grafana password/secret key (files only).
if grep -nE 'GF_SECURITY_(ADMIN_PASSWORD|SECRET_KEY)=' "$BASE" 2>/dev/null; then
  echo "::error:: base compose must use *_FILE for Grafana password/secret key" >&2
  fail=1
fi

# Ports must not be published on 0.0.0.0 / bare (127.0.0.1 only, or absent).
# The C12 public edge overlay is the exception (its bare 80:80/443:443 is the contract).
for p in '3000:3000' '80:80' '443:443'; do
  if grep -rnF "$p" "$DIR" --exclude=docker-compose.grafana-edge-public.yml 2>/dev/null | grep -vF '127.0.0.1:'; then
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

# C7 loopback Caddyfile must not enable public ACME.
if [ -f "$C7_CADDYFILE" ]; then
  if grep -nE '^[[:space:]]*(email|tls)[[:space:]]+\{\$ACME_EMAIL\}' "$C7_CADDYFILE" 2>/dev/null; then
    echo "::error:: C7 Caddyfile must not enable public ACME" >&2
    fail=1
  fi
fi

# Public edge overlay (C12): must publish 80/443 publicly, grafana no host port.
if [ -f "$PUBLIC_EDGE_OVERLAY" ]; then
  if ! grep -qF '80:80' "$PUBLIC_EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: public edge overlay must publish 80:80" >&2
    fail=1
  fi
  if ! grep -qF '443:443' "$PUBLIC_EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: public edge overlay must publish 443:443" >&2
    fail=1
  fi
  if ! grep -q 'ports: !reset' "$PUBLIC_EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: public edge overlay grafana must clear its host port" >&2
    fail=1
  fi
  if grep -nF ':latest' "$PUBLIC_EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: public edge caddy image must be pinned" >&2
    fail=1
  fi
  if grep -nE '127\.0\.0\.1:(80|443):' "$PUBLIC_EDGE_OVERLAY" 2>/dev/null; then
    echo "::error:: public edge overlay must publish 80/443 publicly (no 127.0.0.1)" >&2
    fail=1
  fi
fi

# Public Caddyfile must use ACME tls and proxy to grafana.
if [ -f "$PUBLIC_CADDYFILE" ]; then
  if ! grep -qE '\btls\b' "$PUBLIC_CADDYFILE" 2>/dev/null; then
    echo "::error:: Caddyfile.public must have a tls directive" >&2
    fail=1
  fi
  if ! grep -qF 'reverse_proxy grafana:3000' "$PUBLIC_CADDYFILE" 2>/dev/null; then
    echo "::error:: Caddyfile.public must proxy to grafana:3000" >&2
    fail=1
  fi
fi

# oauth2-proxy overlay (if present): loopback-only, pinned image, no stub secrets.
if [ -f "$OAUTH2_PROXY_OVERLAY" ]; then
  if grep -nF ':latest' "$OAUTH2_PROXY_OVERLAY" 2>/dev/null; then
    echo "::error:: oauth2-proxy image must be pinned (no :latest)" >&2
    fail=1
  fi
  if grep -nE '0\.0\.0\.0:[0-9]+:[0-9]+' "$OAUTH2_PROXY_OVERLAY" 2>/dev/null; then
    echo "::error:: oauth2-proxy must not publish on 0.0.0.0" >&2
    fail=1
  fi
  if grep -nE 'OAUTH2_PROXY_(CLIENT_SECRET|COOKIE_SECRET)[=:][[:space:]]*"?(admin|changeme|secret|password)' "$OAUTH2_PROXY_OVERLAY" 2>/dev/null; then
    echo "::error:: oauth2-proxy secret must not be a stub literal" >&2
    fail=1
  fi
fi

# Dex overlay (if present): pinned image, loopback-only host publish.
if [ -f "$DEX_OVERLAY" ]; then
  if grep -nF ':latest' "$DEX_OVERLAY" 2>/dev/null; then
    echo "::error:: dex image must be pinned (no :latest)" >&2
    fail=1
  fi
  if grep -nF '0.0.0.0' "$DEX_OVERLAY" 2>/dev/null; then
    echo "::error:: dex must not publish on 0.0.0.0" >&2
    fail=1
  fi
fi

# Dex config (if present) must not contain stub secrets.
if [ -f "$DEX_CONFIG" ]; then
  if grep -nE 'changeme|secret:[[:space:]]*"?(admin|password)' "$DEX_CONFIG" 2>/dev/null; then
    echo "::error:: dex config must not contain stub secrets" >&2
    fail=1
  fi
fi

# Base and C6 (generic OAuth) must keep the password login form.
for f in "$BASE" "$OIDC_OVERLAY"; do
  if [ -f "$f" ] && grep -nF 'GF_AUTH_DISABLE_LOGIN_FORM=true' "$f" 2>/dev/null; then
    echo "::error:: $f must not set GF_AUTH_DISABLE_LOGIN_FORM=true" >&2
    fail=1
  fi
done

# SSO overlay (if present): forced SSO must be fully enabled + fail-closed.
if [ -f "$SSO_OVERLAY" ]; then
  if ! grep -qE 'GF_AUTH_DISABLE_LOGIN_FORM[=:][[:space:]]*"?true' "$SSO_OVERLAY" 2>/dev/null; then
    echo "::error:: SSO overlay must set GF_AUTH_DISABLE_LOGIN_FORM=true" >&2
    fail=1
  fi
  if ! grep -qE 'GF_AUTH_GENERIC_OAUTH_ENABLED[=:][[:space:]]*"?true' "$SSO_OVERLAY" 2>/dev/null; then
    echo "::error:: SSO overlay must set GF_AUTH_GENERIC_OAUTH_ENABLED=true" >&2
    fail=1
  fi
  if ! grep -qE 'GF_AUTH_GENERIC_OAUTH_AUTO_LOGIN[=:][[:space:]]*"?true' "$SSO_OVERLAY" 2>/dev/null; then
    echo "::error:: SSO overlay must set GF_AUTH_GENERIC_OAUTH_AUTO_LOGIN=true" >&2
    fail=1
  fi
  if grep -nF 'GF_AUTH_GENERIC_OAUTH_ALLOW_SIGN_UP=true' "$SSO_OVERLAY" 2>/dev/null; then
    echo "::error:: SSO overlay must set GF_AUTH_GENERIC_OAUTH_ALLOW_SIGN_UP=false" >&2
    fail=1
  fi
  if grep -nE 'GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET[=:][[:space:]]*"?(admin|changeme|secret|password)' "$SSO_OVERLAY" 2>/dev/null; then
    echo "::error:: SSO overlay client secret must not be a stub literal" >&2
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

# Only .gitignore and README.md may be tracked under deploy/docker/secrets/.
if git ls-files -- "$DIR/secrets" 2>/dev/null | grep -vE '(\.gitignore|README\.md)$'; then
  echo "::error:: secret files must not be committed to git" >&2
  fail=1
fi

# No sqlite/db files may be committed under deploy/docker/.
if git ls-files -- "$DIR" 2>/dev/null | grep -E '\.(sqlite|db)$'; then
  echo "::error:: sqlite/db files must not be committed to git" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "Grafana auth guard FAILED" >&2
  exit 1
fi

echo "Grafana auth guard OK"

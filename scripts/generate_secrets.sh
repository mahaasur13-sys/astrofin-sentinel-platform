#!/usr/bin/env bash
# generate_secrets.sh — generate cryptographically strong secrets
# Usage: ./scripts/generate_secrets.sh

set -euo pipefail

# Helper: cryptographically secure random
gen_base64() { openssl rand -base64 "$1" | tr -d "\n"; }
gen_hex()    { openssl rand -hex "$1"; }

OUT=".env.secrets"
[ -f "$OUT" ] && { echo "Error: $OUT exists. Refusing to overwrite."; exit 1; }
umask 077

{
  echo "# Generated $(date -u +%Y-%m-%dT%H:%M:%SZ) — DO NOT COMMIT"
  echo "POSTGRES_PASSWORD=$(gen_base64 32)"
  echo "POSTGRES_REPLICA_PASSWORD=$(gen_base64 32)"
  echo "API_KEY=$(gen_hex 32)"
  echo "JWT_SECRET=$(gen_hex 64)"
  echo "METRICS_API_KEY=$(gen_hex 32)"
  echo "S3_ACCESS_KEY=$(gen_hex 20)"
  echo "S3_SECRET_KEY=$(gen_base64 40)"
  echo "OPENAI_API_KEY=sk-REPLACE_ME"
  echo "ANTHROPIC_API_KEY=sk-ant-REPLACE_ME"
  echo "GRAFANA_ADMIN_PASSWORD=$(gen_base64 24)"
} > "$OUT"
chmod 600 "$OUT"
echo "Wrote $OUT (mode 600). Fill OPENAI/ANTHROPIC keys manually."

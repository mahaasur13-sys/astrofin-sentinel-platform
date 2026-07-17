#!/usr/bin/env bash
# load_env.sh — load env files in safe precedence order
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_FILE="${1:-.env}"
SECRETS_FILE="${2:-.env.secrets}"
[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE" >&2; exit 1; }
set -a
. "./$ENV_FILE"
[ -f "$SECRETS_FILE" ] && . "./$SECRETS_FILE"
set +a
echo "loaded: $ENV_FILE${SECRETS_FILE:+ + $SECRETS_FILE} ($(env | grep -cE '^[A-Z_]+=') vars)"

#!/usr/bin/env bash
# Generate a self-signed dev certificate for the Grafana TLS overlay.
#
# Output: deploy/docker/certs/grafana.crt + grafana.key (both gitignored).
# SAN: localhost + 127.0.0.1. Validity <= 825 days.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$HERE/../deploy/docker/certs"

mkdir -p "$OUT_DIR"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$OUT_DIR/grafana.key" \
  -out "$OUT_DIR/grafana.crt" \
  -days 825 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Generated:"
echo "  $OUT_DIR/grafana.crt"
echo "  $OUT_DIR/grafana.key"

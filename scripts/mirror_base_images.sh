#!/usr/bin/env bash
# =============================================================================
# mirror_base_images.sh — copy the pinned official base images to GHCR as
# multi-arch indexes (docker buildx imagetools create, NOT docker tag).
#
# Operator-only. NOT run in CI (Docker Hub / GHCR auth is not available there).
#
# Preconditions (avoid Docker Hub 429):
#   docker login docker.io   # authenticated pull limit
#   docker login ghcr.io     # GHCR write
#
# Usage:
#   ./scripts/mirror_base_images.sh            # copy all four
#   ./scripts/mirror_base_images.sh --dry-run  # print source -> dest, no copy
#   ./scripts/mirror_base_images.sh --help
#
# Exit codes:
#   0  all four mirrored as multi-arch indexes (linux/amd64 + >=1 linux/arm*)
#   1  a mirror is not a multi-arch index / missing platform / missing digest
#   2  registry error (429 / denied / network)
# =============================================================================
set -euo pipefail

if [[ "${1:-}" == "--dry-run" || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  DRY_RUN=1
else
  DRY_RUN=0
fi

# SOURCE (official, digest-pinned) | DEST (ghcr.io/mahaasur13-sys/astrofin-<svc>:<tag>)
IMAGES=(
  "postgres:15-alpine@sha256:fe0737ba566a2c5b2a28f34433c0a423261900ec17b9bf7ad115e1aae7e57f1b|ghcr.io/mahaasur13-sys/astrofin-postgres:15-alpine"
  "redis:7-alpine@sha256:ff02b58f971e7d7d156a1267e283fcbbeee91773b6aa36c49dac28ecfe28eadf|ghcr.io/mahaasur13-sys/astrofin-redis:7-alpine"
  "prom/prometheus:v2.54.1@sha256:f6639335d34a77d9d9db382b92eeb7fc00934be8eae81dbc03b31cfe90411a94|ghcr.io/mahaasur13-sys/astrofin-prometheus:v2.54.1"
  "grafana/grafana:11.2.0@sha256:408afb9726de5122b00a2576763a8a57a3c86d5b0eff5305bc994ceb3eb96c3f|ghcr.io/mahaasur13-sys/astrofin-grafana:11.2.0"
)

fail=0

for entry in "${IMAGES[@]}"; do
  SRC="${entry%%|*}"
  DEST="${entry##*|}"
  echo "== ${SRC}"
  echo "   -> ${DEST}"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "   [dry-run] docker buildx imagetools create --tag ${DEST} ${SRC}"
    continue
  fi

  # 1. Copy as an index (multi-arch preserved). Never `docker tag` (amd64-only).
  if ! out="$(docker buildx imagetools create --tag "$DEST" "$SRC" 2>&1)"; then
    if echo "$out" | grep -qiE '429|toomanyrequests|rate limit|denied|unauthorized|403'; then
      echo "   ERROR: registry 429/denied — retry later (see RUNBOOK §Image pins):" >&2
      echo "   ${out}" >&2
      exit 2
    fi
    echo "   ERROR: imagetools create failed:" >&2
    echo "   ${out}" >&2
    exit 2
  fi

  # 2. Inspect DEST: must be a multi-arch index with linux/amd64 + >=1 linux/arm*.
  if ! inspect="$(docker buildx imagetools inspect "$DEST" 2>&1)"; then
    echo "   ERROR: imagetools inspect failed:" >&2
    echo "   ${inspect}" >&2
    exit 2
  fi

  if ! echo "$inspect" | grep -qE 'index\.v1\+json|manifest\.list\.v2\+json'; then
    echo "   ERROR: ${DEST} is not a multi-arch index (no index/manifest.list media type)" >&2
    fail=1
    continue
  fi
  if ! echo "$inspect" | grep -qE 'Platform:[[:space:]]*linux/amd64'; then
    echo "   ERROR: ${DEST} missing linux/amd64" >&2
    fail=1
    continue
  fi
  if ! echo "$inspect" | grep -qE 'Platform:[[:space:]]*linux/arm'; then
    echo "   ERROR: ${DEST} missing linux/arm* (multi-arch lost)" >&2
    fail=1
    continue
  fi

  digest="$(echo "$inspect" | grep -iE '^Digest:' | head -1 | awk '{print $2}')"
  if [[ -z "$digest" || ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    echo "   ERROR: could not extract a valid index digest from ${DEST}" >&2
    fail=1
    continue
  fi
  echo "   OK  index digest: ${digest}"
done

if [[ "$fail" -ne 0 ]]; then
  echo "mirror_base_images FAILED (some images are not multi-arch indexes)" >&2
  exit 1
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "dry-run: no images were copied."
else
  echo "mirror_base_images OK"
fi

#!/usr/bin/env bash
# CI guard: k8s image refs must use the canonical GHCR web image name
# (ghcr.io/mahaasur13-sys/astrofin-sentinel-platform) and must not carry a
# floating :latest.
#
#  1. Fail if any `image:` line in deploy/k8s/** still references the old
#     `astrofin-sentinel-web` image name.
#  2. Fail if any `image:` line uses `:latest` without the documented
#     `# placeholder` marker — the single deployment image is sed-rewritten to
#     ${VERSION} at deploy time (see .github/workflows/deploy.yml), so `:latest`
#     is only ever a placeholder, never a real prod pull.
#
# Scopes to `image:` lines only: the k8s *workload* name `astrofin-sentinel-web`
# (Deployment/Service/Ingress/HPA metadata + selectors) is intentionally unchanged.
# Deterministic: pure grep. No network, no docker, no kubectl.

set -euo pipefail

fail=0

# 1. Old image name must not appear in any image ref.
if grep -rnE 'image:[[:space:]]*[^[:space:]]*astrofin-sentinel-web' deploy/k8s/ 2>/dev/null; then
  echo "::error:: k8s image ref uses old name astrofin-sentinel-web (canonical: astrofin-sentinel-platform)" >&2
  fail=1
fi

# 2. No floating :latest in an image ref, except the documented sed placeholder.
if grep -rnE 'image:[[:space:]]*[^[:space:]]+:latest([[:space:]]|$)' deploy/k8s/ 2>/dev/null \
    | grep -v 'placeholder'; then
  echo "::error:: floating :latest image ref without '# placeholder' marker" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "k8s image name guard FAILED" >&2
  exit 1
fi

echo "k8s image name guard OK"

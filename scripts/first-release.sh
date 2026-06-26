#!/usr/bin/env bash
set -euo pipefail

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing utility: $1" >&2; exit 1; }
}

need git
need gh
need kubectl
need curl

tag="v1.0.0-rc1"
repo="mahaasur13-sys/astrofin-sentinel-platform"
remote="origin"

if git rev-parse "${tag}" >/dev/null 2>&1; then
  echo "Tag ${tag} already exists locally"
else
  git tag -a "${tag}" -m "${tag}"
  echo "Created local tag ${tag}"
fi

git push "${remote}" "${tag}"
echo "Pushed tag ${tag}"

echo "Recent workflow runs:"
gh run list --repo "$repo" --limit 5 || true

echo
latest_url="$(gh api "repos/$repo/actions/runs?per_page=1" --jq '.workflow_runs[0].html_url' 2>/dev/null || true)"
if [[ -n "$latest_url" && "$latest_url" != "null" ]]; then
  echo "Latest workflow run: $latest_url"
fi

staging_url="${STAGING_HEALTHCHECK_URL:-}"
if [[ -n "$staging_url" ]]; then
  echo "Waiting for staging smoke test target: $staging_url"
  curl -fsS "$staging_url" >/dev/null && echo "Staging smoke-test OK"
fi

if gh auth status >/dev/null 2>&1; then
  pr_url="$(gh pr view --repo "$repo" --json url,state --jq '.url' 2>/dev/null || true)"
  if [[ -n "$pr_url" ]]; then
    echo "PR page: $pr_url"
  fi
fi

# CR-2026-07-11 — KI-128: Workflow triggers for feat/** branches

## Problem

PR-based CI workflows (ci.security, quality-gate, compose-check) are
configured to trigger only on `master` and `develop` branches. As a result,
feature branches like `feat/err-01-improve-error-handling` do not run the
Quality Gate or security jobs on their pull requests.

This **blocks PR #176** (KI-127 — error handling standardization). The
Quality Gate job does not run, so the PR cannot be merged.

## Solution

Add `'feat/**'` and `'fix/**'` glob patterns to the `branches:` list of the
following workflows (for `pull_request` triggers; `push` on `feat/**` is
intentionally NOT added to keep noise low):

- `.github/workflows/ci.security.yml` — `pull_request.branches`
- `.github/workflows/quality-gate.yml` — `pull_request.branches`
- `.github/workflows/compose-check.yml` — both `push.branches` and
  `pull_request.branches`

`ci.yml` already supports the pattern (it was updated earlier).

## Patch

The patch is attached: `ki-128-workflow-triggers.patch`.

Apply locally:
```bash
git apply ki-128-workflow-triggers.patch
```

## Acceptance criteria

- [ ] PR opened: `fix/ki-128-workflow-triggers` → `master`
- [ ] Workflow file changes are visible in the PR
- [ ] Once merged, Quality Gate fires on PR #176
- [ ] PR #176 reaches green and is merged

## Manual application required

> ⚠ The current OAuth token does NOT have the `workflow` scope, so the
> patch cannot be pushed via `gh` or `git push` from this sandbox.
>
> Apply the patch either:
> 1. Locally with a PAT that has `workflow` scope, then push, OR
> 2. In the GitHub web UI: open the branch, edit the three workflow files
>    by hand, and open a PR.

## Risk

Low. Branch-filter widening only — no logic changes.

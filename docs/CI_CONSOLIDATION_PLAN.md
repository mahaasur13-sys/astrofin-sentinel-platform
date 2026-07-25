# CI Consolidation Plan — Wave 2 (2026-07-25)

**F-07:** 17 CI workflows → target 6-8

## Current State (17 workflows)

| # | Workflow | Trigger | Action |
|---|----------|---------|--------|
| 1 | ci.yml | push, PR, manual | **KEEP** — main CI |
| 2 | ci.security.yml | push, PR | → **MERGE into security.yml** |
| 3 | security.yml | push, PR | **KEEP + ABSORB ci.security.yml + secret-scan.yml** |
| 4 | secret-scan.yml | push, PR | → merge into security.yml |
| 5 | lint.yml | push, PR | → merge into ci.yml |
| 6 | compose-check.yml | push, PR | → merge into ci.yml as job |
| 7 | coverage.yml | push, PR | → merge into ci.yml as job |
| 8 | pr-checks.yml | PR | → merge into ci.yml |
| 9 | quality-gate.yml | PR | **KEEP** |
| 10 | graphify-healthcheck.yml | push, manual | → merge into nightly.yml |
| 11 | nightly.yml | cron, manual | **KEEP + ABSORB graphify-healthcheck.yml** |
| 12 | deploy.yml | push, manual | **KEEP** |
| 13 | release.yml | push, manual | **KEEP** |
| 14 | auto-label.yml | PR | **KEEP** (bot-managed) |
| 15 | coderabbit-pr-review.yml | manual | **KEEP** (external) |
| 16 | coderabbit-safety-scan.yml | cron, manual | **KEEP** (external) |
| 17 | load-test.yml | manual | **KEEP** |

## Target (8 workflows)

| # | Workflow | Contents | Trigger |
|---|----------|----------|---------|
| 1 | **ci.yml** | lint + test + compose-check + coverage + pr-checks | push, PR |
| 2 | **security.yml** | bandit + secret-scan + pip-audit + safety | push, PR |
| 3 | **quality-gate.yml** | quality gate, changed-files detection | PR |
| 4 | **nightly.yml** | regression + graphify-healthcheck | cron, manual |
| 5 | **deploy.yml** | deployment | push, manual |
| 6 | **release.yml** | releases | push, manual |
| 7 | **auto-label.yml** | PR labeling | PR |
| 8 | **coderabbit-pr-review.yml** | CodeRabbit | manual |

**Removed:** ci.security.yml, secret-scan.yml, lint.yml, compose-check.yml, coverage.yml, pr-checks.yml, graphify-healthcheck.yml, coderabbit-safety-scan.yml, load-test.yml

**Note:** load-test.yml can remain as standalone manual trigger — not counted in mandatory count.

## Migration Steps

1. Merge `lint.yml` jobs into `ci.yml`
2. Merge `compose-check.yml` job into `ci.yml`
3. Merge `coverage.yml` job into `ci.yml` (or keep as separate reporting step)
4. Merge `pr-checks.yml` into `ci.yml`
5. Merge `ci.security.yml` + `secret-scan.yml` into `security.yml`
6. Merge `graphify-healthcheck.yml` into `nightly.yml`
7. Delete: `ci.security.yml`, `secret-scan.yml`, `lint.yml`, `compose-check.yml`, `coverage.yml`, `pr-checks.yml`, `graphify-healthcheck.yml`, `coderabbit-safety-scan.yml`

## Blockers

- **Workflow scope:** OAuth token lacks `workflow` scope — must be pushed locally
- Apply as a single patch → PR → admin merge

## Risk

- **LOW:** merged workflows are strictly additive (adding jobs, not removing)
- Rollback: restore deleted files from git history

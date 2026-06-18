# Branch Protection -- AstroFin Sentinel V5

This document describes the required branch protection rules for master and develop.

## Required Status Checks (must pass before merge)

The following jobs are REQUIRED -- a red status blocks merging:

1. **architecture-lint** -- runs scripts/architecture_linter.py (R1-R9).
2. **security-scan** -- runs detect-secrets, Bandit, validate_docker_security.
3. **validate-agents** -- runs scripts/validate_agent.py on changed agents.
4. **registry-check** -- validates AGENT_AGENTS coverage.
5. **test** -- runs pytest with coverage on agents/ and core/.

## Required Settings

In GitHub Settings -> Branches -> Branch protection rules -> master / develop:

[x] Require a pull request before merging
    [x] Require approvals: 1
    [x] Dismiss stale pull request approvals when new commits are pushed
[x] Require status checks to pass before merging
    [x] Require branches to be up to date before merging
    Required checks: architecture-lint, security-scan, validate-agents,
                     registry-check, test, blackrock-tests
[x] Require conversation resolution before merging
[x] Require linear history
[x] Do not allow force pushes
[x] Do not allow deletions

## How to Configure

1. Open GitHub repository page.
2. Go to Settings -> Branches.
3. Click "Add rule" or edit existing rule for "master" (repeat for "develop").
4. Apply the settings above.
5. Save changes.

## Why These Settings?

- **architecture-lint** is the primary defense against architectural drift.
  A passing architecture lint means new code follows our 9 hard rules.
- **security-scan** blocks commits with hardcoded secrets or P0 security
  issues.
- **validate-agents** ensures every new agent has tests, an @require_ephemeris
  decorator, an async run() method, and AGENT_AGENTS registration.
- **test** ensures unit and integration tests pass.
- **blackrock-tests** enforces the six required test functions for every agent.

## How to Add an Exemption

If a check fails for a known, documented reason, add a KI-NNN entry to
docs/KNOWN_ISSUES.md. The architecture linter and other tools honour
the list of affected paths in that file.

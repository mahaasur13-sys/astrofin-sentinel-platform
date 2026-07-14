# Security Policy

> Reporting vulnerabilities, supported versions, and the disclosure / fix
> process for the `astrofin-sentinel-platform` repository.

## Supported versions

| Version | Status | Security fixes |
|---|---|---|
| `master` (unreleased) | ✅ Active development | Yes |
| Tagged releases `v1.x` after GA | ✅ Supported | Yes |
| `v0.x` line (`< v1.0.0`) | ⚠️ Best-effort | Critical only |
| Anything older than the latest two minor tags | ❌ End of life | No |

Only the most recent GA line and the `master` branch receive security
backports. The repo's CI gating rules treat `master` as the only
"live" branch; release tags are cut from `master` via squash-merge
PRs (see `MAINTAINERS.md`).

## Reporting a vulnerability

**Please do not file public GitHub issues for suspected vulnerabilities.**

Use one of the private channels below. Both routes reach the same
on-call (Felix, sole maintainer as of 2026-07):

1. **GitHub private vulnerability disclosure** — preferred.
   Go to the [Security tab](../../security/advisories/new) of this
   repository and open a private draft security advisory. GitHub
   will notify maintainers and let us collaborate on a fix before
   disclosure.
2. **Email** — `security@astrofin-sentinel.local` (placeholder, replace
   with a monitored alias before GA; for now route to Felix's
   registered contact in `MAINTAINERS.md`).

Please include:

- A clear description of the issue and its impact.
- Steps to reproduce / a minimal PoC.
- Affected component(s) (`core/`, `agents/`, `web/`, `deploy/`, CI).
- Whether the issue is exploitable in the default `docker-compose up`
  configuration or only in a hardened prod setup.

## What to expect

| Stage | Target SLA |
|---|---|
| Acknowledgement | 48 hours |
| Triage & severity assignment (CVSS-style) | 5 business days |
| Patch for `Critical` / `High` | 14 days from acknowledgement |
| Patch for `Medium` / `Low` | next minor release (≤ 30 days) |
| Public advisory (CVE when applicable) | at fix release, after coordinated disclosure |

We follow **coordinated disclosure**: we will not publicly disclose a
vulnerability until either a fix is shipped or 90 days have elapsed,
whichever comes first, unless immediate disclosure is required to
prevent active harm.

## Security fix process

1. **Triage** in a private security advisory / tracking issue.
2. **Branch** from `master`: `security/<advisory-id>-<slug>`.
3. **Fix** + regression test. Tests must include a failing case that
   reproduces the vulnerability.
4. **Review** by Felix + an external reviewer (see `MAINTAINERS.md`).
5. **Merge** via squash; tag a patch release.
6. **Advisory** published at release time. Severity, affected
   versions, fixed version, and credit to the reporter (unless
   anonymous).

## Out-of-scope reports

The following are **not** security issues and should be filed as
ordinary bugs:

- General best-practice suggestions without a concrete exploit.
- Rate-limiting on unauthenticated endpoints in a default dev
  `docker-compose` (we ship a dev profile with relaxed limits; the
  prod profile is locked down — see `deploy/prod/`).
- Theoretical issues in third-party LLMs we call via `agents/`.
- Findings that require the attacker to already have admin/root
  inside the trust boundary.

## Security tooling already in this repo

This repository runs the following scanners in CI on every PR and
push to `master`:

- **gitleaks** — secret scanning on every commit and PR.
- **detect-secrets** (`Secret Scan`) — baseline-tracked, fails on
  new high-entropy strings.
- **Bandit** — Python security lint (`Security (Bandit + Docker)`
  CI job).
- **pip-audit + safety** — dependency vulnerability scan.
- **Docker security** — image best-practices check.
- **Architecture Lint (R1–R9)** — enforces placement of
  auth-touching modules (see `docs/adr/0009-unified-jwt-auth.md`).
- **Secret Manager / SOPS** — under construction; tracked in
  `PRODUCTION_BACKLOG.md` and `#129`.

## Related documents

- [`PRIVACY.md`](PRIVACY.md) — what data the platform collects and
  how it is protected.
- [`docs/security/THREAT_MODEL.md`](docs/security/THREAT_MODEL.md) —
  STRIDE-style threat model.
- [`docs/adr/0009-unified-jwt-auth.md`](docs/adr/0009-unified-jwt-auth.md) —
  unified JWT authentication (ADR).
- [`RUNBOOK.md`](RUNBOOK.md) — operational incident response.
- [`MAINTAINERS.md`](MAINTAINERS.md) — who can approve a fix.

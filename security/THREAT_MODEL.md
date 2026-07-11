# Threat Model

> Lightweight STRIDE-style model for `astrofin-sentinel-platform`.
> This is a working document — it gets revisited at every major
> release and on any architectural change in `core/`, `web/`, or
> `agents/`.

## Components in scope

| ID | Component | Notes |
|---|---|---|
| **API** | Dash web UI (`web/app.py`), REST endpoints under `/api/…` | Flask + blueprints, JWT-authenticated |
| **AGENTS** | Multi-agent runtime (`agents/`, `meta_rl/`, `orchestration/`) | Talks to LLM providers + internal DB |
| **DB** | SQLite (dev) / Postgres (prod), `core/history.py`, `migrations/` | Persists agent state, audit log |
| **LLM** | Outbound calls to LLM provider APIs (configured per deployment) | Provider-agnostic; secrets in env |
| **CI** | GitHub Actions workflows under `.github/workflows/` | Runs gitleaks / Bandit / tests / compose-check |
| **SECRETS** | `.env`, `.env.prod.example`, future Vault/SOPS (see #129) | Loaded by app at startup |
| **DEPLOY** | `docker-compose.yml`, `deploy/`, future k8s manifests | Runs the platform |
| **LOG** | structlog → Loki (`deploy/monitoring/`) | Includes the PII scrubber from Phase 3b |

Out of scope for this doc: the user's local machine, the LLM
provider's internal security, the GitHub platform itself.

## STRIDE table

| ID | Threat | Component | Mitigation already in place | Residual risk |
|---|---|---|---|---|
| **S1** | Spoofed API caller | API | JWT auth (ADR-0009), gitleaks on every commit | None known; rotate `JWT_SECRET` on any suspected leak (RUNBOOK §1) |
| **S2** | Spoofed CI event | CI | GitHub-managed runner trust model; workflows pinned to repo | A compromised PAT could trigger workflows — see RUNBOOK §3 |
| **T1** | Tampering with stored agent state | DB | Append-only audit log; migrations reviewed | DB compromise = data compromise; mitigated by backups (WAL-G) + least-privilege role |
| **T2** | Tampering with code in flight | DEPLOY | Image digests pinned in `docker-compose.yml`; no `:latest` tags | Operator-level supply chain risk remains (use SLSA/Cosign — tracked #129) |
| **T3** | Tampering with logs | LOG | Loki append-only on the configured backend | Local-disk logs are world-readable by default — restrict with proper file mode |
| **R1** | Repudiation of admin actions | API / AGENTS | Audit log table; structured logs with request id | If logs are deleted, no proof — keep retention ≥ 365 days (PRIVACY) |
| **R2** | Repudiation of CI approval | CI | Required reviewers in branch protection (when enabled) | Currently branch protection is off on `master` — see RUNBOOK |
| **I1** | Disclosure of secrets via logs | LOG | **PII scrubber** (Phase 3b, PR #133); `gitleaks` baseline | Test data with synthetic secrets could still leak if a developer disables scrubber — unit tests guard this |
| **I2** | Disclosure of PII via API | API | JWT scopes; no PII in default responses | If endpoints return user-supplied content, content may contain PII — documented in `PRIVACY.md` |
| **I3** | Disclosure via error pages | API | Flask debug mode off in prod (`Dockerfile`); generic 500s | Stack traces still emit to structured logs — scrubber covers those |
| **D1** | DoS via heavy LLM calls | AGENTS | Per-request timeout; rate limit on inbound API | Provider-side rate limits may still cause cascading failures — circuit breaker planned |
| **D2** | DoS via large payload | API | Flask `MAX_CONTENT_LENGTH` set | DB writes can still be slow; pagination defaults in place |
| **D3** | DoS via CI abuse | CI | GitHub-hosted runners; concurrency limits | Self-hosted runner risk if added later |
| **E1** | Elevation of privilege via `core/auth.py` | API | Static `API_KEY` env removed in favor of JWT (ADR-0009) | A second reviewer is still required for auth changes — see MAINTAINERS |
| **E2** | Elevation via CI workflow write | CI | `secrets.GITHUB_TOKEN` scoped per workflow | Workflows that need extra scopes are reviewed by Felix + external reviewer |

## Mitigations we are *not* there yet (see `PRODUCTION_BACKLOG.md`)

- **WAL-G / S3 backup automation** for Postgres (#129).
- **HashiCorp Vault / SOPS** for runtime secret management (#129).
- **pgvector** + **halfvec** for embedding storage at scale (#129).
- **SLSA Level 3 + Cosign image signing** (#129).
- **PagerDuty on-call rotation** (#129 — currently Felix alone).
- **PII detection beyond regex** (e.g. Microsoft Presidio) for
  higher recall on real-world PII.

## Review schedule

- Every minor release → re-review this file.
- Every change under `core/auth*`, `web/auth*`, or any workflow in
  `.github/` → mandatory STRIDE re-walk in the PR description.
- Every new external dependency → append to the *Out-of-scope
  services* list in `PRIVACY.md` if it receives user data.

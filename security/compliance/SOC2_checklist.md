# SOC 2 — Type II checklist (placeholder)

> **Status (2026-07): this project does NOT currently pass SOC 2.**
> This file is a planning artifact, not an attestation. It tracks
> which Trust Service Criteria we have, which we partially have,
> and which we are explicitly deferring.

A formal SOC 2 Type II audit requires an external auditor and a
willingness to maintain the controls in steady state for 6–12
months. We are not ready for that. This checklist exists so the
gap is visible and can be re-evaluated at any point.

## Trust Service Criteria — coverage map

### CC1 — Control environment

| Criterion | Status | Notes |
|---|---|---|
| Code of conduct | ⚠️ Partial | `CONTRIBUTING.md` exists; no formal Code of Conduct yet |
| Org structure & responsibilities | ✅ | `MAINTAINERS.md` |
| Background checks | ❌ | Single maintainer; not applicable yet |
| Onboarding / offboarding | ❌ | N/A for a single maintainer; documented in `MAINTAINERS.md` when a 2nd is hired |

### CC2 — Communication & information

| Criterion | Status | Notes |
|---|---|---|
| Internal comms | ⚠️ Partial | Issue tracker + ADRs |
| External comms | ✅ | `SECURITY.md`, `PRIVACY.md`, `README.md` |
| Incident communication | ⚠️ Partial | `RUNBOOK.md` covers ops; no public status page |

### CC3 — Risk assessment

| Criterion | Status | Notes |
|---|---|---|
| Risk register | ⚠️ Partial | `PRODUCTION_BACKLOG.md` + `THREAT_MODEL.md` |
| Risk treatment plan | ⚠️ Partial | Same docs, no formal SLT sign-off |
| Vendor risk | ❌ | LLM provider contracts not in scope here |

### CC4 — Monitoring activities

| Criterion | Status | Notes |
|---|---|---|
| Continuous control monitoring | ⚠️ Partial | CI runs Bandit, gitleaks, pip-audit, Architecture Lint |
| Internal audit | ❌ | Not started |

### CC5 — Control activities

| Criterion | Status | Notes |
|---|---|---|
| Documented policies | ✅ | `SECURITY.md`, `PRIVACY.md`, `MAINTAINERS.md`, `RUNBOOK.md`, `SLO.md` |
| Segregation of duties | ❌ | Single maintainer; requires a 2nd before SOC 2 |

### CC6 — Logical & physical access

| Criterion | Status | Notes |
|---|---|---|
| Access provisioning | ⚠️ Partial | GitHub team membership; no formal review cadence |
| Auth (SSO / MFA) | ⚠️ Partial | GitHub-side MFA; platform-side JWT (ADR-0009) |
| Secrets management | ❌ | Vault/SOPS planned (#129); today: `.env` files only |
| Key management & rotation | ⚠️ Partial | `JWT_SECRET` rotation procedure is in `RUNBOOK.md`; not exercised |
| Physical access | ➖ | N/A — no on-prem infra; cloud-provider SOC 2 inherited |

### CC7 — System operations

| Criterion | Status | Notes |
|---|---|---|
| Change management | ✅ | PRs + review + squash-merge to `master` |
| Deploy automation | ⚠️ Partial | `docker-compose` is the only first-class path; no canary/blue-green yet |
| Backup & restore | ⚠️ Partial | `RUNBOOK.md` has the manual procedure; WAL-G automation is #129 |
| Monitoring & alerting | ✅ | Prometheus + alert rules (Phase 3a, PR #132); Loki for logs |
| Incident response | ⚠️ Partial | `RUNBOOK.md` exists; no PagerDuty rotation |

### CC8 — Change management

| Criterion | Status | Notes |
|---|---|---|
| Pre-prod testing | ✅ | CI on every PR; tests + coverage gate (currently relaxed) |
| Rollback plan | ⚠️ Partial | `git revert`; no automated rollback on prod yet |
| Release tagging | ⚠️ Partial | Manual tags; no `release-please` yet |

### CC9 — Risk mitigation

| Criterion | Status | Notes |
|---|---|---|
| Business continuity | ❌ | Single-region deploy; multi-region is #129 |
| Disaster recovery | ⚠️ Partial | `RUNBOOK.md` describes a manual restore from S3 backup; not exercised |

## What we have to do before we can even *start* a SOC 2 audit

1. **Add a second maintainer** and a third-party reviewer rota
   (currently Felix + CodeRabbit + ad-hoc external).
2. **Replace the in-repo `.env` with a real secret manager**
   (Vault or SOPS — #129).
3. **Automate backups** and exercise restore quarterly.
4. **Add a status page** and a real on-call rotation.
5. **Turn on branch protection** on `master` with required
   reviewers + required CI checks.
6. **Run the system in production for ≥ 6 months** with the
   controls above stable, so the auditor has a window to sample.
7. **Pick an auditor** (Vanta / Drata / Tugboat Logic can
   self-asses; a Big-4 firm is required for an opinion).

## What we are explicitly *not* doing yet

- We are not claiming SOC 2 readiness. This file is a *gap
  inventory*, not a marketing claim.
- We are not pursuing ISO 27001 in parallel; it depends on the
  same prerequisites and is a larger investment.
- We are not pursuing HIPAA / PCI DSS — the platform does not
  intentionally process PHI or card data.

## See also

- [`SECURITY.md`](../../SECURITY.md)
- [`PRIVACY.md`](../../PRIVACY.md)
- [`docs/security/THREAT_MODEL.md`](../THREAT_MODEL.md)
- [`RUNBOOK.md`](../../RUNBOOK.md)
- [`PRODUCTION_BACKLOG.md`](../../PRODUCTION_BACKLOG.md) — gaps #129

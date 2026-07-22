# Threat Model (STRIDE) — AstroFin Sentinel

> Status: v1.2.0 documentation track · Owner: Security WG · Last review: 2026-07-08

This document classifies plausible threats to the AstroFin Sentinel platform using the
STRIDE model. Each row identifies the affected component, the current mitigation,
and the residual risk after that mitigation is applied. It is the single source of
truth referenced by the security review checklist and by future hardening work.

Scope:

- Identity & authentication (JWT-based auth on `/api/*`)
- API surface exposed by the web dashboard
- Decision audit trail (`DecisionRecord`) and structured logging
- Secrets handling (SOPS — tracked in #94)
- Rate limiting and DoS posture
- Authorization roles (admin / user) in JWT claims

Out of scope: penetration testing, GDPR / compliance documentation, implementation
of new mitigations.

## STRIDE table

| Threat                | Component               | Mitigation                                                                 | Residual Risk |
|-----------------------|-------------------------|----------------------------------------------------------------------------|---------------|
| Spoofing              | JWT Auth (`/api/*`)     | RS256 signature, issuer (`iss`) and audience (`aud`) claim validation       | Low           |
| Tampering             | API payloads            | HTTPS in transit, signed JWT, request-id propagation                        | Low           |
| Repudiation           | Audit log               | `DecisionRecord` audit trail persisted to structured log + history DB      | Medium        |
| Information Disclosure| Logs                    | PII scrubber planned (no live redaction yet — see "Known gaps")             | High          |
| Denial of Service     | Rate limiting           | Per-user rate limit middleware, `/livez` and `/readyz` health endpoints    | Medium        |
| Elevation of Privilege| Role-based access (RBAC)| Admin / user roles encoded in JWT claims, role checks on privileged paths  | Low           |

## Known gaps

- **PII scrubber** for `core/logging.py` and the `DecisionRecord` pipeline is
  designed but not yet wired into production log handlers. Until that ships,
  Information Disclosure remains the highest residual risk in the table.
- **DecisionRecord retention** is in-process SQLite (`core/history.db`) and is
  not replicated. A corrupted or tampered local store would not be detected by
  the audit trail alone.
- **Rate limiter** is per-user; per-IP and per-tenant limits are not enforced.

## Related references

- ADR-0001 — JWT-based authentication (master)
- `docs/security/THREAT_MODEL.md` — earlier draft (kept for history)
- `docs/ERRORS.md` — error handling reference (PR #144)
- Issue #94 — SOPS-encrypted secrets
- Issue #98 — rate limit unit tests

## Review cadence

This document is reviewed whenever a new external surface is added (new HTTP
route, new agent capability, new secret source) and at least once per minor
release.

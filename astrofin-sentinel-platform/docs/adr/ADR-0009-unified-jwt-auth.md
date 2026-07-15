# ADR-0009: Unified JWT Authentication (RS256)

- **Status:** Proposed
- **Date:** 2026-07-07
- **Deciders:** Felix (owner), Architecture review
- **Sprint:** Phase 2 — Production-readiness foundations
- **Supersedes:** — (no prior ADR; replaces the de-facto dual-mode status quo)
- **Related:** issue #81, ADR-0002 (common contracts), PR #115 (v1 unification)

> **Note on numbering.** `docs/adr/0007-override-aware-tie-break.md` already
> exists and is unrelated. The next free slot is 0009, which is what we use
> here. The original prompt's "ADR-0007" is preserved as a tracking alias in
> the README index for parity with issue #81.

## Context

The platform currently runs **two authentication backends simultaneously**:

1. **Static API key** — `core/auth.py` reads `os.environ["API_KEY"]` and
   verifies it via `secrets.compare_digest`. Used by:
   - `web/wsgi.py::ab_compare` (`@require_api_key`)
   - `web/wsgi.py::live_enable` (`@require_api_key`)
   - `core/auth.py::fastapi_require_api_key` (FastAPI dependency)
2. **JWT (HS256)** — `web/app.py` already imports JWT machinery and the
   Dash app's session is signed with `JWT_SECRET`. The intention is to use
   JWT for everything, but the rollout is incomplete.

Audit findings (folded into issue #81):

- 3+ references to `API_KEY` still alive in `core/`.
- `agents/*` and `meta_rl/*` mix both styles depending on the call site.
- `.env.prod.example` still documents `API_KEY` as the primary secret.
- No CI guard prevents a regression that re-introduces `API_KEY` references.

This is a security risk: static keys are easy to leak (logs, GH Actions,
shell history), can't be rotated without a redeploy, and don't carry
identity claims (who, which role, what scope).

## Decision

**Adopt RS256 JWT as the only authentication mechanism** for all internal
HTTP services. Keep the static `X-API-Key` path available for **one
release** as a deprecation window, then remove it.

### Token shape

```jsonc
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "sub": "user:felix",            // principal id
  "role": "admin",                  // admin | user | agent
  "scope": ["sessions:read",        // optional fine-grained scopes
            "live:enable"],
  "iss": "astrofin-sentinel",
  "aud": "astrofin-sentinel",
  "iat": 1718000000,
  "exp": 1718086400                 // 24h max
}
```

### Roles

| Role | Capabilities |
|---|---|
| `admin` | Everything. Can rotate secrets, enable live, purge sessions. |
| `user`  | Read sessions, run A/B, run backtests. Cannot enable live. |
| `agent` | Service-to-service only. Limited to `sessions:write`, `beliefs:write`. |

### Issuance

- Admin tokens are issued via a CLI tool (`scripts/issue_jwt.py`, TBD).
- Agent tokens are short-lived (≤ 1h) and minted by a dedicated
  `auth-service` (future work; not in scope here).
- No long-lived tokens. Refresh is a non-goal for v1.0.0.

### Verification

- Single middleware in `core/auth.py::require_jwt(request) → Principal`.
- Flask routes use `@require_jwt`; FastAPI uses `Depends(require_jwt)`.
- Public endpoints (`/health`, `/metrics`, `/data-room/conflicts`)
  remain unauthenticated; the rest require a valid JWT.

## Migration plan

1. **Dual-mode window** (one release, ~2 weeks):
   - Add `core/auth.py::require_jwt` (RS256, key from `JWT_PUBLIC_KEY_PATH`).
   - Keep `require_api_key` for backwards compatibility.
   - Add `Deprecation` HTTP header to responses authenticated by API key.
   - CI guard: a new `ci/lint_auth.py` fails the build if `API_KEY`
     appears in `core/`, `agents/`, `meta_rl/`, `web/`, `orchestration/`
     outside the dual-mode allowlist.
2. **Cutover** (next release):
   - Remove `core/auth.py::require_api_key` and `fastapi_require_api_key`.
   - Remove `API_KEY` from `.env.prod.example` and `check_env.py`.
   - Issue admin JWTs to all operators; rotate `JWT_SECRET` once.
3. **Cleanup**:
   - Drop the deprecation header.
   - Delete the dual-mode allowlist.

## Alternatives considered

- **Stay dual-mode indefinitely** — rejected. Two auth paths is a permanent
  footgun and a SOC2 finding waiting to happen.
- **OAuth2 (Auth0 / Keycloak)** — deferred. Worth doing for v1.1 once we
  have multi-tenant requirements. JWT-only is a strict subset of OAuth2
  and a good stepping stone.
- **mTLS** — rejected for v1.0.0. Excellent security, but operational
  complexity (cert rotation) is not yet justified by user count.

## Consequences

**Positive**
- Per-principal audit trail (`sub`, `role`).
- Short-lived tokens, no static secret in the repo.
- Foundation for fine-grained `scope` checks later.

**Negative / risks**
- RS256 key management is new operational surface: we need a
  documented rotation procedure (RUNBOOK.md §"Secret rotation").
- Existing operators must obtain a JWT before the next deploy.
- A bug in the verifier is a full outage — needs strong CI coverage
  (the `ci/lint_auth.py` guard plus unit tests for happy/sad paths).

**Linked work**
- Issue #81 (JWT migration).
- Issue #127 (RUNBOOK/MAINTAINERS/SLO) — the secret-rotation runbook
  referenced from this ADR lands in the same PR.
- Future: replace HS256 in `web/app.py` with RS256; the deprecation
  window covers that as well.

## Acceptance criteria

- [ ] `core/auth.py::require_jwt` implemented with RS256 + role check.
- [ ] `ci/lint_auth.py` fails on any `API_KEY` reference outside the
      allowlist; allowlist itself is empty in the cutover release.
- [ ] `RUNBOOK.md` documents JWT issuance and key rotation.
- [ ] `web/wsgi.py` and `web/data_room.py` updated to use `@require_jwt`.
- [ ] `.env.prod.example` documents `JWT_PUBLIC_KEY_PATH` (and stops
      recommending `API_KEY`).

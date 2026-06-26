# RBAC Matrix — AstroFin Sentinel Platform

> **Status:** Living document — placeholder / template
> **Owner:** Platform team
> **Last reviewed:** 2026-06-26

This document defines **who** can do **what** on **which** resource. It is currently a
**template** — populate before first production deploy.

---

## 1. Roles

| Role | Definition | Authentication |
|------|------------|----------------|
| **viewer** | Read-only access to dashboard, no trades | GitHub OAuth (Dash) |
| **analyst** | Run backtests, view audit log, no live trading | GitHub OAuth + scope |
| **operator** | Start/stop bots, modify configs (weights, thresholds) | GitHub OAuth + 2FA |
| **trader** | Authorise live trades (broker-side already requires its own auth) | Broker + operator approval |
| **admin** | Manage secrets, users, deploys | GitHub OAuth + hardware key |
| **service-account** | CI / bot accounts (e.g. `coderabbit[bot]`) | GitHub App |

---

## 2. Resource → Role matrix

| Resource | viewer | analyst | operator | trader | admin | service-account |
|----------|:------:|:-------:|:--------:|:------:|:-----:|:---------------:|
| Dash dashboard (read) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `/data-room/conflicts` | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Modify agent weights | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Trigger backtest | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Pause/resume live agent | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Submit live order | ❌ | ❌ | ❌ | ✅* | ✅ | ❌ |
| Read `DecisionRecord` audit log | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Read broker secrets | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Rotate secrets | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Deploy to staging | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Deploy to production | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Manage CI workflows | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (CI only) |
| Open / merge PR | ❌ | ✅ (CODEOWNERS) | ✅ (CODEOWNERS) | ❌ | ✅ | ✅ (CI only) |

`*` Requires dual approval if `>= $10 000` notional (proposed rule — to be ratified).

---

## 3. Authentication flow

```
User ──GitHub OAuth──► Dash (web/app.py)
                          │
                          ▼
                   validate_startup()
                   (core/auth.py)
                          │
                          ▼
                roles = gh.get_user_roles(user)
                          │
                          ▼
                gate(roles, resource)
```

For now, `validate_startup()` performs **environment-level** checks
(env vars present, broker reachable). The per-user RBAC layer is **TODO**
(see §6).

---

## 4. Codeowners (GitHub)

```
# .github/CODEOWNERS — placeholder
/agents/_impl/                 @astrofin-agents-team
/orchestration/                @astrofin-platform-team
/meta_rl/                      @astrofin-platform-team
/web/                          @astrofin-platform-team
/security/                     @astrofin-security-team
/.github/workflows/            @astrofin-platform-team
/docs/SECURITY.md              @astrofin-security-team
```

> **Action item:** replace placeholder teams with real GitHub handles.

---

## 5. Audit

Every state-changing action (deploy, secret rotation, weight change) MUST log
a `DecisionRecord` or equivalent:

```
timestamp, actor, role, resource, action, before_hash, after_hash
```

Audit log location: `audit/YYYY-MM-DD.jsonl` (append-only, gitignored).

---

## 6. Open items

- [ ] Implement per-user RBAC in `core/auth.py` (currently environment-only).
- [ ] Wire Dash login → GitHub OAuth callback.
- [ ] Dual-approval for live trades above the notional threshold.
- [ ] Replace `astrofin-*` team placeholders with real handles.
- [ ] Add CI check that fails if `security/rbac-matrix.md` is missing a row.
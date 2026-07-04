# 👥 Team Roles & Responsibilities — AstroFin Sentinel

> **Status:** ✅ Active (last reviewed 2026-07-04)
> **Owner:** Tech Lead (`@asurdev`)
> **Назначение:** формализация ролей, зон ответственности и ownership матрицы. Решает проблему **bus factor = 1** (R-R02).

---

## 1. 🎯 Назначение

**Team Roles & Responsibilities** — это документ, который:

1. **Формализует кто за что отвечает** в проекте
2. **Закрывает риск bus factor** (R-R02: уход одного разработчика = остановка проекта)
3. **Помогает при онбординге** новых контрибьюторов
4. **Даёт основу для CODEOWNERS** (auto-assign reviewers)
5. **Документирует эскалационные пути** при инцидентах

---

## 2. 🏗️ Структура команды

**Текущий состав:** 1 senior full-stack + 0.5 DevOps + 0.25 Security + 0.25 Docs (1.5 FTE)

**Целевой состав к GA (2026-08-09):** добавить **1 backup maintainer** (закрывает R-R02)

### 2.1 Org chart (текущий)

```
            ┌─────────────────────┐
            │   Tech Lead (asurdev)│
            │   - Architecture     │
            │   - Final decisions  │
            │   - Stakeholder comm │
            └──────────┬──────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
   │ Backend │    │ DevOps  │    │ Security│
   │ (0.5    │    │ (0.5    │    │ (0.25   │
   │  FTE)   │    │  FTE)   │    │  FTE)   │
   └─────────┘    └─────────┘    └─────────┘
        │              │              │
   ┌────▼──────────────▼──────────────▼────┐
   │        Docs / Tech Writer (0.25)       │
   └────────────────────────────────────────┘
```

---

## 3. 👤 Primary Roles (RACI матрица)

### 3.1 Tech Lead (asurdev)

**Scope:** overall architecture, final decisions, stakeholder communication

| Зона | Ответственность | RACI |
|------|-----------------|------|
| Архитектура (R1–R9) | Утверждение всех архитектурных решений | **A** (Accountable) |
| ADR review | Approve ADR-XXXX | **A** |
| Release management | Tag, release notes, GA sign-off | **R** (Responsible) + **A** |
| Stakeholder updates | Еженедельный 1-pager | **R** |
| Risk register | Quarterly review | **A** |
| On-call (primary) | 24/7 first responder | **R** |
| Bus factor mitigation | Найти backup maintainer (target: end of W5) | **R** + **A** |
| Bus factor mitigation | Провести pair-programming | **R** |

**Time commitment:** 100% (full-time)

**Required skills:** Python (senior), distributed systems, trading/ML background, SRE basics

**Backup (during vacation):** см. §4.2

---

### 3.2 Senior Backend (часто = Tech Lead, но могут быть +1)

**Scope:** Python core, agents, orchestration, API

| Зона | Ответственность | RACI |
|------|-----------------|------|
| Core (`core/`) | Trading logic, RAG, ephemeris | **R** |
| Orchestration (`orchestration/`) | Sentinel v5, agent council | **R** |
| Web (`web/`) | FastAPI endpoints, dashboards | **R** |
| Tests (`tests/`) | pytest, coverage | **R** |
| Code review | Review PRs в `core/`, `orchestration/`, `web/` | **R** |
| Performance | Locust baseline, query tuning | **R** |

**Time commitment:** 50% (0.5 FTE, в 1.5-FTE плане)

**Required skills:** Python senior, async (asyncio), SQL (PostgreSQL), pytest

---

### 3.3 Senior DevOps

**Scope:** Infrastructure, deployment, observability, security-adjacent

| Зона | Ответственность | RACI |
|------|-----------------|------|
| Infrastructure (k8s, DB) | Cluster management, HA, backups | **R** |
| CI/CD (`.github/workflows/`) | Pipeline setup, secrets, deploys | **R** |
| Observability (Prometheus, Grafana, Tempo, Loki) | Setup, dashboards, alerts | **R** |
| On-call rotation | Secondary (после Tech Lead) | **R** |
| Migration | Submodule → subtree, CloudNativePG | **R** |
| Disaster Recovery | DR drills, WAL-G restore tests | **R** |
| Performance | Capacity planning, load tests | **C** (Consulted) |

**Time commitment:** 50% (0.5 FTE)

**Required skills:** Kubernetes, PostgreSQL HA, Prometheus, Helm, Argo Rollouts

---

### 3.4 Security Engineer (part-time)

**Scope:** Threat model, pen-test, compliance, RLS, SOPS

| Зона | Ответственность | RACI |
|------|-----------------|------|
| Threat model (STRIDE) | Annual + on-major-change | **R** |
| Pen-test coordination | Engage freelancer, triage findings | **R** |
| SAST/DAST | semgrep, OWASP ZAP, rules | **R** |
| RLS policies | Design + review | **R** |
| SOPS / secrets rotation | Quarterly | **R** |
| Compliance docs (GDPR, SOC2) | Drafting + review | **C** (Consulted) |
| Security incidents | First responder (после Tech Lead) | **R** |

**Time commitment:** 25% (0.25 FTE)

**Required skills:** AppSec, OWASP Top 10, GDPR basics, SAST/DAST tooling

---

### 3.5 Tech Writer / Docs (part-time)

**Scope:** User-facing docs, API docs, ADRs, runbooks

| Зона | Ответственность | RACI |
|------|-----------------|------|
| User docs (README, tutorials) | Quick start, FAQ, examples | **R** |
| API docs site | Mintlify/Docusaurus deployment | **R** |
| ADRs | Drafting + maintenance | **C** (Consulted) |
| Runbook (`RUNBOOK.md`) | Update after each incident | **R** |
| CHANGELOG / release notes | Per release | **R** |
| Postmortems | Edit + publish (после incident lead) | **R** |

**Time commitment:** 25% (0.25 FTE)

**Required skills:** Markdown, Docusaurus/Mintlify, technical writing in EN+RU

---

## 4. 🔄 Backup & Escalation

### 4.1 Backup matrix (закрывает R-R02)

| Primary | Backup (цель к концу W5) | Coverage zone |
|---------|--------------------------|---------------|
| Tech Lead (`@asurdev`) | **TBD: 2nd maintainer** (см. P4-10) | Architecture, final decisions, on-call |
| Senior Backend | **TBD: 2nd backend** (P4-10 pair-programming) | Core, orchestration, web |
| Senior DevOps | **TBD: 2nd DevOps** (P4-10) | Infra, CI/CD, observability |
| Security Engineer | **External: pen-test freelancer** | Threat model, pen-test |
| Tech Writer | **Community contributors** (post-GA) | User docs |

**Action items:**
- **W3 (Phase 0 finish):** identify 2nd maintainer candidate
- **W4 (Phase 3 finish):** pair-programming sessions (2× 4h) на orchestrator + security
- **W5 (GA prep):** CODEOWNERS updated, backup has admin access

### 4.2 Escalation path (on-call)

```
Incident detected (P1/P2)
    ↓
[0-15 min] On-call primary (Tech Lead) → triage
    ↓
[15-60 min] Если не решено → DevOps backup
    ↓
[1-4 hours] Если не решено → Security Engineer (если security-related)
    ↓
[4+ hours] Stakeholder notification (по RELEASE_CHECKLIST §6)
    ↓
Post-incident: postmortem в течение 48h
```

**Контакты:** см. internal `docs/EMERGENCY_CONTACTS.md` (PII, не публикуется в Git)

---

## 5. 📋 CODEOWNERS (для GitHub auto-assign)

**Файл:** `.github/CODEOWNERS` (создаётся в W5, PR к P4-10)

```gitignore
# Default owners
*                           @asurdev @<backup-maintainer>

# Core (architecture-critical)
/core/                      @asurdev
/orchestration/             @asurdev
/agents/                    @asurdev

# DevOps (infra-critical)
/deploy/                    @asurdev @<devops-backup>
/.github/workflows/         @asurdev @<devops-backup>
/migrations/                @asurdev

# Security (security-critical)
/security/                  @asurdev @<security-engineer>
*.env*                      @asurdev
SECURITY.md                 @asurdev @<security-engineer>
PRIVACY.md                  @asurdev @<security-engineer>

# Docs
/docs/                      @asurdev @<docs-writer>
*.md                        @asurdev
```

---

## 6. 🧑‍🤝‍🧑 Onboarding новых контрибьюторов

### 6.1 Pre-requisites

- Прочитать `README.md` (5 мин)
- Прочитать `docs/TEAM_ROLES.md` (этот файл, 10 мин)
- Прочитать `PRODUCTION_BACKLOG.md` (top-15 задач, 15 мин)
- Прочитать `docs/DEFINITION_OF_DONE.md` (5 мин)
- Прочитать `CONTRIBUTING.md` (10 мин)

### 6.2 Day 1 checklist

- [ ] GitHub доступ (добавить в org `mahasur13-sys`)
- [ ] k8s namespace создан (`astrofin-dev-{username}`)
- [ ] Локальный setup: `make setup` (см. `Makefile`)
- [ ] `pytest -q` — все тесты зелёные локально
- [ ] `pre-commit install` — hooks активны
- [ ] `gh auth status` — logged in
- [ ] `kubectl get ns` — есть доступ к dev-кластеру

### 6.3 First contribution

- Найти issue с label `good-first-issue` или `help-wanted`
- Создать branch `feature/<issue-number>-<short-desc>`
- Сделать change, запушить, открыть PR
- Прочитать review comments, доработать
- После merge — закрыть issue

**Ожидаемое время до first merged PR:** 1-2 дня (для trivial) / 1-2 недели (для substantial)

---

## 7. 🛡️ Bus Factor Mitigation (P4-10)

**Текущий bus factor = 1** (только `@asurdev` имеет admin + критические знания).

**План к GA (W3–W5):**

| Sprint | Action | Time |
|--------|--------|------|
| W3 | Identify 2nd maintainer candidate (community, friends-of-friends) | 2h |
| W3 | Create `docs/EMERGENCY_CONTACTS.md` (off-Git) | 1h |
| W4 | Pair-programming session #1: orchestrator (4h) | 4h |
| W4 | Pair-programming session #2: security/SOPS (4h) | 4h |
| W5 | Add 2nd maintainer to GitHub org + CODEOWNERS | 1h |
| W5 | Document `MAINTAINERS.md` with zones | 1h |
| W5 | Verify backup has admin + can deploy | 2h |

**Success criteria:**
- 2+ people can independently deploy a hotfix
- 2+ people can answer architecture questions
- CODEOWNERS enforces 2-reviewer rule на critical paths

---

## 8. 🔗 Cross-references

- `file 'CONTRIBUTING.md'` — как контрибьютить (практический гайд)
- `file 'docs/RISK_REGISTER.md'` — R-R02 (bus factor)
- `file 'docs/DEFINITION_OF_DONE.md'` — критерии для PR review
- `file '.github/CODEOWNERS'` — auto-assign reviewers
- `file 'docs/MAINTAINERS.md'` — создаётся в W5 (P4-10)

---

*Last updated: 2026-07-04*

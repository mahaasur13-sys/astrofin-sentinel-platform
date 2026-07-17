# Шаг 3 — Doc Audit

> **Дата:** 2026-07-12
> **Scope:** все top-level `.md` файлы в корне репозитория
> **Классификация:** ✅ Current / 🟡 Drift / 🔴 Stale
> **Предшествующие шаги:** [STEP_2_INVENTORY.md](./STEP_2_INVENTORY.md)

---

## 0. Краткий summary

Просканировано **42 top-level .md** + **~80 docs/ + Knowledge + Documents**. Основные findings:

1. **`asp-work/`** — полная дублирующая копия **27 top-level .md** (включая README, AGENTS, EXECUTIVE_SUMMARY, PRODUCTION_BACKLOG, AUDIT_*). Untracked. Это **drift × 2**: содержимое уже устаревшее (даты 2026-03/06/07), и оно вообще не должно существовать в master.
2. **README.md** ссылается на **6 несуществующих путей** (`infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/`, `audit_reports/`, `agents/_archived/`, `docs/AGENT_REGISTRY.md`).
3. **EXECUTIVE_SUMMARY.md** датирован 2026-07-03, ссылается на Sprint 1 (Mon 2026-07-06). Сегодня 2026-07-12, спринт формально идёт, но документ заявляет горизонт «5 нед до v1.0.0 GA 2026-08-03».
4. **RELEASE_PLAN_v1.0.0.md** имеет target 2026-08-05, но **CHANGELOG.md уже провозгласил v1.0.0 = 2026-07-07** → конфликт версионирования.
5. **PRODUCTION_BACKLOG.md** перечисляет G1–G17 как «осталось закрыть», хотя CHANGELOG утверждает, что многие из них (#123, #124, #131, #132, #133, #134) уже merged в PRах 2026-07-07.
6. **AUDIT_2026-03-26.md** (615 строк) и **AUDIT_2026-06-17.md** (617 строк) — гигантские устаревшие снапшоты. **AUDIT_2026-06-17.md** стоит перенести в `docs/audits/2026-06-17/`, а мартовский — в `docs/audits/2026-03-26/` (или удалить, т.к. есть v2).
7. **GRAPH_ANALYSIS.md** (205 строк) — устаревший, относится к подмодульной эпохе.
8. **PRODUCTION_READINESS_REPORT.md** (362 строки) — датирован 2026-07-02, до текущей ветки работ.
9. **CHANGELOG.md** ссылается на `docs/adr/0009-unified-jwt-auth.md`, но в `docs/adr/` — `ADR-0009-unified-jwt-auth.md` (с префиксом `ADR-`). **Path mismatch** в SECURITY.md, RUNBOOK.md, CHANGELOG.md.
10. **GITHUB_PROJECT_SETUP.md** (629 строк) — единственный экземпляр, без `asp-work/` дубликата → кандидат на перенос в `docs/runbooks/` или `docs/setup/`.

---

## 1. Таблица классификации top-level .md

| # | Файл | Строк | Статус | Краткое обоснование |
|---|------|------:|:------:|---------------------|
| 1 | `README.md` | 98 | 🔴 | 6 невалидных path-референсов; доксит `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/` (не существуют). |
| 2 | `AGENTS.md` | 390 | 🟡 | В целом адекватен, ссылается на `monitoring/health_endpoints.py` (должен быть `health_endpoints.py`); references на `deploy/docker/supervisord.conf` (✅). Содержит секцию 2026 Hybrid Signal — актуальна. |
| 3 | `KNOWN_ISSUES.md` | 58 | 🟡 | Хорошая структура, но не упоминает 51 skipped test (упомянуто в super-memory) и PRs 176/182/184/186. |
| 4 | `EXECUTIVE_SUMMARY.md` | 151 | 🟡 | Дата 2026-07-03, горизонт 5 нед (v1.0.0 GA 2026-08-03). Содержание всё ещё отражает текущее состояние на ~75 % readiness, но формулировки ссылаются на подмодули, которых больше нет. |
| 5 | `PRODUCTION_BACKLOG.md` | 765 | 🔴 | Дата 2026-07-03. Перечисляет G1–G17 как «осталось закрыть», но CHANGELOG.md показывает, что многие пункты (SOPS, PII scrubber, RUNBOOK, MAINTAINERS, SLO, ADR-0009) уже closed PRами 2026-07-07. **Конфликт истины.** |
| 6 | `RELEASE_PLAN_v1.0.0.md` | 332 | 🔴 | Target 2026-08-05, но CHANGELOG.md уже выпустил v1.0.0 = 2026-07-07. Документ ссылается на подмодули. |
| 7 | `CHANGELOG.md` | 44 | 🟡 | Заявляет v1.0.0 = 2026-07-07 GA, но в `Knowledge/multi-agent-digest-2026-07-12.md` (latest) уже идёт работа над Phase 4. Нужна запись v1.0.1+ или явный «Unreleased». |
| 8 | `ROADMAP.md` | 94 | 🔴 | Дата 2026-06-24, последний коммит `e4bbea4`. Этот снапшот 18-дневной давности; заявляет readiness 85 % в mock-режиме. |
| 9 | `PRD.md` | 336 | 🟡 | Вероятно актуален по существу, но не проверен детально. |
| 10 | `PROJECT_SPEC.md` | 492 | 🟡 | Большой, не проверен детально. Стоит сверить с канонической структурой из STEP 2. |
| 11 | `MOSCOW_PRIORITIZATION.md` | 392 | 🟡 | MoSCoW, потенциально всё ещё актуален, но нужна сверка с реальным прогрессом. |
| 12 | `PRODUCTION_READINESS_REPORT.md` | 362 | 🔴 | Дата 2026-07-02, устарел. |
| 13 | `PRODUCTION_RESTORE.md` | 185 | 🟡 | Процедура восстановления. Проверить на актуальность путей и команд. |
| 14 | `SPRINT_1.md` / `SPRINT_2.md` / `SPRINT_1_ISSUES.md` | 304/409/1465 | 🟡 | 1465-строчный SPRINT_1_ISSUES — кандидат на перенос в `docs/sprints/`. |
| 15 | `SECURITY.md` | 110 | 🟡 | Ссылается на `docs/adr/0009-unified-jwt-auth.md` (✅ есть как `ADR-0009-…`). Структура правильная. |
| 16 | `PRIVACY.md` | 124 | 🟡 | GDPR-style, не проверен детально. |
| 17 | `RUNBOOK.md` | 76 | 🟡 | Хорошая структура. Ссылка на `docs/RUNBOOK.md` — есть. Ссылка на `SLO.md` — есть. |
| 18 | `SLO.md` | 68 | ✅ | Аккуратный, self-contained. |
| 19 | `MAINTAINERS.md` | 70 | ✅ | Self-contained, актуальный. |
| 20 | `CONTRIBUTING.md` | 120 | 🔴 | Section «Project Structure» показывает `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/` — **все три не существуют**. |
| 21 | `DEPLOYMENT.md` | 260 | 🟡 | Ссылается на `monitoring/health_endpoints.py` (должен быть `health_endpoints.py` в корне). |
| 22 | `CHANGELOG.md` | 44 | 🟡 | См. #7. |
| 23 | `GITHUB_PROJECT_SETUP.md` | 629 | 🟡 | Кандидат на перенос в `docs/setup/github-project.md`. |
| 24 | `GRAPH_ANALYSIS.md` | 205 | 🔴 | Относится к подмодульной эпохе. |
| 25 | `RALPH_INSTRUCTIONS.md` | 25 | 🟡 | Короткий, не проверен. |
| 26 | `AUDIT_2026-03-26.md` | 615 | 🔴 | Устарел. Есть v2 (42 строки). |
| 27 | `AUDIT_2026-03-26_v2.md` | 42 | 🔴 | 4 месяца давности, мартовский снапшот. |
| 28 | `AUDIT_2026-06-17.md` | 617 | 🟡 | 25-дневной давности, ещё релевантен как reference. |
| 29 | `CLAUDE.md` | 3 | 🟡 | Stub, ссылается на AGENTS.md. |
| 30 | `progress.md` | 778 | 🔴 | Прогресс-журнал, должен быть в `docs/internal/`. |
| 31 | `.github/BRANCH_PROTECTION.md` | 54 | 🟡 | Процедурный, проверить на актуальность. |
| 32 | `Knowledge/multi-agent-digest-*.md` | 30-90 × 44 | 🟡 | Ежедневные дайджесты, исторические архивы. |
| 33 | `Documents/audit-*.md`, `Documents/decision_*.md`, `Documents/stage1-*.md` | 44-292 × 17 | 🟡 | Операционные документы 2026-07-10, стоит перенести в `docs/internal/2026-07-10/`. |

---

## 2. Проверка path-референсов против реальной ФС

| Документ | Ссылается на | Реально | Статус |
|----------|--------------|---------|--------|
| `README.md` | `infrastructure/asurdev/` | ❌ | Stale |
| `README.md` | `kernel/atom-federation/` | ❌ | Stale |
| `README.md` | `bridge/roma/` | ❌ | Stale |
| `README.md` | `audit_reports/` | ❌ | Stale |
| `README.md` | `agents/_archived/` | ❌ | Stale |
| `README.md` | `docs/AGENT_REGISTRY.md` | ❌ | Stale |
| `CONTRIBUTING.md` | `infrastructure/asurdev/` | ❌ | Stale |
| `CONTRIBUTING.md` | `kernel/atom-federation/` | ❌ | Stale |
| `CONTRIBUTING.md` | `bridge/roma/` | ❌ | Stale |
| `RUNBOOK.md` | `monitoring/health_endpoints.py` | ✅ `health_endpoints.py` | Drift (path) |
| `DEPLOYMENT.md` | `monitoring/health_endpoints.py` | ✅ `health_endpoints.py` | Drift (path) |
| `SECURITY.md` | `docs/adr/0009-unified-jwt-auth.md` | ✅ `docs/adr/ADR-0009-unified-jwt-auth.md` | Drift (имя) |
| `CHANGELOG.md` | `docs/adr/0009-unified-jwt-auth.md` | ✅ `docs/adr/ADR-0009-unified-jwt-auth.md` | Drift (имя) |
| `SLO.md` | `deploy/monitoring/recording_rules.yml` | ✅ | OK |
| `SLO.md` | `deploy/monitoring/alert_rules.yml` | ✅ | OK |
| `KNOWN_ISSUES.md` | `agents/`, `core/`, `web/` | ✅ | OK |
| `CHANGELOG.md` | `docs/audits/` | ❌ (есть `audit_repo/`) | Drift |
| `AGENTS.md` | `monitoring/health_endpoints.py` | ✅ `health_endpoints.py` | Drift (path) |
| `AGENTS.md` | `deploy/docker/supervisord.conf` | ✅ | OK |

**Критические находки:**
- **6 невалидных путей** в README/CONTRIBUTING (подмодули `asurdev/`, `atom-federation/`, `roma/` — не существуют, т.к. inline произошёл в Шаге 1 решения).
- **Path drift × 4** в RUNBOOK/DEPLOYMENT/AGENTS/SECURITY/CHANGELOG (некритичный, но inconsistent).

---

## 3. Remediation list (приоритезированный)

### Обязательные (этот цикл)

1. **README.md** — переписать на каноническую структуру (см. §4). Убрать ссылки на `infrastructure/asurdev/`, `kernel/atom-federation/`, `bridge/roma/`, `audit_reports/`, `agents/_archived/`, `docs/AGENT_REGISTRY.md`.
2. **AGENTS.md** — фикс ссылки `monitoring/health_endpoints.py` → `health_endpoints.py`. Сверить секцию «2026 Hybrid Signal Architecture» с реальной структурой (`acos-contracts/`, `integrations/`, `src/`, `agents/`, `core/`, `orchestration/`, `meta_rl/`, `trading/`, `web/`, `tests/`).
3. **KNOWN_ISSUES.md** — добавить секцию «Skipped tests (51)» с ссылками на PRs 176/182/184/186.
4. **EXECUTIVE_SUMMARY.md** — обновить дату до 2026-07-12, пересчитать readiness (после 51 skipped test и PRов 184-189), убрать упоминания подмодулей.
5. **PRODUCTION_BACKLOG.md** — перекрёстная сверка с CHANGELOG: G1 (SOPS), G7 (DR runbook), G8 (SECURITY/PRIVACY), G17 (SLO) уже закрыты. Обновить статусы.
6. **RELEASE_PLAN_v1.0.0.md** — разрешить конфликт с CHANGELOG (либо v1.0.0 = 2026-07-07, либо v1.0.0 = 2026-08-05 — нельзя и то, и другое).
7. **CHANGELOG.md** — добавить секцию «[Unreleased]» с текущими 4 PR (187-189) и Phase 4.

### По возможности (этот цикл)

8. **SECURITY.md**, **RUNBOOK.md** — фикс ссылок `0009-unified-jwt-auth.md` → `ADR-0009-unified-jwt-auth.md`.
9. **DEPLOYMENT.md** — фикс ссылки `monitoring/health_endpoints.py` → `health_endpoints.py`.
10. **CONTRIBUTING.md** — переписать раздел «Project Structure» под каноническую структуру.

### Follow-up (отдельный цикл, объём большой)

11. Перенести `AUDIT_2026-03-26.md`, `AUDIT_2026-03-26_v2.md`, `AUDIT_2026-06-17.md` в `docs/audits/2026-{03-26,06-17}/`.
12. Перенести `progress.md` в `docs/internal/`.
13. Перенести `Knowledge/multi-agent-digest-*.md` в `docs/digests/2026-{04,05,06,07}/`.
14. Перенести `Documents/audit-*.md`, `Documents/decision_*.md`, `Documents/stage1-*.md` в `docs/internal/2026-07-10/`.
15. Перенести `SPRINT_1.md`, `SPRINT_2.md`, `SPRINT_1_ISSUES.md` в `docs/sprints/`.
16. Перенести `GITHUB_PROJECT_SETUP.md` в `docs/setup/`.
17. **`asp-work/` (27 дублей .md)** — untracked, рекомендация: `rm -rf asp-work/` (либо `git rm -rf --cached asp-work/` если хочется сохранить на диске; рекомендую полное удаление — содержимое 100 % дублирует устаревшие top-level .md, никакой уникальной информации не несёт).

---

## 4. План rewrite README.md

### 4.1 Каноническая структура (из STEP 2 + рефакторинг)

```
astrofin-sentinel-platform/
├── acos-contracts/          # Shared contracts (Python types, error schemas)
├── agents/                  # 12 AI agents (AstroCouncil + Electoral + Synthesis)
│   └── _impl/               # Agent implementation sources
├── core/                    # Core utilities (ephemeris, logging, volatility, auth)
├── orchestration/           # Sentinel v5 orchestrator, router
├── meta_rl/                 # Meta-reinforcement-learning pipeline + A/B testing
├── trading/                 # Trading engine (Binance, TWAP, execution)
├── web/                     # FastAPI dashboard
├── knowledge/               # RAG/FAISS knowledge base, atom specs
├── tests/                   # Pytest suite
├── src/                     # Production runtime (security/api/errors)
├── integrations/            # 3rd-party integrations (Stripe, Sentry, etc.)
├── health_endpoints.py      # K8s /healthz, /livez, /readyz
├── deploy/                  # Docker, docker-compose, monitoring, k8s
├── scripts/                 # CLI utilities
├── tools/                   # Internal tooling
├── docs/                    # Architecture, ADRs, runbooks, audits
│   ├── adr/                 # Architecture Decision Records
│   ├── audits/              # (after follow-up) Historical audits
│   ├── api/                 # OpenAPI, Dash UI
│   ├── db/                  # Schema, migrations
│   ├── security/            # Threat model, RBAC, secrets
│   └── runbooks/            # Operational procedures
├── agents/AstroCouncil_instructions.md
├── agents/ElectoralAgent_instructions.md
├── agents/SynthesisAgent_instructions.md
├── knowledge/atom specs     # ATOM_R-041, ATOM-DB-MIGRATION, etc.
├── security/                # Threat model, secrets, RBAC
├── deploy/                  # Production deployment manifests
└── docs/                    # All process & architecture docs
```

**Снятые со структуры (исключить из README):**

- ❌ `infrastructure/asurdev/` — был отдельным submodule, теперь содержимое в `deploy/` и `src/`.
- ❌ `kernel/atom-federation/` — был отдельным submodule, теперь inline в `kernel/atom-federation/` (если есть) или `src/`.
- ❌ `bridge/roma/` — был отдельным submodule, теперь inline в `src/bridges/roma/`.
- ❌ `audit_reports/` — нет такой директории.
- ❌ `agents/_archived/` — нет такой директории.
- ❌ `docs/AGENT_REGISTRY.md` — нет такого файла (агенты описаны в `agents/*_instructions.md`).

### 4.2 Целевая структура нового README.md

```markdown
# AstroFin Sentinel Platform

> Multi-agent trading platform: fundamental + quant + sentiment + astrology
> in a formal ensemble with audit-trail. RAG + Meta-RL + 13-agent council.

[![CI] ...] [![Nightly] ...] [![License: All Rights Reserved] ...]

## TL;DR
- 13 agents (AstroCouncil, Electoral, Synthesis, …) produce ensemble signals.
- Sentinel v5 orchestrator with RAG-first context retrieval.
- Meta-RL for adaptive calibration. A/B testing framework.
- v1.0.0 GA shipped 2026-07-07. Currently: Phase 4 (security/compliance/docs).

## What it does
[ 4-5 строк: что за платформа, для кого, USP ]

## Repository layout
[ Дерево из §4.1 — каноническое ]

## Quick start
[ pip install -e . && pytest -q && python -m web.app ]

## Documentation
- docs/ARCHITECTURE.md — system architecture
- docs/META_RL_ARCHITECTURE.md — meta-RL details
- docs/adr/ — Architecture Decision Records
- docs/api/openapi.yaml — REST API spec
- docs/db/schema.md — database schema
- docs/security/THREAT_MODEL.md — STRIDE threat model
- RUNBOOK.md — on-call runbook
- SLO.md — service-level objectives
- CHANGELOG.md — release history

## Status
| Component | Status | Notes |
|-----------|--------|-------|
| Multi-agent ensemble | ✅ Production | 12 agents + AstroCouncil |
| Sentinel v5 orchestrator | ✅ Production | |
| RAG (FAISS) | ✅ Production | |
| Meta-RL / A/B testing | ✅ Production | |
| Auth (JWT) | 🟡 In progress | dual-model cleanup #81 |
| Tests | 🟡 51 skipped | tracked, non-blocking |
| SLO / Observability | ✅ Production | Prometheus + Grafana |

## Security
See SECURITY.md. Report via GitHub Security Advisories.

## License
All Rights Reserved. See LICENSE.

## Maintainer
@asurdev (Felix)
```

### 4.3 Что НЕ войдёт в новый README (чтобы не плодить drift)

- Никаких упоминаний подмодулей (`asurdev/`, `atom-federation/`, `roma/` как submodule).
- Никаких несуществующих директорий.
- Никаких `audit_reports/`, `agents/_archived/`, `docs/AGENT_REGISTRY.md`.
- Никаких ссылок на `monitoring/health_endpoints.py` (вместо этого `health_endpoints.py`).

---

## 5. Предлагаемый порядок правок в этом цикле

| # | Файл | Действие | Объём |
|---|------|----------|-------|
| 1 | `README.md` | Полный rewrite (см. §4.2) | 1 файл |
| 2 | `AGENTS.md` | Локальные правки: `monitoring/health_endpoints.py` → `health_endpoints.py`; актуализировать «Project Structure» | sed/replace |
| 3 | `KNOWN_ISSUES.md` | Добавить секцию «Skipped tests (51)» | +10-15 строк |
| 4 | `EXECUTIVE_SUMMARY.md` | Обновить дату → 2026-07-12, убрать submodule references | +30-40 строк |
| 5 | `PRODUCTION_BACKLOG.md` | Перекрёстная сверка G1–G17 vs CHANGELOG (только статусы) | +15 строк |
| 6 | `RELEASE_PLAN_v1.0.0.md` | Конфликт-резолв: «v1.0.0 = 2026-07-07 (shipped); v1.0.1 = 2026-08-05 (planned)» | +5 строк |
| 7 | `CHANGELOG.md` | Добавить `[Unreleased]` секцию с PRs 187/188/189 и Phase 4 | +20 строк |
| 8 | `SECURITY.md`, `RUNBOOK.md`, `CHANGELOG.md` | `0009-unified-jwt-auth.md` → `ADR-0009-unified-jwt-auth.md` (3 sed) | 3 sed-а |
| 9 | `DEPLOYMENT.md`, `AGENTS.md` | `monitoring/health_endpoints.py` → `health_endpoints.py` (2 sed-а) | 2 sed-а |
| 10 | `CONTRIBUTING.md` | Переписать «Project Structure» под каноническую | +20 строк |

**Скоуп:** ~10 файлов, ~100-150 строк net change. Безопасный объём для одного цикла.

**Вне scope этого цикла (defer):**

- `AUDIT_*`, `progress.md`, `Knowledge/`, `Documents/`, `SPRINT_*` — перенос в `docs/*`.
- `asp-work/` (27 дублей) — отдельное решение (рекомендую `rm -rf`).
- `GRAPH_ANALYSIS.md` — перевод в `docs/internal/`.
- `ROADMAP.md` — переписать как часть Phase 4 (Sprint 4 docs).

---

## 6. Критические расхождения, требующие немедленного доклада

1. **CHANGELOG vs RELEASE_PLAN**: CHANGELOG провозгласил v1.0.0 = 2026-07-07 GA. RELEASE_PLAN target 2026-08-05. **Это разные релизы или ошибка?** Нужно решение Felix до правки RELEASE_PLAN.

2. **asp-work/ (27 .md дублей)**: это 100 % устаревшие копии (даты 2026-03/06). Они untracked → не в git, но лежат на диске. Если запустить `git status` (после init), они не появятся. Рекомендация: `rm -rf asp-work/` сейчас, в этом же цикле.

3. **README references 6 nonexistent paths** — это видно из публичного GitHub → потенциальный репутационный урон, если кто-то клонирует. **High priority**.

4. **PRODUCTION_BACKLOG G1–G17 vs CHANGELOG** — конфликт статусов. Если G1, G7, G8, G17 уже closed, то PRODUCTION_BACKLOG врёт про текущее состояние. **Medium priority** (внутренний документ, но используется для спринт-планирования).

---

## 7. Следующие шаги

1. Получить от Felix решение по **пункту 1** (v1.0.0 = 2026-07-07 vs 2026-08-05).
2. Получить OK на **пункт 2** (`rm -rf asp-work/`).
3. Применить **§5** в указанном порядке (10 файлов, ~150 строк).
4. После — переход к **Шагу 4: Code Audit** (структура кода, мёртвый код, безопасность, error handling, тесты).

Готов начать. Жду команды.

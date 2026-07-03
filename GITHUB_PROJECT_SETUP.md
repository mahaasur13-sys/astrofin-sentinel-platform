# 🎯 GitHub Project Board + Automation — AstroFin Sentinel Platform

> **Дата:** 2026-07-03
> **Цель:** Объединить все артефакты (Sprint 1-4, MoSCoW, Issue Template, Release Plan) в живую доску с автоматизацией
> **Тип:** GitHub Projects v2 (classic недоступен с 2024)
> **Уровень автоматизации:** Full (триггеры на labels, milestones, PR)

---

## 📋 Оглавление

1. [Что строим](#1-что-строим)
2. [Структура Project Board](#2-структура-project-board)
3. [Labels (5 групп, 22 лейбла)](#3-labels-5-групп-22-лейбла)
4. [Milestones (4 спринта + Release)](#4-milestones-4-спринта--release)
5. [Custom Fields](#5-custom-fields)
6. [Views (5 представлений)](#6-views-5-представлений)
7. [Workflow Automations (8 правил)](#7-workflow-automations-8-правил)
8. [Setup commands (gh CLI)](#8-setup-commands-gh-cli)
9. [Привязка к существующим артефактам](#9-привязка-к-существующим-артефактам)
10. [KPI Project Board](#10-kpi-project-board)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Что строим

**GitHub Project (v2, board)**: живёт в organization `mahaasur13-sys` (или user-repo) под названием **"AstroFin Sentinel — v1.0.0 Production"**.

**Структура:**

```
Project: AstroFin Sentinel — v1.0.0 Production
├── 30 issues (Sprint 1, готовы)
├── ~13 issues (Sprint 2, генерируются из SPRINT_2.md)
├── ~14 issues (Sprint 3, MoSCoW MUST Phase 3 + selected SHOULD)
├── ~12 issues (Sprint 4, MoSCoW MUST Phase 4-5)
└── ~22 issues (SHOULD backlog, без milestone)
─────────────────────────────────────────
ВСЕГО: 91 issue (87 backlog + 4 prep)

Columns: Backlog → Sprint Ready → In Progress → Review → Blocked → Done

Views:
├── 📊 Board (default)        — Kanban-доска
├── 📅 By Milestone           — группировка по спринтам
├── 🏷️ By Label               — фильтр по MoSCoW/Phase/area
├── 👤 By Assignee            — workload по людям
└── 📈 Burndown               — Sprint progress chart
```

**Автоматизация (8 workflow rules):**

1. `phase-X` label → авто-добавление milestone `Sprint X`
2. `critical` label → авто-флаг "Needs Triage", assign `@asurdev`
3. `must` label → авто-флаг "High Priority", поле `moscow` = `must`
4. Issue с `blocked` label → авто-флаг "Status: Blocked"
5. PR linked to issue → авто-перемещение issue в "Review"
6. PR merged → авто-перемещение issue в "Done", закрытие
7. Issue без assignee 7+ дней → авто-уведомление `@asurdev`
8. Milestone достигнут на 100 % → авто-уведомление в Slack/Telegram (через webhook)

---

## 2. Структура Project Board

### 2.1 Создание (через UI или gh CLI)

```bash
# Через gh CLI (создаёт user-owned project)
gh project create --owner mahaasur13-sys \
  --title "AstroFin Sentinel — v1.0.0 Production" \
  --description "Production-readiness backlog. MoSCoW: 31 MUST / 35 SHOULD / 17 COULD / 4 WON'T. Target GA: 2026-08-05."

# Получить ID
gh project list --owner mahaasur13-sys
PROJECT_ID="PVT_xxx"  # подставить реальный ID
```

### 2.2 Колонки (Status field)

| Order | Name | Description | Автоматика |
|------:|------|-------------|------------|
| 1 | 📥 Backlog | Новые issue, не запланированные в спринт | default для новых issue |
| 2 | 🎯 Sprint Ready | Issue запланирован в milestone, готов к работе | milestone set |
| 3 | 🔨 In Progress | Assignee взял в работу | assignee set |
| 4 | 👀 Review | PR открыт, ожидает ревью | PR linked |
| 5 | 🚧 Blocked | Явный блокер (label `blocked`) | label `blocked` |
| 6 | ✅ Done | Issue закрыт, PR мержен | issue closed |

**Настройка через gh CLI** (одна команда создаёт все колонки):

```bash
# Создание single-select field "Status"
gh project field-create $PROJECT_ID \
  --owner mahaasur13-sys \
  --name "Status" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "Backlog,Sprint Ready,In Progress,Review,Blocked,Done"
```

---

## 3. Labels (5 групп, 22 лейбла)

### 3.1 Группа 1: Phase (6 лейблов)

| Label | Color | Описание |
|-------|-------|----------|
| `phase-0` | `#0e8a16` | Подготовка, фикс текущих проблем |
| `phase-1` | `#fbca04` | Quick Wins + API Hardening |
| `phase-2` | `#d93f0b` | Database & Persistence |
| `phase-3` | `#5319e7` | Observability, SLO/SLI, Tracing |
| `phase-4` | `#b60205` | Security, Compliance, Docs |
| `phase-5` | `#1d76db` | Deploy, Release, Performance, On-call |

### 3.2 Группа 2: MoSCoW (4 лейбла)

| Label | Color | Описание |
|-------|-------|----------|
| `must` | `#b60205` | Без этого GA невозможен (MUST HAVE) |
| `should` | `#d93f0b` | Важно, но не блокирует GA |
| `could` | `#fbca04` | Nice-to-have, если будет время |
| `wont` | `#cccccc` | Осознанно отложено в v1.2+ |

### 3.3 Группа 3: Priority (3 лейбла, зарезервированы для critical/high/medium)

| Label | Color | Описание |
|-------|-------|----------|
| `critical` | `#b60205` | Блокер, требует немедленного внимания |
| `high` | `#d93f0b` | Важная задача, не блокер |
| `medium` | `#fbca04` | Средний приоритет |

### 3.4 Группа 4: Area (5 лейблов — кто делает)

| Label | Color | Описание |
|-------|-------|----------|
| `area/backend` | `#1d76db` | Backend-разработка (Python, FastAPI, Flask) |
| `area/devops` | `#5319e7` | DevOps (k8s, CI/CD, monitoring, deploy) |
| `area/security` | `#b60205` | Security (auth, secrets, compliance) |
| `area/docs` | `#0075ca` | Documentation (Markdown, ADRs, runbooks) |
| `area/qa` | `#0e8a16` | QA, testing, performance |

### 3.5 Группа 5: Type (4 лейбла)

| Label | Color | Описание |
|-------|-------|----------|
| `type/bug` | `#ee0701` | Что-то сломалось |
| `type/feature` | `#84b6eb` | Новая функциональность |
| `type/chore` | `#fef2c0` | Тех-долг, рефакторинг, гигиена |
| `type/spike` | `#bfd4f2` | Исследование, прототип |

### 3.6 Создание всех лейблов (bulk)

```bash
REPO="mahaasur13-sys/astrofin-sentinel-platform"

# Phase labels
for label in "phase-0:0e8a16" "phase-1:fbca04" "phase-2:d93f0b" "phase-3:5319e7" "phase-4:b60205" "phase-5:1d76db"; do
  name="${label%%:*}"; color="${label##*:}"
  gh label create "$name" --color "$color" --repo "$REPO" --description "Phase X: $(case $name in phase-0) echo 'Подготовка';; phase-1) echo 'Quick Wins';; phase-2) echo 'Database';; phase-3) echo 'Observability';; phase-4) echo 'Security';; phase-5) echo 'Deploy';; esac)" 2>/dev/null || true
done

# MoSCoW labels
for label in "must:b60205" "should:d93f0b" "could:fbca04" "wont:cccccc"; do
  name="${label%%:*}"; color="${label##*:}"
  gh label create "$name" --color "$color" --repo "$REPO" --description "MoSCoW: $name priority" 2>/dev/null || true
done

# Priority labels
for label in "critical:b60205" "high:d93f0b" "medium:fbca04"; do
  name="${label%%:*}"; color="${label##*:}"
  gh label create "$name" --color "$color" --repo "$REPO" --description "Priority: $name" 2>/dev/null || true
done

# Area labels
for label in "area/backend:1d76db" "area/devops:5319e7" "area/security:b60205" "area/docs:0075ca" "area/qa:0e8a16"; do
  name="${label%%:*}"; color="${label##*:}"
  gh label create "$name" --color "$color" --repo "$REPO" --description "Area: ${name#area/}" 2>/dev/null || true
done

# Type labels
for label in "type/bug:ee0701" "type/feature:84b6eb" "type/chore:fef2c0" "type/spike:bfd4f2"; do
  name="${label%%:*}"; color="${label##*:}"
  gh label create "$name" --color "$color" --repo "$REPO" --description "Type: ${name#type/}" 2>/dev/null || true
done

echo "✅ 22 labels created (или уже существовали)"
```

---

## 4. Milestones (4 спринта + Release)

| Milestone | Due Date | Кол-во задач | Описание |
|-----------|----------|------:|----------|
| `Sprint 1 — v1.0.0-prep` | 2026-07-12 | 30 | Phase 0 + начало Phase 1 |
| `Sprint 2 — Phase 1 finish + Phase 2` | 2026-07-19 | 13 | API hardening + DB foundation |
| `Sprint 3 — Phase 3 + Phase 4 start` | 2026-07-26 | 14 | Observability + Security tech |
| `Sprint 4 — Phase 4 finish + Phase 5` | 2026-08-02 | 12 | Deploy + GA |
| `v1.0.0 GA` | 2026-08-05 | 1 | Tag, release notes, blog post |

### 4.1 Создание milestones (bulk)

```bash
REPO="mahaasur13-sys/astrofin-sentinel-platform"

gh api repos/$REPO/milestones -f title="Sprint 1 — v1.0.0-prep" -f due_on="2026-07-12T23:59:59Z" -f description="30 задач. Phase 0 (7) + Phase 1 (8 MUST + 7 selected SHOULD). Sprint Goal: все тесты green, push разблокирован, secrets в SOPS, JWT готов."
gh api repos/$REPO/milestones -f title="Sprint 2 — Phase 1 finish + Phase 2" -f due_on="2026-07-19T23:59:59Z" -f description="13 задач. Phase 1 SHOULD (7) + Phase 2 MUST (6). Sprint Goal: production DB (TimescaleDB+pgvector), S3 backups, DR runbook."
gh api repos/$REPO/milestones -f title="Sprint 3 — Phase 3 + Phase 4 start" -f due_on="2026-07-26T23:59:59Z" -f description="14 задач. Phase 3 MUST (4) + selected SHOULD (3) + Phase 4 MUST (2). Sprint Goal: SLO/SLI, alerts, vulnerability scan в CI."
gh api repos/$REPO/milestones -f title="Sprint 4 — Phase 4 finish + Phase 5" -f due_on="2026-08-02T23:59:59Z" -f description="12 задач. Phase 4 SHOULD (5) + Phase 5 MUST (2) + selected. Sprint Goal: canary deploy, threat model, PRR, GA-ready."
gh api repos/$REPO/milestones -f title="v1.0.0 GA" -f due_on="2026-08-05T23:59:59Z" -f description="GA release. Tag v1.0.0, release notes, blog post, Reddit/HN announcement."

echo "✅ 5 milestones created"
```

---

## 5. Custom Fields

### 5.1 Список полей

| Field Name | Data Type | Options / Default | Назначение |
|------------|-----------|-------------------|------------|
| `Status` | SINGLE_SELECT | Backlog / Sprint Ready / In Progress / Review / Blocked / Done | Kanban-колонки |
| `MoSCoW` | SINGLE_SELECT | must / should / could / wont | Приоритет (sync с label) |
| `Phase` | SINGLE_SELECT | phase-0 / phase-1 / phase-2 / phase-3 / phase-4 / phase-5 | Sync с label |
| `Area` | SINGLE_SELECT | backend / devops / security / docs / qa | Sync с label |
| `Estimate` | NUMBER | hours | Из Issue Template |
| `Sprint` | SINGLE_SELECT | Sprint 1 / Sprint 2 / Sprint 3 / Sprint 4 / Backlog | По milestone |
| `PRR Required` | CHECKBOX | — | Отметка для Production Readiness Review |
| `Blocker` | CHECKBOX | — | Авто-true если label `critical` или `blocked` |

### 5.2 Создание полей (gh CLI)

```bash
PROJECT_ID="PVT_xxx"  # подставить реальный ID
OWNER="mahaasur13-sys"

# Status
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "Status" --data-type "SINGLE_SELECT" \
  --single-select-options "Backlog,Sprint Ready,In Progress,Review,Blocked,Done"

# MoSCoW
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "MoSCoW" --data-type "SINGLE_SELECT" \
  --single-select-options "must,should,could,wont"

# Phase
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "Phase" --data-type "SINGLE_SELECT" \
  --single-select-options "phase-0,phase-1,phase-2,phase-3,phase-4,phase-5"

# Area
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "Area" --data-type "SINGLE_SELECT" \
  --single-select-options "backend,devops,security,docs,qa"

# Estimate
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "Estimate (h)" --data-type "NUMBER"

# Sprint
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "Sprint" --data-type "SINGLE_SELECT" \
  --single-select-options "Sprint 1,Sprint 2,Sprint 3,Sprint 4,Backlog"

# PRR Required
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "PRR Required" --data-type "CHECKBOX"

# Blocker
gh project field-create $PROJECT_ID --owner $OWNER \
  --name "Blocker" --data-type "CHECKBOX"

echo "✅ 8 custom fields created"
```

---

## 6. Views (5 представлений)

### 6.1 📊 Board (default, Kanban)

**Group by:** Status
**Sort by:** MoSCoW (must first), then Estimate (asc)
**Filter:** MoSCoW != wont
**Layout:** Cards (с полями: Assignee, Estimate, Phase)

### 6.2 📅 By Milestone (Timeline)

**Group by:** Milestone
**Sort by:** Phase, then MoSCoW
**Layout:** Timeline (gantt-like)
**Use case:** видеть, как задачи распределены по 4 неделям

### 6.3 🏷️ By MoSCoW Priority

**Group by:** MoSCoW
**Sort by:** Estimate (asc)
**Filter:** Milestone != empty
**Layout:** Cards
**Use case:** убедиться, что MUST задачи в работе, а WON'T отложены

### 6.4 👤 By Assignee (Workload)

**Group by:** Assignee
**Sort by:** Estimate (desc)
**Filter:** Status != Done
**Layout:** Cards
**Use case:** равномерная нагрузка, ни один человек не перегружен

### 6.5 📈 Burndown (Sprint Progress)

**Type:** Chart
**Chart type:** Stacked area
**X-axis:** Date (по дням)
**Y-axis:** Count of issues (by MoSCoW)
**Filter:** Milestone = current sprint
**Use case:** визуальный burndown, видеть, успеваем ли к концу спринта

---

## 7. Workflow Automations (8 правил)

### 7.1 Automation #1: Auto-milestone по phase-label

**Trigger:** Issue labeled with `phase-X`
**Action:** Set milestone to `Sprint X` (если ещё не назначен)

```yaml
# Через UI: Settings → Workflows → Add rule
# Name: "Auto-milestone by phase"
# Trigger: "Issue labeled"
# Filter: label in ["phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5"]
# Action: "Set milestone to Sprint N (где N = phase number)"
```

**Через gh CLI не поддерживается напрямую** — нужно делать через UI или GitHub Actions.

### 7.2 Automation #2: Critical → assign @asurdev

**Trigger:** Issue labeled with `critical` OR `must`
**Action:** Assign to `@asurdev`, set Status = "Sprint Ready", add `needs-triage` label

### 7.3 Automation #3: MoSCoW sync label → field

**Trigger:** Issue labeled with `must`/`should`/`could`/`wont`
**Action:** Set custom field `MoSCoW` = same value

### 7.4 Automation #4: Blocked → Status = Blocked

**Trigger:** Issue labeled with `blocked`
**Action:** Set Status = "Blocked", add comment "🚧 This issue is blocked. See linked dependencies."

### 7.5 Automation #5: PR linked → Status = Review

**Trigger:** PR opened that mentions issue (e.g., "Closes #123")
**Action:** Move issue to "Review" column, add comment "👀 PR opened: <PR link>"

### 7.6 Automation #6: PR merged → Status = Done

**Trigger:** PR merged that closes issue
**Action:** Move issue to "Done", close issue, set MoSCoW archived field = true

### 7.7 Automation #7: Stale issue (7 days no activity, not In Progress)

**Trigger:** Daily cron (через scheduled workflow)
**Action:** Comment "👋 This issue has been idle for 7 days. Please update or close.", assign to @asurdev for review

### 7.8 Automation #8: Milestone 100 % complete → notify

**Trigger:** Milestone `Sprint N` has 100 % closed issues
**Action:** Post in #releases Slack channel: "🎉 Sprint N complete! X issues closed, Y story points delivered. On track for v1.0.0 GA on <date>."

### 7.9 Реализация через GitHub Actions (для automations #1, #5, #6, #7, #8)

Создать `.github/workflows/project-automation.yml`:

```yaml
name: Project Automation

on:
  issues:
    types: [labeled, assigned, closed]
  pull_request:
    types: [opened, closed, merged]
  schedule:
    - cron: '0 9 * * 1-5'  # будни в 9:00 UTC

jobs:
  sync-milestone-by-phase:
    runs-on: ubuntu-latest
    if: github.event.action == 'labeled'
    steps:
      - uses: actions/checkout@v4
      - name: Sync milestone by phase label
        uses: actions/github-script@v7
        with:
          script: |
            const phase = context.payload.issue.labels.find(l => l.name.match(/^phase-\d$/));
            if (phase) {
              const sprintMap = { 'phase-0': 'Sprint 1', 'phase-1': 'Sprint 1', /* ... */ };
              const milestone = context.repo.milestones.find(m => m.title === sprintMap[phase.name]);
              if (milestone) {
                await github.rest.issues.update({ owner: context.repo.owner, repo: context.repo.repo, issue_number: context.issue.number, milestone: milestone.number });
              }
            }

  pr-linked-move-to-review:
    runs-on: ubuntu-latest
    if: github.event.action == 'opened' && github.event.pull_request
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const pr = context.payload.pull_request;
            const linkedIssues = (pr.body.match(/#\d+/g) || []).map(s => parseInt(s.slice(1)));
            for (const num of linkedIssues) {
              const { data: issue } = await github.rest.issues.get({ owner: context.repo.owner, repo: context.repo.repo, issue_number: num });
              await github.rest.issues.createComment({ owner: context.repo.owner, repo: context.repo.repo, issue_number: num, body: `👀 PR opened: ${pr.html_url}` });
              // Move to Review (через Project API)
              // ...
            }
```

---

## 8. Setup commands (gh CLI)

Полный скрипт инициализации (запускать один раз от maintainer'а):

```bash
#!/bin/bash
# setup-project.sh — инициализация GitHub Project для AstroFin Sentinel
set -e

REPO="mahaasur13-sys/astrofin-sentinel-platform"
OWNER="mahaasur13-sys"

echo "🚀 AstroFin Sentinel — Project Setup"

# 1. Auth check
gh auth status || { echo "❌ gh not authenticated"; exit 1; }

# 2. Create Project
echo "📊 Creating project..."
PROJECT_ID=$(gh project create --owner $OWNER \
  --title "AstroFin Sentinel — v1.0.0 Production" \
  --description "Production-readiness backlog. MoSCoW: 31 MUST / 35 SHOULD / 17 COULD / 4 WON'T. Target GA: 2026-08-05." \
  --format json | jq -r '.id')
echo "✅ Project created: $PROJECT_ID"

# 3. Create labels
echo "🏷️ Creating labels..."
# ... (полный блок из секции 3.6)

# 4. Create milestones
echo "📅 Creating milestones..."
# ... (полный блок из секции 4.1)

# 5. Create custom fields
echo "📋 Creating custom fields..."
# ... (полный блок из секции 5.2)

# 6. Configure workflow automations
echo "⚙️ Configuring workflow automations..."
# Через UI (см. секцию 7)

# 7. Add existing issues to project
echo "📥 Adding existing issues to project..."
gh issue list --repo $REPO --limit 100 --json number --jq '.[].number' | while read num; do
  gh project item-add $PROJECT_ID --owner $OWNER --url "https://github.com/$REPO/issues/$num"
done

# 8. Create 5 views (через UI)
echo "👀 Create views in UI: Board / By Milestone / By MoSCoW / By Assignee / Burndown"

# 9. Set up workflow automation file
echo "⚙️ Creating .github/workflows/project-automation.yml..."
# ... (полный блок из секции 7.9)

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Open Project: https://github.com/orgs/$OWNER/projects/$PROJECT_ID (или /users/$OWNER/projects/$PROJECT_ID)"
echo "2. Configure workflow rules in UI (Settings → Workflows)"
echo "3. Create 5 views (см. секцию 6)"
echo "4. Import Sprint 1 issues from SPRINT_1_ISSUES.md"
```

**Запуск:** `bash setup-project.sh`

---

## 9. Привязка к существующим артефактам

### 9.1 Какие issue генерируются из каких документов

| Источник | Кол-во | Sprint / Milestone | Команда |
|----------|------:|---------------------|---------|
| `SPRINT_1_ISSUES.md` | 30 | Sprint 1 | Backend, DevOps, Security, Writer |
| `SPRINT_2.md` (таблица задач) | 13 | Sprint 2 | Backend, DevOps |
| `SPRINT_3.md` (если есть) | 14 | Sprint 3 | Backend, DevOps, Security |
| `SPRINT_4.md` (если есть) | 12 | Sprint 4 | Backend, DevOps, Tech Lead |
| `MOSCOW_PRIORITIZATION.md` (SHOULD backlog) | 22 | Backlog (без milestone) | — |
| **ИТОГО** | **91** | — | — |

### 9.2 Конвенция имён issue

**Формат:** `[P<phase>-<num>] <Краткое название>`

**Примеры:**
- `[P0-01] Расследовать 26 failing tests`
- `[P1-03] JWT вместо статичного API_KEY`
- `[P5-10] Production Readiness Review meeting`

### 9.3 Привязка issue к Project (bulk)

```bash
PROJECT_ID="PVT_xxx"

# Из SPRINT_1_ISSUES.md — каждое Issue #1..30
# Через UI: drag-and-drop на board
# Или bulk (создаёт issue и сразу добавляет в project):

# Issue #1 (P0-01)
gh issue create --repo $REPO \
  --title "[P0-01] Расследовать 26 failing tests" \
  --body-file issues/P0-01.md \
  --label "phase-0,critical,area/backend,type/chore,must,sprint-1" \
  --milestone "Sprint 1 — v1.0.0-prep" \
  --assignee "asurdev" \
  --project "$PROJECT_ID"
```

---

## 10. KPI Project Board

Метрики, которые считаются автоматически (через Insights → Charts):

| KPI | Целевое | Как считать |
|-----|---------|-------------|
| **Velocity** | 30 issues/нед (1 FTE) / 50 (1.5 FTE) | Sum of closed issues per sprint |
| **Burndown** | Линейный burn, без "hump" в конце | Open issues count по дням спринта |
| **MoSCoW distribution** | MUST 100 % к GA, SHOULD ≥ 60 % | Closed / Total по категориям |
| **Cycle time** | median ≤ 5 дней | (closed_at - created_at) для каждого issue |
| **Lead time** | median ≤ 7 дней | (closed_at - first_commit) для каждого issue |
| **PRR readiness** | 100 % MUST задач closed за 4 недели | См. RELEASE_PLAN_v1.0.0.md §7 |

**Чарты для добавления:**

1. **Velocity chart** (bar): closed issues per week
2. **Cumulative flow diagram** (line): open vs in-progress vs done
3. **MoSCoW pie chart**: distribution of closed issues
4. **Assignee workload** (stacked bar): issues per person
5. **Cycle time histogram**: распределение cycle time

---

## 11. Troubleshooting

### 11.1 "gh project" не работает в старых версиях

**Проблема:** `gh: 'project' is not a gh command`
**Решение:** `gh extension install github/gh-project`

### 11.2 Project не виден в репо

**Проблема:** Project создан, но не отображается в issue sidebar
**Решение:** Settings → Projects → Linked projects → Add → выбрать проект

### 11.3 Automation не срабатывает

**Проблема:** Правило в UI есть, но issue не перемещается
**Решение:**
1. Проверить, что issue в project (`gh project item-list $PROJECT_ID`)
2. Проверить filter (например, "issue is open" может скрывать closed)
3. Проверить, что rule enabled (не draft)

### 11.4 Custom field не обновляется

**Проблема:** Через automation пытаемся set field, но не работает
**Решение:** Некоторые fields нельзя менять через automations (только `Status`). Использовать GitHub Actions + GraphQL API.

### 11.5 Milestone с датой в прошлом

**Проблема:** `due_on` принимает только future dates
**Решение:** Не указывать `due_on` для прошедших milestone, или использовать только title

---

## 📚 Связанные документы

- `PRODUCTION_BACKLOG.md` — мастер-бэклог 87 задач
- `MOSCOW_PRIORITIZATION.md` — MoSCoW-категоризация
- `SPRINT_1.md` + `SPRINT_1_ISSUES.md` — Week 1 план и готовые issue
- `SPRINT_2.md` — Week 2 план
- `.github/ISSUE_TEMPLATE/production-task.md` — Issue Template
- `RELEASE_PLAN_v1.0.0.md` — Release Plan
- `EXECUTIVE_SUMMARY.md` — One-pager для стейкхолдеров

## 📁 Артефакты в этом PR (для воспроизводимости)

Этот документ **не один** — настройка Project Board — это 3 файла, которые коммитятся в репо:

| Файл | Что | Зачем |
|------|-----|-------|
| `.github/project-fields.json` | JSON-схема Custom Fields, 22 labels, 5 milestones | Одноразовый импорт через `gh project create --json-file` |
| `.github/workflows/project-board-lint.yml` | GitHub Action: lint issues + weekly audit | Автоматический контроль: все issue в milestone имеют phase+moscow+area labels, weekly digest в issue |
| `GITHUB_PROJECT_SETUP.md` | Этот документ — общая инструкция, troubleshooting | Onboarding новых контрибьюторов, обновление board при изменении process |

**Создание board** — один раз вручную (через `gh` CLI, см. секцию 8):
```bash
gh project create --owner mahaasur13-sys \
  --title "AstroFin Sentinel — v1.0.0 Production" \
  --json-file .github/project-fields.json
```

**Поддержка** — через `.github/workflows/project-board-lint.yml`:
- При создании/редактировании issue → проверка required labels (phase + moscow + area)
- Каждое воскресенье 23:00 UTC → отчёт: open MUST, blocked, stale >7d, milestone progress
- Отчёт публикуется в issue с label `project-audit` (создаётся автоматически)

---

> 📌 **Этот документ + JSON + Action — целостная система.** Setup один раз → работает месяцами. Любые изменения labels/views правим в JSON, повторно импортируем через `gh project edit`.
# ✅ Definition of Done — AstroFin Sentinel v1.0.0

> **Status:** ✅ Active (last reviewed 2026-07-04)
> **Owner:** Tech Lead (`@asurdev`)
> **Назначение:** чек-листы критериев "готово" на 3 уровнях: задача / спринт / фаза. Использовать в daily standup, sprint review, PRR.

---

## 1. 🎯 Назначение

**Definition of Done (DoD)** — это контракт между разработчиком и ревьюером. Без выполнения DoD задача считается **незавершённой**, даже если код написан.

**3 уровня DoD:**

1. **Task DoD** — что значит "одна задача P0–P5 завершена"
2. **Sprint DoD** — что значит "Sprint 1/2/.../5 готов к закрытию"
3. **Phase DoD** — что значит "фаза (Phase 0–5) завершена, можно переходить к следующей"

**Phase 5 = "GA Ready"** — все фазы DoD выполнены → v1.0.0 можно релизить.

---

## 2. 📋 Task-Level DoD (одна задача)

Каждая задача из `PRODUCTION_BACKLOG.md` считается **DONE**, когда выполнены **все 8 пунктов**:

### 2.1 Code

- [ ] Код написан и проходит `ruff check` (0 errors)
- [ ] Код проходит `mypy --strict` (0 errors на новых файлах)
- [ ] Код проходит `bandit -r` (без новых high)
- [ ] `pre-commit run --all-files` — зелёный

### 2.2 Tests

- [ ] Написаны unit-тесты (coverage ≥ 80 % для нового кода)
- [ ] Написаны integration-тесты (если задача интегрируется с внешним сервисом)
- [ ] Все тесты зелёные: `pytest -q tests/path/to/test_file.py` exit 0
- [ ] `pytest -q` (full suite) — fail count не вырос

### 2.3 Documentation

- [ ] Код задокументирован: docstrings (Google style) на всех public функциях
- [ ] Обновлён соответствующий `docs/*.md` (если меняется архитектура/API)
- [ ] ADR создан (если архитектурное решение): `docs/adr/NNNN-title.md`
- [ ] CHANGELOG обновлён (если user-facing change): `docs/CHANGELOG.md` → секция [Unreleased]

### 2.4 Review

- [ ] PR создан с заполненным шаблоном (`.github/ISSUE_TEMPLATE/production-task.md`)
- [ ] PR прошёл `project-board-lint.yml` (labels, fields)
- [ ] Code review одобрен ≥ 1 reviewer
- [ ] CI зелёный: `python-tests.yml`, `quality-gate.yml`, `security.yml`
- [ ] PR смержен в `release/1.0.0` (не в `master`!)

### 2.5 Deploy

- [ ] Изменение задеплоено в staging через PR merge
- [ ] Smoke test в staging прошёл (manual или automated)
- [ ] Нет регрессий в SLO (если observability уже есть)

### 2.6 Issue Tracking

- [ ] Issue привязан к sprint milestone (`Sprint N`)
- [ ] Issue привязан к правильным labels (Phase, MoSCoW, Area)
- [ ] Issue переведён в статус Closed
- [ ] Если есть sub-tasks — все закрыты

### 2.7 Audit & Compliance

- [ ] `core/audit.py` записал событие (если security/audit-related задача)
- [ ] Нет новых секретов в коде (gitleaks clean)
- [ ] `git log -p` проверен на утечки (PII, tokens)

### 2.8 Verification

- [ ] Acceptance Criteria из бэклога выполнены (все чекбоксы)
- [ ] Demo проведено (если user-facing)
- [ ] Tech Lead подтвердил "done" в standup

> ⚠️ **Если хоть один пункт не выполнен — задача NOT DONE.** Не закрывать issue, не мержить PR, не переходить к dependents.

---

## 3. 🚀 Sprint-Level DoD (один спринт W1–W5)

Спринт считается **DONE**, когда выполнены **все 7 пунктов**:

### 3.1 Tasks

- [ ] Все MUST-задачи спринта выполнены (Task-Level DoD ✅)
- [ ] SHOULD-задачи: ≥ 80 % выполнены, остальные — в carry-over с обоснованием
- [ ] COULD/WON'T — на усмотрение
- [ ] Carry-over ≤ 20 % от sprint commit (если больше — sprint planning error)

### 3.2 Quality

- [ ] `pytest -q` baseline: после спринта fail count **не вырос** относительно pre-sprint
- [ ] `ruff check` — 0 errors
- [ ] `bandit -r` — нет новых high
- [ ] Coverage: ≥ target для спринта (W1: 55 %, W2: 60 %, W3: 65 %, W4: 70 %, W5: 75 %)
- [ ] Security scan: semgrep 0 high, trivy 0 critical

### 3.3 Documentation

- [ ] Все запланированные `docs/*.md` созданы/обновлены
- [ ] CHANGELOG обновлён по итогам спринта
- [ ] README актуален (если менялся стек/команды)
- [ ] ADRs для архитектурных решений — в `docs/adr/`

### 3.4 Observability & Deploy

- [ ] Изменения задеплоены в staging
- [ ] SLO метрики (если есть) в норме: latency p95 < target, error rate < target
- [ ] Alerts работают (test alert отправлен)
- [ ] Dasha board отражает текущий state (не manual update)

### 3.5 Ceremonies

- [ ] Daily standups проведены (5/5 дней)
- [ ] Mid-sprint check проведён (Ср)
- [ ] Sprint Review проведён (Пт) с demo для stakeholders
- [ ] Sprint Retro проведён (Пт) с action items
- [ ] Sprint Planning для следующего спринта проведён

### 3.6 Communication

- [ ] Slack/email уведомление команде: "Sprint N done"
- [ ] Stakeholders получили summary (1-pager или email)
- [ ] `EXECUTIVE_SUMMARY.md` обновлён (если менялись даты/scope)
- [ ] GitHub milestone `Sprint N` closed (все issues закрыты)

### 3.7 Risk & Carry-over

- [ ] `RISK_REGISTER.md` обновлён (новые риски, решенные риски)
- [ ] `DEPENDENCIES.md` актуализирован (если менялись зависимости)
- [ ] Carry-over list для следующего спринта — в `SPRINT_KICKOFF_TEMPLATE.md`
- [ ] Velocity зафиксирована для capacity planning следующего спринта

> ✅ **Sprint Review demo checklist:** см. `SPRINT_N.md` раздел "Ceremonies" — там готовый demo agenda.

---

## 4. 🏗️ Phase-Level DoD (фаза Phase 0–5)

Фаза считается **DONE**, когда выполнены **все 5 пунктов + acceptance criteria из бэклога**:

### 4.1 Functional (Phase 0)

- [ ] `pytest -q` показывает ≤ 21 fail (с 26 → −5 блокеров)
- [ ] `git grep '\.bak-'` возвращает 0 результатов
- [ ] `docs/MIGRATION_submodules.md` существует, проверено на dev-форке
- [ ] `release/1.0.0` ветка создана и защищена
- [ ] `requirements.lock` коммитится, `python-setup.yml` его генерирует
- [ ] Bandit-отчёт лежит в `docs/security/bandit-baseline.md`
- [ ] ADR-0001 создан

### 4.2 Functional (Phase 1)

- [ ] `python tools/check_env.py --prod` exit 0 с реальным `.env.prod`
- [ ] `.env.prod` зашифрован SOPS, расшифровывается в k8s/init-container
- [ ] JWT-эндпоинт `/auth/login` выдаёт access (15 мин) + refresh (7 дн) токены
- [ ] Per-user rate limit срабатывает на 61-м запросе
- [ ] `curl -i http://app:8050/` показывает HSTS, CSP, X-Frame-Options
- [ ] 500-ответы не содержат stack trace
- [ ] Каждый ответ содержит `X-Request-ID`
- [ ] `/livez` и `/readyz` ведут себя по-разному при отказе Redis
- [ ] `ruff check` 0 errors, `bandit -r` без новых high

### 4.3 Functional (Phase 2)

- [ ] `psql -c "SELECT extname FROM pg_extension"` показывает `timescaledb`, `vector`
- [ ] RAG поиск через pgvector возвращает top-5 документов с latency p95 < 80ms (100k docs)
- [ ] `SELECT * FROM agent_decisions WHERE tenant_id = 'X'` возвращает только tenant X при `SET app.tenant = 'X'`
- [ ] `pg_dump` + WAL-G restore в чистый кластер за < 30 мин
- [ ] DB primary падает → replica становится primary за < 30 сек
- [ ] `tools/db_migration_check.sh` exit 0 на CI для всех миграций
- [ ] `psql -c "SHOW ssl"` → `on`
- [ ] `audit.audit_log` содержит записи о тестовом INSERT/UPDATE/DELETE

### 4.4 Functional (Phase 3)

- [ ] `docs/SLO.md` утверждён, error budget dashboard показывает текущий burn-rate
- [ ] Alertmanager шлёт тестовую алерт в Telegram
- [ ] Grafana dashboard `/d/slo-overview` показывает SLO-метрики в реальном времени
- [ ] Tempo/Jaeger показывает полный trace запроса (web → orchestrator → 13 agents → DB)
- [ ] Логи в Loki фильтруются по `trace_id`, по клику открывается trace
- [ ] PII scrubber доказательно удаляет `api_key=...` из логов
- [ ] Locust-baseline закоммичен в `tests/load/baselines.json`, CI падает при деградации > 20 %
- [ ] Sentry получает тестовую ошибку из staging
- [ ] Chaos-тест `kill-app-pod` отрабатывает, recovery < 30 сек, метрики это фиксируют

### 4.5 Functional (Phase 4)

- [ ] `docs/security/THREAT_MODEL.md` описывает все 6 STRIDE-категорий для 4 сервисов
- [ ] `semgrep ci` блокирует merge при ≥1 high
- [ ] `pip-audit` показывает 0 critical, открыты issue на medium
- [ ] `trivy image` показывает 0 critical для всех 4 production images
- [ ] Cosign verification проходит в admission controller (или README описывает процедуру)
- [ ] `SECURITY.md` и `PRIVACY.md` опубликованы
- [ ] CODEOWNERS содержит `* @asurdev @mahaasur13-sys` (или 2+ вторых)
- [ ] `docs/RUNBOOK.md` существует, диагностические скрипты лежат в `tools/diag/`
- [ ] Tabletop exercise проведён, retrospective записан
- [ ] ADR для 5 ключевых архитектурных решений — в `docs/adr/`
- [ ] API doc-site доступен по `docs.api.astrofin` (или staging URL)

### 4.6 Functional (Phase 5)

- [ ] Canary deploy 5 % → 100 % с auto-promote проходит за < 20 мин
- [ ] При injected SLO burn 14× за 1h система откатывается за < 2 мин
- [ ] alembic migration job в CD ждёт готовности DB перед переключением
- [ ] `CAPACITY.md` опубликован, load-test 200 users не роняет p95 > 1s
- [ ] Feature flag `risk_agent_disabled=true` мгновенно отключает риск-агента
- [ ] On-call расписание опубликовано, PagerDuty интегрирован
- [ ] 2 postmortem-документа лежат в `docs/postmortems/`
- [ ] PRR проведён, подписан `go-live` ticket
- [ ] Telegram bot отвечает на `/health` за < 500ms
- [ ] Tag `v1.0.0` подписан, GitHub Release с changelog опубликован

### 4.7 Cross-Phase Quality Gates

- [ ] `pytest -q` (full suite) — 0 fail (или все known issues в `KNOWN_ISSUES.md` с обоснованием)
- [ ] Coverage ≥ 75 % для `core/`, `web/`, `orchestration/`, `db/`
- [ ] Все 5 acceptance criteria фаз (4.1–4.6) выполнены
- [ ] Нет открытых Critical/High issues старше 7 дней
- [ ] Все 22 labels, 5 milestones, 4 views в GitHub Project настроены
- [ ] CI workflows все зелёные: `ci.yml`, `security.yml`, `compose-check.yml`, `deploy.yml`, `slsa4-*.yml`, `project-board-lint.yml`, `progress-report.yml`, `release-readiness-gate.yml`

---

## 5. 🎯 GA Definition of Done (v1.0.0)

**Система готова к GA v1.0.0**, когда выполнены **ВСЕ** пункты:

### 5.1 Functional Completeness

- [ ] Все 87 задач бэклога выполнены или осознанно отложены в W6+ с обоснованием в `KNOWN_ISSUES.md`
- [ ] 0 critical, 0 high в semgrep/trivy/pip-audit
- [ ] Все 26 ранее failing tests — green (или в issue с обоснованием)
- [ ] Нагрузочный тест 200 users проходит с p95 < 1s
- [ ] Все 5 фаз (Phase 0–5) завершены (DoD §4.1–4.6)

### 5.2 Security

- [ ] Threat model опубликован (`docs/security/THREAT_MODEL.md`)
- [ ] JWT-only auth (API_KEY deprecated, период миграции закрыт)
- [ ] SOPS для всех секретов
- [ ] RLS включена
- [ ] Pen-test проведён, critical/high закрыты
- [ ] SLSA L3 provenance для всех images
- [ ] 2 вторых maintainer в CODEOWNERS

### 5.3 Observability

- [ ] SLO/SLI определены и задокументированы
- [ ] Alerts на SLO burn-rate работают
- [ ] Distributed tracing работает (Tempo/Jaeger)
- [ ] PII redaction в логах
- [ ] 2 postmortem-документа (dry-run scenarios)
- [ ] Sentry интегрирован
- [ ] Grafana dashboards v2 активны

### 5.4 Compliance & Docs

- [ ] SECURITY.md, PRIVACY.md опубликованы
- [ ] ADR для ≥5 ключевых решений
- [ ] API docs site запущен
- [ ] CHANGELOG и release notes процесс
- [ ] DR runbook + проведённый drill
- [ ] RUNBOOK.md с диагностическими скриптами

### 5.5 Deploy & Release

- [ ] Canary deploy с auto-rollback
- [ ] Multi-region DR (хотя бы active-passive)
- [ ] v1.0.0 tag подписан, GitHub Release опубликован
- [ ] On-call расписание и PagerDuty
- [ ] 2 postmortem-документа
- [ ] PRR проведён и подписан

### 5.6 Operational Readiness

- [ ] `RISK_REGISTER.md` reviewed, ≤ 2 Open Critical/High рисков
- [ ] `DEPENDENCIES.md` актуален
- [ ] Все 8 CI workflows зелёные
- [ ] Velocity baseline за 5 спринтов: avg ≥ 70 % capacity
- [ ] Stakeholders подписали go-live

> 🚦 **Когда все 6 групп ✅ → "Go" decision. Хотя бы 1 ❌ в группе 5.1–5.5 → "No-Go", сдвиг релиза.**

---

## 6. 📊 DoD Compliance Tracking

| Sprint | Task DoD | Sprint DoD | Phase DoD | Notes |
|---|---|---|---|---|
| W1 | TBD | TBD | Phase 0 (P0-01..07) | Verify в Sprint Review |
| W2 | TBD | TBD | Phase 1 finish (P1-04..16) | |
| W3 | TBD | TBD | Phase 2 finish + Phase 3 start | |
| W4 | TBD | TBD | Phase 3 finish + Phase 4 start | |
| W5 | TBD | TBD | Phase 4 finish + Phase 5 + GA | |

**Tracking:** GitHub Project Board → custom field "DOD: Task ✅/❌", "DOD: Sprint ✅/❌".

---

## 7. 🛠️ Автоматизация DoD

| Check | Где автоматизирован | Что делает |
|---|---|---|
| `ruff check` | `pre-commit`, `ci.yml` | Локально + CI, 0 errors required |
| `mypy --strict` | `ci.yml` | Новые файлы должны быть strict-clean |
| `bandit -r` | `security.yml` | High блокирует merge |
| `pytest -q` | `python-tests.yml` | Fail count baseline tracking |
| `pip-audit` | `ci.yml` | Critical блокирует merge |
| `trivy image` | `deploy.yml` | Critical блокирует deploy |
| `semgrep` | `quality-gate.yml` | High блокирует merge |
| Coverage gate | `ci.yml` | Проверяет target по sprint (55/60/65/70/75 %) |
| `project-board-lint.yml` | `.github/workflows/` | Проверяет labels, fields, structure |
| `progress-report.yml` | `.github/workflows/` | Еженедельный summary |
| `release-readiness-gate.yml` | `.github/workflows/` | PR gate в release branch |

**Manual checks (DoD §2.5 Deploy, §2.8 Demo, §3.5 Ceremonies, §4 Cross-Phase)** — Tech Lead на standup/review.

---

## 8. 🔗 Связанные документы

- `file 'PRODUCTION_BACKLOG.md'` §2–§7 — acceptance criteria по фазам (зеркало §4)
- `file 'SPRINT_*.md'` — Definition of Done для каждого спринта
- `file 'SPRINT_KICKOFF_TEMPLATE.md'` — pre-flight checks (мини-DOD)
- `file 'docs/RISK_REGISTER.md'` — risk-driven DoD (риск закрыт = задача done)
- `file 'docs/DEPENDENCIES.md'` — "dependent task стартовала = upstream task done"
- `file 'docs/RELEASE_CHECKLIST.md'` — финальный go/no-go gate (использует §5)
- `file 'RELEASE_PLAN_v1.0.0.md'` — даты и milestones

---

> 📌 **Этот документ — истина в последней инстанции.** Если задача не соответствует DoD, она **не готова**, даже если кажется завершённой. Любые исключения — только с одобрения Tech Lead, с записью в `KNOWN_ISSUES.md`.

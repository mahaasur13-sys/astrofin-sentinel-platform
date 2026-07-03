---
name: Production Task
about: Стандартный шаблон для production-задач AstroFin Sentinel Platform (Phase 0-5)
title: "[P<phase>-<num>] <краткое название задачи>"
labels: ["production", "triage"]
assignees: []
---

# <краткое название задачи, описывающее результат, а не процесс>

<!--
═══════════════════════════════════════════════════════════════════════════════
📋 ИНСТРУКЦИЯ ПО ЗАПОЛНЕНИЮ
═══════════════════════════════════════════════════════════════════════════════
• Закройте секции с подсказками (`<контент>` или `<!-- ... -->`) и замените их
  реальным содержимым
• Используйте чек-листы `- [ ]` для Acceptance Criteria и Implementation Steps
• Заполняйте Estimate в часах (не в днях, не в story points)
• Указывайте блокирующие зависимости в секции Dependencies
• Привяжите milestone (Sprint 1 / Sprint 2 / v1.0.0)
• После создания issue — отредактируйте `labels` в правой панели GitHub
• При закрытии — заполните Related PRs / Files (ссылки на мерджи и файлы)

═══════════════════════════════════════════════════════════════════════════════
🎯 КОНВЕНЦИЯ НАЗВАНИЯ
═══════════════════════════════════════════════════════════════════════════════
[Phase X-Y] <Краткое название>

Примеры:
  [P0-01] Расследовать 26 failing tests
  [P1-03] JWT вместо статичного API_KEY
  [P2-05] S3 backups через WAL-G
  [P3-01] SLO/SLI определения
  [P4-10] Bus factor mitigation
  [P5-01] Canary deploy с auto-rollback

═══════════════════════════════════════════════════════════════════════════════
🏷️ ДОСТУПНЫЕ ЛЕЙБЛЫ
═══════════════════════════════════════════════════════════════════════════════
Phase:
  • phase-0 — Подготовка (блокеры, гигиена, lock-файлы)
  • phase-1 — Quick Wins + API Hardening
  • phase-2 — Database & Persistence
  • phase-3 — Observability, SLO/SLI, Tracing
  • phase-4 — Security, Compliance & Documentation
  • phase-5 — Deploy, Release, Performance, On-call

MoSCoW (выбрать ОДИН):
  • must — блокирует GA v1.0.0
  • should — важно, но не блокирует GA
  • could — nice-to-have, делаем если есть время
  • wont — осознанно отложено в v1.2+

Severity / Impact (выбрать ОДИН):
  • critical — блокер, нельзя мерджить
  • high — высокий приоритет, неделя на фикс
  • medium — обычный приоритет
  • low — бэклог

Domain (можно несколько):
  • backend — Python, FastAPI, агенты
  • devops — CI/CD, k8s, Docker, мониторинг
  • security — auth, secrets, RLS, compliance
  • database — Postgres, TimescaleDB, pgvector, миграции
  • observability — Prometheus, Grafana, OTel, логи
  • api — REST/JSON, rate limiting, валидация
  • docs — документация, ADR, runbook
  • testing — unit/integration/load/chaos tests

Type:
  • feature — новая функциональность
  • bug — дефект
  • refactor — рефакторинг без изменения поведения
  • chore — гигиена, .gitignore, миграции
  • docs — только документация
  • spike — исследование (POC, spike)

Sprint:
  • sprint-1 — Week 1 (2026-07-06 → 07-12)
  • sprint-2 — Week 2 (2026-07-13 → 07-19)
  • sprint-3 — Week 3 (2026-07-20 → 07-26)
  • sprint-4 — Week 4 (2026-07-27 → 08-02)

═══════════════════════════════════════════════════════════════════════════════
📍 ДОСТУПНЫЕ MILESTONES
═══════════════════════════════════════════════════════════════════════════════
• Sprint 1 (v1.0.0-prep) — 2026-07-12
• Sprint 2 (Phase 1 finish + Phase 2 start) — 2026-07-19
• Sprint 3 (Phase 3 Observability) — 2026-07-26
• Sprint 4 (Phase 4+5 GA) — 2026-08-02
• v1.0.0 GA — 2026-08-03
• v1.0.1 — 2026-08-17
• v1.1.0 — 2026-10-03
-->

---

## 🎯 Goal / Description

<!--
Что нужно сделать? Опишите РЕЗУЛЬТАТ (не процесс).
Плохо: "Написать код для JWT"
Хорошо: "Реализовать JWT-based auth с refresh tokens, dual-mode (X-API-Key + Bearer) на 2 недели"
-->

<что нужно сделать — 1-3 предложения, описывающие конкретный результат>

**Affected components:**

<!--
Перечислите файлы/модули, которых коснётся изменение.
Пример: `core/auth/jwt.py`, `web/middleware.py`, `tests/test_auth_jwt.py`
-->

- `<module/файл 1>`
- `<module/файл 2>`

---

## 📋 Why (контекст и MoSCoW-категория)

<!--
Объясните ЗАЧЕМ это нужно. Свяжите с:
• MoSCoW-категорией (must/should/could/wont)
• Конкретным гэпом (G1–G25) из PRODUCTION_BACKLOG.md
• Бизнес-риском, который устраняется
-->

**MoSCoW:** `must` / `should` / `could` / `wont`

**Gap:** `G<номер>` — `<название гэпа из PRODUCTION_BACKLOG.md>`

**Risk, который устраняется:** `<R<номер>>` — `<название риска>`

**Контекст:**

<почему это важно для v1.0.0 GA, какие последствия если не сделать, какая связь с другими задачами/готовностью 95 %+>

---

## 🔧 Implementation Steps

<!--
Разбейте работу на КОНКРЕТНЫЕ шаги. Используйте чек-боксы, чтобы отслеживать прогресс.
Каждый шаг — атомарное действие, которое можно проверить.
-->

- [ ] <шаг 1>
- [ ] <шаг 2>
- [ ] <шаг 3>
- [ ] <шаг N>

**Примеры хороших шагов:**

```markdown
- [ ] Создать `core/auth/jwt.py` с `JWTManager` классом (RS256, access 15 мин, refresh 7 дней)
- [ ] Добавить JWKS endpoint `GET /.well-known/jwks.json`
- [ ] Реализовать dual-mode в `core/auth/middleware.py`: читать и `X-API-Key`, и `Authorization: Bearer`
- [ ] Обновить `health_endpoints.py` для прокидывания user identity в request.state
- [ ] Покрыть тестами: `tests/test_auth_jwt.py` (issue/refresh/expire/invalid signature)
```

---

## ✅ Acceptance Criteria

<!--
Измеримые критерии ГОТОВНОСТИ. Каждый критерий должен быть проверяемым.
Используйте чек-боксы для отслеживания.
Думайте: "Если бы я пришёл через 3 месяца, как бы я проверил, что задача сделана?"
-->

- [ ] <AC 1: конкретный измеримый результат>
- [ ] <AC 2: проверяемое свойство>
- [ ] <AC N: что-то, что нельзя пропустить>

**Примеры хороших AC:**

```markdown
- [ ] `curl -X POST /auth/login -d '{"user":"x"}'` возвращает `{"access_token":"...","refresh_token":"..."}` (HTTP 200)
- [ ] `curl /protected-endpoint` без токена → HTTP 401
- [ ] `curl /protected-endpoint -H "Authorization: Bearer <expired>"` → HTTP 401 с `{"error_code":"token_expired"}`
- [ ] `pytest tests/test_auth_jwt.py -v` → 12/12 passed
- [ ] `bandit -r core/auth/jwt.py` → 0 high
- [ ] Документация в `docs/auth.md` обновлена
```

---

## 📊 Estimate

<!--
Укажите ОДНУ цифру в часах. Это НЕ story points и НЕ дни.
1 рабочий день 1 FTE = 8 ч.
Используйте эту таблицу для калибровки:
-->

| Размер | Часы | Пример |
|--------|-----:|--------|
| XS | 1 | `.gitignore` обновить |
| S | 2-3 | один класс + тесты |
| M | 4-6 | фича с интеграционными тестами |
| L | 8-12 | компонент с миграциями и observability |
| XL | 16+ | рефакторинг архитектуры (разбить на подзадачи!) |

**Estimate:** **<N> ч**

**Sub-tasks breakdown** (если Estimate ≥ 8 ч, разбить):

- <подзадача 1> — <ч> ч
- <подзадача 2> — <ч> ч
- ...

---

## 🔗 Dependencies

<!--
Какие ДРУГИЕ issue ДОЛЖНЫ быть закрыты ПЕРЕД этой?
Какие issue ЭТА задача БЛОКИРУЕТ?
Используйте ссылки #<номер> для GitHub.
-->

**Blocks (эта задача блокирует):**

- #<номер> — <название>
- #<номер> — <название>

**Blocked by (эта задача заблокирована):**

- #<номер> — <название> (MUST быть merged перед началом)
- #<номер> — <название>

**External dependencies** (не-issue, например, third-party):

- <например: Terraform module v2.0 должен быть опубликован>
- <например: AWS account ID получен>

---

## 🏷️ Labels

<!--
Предложенный набор лейблов. Проверьте/измените в правой панели GitHub.
ОБЯЗАТЕЛЬНО: phase-X (один) + MoSCoW (один) + severity (один) + domain (1-3)
-->

**Required:**

- `phase-<X>` — `<название фазы>`
- `<must|should|could|wont>` — MoSCoW
- `<critical|high|medium|low>` — Severity

**Domain (1-3):**

- `<backend|devops|security|database|observability|api|docs|testing>`

**Type (1):**

- `<feature|bug|refactor|chore|docs|spike>`

**Sprint (опционально):**

- `sprint-<N>` — если привязано к спринту

**Suggested final set:**

```
phase-<X>, <must|should|...>, <critical|...>, <backend|...>, <feature|...>, sprint-<N>
```

---

## 📍 Milestone

<!--
К какому milestone относится задача?
-->

**Milestone:** `<Sprint N / v1.0.0 GA / v1.0.1 / v1.1.0>`

**Target date:** `<YYYY-MM-DD>`

---

## 👤 Assignee

<!--
Кто ОСНОВНОЙ исполнитель? Несколько человек — это anti-pattern, лучше разделить.
-->

**Primary:** `@<github-handle>`

**Reviewer (предложенный):** `@<github-handle>`

**Backup (если Primary недоступен > 24 ч):** `@<github-handle>`

---

## 🧪 Testing Notes

<!--
Как будете тестировать? Какие типы тестов, какие сценарии?
Если задача не требует тестов — напишите "N/A" и объясните почему.
-->

**Test types required:**

- [ ] Unit tests (`tests/test_<module>.py`)
- [ ] Integration tests (с реальной DB/Redis)
- [ ] Load test (Locust, k6)
- [ ] Security test (bandit, semgrep, OWASP ZAP)
- [ ] Manual test (curl, browser)
- [ ] Chaos test (chaos-mesh)

**Test scenarios:**

- `<сценарий 1: например, "happy path — POST /auth/login с валидными credentials">`
- `<сценарий 2: например, "expired token → 401">`
- `<сценарий 3: например, "concurrent requests (100 rps) на /signal endpoint">`

**Coverage target:** `<например, ≥ 80% для нового кода>`

---

## 📝 Related PRs / Files

<!--
ЗАПОЛНЯЕТСЯ ПРИ ЗАКРЫТИИ ISSUE.
Какие PR закрыли задачу, какие файлы созданы/изменены.
-->

**Merged PRs:**

- #<PR-номер> — `<название PR>` (merged YYYY-MM-DD)
- #<PR-номер> — `<название PR>` (merged YYYY-MM-DD)

**Files created:**

- `<path/to/new/file1.py>`
- `<path/to/new/file2.md>`

**Files modified:**

- `<path/to/existing/file1.py>`
- `<path/to/existing/file2.py>`

**Migration scripts:**

- `migrations/<номер>_<название>.sql` (если применимо)

**Documentation:**

- `docs/<section>/<file>.md` (обновлено/создано)

---

## ✅ Definition of Done Checklist

<!--
Финальный чек-лист перед закрытием issue. Пройдитесь по нему перед PR review.
-->

- [ ] Код написан и протестирован локально
- [ ] Все `Acceptance Criteria` выполнены
- [ ] Unit/integration тесты добавлены и проходят
- [ ] `pytest -q` показывает pass rate ≥ baseline (или улучшение)
- [ ] `ruff check` 0 errors, `ruff format --check` clean
- [ ] `bandit -r <changed_files>` без новых high
- [ ] Pre-commit hooks (если есть) проходят
- [ ] Документация обновлена (если применимо)
- [ ] Миграции БД протестированы (up → down → up)
- [ ] Observability: метрики/логи/трейсы добавлены (если применимо)
- [ ] Security headers/RLS/auth проверены (если применимо)
- [ ] PR открыт с правильным шаблоном, прошёл review
- [ ] CI pipeline зелёный
- [ ] Issue привязано к milestone
- [ ] Time-tracked (заполнены часы в `Estimate` vs `Actual`)

**Actual time:** `<N ч>` (заполняется при закрытии)

---

<!--
═══════════════════════════════════════════════════════════════════════════════
📖 ПРИМЕР ЗАПОЛНЕННОГО ШАБЛОНА
═══════════════════════════════════════════════════════════════════════════════
См. ниже — секция "📋 Example: [P0-01] Расследовать 26 failing tests"
═══════════════════════════════════════════════════════════════════════════════
-->

---

# 📋 Example: [P0-01] Расследовать 26 failing tests

> ⚠️ Это ЗАПОЛНЕННЫЙ ПРИМЕР. Реальные issue создаются копированием секций ВЫШЕ и заменой placeholder-текста. Этот пример можно использовать как референс при создании новых issue.

---

## 🎯 Goal / Description

Классифицировать 26 failing tests, починить top-3 broken imports, остальное перенести в tracked issues. На выходе — `tests/FAILING_TESTS.md` с полной классификацией и ≥ 5 tests починенными.

**Affected components:**

- `tests/` — диагностика, классификация, фиксы
- `tests/FAILING_TESTS.md` — новый файл с отчётом
- `<конкретные модули>` — фикс broken imports

---

## 📋 Why

**MoSCoW:** `must`

**Gap:** Не классифицирован явно, но блокирует P5-10 (PRR) и весь release/1.0.0 (CI красный).

**Risk:** R5 — failing tests = CI красный = нельзя мерджить. Без зелёных тестов P5-10 (PRR) не подпишет go-live.

**Контекст:**

CI сейчас красный — 26 из ~300 тестов падают. Без классификации невозможно понять масштаб проблемы (flaky vs broken import vs regression). Без фикса top-3 невозможно мерджить в `release/1.0.0` ветку. PRR (Production Readiness Review) требует зелёный CI как обязательное условие подписания go-live.

---

## 🔧 Implementation Steps

- [ ] `cd /home/workspace/astrofin-sentinel-platform`
- [ ] `source venv/bin/activate` (если есть)
- [ ] `pytest --collect-only -q 2>&1 | head -50` — собрать список
- [ ] `pytest tests/ -x --tb=short 2>&1 | tee /tmp/test_run.log`
- [ ] Создать `tests/FAILING_TESTS.md` с шаблоном:
  - Test ID | Error | Category (flaky/import/broken/regression) | Action
- [ ] Категоризировать каждый из 26 tests
- [ ] Починить top-3 broken imports (отдельная подзадача P0-01.b)
- [ ] `git add tests/FAILING_TESTS.md && git commit -m "P0-01: document 26 failing tests"`

---

## ✅ Acceptance Criteria

- [ ] `tests/FAILING_TESTS.md` существует, заполнен на 100 % (26 строк)
- [ ] Каждый из 26 tests отнесён к одной из категорий: flaky / broken import / regression / async timeout
- [ ] Top-3 broken imports починены
- [ ] `pytest -q tests/test_*.py 2>&1 | tail -1` показывает ≤ 21 fail (было 26)
- [ ] Коммит в ветке с тегом `P0-01`
- [ ] Tracked issues созданы для оставшихся 21 tests с приоритетами

---

## 📊 Estimate

**Estimate:** **6 ч**

**Sub-tasks breakdown:**

- Сбор и анализ failing tests — 3 ч
- Создание FAILING_TESTS.md с классификацией — 2 ч
- Tracked issues для остатков — 1 ч

---

## 🔗 Dependencies

**Blocks:**

- #2 (P0-01.b — top-3 broken imports fix)
- #10 (P1-01 — production .env.prod.example, требует CI green)
- #All — любая задача, требующая зелёный CI для мерджа в release/1.0.0

**Blocked by:**

- (нет, может стартовать немедленно)

**External dependencies:**

- (нет)

---

## 🏷️ Labels

**Required:**

- `phase-0` — Подготовка
- `must` — MoSCoW
- `critical` — Severity (CI блокер)

**Domain (1-2):**

- `backend` — Python tests
- `testing` — собственно тесты

**Type (1):**

- `chore` — гигиена CI

**Sprint:**

- `sprint-1` — Week 1 (2026-07-06 → 07-12)

**Suggested final set:**

```
phase-0, must, critical, backend, testing, chore, sprint-1
```

---

## 📍 Milestone

**Milestone:** `Sprint 1 (v1.0.0-prep)`

**Target date:** `2026-07-12`

---

## 👤 Assignee

**Primary:** `@asurdev`

**Reviewer (предложенный):** `@mahaasur13-sys`

**Backup:** (пока не назначен — bus factor mitigation в P4-10)

---

## 🧪 Testing Notes

**Test types required:**

- [x] Manual test (запуск pytest вручную, классификация)
- [ ] Unit tests — N/A (задача про сами тесты)
- [ ] Integration tests — N/A

**Test scenarios:**

- `pytest --collect-only` — собрано ≥ 300 tests
- `pytest -x` — падает на 1-м же failing test
- `pytest -q tests/test_X.py` — конкретный файл для каждой классификации
- `grep -rn "ImportError" tests/ | wc -l` — подсчёт broken imports

**Coverage target:** N/A (эта задача НЕ добавляет продуктивный код, только классифицирует)

---

## 📝 Related PRs / Files

> *Заполняется при закрытии issue*

**Merged PRs:**

- (ожидается) #XXX — `P0-01: document 26 failing tests`

**Files created:**

- `tests/FAILING_TESTS.md` — отчёт о 26 failing tests с классификацией

**Files modified:**

- (возможно) `tests/test_<module>.py` — фикс broken imports

---

## ✅ Definition of Done Checklist

- [x] Код написан и протестирован локально (P0-01.b — top-3 fix)
- [x] Все `Acceptance Criteria` выполнены
- [ ] Unit/integration тесты добавлены и проходят — **N/A** (задача про гигиену)
- [x] `pytest -q` показывает pass rate улучшение (с 91 % до ≥ 93 %)
- [x] `ruff check` 0 errors
- [x] Документация обновлена (создан `tests/FAILING_TESTS.md`)
- [ ] Миграции БД — N/A
- [ ] Observability — N/A
- [x] PR открыт с правильным шаблоном, прошёл review
- [x] CI pipeline зелёный
- [x] Issue привязано к milestone (Sprint 1)
- [x] Time-tracked: Estimate 6 ч, Actual ___ ч

---

<!--
═══════════════════════════════════════════════════════════════════════════════
💡 TIPS ДЛЯ ISSUE CREATOR
═══════════════════════════════════════════════════════════════════════════════
1. **Делайте issue атомарными.** Если задача занимает > 8 ч, разбейте на подзадачи.
2. **Пишите Acceptance Criteria как тесты.** Если AC нельзя автоматизировать — 
   напишите manual test steps.
3. **Используйте Conventional Commits** в коммитах: `P1-03: add JWT-based auth`
4. **Reference issues** через `#123` (auto-link в GitHub).
5. **Self-assign** сразу при начале работы. Если застряли > 24 ч — 
   напишите комментарий с blocker.
6. **Закрывайте issue ТОЛЬКО после merge**, не после PR open. 
   Иначе теряется связь с PR.
7. **Используйте Projects** для визуализации sprint board (Backlog → 
   In Progress → Review → Done).

═══════════════════════════════════════════════════════════════════════════════
-->

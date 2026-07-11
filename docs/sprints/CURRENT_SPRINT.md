# Текущий активный спринт / активная задача

Этот файл — рабочее состояние на сейчас. Подробные планы спринтов лежат в
`docs/sprints/SPRINT_*.md`. Техдолг — в `docs/TECH_DEBT.md`.

---

## KI-127 — Стандартизация ошибок и auth decorator

- **Статус:** Done (ожидает мёрдж после KI-128)
- **Ветка:** `feat/err-01-improve-error-handling`
- **PR:** [#176](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/pull/176)
- **Коммит:** `a1e6c72` / `8eb6956` (sprint docs)
- **Acceptance criteria:** выполнены
- **Техдолг:** минимальный (shim для `REQUIRE_AUTH` — удалить после переходного
  периода, см. `docs/TECH_DEBT.md`).

### Что сделано

- `REQUIRE_AUTH` → `API_KEY_AUTH_DISABLED` (inverted semantics, truthy =
  отключить auth). Shim сохранён на 1 релиз с `DeprecationWarning`.
- Envelope `core.error_schema.format_error` теперь содержит поле `error`
  (наряду с `code` для back-compat).
- Timestamp regex в `test_timestamp_is_iso_utc` принимает опциональную
  миллисекундную часть.
- Добавлен `tests/error_handling/conftest.py` с фикстурами `error_payload`
  и `isolated_env`.
- `ruff format`/`ruff check`, `mypy core/ web/`, `pytest tests/auth/
  tests/error_handling/` — чисто. **36 passed**.

### Следующие шаги

1. ~~Дождаться зелёного Quality Gate на `a1e6c72`~~ — Quality Gate не
   запускается на `feat/**` (блокер KI-128).
2. Закрыть треды CodeRabbit (или ответить на оставшиеся комментарии).
3. **Дождаться зелёного Quality Gate на `7d43ac9` после мержа KI-128.**
4. Merge PR #176.
5. Перейти к следующей задаче бэклога.

---

## KI-128 — Workflow triggers fix (feat/** support)

- **Статус:** In Progress
- **Ветка:** `fix/ki-128-workflow-triggers`
- **PR:** (готовится)
- **Цель:** разблокировать Quality Gate / Security / Compose checks для всех
  feature-веток (`feat/**`), чтобы CI запускался на PR из feature-веток.
- **Артефакт:** `ki-128-workflow-triggers.patch` + `docs/CHANGE_REQUESTS/CR-2026-07-11-KI-128-workflow-triggers.md`.

### Что нужно сделать

1. Применить `ki-128-workflow-triggers.patch` локально:
   `git apply ki-128-workflow-triggers.patch`.
2. Добавить `feat/**` в branch-паттерны workflow-файлов:
   - `.github/workflows/ci.yml`
   - `.github/workflows/ci.security.yml`
   - `.github/workflows/quality-gate.yml`
   - `.github/workflows/compose-check.yml`
3. Push, открыть PR → `master`, смёрджить (можно squash).
4. После мержа KI-128 Quality Gate автоматически запустится на PR #176.

### Следующие шаги

1. Применить патч и закоммитить.
2. Открыть PR с описанием (см. ниже).
3. Merge.
4. Дождаться зелёного Quality Gate на PR #176 и merge #176.
5. Обновить этот файл и `docs/TECH_DEBT.md` после мержа обоих KI.

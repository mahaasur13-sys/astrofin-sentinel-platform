# Текущий активный спринт / активная задача

Этот файл — рабочее состояние на сейчас. Подробные планы спринтов лежат в
`docs/sprints/SPRINT_*.md`. Техдолг — в `docs/TECH_DEBT.md`.

---

## KI-127 — Стандартизация ошибок и auth decorator

- **Статус:** Done
- **Ветка:** `feat/err-01-improve-error-handling`
- **PR:** [#176](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/pull/176)
- **Коммит:** `a1e6c72`
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

1. Дождаться зелёного Quality Gate на `a1e6c72`.
2. Закрыть треды CodeRabbit (или ответить на оставшиеся комментарии).
3. Merge PR #176.
4. Перейти к следующей задаче бэклога.

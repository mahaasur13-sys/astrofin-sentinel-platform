# AstroFin Sentinel Platform — Consolidation Plan

**Дата:** 2026-07-21
**Статус:** P0 выполнен, P1-P3 спланирован
**Ветка:** `feature/architecture-consolidation`

---

## Executive Summary

Аудит выявил **43 дублированные директории** между корнем workspace и `astrofin-sentinel-platform/`, **5 дублирующихся агентов**, **2 нарушения R-01** (bare `requests`), **4 незащищённых production API-роута**, **485 файлов мёртвого кода** в `audit_repo/`, и **11/627 тестов** падающих на стадии collection.

---

## Фазы консолидации

### ✅ P0: Critical Security + Architecture Violations

| ID | Задача | Статус |
|----|--------|--------|
| SEC-01 | Добавить `@require_api_key` на `/api/v1/*` роуты (кроме `/health`) | ✅ DONE |
| SEC-02 | Блокировать dev-плейсхолдер `dev-api-key-change-me` в production/staging | ✅ DONE |
| ARCH-01 | Заменить `requests` → `aiohttp` в `fundamental_agent.py` | ✅ DONE |
| ARCH-01 | Заменить `requests` → `aiohttp` в `ml_predictor_agent.py` | ✅ DONE |
| DOC-01 | Создать `CONSOLIDATION_PLAN.md` | ✅ DONE |

### 🔴 P1: Мёртвый вес и дедупликация (EST: 2-3h)

| ID | Задача | Обоснование |
|----|--------|-------------|
| DEAD-01 | Удалить `audit_repo/` (485 файлов — устаревшие артефакты) | 485 файлов мёртвого кода, source of truth уже в `docs/` + ADR |
| DEAD-02 | Удалить дубли `v6/`, `v7/`, `v8/` из корня workspace (24 файла) | Snapshot-директории предыдущих версий — не используются, в platform уже есть копии |
| DEAD-03 | Удалить 5 пустых директорий: `AstroFinSentinelV5/`, `AsurDev/`, `astrofin-sentinel-v5/` | Пусты, создают confusion |
| DUPE-01 | Сравнить и синхронизировать корневые `*.py` с `astrofin-sentinel-platform/` | 6 файлов дублируются (`FINAL_INTEGRATION_TEST.py`, `health_endpoints.py`, `langgraph_schema.py`, `logging_setup.py`, `muhurtha.py`, `test_aspects.py`) |
| DUPE-02 | Удалить корневые `.py` после синхронизации (оставить в platform) | Root должен быть чистым workspace, не shadow-копией |
| DUPE-03 | Синхронизировать `AGENTS.md` (root=19K vs platform=24K — platform авторитативнее) | Root-версия устарела |

### 🟡 P2: Качество кода и тесты (EST: 4-6h)

| ID | Задача | Обоснование |
|----|--------|-------------|
| QUAL-01 | Установить all optional deps: `faiss-cpu`, `opentelemetry-*`, `langgraph`, `ollama`, `cachetools` | 11/627 тестов падают только из-за отсутствия опциональных пакетов |
| QUAL-02 | Обновить `requirements.txt` с разделением `[core]`, `[test]`, `[optional]` | Сейчас один плоский requirements.txt, не отражающий реальную зависимость |
| QUAL-03 | `web/callbacks.py` (1162 строки) — разбить на модули | Нарушает Single Responsibility, максимальный файл в проекте |
| QUAL-04 | Обновить `pip` (23.2.1 → 26.1.2) и `pydantic_core` (2.46.4 → 2.47.0) | Outdated пакеты с критическими security fixes |
| QUAL-05 | Запустить `ruff check --fix` на всех Python файлах | Линтер не проходил системно — нужен baseline scan |

### 🟢 P3: Инфраструктура и Observability (EST: 3-5h)

| ID | Задача | Обоснование |
|----|--------|-------------|
| INFRA-01 | `CONSOLIDATION_PLAN.md` в Git с CHANGELOG | Трекать прогресс консолидации |
| INFRA-02 | `npm audit fix` в `web-react/` | React 19 + Vite 8 — свежий стек, но npm audit вероятно покажет warnings |
| INFRA-03 | Добавить pre-commit hook: проверка на `import requests` в агентах | Автоматизация enforce R-01 |
| INFRA-04 | `docker-compose.yml` — добавить healthcheck для all services | Сейчас только postgres/redis имеют healthcheck, api/dashboard — нет |
| INFRA-05 | Обновить `.coderabbit.yaml` с учётом новых правил консолидации | Упомянуть P0 fixes как baseline |

---

## Git-стратегия

```
master (production)
  └── feature/architecture-consolidation  ← ТЕКУЩАЯ ВЕТКА
       ├── P0 fixes (SEC-01, SEC-02, ARCH-01) — squash-merge в master
       ├── P1 cleanup (DEAD-01..DEAD-03, DUPE-01..DUPE-03) — отдельный PR
       ├── P2 quality (QUAL-01..QUAL-05) — отдельный PR
       └── P3 infra (INFRA-01..INFRA-05) — отдельный PR
```

### PR Descriptions

**PR #1: «P0: Security + Architecture fixes»**
```
## Что сделано
- SEC-01: @require_api_key на все /api/v1/* роуты
- SEC-02: Блокировка dev-api-key-change-me в production
- ARCH-01: requests → aiohttp в fundamental_agent и ml_predictor_agent

## Проверка
- [x] python -m py_compile всех изменённых файлов
- [x] @require_api_key на 4 production роутах
- [x] Ни одного `import requests` в agents/_impl/
```

**PR #2: «P1: Dead code removal + deduplication»**
```
## Что сделано
- Удалён audit_repo/ (485 файлов)
- Удалены v6/v7/v8 snapshot-дубли
- Синхронизированы корневые дубликаты *.py
- AGENTS.md обновлён до platform-версии

## Риски
- audit_repo/ содержит 485 файлов — проверено, что все релевантные данные уже в docs/ архивах
```

---

## Миграция данных: Root ↔ Platform

| Категория | Предлагаемое действие |
|-----------|---------------------|
| `AGENTS.md`, `SOUL.md`, `pyproject.toml`, `requirements.txt`, `Makefile` | Platform-версия — авторитативна. Удалить root-копии. |
| `FINAL_INTEGRATION_TEST.py`, `health_endpoints.py`, `langgraph_schema.py`, `logging_setup.py`, `muhurtha.py`, `test_aspects.py` | Проверить differences, синхронизировать, перенести в platform. |
| Daily-reports (`DAILY_REPORT_*.md`, `SPRINT_3_DAILY_*.md`) | Переместить в `platform/reports/daily/`. |
| `astrofin-sentinel-platform/REPORTS/` | Centralised reports directory — все audit + consolidation reports здесь. |

---

## Риски и зависимости

| Риск | Вероятность | Mitigation |
|------|------------|------------|
| Удаление `audit_repo/` сломает импорты | Низкая | grep по всем `.py` на `from audit_repo`, `import audit_repo` — 0 результатов |
| Обновление AGENTS.md перезапишет CI checks section | Низкая | Platform-версия длиннее и содержит все CI rules |
| Функции `_fetch_crypto_metadata` / `_fetch_price_data` теперь async — нужен await | Устранён | Оба метода уже были `async def`, вызываются через `await` |
| `@require_api_key` на `/api/v1/dashboard` сломает фронтенд | Средняя | Фронтенд (React) должен передавать `X-API-Key` header — нужна координация |

---

## Метрики успеха

- [ ] 0 bare `import requests` в `agents/_impl/` ✅ (ARCH-01 выполнен)
- [ ] 100% production API routes за `@require_auth` ✅ (SEC-01 выполнен)
- [ ] 0 dev-плейсхолдеров в `core/settings.py` для production ✅ (SEC-02 выполнен)
- [ ] Тесты: 627/627 collected (0 errors) — 11 фиксится через P2/QUAL-01
- [ ] Количество директорий в root workspace: 2 (platform + Trash) вместо 43
- [ ] Ruff: 0 errors на всём проекте

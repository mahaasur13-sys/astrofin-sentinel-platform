# 🗓️ AstroFin Sentinel — Week 2 Sprint (Phase 1 finish + Phase 2 start)

> **Sprint Window:** 2026-07-13 (Mon) → 2026-07-19 (Sun) — 5 рабочих дней
> **Sprint Goal:** Завершить Phase 1 (API hardening) и развернуть production-ready database stack (TimescaleDB + pgvector + WAL-G backups). На выходе — JWT-only auth, distributed tracing работает, DB schema в проде, первый DR runbook.
> **Capacity:** 80 ч (1 FTE) / 120 ч (1.5 FTE)
> **Всего задач:** 13 (7 из Phase 1 finish + 6 из Phase 2 MUST)
> **Estimated effort:** 51 ч → utilization 64 % (29 ч buffer на ревью, debugging, post-incident fixes от Sprint 1, code freeze issues)
> **Приоритет:** 🟥 MUST + 🟧 SHOULD (MoSCoW)

---

## 📊 Sprint 2 Snapshot

| Метрика | Значение |
|---|---|
| Задач в спринте | 13 (8 backend, 3 devops, 2 security-adjacent) |
| Общий объём | 51 ч |
| Capacity (1 FTE) | 80 ч |
| **Buffer** | **29 ч (36 %)** ← высокий, т.к. Sprint 1 retro выявит tech debt + настройка DB требует исследования |
| Должно быть закрыто из открытых issues | 11 новых (создаются в начале спринта по шаблонам) |
| Carry-over из Sprint 1 | Ожидается 0–2 задачи (всё MUST-критичное) |
| Sprint 1 velocity baseline | 37 ч / 40 ч (92 %) |
| **Sprint 2 commit** | 51 ч / 80 ч (64 %) — осознанно ниже для поглощения Sprint 1 carry-over и DB surprises |

---

## 🎯 Sprint Goal в 3 измеримых результатах

1. **API Security:** JWT-only auth включён (статичный API_KEY deprecated с warning, но всё ещё работает 2 недели для миграции клиентов). Per-user rate limit активен. Security headers на всех endpoints. Input validation через Pydantic v2 покрывает 100 % FastAPI endpoints.
2. **DB Stack:** TimescaleDB extension установлен и работает. Hypertable для `ohlcv_bars` создана и принимает данные. pgvector установлен, RAG-индекс мигрирован (FAISS → pgvector). S3 backups через WAL-G настроены, проверены restore на dev-кластере.
3. **Observability Foundation:** Distributed tracing работает end-to-end (web → orchestrator → 13 agents → DB) с W3C traceparent propagation. PII redaction в логах. Глобальный error handler без stack traces в production responses. /docs/errors страница задокументирована.

---

## 📅 Дневной план (1 FTE baseline, 8 ч/день)

> ⚠️ **Структура:** Каждый день имеет 1–2 **фокусных задачи** (глубокая работа) + 0–1 **background** (ревью, документирование, тесты). Sub-tasks пронумерованы `День.Номер`.

### Пн, 13 июля — Phase 1 finish: API Hardening (ч.1)

**Фокус дня:** Per-user rate limiting + security headers.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P1-04** | Per-user rate limiting (subject claim из JWT) | 3 | Backend | Sprint 1 #P1-03 (JWT) |
| 2 | **P1-07** | Security headers middleware (HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy) | 2 | Backend | — |
| 3 | **P1-09** | Request-ID middleware (X-Request-ID UUIDv7, прокидывается в логи/метрики/трейсы) | 2 | Backend | — |
| 4 | _background_ | Code review для 4 PRов из Sprint 1 carry-over | 1 | Backend | — |

**AC конца дня:**
- [ ] Slowapi `key_func` читает `subject` claim из JWT (fallback на IP)
- [ ] `curl -i http://localhost:8050/` показывает все 5 security headers
- [ ] Каждый ответ содержит `X-Request-ID: <UUIDv7>`
- [ ] Логи в `core/logging.py` автоматически включают `request_id`

**Команды на утро:**
```bash
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull
workon astrofin  # или source venv/bin/activate

# Утренняя проверка
cat /tmp/sprint1_retro.md 2>/dev/null || echo "No retro yet"
git log --oneline -10
gh issue list --milestone "Sprint 1" --state closed --json number,title | head -20
```

---

### Вт, 14 июля — Phase 1 finish: API Hardening (ч.2)

**Фокус дня:** Input validation, error handling, Pydantic v2 migration.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P1-05** | Pydantic v2 input validation на всех FastAPI endpoints | 4 | Backend | P1-09 (Request-ID для error context) |
| 2 | **P1-08** | Глобальный error handler (4xx/5xx → JSON без stack trace) | 3 | Backend | P1-09 |
| 3 | _background_ | Написать тесты для P1-04, P1-07, P1-09 (security_headers_test.py, rate_limit_per_user_test.py) | 1 | Backend | Пн |

**AC конца дня:**
- [ ] Pydantic v2 schemas покрывают 100 % `web/routes/*.py` endpoints
- [ ] `curl -X POST` с невалидным телом возвращает 422 с понятным error_code
- [ ] 500-ответы не содержат stack trace (только в логах)
- [ ] `tests/test_security_headers.py` и `tests/test_rate_limit.py` зелёные

**Если останется время:** начать P1-10 (OpenAPI/Redoc).

---

### Ср, 15 июля — Phase 1 finish: API Hardening (ч.3) + DB Schema start

**Фокус дня:** Документация API + переключение на DB Schema.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P1-10** | OpenAPI/Redoc для FastAPI (`/docs`, `/redoc`, `/openapi.json`) | 2 | Backend | P1-05 (Pydantic schemas) |
| 2 | **P1-12** | Graceful shutdown (SIGTERM handler → drain DB pool, exit 0) | 2 | Backend | — |
| 3 | **P1-14** | Subprocess safety: заменить `os.system`/`subprocess.run(shell=True)` на `subprocess.run([...], check=True, timeout=N)` | 1 | Backend | — |
| 4 | **P2-01a** | TimescaleDB extension — `CREATE EXTENSION timescaledb` в `migrations/0008_timescaledb.sql` | 3 | Backend | — |

**AC конца дня:**
- [ ] `/docs` показывает все endpoints с примерами
- [ ] `kill -SIGTERM <pid>` → in-flight requests завершаются, exit code 0, логи "Graceful shutdown completed"
- [ ] `grep -rn "os.system\|shell=True" core/ orchestration/ | wc -l` = 0
- [ ] `psql -c "SELECT extname FROM pg_extension WHERE extname='timescaledb'"` возвращает `timescaledb`

**Команды для P2-01a:**
```bash
# Локально (dev)
docker exec -it astrofin-postgres psql -U astrofin -d astrofin -c \
  "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Миграция
alembic upgrade head
# или вручную:
psql $DATABASE_URL -f migrations/0008_timescaledb.sql
```

---

### Чт, 16 июля — Phase 2 MUST: DB Schema (ч.2) + Backups

**Фокус дня:** Hypertable + WAL-G backups (самый критичный день для DB).

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-01b** | Hypertable для `ohlcv_bars`, `agent_decisions`, `backtest_runs`. Сжатие по 7 дням, retention 2 года | 3 | Backend | P2-01a |
| 2 | **P2-05** | S3 backups через WAL-G: continuous WAL archiving, daily full, retention 7d/4w/12m | 4 | DevOps | P2-01a |
| 3 | **P2-12** | TLS для Postgres (`ssl=require`, `sslmode=verify-full`, CA в ConfigMap) | 2 | DevOps | — |

**AC конца дня:**
- [ ] `SELECT * FROM timescaledb_information.hypertables` показывает 3 таблицы
- [ ] `wal-g backup-push $WALG_S3_PREFIX` → exit 0, файл в S3
- [ ] **Test restore на отдельном кластере:** `wal-g backup-fetch` → restore → `SELECT count(*) FROM ohlcv_bars` соответствует ожидаемому
- [ ] `psql "sslmode=verify-full" -c "SHOW ssl"` → `on`
- [ ] Connection refused при `sslmode=disable`

**⚠️ Критично:** P2-05 restore-test ОБЯЗАТЕЛЕН. Без него — backups не верифицированы. Потратить хоть 2 ч сверху, но сделать.

---

### Пт, 17 июля — Phase 2 MUST: Backups verify + DR runbook + Migrations CI

**Фокус дня:** Закрыть DB-MUST блок, оставить polished runbook.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-05b** | Backup verification job в CI: еженедельно restore последнего backup в ephemeral контейнер, прогон smoke tests | 3 | DevOps | P2-05 |
| 2 | **P2-06** | DR runbook (`docs/DR_RUNBOOK.md`): шаги восстановления, контакты, RPO/RTO ≤ 1ч/4ч | 3 | DevOps | P2-05 |
| 3 | **P2-08** | Schema migrations CI-gate (`tools/db_migration_check.sh`: up → down → up; pre-commit hook) | 2 | Backend | — |

**AC конца дня:**
- [ ] `.github/workflows/backup-verify.yml` запускается еженедельно, последний run success
- [ ] `docs/DR_RUNBOOK.md` существует, содержит: contact list, RPO/RTO, пошаговый restore, post-mortem шаблон
- [ ] `pre-commit run --all-files` запускает `tools/db_migration_check.sh` локально
- [ ] CI (`python-tests.yml`) запускает тот же скрипт, падает при broken migration

**Команды для backup-verify:**
```bash
# Локальная проверка
docker run --rm -e WALG_S3_PREFIX=$WALG_S3_PREFIX \
  astrofin/wal-g:latest backup-fetch /tmp/restore LATEST
psql $RESTORE_DATABASE_URL -f /tmp/restore/restore.sql
psql $RESTORE_DATABASE_URL -c "SELECT count(*) FROM ohlcv_bars;"
```

---

## 📅 Выходные (опционально, не в capacity)

> Только если есть энергия или критичные fixes. Sprint goal НЕ зависит от выходных.

| # | ID | Задача | Часы | Зачем |
|---|----|--------|-----:|-------|
| 1 | **P1-11** | `print()` → `logger.info()` (ruff T201) | 2 | Hygiene, ruff gate |
| 2 | **P1-15** | `secrets.compare_digest` для HMAC проверок | 1 | Security, быстрый win |

---

## 📈 Burndown (ожидаемый)

| День | Запланировано (нарастающий итог) | Идеальный burndown | Реалистичный (сюрпризы DB) |
|------|--------------------------------:|-------------------:|--------------------------:|
| Пн | 7 ч (P1-04, P1-07, P1-09 + 1ч review) | 7 | 7 |
| Вт | 16 ч (+P1-05, P1-08) | 16 | 14 (если Pydantic migration длиннее) |
| Ср | 24 ч (+P1-10, P1-12, P1-14, P2-01a) | 24 | 22 (DB extension setup = +1ч) |
| Чт | 33 ч (+P2-01b, P2-05, P2-12) | 33 | 30 (WAL-G = +1-2ч на отладку) |
| Пт | 41 ч (+P2-05b, P2-06, P2-08) | 41 | 40 (restore test = ещё +1ч) |
| **Итого** | **41 ч** | **41/51** | **40/51 (78 %)** |

> **Стратегия:** Sprint 2 commit ниже, чем Sprint 1. Причина: DB работы = исследования, surprise factor, особенно WAL-G + TimescaleDB.

---

## 📦 Definition of Done для Sprint 2

### Функциональные
- [ ] JWT-only auth включён, `API_KEY` deprecated warning (но работает)
- [ ] Per-user rate limit активен (subject claim), 60 req/min default
- [ ] Все 5 security headers присутствуют на каждом response
- [ ] Input validation через Pydantic v2 покрывает 100 % FastAPI endpoints
- [ ] `/docs` (Swagger UI) и `/redoc` доступны, все endpoints задокументированы
- [ ] SIGTERM → graceful shutdown, exit 0, логирование завершения
- [ ] `subprocess.run([...], check=True, timeout=N)` паттерн везде
- [ ] `secrets.compare_digest` для всех HMAC проверок

### Database
- [ ] TimescaleDB extension установлен в production
- [ ] 3 hypertables созданы и принимают данные (`ohlcv_bars`, `agent_decisions`, `backtest_runs`)
- [ ] pgvector extension установлен (для Sprint 3 RAG-миграции)
- [ ] WAL-G continuous WAL archiving в S3 работает
- [ ] Backup verification job в CI запускается и проходит
- [ ] Restore test на dev-кластере проходит успешно
- [ ] `sslmode=verify-full` enforced в connection strings
- [ ] `tools/db_migration_check.sh` в CI + pre-commit
- [ ] `docs/DR_RUNBOOK.md` опубликован, RPO/RTO определены

### Observability
- [ ] Глобальный error handler не возвращает stack traces
- [ ] X-Request-ID во всех responses, прокидывается в логи
- [ ] `/docs/errors` страница задокументирована (Sprint 1 carry-over если был)

### Качество
- [ ] `pytest -q` ≤ 18 fail (было 23 после Sprint 1, −5 от DB тестов)
- [ ] `ruff check` 0 errors, `bandit -r` без новых high
- [ ] Coverage ≥ 60 % для `core/`, `web/`, `orchestration/`
- [ ] Code review пройден для всех PR

---

## 🔗 Зависимости от Sprint 1 (blockers)

| Зависит от | Sprint 2 задача | Что нужно от Sprint 1 |
|------------|----------------|----------------------|
| P1-03 (JWT) | **P1-04** (per-user rate limit) | JWT с subject claim |
| P1-09 (Request-ID) | **P1-05, P1-08** (validation, error handler) | Request-ID middleware |
| P1-05 (Pydantic) | **P1-10** (OpenAPI) | Pydantic schemas на endpoints |
| P1-02 (SOPS) | **P2-05** (WAL-G) | S3 credentials через SOPS |
| P1-13 (/livez, /readyz) | **P2-08** (migrations CI) | Health checks работают |
| P0-01 (тесты green) | **Все** | Чтобы CI не красный |

> ⚠️ **Если Sprint 1 задержится** по любой из этих зависимостей, Sprint 2 нужно сдвинуть или перепланировать.

---

## 🔄 Carry-over Plan (если что-то не успеем)

| Задача | Приоритет | Куда идёт |
|--------|----------|-----------|
| P1-11 (print→logger) | 🟨 Low | Sprint 3 background |
| P1-15 (secrets.compare_digest) | 🟧 Should | Sprint 3 (1ч, быстрый win) |
| pgvector RAG-миграция (P2-02) | 🟥 Must | Sprint 3 целиком (8ч, требует research по pgvector performance) |
| RLS policies (P2-03) | 🟧 Should | Sprint 3 (5ч) |

**Sprint 3 preview:** pgvector RAG-миграция, RLS, Connection pool tuning, Read-replica routing.

---

## ⚠️ Риски Sprint 2

| # | Риск | Вероятность | Импакт | Mitigation |
|---|------|------------:|-------:|------------|
| **R-S2-1** | WAL-G S3 permissions misconfigured (нет прав на write) | 🟧 Средняя | 🟥 High | Pre-flight: `aws s3 ls $WALG_S3_PREFIX` перед настройкой; dry-run в dev |
| **R-S2-2** | TimescaleDB extension не в managed PostgreSQL (RDS, Cloud SQL) | 🟧 Средняя | 🟧 High | Проверить в начале спринта версию PG; если managed — нужна tier с поддержкой timescaledb |
| **R-S2-3** | Pydantic v2 migration ломает 5-10 endpoints | 🟧 Средняя | 🟨 Medium | Делать endpoint-by-endpoint, не bulk; катить с feature flag |
| **R-S2-4** | Restore test занимает 3+ часа (большой dataset) | 🟨 Низкая | 🟨 Medium | Использовать subset backup для verify; full restore — раз в месяц |
| **R-S2-5** | Sprint 1 carry-over превышает 5ч | 🟧 Средняя | 🟨 Medium | Sprint 2 commit 64 % оставляет 29ч buffer; если нужно — режем P1-12 (graceful shutdown) в Sprint 3 |
| **R-S2-6** | TLS setup требует перевыпуска сертификатов, может затянуться | 🟨 Низкая | 🟧 Medium | Использовать cert-manager в k8s (если есть) или self-signed для dev |
| **R-S2-7** | DB connection pool exhaustion при WAL-G base backup | 🟨 Низкая | 🟧 Medium | Делать base backup в off-hours, throttle rate |

### Топ-3 риска, требующих внимания в начале спринта

1. **R-S2-1 (WAL-G S3 permissions)** — проверять в Пн утро, не в Чт
2. **R-S2-2 (TimescaleDB в managed PG)** — критично, без этого P2-01a блокируется
3. **R-S2-5 (Sprint 1 carry-over)** — узнать в первый день standup

---

## 🔀 Параллелизм (если 2 FTE)

| Трек | Owner | Задачи | Часы |
|------|-------|--------|-----:|
| **A — Backend** | Senior Backend (1 FTE) | P1-04, P1-05, P1-07, P1-08, P1-09, P1-10, P1-12, P1-14, P2-01a/b, P2-08 | 30 |
| **B — DevOps** | Senior DevOps (1 FTE) | P2-05, P2-05b, P2-06, P2-12, + помощь с P2-01b | 21 |

**2 FTE sprint commit:** 51 ч / 120 ч (43 %) — оба трека закроются в Ср-Чт, освобождая Пт для Sprint 3 planning.

**Если 1.5 FTE:** Backend full + DevOps part-time (0.5). Делаем Б всё что в DevOps, но последовательно.

---

## 🛠️ Команды для старта (Пн утро)

```bash
# 1. Синхронизироваться
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull origin release/1.0.0
workon astrofin

# 2. Создать Sprint 2 milestone (если ещё нет)
gh api repos/mahaasur13-sys/astrofin-sentinel-platform/milestones \
  -f title="Sprint 2 (DB + API finish)" \
  -f due_on="2026-07-19T23:59:59Z"

# 3. Создать 11 issues (см. SPRINT_2_ISSUES.md когда будет готов)
gh issue create --title "[P1-04] Per-user rate limiting" ...

# 4. Утренний check
gh issue list --milestone "Sprint 1" --state all --json number,title,state | jq '.[] | select(.state=="open")'
cat /tmp/sprint1_retro.md 2>/dev/null
```

---

## 📊 Метрики успеха Sprint 2

| Метрика | Цель | Как измерить |
|---------|-----|--------------|
| Sprint commit | 64 % (51/80) | `gh issue list --milestone "Sprint 2" --state closed` |
| Carry-over из Sprint 1 | ≤ 2 задачи | Standup Пн |
| New critical bugs | 0 | `gh issue list --label critical --state open` |
| `pytest` pass rate | ≥ 95 % (было ~88 % после Sprint 1) | `pytest -q tests/ \| tail -1` |
| Coverage | ≥ 60 % (core/web/orchestration) | `coverage report` |
| Security scan clean | semgrep 0 high, trivy 0 critical | CI artifacts |
| WAL-G backup verify success | 100 % за неделю | `.github/workflows/backup-verify.yml` runs |
| API latency p95 | < 500 ms (SLO) | Grafana dashboard |

---

## 🤝 Ceremonies

| Событие | Время | Участники | Длительность |
|---------|-------|-----------|-------------:|
| **Sprint 2 Planning** | Пт 10 июля 16:00 | Вся команда | 1 ч |
| **Daily Standup** | Пн–Пт 09:30 | Backend + DevOps | 15 мин |
| **Mid-sprint Check** | Ср 14:00 | Backend + DevOps | 30 мин (сверить burndown) |
| **Sprint Review** | Пт 17 июля 16:00 | + Stakeholders | 1 ч |
| **Sprint 2 Retro** | Пт 17 июля 17:00 | Вся команда | 1 ч |
| **Sprint 3 Planning** | Пт 17 июля 18:00 | Вся команда | 1 ч |

**Sprint Review demo agenda:**
1. JWT auth в действии (login → token → call)
2. /docs (Swagger UI) с примерами
3. Security headers в DevTools
4. TimescaleDB hypertable с данными (`SELECT count(*) FROM ohlcv_bars`)
5. WAL-G backup push → restore test на dev кластере
6. `/docs/errors` страница

---

## 📎 Приложение A. Carry-over Checklist из Sprint 1

Заполнить в начале Sprint 2 (Пн утро):

```
Sprint 1 Carry-over
═══════════════════════════════════════════════
□ P0-01.b (top-3 broken imports) → Done? Y/N
□ P0-03 (submodule plan) → Done? Y/N
□ P1-01 (.env.prod.example) → Done? Y/N
□ P1-02 (SOPS) → Done? Y/N
□ P1-03 (JWT) → Done? Y/N
□ P1-13 (/livez, /readyz) → Done? Y/N
□ P1-15 (secrets.compare_digest) → Done? Y/N
═══════════════════════════════════════════════
Total carry-over: __/7

If carry-over > 2: reduce Sprint 2 scope
If carry-over = 0: add P2-02 (pgvector) preview to Sprint 2
```

---

## 📎 Приложение B. Где искать что

| Что | Где |
|-----|-----|
| Sprint 1 issues | `gh issue list --milestone "Sprint 1"` |
| Sprint 1 retro | `/tmp/sprint1_retro.md` (создаётся в конце Sprint 1) |
| MoSCoW-приоритезация | `MOSCOW_PRIORITIZATION.md` |
| Полный бэклог | `PRODUCTION_BACKLOG.md` |
| Week 1 sprint | `SPRINT_1.md` |
| Week 1 issues (готовые) | `SPRINT_1_ISSUES.md` |
| DB Architecture | `knowledge/DB_ARCHITECTURE_PROMPT.md` |
| Alembic config | `alembic.ini`, `migrations/` |
| TimescaleDB docs | https://docs.timescale.com/self-hosted/latest/ |
| WAL-G docs | https://github.com/wal-g/wal-g |
| Pydantic v2 migration | https://docs.pydantic.dev/latest/migration/ |

---

## ✅ Готовность к старту

Pre-flight checklist (Пн 09:00):

- [ ] `gh auth status` — logged in
- [ ] `git status` — clean, on `release/1.0.0`
- [ ] `pytest -q tests/ | tail -1` — pass rate из Sprint 1
- [ ] `gh issue list --milestone "Sprint 1" --state closed | wc -l` — Sprint 1 velocity
- [ ] Прочитать `SPRINT_1_ISSUES.md` и `MOSCOW_PRIORITIZATION.md`
- [ ] Проверить `Sprint 1 retro` (если был)
- [ ] `Sprint 2 milestone` создан в GitHub
- [ ] Slack/email уведомление команде: "Sprint 2 starts"

---

> 📌 **Этот документ — операционный план на неделю.** Использовать как checklist на daily standup. После Sprint 2 retro обновить на основе реальной velocity.

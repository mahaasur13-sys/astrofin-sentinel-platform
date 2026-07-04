# 🗓️ AstroFin Sentinel — Week 3 Sprint (Phase 2 finish + Phase 3 start)

> **Sprint Window:** 2026-07-20 (Mon) → 2026-07-26 (Sun) — 5 рабочих дней
> **Sprint Goal:** Завершить Phase 2 (RAG-миграция на pgvector, RLS, HA, performance tuning) и развернуть observability-foundation: distributed tracing backend, PII redaction, Sentry. На выходе — RAG на pgvector в проде, RLS активна, Tempo/Jaeger принимает трейсы, PII не утекает в логи.
> **Capacity:** 80 ч (1 FTE) / 120 ч (1.5 FTE)
> **Всего задач:** 15 top-level (9 из Phase 2 finish + 1 SLO/SLI P3-01 + 1 tracing infra P3-06a + 4 sub-task P2-02a-d; задачи P3-02/06/08 перенесены в W4)
> **Estimated effort:** 66 ч → utilization 83 % (14 ч buffer)
> **Приоритет:** 🟥 MUST + 🟧 SHOULD (MoSCoW)

---

## 📊 Sprint 3 Snapshot

| Метрика | Значение |
|---|---|
| Задач в спринте | 15 (12 backend, 4 devops, 2 security; 4 sub-task P2-02a-d + 1 sub-task P3-06a) |
| Общий объём | 66 ч |
| Capacity (1 FTE) | 80 ч |
| **Buffer** | **14 ч (18 %)** ← средний, т.к. pgvector и RLS требуют исследования |
| Должно быть закрыто | 15 новых (создаются в начале спринта по шаблонам) |
| Carry-over из Sprint 2 | Ожидается 0–3 задачи (P2-01b, P2-05, P2-12) |
| Sprint 2 velocity baseline | 40 ч / 51 ч (78 %) |
| **Sprint 3 commit** | 66 ч / 80 ч (83 %) — высокий, но оправданный: Phase 2 MUST доделываем + SLO-фундамент |

---

## 🎯 Sprint Goal в 3 измеримых результатах

1. **RAG на pgvector в проде:** FAISS-индексы мигрированы в `documents.embedding vector(1536)`, top-5 retrieval работает с p95 < 80ms на 100k docs. `rag_retriever.py` переписан на `asyncpg`. Dual-write период: 1 неделя FAISS+pgvector параллельно.
2. **RLS + DB Performance:** Row-Level Security включена на критических таблицах (`agent_decisions`, `audit_log`), `tenant_id` policy активна. Read-replica routing работает (SELECT → replica). HA: CloudNativePG primary+2 replicas, failover < 30s. Vacuum tuning per table.
3. **Tracing & PII Foundation:** Tempo (или Jaeger v2) развёрнут в `deploy/docker-compose.tempo.yml`, OTel collector с batch+tail-sampling принимает трейсы от web/orchestrator/13 agents. PII scrubber работает в log filter. Sentry интегрирован в FastAPI/Flask/aiohttp.

---

## 📅 Дневной план (1 FTE baseline, 8 ч/день)

> ⚠️ **Структура:** Каждый день имеет 1–2 **фокусных задачи** + 0–1 **background**. Sub-tasks пронумерованы `День.Номер`.

### Пн, 20 июля — Phase 2 finish: RAG-миграция на pgvector (ч.1)

**Фокус дня:** Extension + схема + начало миграции FAISS-индексов.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-02a** | pgvector extension + `migrations/0009_pgvector.sql` (CREATE EXTENSION vector, table `documents.embedding vector(1536)`, HNSW index) | 4 | Backend | P2-01b (Sprint 2) |
| 2 | **P2-02b** | Скрипт миграции FAISS → pgvector: `tools/migrate_faiss_to_pgvector.py` (читает `.faiss` индекс, батчево пишет в Postgres) | 3 | Backend | P2-02a |
| 3 | _background_ | P3-01 SLO/SLI определения: `docs/SLO.md` — API (p95 < 500ms, error < 0.1%, availability 99.9%), backtest (p95 < 30s, success > 99%), ML inference (p95 < 200ms). Error budget calc | 3 | DevOps | — |

**AC конца дня:**
- [ ] `psql -c "\dx"` показывает `vector` extension
- [ ] `SELECT count(*) FROM documents` соответствует FAISS-индексу
- [ ] HNSW index создан: `\d documents` показывает `embedding vector(1536) INDEX ... USING hnsw`
- [ ] Migration script dry-run на dev-кластере, row count match FAISS

**Команды на утро:**
```bash
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull
workon astrofin

# Утренняя проверка
cat /tmp/sprint2_retro.md 2>/dev/null || echo "No retro yet"
gh issue list --milestone "Sprint 2" --state closed --json number,title | head -20
psql $DATABASE_URL -c "\dx" | grep -E "timescaledb|vector" || echo "Extensions missing"
```

---

### Вт, 21 июля — Phase 2 finish: RAG-миграция (ч.2) + retriever rewrite

**Фокус дня:** Переписать `knowledge/rag_retriever.py` на asyncpg, dual-write.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-02c** | Переписать `knowledge/rag_retriever.py`: `asyncpg.Pool`, `<=>` cosine distance, top-K с HNSW, fallback на FAISS на время dual-write | 5 | Backend | P2-02b |
| 2 | **P2-02d** | Dual-write feature flag: `RAG_BACKEND=pgvector|faiss|both`. По умолчанию `both` 1 неделю, затем `pgvector` | 2 | Backend | P2-02c |
| 3 | _background_ | Benchmark `pgvector` vs FAISS на 100k docs (p50/p95/p99) | 1 | Backend | P2-02c |

**AC конца дня:**
- [ ] `rag_retriever.search("bitcoin halving", top_k=5)` возвращает результаты из pgvector
- [ ] Feature flag `RAG_BACKEND=faiss` — старый путь работает
- [ ] Benchmark: pgvector p95 < 80ms, FAISS p95 < 50ms (разница ≤ 30ms acceptable)
- [ ] Тесты `tests/test_rag_retriever.py` зелёные для обоих backend'ов

**Если останется время:** начать P2-03 (RLS).

---

### Ср, 22 июля — Phase 2 finish: Row-Level Security + SLO/SLI start

**Фокус дня:** RLS policies + начать SLO/SLI (для W4 P3-03 Prometheus rules).

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-03** | RLS для `agent_decisions`, `audit_log`, `backtest_runs`. `migrations/0010_rls.sql`: `ENABLE ROW LEVEL SECURITY`, `CREATE POLICY tenant_isolation ON ... USING (tenant_id = current_setting('app.tenant')::uuid)` | 4 | Security Engineer | P2-01b |
| 2 | **P2-14** | DB-level audit log: trigger `audit.log_changes()` на INSERT/UPDATE/DELETE для `agent_decisions` → `audit.audit_log` (partitioned by month) | 3 | Security Engineer | P2-03 |
| 3 | _background_ | Тесты `tests/test_rls_isolation.py`: tenant A не видит данные tenant B | 1 | Security Engineer | P2-03 |

**AC конца дня:**
- [ ] `\d agent_decisions` показывает `Row security: enabled`
- [ ] `SET app.tenant = 'tenant-A'; SELECT * FROM agent_decisions` → только tenant A
- [ ] `SET app.tenant = 'tenant-B'; SELECT * FROM agent_decisions` → только tenant B
- [ ] App user с `BYPASSRLS=false`, superuser bypass для миграций
- [ ] `audit.audit_log` содержит запись о тестовом INSERT
- [ ] `tests/test_rls_isolation.py` 5/5 зелёные

**⚠️ Критично:** P2-03 требует ревью security инженером. Без RLS — compliance gap для SOC2.

---

### Чт, 23 июля — Phase 2 finish: HA + Read-replica routing

**Фокус дня:** CloudNativePG operator, primary/replica, router для SELECT.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-07** | CloudNativePG operator: 1 primary + 2 replicas, automatic failover 30s, `home-cluster-iac/` — манифесты, secrets, pgbouncer pooler | 4 | DevOps | P2-01b |
| 2 | **P2-04** | Connection pool tuning: `db/session.py` — pgbouncer-friendly (disable prepared statements, statement_timeout=30s, idle_in_transaction_session_timeout=60s). Лимиты: app=20, ml-engine=10, gpu-worker=5 | 2 | Backend | P2-07 |
| 3 | **P2-09** | Read-replica routing: `DATABASE_URL_READ` env, `db/router.py` автоматически роутит SELECT в replica (через `psycopg2.AsyncConnection` replica pool). Read-only transaction marker | 2 | Backend | P2-07 |

**AC конца дня:**
- [ ] `kubectl get cluster -n postgres` показывает `astrofin-pg` Cluster с `Instances: 3, Ready: 3`
- [ ] `kubectl delete pod astrofin-pg-1` → новый pod поднимается за < 30s, replica становится primary
- [ ] `db/router.py` route SELECT через `DATABASE_URL_READ` (логируем)
- [ ] `pgbench` на primary: 1000 TPS, на replica: 800 TPS (read-only)
- [ ] Connection refused при `pgbouncer=disable` и 100+ одновременных коннектах

**⚠️ Критично:** P2-07 требует Helm install CloudNativePG, dry-run на dev-кластере обязателен.

---

### Пт, 24 июля — Phase 2 finish: Performance tuning + Phase 3 start (Tracing backend)

**Фокус дня:** Vacuum tuning, slow-query log, и старт tracing-стека.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P2-13** | Vacuum/analyze policy: `tools/db_maintenance.sql` — autovacuum tuning per table (high-churn: `agent_decisions`, `audit_log` — scale factor 0.01, `ohlcv_bars` — 0.05) | 2 | Backend | P2-01b |
| 2 | **P2-10** | Slow-query log + autoindex: `pg_stat_statements` extension, `tools/slow_query_report.sh` (еженедельный), `tools/index_advisor.py` (suggest indexes based on seq_scan > 1000) | 2 | Backend | P2-13 |
| 3 | **P2-11** | Data integrity tests: hypothesis-based DB roundtrip, FK constraints проверяются, миграции идемпотентны (`tests/test_migration_idempotent.py`) | 1 | Backend | P2-08 (Sprint 2) |
| 4 | **P2-15** | Connection-per-tenant isolation (placeholder): namespace per tenant, separate DB user, separate connection pool (только дизайн, без реализации) | 1 | Backend | P2-03 |
| 5 | **P3-06a** | Tempo stack в `deploy/docker-compose.tempo.yml`: Tempo + OTel Collector + tail-sampling processor (10% head, 100% on error) | 2 | DevOps | — |

**AC конца дня:**
- [ ] `autovacuum_vacuum_scale_factor = 0.01` для `agent_decisions`, `audit_log` (проверить `\d+`)
- [ ] `pg_stat_statements` показывает top-10 slow queries
- [ ] `tools/index_advisor.py --report` генерирует markdown с предложениями
- [ ] `pytest tests/test_migration_idempotent.py` — 8/8 зелёные
- [ ] `docker compose -f deploy/docker-compose.tempo.yml up -d` — Tempo + OTel Collector работают
- [ ] OTel Collector endpoint `localhost:4317` принимает OTLP

**Команды для P3-06a:**
```bash
# Локальная проверка
docker compose -f deploy/docker-compose.tempo.yml up -d
docker logs -f astrofin-otel-collector 2>&1 | head -20
curl -X POST http://localhost:4318/v1/traces -H "Content-Type: application/json" -d @dev/trace_sample.json
# Должен вернуть 200, в Tempo UI (http://localhost:3200) — trace виден
```

---

## 📅 Выходные (опционально, не в capacity)

> Только если есть энергия или критичные fixes. Sprint goal НЕ зависит от выходных.

| # | ID | Задача | Часы | Зачем |
|---|----|--------|-----:|-------|
| 1 | **P2-02 cleanup** | Удалить FAISS-индексы (после dual-write периода) | 1 | Hygiene, освободить 5GB |
| 2 | **P2-11 expansion** | Добавить ещё 5 hypothesis-based тестов на edge cases | 2 | Coverage для DB |

---

## 📈 Burndown (ожидаемый)

| День | Запланировано (нарастающий итог) | Идеальный burndown | Реалистичный (pgvector surprises) |
|------|--------------------------------:|-------------------:|---------------------------------:|
| Пн | 10 ч (P2-02a/b + 3ч P3-01 background) | 10 | 10 (тяжёлый день, SLO — бумажная работа) |
| Вт | 18 ч (+P2-02c/d + benchmark) | 18 | 17 (HNSW index creation = +1ч) |
| Ср | 26 ч (+P2-03, P2-14 + 1ч tests) | 26 | 25 (RLS policy debugging = +1ч) |
| Чт | 34 ч (+P2-07, P2-04, P2-09) | 34 | 32 (CloudNativePG install + replica sync = +2ч) |
| Пт | 42 ч (+P2-13, P2-10, P2-11, P2-15) + 4ч (P3-06a) | 46 | 44 (Tempo config + tail-sampling = +2ч) |
| **Итого** | **66 ч (42 Phase 2 + 3 SLO + 4 Phase 3 tracing) + 17 ч carry-over/P3-15** | **66/66** | **64/66 (97 %)** |

> **Стратегия:** Sprint 3 commit высокий, т.к. критичные Phase 2 MUST должны быть закрыты до Phase 3 finish. Если что-то провисает — P2-15 и P3-15 можно перенести в Sprint 4.

---

## 📦 Definition of Done для Sprint 3

### Database
- [ ] pgvector extension работает, `documents.embedding vector(1536)` заполнен
- [ ] RAG search через pgvector возвращает top-5 с p95 < 80ms (100k docs)
- [ ] FAISS-индексы мигрированы (dual-write 1 неделю, затем `RAG_BACKEND=pgvector`)
- [ ] RLS включена на `agent_decisions`, `audit_log`, `backtest_runs`
- [ ] `SET app.tenant = 'X'` фильтрует данные корректно
- [ ] DB-level audit log триггеры работают, `audit.audit_log` partitioned by month
- [ ] CloudNativePG Cluster с 3 instances (1 primary + 2 replicas), failover < 30s
- [ ] `DATABASE_URL_READ` роутит SELECT в replica
- [ ] Connection pool tuned: app=20, ml-engine=10, gpu-worker=5
- [ ] Autovacuum scale_factor настроен per table
- [ ] `pg_stat_statements` + slow-query log + index-advisor работают
- [ ] Migration idempotency test suite зелёный
- [ ] docs/SLO.md утверждён, error budget calculation задокументирован

### Observability (start)
- [ ] Tempo + OTel Collector развёрнуты в `deploy/docker-compose.tempo.yml`
- [ ] Tail-sampling 10% head, 100% on error работает
- [ ] `localhost:4317` принимает OTLP traces
- [ ] Tempo UI (http://localhost:3200) показывает тестовый trace

### Качество
- [ ] `pytest -q` ≤ 12 fail (было 18 после Sprint 2, −6 от RAG/RLS/HA тестов)
- [ ] `ruff check` 0 errors, `bandit -r` без новых high
- [ ] Coverage ≥ 65 % для `core/`, `web/`, `orchestration/`, `db/`
- [ ] Code review пройден для всех PR

---

## 🔗 Зависимости от Sprint 2 (blockers)

| Зависит от | Sprint 3 задача | Что нужно от Sprint 2 |
|------------|----------------|----------------------|
| P2-01b (hypertable) | **P2-02**, **P2-03**, **P2-07**, **P2-13** | TimescaleDB extension активен |
| P2-05 (WAL-G backups) | **P2-07** (HA) | S3 backups для replica bootstrap |
| P2-06 (DR runbook) | **P2-15** | RLS-aware restore procedure |
| P2-08 (migration CI) | **P2-11** | Migration framework готов |
| P2-12 (TLS) | **Все DB задачи** | `sslmode=verify-full` enforced |
| P1-02 (SOPS) | **P2-04, P2-07** | Secrets расшифровываются в k8s |

> ⚠️ **Если Sprint 2 задержится** по P2-01b или P2-05, Sprint 3 нужно сдвинуть или перепланировать.

---

## 🔄 Carry-over Plan (если что-то не успеем)

| Задача | Приоритет | Куда идёт |
|--------|----------|-----------|
| P2-15 (tenant isolation) | 🟨 Low | Sprint 4 background (placeholder only) |
| P3-15 (APM для воркеров) | 🟨 Low | Sprint 4 (3ч, требует P3-07 готовое) |
| pgvector HNSW tuning | 🟧 Should | Sprint 4 (2ч, если p95 > 80ms) |
| Multi-region DB replication | 🟥 Must | Sprint 5 (P5-04, 8ч) |

**Sprint 4 preview:** Phase 3 finish (SLI exporters, recording rules, Alertmanager, Grafana v2, PII redaction, Sentry, chaos basics) + Phase 4 start (threat model, SAST/DAST CI, dependency scan, container scan).

---

## ⚠️ Риски Sprint 3

| # | Риск | Вероятность | Импакт | Mitigation |
|---|------|------------:|-------:|------------|
| **R-S3-1** | pgvector HNSW index creation на 1M docs занимает > 30 мин (блокирует миграцию) | 🟧 Средняя | 🟥 High | Использовать IVFFlat вместо HNSW для больших объёмов; batch creation |
| **R-S3-2** | RLS policy конфликтует с существующими запросами (orphaned rows, 500 errors) | 🟧 Средняя | 🟧 High | Feature flag `RLS_ENABLED=false` для быстрого rollback; staging-тесты перед prod |
| **R-S3-3** | CloudNativePG replica lag > 10s на write-heavy нагрузке | 🟨 Низкая | 🟧 Medium | Мониторинг `pg_stat_replication`; настройка `max_wal_size` |
| **R-S3-4** | Tempo storage быстро растёт (OTLP batch без sampling) | 🟧 Средняя | 🟨 Medium | Tail-sampling с самого начала; retention 7d traces |
| **R-S3-5** | pgvector performance p95 > 200ms (не 80ms) | 🟧 Средняя | 🟧 High | Benchmark в Пн; если плохо — увеличить `hnsw.ef_construction` или fallback на IVFFlat |
| **R-S3-6** | Connection pool exhaustion при HA failover | 🟨 Низкая | 🟧 Medium | pgbouncer connection multiplexing; retry logic в app |
| **R-S3-7** | Sprint 2 carry-over > 5ч (P2-05 restore test, P2-12 TLS) | 🟧 Средняя | 🟨 Medium | Sprint 3 commit 80% оставляет 16ч buffer |

### Топ-3 риска, требующих внимания в начале спринта

1. **R-S3-1 (pgvector HNSW performance)** — benchmark в Пн утро, не в Ср
2. **R-S3-2 (RLS conflicts)** — тесты с разными tenants в Вт, не в Чт
3. **R-S3-5 (pgvector p95)** — если > 80ms, пересмотреть стратегию в Ср

---

## 🔀 Параллелизм (если 2 FTE)

| Трек | Owner | Задачи | Часы |
|------|-------|--------|-----:|
| **A — Backend** | Senior Backend (1 FTE) | P2-02a/b/c/d, P2-04, P2-09, P2-10, P2-11, P2-13, P2-15 | 26 |
| **B — DevOps** | Senior DevOps (1 FTE) | P2-07, P3-06a | 10 |
| **C — Security** | Security Engineer (0.5 FTE) | P2-03, P2-14 | 7 |
| **D — Backend (tracing)** | Backend (0.5 FTE) | P3-15, integration support | 3 |

**2 FTE sprint commit:** 64 ч / 120 ч (53 %) — оба трека закроются в Ср-Чт, освобождая Пт для Sprint 4 planning.

**Если 1.5 FTE:** Backend full + DevOps part-time (0.5) + Security part-time (0.25).

---

## 🛠️ Команды для старта (Пн утро)

```bash
# 1. Синхронизироваться
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull origin release/1.0.0
workon astrofin

# 2. Создать Sprint 3 milestone (если ещё нет)
gh api repos/mahaasur13-sys/astrofin-sentinel-platform/milestones \
  -f title="Sprint 3 (DB finish + Observability start)" \
  -f due_on="2026-07-26T23:59:59Z"

# 3. Создать 18 issues (см. шаблон в .github/ISSUE_TEMPLATE/production-task.md)
gh issue create --title "[P2-02] pgvector RAG migration" --milestone "Sprint 3" ...

# 4. Утренний check
gh issue list --milestone "Sprint 2" --state all --json number,title,state | jq '.[] | select(.state=="open")'
cat /tmp/sprint2_retro.md 2>/dev/null
psql $DATABASE_URL -c "\dx" | grep -E "timescaledb|vector"
```

---

## 📊 Метрики успеха Sprint 3

| Метрика | Цель | Как измерить |
|---------|-----|--------------|
| Sprint commit | 80 % (64/80) | `gh issue list --milestone "Sprint 3" --state closed` |
| Carry-over из Sprint 2 | ≤ 3 задачи | Standup Пн |
| New critical bugs | 0 | `gh issue list --label critical --state open` |
| `pytest` pass rate | ≥ 96 % (было ~95 % после Sprint 2) | `pytest -q tests/ \| tail -1` |
| Coverage | ≥ 65 % (core/web/orchestration/db) | `coverage report` |
| pgvector p95 latency | < 80 ms (100k docs) | `tests/perf/test_pgvector_latency.py` |
| RLS isolation tests | 100 % pass | `pytest tests/test_rls_isolation.py` |
| Tempo OTel collector health | up | `curl http://localhost:8888/metrics` |
| HA failover time | < 30 s | `kubectl delete pod` → measure time |
| Read-replica routing % | ≥ 70 % SELECTs | logs `db/router.py` |

---

## 🤝 Ceremonies

| Событие | Время | Участники | Длительность |
|---------|-------|-----------|-------------:|
| **Sprint 3 Planning** | Пт 17 июля 16:00 | Вся команда | 1 ч |
| **Daily Standup** | Пн–Пт 09:30 | Backend + DevOps + Security | 15 мин |
| **Mid-sprint Check** | Ср 14:00 | Backend + DevOps | 30 мин (burndown review) |
| **Sprint Review** | Пт 24 июля 16:00 | + Stakeholders | 1 ч |
| **Sprint 3 Retro** | Пт 24 июля 17:00 | Вся команда | 1 ч |
| **Sprint 4 Planning** | Пт 24 июля 18:00 | Вся команда | 1 ч |

**Sprint Review demo agenda:**
1. RAG search через pgvector (live demo, top-5 results < 80ms)
2. RLS в действии (tenant A не видит tenant B)
3. CloudNativePG HA: kill pod, watch failover < 30s
4. Read-replica routing: запросы идут на replica (логи)
5. Tempo UI: trace запроса от web → orchestrator → 13 agents → DB
6. DB-level audit log: trigger сработал на INSERT

---

## 📎 Приложение A. Carry-over Checklist из Sprint 2

Заполнить в начале Sprint 3 (Пн утро):

```
Sprint 2 Carry-over
═══════════════════════════════════════════════
□ P2-01b (hypertable) → Done? Y/N
□ P2-05 (WAL-G S3 backups) → Done? Y/N
□ P2-05b (backup verify CI) → Done? Y/N
□ P2-06 (DR runbook) → Done? Y/N
□ P2-08 (migration CI-gate) → Done? Y/N
□ P2-12 (TLS for Postgres) → Done? Y/N
═══════════════════════════════════════════════
Total carry-over: __/6

If carry-over > 3: reduce Sprint 3 scope (drop P2-15)
If carry-over = 0: add P3-04 (Alertmanager) preview to Sprint 3
```

---

## 📎 Приложение B. Где искать что

| Что | Где |
|-----|-----|
| Sprint 2 issues | `gh issue list --milestone "Sprint 2"` |
| Sprint 2 retro | `/tmp/sprint2_retro.md` (создаётся в конце Sprint 2) |
| MoSCoW-приоритезация | `MOSCOW_PRIORITIZATION.md` |
| Полный бэклог | `PRODUCTION_BACKLOG.md` |
| Week 1 sprint | `SPRINT_1.md` |
| Week 2 sprint | `SPRINT_2.md` |
| Week 3 sprint (этот) | `SPRINT_3.md` |
| DB Architecture | `knowledge/DB_ARCHITECTURE_PROMPT.md` |
| pgvector docs | https://github.com/pgvector/pgvector |
| CloudNativePG docs | https://cloudnative-pg.io/documentation/ |
| Tempo docs | https://grafana.com/docs/tempo/latest/ |

---

## ✅ Готовность к старту

Pre-flight checklist (Пн 09:00):

- [ ] `gh auth status` — logged in
- [ ] `git status` — clean, on `release/1.0.0`
- [ ] `pytest -q tests/ | tail -1` — pass rate из Sprint 2
- [ ] `gh issue list --milestone "Sprint 2" --state closed | wc -l` — Sprint 2 velocity
- [ ] Прочитать `SPRINT_2.md` и `MOSCOW_PRIORITIZATION.md`
- [ ] Проверить `Sprint 2 retro` (если был)
- [ ] `Sprint 3 milestone` создан в GitHub
- [ ] Slack/email уведомление команде: "Sprint 3 starts"
- [ ] pgvector extension протестирован на dev-кластере (предварительно)

---

> 📌 **Этот документ — операционный план на неделю.** Использовать как checklist на daily standup. После Sprint 3 retro обновить на основе реальной velocity.

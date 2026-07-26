# 🏃 Sprint G-2 — Hardening Start (04.08 – 08.08)

> **Спринт:** G-2 (Неделя 2 Фазы 7)
> **Цель:** Load test baseline, SLO calibration, документация к GA
> **Definition of Done:** Load test отчёт, SLO зафиксированы, release notes черновик

---

## Backlog (6 задач, ~15 ч)

### 1. G-08: Нагрузочное тестирование (Locust) 🔴 P1 • 4h

**План:**
1. Развернуть staging (G-03 должен быть готов)
2. Запустить `locust -f locustfile_sprint_e.py --host http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m`
3. Метрики для baseline:
   - `/api/v1/agent/run` → p50/p95/p99 latency
   - RPS (requests/sec)
   - Failure rate
   - CPU/memory при 50 concurrent users
4. Записать в `docs/performance/load-test-2026-08.md`

**Acceptance:**
- [ ] Baseline зафиксирован
- [ ] Нет ошибок 5xx
- [ ] p95 < 2s для agent/run

---

### 2. G-09: SLO/SLI калибровка 🔴 P1 • 3h

**План:**
1. Проверить Prometheus recording rules (`prometheus/recording_rules.yml`)
2. Снять метрики со staging за 24h:
   - Availability (up)
   - Latency (histogram_quantile)
   - Error rate
3. Выставить реалистичный SLO:
   - Availability: 99.0% (неделя) → 99.5% (месяц) как aspirational
   - Latency: p95 < 3s
   - Error rate: < 1%
4. Обновить `monitoring/slo.yml`

**Acceptance:** SLO dashboard в Grafana показывает compliance

---

### 3. G-10: Runbook — 2 новых алерта 🔴 P1 • 2h

**План:**
1. Создать `docs/runbooks/ALERT_PostgresConnectionPoolExhausted.md`:
   - Симптомы: pool exhausted в логах
   - Диагностика: `SELECT count(*) FROM pg_stat_activity`
   - Решение: увеличить pool size / убить idle connections / перезапустить app
2. Создать `docs/runbooks/ALERT_RedisMemoryHigh.md`:
   - Симптомы: Redis OOM, evictions
   - Диагностика: `redis-cli INFO memory`
   - Решение: `FLUSHDB` (осторожно) / увеличить maxmemory / добавить TTL

**Acceptance:** Оба runbook'а с секциями Symptoms → Diagnosis → Resolution

---

### 4. G-11: Release Notes v1.0.0 (черновик) 🔴 P1 • 3h

**План:**
1. Собрать список PR'ов: `gh pr list --state merged --base master --limit 50`
2. Категоризировать:
   - 🚀 Features (13 agents, Meta-RL, dashboard, Telegram bot)
   - 🔧 Bug Fixes (flake8→ruff, CI stabilisation, arch linter)
   - 🏗️ Infrastructure (TimescaleDB, WAL-G, Loki/Promtail, PII scrubber)
   - 📚 Documentation (3 runbooks, incident response, CHANGELOG)
   - ⚠️ Breaking Changes (submodules inlined, data_room/ required)
3. Upgrade guide: как перейти с beta на GA

**Acceptance:** Файл `docs/RELEASE_NOTES_v1.0.0.md` с 5 секциями

---

### 5. G-12: Актуализировать ARCHITECTURE.md 🟡 P2 • 2h

**План:**
1. Добавить секцию «Infrastructure»:
   - TimescaleDB: hypertables, compression policy, asyncpg pool
   - WAL-G: backup sidecar, restore procedure
   - PII scrubber: какие поля, когда срабатывает
2. Обновить диаграмму данных (data flow от API → agents → DB → dashboard)
3. Отразить circuit breakers (CoinGecko, Ephemeris, LLM) и rate limiting

**Acceptance:** `docs/ARCHITECTURE.md` содержит infrastructure-секцию

---

### 6. G-13: GitHub Release draft 🟡 P2 • 1h

**План:**
1. `gh release create v1.0.0 --draft --title "v1.0.0 Aurora Prime" --notes-file docs/RELEASE_NOTES_v1.0.0.md`
2. Приаттачить артефакты (если есть бинарные сборки)
3. Проверить авто-generated changelog (из PR titles)

**Acceptance:** Draft release виден в GitHub Releases

---

## Sprint Board

| Статус | Задача | Assignee | Estimate |
|--------|--------|----------|----------|
| ⬜ Todo | G-08 Load test | felix | 4h |
| ⬜ Todo | G-09 SLO calibration | felix | 3h |
| ⬜ Todo | G-10 Runbooks | felix | 2h |
| ⬜ Todo | G-11 Release notes | felix | 3h |
| ⬜ Todo | G-12 ARCHITECTURE.md | felix | 2h |
| ⬜ Todo | G-13 Draft release | felix | 1h |

---

## Daily Standup

| День | Фокус | Ожидаемый результат |
|------|-------|---------------------|
| Пн 04.08 | G-08 (load test start) | Locust запущен, baseline снимается |
| Вт 05.08 | G-08 + G-09 (load + SLO) | load test отчёт + SLO target |
| Ср 06.08 | G-10 + G-11 (runbooks + release notes) | 2 runbooks + черновик |
| Чт 07.08 | G-12 + G-13 (docs + draft) | ARCHITECTURE обновлён |
| Пт 08.08 | Review + buffer | sprint G-2 closed |

---

> 📎 Связано: `DEVELOPMENT_PLAN_v1.1.0.md` · `SPRINT_1.md` · `RELEASE_PLAN_v1.0.0.md`

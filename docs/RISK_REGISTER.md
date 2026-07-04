# 🛡️ Risk Register — AstroFin Sentinel v1.0.0 GA

> **Status:** ✅ Active (last reviewed 2026-07-04)
> **Owner:** Tech Lead (`@asurdev`)
> **Review cadence:** Weekly (Mon standup) + on-incident + post-sprint
> **Гэп к релизу:** 21 % (74 % → 95 % production-readiness по `PRODUCTION_BACKLOG.md`)

---

## 1. 🎯 Назначение

**Risk Register** — единый источник правды по рискам проекта. Используется для:

- **Приоритизации работ** — Critical risks → MUST в спринте
- **PRR (Production Readiness Review)** — gate-check на P5-10
- **On-call briefing** — новый дежурный читает перед сменой
- **Stakeholder reporting** — топ-3 риска в `EXECUTIVE_SUMMARY.md`

**Отличие от** `PRODUCTION_BACKLOG.md` §10:
- Бэклог = риски + **задачи** (P0–P5)
- Risk Register = **только риски** + митигация + owner + status tracking

---

## 2. 📊 Risk Heat Map

```markdown
                  Impact →
            Low      Medium     High      Critical
P       ┌──────────┬──────────┬──────────┬──────────┐
r  Low  │ 🟢 Accept│ 🟢 Accept│ 🟡 Monit.│ 🟡 Monit.│
o       ├──────────┼──────────┼──────────┼──────────┤
b  Med  │ 🟢 Accept│ 🟡 Monit.│ 🟠 Plan  │ 🔴 Act  │
a       ├──────────┼──────────┼──────────┼──────────┤
b  High │ 🟡 Monit.│ 🟠 Plan  │ 🔴 Act  │ 🚨 IMMED│
.       ├──────────┼──────────┼──────────┼──────────┤
↓  Crit │ 🟠 Plan  │ 🔴 Act  │ 🚨 IMMED│ 🚨 IMMED│
        └──────────┴──────────┴──────────┴──────────┘
```

**Распределение по heat map (на 2026-07-04):**

| Зона | Кол-во | % |
|---|---:|---:|
| 🟢 Accept (Low-Low) | 0 | 0 % |
| 🟡 Monitor (Med-High, Low-Crit) | 3 | 23 % |
| 🟠 Plan (High-Med, Crit-Low) | 5 | 38 % |
| 🔴 Act (High-High, Crit-Med) | 4 | 31 % |
| 🚨 Immediate (Crit-High, Crit-Crit) | 1 | 8 % |
| **Total** | **13** | **100 %** |

---

## 3. 🔥 Top-13 Risks (детально)

### R-01: Submodule crisis блокирует push (R1 из бэклога) 🚨

| Поле | Значение |
|---|---|
| **Категория** | Git / Infrastructure |
| **Вероятность** | 🟥 Высокая (4/5) |
| **Импакт** | 🟥 Критический (5/5) |
| **Heat score** | 20/25 (Immediate) |
| **Владелец** | DevOps |
| **Status** | 🟠 Plan (mitigation in progress) |
| **Sprint** | W1 (P0-03) + W5 (P5-13) |
| **Митигация** | P0-03 dry-run + P5-13 execute; lock 4 submodules в README, чтобы не было 404 |

**Триггер (если случится):**
- `git push origin master` → HTTP 404 на submodule URL
- CI fail на `actions/checkout@v4` с `submodule 'foo' not found`

**План реакции:**
1. Откат к последнему зелёному commit (`git reset --hard origin/master@<last-green>`)
2. Включить P0-03 dry-run немедленно (если не сделан)
3. Если критично для GA — `git submodule deinit` + `git rm --cached`, переход в subtree

**Связанные:** P0-03, P5-11, P5-13

---

### R-02: Bus factor = 1 (R2 из бэклога) 🚨

| Поле | Значение |
|---|---|
| **Категория** | Process / People |
| **Вероятность** | 🟧 Средняя (3/5) — вероятность ухода/volunteer на больничный |
| **Импакт** | 🟥 Критический (5/5) — нет knowledge transfer |
| **Heat score** | 15/25 (Act) |
| **Владелец** | Tech Lead |
| **Status** | 🟠 Plan (P4-10 в W3-W4) |
| **Спринт** | W3-W4 (P4-10) |
| **Митигация** | P4-10: пригласить 1-2 человек, pair-programming на critical modules (orchestrator, security, db) |

**Триггер:** уход/volunteer ≥ 1 неделя, или burnout warning.

**План реакции:**
1. Hot-fix: 2-я линия поддержки может чинить только через RUNBOOK.md + pre-approved PRs
2. Cold-fix: 4-6 недель набора нового senior + ramp-up
3. Краткосрочно: contractor на 2-4 недели для покрытия

**Связанные:** P4-10, P5-08 (on-call rotation нужен ≥ 2 человека)

---

### R-03: 26 failing tests не расследованы (R5) 🟥

| Поле | Значение |
|---|---|
| **Категория** | Testing / CI |
| **Вероятность** | 🟥 Высокая (4/5) — уже failing в master |
| **Импакт** | 🟧 Высокий (4/5) — нельзя merge без green CI |
| **Heat score** | 16/25 (Act) |
| **Владелец** | Backend |
| **Status** | 🔴 Act (Sprint 1 W1) |
| **Спринт** | W1 (P0-01) |
| **Митигация** | P0-01: расследовать top-5 blockers, починить, открыть issue на остальные 21 |

**Триггер:** `pytest -q` показывает > 21 fail после W1.

**План реакции:**
1. Sprint carry-over: оставшиеся 21 fail переходят в W2-W3 как background tasks
2. Если к W3-end > 12 fail — критичный стоп-сигнал, рескейлинг scope

**Связанные:** P0-01, DoD для каждого спринта (pytest baseline)

---

### R-04: Pen-test выявит критические уязвимости (R17) 🟥

| Поле | Значение |
|---|---|
| **Категория** | Security / Compliance |
| **Вероятность** | 🟧 Средняя (3/5) |
| **Импакт** | 🟥 Критический (5/5) — block GA |
| **Heat score** | 15/25 (Act) |
| **Владелец** | Security Engineer (part-time) |
| **Status** | 🟠 Plan (P4-02 в W5) |
| **Спринт** | W5 (P4-02) |
| **Митигация** | P4-02: pen-test в начале W5, 2 недели на фикс критических до GA |

**Триггер:** pen-test report содержит ≥ 1 Critical или ≥ 3 High.

**План реакции:**
1. Если Critical → блок GA, hot-fix в течение 1-2 дней, re-test
2. Если High ≥ 3 → fix-or-waiver meeting, минимум 2 недели на фикс
3. Если Medium → документируем в `KNOWN_ISSUES.md`, план в Sprint 6

**Связанные:** P4-01 (threat model), P4-03 (SAST), P4-02 (pen-test)

---

### R-05: pgvector embeddings раздувают БД (R11) 🟧

| Поле | Значение |
|---|---|
| **Категория** | Database / Performance |
| **Вероятность** | 🟧 Средняя (3/5) — реально при 1M+ docs |
| **Импакт** | 🟧 Высокий (4/5) — backup size растёт, restore медленнее |
| **Heat score** | 12/25 (Plan) |
| **Владелец** | Backend |
| **Status** | 🟠 Plan (W3 P2-02) |
| **Спринт** | W3 (P2-02) |
| **Митигация** | P2-02: использовать `halfvec(1536)` вместо `vector(1536)` (3GB вместо 6GB на 1M docs) + IVF index + мониторинг размера |

**Триггер:** `pg_database_size('astrofin')` > 50 GB или `ohlcv_bars` size > 30 GB.

**План реакции:**
1. Quantize embeddings: `halfvec` (float16) → 50 % экономии
2. Vacuum aggressive: `VACUUM FULL` на старых чанках TimescaleDB
3. Рассмотреть partitioning FAISS-индекса по годам (после 1M docs)

**Связанные:** P2-02, P2-10 (slow-query log)

---

### R-06: JWT-миграция ломает существующих клиентов (R10) 🟧

| Поле | Значение |
|---|---|
| **Категория** | API / Backward compat |
| **Вероятность** | 🟧 Средняя (3/5) |
| **Импакт** | 🟧 Высокий (4/5) — клиенты получают 401 |
| **Heat score** | 12/25 (Plan) |
| **Владелец** | Backend |
| **Status** | 🟡 Monitor (dual-mode в W1 P1-03) |
| **Спринт** | W1 (P1-03), W2 (P1-04) |
| **Митигация** | P1-03: dual-mode (X-API-Key + Bearer) на 2 недели, changelog, deprecation notice |

**Триггер:** spike 401 errors в первые 24ч после JWT-only.

**План реакции:**
1. Rollback на dual-mode (config flag: `AUTH_MODE=dual`)
2. Email клиентам с предупреждением
3. Re-schedule JWT-only на +1 неделю

**Связанные:** P1-03, P1-04

---

### R-07: Canary deploy требует Argo Rollouts (R12) 🟧

| Поле | Значение |
|---|---|
| **Категория** | Deploy / Infrastructure |
| **Вероятность** | 🟧 Средняя (3/5) — кластер может не иметь operator |
| **Импакт** | 🟨 Средний (3/5) — откат на rolling update |
| **Heat score** | 9/25 (Plan) |
| **Владелец** | DevOps |
| **Status** | 🟠 Plan (W5 P5-01) |
| **Спринт** | W5 (P5-01) |
| **Митигация** | P5-01: сначала simple `Deployment` strategy change (`maxSurge=0, maxUnavailable=1`), потом миграция на Argo Rollouts |

**Триггер:** Argo Rollouts CRD не установлен в кластере.

**План реакции:**
1. Helm install Argo Rollouts (если есть Helm-чарт)
2. Fallback: native k8s RollingUpdate с `maxSurge=0` + ручной rollback через `kubectl rollout undo`

**Связанные:** P5-01, P5-02

---

### R-08: On-call без backup (R13) 🟧

| Поле | Значение |
|---|---|
| **Категория** | Process / People |
| **Вероятность** | 🟧 Средняя (3/5) |
| **Импакт** | 🟧 Высокий (4/5) — если оба unavailable, инцидент эскалируется в Tech Lead |
| **Heat score** | 12/25 (Plan) |
| **Владелец** | Tech Lead |
| **Status** | 🟠 Plan (P4-10 + P5-08) |
| **Спринт** | W3-W4 (P4-10), W5 (P5-08) |
| **Митигация** | P4-10: привлечь ещё 1-2 человек, shadow-on-call обязателен 2 недели |

**Триггер:** 1 из 2 on-call unavailable > 24ч.

**План реакции:**
1. Shadow-on-call дежурит (P5-08)
2. Tech Lead как escalation
3. Если оба unavailable → инцидент-менеджер = Tech Lead

**Связанные:** P4-10, P5-08

---

### R-09: AstroFin-sentinel-v5 submodule = snapshot (R3) 🟨

| Поле | Значение |
|---|---|
| **Категория** | Git / Architecture |
| **Вероятность** | 🟧 Средняя (3/5) |
| **Импакт** | 🟨 Средний (3/5) — развитие v6 блокировано |
| **Heat score** | 9/25 (Plan) |
| **Владелец** | DevOps |
| **Status** | 🟡 Monitor (P5-11 в W5) |
| **Спринт** | W5 (P5-11) |
| **Митигация** | P5-11: мигрировать submodule → root directory |

**Триггер:** попытка push в submodule → 404 на upstream.

**План реакции:** см. R-01 (единая git-стратегия).

**Связанные:** P5-11

---

### R-10: Audit.py.bak-006 с утечкой секрета (R4) 🟨

| Поле | Значение |
|---|---|
| **Категория** | Security / Secrets |
| **Вероятность** | 🟨 Низкая (1/5) — секрет уже в GitHub, но VSELM_API_KEY не активен |
| **Импакт** | 🟥 Критический (5/5) — если активен, compromise |
| **Heat score** | 5/25 (Monitor) |
| **Владелец** | Backend |
| **Status** | 🟢 Accept (митигирован P0-02) |
| **Спринт** | W1 (P0-02) |
| **Митигация** | P0-02: удалить + `.gitignore`; проверить `git log -p` на историю; ротация ключей |

**Триггер:** VSELM_API_KEY активен, видны аномальные запросы.

**План реакции:**
1. Немедленная ротация ключа на vsellm.ru
2. Проверка access logs за 90 дней
3. Incident report в `docs/postmortems/`

**Связанные:** P0-02, P4-19 (secret rotation policy)

---

### R-11: Performance baseline выявит архитектурные проблемы (R20) 🟧

| Поле | Значение |
|---|---|
| **Категория** | Performance / Architecture |
| **Вероятность** | 🟧 Средняя (3/5) — 13 агентов могут быть sequential |
| **Импакт** | 🟧 Высокий (4/5) — p95 > 1s → fail SLO |
| **Heat score** | 12/25 (Plan) |
| **Владелец** | Backend |
| **Status** | 🟠 Plan (P3-12 + P5-05) |
| **Спринт** | W4 (P3-12), W5 (P5-05) |
| **Митигация** | P3-12: 2 дня на профилирование + refactor orchestrator при необходимости |

**Триггер:** Locust p95 > 1s на 200 users.

**План реакции:**
1. Profiling: cProfile + flame graph → найти bottleneck
2. Parallel agents: заменить sequential loop на `asyncio.gather` для независимых агентов
3. Caching: Redis cache для RAG retrieval (1-5 мин TTL)

**Связанные:** P3-12, P5-05, SLO.md (будет создан в W3)

---

### R-12: Cosign keyless (SLSA L3) может не пройти (R14) 🟨

| Поле | Значение |
|---|---|
| **Категория** | Security / Supply chain |
| **Вероятность** | 🟨 Низкая (2/5) — обычно работает |
| **Импакт** | 🟨 Средний (3/5) — fallback на key-based |
| **Heat score** | 6/25 (Monitor) |
| **Владелец** | DevOps |
| **Status** | 🟡 Monitor (P4-06 в W5) |
| **Спринт** | W5 (P4-06) |
| **Митигация** | P4-06: fallback на key-based cosign с quarterly rotation |

**Триггер:** admission controller reject pull.

**План реакции:** переключение на key-based cosign, документирование процедуры.

**Связанные:** P4-05, P4-06

---

### R-13: Sentry может стоить дорого при высоком error rate (R15) 🟨

| Поле | Значение |
|---|---|
| **Категория** | Cost / Observability |
| **Вероятность** | 🟨 Низкая (2/5) |
| **Импакт** | 🟨 Средний (3/5) — $200-500/мес |
| **Heat score** | 6/25 (Monitor) |
| **Владелец** | DevOps |
| **Status** | 🟡 Monitor (P3-13 в W4) |
| **Спринт** | W4 (P3-13) |
| **Митигация** | P3-13: sample rate 10 % в prod, 100 % только для 5xx |

**Триггер:** Sentry invoice > $300/мес.

**План реакции:** rate-limit на 5 %, plan upgrade или self-hosted (Sentry OSS).

**Связанные:** P3-13, P3-14 (FinOps)

---

## 4. 🛡️ Mitigation Status Summary

| ID | Heat | Owner | Status | Sprint | ETA |
|---|---|---|---|---|---|
| R-01 | 🚨 20 | DevOps | 🟠 Plan | W1+W5 | 2026-08-09 |
| R-02 | 🔴 15 | Tech Lead | 🟠 Plan | W3-W4 | 2026-08-02 |
| R-03 | 🔴 16 | Backend | 🔴 Act | W1 | 2026-07-12 |
| R-04 | 🔴 15 | Security | 🟠 Plan | W5 | 2026-08-05 |
| R-05 | 🟠 12 | Backend | 🟠 Plan | W3 | 2026-07-26 |
| R-06 | 🟠 12 | Backend | 🟡 Monitor | W1-W2 | 2026-07-19 |
| R-07 | 🟠 9 | DevOps | 🟠 Plan | W5 | 2026-08-09 |
| R-08 | 🟠 12 | Tech Lead | 🟠 Plan | W3-W5 | 2026-08-09 |
| R-09 | 🟠 9 | DevOps | 🟡 Monitor | W5 | 2026-08-09 |
| R-10 | 🟡 5 | Backend | 🟢 Accept | W1 | ✅ 2026-07-12 |
| R-11 | 🟠 12 | Backend | 🟠 Plan | W4-W5 | 2026-08-09 |
| R-12 | 🟡 6 | DevOps | 🟡 Monitor | W5 | 2026-08-09 |
| R-13 | 🟡 6 | DevOps | 🟡 Monitor | W4 | 2026-07-26 |

**Overall:** 1 Immediate, 4 Act, 5 Plan, 3 Monitor, 1 Accept. До W5-end все должны быть Plan/Monitor/Accept.

---

## 5. 🔗 Risk ↔ Task Cross-Reference

| Risk | Tasks | Cross-refs |
|---|---|---|
| R-01 | P0-03, P5-13, P5-11 | `SPRINT_1.md` (W1), `SPRINT_5.md` (W5) |
| R-02 | P4-10, P5-08 | `SPRINT_4.md` (W4), `SPRINT_5.md` (W5) |
| R-03 | P0-01 | `SPRINT_1.md` (W1) |
| R-04 | P4-01, P4-02, P4-03 | `SPRINT_5.md` (W5) |
| R-05 | P2-02, P2-10 | `SPRINT_3.md` (W3) |
| R-06 | P1-03, P1-04 | `SPRINT_1.md` (W1), `SPRINT_2.md` (W2) |
| R-07 | P5-01, P5-02 | `SPRINT_5.md` (W5) |
| R-08 | P4-10, P5-08 | `SPRINT_4.md` (W4), `SPRINT_5.md` (W5) |
| R-09 | P5-11 | `SPRINT_5.md` (W5) |
| R-10 | P0-02, P4-19 | `SPRINT_1.md` (W1) |
| R-11 | P3-12, P5-05 | `SPRINT_4.md` (W4), `SPRINT_5.md` (W5) |
| R-12 | P4-05, P4-06 | `SPRINT_5.md` (W5) |
| R-13 | P3-13, P3-14 | `SPRINT_4.md` (W4) |

---

## 6. 📈 Risk Review Cadence

| Событие | Действие | Owner |
|---|---|---|
| **Daily standup** | Blockers → update R-01/03/04 | Tech Lead |
| **Weekly Mon** | Heat map review, новые риски, retire resolved | Tech Lead |
| **Mid-sprint Wed** | Re-score heat после прогресса | Tech Lead |
| **Sprint review** | Risk report to stakeholders (top-3) | Tech Lead |
| **Post-incident** | Новый риск или upgrade существующего | Incident Lead |
| **Sprint 5 PRR** | Финальный review перед GA | Tech Lead + Stakeholders |

---

## 7. 🔗 Связанные документы

- `file 'PRODUCTION_BACKLOG.md'` §10 — первоисточник R1–R20
- `file 'MOSCOW_PRIORITIZATION.md'` — какие риски = MUST
- `file 'SPRINT_*.md'` — execution plan для mitigation
- `file 'docs/DEPENDENCIES.md'` — task-level dependencies (комплимент к рискам)
- `file 'docs/DEFINITION_OF_DONE.md'` — критерии "risk closed"
- `file 'docs/RELEASE_CHECKLIST.md'` — go/no-go gate использует risk status
- `file 'docs/RUNBOOK.md'` — operational response на инциденты

---

> 📌 **Этот документ обновляется еженедельно** (Mon standup). После W5 (2026-08-09) — переход в steady-state: monthly review.

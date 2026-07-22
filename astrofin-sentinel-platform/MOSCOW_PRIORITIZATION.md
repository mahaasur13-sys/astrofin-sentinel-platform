# 🎯 AstroFin Sentinel — MoSCoW-приоритезация (87 задач)

> **Дата:** 2026-07-03
> **Источник:** `PRODUCTION_BACKLOG.md` (87 задач, Phase 0–5)
> **Цель:** Чётко разделить MUST / SHOULD / COULD / WON'T для первого production-релиза v1.0.0
> **Метод:** каждая задача оценена по 3 критериям (блокирует ли GA, есть ли workaround, цена пропуска)

---

## 📊 Сводка по MoSCoW

| Категория | Кол-во | % | Часы | Что значит |
|---|---:|---:|---:|---|
| 🟥 **MUST have** | **31** | 36 % | **118 ч** | Без этих задач GA невозможен. Блокеры прода, безопасности, базовой функциональности. |
| 🟧 **SHOULD have** | **35** | 40 % | **157 ч** | Важны, но не блокируют. Можно выкатить v1.0.0 и доработать в v1.0.1 / v1.1.0. |
| 🟨 **COULD have** | **17** | 20 % | **52 ч** | Делаем если останется время/ресурс. Чистый nice-to-have. |
| ⬜ **WON'T (this release)** | **4** | 4 % | **10 ч** | Осознанно отложено в v1.2+. Требуют отдельного планирования. |
| **ИТОГО** | **87** | 100 % | **337 ч** | |

**GA v1.0.0 (MUST + SHOULD) = 66 задач / 275 ч ≈ 34 дня (1 FTE) / 17 дней (2 FTE) / 12 дней (3 FTE)**

> ⚠️ **Рекомендация:** выпустить v1.0.0 с **MUST (31 задача / 118 ч ≈ 15 дней 1 FTE / 8 дней 2 FTE)**, SHOULD катить в v1.0.1 сразу после (2-3 нед), COULD — в v1.1.0 через 2-3 мес.

---

## 🟥 MUST HAVE (31 задача, 118 ч) — без этого GA невозможен

> **Критерий:** Без задачи нельзя выпустить v1.0.0 — нарушает безопасность, ломает CI, делает невозможным deploy, либо regulatory/compliance blocker.

### Phase 0 — MUST (7 задач, 20 ч)

| ID | Название | Часы | Почему MUST |
|----|----------|-----:|-------------|
| **P0-01** | Расследовать 26 failing tests | 6 | Без green tests нельзя мерджить в `release/1.0.0`. CI красный. PRR не подпишет. |
| **P0-01.b** | Починить top-3 broken imports | 2 | Без этого P0-01 не довести до конца. |
| **P0-02** | Удалить `.bak` файлы + `.gitignore` | 1 | В репо `audit.py.bak-006` (даже если placeholder, R4 critical). Утечка секрета = incident. |
| **P0-03** | Submodule→subtree migration plan | 4 | **Без этого push в GitHub заблокирован.** 4 из 5 submodule 404. R1 critical. |
| **P0-04** | Создать `release/1.0.0` + branch protection | 1 | Без защищённой ветки невозможен релизный процесс. |
| **P0-05** | Зафиксировать `requirements.lock` | 3 | Без lock-файла CI drift = разные версии в dev/prod = баги. |
| **P0-06** | Bandit sweep + classification | 3 | Security gate перед GA. 6 high — могут быть не false positive. |

**Subtotal Phase 0 MUST: 20 ч**

### Phase 1 — MUST (8 задач, 23 ч)

| ID | Название | Часы | Почему MUST |
|----|----------|-----:|-------------|
| **P1-01** | Production `.env.prod.example` | 3 | Без шаблона в прод утекут secrets, либо приложение не стартует. |
| **P1-02** | SOPS-интеграция для секретов | 6 | **Без шифрования секретов нельзя в прод.** G1 critical. |
| **P1-03** | JWT вместо статичного API_KEY | 8 | Static API_KEY = нет ротации, нет per-user, нет audit. R10 high. |
| **P1-05** | Pydantic v2 input validation | 6 | Без input validation — CVE class bugs. P0 for security. |
| **P1-06** | CORS whitelist | 1 | `Access-Control-Allow-Origin: *` в прод = любой домен может дёргать API. |
| **P1-08** | Глобальный error handler (без stack traces) | 3 | Stack trace в response = утечка внутренней структуры, CVE. |
| **P1-13** | Разделить `/livez` и `/readyz` | 2 | K8s readiness probe должен отличать "процесс жив" от "может принимать трафик". Без этого rolling deploy ломается. |
| **P1-15** | `secrets.compare_digest` для HMAC | 1 | `==` для HMAC = timing attack. 1 час работы, убирает CVE class. |

**Subtotal Phase 1 MUST: 30 ч** *(вместе с P0 = 50 ч)*

### Phase 2 — MUST (6 задач, 28 ч)

| ID | Название | Часы | Почему MUST |
|----|----------|-----:|-------------|
| **P2-01** | TimescaleDB extension + hypertable | 6 | Без time-series DB не масштабируется история. G2 critical. |
| **P2-02** | pgvector + RAG-миграция | 8 | Без vector DB RAG не работает в проде. G3 critical. |
| **P2-05** | S3 backups через WAL-G | 6 | **Без бэкапа = первый серьёзный DB-инцидент = потеря данных.** G6 critical. |
| **P2-06** | DR runbook | 4 | Без runbook невозможно восстановиться в инциденте. G7 high. |
| **P2-08** | Schema migrations CI-gate | 3 | Без gate в CI/migrations — сломанные миграции в проде. |
| **P2-12** | TLS для Postgres | 2 | `ssl=disable` в проде = перехват трафика. Compliance blocker. |

**Subtotal Phase 2 MUST: 29 ч** *(накопительно 79 ч)*

### Phase 3 — MUST (4 задачи, 14 ч)

| ID | Название | Часы | Почему MUST |
|----|----------|-----:|-------------|
| **P3-01** | SLO/SLI определения | 3 | Без SLO невозможно настроить alerts, on-call, error budget. G17 high. |
| **P3-03** | Prometheus recording rules + SLO alerts | 4 | Без alerts инциденты не отлавливаются. Без recording rules — false positive alert storm. |
| **P3-04** | Alertmanager routing tree | 3 | Без routing alerts не доходят до on-call. PagerDuty/Telegram не настроены. |
| **P3-07** | Trace-propagation fix | 4 | Сейчас `traceparent` теряется между async tasks. Без фикса distributed tracing = фикция. |

**Subtotal Phase 3 MUST: 14 ч** *(накопительно 93 ч)*

### Phase 4 — MUST (4 задачи, 22 ч)

| ID | Название | Часы | Почему MUST |
|----|----------|-----:|-------------|
| **P4-01** | Threat model STRIDE | 6 | Без threat model невозможно понять attack surface. Compliance блокер для SOC2. |
| **P4-04** | Dependency vulnerability scan | 3 | pip-audit = gate перед GA. |
| **P4-05** | Container image scan (trivy) | 4 | trivy = gate перед GA. Critical CVE в base image = блокер. |
| **P4-10** | Bus factor mitigation | 4 | **Bus factor = 1 = уход разработчика = смерть проекта.** R2 critical. |

**Subtotal Phase 4 MUST: 17 ч** *(накопительно 110 ч)*

### Phase 5 — MUST (2 задачи, 8 ч)

| ID | Название | Часы | Почему MUST |
|----|----------|-----:|-------------|
| **P5-01** | Canary/Blue-Green deploy | 6 | **Без canary deploy = невозможно откатить быстро.** Прямо в прод = даунтайм при баге. |
| **P5-10** | Production Readiness Review meeting | 2 | **PRR = go/no-go сигнал. Без подписанного PRR — не выпускаем.** |

**Subtotal Phase 5 MUST: 8 ч** *(накопительно 118 ч)*

> **ИТОГО MUST: 31 задача / 118 ч**
> Календарно: **~15 рабочих дней 1 FTE / 8 дней 2 FTE / 7 дней 3 FTE**

---

## 🟧 SHOULD HAVE (35 задач, 157 ч) — важно, но не блокирует GA

> **Критерий:** Задача улучшает продукт, убирает риск, повышает readiness с 80 % до 95 %, но выпустить v1.0.0 МОЖНО и без неё. В v1.0.1 / v1.1.0.

### Phase 1 — SHOULD (7 задач, 18 ч)

| ID | Название | Часы | Почему SHOULD, не MUST |
|----|----------|-----:|-------------------------|
| P1-04 | Per-user rate limiting | 3 | Rate limit уже есть по IP. Per-user — nice-to-have для multi-tenant. |
| P1-07 | Security headers middleware | 2 | HSTS/CSP важны, но не блокируют (можно security headers в nginx). |
| P1-09 | Request-ID middleware | 2 | Без него трейсинг чуть сложнее, но работает. |
| P1-10 | OpenAPI/Redoc | 3 | Документация — не блокер. |
| P1-11 | print() → logger | 2 | Hygiene. CI gate добавим в v1.0.1. |
| P1-12 | Graceful shutdown | 3 | K8s SIGTERM всё равно подождёт 30 сек. Не идеально, но работает. |
| P1-14 | subprocess.run с check=True | 3 | Безопасность важна, но subprocess не в hot path. |

**Subtotal Phase 1 SHOULD: 18 ч**

### Phase 2 — SHOULD (9 задач, 37 ч)

| ID | Название | Часы | Почему SHOULD, не MUST |
|----|----------|-----:|-------------------------|
| P2-03 | Row-Level Security | 5 | Multi-tenant ещё не запущен. Single-tenant — не критично. |
| P2-04 | Connection pool tuning | 3 | Default пулы работают. Тюнинг для 1000+ RPS. |
| P2-07 | PostgreSQL HA (replica) | 6 | Single-pod Postgres работает. Replica = улучшение availability. |
| P2-09 | Read-replica routing | 4 | Зависит от P2-07. Single-pod сойдёт. |
| P2-10 | Slow-query log + autoindex | 4 | Улучшение перформанса. Не блокер. |
| P2-11 | Data integrity tests | 5 | Тесты важны, но failing tests закрываются в P0-01. |
| P2-13 | Vacuum/analyze policy | 2 | Autovacuum defaults работают. |
| P2-14 | DB-level audit log | 4 | Application-level audit уже есть (AMRE). DB-level — дополнение. |
| P2-15 | Connection-per-tenant | 3 | Multi-tenant отложен. |

**Subtotal Phase 2 SHOULD: 37 ч**

### Phase 3 — SHOULD (10 задач, 42 ч)

| ID | Название | Часы | Почему SHOULD, не MUST |
|----|----------|-----:|-------------------------|
| P3-02 | SLI exporters | 5 | Базовые метрики уже есть. Расширение — не блокер. |
| P3-05 | Grafana dashboards v2 | 5 | v1 дашборды работают. |
| P3-06 | Tempo/Jaeger | 6 | OpenTelemetry уже инжектится. Backend — улучшение. |
| P3-08 | Loki log aggregation | 4 | Логи в stdout уже собираются (Loki через promtail). |
| P3-09 | PII redaction в логах | 3 | **Спорно — может быть MUST.** PII в логах = GDPR. Оставляем SHOULD. |
| P3-11 | Synthetic monitoring | 3 | Healthz prober. Не блокер. |
| P3-12 | Performance baseline | 4 | Важно, но не блокирует GA. |
| P3-13 | Sentry | 3 | Альтернатива — Sentry через alertmanager. |
| P3-14 | Cost monitoring (FinOps) | 4 | Финансовая оптимизация. Не блокер. |
| P3-15 | APM-точки для воркеров | 3 | Улучшение observability. |

**Subtotal Phase 3 SHOULD: 42 ч**

### Phase 4 — SHOULD (9 задач, 39 ч)

| ID | Название | Часы | Почему SHOULD, не MUST |
|----|----------|-----:|-------------------------|
| P4-02 | Pen-test | 8 | Идеально — MUST. Реалистично — привлечь 1 фрилансера сложно, отложим. |
| P4-03 | SAST/DAST в CI | 4 | Semgrep/ZAP — отличные, но pip-audit + bandit уже покрывают MUST. |
| P4-06 | SLSA Level 3 provenance | 5 | SLSA L2 достаточно для v1.0.0. L3 — nice-to-have. |
| P4-07 | SECURITY.md | 2 | Желательно до GA, но не блокер. |
| P4-08 | PRIVACY.md / DPA | 4 | GDPR compliance. Можно отложить если не EU-юзеры. |
| P4-11 | Runbook для on-call | 6 | Без runbook тяжело, но P5-08 + дежурный сам разберётся. |
| P4-12 | ADR | 5 | Документация решений. Годно, но не блокер. |
| P4-13 | API documentation site | 6 | OpenAPI/Redoc есть. Внешний site — отложим. |
| P4-15 | User-facing docs (README) | 5 | README есть, tutorial'ы — улучшение. |

**Subtotal Phase 4 SHOULD: 45 ч** *(скорректировано: 39 ч)*

### Phase 5 — SHOULD (5 задач, 21 ч)

| ID | Название | Часы | Почему SHOULD, не MUST |
|----|----------|-----:|-------------------------|
| P5-02 | Auto-rollback | 4 | Ручной rollback работает. Auto-rollback — улучшение. |
| P5-03 | DB migration gate в CD | 4 | Pre-upgrade job полезен. Без него можно мерджить миграции аккуратнее. |
| P5-04 | Multi-region DR | 8 | Active-passive. Single-region работает. |
| P5-05 | Performance optimisation | 8 | P3-12 покажет узкие места. Может быть MUST post-baseline. |
| P5-09 | Postmortem template + 2 dry-runs | 3 | Process improvement. |

**Subtotal Phase 5 SHOULD: 27 ч** *(скорректировано: 21 ч)*

> **ИТОГО SHOULD: 35 задач / 157 ч**
> Календарно: **~20 дней 1 FTE** (сверх MUST)

---

## 🟨 COULD HAVE (17 задач, 52 ч) — nice-to-have

> **Критерий:** Полезно, но v1.0.0 не пострадает. Можно катить в v1.1.0 / v1.2.0.

### Phase 0 — COULD (1 задача, 2 ч)

| ID | Название | Часы | Комментарий |
|----|----------|-----:|-------------|
| P0-07 | ADR-0001 | 2 | Полезная практика, но не блокер. |

### Phase 2 — COULD (3 задачи, 6 ч)

| ID | Название | Часы | Комментарий |
|----|----------|-----:|-------------|
| P2-13 | Vacuum tuning | 2 | Defaults работают. |
| P2-14 (partial) | DB audit | — | Application-level audit уже есть. |
| P2-15 | Connection-per-tenant | 3 | Multi-tenant отложен. |

### Phase 3 — COULD (3 задачи, 12 ч)

| ID | Название | Часы | Комментарий |
|----|----------|-----:|-------------|
| P3-10 | Chaos engineering | 5 | Полезно для resilience, но можно без. |
| P3-14 | FinOps | 4 | Оптимизация затрат, не блокер. |
| P3-15 | APM для воркеров | 3 | Улучшение, не MUST. |

### Phase 4 — COULD (8 задач, 24 ч)

| ID | Название | Часы | Комментарий |
|----|----------|-----:|-------------|
| P4-09 | SOC2 readiness checklist | 6 | Type 2 — отдельный проект. Type 1 — не блокер для v1.0.0. |
| P4-14 | CHANGELOG automation | 3 | release-please — улучшение процесса. |
| P4-16 | DR tabletop | 4 | Полезно, но не блокер. |
| P4-17 | Compliance logging 7y | 3 | Audit log уже создаётся. Retention 7 лет — compliance. |
| P4-18 | Network Policies | 4 | Cluster default-deny. Default-allow в k8s работает. |
| P4-19 | Secret rotation policy | 3 | Процесс. |
| P4-20 | Bug-bounty | 2 | Community program. |
| P4-04 (additional) | Renovate/Dependabot PR | — | Авто-PR. |

### Phase 5 — COULD (4 задачи, 11 ч)

| ID | Название | Часы | Комментарий |
|----|----------|-----:|-------------|
| P5-06 | Capacity planning | 4 | Документ. |
| P5-07 | Feature flags | 5 | Без них релизим аккуратно. PostHog/Unleash — позже. |
| P5-12 | Telegram bot | 5 | UX improvement. |
| P5-15 | Decommission dev | 3 | Hygiene. |

> **ИТОГО COULD: 17 задач / 52 ч**
> Календарно: **~6.5 дней 1 FTE**

---

## ⬜ WON'T (this release) (4 задачи, 10 ч) — осознанно отложено

> **Критерий:** Требует отдельного планирования, ресурсов, либо вне scope v1.0.0.

| ID | Название | Часы | Почему WON'T | Куда отложено |
|----|----------|-----:|--------------|---------------|
| **G25** | Multi-region active-active | — | Single region работает. Active-passive хватит для DR. | v1.2.0+ |
| **G23** | Telegram bot для торговых команд | 5 | Это **операционный** инструмент, не часть core. | v1.1.0 |
| **G25** | Полноценный chaos engineering (chaos-mesh prod) | 5 | Базовый chaos (P3-10) в COULD. Полноценный — отдельный проект. | v1.2.0 |
| **P4-20** | Bug-bounty с bounty | — | Программа с денежным bounty — отдельное решение. SECURITY.md покроет disclosure. | v1.2.0+ |

> **ИТОГО WON'T: 4 задачи / 10 ч**

---

## 📈 Стратегия выпуска релизов

### Релиз 1.0.0 (GA) — 31 MUST задача

**Scope:** Безопасность, CI green, secrets management, базовый observability, deploy.

**Состав:** Phase 0 (7) + Phase 1 MUST (8) + Phase 2 MUST (6) + Phase 3 MUST (4) + Phase 4 MUST (4) + Phase 5 MUST (2) = **31 задача / 118 ч**.

**Срок:**
- 1 FTE: 15 дней (~4 нед)
- 2 FTE: 10 дней (~2 нед)
- 1.5 FTE (рекомендация): 13 дней (~3 нед)

**Go/No-Go критерии (Definition of Done):**
- [ ] Все 26 failing tests — green
- [ ] SOPS для всех secrets
- [ ] JWT auth работает
- [ ] S3 backups + DR runbook опубликован
- [ ] Canary deploy + auto-rollback (или ручной rollback runbook)
- [ ] PRR подписан
- [ ] Container image scan 0 critical
- [ ] SLO/SLI определены и alerting работает

**Readiness после v1.0.0: ~85 %** (без SHOULD/COULD)

### Релиз 1.0.1 (Hot-fix + Quality) — следующие 2-3 недели

**Scope:** 15 самых дешёвых SHOULD задач, которые быстро повышают quality.

Кандидаты:
- P1-04, P1-07, P1-09, P1-10, P1-11, P1-12, P1-14
- P2-04, P2-13
- P3-02, P3-05
- P4-07 (SECURITY.md), P4-12 (ADR)
- P5-03, P5-09

**Часы:** ~50 ч / 1 FTE = 6 дней

**Readiness после v1.0.1: ~90 %**

### Релиз 1.1.0 (Feature + Hardening) — через 2-3 мес

**Scope:** оставшиеся SHOULD (20 задач) + COULD (10-12 задач).

**Часы:** ~100 ч / 1 FTE = 12 дней

**Readiness после v1.1.0: ~95 %** 🎯

### Релиз 1.2.0+ (Scale) — через 6+ мес

**Scope:** Multi-region active-active, chaos engineering prod, bug-bounty, WON'T задачи.

---

## 🎯 Sprint Planning 1 (MUST only)

Неделя 1 (5 рабочих дней, 1 FTE = 40 ч):

| День | Задачи | Часы |
|------|--------|-----:|
| Пн | P0-01 (3ч) + P0-01.b (2ч) + P0-02 (1ч) + P0-04 (1ч) | 7 |
| Вт | P0-03 (4ч) + P0-05 (3ч) + P0-06 (1ч) | 8 |
| Ср | P1-01 (3ч) + P1-02 (4ч) | 7 |
| Чт | P1-02 (2ч продолжение) + P1-03 (4ч) + P1-15 (1ч) | 7 |
| Пт | P1-05 (4ч) + P1-06 (1ч) + P1-08 (2ч) + P1-13 (1ч) | 8 |
| **Итого за неделю** | **9 задач / 37 ч** | **37/40** |

**Capacity utilization:** 92 % (3 ч buffer на ревью/непредвиденное)

**Sprint Goal:** Все тесты green, push разблокирован, secrets в SOPS, JWT готов, базовая безопасность на месте.

**К концу недели 1:** Readiness ~78 % (+3 п.п. с 75 %).

### Sprint 2 (неделя 2) — фокус на MUST Phase 1 finish + Phase 2

**Задачи:** P2-01, P2-02, P2-05, P2-06, P2-08, P2-12, остатки Phase 1.

**Capacity:** ~35-40 ч / 1 FTE = 8-9 задач.

**Sprint Goal:** Database production-ready, backups настроены.

**К концу недели 2:** Readiness ~82 %.

### Sprint 3 (неделя 3) — Phase 3 MUST

**Задачи:** P3-01, P3-03, P3-04, P3-07 + P4-04, P4-05.

**Sprint Goal:** SLO/SLI + алерты работают, vulnerability scan в CI.

**К концу недели 3:** Readiness ~85 %.

### Sprint 4 (неделя 4) — Phase 4 + Phase 5 MUST

**Задачи:** P4-01, P4-10, P5-01, P5-10.

**Sprint Goal:** Threat model, bus factor fixed, canary deploy, PRR.

**К концу недели 4:** Readiness **~85-87 %** → **GA v1.0.0! 🎉**

---

## 📋 Спринт-чеклист (для 1 FTE)

```
Week 1 (37ч): P0-01, P0-01.b, P0-02, P0-03, P0-04, P0-05, P0-06, P1-01, P1-02, P1-03, P1-05, P1-15
Week 2 (38ч): P1-06, P1-08, P1-13, P2-01, P2-02, P2-05, P2-06, P2-08, P2-12
Week 3 (37ч): P3-01, P3-03, P3-04, P3-07, P4-04, P4-05
Week 4 (36ч): P4-01, P4-10, P5-01, P5-10
─────────────────────────────────────────────────────
ИТОГО: 31 MUST / 118 ч / 4 недели (1 FTE)
```

**С 2 FTE:** 2 недели (10 рабочих дней).
**С 1.5 FTE:** 3 недели (15 рабочих дней).

---

## ✅ Чек-лист для принятия решения

Готовы к GA v1.0.0 когда:

- [ ] Все 31 MUST задача завершены
- [ ] Все 9 acceptance criteria v1.0.0 выполнены (см. PRODUCTION_BACKLOG.md, Приложение A)
- [ ] PRR встреча проведена и подписана
- [ ] Sentry/slack/Telegram alerts настроены и протестированы
- [ ] Tag `v1.0.0` создан, release notes опубликованы
- [ ] README обновлён с инструкцией по v1.0.0

**Рекомендация:** начинаем с MUST, релизим v1.0.0 через 4 недели, потом SHOULD в v1.0.1 (ещё 2-3 нед), COULD в v1.1.0 (2-3 мес).

---

> 📌 **Этот файл — основа для решений.** Issue Template, Project board, Sprint Plans — всё ссылается на MoSCoW-категорию. Обновлять при изменении scope.

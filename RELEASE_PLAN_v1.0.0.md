# 🚀 Release Plan v1.0.0 — AstroFin Sentinel Platform

> **Product:** AstroFin Sentinel Platform — мульти-агентная торговая платформа (fundamental + quant + sentiment + astrology в формальном ensemble)
> **Target Release Date:** 2026-08-03 (Mon, W4 + 3 дня buffer)
> **Status:** 🟡 In Preparation
> **Release Manager:** @asurdev
> **PRR Sign-off Required:** 2 reviewers (минимум 1 architect, 1 DevOps)
> **Rollback SLA:** < 5 мин (auto-rollback при SLO burn 14×)

---

## 1. 🎯 Release Goal

**v1.0.0 = "Production-Ready Foundation"**: пользователь получает стабильную, наблюдаемую, безопасную платформу с 13-агентным советом, real-time ensemble-сигналами, AMRE audit trail и полным compliance-пакетом (SLO/SLI, SOPS secrets, JWT, backups, DR runbook).

**Ключевая ценность:** единственный open-source фреймворк, где fundamental, quant, sentiment и астрология объединены в формальном ensemble с явным audit-trail, RAG-поиском, Meta-RL обучением и воспроизводимыми бэктестами.

---

## 2. 📦 Scope (Что входит в v1.0.0)

### 2.1 ✅ IN-SCOPE (MUST — 31 задача, 118 ч)

| Категория | Кол-во | Содержание |
|-----------|------:|------------|
| **Phase 0** — Подготовка | 7 | Fix 26 failing tests, remove .bak, submodule→subtree plan, branch protection, requirements.lock, bandit sweep |
| **Phase 1** — API Hardening | 8 | .env.prod template, SOPS secrets, JWT auth, Pydantic v2, CORS, error handler без stack traces, /livez + /readyz, secrets.compare_digest |
| **Phase 2** — Database | 6 | TimescaleDB, pgvector, S3 backups (WAL-G), DR runbook, migrations CI-gate, TLS for Postgres |
| **Phase 3** — Observability | 4 | SLO/SLI definitions, Prometheus recording rules + SLO alerts, Alertmanager routing, trace-propagation fix |
| **Phase 4** — Security & Bus Factor | 4 | STRIDE threat model, dependency scan (pip-audit), container scan (trivy), bus factor mitigation (2-й maintainer) |
| **Phase 5** — Deploy & GA | 2 | Canary/B-G deploy с auto-rollback, Production Readiness Review meeting |

### 2.2 🟡 IN-SCOPE (выбранные SHOULD — 11 задач, ~45 ч)

Задачи, без которых v1.0.0 не имеет смысла по UX/operations:

| ID | Название | Часы | Sprint |
|----|----------|-----:|--------|
| **P1-04** | Per-user rate limiting (расширение JWT) | 3 | 2 |
| **P1-07** | Security headers middleware | 2 | 2 |
| **P1-09** | Request-ID middleware (X-Request-ID) | 2 | 2 |
| **P2-03** | Row-Level Security (multi-tenant ready) | 5 | 2 |
| **P2-14** | DB-level audit log (immutable, 7-year retention) | 4 | 2 |
| **P3-08** | Log aggregation (Loki + promtail) | 4 | 3 |
| **P3-13** | Error tracking (Sentry) | 3 | 3 |
| **P4-07** | SECURITY.md (disclosure policy) | 2 | 3 |
| **P4-08** | PRIVACY.md / DPA (GDPR) | 4 | 3 |
| **P5-08** | On-call rotation (PagerDuty, 2 чел.) | 3 | 4 |
| **P5-11** | Migration v5 submodule → root repo | 4 | 4 |

**ИТОГО Scope v1.0.0: 42 задачи / 163 ч** (MUST 31 + выбранные SHOULD 11)

### 2.3 ❌ OUT-OF-SCOPE (в v1.1+)

- COULD-задачи (17 шт): pgvector IVF optimization, chaos engineering в прод, cost monitoring (FinOps), bug-bounty, feature flags, Telegram bot
- WON'T (4 шт): Multi-region active-active, code signing certificates, dark launch mode
- Все остальные SHOULD (24 шт): performance optimization, capacity planning, additional API docs, ADRs для 5 решений — в v1.0.1 / v1.1.0

---

## 3. 📅 Timeline (Sprint 1–4)

| Sprint | Window | Фокус | Key Deliverables | Задач / ч |
|--------|--------|-------|------------------|----------:|
| **Sprint 1** | 07-06 → 07-12 | Phase 0 (целиком) + Phase 1 MUST start | 26 tests classified, .bak removed, submodule plan, .env.prod, SOPS, JWT готов | 30 / 63 |
| **Sprint 2** | 07-13 → 07-19 | Phase 1 finish + Phase 2 MUST start | Pydantic, security headers, /livez+/readyz, TimescaleDB, pgvector, S3 backups, DR runbook, RLS, DB audit log | 13 / 51 |
| **Sprint 3** | 07-20 → 07-26 | Phase 3 MUST + Phase 4 MUST | SLO/SLI, alerts, Loki logs, Sentry, threat model, pip-audit, trivy, SECURITY.md, PRIVACY.md | 10 / 42 |
| **Sprint 4** | 07-27 → 08-02 | Phase 5 MUST + P5-11 + P5-08 + P5-14 | Canary deploy, bus factor fix, on-call setup, v5 migration, tag v1.0.0 | 7 / 33 |
| **Buffer** | 08-03 → 08-05 | PRR, smoke, freeze | Production Readiness Review meeting, go-live | — / 24 |

**Прогнозируемая дата релиза:** **2026-08-05** (3 дня buffer на PRR + непредвиденные)

---

## 4. ✅ Definition of Done для GA (расширенный чек-лист)

### 4.1 Функциональная готовность

- [ ] Все 42 задачи Scope выполнены и код в `main`
- [ ] Все 26 ранее failing tests — green (или в issue с обоснованием)
- [ ] `pytest -q` показывает pass rate ≥ 95 %
- [ ] Coverage ≥ 70 % для core/ и agents/
- [ ] Ruff 0 errors, Bandit 0 high, semgrep 0 high
- [ ] Locust load-test 100 users / 5 rps проходит с p95 < 1s

### 4.2 Безопасность

- [ ] JWT-only auth (API_KEY удалён или deprecated)
- [ ] SOPS для всех секретов в `.env.prod`
- [ ] CORS whitelist настроен (не `*`)
- [ ] Security headers (HSTS, CSP, X-Frame-Options) в каждом response
- [ ] Pydantic v2 input validation на всех FastAPI/Flask endpoints
- [ ] 4xx/5xx не содержат stack traces
- [ ] RLS включена для `agent_decisions`, `users`, `api_keys`
- [ ] DB-level audit log пишет INSERT/UPDATE/DELETE
- [ ] TLS for Postgres (`sslmode=verify-full`)
- [ ] pip-audit: 0 critical CVE
- [ ] trivy image: 0 critical CVE
- [ ] STRIDE threat model опубликован в `docs/security/THREAT_MODEL.md`
- [ ] SECURITY.md и PRIVACY.md опубликованы

### 4.3 Database & Persistence

- [ ] TimescaleDB extension включён, hypertable создана для `ohlcv_bars`
- [ ] pgvector extension включён, RAG-индекс мигрирован
- [ ] WAL-G continuous backup в S3 (daily full + WAL streaming)
- [ ] DR runbook опубликован и протестирован
- [ ] Alembic migrations CI-gate работает (up → down → up)
- [ ] Schema migrations idempotent, проверено на 10 миграциях

### 4.4 Observability

- [ ] SLO/SLI определены в `docs/SLO.md`
- [ ] Prometheus recording rules + SLO burn-rate alerts (1h/6h, 6h/3d, 24h/30d)
- [ ] Alertmanager routing → Telegram (page) / Slack (warning) / email (info)
- [ ] Distributed tracing работает (Tempo/Jaeger), traceparent пробрасывается через async
- [ ] Loki + promtail собирает JSON-логи, derived fields `trace_id`, `request_id`
- [ ] PII redaction в логах (api_key, email, phone)
- [ ] Sentry получает тестовую ошибку, sample rate настроен
- [ ] Grafana SLO dashboard показывает error budget burn-rate

### 4.5 Deploy & Release

- [ ] Canary deploy с auto-rollback (Argo Rollouts)
- [ ] Alembic migration job в CD ждёт готовности DB перед traffic switch
- [ ] v1.0.0 tag подписан, GitHub Release с changelog опубликован
- [ ] Production Readiness Review (PRR) проведена и подписана
- [ ] 2+ подписанта PRR (1 architect, 1 DevOps)

### 4.6 Bus Factor & Process

- [ ] CODEOWNERS содержит `* @asurdev @mahaasur13-sys` (минимум 2 maintainer)
- [ ] 2+ часа pair-programming на critical-зонах (orchestrator, security, db)
- [ ] PagerDuty on-call rotation опубликована (2 человека, shadow on-call first 2 weeks)
- [ ] DR drill проведён, retrospective записан
- [ ] 1 postmortem-документ (dry-run) в `docs/postmortems/`

---

## 5. 🛡️ Rollout Strategy (Canary)

```
Day 0 (Release day, Mon 2026-08-05):
   09:00 UTC  PRR meeting → go/no-go
   10:00 UTC  Tag v1.0.0 + GitHub Release
   11:00 UTC  Deploy to staging → 30 min smoke tests
   12:00 UTC  Canary prod: 5% traffic (Argo Rollouts)
   12:30 UTC  SLO burn-rate check: green → promote 25%
   13:00 UTC  SLO check: green → promote 50%
   14:00 UTC  SLO check: green → promote 100%
   15:00 UTC  Monitor 2h intensive (no alerts)
   17:00 UTC  Announce: "v1.0.0 in production"
```

### 5.1 Rollback Plan

| Триггер | Действие | SLA |
|---------|----------|-----|
| **Auto:** SLO burn-rate > 14× за 1h | Argo Rollouts auto-rollback | < 2 мин |
| **Auto:** Error rate > 1% за 5 мин | Argo Rollouts auto-rollback | < 2 мин |
| **Auto:** p95 latency > 2s за 5 мин | Argo Rollouts auto-rollback | < 2 мин |
| **Manual:** on-call решает | `kubectl argo rollouts abort` | < 1 мин |
| **Manual:** через GitHub | `git revert` + redeploy | < 10 мин |

**Rollback target:** `v0.9.0-rc.2` (последний стабильный RC), `v0.8.0` (предыдущий GA).

### 5.2 Freeze Period

**2026-08-05 → 2026-08-12:** code freeze для `main` ветки. Только hotfix-ы через PR с label `hotfix` + 2 reviewer.

---

## 6. 📈 Success Metrics (KPI после релиза)

### 6.1 Readiness Score

| Метрика | До v1.0.0 | Цель v1.0.0 | Цель v1.1.0 |
|---------|----------:|------------:|------------:|
| Production Readiness (overall) | ~75 % | **≥ 95 %** | ≥ 97 % |
| API & Security | 70 % | ≥ 95 % | ≥ 97 % |
| Database & Persistence | 65 % | ≥ 95 % | ≥ 97 % |
| Observability | 80 % | ≥ 95 % | ≥ 97 % |
| Documentation | 65 % | ≥ 90 % | ≥ 95 % |

### 6.2 Operational KPIs (первые 30 дней)

| KPI | Target | Measurement |
|-----|-------:|-------------|
| **Uptime** | ≥ 99.9 % (≤ 43 мин downtime/мес) | Prometheus uptime probe |
| **API p95 latency** | < 500 мс | `histogram_quantile:0.95:http_request_duration:5m` |
| **API p99 latency** | < 1.5 s | `histogram_quantile:0.99:...` |
| **Error rate (5xx)** | < 0.1 % | `rate:http_requests_total:5m{code=~"5.."}` |
| **Error budget burn rate** | < 1× steady state | SLO alerts |
| **Test coverage** | ≥ 70 % | `coverage report` в CI |
| **Critical CVE** | 0 | trivy, pip-audit |
| **MTTR (mean time to recover)** | < 30 мин | Incident retrospective |
| **MTBF (mean time between failures)** | ≥ 7 дней | Incident log |

### 6.3 Adoption KPIs (первые 60 дней)

| KPI | Target |
|-----|-------:|
| GitHub stars | ≥ 50 |
| Active installations | ≥ 10 |
| Telegram bot users | ≥ 30 (после v1.0.1) |
| Issues opened (community) | ≥ 5 / мес |
| PRs merged (community) | ≥ 2 / мес |
| Backtest runs / day | ≥ 100 |

---

## 7. 🚦 Go/No-Go Criteria (для PRR)

**PRR meeting:** 2026-08-05 09:00 UTC, участники: @asurdev, @mahaasur13-sys, + 1 architect.

### 7.1 Hard Blockers (любой = NO-GO)

- [ ] ❌ Любая MUST-задача не завершена
- [ ] ❌ `pytest -q` показывает < 95 % pass rate
- [ ] ❌ Любой critical CVE в trivy/pip-audit
- [ ] ❌ Canary deploy smoke test failed
- [ ] ❌ Sentry получает unhandled exception в staging
- [ ] ❌ WAL-G restore test failed
- [ ] ❌ < 2 подписанта PRR
- [ ] ❌ Bus factor = 1 (нет второго maintainer)

### 7.2 Soft Warnings (могут быть NO-GO по решению PRR)

- ⚠️ Coverage < 70 % (цель, не блокер)
- ⚠️ Есть medium CVE (допустимо, нужны issue)
- ⚠️ Performance test p95 > 1s (нужен follow-up issue)
- ⚠️ On-call rotation < 2 человек

### 7.3 Go-Decision Template

```
PRR-2026-08-05-v1.0.0:
  Hard Blockers: [0/8 → GO]
  Soft Warnings: [N → resolved by owner / accepted]
  Decision: GO / NO-GO / DELAY
  Sign-offs: @asurdev ✅, @mahaasur13-sys ✅, @architect ✅
  Date: 2026-08-05
  Release tag: v1.0.0
```

---

## 8. 📣 Communication Plan

| Аудитория | Канал | Когда | Что |
|-----------|-------|-------|-----|
| **Команда** | Slack #releases | 2026-08-03 (Mon) | "Sprint 4 complete, PRR scheduled" |
| **Команда** | Daily standup | 2026-08-04 → 08-05 | Final status, blockers, last-mile prep |
| **Maintainers** | Email + Slack | 2026-08-05 09:00 | PRR invitation, agenda |
| **GitHub** | Release notes | 2026-08-05 10:00 | Tag v1.0.0 + GitHub Release с changelog |
| **Users (early adopters)** | Email blast | 2026-08-05 17:00 | "v1.0.0 is live" + migration guide |
| **GitHub Discussions** | Announcement | 2026-08-05 17:00 | Pinned post: "v1.0.0 released" |
| **Reddit r/algotrading** | Post | 2026-08-06 | Launch post (утро US time) |
| **Hacker News** | Show HN | 2026-08-06 | "Show HN: Multi-agent trading platform with astrological signals" |
| **Twitter/X** | Thread | 2026-08-06 | 5-tweet launch thread |
| **Telegram bot** | Push to subscribers | 2026-08-05 17:00 | "v1.0.0 is live — /changelog" |

**Press kit:** `docs/press/LAUNCH_v1.0.0.md` (создать в Sprint 4 W4) с 1-pager, screenshots, FAQ.

---

## 9. 🔄 Post-Release Activities (первые 30 дней)

### 9.1 Monitoring Window (Days 0–7)

- [ ] Daily check: error rate, p95 latency, alerts count
- [ ] On-call: 24/7 coverage, 2 чел., shadow on-call
- [ ] Daily 15-min standup с командой: "any new issues?"
- [ ] Hotfix policy: PR с label `hotfix` → fast-track merge (1 reviewer, < 30 мин SLA)

### 9.2 Week 1 Retrospective (Day 7, 2026-08-12)

- [ ] Что пошло не так? (incidents, bugs, deploy issues)
- [ ] Что пошло хорошо? (smooth deploys, zero downtime)
- [ ] Что улучшить в v1.0.1?
- [ ] Записать в `docs/postmortems/2026-08-12_v1.0.0_week1.md`

### 9.3 v1.0.1 Backlog (планируется сразу после релиза)

**Источник:** оставшиеся 24 SHOULD + баги из Week 1 + community feedback.

**Scope v1.0.1** (планируемая оценка, ~3-4 нед):
- Performance optimization (P5-05, P5-06) — если были жалобы на latency
- Feature flags (P5-07) — для безопасного rollout risk-agent
- Per-user rate limits hard limits (P1-04 уже в v1.0.0)
- Postmortem реальных инцидентов (P5-09)
- ADR для 5 архитектурных решений (P4-12)
- README quickstart rewrite (P4-15)
- API docs site на production domain (P4-13)

**Релиз v1.0.1:** планируется ~2026-08-26 (3 нед после v1.0.0).

---

## 10. 📚 Связанные документы

| Документ | Назначение |
|----------|-----------|
| `PRODUCTION_BACKLOG.md` | Полный бэклог 87 задач, 5 фаз |
| `MOSCOW_PRIORITIZATION.md` | MUST/SHOULD/COULD/WON'T распределение |
| `SPRINT_1.md` + `SPRINT_1_ISSUES.md` | Неделя 1: Phase 0 + начало Phase 1 |
| `SPRINT_2.md` | Неделя 2: Phase 1 finish + Phase 2 start |
| `SPRINT_3.md` (TBD) | Неделя 3: Phase 3 + Phase 4 |
| `SPRINT_4.md` (TBD) | Неделя 4: Phase 5 + GA |
| `EXECUTIVE_SUMMARY.md` | One-pager для инвесторов / стейкхолдеров |
| `.github/ISSUE_TEMPLATE/production-task.md` | Шаблон для создания issues |

---

## 11. ✅ Sign-off

| Роль | Имя | Подпись | Дата |
|------|-----|---------|------|
| Release Manager | @asurdev | ☐ | _______ |
| Architect | @mahaasur13-sys | ☐ | _______ |
| DevOps Lead | @____ | ☐ | _______ |
| Security | @____ | ☐ | _______ |

**Release approval date:** 2026-08-05 (после PRR)

**Release tag:** `v1.0.0`

**Release URL:** `https://github.com/mahaasur13-sys/astrofin-sentinel-platform/releases/tag/v1.0.0`

---

> 📌 **Этот документ — single source of truth для релиза v1.0.0.** Обновлять при изменении scope или сроков. После GA — архивировать в `docs/releases/v1.0.0/`.

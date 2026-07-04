# 🗓️ AstroFin Sentinel — Week 5 Sprint (Phase 4 finish + Phase 5: GA v1.0.0)

> **Sprint Window:** 2026-08-03 (Mon) → 2026-08-09 (Sun) — 5 рабочих дней
> **Sprint Goal:** Завершить Phase 4 (pen-test fixes, SLSA L3, SOC2 readiness, user docs, tabletop drill, API doc-site, ADR-набор) и выполнить Phase 5 GA: canary deploy, auto-rollback, multi-region DR, performance optimization, feature flags, on-call rotation, PRR, GA release v1.0.0. На выходе — `v1.0.0` tag подписан, GitHub Release опубликован, on-call расписание активно, GA cut-over завершён.
> **Capacity:** 80 ч (1 FTE) / 120 ч (1.5 FTE)
> **Всего задач:** 10 top-level (5 из Phase 4 finish + 5 из Phase 5 GA; 2 sub-task P5-04a/b)
> **Estimated effort:** 47 ч → utilization 59 % (33 ч buffer на bugfixes, RC-релиз, post-GA fixes)
> **Приоритет:** 🟥 MUST + 🟧 SHOULD (MoSCoW) — все задачи MUST, ни одна не может быть отложена

---

## 📊 Sprint 5 Snapshot

| Метрика | Значение |
|---|---|
| Задач в спринте | 10 (5 devops, 3 docs/process, 2 backend) |
| Общий объём | 47 ч |
| Capacity (1 FTE) | 80 ч |
| **Buffer** | **33 ч (41 %)** ← очень высокий, т.к. PRR + GA cut-over — итеративные процессы, могут потребовать дополнительных fix-ов |
| Должно быть закрыто | 9 новых + 1 carry-over (P5-04 multi-region DR) |
| Carry-over из Sprint 4 | Ожидается 0–1 задача (P3-14 FinOps или P3-11 synthetic) |
| Sprint 4 velocity baseline | 66 ч / 68 ч (97 %) |
| **Sprint 5 commit** | 47 ч / 80 ч (59 %) — низкий intentionally, чтобы поглотить GA surprises |

---

## 🎯 Sprint Goal в 3 измеримых результатах

1. **GA Release v1.0.0:** Canary deploy 5%→100% с auto-promote по SLO работает за < 20 мин. Auto-rollback срабатывает на injected SLO burn 14× за 1h за < 2 мин. Alembic migration gate в CD ждёт готовности DB. Tag `v1.0.0` подписан (cosign), GitHub Release опубликован с changelog.
2. **Multi-region DR + Perf:** Multi-region DR (active-passive) развёрнут в `fra1`, restore from S3 при failover, RTO < 1h, RPO < 15 мин. Performance optimization: 13 агентов параллельно (не последовательно), p95 /healthz < 300ms. Capacity planning docs опубликован.
3. **Process & Docs finish:** Pen-test top-3 исправлены. SLSA L3 provenance работает. SOC2 readiness checklist опубликован. ADR для 5 ключевых решений (hybrid agents, pgvector, Tempo, JWT, SOPS). API doc-site запущен. Tabletop drill проведён. On-call rotation (PagerDuty, 2 человека, shadow first 2 weeks). PRR meeting с подписью go-live.

---

## 📅 Дневной план (1 FTE baseline, 8 ч/день)

> ⚠️ **Структура:** Каждый день имеет 1 **фокусную задачу** (критичные deploy-задачи) + 0–1 **background** (документация, ADR, cleanup). Sub-tasks пронумерованы `День.Номер`.

### Пн, 3 августа — Phase 5: Canary deploy + Auto-rollback

**Фокус дня:** Deploy automation — самый критичный день для GA.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P5-01** | Blue/Green или Canary deploy: k8s `Deployment` со стратегией `RollingUpdate: maxSurge=0, maxUnavailable=1` + Argo Rollouts (canary 5%→25%→100% с auto-promote по метрикам) | 5 | DevOps | Sprint 4 P3-03 (SLO alerts) |
| 2 | **P5-02** | Auto-rollback на SLO burn-rate > 14× за 1h: Argo Rollouts AnalysisTemplate читает Prometheus, rollback в pre-promote | 3 | DevOps | P5-01, Sprint 4 P3-03 |
| 3 | _background_ | Code review для 1–2 PRов из Sprint 4 carry-over | 1 | DevOps | — |

**AC конца дня:**
- [ ] Argo Rollouts controller установлен в k8s кластер
- [ ] `kubectl argo rollouts get rollout astrofin-web -n astrofin` показывает статус
- [ ] Canary 5% deploy проходит, auto-promote после 5 мин если SLO stable
- [ ] Injected SLO burn 14× за 1h → rollback в pre-promote за < 2 мин
- [ ] Argo Rollouts UI (http://argo-rollouts:3100) показывает analysis history

**Команды на утро:**
```bash
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull
workon astrofin

# Утренняя проверка
cat /tmp/sprint4_retro.md 2>/dev/null || echo "No retro yet"
gh issue list --milestone "Sprint 4" --state closed --json number,title | head -20
kubectl get rollouts -n astrofin 2>/dev/null || echo "Argo Rollouts not yet installed"
```

**Команды для P5-01:**
```bash
# Установка Argo Rollouts (один раз)
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Установка kubectl plugin
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-darwin-amd64
chmod +x kubectl-argo-rollouts-darwin-amd64
sudo mv kubectl-argo-rollouts-darwin-amd64 /usr/local/bin/kubectl-argo-rollouts

# Тест canary
kubectl argo rollouts set image astrofin-web astrofin=astrofin:v1.0.0-rc1
kubectl argo rollouts get rollout astrofin-web --watch
```

---

### Вт, 4 августа — Phase 5: DB migration gate + Multi-region DR (start)

**Фокус дня:** CD pipeline hardening + начало multi-region.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P5-03** | Database migration gate в CD: pre-upgrade job ждёт завершения `alembic upgrade head` + smoke `SELECT 1`; только потом переключает traffic | 3 | DevOps | Sprint 2 P2-08 (migration CI) |
| 2 | **P5-04a** | Multi-region DR (active-passive) — start: вторая k8s-инсталляция в `fra1`, terraform/ansible provisioning | 4 | DevOps | Sprint 3 P2-07, Sprint 2 P2-05 |
| 3 | _background_ | ADR-0004: JWT auth (по факту реализации в Sprint 1) | 1 | Tech Writer | — |

**AC конца дня:**
- [ ] `deploy.yml` job `db-migration` ждёт `alembic upgrade head` exit 0
- [ ] `kubectl logs job/db-migration` показывает successful migration
- [ ] `kubectl wait --for=condition=ready pod/db-migration-xxx` → 0 sec wait
- [ ] Только после successful migration — traffic switch
- [ ] `fra1` k8s cluster provisioned, 3 nodes, basic networking
- [ ] `ADR-0004-jwt-auth.md` опубликован в `docs/adr/`

**Команды для P5-03:**
```bash
# Тест migration gate
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
# Watch .github/workflows/deploy.yml → db-migration job должен пройти до deploy

# Smoke после migration
psql $DATABASE_URL -c "SELECT 1"
psql $DATABASE_URL -c "\dt" | head -20  # все таблицы
```

---

### Ср, 5 августа — Phase 5: Performance optimization + Capacity

**Фокус дня:** Ускорение orchestrator (параллельные агенты), capacity planning docs.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P5-05** | Performance optimisation: параллельный запуск 13 агентов в `sentinel_v5.py` через `asyncio.gather`, кеширование (Redis) для RAG retrieval, DB-query tuning. Целевой p95 /healthz < 300ms | 5 | Backend | Sprint 4 P3-12 (baseline) |
| 2 | **P5-06** | Capacity planning: `docs/CAPACITY.md` — текущая нагрузка, прогноз ×3 за 6 мес, sizing. Load-test 200 users | 2 | DevOps | Sprint 4 P3-12 |
| 3 | _background_ | ADR-0005: SOPS secrets (по факту реализации) | 1 | Tech Writer | — |

**AC конца дня:**
- [ ] `sentinel_v5.py` запускает 13 агентов через `asyncio.gather()` (verified в коде)
- [ ] RAG retrieval кешируется в Redis с TTL 5 мин
- [ ] p95 `/healthz` < 300ms (verified в Locust)
- [ ] p95 `/signal BTC` < 5 сек (down from 8.5 сек в baseline)
- [ ] `docs/CAPACITY.md` опубликован, load-test 200 users проходит с p95 < 1s
- [ ] `ADR-0005-sops-secrets.md` готов

**Команды для P5-05:**
```bash
# До оптимизации (baseline)
locust -f tests/load/api_baseline.py --headless --users 100 --spawn-rate 5 --run-time 5m | tee /tmp/perf_before.log
grep "95%" /tmp/perf_before.log

# После оптимизации
locust -f tests/load/api_baseline.py --headless --users 100 --spawn-rate 5 --run-time 5m | tee /tmp/perf_after.log
grep "95%" /tmp/perf_after.log
# Должно быть улучшение > 20%
```

---

### Чт, 6 августа — Phase 4 finish: Docs, ADR, Tabletop + Phase 5: Feature flags + On-call

**Фокус дня:** Compliance docs finish + процесс передачи on-call.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P4-12** | ADR-набор: `docs/adr/0001-hybrid-agents.md`, `0002-pgvector-rag.md`, `0003-tempo-tracing.md`, `0004-jwt-auth.md` (УЖЕ), `0005-sops-secrets.md` (УЖЕ) | 2 | Tech Writer | Phase 1–4 |
| 2 | **P4-13** | API documentation site (публичный): на базе `openapi.json` поднять Mintlify/Docusaurus/starlight на `docs.api.astrofin`. Секции: Quickstart, Auth, Endpoints, Errors, SDKs | 3 | Tech Writer | Sprint 1 P1-10 (OpenAPI) |
| 3 | **P4-16** | Disaster Recovery tabletop exercise: 1-часовой сценарий (DB crash, region down, secret leak) с командой. Итог → `docs/DR_DRILL_2026-08-06.md` | 2 | DevOps | Sprint 2 P2-06 (DR runbook) |
| 4 | **P5-07** | Feature flags: интегрировать `posthog` или self-hosted `unleash`. Kill-switch для risk-agent | 3 | Backend | — |
| 5 | **P5-08** | On-call rotation: PagerDuty-расписание (2 человека), shadow on-call первые 2 недели, дежурный имеет доступ к проде через teleport/sso | 1 | DevOps | Sprint 4 P4-11 (runbook) |
| 6 | _background_ | ADR-0002: pgvector RAG, ADR-0003: Tempo tracing | 1 | Tech Writer | — |

**AC конца дня:**
- [ ] 5 ADR опубликованы в `docs/adr/` (0001, 0002, 0003, 0004, 0005)
- [ ] API doc-site доступен по `https://docs.api.astrofin` (или staging URL)
- [ ] Feature flag `risk_agent_disabled=true` мгновенно отключает риск-агента (verified в тестах)
- [ ] PagerDuty schedule создан, 2 человека, rotation start date 2026-08-10
- [ ] Shadow on-call назначен (первые 2 недели — действующий on-call + shadow)
- [ ] Teleport/SSO доступ настроен для on-call инженеров

---

### Пт, 7 августа — Phase 5: PRR + GA Release v1.0.0 🎉

**Фокус дня:** Production Readiness Review + tag v1.0.0 + GitHub Release.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P5-10** | Production Readiness Review meeting: чек-лист `docs/PRR_CHECKLIST.md` + встреча с командой. Подпись "go-live" | 2 | Tech Lead | All phases 0–4 |
| 2 | **P5-14** | GA release v1.0.0: tag, signed release notes, blog post, Reddit/HN | 2 | Tech Lead | All phases 0–5 |
| 3 | **P5-09** | Postmortem template + 2 dry-run сценария: `docs/postmortems/TEMPLATE.md`, "что если упадёт pg", "что если S3 недоступен" | 2 | DevOps | Sprint 4 P4-11 |
| 4 | **P5-15** | Decommission dev-environment: почистить неиспользуемые сервисы, удалить мёртвый код (но `agents/_archived/` оставить для истории) | 1 | Backend | Sprint 1 P0-01 |

**AC конца дня:**
- [ ] `docs/PRR_CHECKLIST.md` заполнен, все 50+ пунктов ✓
- [ ] PRR meeting проведён, signed go-live ticket (Google Doc, PDF, или GitHub issue)
- [ ] `git tag -s v1.0.0 -m "GA release v1.0.0"` (GPG-signed)
- [ ] `git push origin v1.0.0`
- [ ] GitHub Release опубликован с changelog (release-please или towncrier)
- [ ] Blog post опубликован (DEV.to, Medium, или self-hosted)
- [ ] Reddit r/algotrading, Hacker News post (optional, но high-impact)
- [ ] 2 postmortem-документа лежат в `docs/postmortems/`
- [ ] Dev environment cleanup: неиспользуемые сервисы остановлены, LOC снижен на 5%+

**🎉 КОНЕЦ SPRINT 5 = GA v1.0.0**

**Команды для P5-14:**
```bash
# 1. Убедиться, что все тесты зелёные
pytest -q tests/ | tail -1
# Ожидается: 0 failed, 0 errors

# 2. Создать tag (GPG-signed)
git tag -s v1.0.0 -m "GA release v1.0.0 — AstroFin Sentinel v5

Hybrid Signal Architecture (13 agents)
Phase 0-5 complete: 87/87 tasks done
SLO: 99.9% availability, p95 < 500ms
Multi-region DR active-passive (fra1)
Sprint 1-5 velocity: 19+37+62+66+47 = 231/280 (83%)

Co-authored-by: <contributors>"

# 3. Push tag
git push origin v1.0.0

# 4. GitHub Release через UI или gh CLI
gh release create v1.0.0 \
  --title "AstroFin Sentinel v1.0.0 — GA" \
  --notes-file CHANGELOG.md \
  --target release/1.0.0

# 5. Cosign verification (если настроен)
cosign verify --key cosign.pub ghcr.io/mahaasur13-sys/astrofin:v1.0.0
```

---

## 📅 Выходные (опционально, не в capacity)

> Только если есть энергия или критичные fixes. Sprint goal УЖЕ достигнут (v1.0.0 tagged).

| # | ID | Задача | Часы | Зачем |
|---|----|--------|-----:|-------|
| 1 | **P4-15** | User-facing docs (README + tutorials): переписать `README.md` под "Quick start in 5 minutes", tutorial "01_first_signal.md", "02_backtest.md", "03_custom_agent.md" | 5 | UX, on-boarding |
| 2 | **P5-12** | Telegram bot для алертов и quick-commands: `/signal BTC`, `/health`, `/status` — fastapi webhook + python-telegram-bot | 5 | UX, но не блокер |

---

## 📈 Burndown (ожидаемый)

| День | Запланировано (нарастающий итог) | Идеальный burndown | Реалистичный (GA surprises) |
|------|--------------------------------:|-------------------:|--------------------------:|
| Пн | 9 ч (P5-01, P5-02 + 1ч review) | 9 | 9 |
| Вт | 17 ч (+P5-03, P5-04a + ADR-0004) | 17 | 16 (fra1 provisioning = +1ч) |
| Ср | 25 ч (+P5-05, P5-06 + ADR-0005) | 25 | 24 (parallel refactor = +1ч) |
| Чт | 33 ч (+P4-12, P4-13, P5-07, P5-08 + 2 ADR) | 33 | 30 (Mintlify setup = +3ч) |
| Пт | 45 ч (+P5-10 PRR, P5-14 GA, P5-09, P5-15) | 45 | 47 (PRR итерации + postmortem prep) |
| **Итого** | **47 ч** | **47/47** | **47/47 (100 %)** |

> **Стратегия:** Sprint 5 commit 59% — низкий, потому что GA cut-over — итеративный процесс, могут потребоваться дополнительные fix-ы в Чт-Пт. Buffer 33 ч даёт пространство для troubleshooting.

---

## 📦 Definition of Done для Sprint 5 (GA Definition of Done)

### Deploy & Release
- [ ] Canary deploy 5% → 100% с auto-promote проходит за < 20 мин
- [ ] Auto-rollback срабатывает на injected SLO burn 14× за 1h за < 2 мин
- [ ] Alembic migration gate в CD ждёт `alembic upgrade head` + `SELECT 1` перед traffic switch
- [ ] Multi-region DR (active-passive) в `fra1` развёрнут, RTO < 1h, RPO < 15 мин
- [ ] `v1.0.0` tag подписан (GPG), push в remote
- [ ] GitHub Release опубликован с changelog
- [ ] PRR meeting проведён, signed go-live ticket
- [ ] `agents/_archived/` оставлен для истории (R-08), но verified что нигде не импортируется

### Performance & Capacity
- [ ] 13 агентов запускаются параллельно (asyncio.gather), p95 /healthz < 300ms
- [ ] RAG retrieval кешируется в Redis с TTL 5 мин
- [ ] Load-test 200 users проходит с p95 < 1s
- [ ] `docs/CAPACITY.md` опубликован с прогнозом ×3 за 6 мес

### Process & Safety
- [ ] Feature flags интегрированы (`posthog` или `unleash`), kill-switch для risk-agent работает
- [ ] On-call расписание в PagerDuty (2 человека, rotation start 2026-08-10)
- [ ] Shadow on-call назначен (первые 2 недели)
- [ ] 2 postmortem-документа лежат в `docs/postmortems/`
- [ ] Dev environment cleanup: неиспользуемые сервисы остановлены, LOC снижен на 5%+

### Documentation & Compliance
- [ ] 5 ADR опубликованы в `docs/adr/` (0001, 0002, 0003, 0004, 0005)
- [ ] API doc-site доступен по `https://docs.api.astrofin` (или staging URL)
- [ ] Tabletop drill проведён (1-часовой сценарий), retrospective записан

### Качество
- [ ] `pytest -q` 0 failed, 0 errors
- [ ] `ruff check` 0 errors, `bandit -r` без новых high
- [ ] `semgrep ci` 0 high, `pip-audit` 0 critical, `trivy image` 0 critical
- [ ] Coverage ≥ 75 % для `core/`, `web/`, `orchestration/`
- [ ] Code review пройден для всех PR (≥1 reviewer)
- [ ] SLSA L3 provenance для всех 4 production images
- [ ] Cosign verification работает в admission controller (или README описывает процедуру)

---

## 🔗 Зависимости от Sprint 4 (blockers)

| Зависит от | Sprint 5 задача | Что нужно от Sprint 4 |
|------------|----------------|----------------------|
| Sprint 4 P3-03 (Prometheus rules) | **P5-01** (canary), **P5-02** (rollback) | SLO burn-rate метрики работают |
| Sprint 4 P4-11 (runbook) | **P5-08** (on-call), **P5-09** (postmortem) | Runbook готов |
| Sprint 4 P3-12 (perf baseline) | **P5-05** (optimization) | Baseline numbers для сравнения |
| Sprint 1 P1-10 (OpenAPI) | **P4-13** (API doc-site) | OpenAPI spec готов |
| Sprint 1 P0-01 (fix tests) | **P5-15** (decommission) | Зелёные тесты для refactoring |

> ⚠️ **Если Sprint 4 задержится** по P3-03 (SLO alerts), Sprint 5 canary/rollback невозможны.

---

## 🔄 Carry-over Plan (если что-то не успеем)

| Задача | Приоритет | Куда идёт |
|--------|----------|-----------|
| P4-15 (user docs) | 🟧 Should | Post-GA Sprint 6 (1 неделя) |
| P5-12 (Telegram bot) | 🟨 Low | Post-GA Sprint 6 (опц.) |
| P4-09 (SOC2 readiness) | 🟨 Medium | Post-GA Sprint 7 (1 неделя) |
| P4-20 (bug-bounty program) | 🟨 Medium | Post-GA Q4 2026 |

**Sprint 6 preview (post-GA, optional):** v1.0.1 bugfixes, user docs, Telegram bot, A/B testing calibration, performance optimization v2, ML model v6.

---

## ⚠️ Риски Sprint 5

| # | Риск | Вероятность | Импакт | Mitigation |
|---|------|------------:|-------:|------------|
| **R-S5-1** | Canary deploy зависает на анализе метрик, auto-promote не срабатывает | 🟧 Средняя | 🟥 Critical | Manual promote кнопка в Argo UI; timeout 30 мин → abort |
| **R-S5-2** | Auto-rollback срабатывает на fluky SLO spike (false positive) | 🟧 Средняя | 🟧 High | Confirmation timeout 5 мин (двойная проверка burn-rate) |
| **R-S5-3** | Multi-region DR provisioning требует > 8ч (terraform state, network setup) | 🟧 Средняя | 🟧 High | Начать во Вт утро (P5-04a), не в Чт; dry-run на dev кластере |
| **R-S5-4** | Parallel agents (asyncio.gather) ломает 2-3 endpoint (shared state) | 🟧 Средняя | 🟧 High | Feature flag `PARALLEL_AGENTS=true`; staged rollout |
| **R-S5-5** | PRR выявляет 5+ недостающих пунктов, GA откладывается | 🟧 Средняя | 🟥 Critical | PRR draft за 2 дня до meeting; soft-launch в Чт-Пт |
| **R-S5-6** | PagerDuty интеграция требует admin access, задержка provisioning | 🟨 Низкая | 🟧 Medium | Использовать personal PagerDuty account first; migrate позже |
| **R-S5-7** | Mintlify/Docusaurus setup не работает с нашим OpenAPI spec | 🟨 Низкая | 🟨 Medium | Fallback на Swagger UI + README (P4-15); не блокер GA |
| **R-S5-8** | GA cut-over выявляет критичный bug в production (не в staging) | 🟧 Средняя | 🟥 Critical | Shadow deploy 24ч перед GA; feature flag для instant rollback |

### Топ-3 риска, требующих внимания в начале спринта

1. **R-S5-1 (canary hang)** — Argo Rollouts нужен к Пн утру, не к Вт
2. **R-S5-3 (multi-region DR time)** — начать во Вт, не в Чт
3. **R-S5-5 (PRR gaps)** — draft PRR checklist в начале недели, не в конце

---

## 🔀 Параллелизм (если 2 FTE)

| Трек | Owner | Задачи | Часы |
|------|-------|--------|-----:|
| **A — DevOps** | Senior DevOps (1 FTE) | P5-01, P5-02, P5-03, P5-04a, P5-08, P5-10, P5-14, P5-15 | 22 |
| **B — Backend** | Senior Backend (1 FTE) | P5-05, P5-07 | 8 |
| **C — Tech Writer** | Tech Writer (1 FTE) | P4-12, P4-13, ADR-0002, ADR-0003 | 7 |
| **D — DevOps (post-GA)** | DevOps (0.5 FTE) | P5-09 | 2 |

**2 FTE sprint commit:** 47 ч / 80 ч (59 %) — все треки закроются в Ср-Чт, освобождая Пт для PRR + GA + postmortem prep.

**Если 1.5 FTE:** DevOps full + Backend part-time (0.5) + Tech Writer part-time (0.25).

**Если 1 FTE:** DevOps full (только критичные deploy), Backend всё остальное (P5-05, P5-07, P5-15).

---

## 🛠️ Команды для старта (Пн утро)

```bash
# 1. Синхронизироваться
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull origin release/1.0.0
workon astrofin

# 2. Создать Sprint 5 milestone
gh api repos/mahaasur13-sys/astrofin-sentinel-platform/milestones \
  -f title="Sprint 5 (GA v1.0.0)" \
  -f due_on="2026-08-09T23:59:59Z"

# 3. Создать 10 issues
gh issue create --title "[P5-01] Canary deploy" --milestone "Sprint 5" ...

# 4. Утренний check
gh issue list --milestone "Sprint 4" --state all --json number,title,state | jq '.[] | select(.state=="open")'
cat /tmp/sprint4_retro.md 2>/dev/null
kubectl get rollouts -n astrofin 2>/dev/null | head -5
gh release list --limit 5
```

---

## 📊 Метрики успеха Sprint 5

| Метрика | Цель | Как измерить |
|---------|-----|--------------|
| Sprint commit | 59 % (47/80) | `gh issue list --milestone "Sprint 5" --state closed` |
| Carry-over из Sprint 4 | ≤ 1 задача | Standup Пн |
| New critical bugs | 0 | `gh issue list --label critical --state open` |
| `pytest` pass rate | 100 % (было ~98 % после Sprint 4) | `pytest -q tests/ \| tail -1` |
| Coverage | ≥ 75 % (core/web/orchestration) | `coverage report` |
| Canary deploy time | < 20 мин (5% → 100%) | Argo Rollouts UI |
| Auto-rollback time | < 2 мин (SLO burn injected) | manual test в Пн |
| p95 /healthz | < 300ms | Locust test |
| p95 /signal BTC | < 5s (down from 8.5s) | Locust test |
| Multi-region RTO | < 1h | DR drill в Чт |
| Multi-region RPO | < 15 мин | WAL-G + S3 lag |
| PagerDuty schedule active | Yes, с 2026-08-10 | PagerDuty UI |
| v1.0.0 tag signed | Yes (GPG) | `git tag -v v1.0.0` |
| PRR go-live signed | Yes | docs/PRR_CHECKLIST.md |

---

## 🤝 Ceremonies

| Событие | Время | Участники | Длительность |
|---------|-------|-----------|-------------:|
| **Sprint 5 Planning** | Пт 31 июля 16:00 | Вся команда | 1 ч |
| **Daily Standup** | Пн–Пт 09:30 | DevOps + Backend + Writer | 15 мин |
| **Mid-sprint Check** | Ср 14:00 | DevOps + Backend | 30 мин (burndown) |
| **PRR Meeting** | Пт 7 августа 14:00 | All + Stakeholders | 2 ч |
| **GA Release** | Пт 7 августа 16:00 | DevOps + Tech Lead | 30 мин |
| **Sprint 5 Retro** | Пт 7 августа 17:00 | Вся команда | 1 ч |
| **🎉 GA Celebration** | Пт 7 августа 18:00 | Вся команда | 🎊 |

**PRR meeting agenda:**
1. SLO/SLI обзор: burn-rate, error budget, MTTR
2. Security: semgrep/pip-audit/trivy отчёты, threat model walkthrough
3. Performance: Locust baseline, capacity planning
4. DR: multi-region status, RTO/RPO validated
5. Runbook review: top-15 алертов с диагностикой
6. Bus factor: 2-й maintainer on boarded
7. Open issues: critical, high (должно быть 0)
8. **Go/No-Go vote**

**GA Release demo agenda:**
1. Live canary deploy demo (5% → 100%)
2. Auto-rollback demo (inject error)
3. Multi-region failover demo (simulate region down)
4. Performance dashboard: p95 < 300ms verified
5. `git tag -s v1.0.0` ceremony
6. GitHub Release публикация
7. 🎉

---

## 📎 Приложение A. Carry-over Checklist из Sprint 4

Заполнить в начале Sprint 5 (Пн утро):

```
Sprint 4 Carry-over
═══════════════════════════════════════════════
□ P3-01 (SLO defs) → Done? Y/N
□ P3-02 (SLI exporters) → Done? Y/N
□ P3-03 (Prometheus rules) → Done? Y/N
□ P3-04 (Alertmanager routing) → Done? Y/N
□ P3-05 (Grafana v2) → Done? Y/N
□ P3-06 (Tempo) → Done? Y/N
□ P3-07 (Traceprop fix) → Done? Y/N
□ P3-08 (Loki logs) → Done? Y/N
□ P3-09 (PII redaction) → Done? Y/N
□ P3-10 (Chaos test) → Done? Y/N
□ P3-12 (Locust baseline) → Done? Y/N
□ P3-13 (Sentry) → Done? Y/N
□ P3-15 (APM spans) → Done? Y/N
□ P4-01 (Threat model) → Done? Y/N
□ P4-03 (semgrep CI) → Done? Y/N
═══════════════════════════════════════════════
Total carry-over: __/15

If carry-over > 1: reduce Sprint 5 scope (drop P5-12, P4-15)
If carry-over = 0: add P4-15 (user docs) to Sprint 5
```

---

## 📎 Приложение B. PRR Checklist Template

`docs/PRR_CHECKLIST.md` (создаётся в начале Sprint 5, заполняется к Пт):

```markdown
# Production Readiness Review (PRR) — v1.0.0

**Date:** 2026-08-07
**Reviewers:** [Имена]
**Decision:** [ ] GO  [ ] NO-GO

## 1. Architecture & Code (95%)
- [ ] 13-agent hybrid signal architecture протестирована
- [ ] Conflict resolution работает (Astro vs Fundamental+Quant)
- [ ] 0 critical issues в KNOWN_ISSUES.md

## 2. API & Security (95%)
- [ ] JWT-only auth, API_KEY deprecated
- [ ] Per-user rate limiting работает
- [ ] All 5 security headers на каждом response
- [ ] PII redaction в логах verified

## 3. Database & Persistence (95%)
- [ ] TimescaleDB hypertable в проде, retention 2y
- [ ] pgvector RAG search p95 < 80ms
- [ ] RLS active, tenant isolation verified
- [ ] WAL-G backup verified (latest restore OK)
- [ ] Multi-region DR: RTO < 1h, RPO < 15 мин

## 4. Observability (95%)
- [ ] SLO/SLI определены, error budget tracked
- [ ] SLO burn-rate alerts работают
- [ ] Distributed tracing end-to-end (Tempo)
- [ ] Sentry integration работает
- [ ] PII redaction verified

## 5. Security & Compliance (95%)
- [ ] semgrep/pip-audit/trivy: 0 critical
- [ ] Threat model STRIDE опубликован
- [ ] Pen-test top-3 исправлены
- [ ] SLSA L3 provenance для images
- [ ] SECURITY.md, PRIVACY.md published

## 6. Infrastructure & Deployment (95%)
- [ ] Canary deploy + auto-rollback работают
- [ ] DB migration gate в CD
- [ ] Multi-region DR active-passive
- [ ] On-call rotation active (PagerDuty)
- [ ] 2 postmortem-документа

## 7. Documentation & Process (95%)
- [ ] README + 3 tutorials
- [ ] 5 ADR опубликованы
- [ ] API doc-site запущен
- [ ] Runbook для on-call готов
- [ ] 2-й maintainer on boarded (bus factor = 2)

## 8. Testing & Quality (95%)
- [ ] pytest 0 failed, 0 errors
- [ ] Coverage ≥ 75% (core/web/orchestration)
- [ ] Load-test 200 users: p95 < 1s
- [ ] Locust baseline закоммичен, CI gate активен

## Signatures

- [ ] Tech Lead: _______________
- [ ] DevOps Lead: _______________
- [ ] Security Engineer: _______________
- [ ] Product Owner: _______________

**Go-Live Authorization:** ☐ APPROVED  ☐ DENIED  ☐ APPROVED WITH CONDITIONS
```

---

## 📎 Приложение C. Где искать что

| Что | Где |
|-----|-----|
| Sprint 4 issues | `gh issue list --milestone "Sprint 4"` |
| Sprint 4 retro | `/tmp/sprint4_retro.md` |
| MoSCoW-приоритезация | `MOSCOW_PRIORITIZATION.md` |
| Полный бэклог | `PRODUCTION_BACKLOG.md` |
| Week 1 sprint | `SPRINT_1.md` |
| Week 2 sprint | `SPRINT_2.md` |
| Week 3 sprint | `SPRINT_3.md` |
| Week 4 sprint | `SPRINT_4.md` |
| Week 5 sprint (этот) | `SPRINT_5.md` |
| Argo Rollouts docs | https://argoproj.github.io/argo-rollouts/ |
| Multi-region k8s | https://kubernetes.io/docs/setup/best-practices/multiple-zones/ |
| GA Release template | `RELEASE_PLAN_v1.0.0.md` |
| Executive Summary | `EXECUTIVE_SUMMARY.md` |

---

## ✅ Готовность к старту

Pre-flight checklist (Пн 09:00):

- [ ] `gh auth status` — logged in
- [ ] `git status` — clean, on `release/1.0.0`
- [ ] `pytest -q tests/ | tail -1` — pass rate 100% из Sprint 4
- [ ] `gh issue list --milestone "Sprint 4" --state closed | wc -l` — Sprint 4 velocity ≥ 16/16
- [ ] Прочитать `SPRINT_4.md` и `MOSCOW_PRIORITIZATION.md`
- [ ] Проверить `Sprint 4 retro` (если был)
- [ ] `Sprint 5 milestone` создан в GitHub
- [ ] Slack/email уведомление команде: "Sprint 5 starts — last sprint before GA"
- [ ] Argo Rollouts controller установлен в k8s
- [ ] Prometheus SLO burn-rate alerts работают (от Sprint 4)

---

> 📌 **Этот документ — операционный план на финальную неделю.** Использовать как checklist на daily standup. После Sprint 5 retro обновить на основе реальной velocity и lessons learned для v1.0.1.

---

## 🎉 ЗАКЛЮЧЕНИЕ

Sprint 5 — финальный спринт. На выходе:

1. **GA v1.0.0** tagged, signed, released
2. **Multi-region DR** active-passive в `fra1`
3. **On-call** rotation active (2 человека + shadow)
4. **Performance** p95 < 300ms verified
5. **PRR** meeting с go-live подписью
6. **All 87 tasks** из бэклога выполнены (или осознанно отложены в Sprint 6+)

После Sprint 5 retro:
- Velocity total: 19 (Sprint 1 partial) + 37 (S1) + 62 (S2) + 66 (S3) + 47 (S4) = **231 ч / 280 ч (83 %)**
- Команда готова к v1.0.1 bugfixes (Sprint 6) и feature work (Sprint 7+)

**Удачи в GA! 🚀**
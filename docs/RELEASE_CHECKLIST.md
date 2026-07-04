# 🚦 Release Checklist — v1.0.0 GA

> **Status:** ✅ Active (last reviewed 2026-07-04)
> **Owner:** Tech Lead (`@asurdev`)
> **Target GA date:** 2026-08-09
> **Назначение:** go/no-go чек-лист для релиза v1.0.0. Заполняется в W5 (с 2026-08-03), финальный sign-off — на PRR (2026-08-08).

---

## 1. 🎯 Назначение

**Release Checklist** — это **финальный gate** перед публичным релизом. Отличается от `DEFINITION_OF_DONE.md` тем, что:

- **DoD** — критерии "задача/спринт/фаза готова" (в процессе работы)
- **Release Checklist** — критерии "v1.0.0 можно публиковать" (за 1 день до GA)

**Процесс:**
1. W5 Пн–Чт: чек-лист заполняется (по мере выполнения W5 задач)
2. W5 Пт (2026-08-08): **PRR meeting**, финальный sign-off всех stakeholders
3. W5 Пт (после PRR): tag `v1.0.0`, GitHub Release, deployment в production
4. W6 Пн: post-release monitoring, начинается Sprint 6 (v1.0.1 bugfix)

**Если хотя бы 1 пункт в Critical (🟥) ❌ → NO-GO, сдвиг релиза на 1-2 недели.**

---

## 2. 🟥 Critical (блокирует релиз)

Эти пункты **обязательны** для `v1.0.0`. Без них релиз невозможен.

### 2.1 Functional (Phase 0–5 DoD)

- [ ] **Phase 0 done:** 7/7 задач P0-01..P0-07, test fail count ≤ 21, release/1.0.0 branch существует
- [ ] **Phase 1 done:** все 16 задач P1-01..P1-16, JWT-only auth работает, security headers + rate limit активны
- [ ] **Phase 2 done:** все 15 задач P2-01..P2-15, TimescaleDB + pgvector + RLS + HA + WAL-G backups работают
- [ ] **Phase 3 done:** все 15 задач P3-01..P3-15, SLO/SLI + Prometheus rules + Alertmanager + Tempo/Loki + Sentry + PII redaction активны
- [ ] **Phase 4 done:** все 20 задач P4-01..P4-20, threat model + pen-test + SAST/DAST + SLSA L3 + SECURITY/PRIVACY/ADR документы опубликованы
- [ ] **Phase 5 done:** все 15 задач P5-01..P5-15, canary deploy + auto-rollback + on-call + PRR проведены

**Total:** 88/88 задач выполнены (100 %).

### 2.2 Security

- [ ] `semgrep ci` — 0 high
- [ ] `trivy image` — 0 critical на 4 production images (web, orchestrator, ml-engine, gpu-worker)
- [ ] `pip-audit` — 0 critical
- [ ] `bandit -r` — 0 new high
- [ ] **Pen-test проведён** (P4-02), все Critical/High закрыты
- [ ] **SLSA L3 provenance** для всех images (P4-06), verification проходит
- [ ] **JWT-only auth** (API_KEY deprecated, период миграции закрыт)
- [ ] **SOPS** для всех секретов, `.env.prod` зашифрован
- [ ] **RLS** активна на `agent_decisions`, `audit_log`, `backtest_runs`
- [ ] **Network Policies** в k8s (P4-18) — default-deny + явные allow
- [ ] **Cosign verification** проходит в admission controller
- [ ] **2 вторых maintainer** в CODEOWNERS (P4-10)
- [ ] **SECRET_ROTATION.md** (P4-19) — процедура ротации каждые 90 дней

### 2.3 Observability & SLO

- [ ] `docs/SLO.md` утверждён (P3-01)
- [ ] SLO метрики в норме за последние 7 дней (staging):
  - [ ] API latency p95 < 500 ms
  - [ ] API error rate < 0.1 %
  - [ ] API availability > 99.9 % (calculated over 30 days)
  - [ ] Backtest success rate > 99 %
  - [ ] ML inference latency p95 < 200 ms
- [ ] Error budget > 50 % остался
- [ ] **Alertmanager** шлёт тестовые алерты (P3-04) в Telegram/Slack/PagerDuty
- [ ] **Distributed tracing** работает end-to-end (P3-06, P3-07)
- [ ] **PII redaction** в логах доказательно (P3-09): `api_key=...` не появляется в Loki
- [ ] **Sentry** интегрирован (P3-13), тестовая ошибка доставлена
- [ ] **Grafana dashboards v2** активны (P3-05), SLO panel + on-call overview
- [ ] **Synthetic monitoring** работает (P3-11): blackbox-exporter → `/healthz` каждые 30s, 0 false alerts за 7 дней

### 2.4 Backup & DR

- [ ] **WAL-G backups** в S3 работают (P2-05), последний успешный backup < 24h назад
- [ ] **Backup verification job** в CI проходит (P2-05b)
- [ ] **Restore test** проведён на dev-кластере за последние 7 дней (P2-05b)
- [ ] **DR runbook** (`docs/DR_RUNBOOK.md`) опубликован (P2-06)
- [ ] **RPO ≤ 1ч, RTO ≤ 4ч** — задокументировано, проверено в dry-run
- [ ] **Tabletop exercise** проведён (P4-16), retrospective записан
- [ ] **Multi-region DR** (active-passive) — второй кластер в `fra1` готов (P5-04)

### 2.5 Deploy

- [ ] **Canary deploy** 5 % → 100 % с auto-promote проходит за < 20 мин (P5-01)
- [ ] **Auto-rollback** на injected SLO burn 14× за 1h работает (P5-02), откат за < 2 мин
- [ ] **DB migration gate** в CD ждёт `alembic upgrade head` + `SELECT 1` перед переключением (P5-03)
- [ ] **Feature flag** `risk_agent_disabled=true` мгновенно отключает риск-агента (P5-07)
- [ ] **On-call rotation** опубликован (P5-08), PagerDuty интегрирован, shadow-on-call 2 недели проведены

### 2.6 Compliance & Docs

- [ ] `SECURITY.md` опубликован (P4-07) с disclosure policy, контактами, scope
- [ ] `PRIVACY.md` / DPA опубликован (P4-08), GDPR-совместимый
- [ ] **5 ADR** для ключевых решений (P4-12): 0001-hybrid-agents, 0002-pgvector-rag, 0003-tempo-tracing, 0004-jwt-auth, 0005-sops-secrets
- [ ] **API doc-site** доступен (P4-13): `docs.api.astrofin` или staging URL
- [ ] **CHANGELOG.md** + release notes процесс (P4-14, release-please или towncrier)
- [ ] **README.md** обновлён (P4-15): "Quick start in 5 minutes"
- [ ] **RUNBOOK.md** (P4-11) с top-15 алертами + диагностические скрипты в `tools/diag/`
- [ ] **2 postmortem-документа** (P5-09): сценарии "что если упадёт pg" и "что если S3 недоступен"

### 2.7 Quality Gates

- [ ] `pytest -q` (full suite) — **0 fail** (все 26 ранее failing tests — green)
- [ ] `ruff check` — 0 errors
- [ ] `mypy --strict` — 0 errors на новых файлах
- [ ] `coverage report` — ≥ 75 % для `core/`, `web/`, `orchestration/`, `db/`
- [ ] **Load test** 200 users (P3-12): p95 < 1s, success rate > 99 %
- [ ] **Chaos test** `kill-app-pod` (P3-10): recovery < 30 сек, метрики фиксируют

### 2.8 Risk & Dependencies

- [ ] **RISK_REGISTER.md** reviewed: ≤ 2 Open рисков с Heat ≥ 12
- [ ] **DEPENDENCIES.md** актуален
- [ ] **Carry-over** из W5 ≤ 1 задача (если больше — sprint planning error, рескейлинг)

---

## 3. 🟧 Important (желательно, но не блокер)

Эти пункты **настоятельно рекомендуются**, но их отсутствие не блокирует GA. Решение принимает Tech Lead + Product Owner.

### 3.1 Performance

- [ ] **Performance optimization** (P5-05) — async-параллелизм в `sentinel_v5.py`, кеширование, DB query tuning
- [ ] **Capacity planning** (P5-06) — `docs/CAPACITY.md` опубликован, прогноз ×3 за 6 мес

### 3.2 Cost & FinOps

- [ ] **Cost monitoring** (P3-14) — kubecost/cost-exporter dashboard, $/request, $/signal
- [ ] **Sentry sample rate** 10 % в prod (P3-13)
- [ ] **OTel tail-sampling** 5 % head (P3-07) — overhead < 5 % на p99

### 3.3 UX & Docs

- [ ] **Telegram bot** (P5-12) — `/signal BTC`, `/health`, `/status` работают
- [ ] **User-facing tutorials** (P4-15) — `01_first_signal.md`, `02_backtest.md`, `03_custom_agent.md`
- [ ] **API doc-site** имеет search, code samples (Python + JS SDKs)

### 3.4 Community

- [ ] **Bug-bounty program** (P4-20, optional) — disclosure policy + scope.txt опубликованы
- [ ] **Reddit / HN post** подготовлен (P5-14) для launch

---

## 4. 🟢 Nice-to-Have (post-GA, Sprint 6+)

Эти пункты **не блокируют v1.0.0**, но попадают в `KNOWN_ISSUES.md` и план на v1.0.1 / v1.1.0.

- [ ] **SOC2 Type 1 readiness** (P4-09) — partial, post-GA full audit
- [ ] **Compliance logging** с retention 7 лет (P4-17)
- [ ] **mTLS через Istio/Linkerd** (Phase 5+)
- [ ] **Polygon.io** интеграция (платная)
- [ ] **Submodule → subtree** полная миграция (P5-13)
- [ ] **Decommiss dev-environment** (P5-15)
- [ ] **AstroFin-Sentinel-v6** (submodule migration artifacts) — если будет

---

## 5. 📋 Pre-PRR Checklist (за 3 дня до GA)

**Дата выполнения:** 2026-08-06 (Ср) — за 3 дня до PRR

### 5.1 Verification

- [ ] Все 88 задач бэклога выполнены или в `KNOWN_ISSUES.md` с обоснованием
- [ ] Все 5 фаз DoD (§4.1–4.6 из `DEFINITION_OF_DONE.md`) ✅
- [ ] Все Critical (🟥) пункты §2 этого чек-листа — **выполняются по факту**, не на бумаге
- [ ] Sprint 5 burndown показывает 100 % commit (≥ 47 ч done)

### 5.2 Smoke Tests (manual + automated)

- [ ] **Login flow:** `POST /auth/login` → JWT → `GET /users/me` с Bearer → 200 OK
- [ ] **Signal flow:** `POST /signal/BTCUSDT` → оркестратор → 13 агентов → response с confidence и direction
- [ ] **Backtest flow:** `POST /backtest` → 30 сек → response с метриками (Sharpe, max drawdown)
- [ ] **Health checks:** `/livez` (200), `/readyz` (200 с Redis+DB up, 503 с DB down)
- [ ] **Sentry:** вызвать искусственную ошибку → Sentry UI показывает event за < 30 сек
- [ ] **Tracing:** `GET /signal/ETHUSDT` → Tempo UI показывает полный trace
- [ ] **Alerts:** вызвать test alert → Telegram получает сообщение за < 60 сек

### 5.3 Rollback Plan

- [ ] **Rollback runbook** в `docs/ROLLBACK.md` (или секция в `RUNBOOK.md`)
- [ ] **Previous version tagged:** `v0.9.5` или `v1.0.0-rc.1` доступен для `kubectl rollout undo`
- [ ] **Database migration rollback:** `alembic downgrade -1` протестирован
- [ ] **Communication plan:** кто пишет в Slack/email при rollback (Tech Lead, DevOps on-call)

### 5.4 Stakeholders

- [ ] **Email stakeholders** за 3 дня: "GA scheduled for 2026-08-09, please review RELEASE_CHECKLIST"
- [ ] **Demo scheduled** для Пт (2026-08-08) с product team
- [ ] **Customer-facing changelog** подготовлен (P4-14)

---

## 6. 🎯 PRR Meeting Agenda (2026-08-08, Пт)

**Длительность:** 1.5 ч
**Участники:** Tech Lead, Product Owner, DevOps Lead, Security Engineer (если есть), 1 Backend Senior

### Agenda

| # | Тема | Длительность | Owner |
|---|------|---:|---|
| 1 | Sprint 5 review (demo) | 20 мин | Backend Senior |
| 2 | Release Checklist walkthrough (этот документ) | 25 мин | Tech Lead |
| 3 | RISK_REGISTER review — top-3 риска | 10 мин | Tech Lead |
| 4 | SLO/metrics dashboard review | 10 мин | DevOps Lead |
| 5 | Security gate (pen-test, SLSA, scan results) | 10 мин | Security Engineer |
| 6 | Open questions / concerns | 10 мин | All |
| 7 | **GO/NO-GO vote** | 5 мин | Tech Lead + Product Owner |

**GO criteria:** Все 🟥 Critical (раздел 2) ✅ + Tech Lead + Product Owner за.

**NO-GO criteria:** Любой 🟥 ❌ ИЛИ Tech Lead/Product Owner против ИЛИ > 2 🟧 Important отсутствует.

### Decision Record

После PRR создаётся `docs/prr/2026-08-08_PRR_v1.0.0.md`:

```markdown
# PRR v1.0.0 — 2026-08-08

## Decision: GO ✅ / NO-GO ❌

## Vote
- Tech Lead (@asurdev): GO / NO-GO
- Product Owner: GO / NO-GO
- DevOps Lead: GO / NO-GO
- Security Engineer: GO / NO-GO (если присутствует)

## Critical items status
[скопировать раздел 2 этого чек-листа с отметками]

## Concerns
[если есть]

## Next steps (if GO)
- 2026-08-08 18:00: tag v1.0.0
- 2026-08-08 19:00: deploy to production
- 2026-08-08 20:00: smoke tests in prod
- 2026-08-09 09:00: public announcement

## Next steps (if NO-GO)
- [ ] Список blockers
- [ ] New target date
- [ ] Action items
```

---

## 7. 🚀 GA Day Procedure (2026-08-08 / 2026-08-09)

### Шаг 1: Tag & Release (Tech Lead)

```bash
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull

# Финальные тесты
pytest -q
ruff check
mypy core/ web/ orchestration/

# Tag
git tag -s v1.0.0 -m "AstroFin Sentinel v1.0.0 GA — 2026-08-08"
git push origin v1.0.0

# GitHub Release
gh release create v1.0.0 \
  --title "AstroFin Sentinel v1.0.0" \
  --notes-file docs/RELEASE_NOTES_v1.0.0.md \
  --target release/1.0.0
```

### Шаг 2: Deploy (DevOps Lead)

```bash
# Через Argo Rollouts
kubectl apply -f deploy/k8s/v1.0.0/
argocd app sync astrofin-prod

# Мониторинг
watch kubectl get pods -n astrofin
# Должно показать canary 5% → 25% → 100% за < 20 мин
```

### Шаг 3: Post-Deploy Verification (Backend Senior)

```bash
# Smoke test
curl -f https://api.astrofin.io/livez
curl -f https://api.astrofin.io/readyz
curl -X POST https://api.astrofin.io/auth/login -d '{"user":"smoke","pass":"***"}'

# Sentry test
curl -X POST https://api.astrofin.io/signal/INVALID -H "Authorization: Bearer ***"
# Должно появиться в Sentry за < 30 сек
```

### Шаг 4: Public Announcement (Tech Lead)

```bash
# Reddit / HN
[schedule post on r/MachineLearning, r/algotrading]

# Twitter / X
[tweet with demo video]

# Blog
[publish post на astrofin.io/blog/v1.0.0-launch]
```

### Шаг 5: Post-Release Monitoring (On-call, 24h)

- [ ] Следить за SLO dashboard: latency, error rate
- [ ] Следить за error budget burn rate
- [ ] Быть готовым к rollback (runbook открыт)
- [ ] Slack channel `#astrofin-prod` активен

---

## 8. 📊 Release Health Metrics (post-GA, W6)

Через 1 неделю после GA (2026-08-16):

| Метрика | Target | Как измерить |
|---|---|---|
| API availability | ≥ 99.9 % | Grafana uptime за 7 дней |
| API latency p95 | < 500 ms | Prometheus histogram_quantile |
| Error rate | < 0.1 % | Sentry + Prometheus |
| Daily active signals | > 100 (baseline) | Business metric |
| Customer issues (GitHub) | < 5 High, 0 Critical | `gh issue list --label critical --state open` |
| Mean time to recovery (MTTR) | < 30 мин | Incident log |
| Backup success rate | 100 % | WAL-G logs |

Если targets не достигнуты — эскалация в Tech Lead, обсуждение v1.0.1 hotfix.

---

## 9. 🔗 Связанные документы

- `file 'docs/DEFINITION_OF_DONE.md'` — базовые DoD (task/sprint/phase), на которых основан этот чек-лист
- `file 'docs/RISK_REGISTER.md'` — top-3 риска в PRR
- `file 'docs/DEPENDENCIES.md'` — critical path на PRR
- `file 'RELEASE_PLAN_v1.0.0.md'` — даты и timeline
- `file 'EXECUTIVE_SUMMARY.md'` — one-pager для stakeholders
- `file 'PRODUCTION_BACKLOG.md'` §8 — critical path (16 задач)
- `file 'SPRINT_5.md'` — execution plan для W5

---

## 10. ✅ Final Sign-Off

**GA v1.0.0 Release Approval:**

| Role | Name | Date | Signature |
|---|---|---|---|
| Tech Lead | @asurdev | 2026-08-08 | _________ |
| Product Owner | _________ | 2026-08-08 | _________ |
| DevOps Lead | _________ | 2026-08-08 | _________ |
| Security Engineer | _________ | 2026-08-08 | _________ |

**Release Manager:** @asurdev
**Backup Release Manager:** _________ (P4-10 — bus factor)

---

> 🚦 **Этот чек-лист заполняется один раз — в W5 (2026-08-03..09).** Хранится в `docs/prr/2026-08-08_PRR_v1.0.0.md` после GA как исторический артефакт.

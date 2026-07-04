# 🗓️ AstroFin Sentinel — Week 4 Sprint (Phase 3 finish + Phase 4 start)

> **Sprint Window:** 2026-07-27 (Mon) → 2026-08-02 (Sun) — 5 рабочих дней
> **Sprint Goal:** Завершить Phase 3 (SLI/Prometheus rules/Alertmanager/Grafana v2/Sentry/chaos/perf baseline) и начать Phase 4 (threat model, SAST/DAST, container scan, compliance docs, runbook). На выходе — SLO burn-rate alerts шлют в Telegram, Grafana показывает SLO-метрики, threat model опубликован, pen-test начат, runbook для on-call готов.
> **Capacity:** 80 ч (1 FTE) / 120 ч (1.5 FTE)
> **Всего задач:** 16 (8 из Phase 3 finish + 5 из Phase 4 MUST + 3 sub-task P3-02a/b, P3-05a, P4-01; pen-test P4-02 уточнён в Carry-over)
> **Estimated effort:** 68 ч → utilization 85 % (12 ч buffer)
> **Приоритет:** 🟥 MUST + 🟧 SHOULD (MoSCoW)

---

## 📊 Sprint 4 Snapshot

| Метрика | Значение |
|---|---|
| Задач в спринте | 16 (6 backend, 6 devops, 3 security, 1 docs) |
| Общий объём | 68 ч |
| Capacity (1 FTE) | 80 ч |
| **Buffer** | **12 ч (15 %)** ← низкий, т.к. chaos + pen-test — исследовательские задачи |
| Должно быть закрыто | 14 новых + 2 carry-over из Sprint 3 |
| Carry-over из Sprint 3 | Ожидается 0–2 задачи (P3-15, pgvector tuning) |
| Sprint 3 velocity baseline | 62 ч / 64 ч (97 %) |
| **Sprint 4 commit** | 68 ч / 80 ч (85 %) — высокий, но критичные Phase 3 MUST доделываем |

---

## 🎯 Sprint Goal в 3 измеримых результатах

1. **SLO & Alerts в проде:** SLI exporters работают (http/db/agent histograms). Prometheus recording rules + SLO burn-rate alerts (1h/6h, 6h/3d, 24h/30d multi-window) активны. Alertmanager шлёт тестовый alert в Telegram за < 30s. Grafana dashboard `/d/slo-overview` показывает error budget remaining в реальном времени.
2. **Tracing & Sentry:** Trace-propagation fix (W3C traceparent в async tasks + HTTP) применён. Loki log aggregation с promtail + derived fields (trace_id, request_id) работает. Sentry интегрирован в FastAPI/Flask/aiohttp, тестовая ошибка из staging приходит в Sentry UI. PII redaction доказательно удаляет `api_key=...` из логов.
3. **Chaos & Perf baseline:** Chaos-тесты (kill pod, latency injection, network partition) отрабатывают, recovery < 30s, метрики фиксируют. Locust-baseline закоммичен в `tests/load/baselines.json`, CI падает при деградации > 20 %. Security: threat model STRIDE опубликован, semgrep+pip-audit+trivy в CI блокируют merge при high.

---

## 📅 Дневной план (1 FTE baseline, 8 ч/день)

> ⚠️ **Структура:** Каждый день имеет 1–2 **фокусных задачи** + 0–1 **background**. Sub-tasks пронумерованы `День.Номер`.

### Пн, 27 июля — Phase 3 finish: SLI exporters + Prometheus rules (ч.1)

**Фокус дня:** Метрики + SLO recording rules.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P3-01** | SLO/SLI определения: `docs/SLO.md` — user-facing API (latency p95 < 500ms, error rate < 0.1%, availability 99.9% monthly), backtest API (p95 < 30s, success > 99%), ML-inference (p95 < 200ms). Error budget calculation | 3 | DevOps | Sprint 3 P2-13 (perf baseline) |
| 2 | **P3-02a** | SLI exporters: `observability/sli.py` — `http_request_duration_seconds` histogram (slo-бакеты: 0.1, 0.25, 0.5, 1, 2, 5), `http_requests_total{code}`, `db_query_duration_seconds` | 3 | Backend | P3-01 |
| 3 | **P3-02b** | `agent_runtime_seconds{agent}` histogram для 13 agents + RAG retrieval latency | 2 | Backend | P3-02a |
| 4 | _background_ | Code review для 3–5 PRов из Sprint 3 carry-over | 1 | Backend | — |

**AC конца дня:**
- [ ] `docs/SLO.md` существует, утверждён, содержит error budget calc
- [ ] `observability/sli.py` экспортирует метрики на `/metrics` endpoint
- [ ] `curl http://localhost:8050/metrics | grep http_request_duration_seconds_bucket` показывает buckets
- [ ] `agent_runtime_seconds` per agent видны (FundamentalAgent, QuantAgent, etc.)

**Команды на утро:**
```bash
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull
workon astrofin

# Утренняя проверка
cat /tmp/sprint3_retro.md 2>/dev/null || echo "No retro yet"
gh issue list --milestone "Sprint 3" --state closed --json number,title | head -20
curl http://localhost:8050/metrics 2>/dev/null | head -5 || echo "Metrics endpoint not yet implemented"
```

---

### Вт, 28 июля — Phase 3 finish: Prometheus rules + Alertmanager

**Фокус дня:** Recording rules, SLO burn-rate alerts, маршрутизация в Telegram/Slack/PagerDuty.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P3-03** | Prometheus recording rules: `deploy/monitoring/prometheus-rules.yml` — pre-computed rates (`rate:http_requests:5m`, `histogram_quantile:0.95:http_request_duration:5m`), SLO burn-rate alerts (multi-window 1h/6h, 6h/3d, 24h/30d) | 4 | DevOps | P3-02a/b |
| 2 | **P3-04** | Alertmanager routing tree: severity (page/critical/warning/info), receivers: Telegram (page), Slack (warning), PagerDuty (critical), email (info). Inhibition rules, repeat intervals 4h/24h | 3 | DevOps | P3-03 |
| 3 | _background_ | Тестовый alert: inject 500-error, проверить что Telegram получил за < 30s | 1 | DevOps | P3-04 |

**AC конца дня:**
- [ ] `promtool check rules deploy/monitoring/prometheus-rules.yml` → 0 errors
- [ ] SLO burn-rate alert `HighBurnRate1h` срабатывает на injected error
- [ ] Telegram bot получает сообщение в течение 30s
- [ ] Inhibition: critical alert подавляет warning для того же service
- [ ] Repeat interval: page не повторяется чаще 4h

**Команды для P3-04:**
```bash
# Проверка recording rules
promtool check rules deploy/monitoring/prometheus-rules.yml

# Тестовый alert
curl -X POST http://alertmanager:9093/api/v1/alerts -d '[{
  "labels": {"alertname":"HighBurnRate1h", "severity":"page", "service":"web"},
  "annotations": {"summary":"Test alert from Sprint 4"}
}]'
# Проверить Telegram: должно прийти сообщение за < 30s
```

---

### Ср, 29 июля — Phase 3 finish: Grafana v2 + PII redaction

**Фокус дня:** SLO-панель в Grafana + scrubber для PII.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P3-05a** | Grafana dashboards v2: SLO-панель (burn-rate, error budget remaining), on-call overview, business metrics (signals per day, agent agreement score, RAG retrieval hit rate) | 4 | DevOps | P3-01 |
| 2 | **P3-09** | PII redaction в логах: scrubber для `email`, `api_key`, `phone`, `card_number`. OpenTelemetry processor + log filter в `core/logging.py` | 3 | Security Engineer | Sprint 3 P3-08 (Loki) |
| 3 | _background_ | Test: отправить лог с `api_key=secret123`, проверить что в Loki идёт `api_key=***` | 1 | Security Engineer | P3-09 |

**AC конца дня:**
- [ ] Grafana dashboard `/d/slo-overview` импортируется, показывает 6 панелей (burn-rate 1h/6h/3d/30d, error budget, MTTR)
- [ ] Business metrics панель показывает signals per day (с Prometheus query)
- [ ] `core/logging.py` PII filter: regex `api_key=[A-Za-z0-9]+` → `api_key=***`
- [ ] `tests/test_pii_redaction.py` 8/8 зелёные
- [ ] Loki query `{app="astrofin"} |= "api_key"` возвращает только redacted строки

---

### Чт, 30 июля — Phase 3 finish: Sentry + APM для воркеров

**Фокус дня:** Error tracking + APM-точки для backtest/audit/RAG.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P3-13** | Sentry integration: `sentry-sdk[fastapi,flask,aiohttp]`, breadcrumbs для ORM и HTTP. Sample rate 10% в prod, 100% для 5xx. PII scrubbing (reuse P3-09 scrubber) | 3 | Backend | P3-09 |
| 2 | **P3-15** | APM-точки для воркеров: KARL backtest loop, AMRE audit, RAG indexing — отдельные span с критическими атрибутами (`backtest_id`, `agent_pool_size`, `vectors_indexed`) | 3 | Backend | Sprint 3 P3-07 (traceprop) |
| 3 | **P3-07** | Trace-propagation fix: `core/tracing.py` инжектит W3C `traceparent` в исходящие HTTP (httpx/aiohttp), прокидывает в async tasks (`asyncio.create_task` + `contextvars`) | 2 | Backend | Sprint 3 P3-06 (Tempo) |

**AC конца дня:**
- [ ] Sentry получает тестовую ошибку из staging
- [ ] `sentry-sdk` не отправляет PII (email, api_key)
- [ ] KARL backtest loop имеет span с `backtest_id` атрибутом
- [ ] RAG indexing имеет span с `vectors_indexed=10000`
- [ ] Async task `asyncio.create_task(agent.run())` сохраняет `traceparent` (verified в Tempo UI)
- [ ] `httpx` исходящие запросы к Ollama/Polygon содержат `traceparent` header

**⚠️ Критично:** P3-07 — основа для distributed tracing. Без него каждый span будет отдельным trace'ом.

---

### Пт, 31 июля — Phase 3 finish: Chaos + Performance baseline + Phase 4 start (Threat model)

**Фокус дня:** Chaos-тесты, locust-baseline, и старт threat model.

| # | ID | Задача | Часы | Owner | Зависимости |
|---|----|--------|-----:|-------|-------------|
| 1 | **P3-10** | Chaos engineering basics: chaos-mesh (или podman chaos test) — kill random pod, latency injection 200ms на 5 мин, network partition между app↔db. Сценарии в `tests/chaos/` | 4 | DevOps | P3-03 |
| 2 | **P3-12** | Performance baseline: Locust-сценарий `tests/load/api_baseline.py` — 100 users, 5 rps, 5 мин. Зафиксировать p50/p95/p99 для каждого эндпоинта. Запускать в CI при изменениях в `orchestration/` и `web/` | 3 | Backend | — |
| 3 | **P4-01** | Threat model STRIDE: `docs/security/THREAT_MODEL.md` — для 4 сервисов (web/api, orchestrator, ml-engine, gpu-worker). 6 STRIDE-категорий | 1 | Security Engineer | — |

**AC конца дня:**
- [ ] `tests/chaos/kill_app_pod.py` отрабатывает, recovery < 30s, метрики фиксируют
- [ ] `tests/chaos/network_partition.py` блокирует app↔db на 2 мин, circuit breaker срабатывает
- [ ] `tests/load/baselines.json` содержит p50/p95/p99 для `/healthz`, `/signal`, `/backtest`
- [ ] `locust -f tests/load/api_baseline.py --headless --users 100 --spawn-rate 5 --run-time 5m` проходит
- [ ] `.github/workflows/perf-baseline.yml` падает при деградации > 20 %
- [ ] `docs/security/THREAT_MODEL.md` — раздел для web/api готов (S+T+R+etc)

**Команды для P3-10:**
```bash
# Chaos-mesh install (один раз)
kubectl apply -f https://mirrors.chaos-mesh.org/v2.6.2/install.sh

# Kill pod test
python tests/chaos/kill_app_pod.py --namespace astrofin --duration 5m
# Смотреть recovery time в Grafana
```

---

## 📅 Выходные (опционально, не в capacity)

> Только если есть энергия или критичные fixes.

| # | ID | Задача | Часы | Зачем |
|---|----|--------|-----:|-------|
| 1 | **P3-14** | Cost monitoring (FinOps): kubecost или self-hosted cost-exporter; дэшборд $/request, $/signal, $/backtest-run | 4 | FinOps, не блокер |
| 2 | **P3-11** | Synthetic monitoring: blackbox-exporter → `/healthz` каждые 30s + multi-region prober (Amsterdam, Singapore, Virginia) | 3 | Расширение observability |

---

## 📈 Burndown (ожидаемый)

| День | Запланировано (нарастающий итог) | Идеальный burndown | Реалистичный (chaos + pen-test surprises) |
|------|--------------------------------:|-------------------:|----------------------------------------:|
| Пн | 9 ч (P3-01, P3-02a/b + 1ч review) | 9 | 9 |
| Вт | 17 ч (+P3-03, P3-04 + 1ч test) | 17 | 16 (recording rules tuning = +1ч) |
| Ср | 25 ч (+P3-05a, P3-09 + 1ч test) | 25 | 24 (Grafana provisioning = +1ч) |
| Чт | 33 ч (+P3-13, P3-15, P3-07) | 33 | 31 (Sentry SDK conflicts = +2ч) |
| Пт | 41 ч (+P3-10, P3-12, P4-01) | 41 | 39 (chaos-mesh install = +2ч) |
| **Итого** | **68 ч** | **68/68** | **66/68 (97 %)** |

> **Стратегия:** Sprint 4 commit 85% — высокий. Если chaos/pen-test растягиваются, перенести P3-14 (FinOps) в Sprint 5.

---

## 📦 Definition of Done для Sprint 4

### Observability (Phase 3 finish)
- [ ] `docs/SLO.md` утверждён, error budget dashboard показывает burn-rate в реальном времени
- [ ] SLI exporters работают (http_request_duration, agent_runtime, db_query)
- [ ] Prometheus recording rules: 0 errors при `promtool check rules`
- [ ] SLO burn-rate alerts (1h/6h, 6h/3d, 24h/30d) активны
- [ ] Alertmanager шлёт тестовый alert в Telegram за < 30s
- [ ] Grafana `/d/slo-overview` dashboard с 6 панелями (burn-rate, error budget, MTTR)
- [ ] Business metrics dashboard: signals per day, agent agreement score, RAG hit rate
- [ ] Trace-propagation W3C работает (async tasks, HTTP outbound)
- [ ] PII redaction в логах: `api_key=***` в Loki
- [ ] Sentry получает тестовую ошибку из staging
- [ ] KARL backtest + RAG indexing имеют APM spans
- [ ] Chaos test kill-pod отрабатывает, recovery < 30s
- [ ] Locust-baseline закоммичен, CI падает при деградации > 20%

### Security (Phase 4 start)
- [ ] `docs/security/THREAT_MODEL.md` опубликован (все 6 STRIDE для 4 сервисов)
- [ ] semgrep ruleset в `quality-gate.yml` блокирует merge при ≥1 high

### Качество
- [ ] `pytest -q` ≤ 8 fail (было 12 после Sprint 3, −4 от observability/security тестов)
- [ ] `ruff check` 0 errors, `bandit -r` без новых high
- [ ] Coverage ≥ 70 % для `core/`, `web/`, `orchestration/`
- [ ] Code review пройден для всех PR

---

## 🔗 Зависимости от Sprint 3 (blockers)

| Зависит от | Sprint 4 задача | Что нужно от Sprint 3 |
|------------|----------------|----------------------|
| Sprint 3 P2-13 (vacuum tuning) | **P3-01** (SLO defs) | DB performance baseline |
| Sprint 3 P3-06 (Tempo) | **P3-07** (traceprop) | OTel collector работает |
| Sprint 3 P3-08 (Loki) | **P3-09** (PII) | Log aggregation готова |
| Sprint 3 P3-13 (Sentry placeholder) | **P3-13** (полная интеграция) | Sentry SDK установлен |
| Sprint 3 P3-15 (placeholder) | **P3-15** (APM spans) | APM hooks в orchestrator |

> ⚠️ **Если Sprint 3 задержится** по P3-06 (Tempo) или P3-08 (Loki), Sprint 4 нужно сдвинуть.

---

## 🔄 Carry-over Plan (если что-то не успеем)

| Задача | Приоритет | Куда идёт |
|--------|----------|-----------|
| P3-14 (FinOps) | 🟨 Low | Sprint 5 background |
| P3-11 (synthetic monitoring) | 🟧 Should | Sprint 5 (3ч) |
| P4-13 (API doc-site) | 🟧 Should | Sprint 5 (6ч) |
| Pen-test report | 🟧 Should | Sprint 5 (если фрилансер не успеет) |

**Sprint 5 preview:** Phase 4 finish (pen-test fixes, SLSA L3, SOC2 readiness, user docs, tabletop) + Phase 5 start (canary, auto-rollback, multi-region DR, GA release v1.0.0).

---

## ⚠️ Риски Sprint 4

| # | Риск | Вероятность | Импакт | Mitigation |
|---|------|------------:|-------:|------------|
| **R-S4-1** | Prometheus storage растёт быстро (high cardinality `agent` label) | 🟧 Средняя | 🟧 High | Drop метрики с cardinality > 1000; retention 30d |
| **R-S4-2** | Alertmanager routing misconfigured (alerts идут не туда) | 🟧 Средняя | 🟧 High | Dry-run перед prod; тестовые alerts в начале спринта |
| **R-S4-3** | Sentry SDK конфликтует с существующими логгерами (structlog) | 🟨 Низкая | 🟧 Medium | Интегрировать через SentryLoggingIntegration, не заменять structlog |
| **R-S4-4** | Chaos-mesh требует privileged pods, может не пройти в managed k8s | 🟧 Средняя | 🟨 Medium | Fallback на podman chaos test (локально); для k8s — chaos-mesh в отдельном namespace |
| **R-S4-5** | Threat model требует экспертизы, занимает > 8ч (single FTE) | 🟧 Средняя | 🟧 High | Привлечь security инженера part-time; использовать STRIDE-by-example template |
| **R-S4-6** | PII scrubber не покрывает все edge cases (PII в JSON values) | 🟧 Средняя | 🟧 High | Comprehensive test suite `tests/test_pii_redaction.py`; review в code review |
| **R-S4-7** | Locust-baseline слишком flaky (CI падает на network jitter) | 🟧 Средняя | 🟨 Medium | Threshold 20% (не 10%); rerun при flake |
| **R-S4-8** | Trace-propagation fix ломает 2-3 endpoints (httpx custom transport) | 🟨 Низкая | 🟧 Medium | Feature flag `TRACE_PROPAGATION_ENABLED` для быстрого rollback |

### Топ-3 риска, требующих внимания в начале спринта

1. **R-S4-1 (Prometheus cardinality)** — проверить метрики в Пн, не в Ср
2. **R-S4-2 (Alertmanager routing)** — тестовые alerts во Вт, не в Чт
3. **R-S4-5 (Threat model effort)** — security инженер part-time с самого начала

---

## 🔀 Параллелизм (если 2 FTE)

| Трек | Owner | Задачи | Часы |
|------|-------|--------|-----:|
| **A — Backend** | Senior Backend (1 FTE) | P3-02a/b, P3-07, P3-13, P3-15 | 12 |
| **B — DevOps** | Senior DevOps (1 FTE) | P3-01, P3-03, P3-04, P3-05a, P3-10 | 18 |
| **C — Security** | Security Engineer (0.5 FTE) | P3-09, P4-01, P4-03 | 8 |
| **D — Backend (perf)** | Backend (0.5 FTE) | P3-12, P4-04 | 6 |
| **E — DevOps (deferred)** | DevOps (0.5 FTE, Sprint 5) | P3-11, P3-14 | 7 |

**2 FTE sprint commit:** 68 ч / 120 ч (57 %) — два трека закроются в Ср-Чт, освобождая Пт для Sprint 5 planning.

**Если 1.5 FTE:** Backend full + DevOps part-time (0.5) + Security part-time (0.25).

---

## 🛠️ Команды для старта (Пн утро)

```bash
# 1. Синхронизироваться
cd /home/workspace/astrofin-sentinel-platform
git checkout release/1.0.0
git pull origin release/1.0.0
workon astrofin

# 2. Создать Sprint 4 milestone
gh api repos/mahaasur13-sys/astrofin-sentinel-platform/milestones \
  -f title="Sprint 4 (Observability finish + Security start)" \
  -f due_on="2026-08-02T23:59:59Z"

# 3. Создать 16 issues
gh issue create --title "[P3-01] SLO/SLI definitions" --milestone "Sprint 4" ...

# 4. Утренний check
gh issue list --milestone "Sprint 3" --state all --json number,title,state | jq '.[] | select(.state=="open")'
cat /tmp/sprint3_retro.md 2>/dev/null
curl http://localhost:8050/metrics 2>/dev/null | grep -c "http_request_duration" || echo "No metrics yet"
```

---

## 📊 Метрики успеха Sprint 4

| Метрика | Цель | Как измерить |
|---------|-----|--------------|
| Sprint commit | 85 % (68/80) | `gh issue list --milestone "Sprint 4" --state closed` |
| Carry-over из Sprint 3 | ≤ 2 задачи | Standup Пн |
| New critical bugs | 0 | `gh issue list --label critical --state open` |
| `pytest` pass rate | ≥ 97 % (было ~96 % после Sprint 3) | `pytest -q tests/ \| tail -1` |
| Coverage | ≥ 70 % (core/web/orchestration) | `coverage report` |
| SLO burn-rate alert latency | < 30s (Telegram) | manual test в Вт |
| Trace propagation coverage | 100% для outbound HTTP | OTel collector stats |
| PII redaction test pass | 100% (8/8) | `pytest tests/test_pii_redaction.py` |
| Chaos recovery time | < 30s (kill pod) | `tests/chaos/kill_app_pod.py` |
| Locust baseline p95 | < 500ms (commit baseline) | `tests/load/baselines.json` |
| Threat model coverage | 4 services × 6 STRIDE = 24 cells | `docs/security/THREAT_MODEL.md` |

---

## 🤝 Ceremonies

| Событие | Время | Участники | Длительность |
|---------|-------|-----------|-------------:|
| **Sprint 4 Planning** | Пт 24 июля 16:00 | Вся команда | 1 ч |
| **Daily Standup** | Пн–Пт 09:30 | Backend + DevOps + Security | 15 мин |
| **Mid-sprint Check** | Ср 14:00 | Backend + DevOps | 30 мин (burndown) |
| **Sprint Review** | Пт 31 июля 16:00 | + Stakeholders | 1 ч |
| **Sprint 4 Retro** | Пт 31 июля 17:00 | Вся команда | 1 ч |
| **Sprint 5 Planning** | Пт 31 июля 18:00 | Вся команда | 1 ч |

**Sprint Review demo agenda:**
1. SLO dashboard live: burn-rate 1h/6h/3d, error budget remaining
2. Test alert в Telegram (inject 500-error, watch PagerDuty escalation)
3. Tempo trace запроса: web → orchestrator → 13 agents → DB (полный span tree)
4. PII redaction proof: лог с `api_key=secret` → Loki показывает `api_key=***`
5. Chaos test demo: kill pod, watch recovery < 30s в Grafana
6. Threat model walkthrough: STRIDE для web/api

---

## 📎 Приложение A. Carry-over Checklist из Sprint 3

Заполнить в начале Sprint 4 (Пн утро):

```
Sprint 3 Carry-over
═══════════════════════════════════════════════
□ P2-02 (pgvector migration) → Done? Y/N
□ P2-03 (RLS) → Done? Y/N
□ P2-07 (CloudNativePG HA) → Done? Y/N
□ P2-09 (read-replica routing) → Done? Y/N
□ P3-06 (Tempo stack) → Done? Y/N
□ P3-08 (Loki logs) → Done? Y/N
□ P3-15 (APM для воркеров) → Done? Y/N
═══════════════════════════════════════════════
Total carry-over: __/7

If carry-over > 2: reduce Sprint 4 scope (drop P3-14)
If carry-over = 0: add P4-13 (API doc-site) preview to Sprint 4
```

---

## 📎 Приложение B. Где искать что

| Что | Где |
|-----|-----|
| Sprint 3 issues | `gh issue list --milestone "Sprint 3"` |
| Sprint 3 retro | `/tmp/sprint3_retro.md` (создаётся в конце Sprint 3) |
| MoSCoW-приоритезация | `MOSCOW_PRIORITIZATION.md` |
| Полный бэклог | `PRODUCTION_BACKLOG.md` |
| Week 1 sprint | `SPRINT_1.md` |
| Week 2 sprint | `SPRINT_2.md` |
| Week 3 sprint | `SPRINT_3.md` |
| Week 4 sprint (этот) | `SPRINT_4.md` |
| SLO template | https://sre.google/workbook/table-of-contents/ |
| STRIDE guide | https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-getting-started |
| OTel Python docs | https://opentelemetry.io/docs/languages/python/ |
| Sentry FastAPI | https://docs.sentry.io/platforms/python/guides/fastapi/ |

---

## ✅ Готовность к старту

Pre-flight checklist (Пн 09:00):

- [ ] `gh auth status` — logged in
- [ ] `git status` — clean, on `release/1.0.0`
- [ ] `pytest -q tests/ | tail -1` — pass rate из Sprint 3
- [ ] `gh issue list --milestone "Sprint 3" --state closed | wc -l` — Sprint 3 velocity
- [ ] Прочитать `SPRINT_3.md` и `MOSCOW_PRIORITIZATION.md`
- [ ] Проверить `Sprint 3 retro` (если был)
- [ ] `Sprint 4 milestone` создан в GitHub
- [ ] Slack/email уведомление команде: "Sprint 4 starts"
- [ ] Prometheus/Tempo/Loki работают (от Sprint 3)

---

> 📌 **Этот документ — операционный план на неделю.** Использовать как checklist на daily standup. После Sprint 4 retro обновить на основе реальной velocity.

# 🗺️ AstroFin Sentinel — План развития v1.1.0 (post-beta)

> **Дата:** 2026-07-26
> **Исходная точка:** v1.0.0-beta (Sprint F closed, 8/8 CI green, zero-WARN, 15 alerts, 6 dashboards)
> **Цель GA:** v1.0.0 — 2026-09-15
> **Горизонт плана:** 4 недели (28.07 – 22.08) → hardening 2 недели → GA 15.09

---

## Текущий срез (26.07.2026)

| Параметр | Значение |
|----------|---------|
| Репо | `mahaasur13-sys/astrofin-sentinel-platform` |
| Ветка | `master` @ `26e34914` |
| Тег | `v1.0.0-beta` |
| CI | 8/8 green (Arch linter, Lint, Unit 3.11/3.12, Data room, Sub-package, Status, Security ⚠️ non-blocking) |
| Агенты | 13 активных (Fundamental 20% … Cycle 5%) |
| Meta-RL | inference per request + nightly training |
| API | FastAPI + rate limiting + circuit breakers |
| БД | TimescaleDB hypertable (0008) + compression (0009) + WAL-G sidecar |
| Мониторинг | 15 алертов, 6 дашбордов / 43 панели, Loki + Promtail |
| Безопасность | PII scrubber 19/19, audit 10/10 closed, secrets rotation |
| Документация | 3 runbooks, incident response template, CHANGELOG, sprint docs |

### Что ещё висит (из handoff)

| Шаг | Статус |
|-----|--------|
| `test_frontend_contract` flaky test | ✅ 4/4 green (REQUIRE_AUTH=false + conftest), но CI показывает failure на последних run'ах — требует стабилизации |
| Bandit cleanup | ✅ `.bandit` 8 skips + justification, CI `\|\| true` |
| Alertmanager credentials | ⚠️ заполнить production creds |
| docker-compose staging test | ⚠️ проверить полный стек |
| Backtest report review | ⚠️ первый отчёт после пилота |
| On-call ротация | ⚠️ назначить |

---

## Фаза 7: Sprint G — Stabilization & GA Prep (28.07 – 08.08, 2 недели)

### Неделя 1: Закрыть оставшиеся блокеры (28.07 – 01.08)

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| **G-01** | Стабилизировать `test_frontend_contract` — investigate CI vs local расхождение, зафиксировать seed/данные | P0 | 3h | — |
| **G-02** | Заполнить Alertmanager production credentials (Slack webhook, PagerDuty routing key) в GitHub Secrets | P0 | 1h | — |
| **G-03** | `docker-compose up` staging → full stack smoke test (postgres + redis + app + dash + telegram bot) | P0 | 4h | G-02 |
| **G-04** | Запустить backtest pipeline на 90-дневном окне, сгенерировать первый отчёт (`docs/performance/backtest-report-2026-07.md`) | P1 | 3h | — |
| **G-05** | CI: починить красные юнит-тесты на Python 3.11/3.12 (2 failing jobs из последнего run) | P0 | 4h | G-01 |
| **G-06** | Проверить WAL-G restore drill: backup → drop DB → restore → verify integrity | P0 | 2h | — |
| **G-07** | Назначить on-call ротацию, обновить `docs/RUNBOOK.md` escalation contacts | P1 | 1h | — |

**Итого неделя 1:** 7 задач / ~18 часов

### Неделя 2: Hardening + Docs (04.08 – 08.08)

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| **G-08** | Нагрузочное тестирование: пройти Locust `locustfile_sprint_e.py` на staging, записать baseline | P1 | 4h | G-03 |
| **G-09** | SLO/SLI калибровка: проверить Prometheus recording rules на staging, выставить реалистичные SLO (99.5% → возможно 99.0% для beta) | P1 | 3h | G-03 |
| **G-10** | `docs/runbooks/` — дополнить runbook для ALERT_PostgresConnectionPoolExhausted + ALERT_RedisMemoryHigh | P1 | 2h | — |
| **G-11** | `docs/RELEASE_NOTES_v1.0.0.md` — черновик release notes (features, breaking changes, upgrade guide) | P1 | 3h | — |
| **G-12** | `docs/ARCHITECTURE.md` — актуализировать: отразить TimescaleDB hypertables, asyncpg pool, WAL-G, PII scrubber | P2 | 2h | — |
| **G-13** | GitHub Release: создать draft release v1.0.0 с авто-generated changelog из PR history | P2 | 1h | — |

**Итого неделя 2:** 6 задач / ~15 часов

---

## Фаза 8: Hardening Window (11.08 – 22.08, 2 недели)

### Неделя 3: Performance & Resilience (11.08 – 15.08)

| ID | Задача | Приоритет | Оценка |
|----|--------|-----------|--------|
| **H-01** | Профилирование агентов: найти top-3 bottlenecks (cProfile/py-spy), оптимизировать | P1 | 6h |
| **H-02** | Нагрузочный тест на 100 RPS → зафиксировать breaking point, определить горизонтальный scaling ceiling | P1 | 4h |
| **H-03** | Circuit breaker тестирование: эмулировать отказ CoinGecko/Ephemeris/LLM → проверить graceful degradation | P1 | 3h |
| **H-04** | Redis failover: отключить Redis → проверить fallback на direct execution (без кэша) | P2 | 2h |
| **H-05** | Prometheus alert storm test: триггернуть все 15 алертов → проверить routing + dedup | P2 | 2h |

### Неделя 4: Final Polish (18.08 – 22.08)

| ID | Задача | Приоритет | Оценка |
|----|--------|-----------|--------|
| **H-06** | Полный integration test: API → agents → KARL synthesis → dashboard → Telegram alert — end-to-end | P0 | 4h |
| **H-07** | Security review: повторный Bandit scan (без `\|\| true`), убрать skip-правила где возможно | P1 | 3h |
| **H-08** | Dependency audit: `pip-audit` / `safety check` на все зависимости, обновить уязвимые | P1 | 2h |
| **H-09** | `README.md` — production quickstart (как развернуть с нуля за 5 минут) | P1 | 2h |
| **H-10** | Code freeze + финальное review CHANGELOG, DEPLOYMENT, RELEASE_NOTES | P0 | 2h |

---

## Фаза 9: GA Release (25.08 – 15.09)

| Дата | Действие |
|------|---------|
| **25.08** | Code freeze — только bugfixes |
| **01.09** | Release candidate `v1.0.0-rc1` — staging deploy, smoke test |
| **05.09** | Go/No-Go meeting: review hardening results, SLO compliance, backup integrity |
| **08.09** | Final release candidate `v1.0.0-rc2` (если нужен) |
| **15.09** | 🎉 **v1.0.0 GA** — tag, release notes, GitHub Release publish, announce в Telegram |

---

## Долгосрочный горизонт: v1.1.0 → v1.2.0

### v1.1.0 (Q4 2026)

- **Live trading integration** — Binance/Bybit API через `trading/execution/`
- **Real-time WebSocket stream** — цены + сигналы в dashboard
- **Agent marketplace** — кастомные агенты через plugin system
- **Multi-user dashboard** — роли: admin, trader, viewer
- Grafana public dashboard (read-only share)

### v1.2.0 (Q1 2027)

- **Multi-region** — PostgreSQL read replicas, Redis Cluster
- **GraphQL API** — альтернатива REST
- **ML A/B testing framework** — shadow deployment для Meta-RL
- **Mobile PWA** — dashboard на телефоне
- SOC2 Type 1 audit (если есть заказчик)

---

## Ресурсы и риски

| Ресурс | Доступность |
|--------|------------|
| Felix (core dev) | 1 FTE |
| Zo Computer (облачный стенд) | 24/7 |
| GitHub Actions (CI) | 2000 min/month (free tier) |

| Риск | Impact | Mitigation |
|------|--------|------------|
| Flaky `test_frontend_contract` возвращается | High | Зафиксировать seed, изолировать от внешних API |
| Staging не повторяет production (разные версии deps) | Medium | Docker Compose с фиксированными тегами образов |
| WAL-G restore не работает под нагрузкой | High | DR drill с реальным объёмом данных (не на пустой БД) |
| Bandit находит новые CVE перед релизом | Low | Еженедельный security scan + быстрый triage |

---

## Чек-лист GA (из `PRODUCTION_BACKLOG.md` Appendix A)

- [ ] Все P0 задачи (G-01–G-07, H-06, H-10) закрыты
- [ ] 0 failing CI jobs
- [ ] Bandit 0 HIGH/MEDIUM (допустимы LOW с justification)
- [ ] WAL-G restore drill пройден (integrity check)
- [ ] Load test baseline записан (`docs/performance/load-test-2026-08.md`)
- [ ] SLO: 99.0% за неделю staging (реалистичная цель)
- [ ] Release notes опубликованы
- [ ] Alertmanager routing проверен (Slack + email)
- [ ] On-call контакты актуальны
- [ ] `git tag v1.0.0 && git push --tags`

---

> 📌 **Этот план заменяет** `MOSCOW_PRIORITIZATION.md` и `RELEASE_PLAN_v1.0.0.md` в части недельных спринтов. Фазы 0-5 из `PRODUCTION_BACKLOG.md` считаются выполненными (Sprints A-F). Оставшиеся задачи — в секции «Фаза 7» этого документа.

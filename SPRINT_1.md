# 🏃 Sprint G-1 — Stabilization Week (28.07 – 01.08)

> **Спринт:** G-1 (Неделя 1 Фазы 7)
> **Цель:** Закрыть оставшиеся P0-блокеры перед hardening
> **Definition of Done:** 0 failing CI jobs, staging stack smoke test passed, backtest report generated

---

## Backlog (7 задач, ~18 ч)

### 1. G-01: Стабилизировать `test_frontend_contract` 🔴 P0 • 3h

**Проблема:** CI показывает failure на Unit tests (3.11/3.12), локально проходит. Расхождение CI vs local.

**План:**
1. `gh run view <id> --log --job=<unit-3.12>` — посмотреть точный traceback
2. Проверить `conftest.py` — возможно разное поведение pytest plugins
3. Зафиксировать seed в тесте (`random.seed(42)`, `np.random.seed(42)`)
4. Изолировать от внешних API вызовов (mock или skip в CI)
5. PR → проверить CI green на обоих Python

**Acceptance:** 3 последовательных CI run'а без flaky failure

---

### 2. G-02: Alertmanager production credentials 🔴 P0 • 1h

**План:**
1. Создать Slack webhook для канала `#alerts-astrofin`
2. Запросить PagerDuty routing key (или placeholder)
3. Добавить в GitHub Secrets: `ALERTMANAGER_SLACK_WEBHOOK`, `ALERTMANAGER_PD_ROUTING_KEY`
4. Обновить `alertmanager.yml` — заменить `placeholder` на `$ALERTMANAGER_SLACK_WEBHOOK`
5. Триггернуть тестовый alert → проверить доставку в Slack

**Acceptance:** Тестовый alert пришёл в Slack

---

### 3. G-03: docker-compose staging smoke test 🔴 P0 • 4h

**План:**
1. `docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d`
2. Проверить:
   - PostgreSQL: `docker exec astrofin-postgres pg_isready`
   - Redis: `docker exec astrofin-redis redis-cli ping`
   - TimescaleDB hypertable: `docker exec astrofin-postgres psql -c "\dt"` → видим hypertable
   - WAL-G sidecar: логи без ошибок
   - App: `curl http://localhost:8050/health` → 200 + `{"status":"healthy"}`
   - Dashboard: `curl http://localhost:8050/` → HTML ответ
   - FastAPI: `curl http://localhost:8000/health`
   - Telegram bot: логи старта без exception
3. Пройти полный цикл: `python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING`
4. Проверить запись в БД, логи агентов в Loki

**Acceptance:** Full stack up, health green, sentinel_v5 отработал

---

### 4. G-04: Backtest pipeline — первый отчёт 🔴 P1 • 3h

**План:**
1. Запустить `python -m backtest.metrics_agent --days 90 --symbols BTCUSDT,ETHUSDT`
2. Проверить вывод: Sharpe, max drawdown, win rate, profit factor
3. Сгенерировать HTML-отчёт: `python -m backtest.metrics_agent --report-html`
4. Сохранить в `docs/performance/backtest-report-2026-07.md`
5. Проверить KPI Control Loop логи (OAP drift, oos_fail_rate)

**Acceptance:** Отчёт сгенерирован, метрики в разумных пределах

---

### 5. G-05: Починить CI (Python 3.11/3.12 unit test failures) 🔴 P0 • 4h

**План:**
1. Анализ логов: `gh run view <latest-failed> --log --job='Unit tests (Python 3.12)'`
2. Категоризировать ошибки:
   - ImportError → проверить `pyproject.toml` / `uv.lock` для 3.11/3.12
   - AssertionError → сравнить с local, искать разницу в окружении
   - Timeout → увеличить timeout или добавить retry
3. Fix → push → `gh run watch`
4. Повторить для Python 3.11

**Acceptance:** 3 последовательных CI run'а — все 8 jobs green

---

### 6. G-06: WAL-G restore drill 🔴 P0 • 2h

**План:**
1. Сделать свежий backup: `wal-g backup-push $PGDATA`
2. Остановить PostgreSQL
3. Удалить data directory: `rm -rf $PGDATA`
4. Restore: `wal-g backup-fetch $PGDATA LATEST`
5. Запустить PostgreSQL, проверить integrity: `pg_isready && psql -c "SELECT count(*) FROM agent_responses"`
6. Документировать в `docs/runbooks/DR_WALG_RESTORE.md`

**Acceptance:** Восстановленная БД содержит те же данные

---

### 7. G-07: On-call ротация 🔴 P1 • 1h

**План:**
1. Назначить primary/secondary on-call в `docs/RUNBOOK.md`
2. Обновить escalation contacts: Slack, Telegram, email
3. Проверить Alertmanager routing: critical → on-call Slack + PagerDuty
4. Создать `docs/runbooks/ONCALL_HANDOVER.md` — шаблон передачи смены

**Acceptance:**
- [ ] `docs/RUNBOOK.md` содержит актуальные контакты
- [ ] Тестовый critical alert доставлен on-call

---

## Sprint Board

| Статус | Задача | Assignee | Estimate |
|--------|--------|----------|----------|
| ⬜ Todo | G-01 test_frontend_contract | felix | 3h |
| ⬜ Todo | G-02 Alertmanager creds | felix | 1h |
| ⬜ Todo | G-03 docker-compose smoke | felix | 4h |
| ⬜ Todo | G-04 Backtest report | felix | 3h |
| ⬜ Todo | G-05 CI fix | felix | 4h |
| ⬜ Todo | G-06 WAL-G drill | felix | 2h |
| ⬜ Todo | G-07 On-call rotation | felix | 1h |

---

## Daily Standup

| День | Фокус | Ожидаемый результат |
|------|-------|---------------------|
| Пн 28.07 | G-01 + G-05 (CI) | root cause flaky test |
| Вт 29.07 | G-02 + G-03 (staging) | docker-compose up green |
| Ср 30.07 | G-03 complete + G-06 (WAL-G) | smoke test + restore drill |
| Чт 31.07 | G-04 + G-07 (backtest + on-call) | первый отчёт |
| Пт 01.08 | Buffer + review | sprint G-1 closed |

---

> 📎 Связано: `DEVELOPMENT_PLAN_v1.1.0.md` · `PRODUCTION_BACKLOG.md` · `GITHUB_PROJECT_SETUP.md`

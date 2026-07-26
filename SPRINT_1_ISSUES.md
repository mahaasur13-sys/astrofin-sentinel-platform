# 📋 Sprint G-1 — Ready-to-Create GitHub Issues

> **Как использовать:** скопировать блок → `gh issue create --title "..." --body "..." --label "..." --milestone "..."`

---

## G-01: Stabilize test_frontend_contract

```bash
gh issue create \
  --title "G-01: Stabilize test_frontend_contract — CI vs local discrepancy" \
  --body '## Problem
CI показывает failure на Unit tests (Python 3.11/3.12), локально 4/4 green. Последний run: `26e34914`.

## Steps
1. `gh run view <latest-failed> --log --job="Unit tests (Python 3.12)"` — точный traceback
2. Проверить `conftest.py` — разное поведение pytest plugins
3. Зафиксировать seed: `random.seed(42)`, `np.random.seed(42)`
4. Изолировать от внешних API (mock или skip в CI)
5. PR → 3 последовательных CI run без failure

## Acceptance
- 3 CI run подряд: все 8 jobs green
- Нет flaky failures в течение недели' \
  --label "phase:stabilization,moscow:must,p0,area:ci" \
  --milestone "Sprint G-1"
```

---

## G-02: Alertmanager production credentials

```bash
gh issue create \
  --title "G-02: Alertmanager — заполнить production credentials" \
  --body '## Problem
Alertmanager настроен с placeholder-значениями: `slack_webhook: "https://hooks.slack.com/PLACEHOLDER"`.
Без реальных credentials алерты никуда не доходят.

## Steps
1. Создать Slack webhook в `#alerts-astrofin`
2. Запросить PagerDuty routing key (или временно email-only)
3. `gh secret set ALERTMANAGER_SLACK_WEBHOOK`
4. `gh secret set ALERTMANAGER_PD_ROUTING_KEY` (если есть)
5. Обновить `alertmanager.yml`
6. Триггернуть тестовый alert: `curl -X POST http://localhost:9093/api/v1/alerts ...`

## Acceptance
- Тестовый alert пришёл в Slack
- PagerDuty/email routing работает (или документировано known-issue)' \
  --label "phase:stabilization,moscow:must,p0,area:ops" \
  --milestone "Sprint G-1"
```

---

## G-03: docker-compose staging smoke test

```bash
gh issue create \
  --title "G-03: docker-compose staging — full stack smoke test" \
  --body '## Problem
Полный стек (postgres + redis + app + dash + telegram bot) не тестировался в staging после всех Sprint A-F изменений.

## Steps
1. `docker-compose -f docker-compose.yml up -d`
2. Check PostgreSQL: `pg_isready`
3. Check Redis: `redis-cli ping`
4. Check hypertable: `psql -c "\dt"`
5. Check health: `curl http://localhost:8050/health`
6. Check dashboard: `curl http://localhost:8050/`
7. Check FastAPI: `curl http://localhost:8000/health`
8. Run sentinel: `python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING`
9. Check WAL-G sidecar logs
10. Verify Loki log ingestion

## Acceptance
- Все 10 checks green
- Sentinel отработал, сигнал в БД
- Dashboard доступен, показывает панели' \
  --label "phase:stabilization,moscow:must,p0,area:infra" \
  --milestone "Sprint G-1"
```

---

## G-04: Backtest pipeline — первый отчёт

```bash
gh issue create \
  --title "G-04: Backtest pipeline — запустить на 90 днях, сгенерировать отчёт" \
  --body '## Steps
1. `python -m backtest.metrics_agent --days 90 --symbols BTCUSDT,ETHUSDT`
2. Проверить метрики: Sharpe ratio, max drawdown, win rate, profit factor
3. `python -m backtest.metrics_agent --report-html --output docs/performance/`
4. Сохранить Markdown отчёт: `docs/performance/backtest-report-2026-07.md`
5. Проверить KPI Control Loop логи — нет ли OAP drift > 0.5

## Acceptance
- Отчёт в `docs/performance/backtest-report-2026-07.md`
- Метрики в разумных пределах (Sharpe >= -1, win rate 30-70%)
- KPI Control Loop не показывает деградации' \
  --label "phase:stabilization,moscow:should,p1,area:ml" \
  --milestone "Sprint G-1"
```

---

## G-05: CI — unit test failures (Python 3.11/3.12)

```bash
gh issue create \
  --title "G-05: CI — починить unit test failures на Python 3.11 и 3.12" \
  --body '## Problem
Последние CI run (sha `26e34914`): `Unit tests (Python 3.12): failure`, `Unit tests (Python 3.11): failure`.
Остальные 6 jobs green.

## Steps
1. `gh run view <id> --log --job="Unit tests (Python 3.12)"` — точный traceback
2. Категоризировать:
   - ImportError → проверить `pyproject.toml`/`uv.lock` на 3.11/3.12 совместимость
   - AssertionError → сравнить с локальным run, найти diff
   - Timeout → увеличить timeout или retry
3. Fix → push → `gh run watch`
4. Повторить для 3.11

## Acceptance
- 3 последовательных CI run: все 8 jobs green
- 0 failures на обоих Python' \
  --label "phase:stabilization,moscow:must,p0,area:ci" \
  --milestone "Sprint G-1"
```

---

## G-06: WAL-G restore drill

```bash
gh issue create \
  --title "G-06: WAL-G — restore drill (backup → destroy → restore → verify)" \
  --body '## Steps
1. `wal-g backup-push $PGDATA`
2. `docker-compose stop postgres`
3. `rm -rf $PGDATA`
4. `wal-g backup-fetch $PGDATA LATEST`
5. `docker-compose start postgres`
6. `pg_isready && psql -c "SELECT count(*) FROM agent_responses"`
7. Документировать: `docs/runbooks/DR_WALG_RESTORE.md`

## Acceptance
- Восстановленная БД содержит все данные
- `pg_isready` → accepting connections
- Count agent_responses совпадает с pre-backup
- Runbook создан' \
  --label "phase:stabilization,moscow:must,p0,area:infra" \
  --milestone "Sprint G-1"
```

---

## G-07: On-call ротация

```bash
gh issue create \
  --title "G-07: On-call — назначить ротацию, обновить RUNBOOK" \
  --body '## Steps
1. Назначить primary/secondary в `docs/RUNBOOK.md`
2. Escalation: Slack (канал), Telegram (@Felix), email (mahaasur13@gmail.com)
3. Проверить Alertmanager routing: critical → Slack + email
4. Создать `docs/runbooks/ONCALL_HANDOVER.md` — шаблон

## Acceptance
- `docs/RUNBOOK.md` содержит актуальные контакты
- Тестовый critical alert доставлен (Slack или email)
- Handover template готов' \
  --label "phase:stabilization,moscow:should,p1,area:ops" \
  --milestone "Sprint G-1"
```

---

## Batch Create All Issues

```bash
# Копировать все 7 блоков выше как один скрипт, либо по одному:
gh issue create --title "G-01: Stabilize test_frontend_contract" \
  --body "$(cat <<'EOF'
... (body from above)
EOF
)" \
  --label "phase:stabilization,moscow:must,p0,area:ci" \
  --milestone "Sprint G-1"
```

> 📎 Связано: `SPRINT_1.md` · `DEVELOPMENT_PLAN_v1.1.0.md` · `GITHUB_PROJECT_SETUP.md`

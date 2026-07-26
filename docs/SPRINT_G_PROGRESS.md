# Sprint G — Неделя 1: Stabilization & GA Prep

**Даты:** 28.07 – 01.08.2026 | **Ветка:** master @ `19508f35`
**CI:** [![CI](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/ci.yml)

---

## Итог: 2026-07-26

| Задача | Статус | Комментарий |
|--------|--------|-------------|
| **G-01+G-05: Стабилизация CI** | ✅ **8/8 green** | 3.11 + 3.12 стабильны. Фикс: `unittest.mock.patch("core.settings.get_settings")` в тесте. Lint fix (F541). ROMA SystemExit fix. |
| **G-02: Alertmanager creds** | ⚠️ Требует ручных действий | GitHub Secrets созданы: `ALERTMANAGER_SLACK_WEBHOOK_URL`, `ALERTMANAGER_SMTP_PASSWORD` и др. Осталось: заполнить реальные значения. |
| **G-03: Staging smoke test** | ⚠️ Docker недоступен в sandbox | Docker daemon не запущен. Тест перенесён на staging-окружение. Smoke test plan: `docs/staging-smoke-test-plan.md`. |
| **G-04: Backtest report** | ✅ Выполнен | `backtest/reports/backtest-2026-07-26.json` (617 trades, 90 days). Win Rate 42.0%, Sharpe 0.01. Детали: `docs/backtest/BACKTEST_REPORT.md`. |
| **G-06: WAL-G drill** | ⚠️ Docker недоступен | Runbook готов: `docs/runbooks/WALG_RESTORE_DRILL.md`. Drill выполняется на staging. |
| **G-07: On-call rotation** | ✅ Документирован | `docs/on-call.md` — primary: Felix, escalation: Slack → PagerDuty. |

---

## CI Pipeline (v1.0.0-beta → GA)

| Job | Статус |
|-----|--------|
| Architecture linter | ✅ pass |
| Lint (ruff + bandit + radon) | ✅ pass |
| Unit tests (Python 3.11) | ✅ pass |
| Unit tests (Python 3.12) | ✅ pass |
| Sub-package tests (bridge/roma) | ✅ pass |
| Sub-package tests (kernel/atom-federation) | ✅ pass |
| Validate data room | ✅ pass |
| **Status aggregator** | ✅ **ALL GREEN** |

Security workflow (Bandit blocking): ⚠️ non-blocking — B324, B104, B310 findings уже в `.bandit` skip-листе, CI `|| true`.

---

## Коммиты Sprint G

1. `d2b1fe54` — fix(ci): env vars BEFORE imports — resolve CI 403/401 in test_frontend_contract
2. `1c8d9d9f` — fix(ci): datetime.utcnow() → datetime.now(UTC) + ROMA test_ci SystemExit fix
3. `8950b170` — fix(lint): remove f-string without placeholders F541
4. `19508f35` — fix(ci): mock get_settings() in test_frontend_contract — robust auth disable

---

## Path to GA (оставшиеся шаги)

| Шаг | Статус | Приоритет |
|-----|--------|-----------|
| CI стабилен (5 green runs) | ✅ 1/5 (run #30194879001) | P0 |
| Alertmanager credentials | ⚠️ заполнить production creds | P0 |
| Docker compose staging test | ⚠️ проверить полный стек на staging | P0 |
| Backtest report review | ⚠️ первый отчёт после пилота | P1 |
| WAL-G restore drill | ⚠️ подтвердить disaster recovery | P0 |
| On-call ротация | ⚠️ назначить + протестировать | P1 |
| Bandit Medium findings → 0 | ⚠️ B324, B104, B310 (v1.1.0) | P2 |

---

## Следующий шаг

Продолжить итерацию `test_frontend_contract` для следующих 4 green runs на CI.
Назначить backup on-call и протестировать Slack+PagerDuty escalation.

# On-Call Rotation — AstroFin Sentinel v1.0.0-beta

**Версия:** 1.0 | **Дата:** 2026-07-26 | **Владелец:** Felix (mahaasur13-sys)

---

## Контакты

| Роль | Имя | Контакт | Часы |
|------|-----|---------|------|
| **Primary** | Felix | Telegram: @asurdev, Email: mahaasur13@gmail.com | 24/7 |
| **Backup** | [назначить] | Slack / PagerDuty | Business hours |
| **Escalation** | [назначить] | PagerDuty | 24/7 |

---

## Эскалация

```
Alert → Primary (Felix) → Slack DM
  ├─ 15 мин без ответа → Backup (Slack + PagerDuty)
  └─ 30 мин без ответа → PagerDuty incident (severity=critical)
```

---

## Alertmanager Routing

| Severity | Канал | Repeat Interval | Group Wait |
|----------|-------|-----------------|------------|
| **critical** | Slack #alerts-critical + PagerDuty | 4h | 30s |
| **warning** | Slack #alerts-warning | 12h | 1m |
| **slo** | Email (weekly digest) | — | — |
| **info** | Slack #alerts-info | 24h | 2m |

---

## Runbooks

| Alert | Runbook |
|-------|---------|
| `ALERT_DiskSpaceWALG` | `docs/runbooks/ALERT_DiskSpaceWALG.md` |
| `ALERT_MetaRLNightlyFail` | `docs/runbooks/ALERT_MetaRLNightlyFail.md` |
| `ALERT_DashboardLatencyHigh` | `docs/runbooks/ALERT_DashboardLatencyHigh.md` |
| `WALG Restore Drill` | `docs/runbooks/WALG_RESTORE_DRILL.md` |
| `Incident Response` | `docs/incident-response.md` |

---

## Процедура инцидента

1. **Обнаружение:** Alertmanager отправляет alert в Slack/PagerDuty
2. **Triage (15 мин):** On-call engineer подтверждает инцидент
3. **Investigation (30 мин):** Поиск root cause, применение runbook
4. **Resolution:** Fix, verify, close alert
5. **Post-mortem:** Запись в `docs/postmortems/` в течение 24 часов

---

## Смены

- Текущий график: 24/7 (Felix — single point of failure)
- Планируемый: 2 человека, 12-часовые смены (08:00–20:00 / 20:00–08:00 Europe/Samara)
- PagerDuty integration: [настроить]

---

## Тестовая тревога

```bash
# Отправить тестовый alert
amtool alert add alertname=TestOnCall severity=critical \
  --annotation=summary="On-call rotation test" \
  --annotation=description="Sprint G G-07 smoke test"

# Проверить получение в Slack
# Проверить escalation на backup (если нет ответа)
```

# SLO / SLI — AstroFin Sentinel Platform

> **Версия:** 1.0  •  **Дата:** 2026-06-26  •  **Владелец:** SRE-team
> **Связанные документы:** [RUNBOOK.md](./RUNBOOK.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [chaos-engineering.md](./chaos-engineering.md)

## Что такое SLO и зачем

**SLO (Service Level Objective)** — это внутренняя цель по качеству сервиса,
выраженная в измеримых величинах. SLO нужен, чтобы:

1. Объективно измерить, насколько платформа «здорова» в долгосрочной перспективе.
2. Связать инженерные решения с пользовательской ценностью.
3. Избежать «alert fatigue» — алерты привязаны к burn rate бюджета, а не к сырым метрикам.

## Архитектура SLO

```
┌────────────────────────────────────────────────────────────────────┐
│ User-facing Service (web-dashboard, ml-inference)                  │
│                                                                    │
│  ┌────────────────┐         ┌──────────────────────────────────┐  │
│  │ SLI: доступность│ ──────► │ SLO: 99.9% за rolling 30 дней    │  │
│  │  (2xx+3xx)/all │         │ Error budget: 43.2 мин downtime   │  │
│  └────────────────┘         └──────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────┐         ┌──────────────────────────────────┐  │
│  │ SLI: latency    │ ──────► │ SLO: p95 < 200 ms за 5 мин окно   │  │
│  │  p95 по /health │         │ Success rate: ≥ 99.9% запросов    │  │
│  └────────────────┘         └──────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## Определения SLI/SLO

### SLO-1: Availability (доступность)

| Поле | Значение |
|---|---|
| **SLI** | `(rate(http_requests_total{code!~"5.."}[30d])) / (rate(http_requests_total[30d]))` для `service="web-dashboard"` |
| **SLO** | ≥ 99.9% за rolling 30 дней |
| **Error budget** | 30 дней × 24 ч × 60 мин × 0.001 = **43.2 минуты** downtime в месяц |
| **Window** | Rolling 30 дней |
| **Measurement** | Prometheus recording rule → alertmanager SLO burn |
| **Burn-rate алерты** | 14.4x за 1 ч (съедает budget за 2 дня), 6x за 6 ч (за 5 дней) |

**Исключения** (НЕ считаются за failure):
- Запланированные maintenance-окна (помечаются в Grafana annotations).
- Отказы, вызванные upstream-провайдерами (внешние API биржевых данных).

### SLO-2: Latency (задержка healthcheck)

| Поле | Значение |
|---|---|
| **SLI** | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{le="0.2"}[5m]))` |
| **SLO** | ≥ 99.9% запросов `GET /healthz` возвращаются за **< 200 ms** (5-мин окно) |
| **Window** | 5 минут (sliding) |
| **Measurement** | Prometheus histogram → `SLOLatencyBudgetBurn` alert |

### SLO-3: Healthcheck uptime

| Поле | Значение |
|---|---|
| **SLI** | `probe_success{job="blackbox-web"}` |
| **SLO** | ≥ 99.95% за rolling 30 дней |
| **Window** | Rolling 30 дней |
| **Measurement** | Blackbox exporter → `HealthcheckFailing` alert |

## Error Budget Policy

### Когда бюджет НЕ израсходован (>50% остаётся)
- Новые эксперименты и фичи — без ограничений.
- Chaos-эксперименты — по обычному расписанию.

### Когда бюджет израсходован на 50–90%
- Code freeze для non-critical фич.
- Усиленный code review для performance-изменений.
- Weekly review SLO с командой.

### Когда бюджет израсходован на 100% (full burn)
- **Hard freeze** всех деплоев кроме security-фиксов.
- Обязательный post-mortem даже если инцидент «мелкий».
- SRE-team имеет право откатить любую фичу.

## Burn-Rate алерты

Prometheus alerts в `deploy/monitoring/prometheus-alerts.yml` секция `astrofin_slo`:

| Alert | Burn rate | Время съедания бюджета | Severity |
|---|---|---|---|
| `SLOAvailabilityBurn` fast | 14.4x | 2 дня | critical |
| `SLOAvailabilityBurn` slow | 6x | 5 дней | warning |
| `SLOLatencyBudgetBurn` | continuous <99.9% за 5 мин | n/a | critical |

## Измерение compliance

Раз в неделю SRE публикует отчёт:
- Текущий остаток error budget.
- Топ-3 причины consumption.
- Действия на следующую неделю.

Шаблон отчёта: `docs/slo-reports/YYYY-WW.md`.

## История изменений

| Дата | Версия | Изменение |
|---|---|---|
| 2026-06-26 | 1.0 | Initial SLO definition |
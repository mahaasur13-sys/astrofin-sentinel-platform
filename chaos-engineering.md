# Chaos Engineering — план внедрения

> **Статус:** план готов, реализация отложена до появления production-кластера.
> **Ответственный:** @SRE-team
> **Последнее обновление:** 2026-06-26

## Цель

Регулярно проверять resilience AstroFin Sentinel Platform путём введения
контролируемых отказов в production-окружении (в выделенные maintenance-окна)
и в staging-ежедневно.

## Принципы

1. **Blast radius минимален** — эксперимент затрагивает ≤ 1/3 pod'ов.
2. **Abort-критерий заранее определён** — если SLO budget исчерпан на 50% за время эксперимента — остановка.
3. **Game days** — каждое воскресенье 14:00 UTC запускается scripted game day.
4. **Observability first** — никаких экспериментов без подключённого Prometheus/Grafana.

## Выбор платформы

| Платформа   | Плюсы                                                    | Минусы                                  | Решение |
|-------------|----------------------------------------------------------|-----------------------------------------|---------|
| **Chaos Mesh** | k8s-native, CRD-based, удобный UI, широкий набор экспериментов | Требует установки control plane          | **primary** |
| LitmusChaos | Большой experiment hub, community                       | Тяжелее в эксплуатации                  | fallback |
| Gremlin     | SaaS, мощный scheduler                                   | Платный, vendor lock                    | не используем |

**Решение:** [Chaos Mesh](https://chaos-mesh.org/) — установить в namespace `chaos-testing`,
эксперименты запускать через `kubectl apply` или GitHub Actions workflow
(см. ниже шаблон).

## Каталог экспериментов

### E-001. PodChaos — kill random web pod

| Поле | Значение |
|---|---|
| Severity | low |
| Target | `deployment/astrofin-sentinel-web` |
| Action | kill 1 из 2 pod'ов, длительность 5 мин |
| Abort-критерий | latency p95 > 500 ms или error rate > 1% |
| Ожидаемый эффект | rolling restart второго replica, восстановление ≤ 60 сек |
| Проверка | `kubectl get pods -l app.kubernetes.io/name=astrofin-sentinel-web` |

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: web-pod-kill
  namespace: chaos-testing
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - astrofin-sentinel
    labelSelectors:
      app.kubernetes.io/name: astrofin-sentinel-web
  duration: "5m"
  scheduler:
    cron: "@every 2m"
```

### E-002. NetworkChaos — потеря сети между web и БД

| Поле | Значение |
|---|---|
| Severity | medium |
| Target | egress web → postgres:5432 |
| Action | 30% packet loss на 10 мин |
| Abort-критерий | error rate > 5% или healthcheck недоступен |
| Ожидаемый эффект | увеличение p95 latency, circuit-breaker срабатывает, recovery ≤ 30 сек |

### E-003. StressChaos — нагрузка CPU на ML engine

| Поле | Значение |
|---|---|
| Severity | high (game day only) |
| Target | `ml-engine` pod |
| Action | 80% CPU workers на 15 мин |
| Abort-критерий | SLO budget burn rate > 5x за 5 мин |
| Ожидаемый эффект | увеличение queue depth, но graceful degradation без падений |

### E-004. IOChaos — задержка дисковых операций Postgres

| Поле | Значение |
|---|---|
| Severity | medium |
| Target | postgres pod |
| Action | 50ms latency на I/O в течение 10 мин |
| Ожидаемый эффект | увеличение write latency, проверка таймаутов на стороне приложения |

### E-005. TimeChaos — рассинхронизация времени на agent pod'ах

| Поле | Значение |
|---|---|
| Severity | low |
| Target | agents namespace |
| Action | смещение времени на 5 сек вперёд на 10 мин |
| Ожидаемый эффект | проверка работы системы при clock skew (особенно для JWT exp) |

## Steady-State Hypothesis (для каждого эксперимента)

Перед запуском каждого эксперимента формулируется гипотеза:

```
HYPOTHESIS: "Если мы убьём один из двух web-pod'ов,
             latency p95 останется < 200 ms благодаря rolling restart,
             а error rate не превысит 0.1%."

NULL:        latency p95 > 200 ms ИЛИ error rate > 0.1% в течение 60 сек после убийства.
```

Если NULL подтверждается — эксперимент считается проваленным, открывается
incident-review.

## Метрики успешности платформы chaos-тестирования

| Метрика | Целевое значение (через 3 мес.) |
|---|---|
| Количество запущенных экспериментов в месяц | ≥ 8 |
| Доля успешных экспериментов (null не подтвердилась) | ≥ 90% |
| MTTD (mean time to detect) для production-инцидентов | ≤ 5 мин |
| Среднее время восстановления после chaos | ≤ 60 сек |
| Количество найденных реальных багов через chaos | ≥ 2 в квартал |

## Rollout-план

1. **Phase 1 (Q3 2026) — подготовка**
   - Развернуть Chaos Mesh control plane в кластере `chaos-testing` namespace
   - Настроить RBAC, выдать права CI/CD
   - Добавить отдельный GitHub workflow `chaos-experiment.yml` с manual trigger
   - Прогнать E-001 в staging 5 раз подряд — отладить pipeline

2. **Phase 2 (Q4 2026) — staging-on-fire**
   - Запускать все 5 экспериментов еженедельно в staging
   - Начать собирать метрики успешности
   - Провести 2 game day с командой разработки

3. **Phase 3 (Q1 2027) — production в maintenance-окнах**
   - Первые эксперименты в production — только E-001 (pod-kill) и E-005 (time-skew)
   - Review board: каждое воскресенье 14:00 UTC, окно 30 мин
   - Только после 3 месяцев стабильных staging-экспериментов

## Шаблон GitHub Actions workflow

```yaml
# .github/workflows/chaos-experiment.yml  (будет создан в Phase 1)
name: Chaos experiment
on:
  workflow_dispatch:
    inputs:
      experiment:
        type: choice
        options: [pod-kill, network-loss, cpu-stress]
      namespace:
        default: 'astrofin-sentinel-staging'
jobs:
  run:
    runs-on: ubuntu-latest
    environment: chaos-staging
    steps:
      - uses: actions/checkout@v4
      - run: |
          kubectl apply -f chaos/${EXPERIMENT}.yaml
      - run: |
          sleep 600  # 10 min observation
          kubectl delete -f chaos/${EXPERIMENT}.yaml
```

## Связанные документы

- [SLO/SLI](./slo.md)
- [RUNBOOK](./RUNBOOK.md)
- [deploy/monitoring/prometheus.yml](../deploy/monitoring/prometheus.yml)
- ADR-0004: Hybrid Memory Policy (для time-skew experiments)

## История ревью плана

| Дата | Решение | Участники |
|---|---|---|
| 2026-06-26 | Initial draft | @SRE-team |
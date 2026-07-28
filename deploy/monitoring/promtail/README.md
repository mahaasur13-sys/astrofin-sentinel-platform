# Promtail → Loki — Log Shipping (AstroFin Sentinel V5)

## Назначение

Сбор и отправка структурированных логов платформы AstroFin Sentinel в Loki для
централизованного мониторинга и алертинга через Grafana.

## Архитектура

```
┌──────────────────────────────────────────────────┐
│                 Zo Sandbox                        │
│  /dev/shm/*.log (tmpfs) ──┐                      │
│  /var/log/syslog ─────────┤                      │
│  /var/log/nginx/access.log┤                      │
│  /var/lib/docker/containers┼──► Promtail ──► Loki │
│                            │    (port 9080)       │
└────────────────────────────┼──────────────────────┘
                             │
                             ▼
                   ┌───────────────────┐
                   │ Grafana Dashboard  │
                   │ (Explore → LogQL)  │
                   └───────────────────┘
```

## Быстрый запуск

```bash
# Из корня проекта
docker compose -f deploy/docker-compose.monitoring.yml up -d promtail

# Проверка статуса
docker compose -f deploy/docker-compose.monitoring.yml logs promtail
docker compose -f deploy/docker-compose.monitoring.yml ps promtail
```

## Настройка Grafana Cloud (опционально)

Для отправки логов в Grafana Cloud задайте переменные окружения:

```bash
export LOKI_URL="https://logs-prod-<n>.grafana.net/loki/api/v1/push"
export LOKI_USER="<your-instance-id>"
export LOKI_TOKEN="<your-grafana-cloud-api-token>"
```

При локальном использовании (Loki в том же compose) переменные не нужны —
Promtail использует `http://loki:3100` по умолчанию.

## Labels (Query Hints)

| Label | Пример | Назначение |
|-------|--------|-----------|
| `app` | `astrofin` | Приложение (всегда astrofin) |
| `env` | `production` / `staging` | Окружение |
| `component` | `platform` / `system` / `docker` / `nginx` | Компонент системы |
| `job` | `astrofin-platform` / `astrofin-system` | Job-специфичный |
| `host` | `zo-sandbox` | Хост (автоматически из `$HOSTNAME`) |
| `level` | `INFO` / `WARNING` / `ERROR` | Уровень лога |
| `agent` | `SynthesisAgent` / `FundamentalAgent` | Агент (из structlog) |

### Примеры запросов в Grafana (LogQL)

```logql
# Все ошибки за последний час
{app="astrofin", level="ERROR"}

# Логи конкретного агента
{app="astrofin", agent="SynthesisAgent"}

# Поиск по тексту
{app="astrofin"} |= "timeout"

# Ошибки по окружениям
sum by (env) (count_over_time({app="astrofin", level="ERROR"}[1h]))
```

## Структура логов (structlog JSON)

Promtail ожидает JSON-логи от `structlog`:

```json
{
  "timestamp": "2026-07-27T12:00:00.000Z",
  "level": "info",
  "logger": "orchestration.sentinel_v5",
  "event": "Synthesis complete",
  "agent": "SynthesisAgent",
  "session_id": "a1b2c3d4",
  "confidence": 0.85,
  "signal": "BUY"
}
```

Поля `timestamp`, `level`, `event` — обязательные. Остальные — опциональны.

## Обновление конфигурации

1. Отредактируйте `deploy/monitoring/promtail/promtail-config.yml`.
2. Перезапустите Promtail:

```bash
docker compose -f deploy/docker-compose.monitoring.yml restart promtail
```

3. Проверьте логи на наличие ошибок:

```bash
docker compose -f deploy/docker-compose.monitoring.yml logs --tail=50 promtail
```

## Устойчивость

- **Restart policy:** `unless-stopped` — Promtail перезапустится после сбоя
- **Positions:** `/tmp/promtail/positions.yaml` (persistent volume) — отслеживает прогресс чтения
- **Rate limiting:** `readline_rate: 10000` — предотвращает перегрузку файловой системы
- **Healthcheck:** `http://localhost:9080/ready` — мониторинг состояния

## Устранение неполадок

### Promtail не видит логи

```bash
# Проверьте, что логи пишутся
ls -la /dev/shm/*.log

# Проверьте права на чтение (пользователь promtail = uid 1000)
docker compose -f deploy/docker-compose.monitoring.yml exec promtail ls -la /dev/shm/
```

### Ошибка подключения к Loki

```bash
# Проверьте доступность Loki
curl http://localhost:3100/ready

# Проверьте URL в конфигурации
docker compose -f deploy/docker-compose.monitoring.yml exec promtail cat /etc/promtail/config.yml
```

### Логи дублируются после перезапуска

```bash
# Очистите файл позиций
docker compose -f deploy/docker-compose.monitoring.yml down promtail
docker volume rm astrofin-sentinel-platform_promtail-positions
docker compose -f deploy/docker-compose.monitoring.yml up -d promtail
```

## Freeze Compliance

- ✅ Конфигурационные файлы только в `deploy/monitoring/`
- ✅ Никаких изменений в production-коде
- ✅ Никаких изменений в зависимостях (pyproject.toml, requirements.txt)
- ✅ Credentials только через environment variables
- ✅ Infra-only PR в `release/v1.0.0`

---

**Автор:** Zo (asurdev) — 2026-07-27
**Версия:** v1.0.0

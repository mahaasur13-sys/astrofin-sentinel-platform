# Grafana Cloud Alert Rules — AstroFin Sentinel V5

**Создано:** 2026-08-03
**Datasource:** `grafanacloud-mahaasur13-prom` (Grafana Cloud hosted Prometheus)
**Contact point:** `email-alerts` → mahaasur13@gmail.com

> ⚠️ При импорте эти алерты **сразу перейдут в Firing** (метрики отсутствуют).
> Это ОСОЗНАННЫЙ watchdog — как только экспортёр запустится, алерты автоматически погаснут.

---

## Способ создания (через Grafana Alerting UI)

### Шаг 1: Contact point

1. Alerting → Contact points → New contact point
2. **Name:** `email-alerts`
3. **Integration:** Email
4. **Addresses:** `mahaasur13@gmail.com`
5. **Disable resolved message:** выключить (получать уведомления о recovery)
6. Save

### Шаг 2: Notification policy

1. Alerting → Notification policies → Edit (три точки справа от Default)
2. **Default contact point:** `email-alerts`
3. **Group by:** `severity`, `component`
4. **Group wait:** `30s`
5. **Group interval:** `5m`
6. **Repeat interval:** `30m`
7. Save

### Шаг 3: Alert rules → New folder `AstroFin`

Alerting → Alert rules → New folder → **AstroFin**

Затем создать правила ниже (New alert rule):

---

## ── CRITICAL GROUP (evaluation: 1m) ──

### 1. AstroFinExporterAbsent — Экспортёр метрик не скрейпится

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
up{job="astrofin-metrics-exporter"}
```

**Settings:**
- **Rule name:** AstroFinExporterAbsent
- **Folder:** AstroFin
- **Evaluation group:** astrofin-critical
- **Pending period:** 2m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = critical
team = astrofin
component = infrastructure
```

**Annotations:**
```
summary = AstroFin metrics exporter is not scraped
description = Prometheus cannot scrape the AstroFin metrics exporter on port 9191. The exporter process may be down.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 2. AstroFinMetricsServerDown — Внутренний metrics server упал

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
astrofin_up{component="metrics_server"}
```

**Settings:**
- **Rule name:** AstroFinMetricsServerDown
- **Folder:** AstroFin
- **Evaluation group:** astrofin-critical
- **Pending period:** 2m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = critical
team = astrofin
component = metrics_server
```

**Annotations:**
```
summary = AstroFin internal metrics server is down
description = The astrofin_up{component="metrics_server"} metric is 0 or missing. The tools/metrics_server.py process is not emitting metrics.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 3. AgentMetricsAbsent — Метрики агентов пропали

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
count(astrofin_agent_duration_seconds_count)
```

**Settings:**
- **Rule name:** AgentMetricsAbsent
- **Folder:** AstroFin
- **Evaluation group:** astrofin-critical
- **Pending period:** 3m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = critical
team = astrofin
component = agents
```

**Annotations:**
```
summary = Agent metrics are absent
description = No astrofin_agent_duration_seconds_count metric found. All agents or the orchestration layer may be down. Graceful degradation may be in effect.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md#agent-metrics-absent
```

---

### 4. DataRoomMetricsAbsent — Data Room упал

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
count(astrofin_cache_hits)
```

**Settings:**
- **Rule name:** DataRoomMetricsAbsent
- **Folder:** AstroFin
- **Evaluation group:** astrofin-critical
- **Pending period:** 3m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = critical
team = astrofin
component = data_room
```

**Annotations:**
```
summary = Data Room metrics are absent
description = No astrofin_cache_hits metric found. The Data Room or metrics_server process may be down.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 5. MetaRLMetricsAbsent — Meta-RL компонент упал

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
count(astrofin_evolution_runs)
```

**Settings:**
- **Rule name:** MetaRLMetricsAbsent
- **Folder:** AstroFin
- **Evaluation group:** astrofin-critical
- **Pending period:** 5m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = critical
team = astrofin
component = meta_rl
```

**Annotations:**
```
summary = Meta-RL metrics are absent
description = No astrofin_evolution_runs metric found. The Meta-RL component may have crashed or is not running.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 6. AgentsStalled — Агенты живы, но не работают

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
rate(astrofin_agent_duration_seconds_count[5m])
```

**Settings:**
- **Rule name:** AgentsStalled
- **Folder:** AstroFin
- **Evaluation group:** astrofin-critical
- **Pending period:** 5m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = warning
team = astrofin
component = agents
```

**Annotations:**
```
summary = Agents have stopped producing work
description = The rate of astrofin_agent_duration_seconds_count is 0 over the last 5 minutes. Agents may be alive but blocked.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

## ── WARNING GROUP (evaluation: 5m) ──

### 7. HighRAGErrorRate — Высокий процент ошибок RAG

**Condition:**
```
A: Classic condition
  WHEN avg()    OF query(A, 5m, now)    IS ABOVE 0.1
```

**Query A:**
```promql
rate(astrofin_rag_errors_total[5m]) / rate(astrofin_rag_queries_total[5m])
```

**Settings:**
- **Rule name:** HighRAGErrorRate
- **Folder:** AstroFin
- **Evaluation group:** astrofin-warning
- **Pending period:** 3m
- **No Data:** OK (отсутствие данных = нет ошибок)
- **Error:** Alerting

**Labels:**
```
severity = warning
team = astrofin
component = rag
```

**Annotations:**
```
summary = RAG error rate exceeds 10%
description = {{ $values.A.Value | humanizePercentage }} of RAG queries are failing.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 8. LowCacheHitRate — Низкий cache hit rate

**Condition:**
```
A: Classic condition
  WHEN avg()    OF query(A, 5m, now)     IS BELOW 0.5
```

**Query A:**
```promql
rate(astrofin_cache_hits[5m]) / (rate(astrofin_cache_hits[5m]) + rate(astrofin_cache_misses[5m]))
```

**Settings:**
- **Rule name:** LowCacheHitRate
- **Folder:** AstroFin
- **Evaluation group:** astrofin-warning
- **Pending period:** 5m
- **No Data:** NoData
- **Error:** Alerting

**Labels:**
```
severity = warning
team = astrofin
component = data_room
```

**Annotations:**
```
summary = Cache hit rate below 50%
description = Current hit rate: {{ $values.A.Value | humanizePercentage }}. Data Room cache may be cold or evicting entries.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 9. HighBrokerErrorRate — Ошибки брокера

**Condition:**
```
A: Classic condition
  WHEN avg()    OF query(A, 5m, now)    IS ABOVE 5
```

**Query A:**
```promql
rate(astrofin_broker_errors_total[5m])
```

**Settings:**
- **Rule name:** HighBrokerErrorRate
- **Folder:** AstroFin
- **Evaluation group:** astrofin-warning
- **Pending period:** 3m
- **No Data:** OK
- **Error:** Alerting

**Labels:**
```
severity = warning
team = astrofin
component = trading
```

**Annotations:**
```
summary = Broker errors detected
description = Broker error rate: {{ $values.A.Value }} errors/second. Check trading execution logs.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

### 10. OllamaStatusDegraded — Локальный LLM недоступен

**Condition:**
```
A: Classic condition
  WHEN last()    OF query(A, 5m, now)    IS BELOW 1
```

**Query A:**
```promql
astrofin_ollama_status
```

**Settings:**
- **Rule name:** OllamaStatusDegraded
- **Folder:** AstroFin
- **Evaluation group:** astrofin-warning
- **Pending period:** 3m
- **No Data:** Alerting
- **Error:** Alerting

**Labels:**
```
severity = warning
team = astrofin
component = llm
```

**Annotations:**
```
summary = Ollama LLM service is degraded
description = astrofin_ollama_status = {{ $values.A.Value }}. The LLM router will fallback to OpenRouter.
runbook_url = https://github.com/mahaasur13-sys/astrofin-sentinel-platform/blob/master/RUNBOOK.md
```

---

## Evaluation groups summary

| Group | Interval | Alerts |
|-------|----------|--------|
| `astrofin-critical` | 1m | AstroFinExporterAbsent, MetricsServerDown, AgentMetricsAbsent, DataRoomMetricsAbsent, MetaRLMetricsAbsent, AgentsStalled |
| `astrofin-warning` | 5m | HighRAGErrorRate, LowCacheHitRate, HighBrokerErrorRate, OllamaStatusDegraded |

**Total: 10 alert rules в 2 evaluation groups**

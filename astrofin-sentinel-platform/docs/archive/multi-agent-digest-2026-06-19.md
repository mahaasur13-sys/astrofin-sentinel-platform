# Multi-Agent AI Daily — 2026-06-19

Сводка за последние 7 дней по multi-agent AI: отобраны только релевантные релизы/обсуждения с реальной технической ценностью.

## Источники
- GitHub / X: Synapse AI — open-source DAG-оркестрация для мультиагентных workflows.
- OpenReview: Foundry — host-owned trust and memory for long-horizon agent swarms.
- Databricks Blog / Community: Agent Bricks / Supervisor Agent — governed orchestration на уровне enterprise-платформы.

## Топ-3

### 1) Synapse AI — open-source multi-agent orchestration stack
- **Источник:** X / GitHub
- **Краткое описание:** Новая open-source платформа с DAG-подходом к мультиагентной оркестрации: отдельные шаги для agent / LLM / tool / evaluator / parallel / loop / human / transform. Важно тем, что заменяет “loose chat loops” на детерминированные рабочие графы с resume, checkpoints, human-in-the-loop и поддержкой MCP, REST, webhooks и Python tools.
- **Применение для AstroFinSentinelV5:** Хороший референс для формализации pipeline’ов с жёсткими зависимостями, чекпоинтами и управляемым human review. Можно заимствовать идею разделения ролей и устойчивого replay/resume для критичных финансовых сценариев.

### 2) Foundry: Host-Owned Trust and Memory for Long-Horizon Agent Swarms
- **Источник:** OpenReview
- **Краткое описание:** Предлагает host-owned control plane, где агенты генерируют предложения, а хост отдельно проверяет их через trusted evaluator и накапливает evidence в persistent memory. Это сильный архитектурный ответ на проблему доверия и деградации контекста в долгих multi-agent циклах.
- **Применение для AstroFinSentinelV5:** Полезно как шаблон для разделения “proposal” и “verification” в задачах с высоким риском ошибки. Особенно ценно для финансовых решений, где важно сохранять доказательства, историю проверок и устойчивую память между сессиями.

### 3) Databricks Agent Bricks / Supervisor Agent
- **Источник:** Databricks Blog / Community
- **Краткое описание:** Databricks вывел multi-agent orchestration в production-платформу: Supervisor Agent маршрутизирует запросы к специализированным агентам и инструментам с governance через Unity Catalog. Сильная сторона — enterprise-scale observability, cost attribution, model flexibility и поддержка разных harness’ов.
- **Применение для AstroFinSentinelV5:** Полезно как ориентир для governance-слоя: кто что может запускать, к каким данным имеет доступ, как считать стоимость и как логировать трассы. Может подсказать, как строить централизованный supervisor поверх специализированных агентов и инструментов.

## Итог
Лидеры дня: **Synapse AI** за практичную DAG-оркестрацию, **Foundry** за trust/memory-архитектуру для long-horizon swarms, и **Databricks Agent Bricks** за production-grade governance и supervisor-подход.

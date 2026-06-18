# Multi-Agent AI Daily Digest

**Дата:** 2026-05-04

**Источники:** GitHub, arXiv, X/Twitter, Reddit, форумы

---

## Топ-3 за сегодня

**1. [Orloj — Declarative Multi-Agent Orchestration Platform]**
- **Источник:** GitHub — OrlojHQ/orloj
- **Описание:** Orloj — это open-source платформа для полного жизненного цикла multi-agent систем: декларативное управление через YAML, REST/CLI/SDK API, scheduling, routing, retries, idempotency, approvals, human-in-the-loop gates, аудит и observability (Prometheus, OpenTelemetry). Поддерживает in-memory или Postgres state, NATS JetStream messaging, Kubernetes/Docker/VPS deployment. Активная разработка, v0.12.1 от 2026-05-03.
- **Применение для AstroFinSentinelV5:** Оркестрация сложных финансовых workflow с контролем governance и token budgets. YAML-first подход упростит declarative определение агентов для анализа рисков и алертинга.

**2. [Dapr Agents — Production-Grade Multi-Agent Framework]**
- **Источник:** GitHub — dapr/dapr-agents
- **Описание:** Python-фреймворк для orchestration, построенный на Dapr. Обеспечивает durable workflow execution, автоматические retry, resilience, Kubernetes-native deployment, встроенную observability и state management. Поддерживает secure multi-agent collaboration и vendor-neutral дизайн. Последний релиз v1.0.1 (Apr 2026).
- **Применение для AstroFinSentinelV5:** Dapr-based durability гарантирует завершение критических финансовых задач даже при сбоях. Интеграция с Kubernetes упрощает деплой в production.

**3. [Graph-of-Agents (GoA) — Graph-Based LLM Coordination]**
- **Источник:** arXiv — 2604.17148
- **Описание:** Новый фреймворк координации множества LLM через направленный граф. Использует model cards для выбора релевантных агентов, затем направленное распространение информации от более релевантных агентов к менее, с финальной агрегацией ответов. Превосходит базовые подходы при использовании всего 3 агентов из пула.
- **Применение для AstroFinSentinelV5:** Graph-based координация может заменить иерархические схемы в AstroFinSentinelV5 — агенты анализа рынка, рисков и портфеля смогут обмениваться информацией через направленный граф для более точных решений.

---

*Сохранено: /home/workspace/Knowledge/multi-agent-digest-2026-05-04.md*
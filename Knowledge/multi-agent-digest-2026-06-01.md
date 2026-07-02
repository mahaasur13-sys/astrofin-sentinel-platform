# Multi-Agent AI Daily — 2026-06-01

**Источники:** GitHub, arXiv, X/Twitter, Reddit (r/LocalLLaMA, r/AI_Agents, r/LLMDevs)

---

## Топ-3 за неделю

---

**1. Durable-Agents v0.1.0 — фреймворк для отказоустойчивых мультиагентов на базе Temporal**

- **Источник:** GitHub — piotrwachowski/durable-agents
- **Описание:** Python-фреймворк нового поколения, где каждый шаг агента выполняется как durable Temporal activity/child workflow. Это означает, что состояние агента хранится в event history, а не в памяти — при краше или перезапуске агент продолжает работу точно с места остановки. Поддерживает sub-agent delegation как изолированные child workflows, @skill и @tool декораторы, встроенные файловые инструменты. Релиз v0.1.0 вышел 30 мая 2026.
- **Применение для AstroFinSentinelV5:** Механизм durable execution идеально подходит для финансовых агентов, где сбой на середине транзакции недопустим. Можно использовать Temporal как backend для критических агентов системы, обеспечивая автоматическое продолжение работы при любых инфраструктурных сбоях.

---

**2. Microsoft Agent Framework v1.7.0 — A2A protocol и background agents укрепляют enterprise orchestration**

- **Источник:** GitHub — microsoft/agent-framework, релиз python-1.7.0 (28 мая 2026)
- **Описание:** Релиз добавляет A2AAgentSession с referenced task IDs и input-required support, новый HarnessAgent и background-agents harness provider. Также появилась экспериментальная поддержка Foundry Toolbox MCP invocation. Фреймворк поддерживает Python и .NET, имеет развитую систему хостинга, declarative agents и A2A (Agent-to-Agent) протокол для межагентного взаимодействия.
- **Применение для AstroFinSentinelV5:** A2A protocol из Microsoft — это фактически стандарт интероперабельности агентов. Интеграция с Microsoft-экосистемой (Azure, Teams) актуальна для корпоративных пользователей. Background agents позволяют запускать длительные задачи без блокировки основного потока.

---

**3. Agent Harness Engineering Survey — ETCLOVG: таксономия для production-grade мультиагентных систем**

- **Источник:** arXiv/OpenReview (2026)
- **Описание:** Комплексное исследование, которое вводит 7-слойную таксономию ETCLOVG (Execution environment, Tool interface, Context management, Lifecycle/Orchestration, Observability, Verification, Governance) для инженерии AI agent infrastructure. Охватывает 170+ open-source проектов, анализирует production-опыт OpenAI, Anthropic, LangChain. Подчёркивает, что надёжность мультиагентных систем определяется не моделью, а surrounding harness — инфраструктурным слоем.
- **Применение для AstroFinSentinelV5:** ETCLOVG может служить архитектурным чеклистом при построении AstroFinSentinelV5 — от мониторинга (Observability) до governance политик и verification механизмов. Особенно полезно для масштабирования системы и обеспечения auditability финансовых операций.

---

*Сгенерировано автоматически. Источники проверены на актуальность: все события опубликованы или активно обсуждаются в период 25 мая — 1 июня 2026.*
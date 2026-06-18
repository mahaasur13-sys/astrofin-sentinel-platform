# Multi-Agent AI Daily — 2026-05-29

## Источники
- GitHub: vantyx-ai, council-agentflow, bottega, AIntegriX, AgensFlow, ax-lmoma, evo-nexus, AgentForge, fleet, cli-boot-agents, Multica
- arXiv: AgensFlow (2605.27466), Agent Harness Engineering Survey, Hierarchical Multi-agent LLM Reasoning (MASTER), Organizational Control Layer
- X/Twitter: #multiagent, #AIagents, #agentframework

---

## Топ-3 за сегодня

**1. [AgensFlow — Learnable Coordination Policy для Multi-Agent систем]**
- Источник: arXiv (arXiv:2605.27466, 28 мая 2026)
- Краткое описание: AgensFlow — open-source фреймворк, который treats agent orchestration как задачу онлайн policy-learning под частичной наблюдаемостью. Вместо статических pipeline'ов координация (выбор skill, модели, роли, топологии) становится наблюдаемой и обучаемой из повторяющихся траекторий. Эксперименты показывают, что learned routing превосходит фиксированные pipelines на задачах с интенсивной координацией, а warm-started policy graphs сокращают cost exploration.
- Применение для AstroFinSentinelV5: Интересен подход с learnable routing — можно адаптировать для динамического распределения задач между агентами AstroFinSentinelV5 в зависимости от типа финансовой задачи, автоматически оптимизируя стратегию координации на основе накопленного опыта.

**2. [Multica v0.3.6 — AI Agents как реальные teammates в Jira/GitHub workflow]**
- Источник: GitHub (multica-ai/multica, 22–27 мая 2026, 34k+ stars)
- Краткое описание: Multica — open-source платформа (TypeScript), которая превращает coding agents в полноценных участников команды: assign issues напрямую агентам, track progress в реальном времени, agents report blockers themselves, reuse learned skills. Активно развивается (много PRs по agent-driven promotions, workspace context injection, live activity indicators). Интегрируется с Jira и GitHub как единый dashboard.
- Применение для AstroFinSentinelV5: Концепция "agent teammate" с tracking и blocker reporting — отличная модель для мониторинга агентов в AstroFinSentinelV5. Можно перенять паттерн live activity chip и per-issue agent indicator для визуализации статусов мультиагентных финансовых workflow.

**3. [Agent Harness Engineering Survey — ETCLOVG taxonomy для multi-agent coordination]**
- Источник: arXiv (OpenReview, 170+ open-source проектов)
- Краткое описание: Обзор говорит, что надёжность LLM-агентов в production определяется больше harness (инфраструктурой вокруг модели), чем самой моделью. Предложена семи слойная ETCLOVG taxonomy: Execution environment, Tool interface, Context management, Lifecycle/Orchestration, Observability, Verification, Governance. Показано, что coordination между агентами зависит от качества harness layer, и что variance от harness может превышать variance от model choice.
- Применение для AstroFinSentinelV5: напрямую применимо к архитектуре AstroFinSentinelV5 — понимание того что именно orchestration/harness layer определяет производительность агентов, поможет правильно спроектировать observability и governance слои для финансовых агентов с их严格要求 к reliability и auditability.
# 🤖 Multi-Agent AI Daily — 2026-06-09

Ежедневный дайджест новостей из мира multi-agent AI-инструментов, фреймворков и исследований. Отобрано 3 самых значимых события за последние 7 дней по приоритетам: технический вклад > ценность для AstroFinSentinelV5 > community response.

---

## 1. Microsoft Agent Framework Python 1.8.0 — стабилизация Magentic multi-agent оркестрации

- **Источник:** GitHub — `microsoft/agent-framework`
- **Ссылка:** https://github.com/microsoft/agent-framework/releases/tag/python-1.8.0
- **Дата релиза:** 2026-06-04

**Краткое описание:** Крупный релиз вендорского multi-agent SDK от Microsoft, объединившего AutoGen и Semantic Kernel в единый graph-based фреймворк (1.0 GA был в апреле 2026). Версия 1.8.0 фиксирует спорное предупреждение в `MagenticBuilder` при использовании кастомного менеджера и вводит `UNSET` sentinel для корректной обработки `max_stall_count`. Поддерживаются паттерны sequential, concurrent, handoff, group chat и Magentic-One. Python-пакет стабилен на PyPI.

**Применение для AstroFinSentinelV5:** WorkflowBuilder с типизированными executor-нодами можно использовать как reference-архитектуру для финансового пайплайна (Researcher → Risk → Trader → Reviewer). Встроенная поддержка MCP и A2A-протоколов упрощает интеграцию с внешними источниками рыночных данных и broker-API. Magentic-One паттерн полезен для адаптивного управления «свормом» аналитических агентов в условиях высокой волатильности.

---

## 2. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems

- **Источник:** arXiv / OpenReview (research paper)
- **Ссылка:** https://openreview.net/forum?id=wmucOCOBPq
- **Дата:** опубликовано в этом месяце

**Краткое описание:** Академическая работа, предлагающая новый подход к координации LLM-агентов: union graph, собранный из комплементарных топологий через Monte Carlo Tree Search (MCTS) + Determinantal Point Process (DPP), иерархическая sparse-координация, активирующая только подграф на каждом шаге с компрессированными latent briefs, плюс local self-refinement этап. SOTA на 8 бенчмарках, в среднем +2.98% над сильными baselines и до +10.27% на MMLU-Pro.

**Применение для AstroFinSentinelV5:** Идеи sparse-активации и hierarchical briefs напрямую применимы для снижения стоимости оркестрации: вместо одновременного запуска всех аналитических агентов система может динамически выбирать sparse-подграф под текущий market regime. MCTS + DPP подход полезен для бэктестинга альтернативных цепочек решений в режиме what-if, а механизм local self-refinement можно использовать для автокоррекции сигналов при смене волатильности.

---

## 3. Hermes Agent v0.16.0 (Surface Release) — Kanban multi-agent swarm

- **Источник:** GitHub — `NousResearch/hermes-agent`
- **Ссылка:** https://github.com/NousResearch/hermes-agent/releases/tag/v2026.6.5
- **Дата релиза:** 2026-06-05

**Краткое описание:** Крупное обновление open-source multi-agent фреймворка с SQLite-бэкендом Kanban-доски (`~/.hermes/kanban.db`). Каждый воркер запускается в отдельном OS-процессе с собственной памятью и профилем. Релиз добавил: (1) leaner default skill set с environments: kanban/docker/s6 gate, (2) goal_mode cards с `/goal` loop и worker vision для прикреплённых изображений, (3) default assignee fallback + per-profile concurrency cap, (4) target_node proof gate для безопасной completion логики в распределённой среде. Model-agnostic core: работает с Claude, GPT-5.5, MiniMax, локальным Ollama.

**Применение для AstroFinSentinelV5:** Kanban-модель с per-worker process isolation — отличный шаблон для запуска изолированных финансовых агентов (риск-менеджер, арбитражер, sentiment-аналитик) без cross-contamination. Goal loop + file attachments легко адаптируется под долгосрочные миссии (например, мониторинг конкретной позиции с прикреплением отчётов). Environments gate даёт полезный паттерн динамической загрузки skills только под нужный market context (futures/options/forex).

---

## Прочие заметные релизы (для контекста)

- **simstudioai/sim v0.6.103** — добавлены OpenTelemetry-метрики для Grafana, ClickHouse block с hardened read-only enforcement, 7 новых knowledge-base connectors (Google Forms, Typeform, YouTube, S3, Sentry и др.).
- **CORAL v0.6.0 (Human-Agent-Society)** — обновление фреймворка autonomous self-evolution для Claude Code, Codex, Cursor, OpenCode.
- **DySCo (Dynamic Sparse Consensus)** — снижает O(N²) overhead в multi-agent debate до near-linear через budget-constrained edge selection.
- **HMASP** — первый end-to-end LLM multi-agent фреймворк для payment-воркфлоу.

---

*Источники: GitHub releases, OpenReview, arXiv, X/Twitter, Reddit, AI-community блоги. Период: 2026-06-02 — 2026-06-09.*

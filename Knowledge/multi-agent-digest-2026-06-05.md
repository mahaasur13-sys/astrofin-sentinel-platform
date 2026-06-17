# Multi-Agent AI Daily — 2026-06-05

**Источники:** arXiv / OpenReview, GitHub, X/Twitter, Reddit, Hugging Face, Microsoft DevBlogs, JetBrains Blog, Truefoundry

**Период:** 29 мая — 5 июня 2026 (последние 7 дней)

---

## Топ-3 за неделю

---

**1. CaveAgent — LLM как stateful runtime operator с persistent Python-средой**

- **Источник:** arXiv / OpenReview (2026, ID p3dlOhpqKD)
- **Краткое описание:** CaveAgent переосмысляет роль LLM-агента с «text generator» на «runtime operator». Архитектура использует dual-stream подход: семантический поток для лёгкого рассуждения + персистентный Python-runtime, который хранит и мутирует сложные объекты (DataFrame, DB-connection, state-машины) между ходами. Это устраняет context drift и снижает расход токенов до 28.4% (51% на data-heavy задачах). На бенчмарках Tau²-bench и BFCL превосходит baselines в 11 из 12 настроек, +13.5% на multi-turn retail-задачах, при этом 30B Qwen3-Coder достигает 94.4% — на уровне Claude Sonnet 4.5 и Gemini 3 Pro. Дополнительно расширяет Agent Skills open standard runtime-integrated skill management — навыки можно инжектить как исполняемый код.
- **Применение для AstroFinSentinelV5:** Концепция persistent runtime напрямую решает проблему текущих QuantAgent / CycleAgent, которые пересчитывают state с нуля на каждом вызове `run_sentinel_v5()`. Внедрение runtime-интегрированного state (DataFrame с positions, persistent DB-connection к market data, мутируемые cycle buffers) между ходами даст +28% экономии токенов и более стабильные решения в multi-turn сценариях (например, watch-list мониторинг). Runtime-интегрированные skills позволят оформить Muhurta-расчёты ElectoralAgent и Bradley seasonality как исполняемые навыки.

---

**2. langchain-dynamic-workflow v0.2.0 — Python как orchestration language для детерминированных multi-agent workflows**

- **Источник:** GitHub — nemori-ai/langchain-dynamic-workflow (v0.2.0, июнь 2026)
- **Краткое описание:** Python-фреймворк, инспирированный Claude Code Dynamic Workflows, инвертирует типичный control flow мультиагентных систем. Вместо того чтобы агенты сами управляли петлями и состоянием, control flow диктуется Python-оркестрационным скриптом, написанным разработчиком. Leaf-вызовы `agent()` выполняются в изолированных контекстах. Безопасность обеспечивается AST-based security gate + restricted exec environment. Примитивы: `agent`, `parallel`, `pipeline`, `race`, `phase`, `log`, `budget`, `workflow`. Все решения журналируются для воспроизводимого resume после сбоя. Интеграция с LangChain deepagents. Релиз v0.2.0 — июнь 2026.
- **Применение для AstroFinSentinelV5:** Это ровно тот паттерн, который нужен для формализации HYBRID_WEIGHTS и Conflict Resolution из `agents/_impl/synthesis_agent.py`. Trading-процедуру (router → 5 параллельных агентов → synthesis → risk gate) можно описать как детерминированный Python-скрипт с явными `parallel()` блоками и журналируемыми решениями — это и есть ATOM-KARL-009 Decision Audit Trail в виде исполняемого кода. AST-gate дополнительно защитит финансовые агенты от prompt-injection в runtime-скриптах.

---

**3. Microsoft Agent Framework @ BUILD 2026 — Agent Harness как first-class паттерн + Hosted Agents + CodeAct**

- **Источник:** Microsoft DevBlogs (BUILD 2026, конец мая 2026) + JetBrains PyCharm Blog
- **Краткое описание:** Microsoft выкатил крупное обновление MAF — open-source SDK и runtime для .NET и Python с единым API. Ключевые новинки: (1) **Agent Harness** как first-class production-паттерн (а не как DIY-обвязка вокруг LLM); (2) **Hosted Agents in Foundry Agent Service** — managed-хостинг с identity, autoscaling, session state, observability и versioning; (3) **CodeAct** — протокол, в котором агент пишет и исполняет код вместо JSON tool-calls (по аналогии со smolagents); (4) экспериментальная поддержка Foundry Toolbox MCP invocation. JetBrains параллельно опубликовал обзор «Top Agentic Frameworks 2026», где LangGraph, CrewAI, smolagents и MAF выделены как four primary paradigms. NVIDIA на Computex 2026 добавила свою orchestration-framework ноту, намекая на on-prem вариант.
- **Применение для AstroFinSentinelV5:** Agent Harness pattern — это формализация того, что уже частично сделано через `core/checkpoint.py` и `core/history_db.py`. Концепция Hosted Agents подсказывает направление миграции с SQLite + локального Python на managed-хостинг (Azure / Foundry) с готовой observability. CodeAct стоит пилотировать на QuantAgent — позволит агенту писать pandas/numpy-код для бэктеста прямо в ходе принятия решения, а не вызывать статические tools.

---

## Honorable mentions (не вошли в топ-3)

- **piotrwachowski/durable-agents** — Temporal-based durable execution для multi-agent систем (отказоустойчивость через event history)
- **shalinda-j/Claude-Team-MCP** — MCP hub для координации Claude Code / Cursor / Codex CLI в ролях PM/Backend/Frontend/QA
- **pi-subagents v0.27.0** (2026-05-30) — TypeScript фреймворк с evidence-driven acceptance и run-scoped finalization
- **voocel/agentcore v1.6.10** — Go-фреймворк с work-stealing IdleClaim и parent-to-child message queuing
- **EvoMaster** (OpenReview) — фундаментальный self-evolving agent framework, +316% над OpenClaw baseline на Humanity's Last Exam
- **FD-RAG** (OpenReview) — federated dual-system RAG с 8.4× ускорением latency
- **Paperclip** — приложение для управления AI-агентами как «team of agents for every person», быстро набирает популярность
- **Fetch.ai Agent Launchpad** — agentic token deployment platform для on-chain координации агентов
- **HuggingFace smolagents v1.26.0** (2026-05-29) — добавлен Exa в WebSearchTool, удалён WasmExecutor
- **Cloudflare agents@0.14.0** (2026-06-02) — agent Skills engine и structured failure envelope

---

*Сгенерировано автоматически. Все события опубликованы или активно обсуждаются в период 29 мая — 5 июня 2026. Применение к AstroFinSentinelV5 описано с учётом текущей архитектуры (RAG-First + LangGraph + Multi-Agent + Hybrid Signal) и AMRE / ATOM-KARL фреймворка.*

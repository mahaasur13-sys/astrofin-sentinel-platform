# Multi-Agent AI Daily — 2026-06-06

**Источники:** arXiv (AutoScientists), GitHub (Mastra, open-multi-agent), Microsoft DevBlogs / Build 2026, Cloud Security Alliance, JetBrains, DEV.to, X/Twitter

**Период:** 31 мая — 6 июня 2026 (последние 7 дней)

---

## Топ-3 за неделю

---

**1. AutoScientists (Harvard Zitnik Lab) — самопорождающиеся мультиагенты для долгих научных экспериментов**

- **Источник:** arXiv + Harvard Zitnik Lab, препринт «AutoScientists: Self-Organizing Agent Teams for Long-Running Scientific Experimentation» (Gao, Fang, Zitnik, конец мая 2026)
- **Краткое описание:** Полностью децентрализованная мультиагентная система для научных исследований. В отличие от классических supervisor–worker паттернов, у AutoScientists **нет центрального планировщика** — агенты сами интерпретируют общий experimental dataset, самоорганизуются вокруг перспективных направлений, оценивают proposal-ы до выделения ресурсов и ведут журнал успехов **и неудач** (failure documentation как first-class шаг). Эмпирически: ускорение сходимости обучения языковых моделей ×1.9, +12.5% точности на узких белковых ассеях (ProteinGym) и +6.5% на широких. Главный тезис авторов: «бутылочное горло AI-scientist — это governance, а не сырая capability модели».
- **Применение для AstroFinSentinelV5:** Концепция «failure documentation as first-class» напрямую встраивается в уже существующий AMRE/ATOM-KARL-009 Decision Audit Trail — `DecisionRecord` и `AuditLog.analyze_drift()` могут начать журналировать не только финальные сигналы, но и **failed hypotheses** (например, когда QuantAgent выдал сигнал LONG, а CycleAgent — STRONG_SELL, и какой из них оказался прав post-hoc). Децентрализация без супервизора подсказывает структуру нового sub-ecosystem: AstroCouncil теряет роль абсолютного координатора и становится равноправным с SynthesisAgent, а Bull/Bear Researchers получают право «ветировать» решения при наличии астро-фактора высокой силы. На уровне ATOM-KARL-010 это даст более честный OOS-fail-rate для KPI Control Loop.

---

**2. Microsoft Agent Framework v1.0 + CodeAct + Handoff pattern — «Agent Harness» как first-class production-паттерн**

- **Источник:** Microsoft DevBlogs (BUILD 2026, начало июня) + Microsoft Learn + JetBrains PyCharm Blog
- **Краткое описание:** Microsoft выкатил MAJOR-релиз MAF — open-source SDK и runtime для .NET и Python с единым API. Ключевые новинки: (1) **Agent Harness** как first-class паттерн (production-ready обвязка из tool-loop, conversation history, context compaction, planning, durable memory, skills, observability) с удобной `create_harness_agent()`; (2) **CodeAct** — протокол, где агент пишет и исполняет код вместо JSON tool-calls (по аналогии со smolagents, 67% vs 7% на GAIA benchmark); (3) **Handoff pattern** — формальная multi-agent оркестрация с явной передачей контекста между специализированными агентами; (4) **Hosted Agents in Foundry** — managed-хостинг с identity, autoscaling, session state, observability и versioning; (5) **A2A cross-runtime messaging** и **MCP tool discovery** на стабильных API. JetBrains параллельно выпустил «Top Agentic Frameworks 2026», где LangGraph, CrewAI, smolagents и MAF названы четырьмя основными парадигмами.
- **Применение для AstroFinSentinelV5:** Agent Harness pattern — это формализация того, что уже частично сделано вручную через `core/checkpoint.py` и `core/history_db.py`. CodeAct-протокол стоит пилотировать на QuantAgent: вместо вызова статических tools агент будет писать pandas/numpy-код для бэктеста прямо в ходе принятия решения. Handoff pattern решает давнюю проблему AstroCouncil — сейчас он «общается» с суб-агентами через разделяемые структуры, а MAF-формализация даст стандартизованный Handoff-контракт (тип контекста, условия передачи, таймауты). Hosted Agents в Foundry — направление будущей миграции с SQLite + локального Python на managed-хостинг с готовой observability.

---

**3. open-multi-agent v1.5.0 — TypeScript-native goal-to-DAG orchestrator с 6.3k stars и post-run trace dashboard**

- **Источник:** GitHub (open-multi-agent/open-multi-agent, v1.5.0, 30 мая 2026) + niteagent.com writeup
- **Краткое описание:** TypeScript-native фреймворк, который инвертирует control flow мультиагентных систем: ты даёшь ему **только goal** и команду агентов, а координатор сам декомпозирует цель в направленный ациклический граф задач (DAG) в runtime, параллелизует независимые ветки и синтезирует результат. Всего 3 runtime-зависимости. Поддержка MCP, mixed-provider команд (Anthropic, OpenAI, Gemini, Ollama), shared memory store, JSON-first CLI `oma`, post-run HTML trace dashboard с per-node assignees и token breakdown, lifecycle hooks (`beforeRun`/`afterRun`), AbortSignal, loop detection, context window strategies (sliding window, summarization, compaction), tool output truncation. Production checklist закрывает retry/backoff, observability и sandbox config. Реальный community traction — 6.3k stars за несколько недель.
- **Применение для AstroFinSentinelV5:** Несмотря на TypeScript-стек, сама модель «goal-to-DAG» — это то, чего не хватает текущему SynthesisAgent. Сейчас у нас hard-coded HYBRID_WEIGHTS и фиксированный pipeline `router → 5 параллельных агентов → synthesis → risk`. open-multi-agent подсказывает путь к **динамической композиции**: пользователь пишет «analyze BTC for swing trade», а оркестратор сам решает — нужно ли звать OptionsFlowAgent, или хватит базовой тройки Fundamental+Macro+Quant. Это даст +5-15% экономии на LLM-вызовах в типичных кейсах и позволит запускать «глубокие» конфигурации только когда запрос пользователя это оправдывает. Цикл «goal → DAG → execution → trace dashboard» — почти 1-в-1 воспроизводит то, что мы делаем через orchestration/sentinel_v5.py, но с визуальной трассировкой.

---

## Honorable mentions (не вошли в топ-3)

- **Mastra v1.39.0** (2026-06-03) — record-first notification signals с thread-scoped inbox, agent.sendNotificationSignal(), priority-aware delivery, state lanes через computeStateSignal(); opt-in working memory через state signals с unified-diff delivery.
- **verl v0.8.0** (RL multi-agent training) — multi-agent RL training capabilities, scalable agent framework uni-agent, per-sample tool routing, TRT-LLM rollout, улучшенный tool parser (Gemma4).
- **ORCHIDEAS + MAESTRO** (CSA, 2026-06-05) — nine-pillar secure-by-construction фреймворк дизайна агентных систем (Autonomy, Identity & Intent, Data, Context, Runtime, Human Oversight, Observability, Eval, Scalability), интегрированный с MAESTRO threat modeling.
- **OWASP Agentic AI Security Maturity Framework** (2026-06-03) — четырёхуровневая maturity-модель для agentic governance (от experimentation до continuous oversight с adaptive enforcement).
- **Singapore Agentic AI Governance Framework** (запущен в Давосе, январь 2026) — четыре governance-измерения для автономных агентов, первые в мире, с practical setup guide.
- **agentic-product-standard (Moai-Team-LLC)** — repo с 7-layer harness для LLM loop, single-agent + multi-agent скиллами, фокус на architecture/harness/evaluation discipline.
- **duet-agent (dzhng)** — agent harness для jobs that outlive the chat: durable memory, multi-agent relay, resume в новом sandbox через дни/месяцы.
- **antigravity-awesome-skills** — npm-установщик reusable SKILL.md playbooks для Claude Code / Cursor.
- **Containarium v0.22.4** — open-source self-hostable sandbox-платформа для agent-native containers, plug-in для Claude Code / Cursor / OpenCode через MCP.
- **TAOCAO/sandcastle** — TypeScript библиотека для оркестрации coding agents в изолированных sandboxes (Docker/Podman/Vercel), с branch strategies (Head/Merge-to-head/Branch).
- **Google DeepMind Co-Scientist** (упоминание) — previews automates scientific hypothesis generation, в связке с AutoScientists формирует тренд «AI as research colleague».

---

*Сгенерировано автоматически. Все события опубликованы или активно обсуждаются в период 31 мая — 6 июня 2026. Применение к AstroFinSentinelV5 описано с учётом текущей архитектуры (RAG-First + LangGraph + Multi-Agent + Hybrid Signal) и AMRE / ATOM-KARL фреймворка.*

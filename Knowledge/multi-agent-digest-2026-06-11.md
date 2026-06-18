# Multi-Agent AI Daily — 2026-06-11

**Источники:** GitHub (langchain-ai/deepagents, langchain-ai/langgraphjs, Human-Agent-Society/CORAL, ziyu111777/HiveMind, axocoatl/axocoatl, agentlas-ai/Hephaestus, Jah-yee/orch, langflow-ai/langflow, spring-agent-flow), OpenReview / arXiv (MMAD, MARS, SIMAS, URAFM, DxChain, RefCon, Ask-or-Assume, Latent Agents, Beyond-Tokens), X/Twitter (@LangChain_JS, @itsharmanjot, @vorty279, @kunaldchowdhury, @PacktPublishing), O'Reilly Radar

**Период:** 4–11 июня 2026 (последние 7 дней)

---

## Топ-3 за неделю

---

**1. LangChain Deep Agents — open-source реплика Claude Code под MIT (любая модель, $0) + LangGraphJS 1.4.0 с durable execution**

- **Источник:** GitHub `langchain-ai/deepagents` (v0.1.10, 0.1.9) + PR #3759/3821/3810/3792 + PR #2494/2500/2497 `langchain-ai/langgraphjs` v1.4.0 + X (@itsharmanjot, @LangChain_JS, июнь 2026)
- **Краткое описание:** LangChain официально опенсорснул **Deep Agents** — batteries-included agent harness, повторяющий архитектуру Claude Code: planning-first, TODO-список, filesystem access, subagent delegation, human-in-the-loop, long-term memory, middleware pipeline (`BackendMiddleware`, `SkillsMiddleware`, `CodeInterpreterMiddleware`). MIT-лицензия, `pip install deepagents → create_deep_agent(tools=[...])`. Параллельно **LangGraphJS 1.4.0** добавил production-grade durability: drain/resume графов, recovery от node failures, **timeouts** для bound runaway work, **DeltaChannel** для снижения checkpoint bloat. Дополнительно — subagent cards hydra­tion при thread reconnect, optimistic submit echo, v3 streaming protocol. Packt Publishing анонсировал книгу «Multi-Agent AI Engineering» от создателя AutoGen. Сильный community response: релиз Deep Agents разошёлся по X/Twitter в течение 24 часов.
- **Применение для AstroFinSentinelV5:** Deep Agents pattern — это готовая реализация того, что мы сейчас делаем вручную через `core/checkpoint.py` + `core/history_db.py` + R-08. Конкретные wins: (1) `SkillsMiddleware` напрямую заменяет наши ad-hoc astro-skills (Muhurta, Bradley seasonality) на формальный runtime с `requested_skills` state key; (2) subagent delegation из коробки решает проблему AstroCouncil → 5 суб-агентов (сейчас мы запускаем их через `parallel` и shared `TradingSignal.from_agents()`, а Deep Agents даёт формальный handoff с контекстом); (3) LangGraphJS 1.4.0 DeltaChannel + drain/resume переносимы в Python-LangGraph и закрывают пункт TODO «DB Migration: SQLite → PostgreSQL + TimescaleDB + pgvector» в части persistent state. Начать стоит с **пилота** `BackendMiddleware` поверх существующего `core/checkpoint.py`, чтобы не ломать HYBRID_WEIGHTS и conflict resolution.

---

**2. MMAD (Multi-Agent Mutual Awareness Debate) — двух-уровневая Theory-of-Mind framework, стабилизирующая дебаты маленьких LLM**

- **Источник:** OpenReview `0h3dbL6Iy3` (ACL ARR 2026 submission) + смежные arXiv-работы «Beyond tokens: latent communication in LLM MAS» (2606.05711) и «Latent Agents: A Post-Training Procedure for Internalized Multi-Agent Debate» (Cambridge, Hacker News, июнь 2026)
- **Краткое описание:** MMAD решает **sycophantic drift** — главную болезнь multi-agent debate, когда агенты 3–8B (Mistral-7B, Phi-4-mini, Qwen2.5-7B) «капитулируют» перед peer-pressure вместо reasoned updates. Архитектура: **Tier 1** — peer-level Mutual Theory of Mind (агент явно моделирует, *почему* peer пришёл к своему выводу, прежде чем обновлять своё мнение); **Tier 2** — teacher-level MToM с 30B «учителем», который делает second-order ToM и даёт персонализированные подсказки каждому агенту, не раскрывая финального ответа. Эмпирически: **+73.3 п.п.** на GSM8K, **+23.8 п.п.** на CodeQA, **+16.7 п.п.** на CS1QA, **+31.7 п.п.** на CommonsenseQA (Round 4 vs single-agent). Drift на GSM8K упал до **0.0%** к 4-му раунду. Смежная работа «Beyond tokens» формализует latent communication (KV-cache, hidden states) для ускорения MAS, а «Latent Agents» (Cambridge) показывает, что single-LLM с post-training «сжимает» multi-agent debate в себя, **срезая до 93% токенов** при сохранении качества.
- **Применение для AstroFinSentinelV5:** Прямое применение — **BullResearcher ↔ BearResearcher** (сейчас каждый даёт свой 5%-вес голос, и при конфликте нет формализованного протокола разрешения — мы просто суммируем). MMAD-style ToM позволит Bull-агенту сначала смоделировать, *почему* Bear-агент пришёл к медвежьему выводу (опереться на `astro_factors` Bear-агента, на его risk-engineering), и только потом либо обновить, либо аргументированно возразить. Latent-communication и Latent Agents подсказывают второй оптимизационный путь: если у нас уже есть 5 Astro-суб-агентов + 8 базовых, можно через reward scheduling + length clipping «впечатать» их reasoning в один синтезатор, экономя до 50–90% токенов (то, что MARS уже показал — −50% токенов при сохранении MAD-качества через review-style workflow). Это меняет архитектуру SynthesisAgent с 100% coordinator на **debate-orchestrator** с Tier-1/Tier-2 ToM.

---

**3. Axocoatl / Hephaestus / HiveMind / CORAL v0.6.0 / open-multi-agent v1.5.0 — волна «orchestrator-over-CLI» фреймворков с MCP и durable state**

- **Источник:** GitHub — `axocoatl/axocoatl` (Rust, stigmergic coordination), `agentlas-ai/Hephaestus` v0.3.0 (no-code multi-agent builder), `ziyu111777/HiveMind` (AgentFlow — multi-framework runtime), `Human-Agent-Society/CORAL` v0.6.0 (2026-06-05, self-evolving autoresearch), `open-multi-agent/open-multi-agent` v1.5.0 (TS goal-to-DAG), `Jah-yee/orch` (multi-agent task orch), `greenticai/greentic-runner` agent-graph v2 (supervisor/parallel/join), `langflow-ai/langflow` v1.10.0 (Code Agents, multi-version flows), `spring-agent-flow` (Spring AI graph-based orchestration, июнь 2026)
- **Краткое описание:** За последние 7 дней вышла волна из 8+ «orchestrator-over-CLI» фреймворков с разными акцентами. **Axocoatl** — Rust, stigmergic coordination без центрального оркестратора, EventLattice с pheromone-сигналами, персистентные агенты с 4-tier memory. **Hephaestus** — no-code, превращает «идею» в installable multi-agent team (HQ, Memory Curator, Policy Gate, QA), локальный ontology-runtime. **HiveMind (AgentFlow)** — Java/Spring Boot API + Python workers, Redis-очереди, Postgres-state, unified runtime, который запускает LangGraph/AutoGen/CrewAI/PydanticAI через адаптеры. **CORAL v0.6.0** — light-weight self-evolving multi-agent фреймворк, совместимый с Claude Code/Codex/Cursor/OpenCode/Kiro. **open-multi-agent v1.5.0** — TypeScript-native goal-to-DAG с 6.3k stars, MCP, mixed-provider, HTML trace dashboard. **langflow v1.10.0** — добавлены CodeAct-агенты (CodeAct, OpenDsStar) и multi-version flows для projects. **spring-agent-flow** — граф-оркестрация поверх Spring AI с JDBC/Redis checkpoints и resilience4j circuit breaker.
- **Применение для AstroFinSentinelV5:** Главный тренд волны — **«внешний оркестратор + локальные агенты»** вместо «один монолит-фреймворк». Это подтверждает правильность нашего выбора с AMRE/ATOM-KARL как orchestration-слоя над 13 специализированными агентами. Конкретные takeaways: (1) **Axocoatl** подтверждает наш путь к **децентрализации AstroCouncil** (вместо супервизора — EventLattice-стиль активации суб-агентов по сигналу `TaskCompleted`); (2) **HiveMind (AgentFlow)** — это reference architecture для будущей миграции на Postgres + Redis + SSE-streams (закрывает TODO про DB Migration); (3) **open-multi-agent** с HTML trace dashboard — почти 1-в-1 то, что нам нужно для AMRE/ATOM-KARL-009 (сейчас `AuditLog.export_json()` — это JSON, а нам нужен визуальный per-agent trace); (4) **langflow v1.10.0** + CodeAct-агенты = быстрый способ дать QuantAgent runtime-инструмент написания pandas/numpy-кода для бэктеста. Стоит провести **RFC**: оставляем ли мы Python-LangGraph как ядро, или переходим на HiveMind-style split (Java/Python)?

---

## Honorable mentions (не вошли в топ-3)

- **LangGraphJS 1.4.0** (2026-06-09) — drain/resume, DeltaChannel, timeouts, recovery, subagent cards, optimistic submit echo, v3 streaming.
- **langchain==1.3.6** (патч) — fix для summarization trigger compatibility; мелкое, но влияет на multi-agent workflows.
- **CrewAI 1.14.7a2** (pre-release, лето 2026) — conversational flow traces, surface finish_reason/sampling params, chat API, Flow DSL split на focused decorator modules.
- **Langflow v1.10.0** — CodeAct и OpenDsStar агенты, file ingestion components, LFX Extension Framework, multi-version flows.
- **spring-agent-flow** — graph-based orchestration поверх Spring AI, JDBC/Redis checkpoints, resilience4j.
- **atomr-agents v0.20.0** — Claude Agent SDK harness, MicroVM sandbox, Meetings/STT harnesses, Phase C (async scorers, Python workflow runner).
- **CORAL v0.6.0** (Human-Agent-Society) — self-evolving multi-agent autoresearch framework, совместим с Claude Code/Codex/Cursor/OpenCode/Kiro.
- **MARS** (OpenReview `rG0PKKeYfI`) — role-based multi-agent review system, экономит ~50% токенов vs MAD при сохранении качества.
- **SIMAS** (OpenReview `VC0ktUy18d`) — scaling laws для homogeneous MAS: больше агентов ≠ лучше; sweet spot зависит от task type.
- **URAFM** (OpenReview `r9rzf64V0O`) — single-LLM с multi-path expert voting, +3.3 п.п. на relevance annotation.
- **DxChain** (OpenReview `GY0X2Y9U4u`) — clinical multi-agent с Profile-Then-Plan + Angel-Devil adversarial debate.
- **Ask-or-Assume** (OpenReview `a25dmoIflA`) — uncertainty-aware multi-agent scaffold для coding agents, 69.4% vs 61.2% baseline на OpenHands + Sonnet 4.5.
- **RefCon** (OpenReview `fatsyRRKEs`) — iterative refinement + contrastive memory extraction, +21.6% на ACE без gold labels.
- **LGRA** (Springer 2026) — LLM как online semantic teacher для cooperative MARL, SOTA на 13/14 LBF/RWARE/SMAC.
- **Latent Agents** (Cambridge, июнь 2026) — post-training «сжимает» multi-agent debate в single-LLM, −93% токенов, emergent interpretable subspaces.
- **Beyond tokens: latent communication** (arXiv 2606.05711) — unified framework для latent communication в LLM MAS (embeddings, hidden states, KV-caches).
- **Open Multi-Agent** v1.5.0 — TS goal-to-DAG orchestrator, 6.3k stars, MCP, mixed-provider, HTML trace dashboard.
- **Jah-yee/orch** — multi-agent task orch для Claude/Codex/OpenCode/Kimi, GitHub Projects V2 sync, per-task worktree isolation.
- **gentle-ai (Codex multi-agent SDD)** — opt-in multi-agent delegation через spawn_agent/wait_agent/close_agent, default off, agents.max_threads=4.
- **Pydantic AI / Logfire** — продолжает набирать adoption (Overjoy, Lema AI мигрировали с LangChain), позиционируется как type-safe end-to-end agent stack.
- **Hephaestus v0.3.0** — multilingual search + grounded-agent wiring + local ontology runtime.
- **Containarium v0.22.4** — self-hostable sandbox-платформа для agent-native containers.
- **O'Reilly Radar «The AI Agents Stack (2026 Edition)»** — survey показывает 89% production-команд имеют observability, но только 52% — evals.

---

*Сгенерировано автоматически. Все события опубликованы или активно обсуждаются в период 4–11 июня 2026. Применение к AstroFinSentinelV5 описано с учётом текущей архитектуры (RAG-First + LangGraph + Multi-Agent + Hybrid Signal) и AMRE / ATOM-KARL фреймворка.*

# Multi-Agent AI Daily Digest — 2026-06-22

> Утренний дайджест по multi-agent AI инструментам, исследованиям и community-обсуждениям за последние 7 дней. Подборка сфокусирована на практической значимости для системы мультиагентов **AstroFinSentinelV5** (RAG-First + LangGraph + Multi-Agent + Hybrid Signal, ~13 агентов с фиксированными весами + AstroCouncil).

---

## Источники мониторинга

- **arXiv (cs.AI / cs.MA / cs.CL)** — препринты по multi-agent системам, agent coordination, LLM orchestration
- **GitHub** — релизы и активные репозитории по multi-agent framework, agent orchestration
- **OpenReview** — работы с топ-конференций (ICML, NeurIPS track)
- **X (Twitter) / LinkedIn** — обсуждения в сообществе, продуктовые анонсы
- **VentureBeat / отраслевые медиа** — обзоры релизов

---

## Топ-3 за сегодня

### 1. Salesforce Agentforce Multi-Agent Orchestration — GA с Atlas 3.0 и description-based routing ($800M ARR, +169% YoY)

- **Источник:** Salesforce (Agentblazer Trailhead, TechTimes, 15–16 июня 2026) + X (`@d3x2`) — продуктовый релиз + сообщество
- **Краткое описание:** Multi-Agent Orchestration в Agentforce достигла General Availability 15 июня 2026 как центральный элемент Summer '26 release. **Atlas Reasoning Engine 3.0** маршрутизирует задачи к специализированным субагентам (billing, scheduling, product-support) на основе их plain-language **описаний**, а не хардкод-роутинга. Tableau MCP интегрирует live-аналитику прямо в разговор. ARR составляет **$800M (+169% YoY)** — крупнейший enterprise-сигнал о том, что multi-agent orchestration вышел в production-ready стадию. Ключевой инсайт: agent's description, а не underlying model, решает, правильно ли роутится работа — качество промптов субагентов становится критичным.
- **Применение для AstroFinSentinelV5:** Подтверждает направление из TODO на замену hardcoded weighted-voting в `SynthesisAgent` (100% coordinator) на **description-driven routing**. Прямое применение: каждый из 13 агентов уже имеет docstring-описание своей зоны ответственности — можно построить meta-router, который выбирает не "какой агент главнее по весу", а "какой агент наиболее релевантен текущему режиму рынка" (regime-aware routing). Например, при regime=HIGH_VOLATILITY → MacroAgent + RiskAgent приоритет, при regime=BULL_TREND → QuantAgent + TechnicalAgent. Это естественно ложится на существующую логику `core/volatility.py` и amre_kpi control loop.

### 2. Foundry — Host-Owned Trust & Memory для long-horizon multi-agent swarms (SOTA на math, GPU kernels, computational biology)

- **Источник:** OpenReview (MWLIRDa4DC, ICML 2026 track, Tianyi Zhang et al.) — академическая работа
- **Краткое описание:** Foundry решает два главных bottleneck long-horizon multi-agent discovery: (1) **trust** — агенты предлагают идеи, но центральный host верифицирует их через authoritative evaluator, (2) **memory** — persistent established-facts registry предотвращает "rediscovering" уже подтверждённых фактов. Архитектура: **hypervisor → orchestrator → solver** с token-budgeted task routing. SOTA-результаты в комбинаторной математике, GPU kernel engineering, computational biology без domain-specific модификаций. Главная идея: прогресс в agent-based discovery зависит не столько от agent capability, сколько от **system boundaries** (trustworthy verification + persistent memory).
- **Применение для AstroFinSentinelV5:** Очень прямо ложится на уже существующий **AMRE-стек** (`agents/_impl/amre/audit.py` — DecisionRecord, AuditLog, ATOM-KARL-009). Foundry фактически формализует то, что у SentinelV5 уже частично есть: `DecisionRecord.state_hash` + `find_by_state_hash()` — это и есть "established-facts registry" в миниатюре. Конкретный actionable: добавить **двухуровневую верификацию** в `KARLSynthesisAgent` — (a) каждый агент предлагает сигнал с confidence, (b) SynthesisAgent делает cross-agent verification (например, если QuantAgent говорит LONG, а SentimentAgent говорит SHORT с высокой confidence — требуется explicit reconciliation step, а не простое взвешенное голосование). Также: расширить `AuditLog` с "verified_facts" subset, который не пересчитывается при каждом run.

### 3. CAID — Centralized Asynchronous Isolated Delegation: branch-and-merge для SWE-агентов (+26.7% PaperBench, +14.3% Commit0)

- **Источник:** OpenReview (zayaq7ssvH, ICML 2026 track, Graham Neubig et al.) — академическая работа
- **Краткое описание:** CAID формализует паттерн **"центральный менеджер → dependency-aware план → параллельные субагенты в изолированных worktree → branch-and-merge через executable tests"**. Главная находка: **branch-and-merge через git** как центральный coordination-механизм работает лучше, чем shared mutable state. На **PaperBench +26.7%** accuracy, на **Commit0 +14.3%** vs single-agent baseline. Практически: SWE-примитивы (worktree, branch, commit, merge, test) заменяют сложные message-bus-архитектуры. Показывает, что для long-horizon задач централизованное планирование + асинхронное выполнение + test-based verification превосходят pure decentralized подходы.
- **Применение для AstroFinSentinelV5:** Подтверждает и конкретизирует стратегию для **research-агентов AstroCouncil** (BradleyAgent, GannAgent, CycleAgent, TimeWindowAgent, ElectoralAgent — суммарно ~16% веса). Вместо общего state Swiss Ephemeris (через `@require_ephemeris`), где несколько агентов могут конкурировать за один и тот же snapshot, можно выделить **изолированные расчётные ветки** — каждый астро-агент получает свой snapshot позиций планет и свою интерпретацию, а `AstroCouncilAgent` мерджит результаты с **верификацией через cross-check** (например, Bradley и Gann дают схожий тайминг → высокая confidence, расходятся → требуется arbitration). Branch-and-merge хорошо ложится на `TradingSignal.from_agents()` логику и `confidence_final` расчёт в AMRE.

---

## Дополнительные сигналы (вне топ-3, для контекста)

- **AAOSA — distributed orchestration** (Cognizant AI Lab, X) — паттерн "каждый агент сам оценивает входящий input и забирает релевантные части" вместо центрального orchestrator. Альтернативный подход к Foundry/CAID — emergent claim-based coordination.
- **Databricks Agent Bricks** (X, 14 июня 2026) — Supervisor Agent + MCP + MLflow 3.0 + Unity Catalog governance. Продакшен-готовый стек для enterprise multi-agent с lineagedata.
- **Omnigent** (Databricks open-source, 15 июня 2026) — open-source платформа для интеграции Claude Code, Codex и других агентов в одну систему с policy + sandboxing.
- **Agent Switchboard — Orchestration category** (X, 18 июня 2026) — каталог multi-agent frameworks: AgentRQ, Temporal (20k+⭐), Hatchet, LangGraph, CrewAI, AutoGen.
- **From Trainee to Trainer** (arXiv 2606.17682) — LLM как Environment Engineer для multi-agent RL, MAPF-FrozenLake testbed.
- **DT-GAT-MARL** (Nature Scientific Reports) — graph-attention multi-agent RL для динамической интерсепции; топологически адаптивный, концептуально применимо к динамическому перевзвешиванию агентов.
- **Artificial Leviathan** (Frontiers in Physics) — Hobbesian social contract framework для emergent LLM-agent society; интересно для long-term emergent coordination research.
- **PULSE** (OpenReview) — evaluation framework для human-agent collaboration, -40% confidence interval vs A/B; релевантно для оценки качества SentinelV5.
- **SWE-chat** (OpenReview) — 6,000 real coding sessions, 355k tool calls; эмпирические данные о том, как агенты реально используются в production.
- **MIRA** (Nature) — autonomous medical AI agent с 11+ tools, FHIR/ICD/SNOMED; референс для tool-rich агента.
- **Google DeepMind AI Control Roadmap** (18 июня 2026) — 15 system-level defenses для agent security, 3 уровня (individual/multi-agent/ecosystem); напрямую релевантно для AMRE risk management.

---

*Сгенерировано автоматически. Источники: arXiv, OpenReview, GitHub, X/Twitter, Salesforce Trailhead, TechTimes, Nature, Frontiers.*
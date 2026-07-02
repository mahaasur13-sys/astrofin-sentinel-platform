# Multi-Agent AI Daily Digest — 2026-04-27

## Источники

- GitHub: Search по запросам "multi-agent AI framework", "agent orchestration", "multi-agent tools"
- arXiv: Search по "multi-agent LLM", "agent collaboration", "multi-agent systems", "agent coordination"
- Twitter/X: Поиск по #multiagent, #AIagents, #agentframework
- Форумы: Reddit, Medium, LinkedIn, industry blogs

---

## Топ-3 за неделю

** [Graph-of-Agents: Graph-based Framework for Multi-Agent LLM Collaboration] **
- Источник: arXiv (arXiv:2604.17148)
- Краткое описание: Фреймворк координирует несколько LLM через графовую структуру — использует model cards для выбора релевантных агентов, строит направленные рёбра на основе кросс-агентного анализа ответов и применяет forward/reverse message passing для уточнения результатов. Эмпирически показано, что GoA с 3 агентами превосходит базовые системы с 6 агентами на бенчмарках MMLU, MMLU-Pro, GPQA, MATH, HumanEval, MedMCQA. Технический вклад заключается в principled подходе к pruned агент-пулу и графовому протоколу коммуникации.
- Применение для AstroFinSentinelV5: Механизм выбора агентов по model cards пригодится для динамического назначения специализированных агентов (аналитик, риск-менеджер,execution) в зависимости от типа финансовой задачи. Графовая координация улучшит качество коллаборативного reasoning при принятии инвестидционированных решений.

** [HiveMind: OS-Inspired Scheduling for Concurrent LLM Agent Workloads] **
- Источник: arXiv (arXiv:2604.17111)
- Краткое описание: HTTP-прокси, координирующий параллельных LLM-агентов с помощью OS-примитивов — admission control, rate-limit tracking, AIMD backpressure с circuit breaking, token budget management и priority queuing. Не требует модификации кода агентов. Демонстрирует сокращение failures under contention с 72-100% до 0-18%, элиминирует 48-100% compute waste. Overhead менее 3ms на запрос. MIT license.
- Применение для AstroFinSentinelV5: Критически важно для системы с множеством одновременно работающих агентов, обращающихся к rate-limited LLM API. Admission control и token budgeting обеспечат отказоустойчивость при пиковых нагрузках, а priority queuing гарантирует, что time-sensitive trading decisions получат ресурсы в первую очередь.

** [Microsoft Agent Framework] **
- Источник: GitHub (microsoft/agent-framework)
- Краткое описание: Кросс-языковый (Python + .NET) фреймворк для построения, оркестрации и деплоя AI-агентов и multi-agent workflows. Поддерживает graph-based workflows с streaming, checkpointing, human-in-the-loop и time-travel debugging. Включает экспериментальные "AF Labs" с RL и benchmarking. Свежий релиз python-1.1.0 (April 2026), ~9.7k stars, 120 contributors, активное развитие.
- Применение для AstroFinSentinelV5: Graph-based оркестрация с human-in-the-loop позволит строеть надежные финансовые workflows с возможностью вмешательства человека. Time-travel debugging критичен для аудита принятых решений и отладки сложных multi-agent сценариев (например, backtesting стратегий).

---

## Дополнительно (также релевантно)

- **MPAC** (arXiv:2604.09744v1) — протокол многоprincipals координации с 5-слойной архитектурой, intent-first coordination, governance layer. ~95% сокращение coordination overhead.
- **CAMCO** (arXiv:2604.17240) — policy-aware координация для enterprise AI. Zero policy violations, 92-97% utility retention.
- **REDEREF** (arXiv:2603.13256) — training-free routing controller. 28% token reduction, 17% fewer agent calls.
- **PSMAS** (arXiv:2604.17400) — token-efficient phased scheduling. 21-35% token savings при потере <2.1% качества.
- **Agent Orcha** (GitHub ddalcu/agent-orcha) — declarative YAML, model-agnostic, P2P sharing, in-browser studio.
- **KiwiQ** (GitHub rcortx/kiwiq) — production-grade platform с 24+ node types, 27+ ready workflows, PostgreSQL/MongoDB/Weaviate/Redis memory.
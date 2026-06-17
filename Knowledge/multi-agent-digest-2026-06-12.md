# Multi-Agent AI Daily — 2026-06-12

Утренний дайджест по multi-agent AI инструментам, фреймворкам и исследованиям.

**Период поиска:** последние 7 дней (2026-06-05 — 2026-06-12)
**Источники:** GitHub, arXiv/OpenReview, Hugging Face Papers, web_search, X/Twitter
**Критерий отбора:** наибольший technical contribution + ценность для AstroFinSentinelV5 + community interest

---

## Топ-3 находки

### 1. MARS: Role-Based Multi-Agent Collaboration (~50% reduction in token usage)

- **Источник:** arXiv/OpenReview — [MARS preprint](https://openreview.net/forum?id=rG0PKKeYfI)
- **Краткое описание:** MARS заменяет дорогостоящие peer-to-peer дебаты в multi-agent системах (как в MAD) на структурированный review-centric пайплайн: Author → несколько Reviewer-агентов → Meta-reviewer. Эксперименты на нескольких бенчмарках показывают, что точность сохраняется на уровне MAD, а расход токенов падает примерно на 50%. Это прямой ответ на главную боль всех multi-agent систем — взрывной рост стоимости при росте числа агентов.
- **Применение для AstroFinSentinelV5:** Взять паттерн «author + N reviewer + meta-reviewer» для финансовых сценариев, где дорого каждый раз поднимать всех агентов на дебаты. Можно использовать для второго уровня валидации торговых сигналов или risk-reports: один агент-аналитик генерирует thesis, 2-3 reviewer-агента (technical/fundamental/sentiment) дают оценки, meta-reviewer собирает финальное решение. Экономия токенов критична при больших портфелях.

---

### 2. EMS: Efficient Majority-then-Stopping для multi-agent voting (~32% fewer agents)

- **Источник:** arXiv/OpenReview — [EMS preprint](https://openreview.net/forum?id=YsdEcidY7q)
- **Краткое описание:** EMS превращает multi-agent voting в reliability-aware scheduling задачу. Вместо того, чтобы ждать ответа от всех агентов, фреймворк оценивает надёжность каждого (Agent Confidence Modeling), адаптивно выбирает, кого спрашивать (Adaptive Incremental Voting) и обновляет веса по ходу (Individual Confidence Updating). Ранний стоп, как только набирается majority. На 6 бенчмарках это сократило количество вызванных агентов на ~32% без потери качества.
- **Применение для AstroFinSentinelV5:** В trading-совете, где сейчас каждый сигнал идёт через всех агентов, можно приоритизировать вызовы по исторической точности каждого агента на конкретном типе сигнала (momentum/mean-reversion/breakout). Сильные агенты голосуют первыми, слабые подключаются только при спорных результатах. Даёт ускорение + снижение стоимости + автоматический re-ranking агентов по их реальной performance.

---

### 3. AgentScope v2.0.1: Agent Team service для multi-agent coordination

- **Источник:** GitHub — [agentscope-ai/agentscope v2.0.1](https://github.com/agentscope-ai/agentscope/releases/tag/v2.0.1) (релиз 2026-06-05)
- **Краткое описание:** В фреймворке AgentScope (от Alibaba/DAMO) появился новый Agent Team service — рефакторинг agent service, который даёт нативную поддержку координированной multi-agent работы как единой сущности. В отличие от одноуровневых multi-agent setups, team-service вводит абстракцию команды с разделяемым контекстом, lifecycle-управлением и согласованной маршрутизацией задач между участниками.
- **Применение для AstroFinSentinelV5:** Готовая абстракция «agent team» с lifecycle и shared context — это ровно то, чего не хватает, когда несколько специализированных агентов (research/risk/execution/sentiment) должны работать над одной сделкой как единое целое. Можно либо взять AgentScope как runtime-каркас для одной из подсистем, либо портировать идею team-service (shared team context, role-based routing) в собственный orchestrator.

---

## Дополнительные сигналы (не вошли в топ-3, но值得关注)

- **crewAI 1.14.7a2** — добавлены conversational flow traces, route-aware DSL triggers, chat API для multi-turn сценариев. Полезно для логирования диалогов между агентами AstroFinSentinelV5.
- **MTOF/MMAD** — Mutual Theory-of-Mind фреймворк для стабилизации дебатов маленьких LLM (3-8B), устраняет sycophantic drift. Интересно для случая, когда нужно использовать бюджетные модели в рое.
- **POISE: AI Scientist** — closed-loop LLM-RL discovery: автоматически нашёл policy optimization, улучшающий weighted Overall с 47.8 до 52.5. Применимо к RL-компонентам вашей системы.
- **AtomR Agents v0.20.0** — MicroVM sandbox на Firecracker/KVM для безопасного исполнения кода агентами, Claude Agent SDK harness как first-class. Полезно для secure execution пользовательских стратегий.

---

## Резюме

Сегодняшний день дал три сильные работы, объединённые одной темой: **как сделать multi-agent системы дешевле и надёжнее без потери качества**. MARS и EMS — это исследования с конкретными метриками экономии (50% токенов, 32% агентов), а AgentScope v2.0.1 — production-ready runtime-абстракция, которую можно попробовать сразу. Все три паттерна (role-based review, reliability-weighted voting, agent-team service) переносимы в архитектуру AstroFinSentinelV5.

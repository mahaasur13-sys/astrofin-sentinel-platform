# Multi-Agent AI Daily — 20 июля 2026

Период мониторинга: 13–20 июля 2026. В отбор включены материалы, одновременно релевантные multi-agent/tool-use/coordination, новые за последние 7 дней и содержащие практический технический вклад.

## 1. Reward-Free Evolving Agents via Pairwise Validator

- **Источник:** arXiv, 15 июля 2026 — https://arxiv.org/abs/2607.14408v1
- **Краткое описание:** Работа заменяет дорогой скалярный reward в self-evolving agent loops на pairwise validator: замороженная LLM сравнивает родительскую и дочернюю версию агента и решает, какая лучше. Подход интегрирован в GEPA, ADRS и ShinkaEvolve; на большинстве проверенных конфигураций он сопоставим или превосходит reward-based baseline, снижая потребность в разметке и калибровке шкалы.
- **Применение для AstroFinSentinelV5:** Использовать pairwise gate для сравнения версий промптов и политик агентов Fundamental/Quant/Sentiment по audit-trailed backtest episodes. KARL может принимать только те изменения, которые проходят независимое сравнение по PnL, drawdown, confidence calibration и качеству объяснений, не полагаясь на один нестабильный reward.

## 2. Orchestrating Power Grid Studies with Multi-Agent AI and MCP Servers

- **Источник:** arXiv, 14 июля 2026 — https://arxiv.org/abs/2607.14158v1
- **Краткое описание:** Авторы показывают практическую схему подключения LLM-агентов к численному симулятору через MCP-интерфейс pypowsybl-mcp: агенты настраивают симуляции, запускают анализы и получают результаты через стандартизированные tool calls. Важны не только MCP, но и human-in-the-loop, аудитируемость и оценка workflow по техническим и пользовательским метрикам.
- **Применение для AstroFinSentinelV5:** Перенести паттерн на data_room: оформить рыночные резолверы и backtest/simulation actions как типизированные MCP tools с политиками доступа, подтверждением рискованных действий и полным DecisionRecord. Это усилит RAG-first слой и позволит воспроизводимо связывать агентские выводы с фактическими расчётами.

## 3. Agent Framework Go / практический запрос на графовую оркестрацию

- **Источник:** Forum — Reddit r/AIDeveloperNews, 15 июля 2026; GitHub: https://github.com/microsoft/agent-framework-go
- **Краткое описание:** Обсуждение публичного preview Go-реализации Microsoft Agent Framework описывает графовые workflow с последовательным, параллельным, групповым и условным выполнением, middleware, human approval, OpenTelemetry и поддержкой разных провайдеров. Это заметный community signal в пользу явного stateful orchestration вместо свободного обмена сообщениями между агентами.
- **Применение для AstroFinSentinelV5:** Сравнить с текущим LangGraph orchestration по трём критериям: checkpoint/retry semantics, distributed tracing и human approval для торговых действий. Практически полезные идеи — унифицированный middleware для tool calls и OTel-трассировка цепочки Router → Agent Council → KARL → risk gate; сам Go runtime не нужно внедрять без подтверждения latency/операционных преимуществ.

## Дополнительные наблюдения

- В GitHub за неделю также заметен релиз `earendil-works/pi` v0.80.7 (14 июля): cache-friendly dynamic tool loading и inherited toolChoice полезны для tool-heavy агентских циклов, но релиз не вошёл в топ-3 из-за меньшего прямого влияния на multi-agent coordination.
- Из свежих arXiv-материалов `Speculate with Memory` (14 июля) показывает 19–39% прироста точности action prediction и до 2,5× для observation prediction; это перспективно для фонового speculative execution, но работа не является multi-agent-specific.
- X/community обсуждения дополнительно подтверждают тренд на shared state, verification/replan, guardrails и auditable coordination; неподтверждённые hype-посты исключены.

# Multi-Agent AI Daily — 21 июля 2026

**Период мониторинга:** 14–21 июля 2026 (Europe/Samara). Проверены GitHub, свежие arXiv-препринты, Hugging Face, Reddit и X; в топ включены только материалы с прямой связью с multi-agent/tool-use/coordination, свежестью и практическим техническим вкладом.

## 1. Reward-Free Evolving Agents via Pairwise Validator

- **Источник:** arXiv, 15 июля 2026 — https://arxiv.org/abs/2607.14408v1
- **Краткое описание:** Авторы заменяют дорогостоящий скалярный reward в self-evolving agent loops на pairwise validator: замороженная LLM сравнивает родительскую и дочернюю версии агента и выбирает лучшую. Подход интегрирован в GEPA, ADRS и ShinkaEvolve; на большинстве проверенных конфигураций он сопоставим или превосходит reward-based baseline, уменьшая потребность в разметке и ручной калибровке reward.
- **Применение для AstroFinSentinelV5:** Использовать pairwise gate для сравнения версий промптов и политик Fundamental/Quant/Sentiment по audit-trailed backtest episodes. KARL сможет принимать изменение только после независимого сравнения PnL, drawdown, confidence calibration и качества объяснений, не полагаясь на один нестабильный reward.

## 2. pi v0.80.9: Kimi K3 и deferred tool loading

- **Источник:** GitHub — earendil-works/pi, релиз 16 июля 2026 — https://github.com/earendil-works/pi/releases/tag/v0.80.9
- **Краткое описание:** Релиз добавляет Kimi K3 для нескольких провайдеров и deferred tool loading: расширения активируют инструменты по требованию через нативный протокол, вместо загрузки всей библиотеки в каждый контекст. Это снижает контекстную нагрузку и улучшает масштабирование tool-heavy агентских workflow; проект имеет около 73,9 тыс. stars.
- **Применение для AstroFinSentinelV5:** Внедрить аналогичный dynamic tool registry для data_room и агентов: Router раскрывает только нужные market-data, RAG и backtest tools, а не весь каталог. Это может снизить prompt overhead и уменьшить ошибки выбора инструмента при параллельной работе Совета директоров.

## 3. Orchestrating Power Grid Studies with Multi-Agent AI and MCP Servers

- **Источник:** arXiv, 14 июля 2026 — https://arxiv.org/abs/2607.14158v1
- **Краткое описание:** Работа описывает практическое подключение LLM-агентов к численному симулятору через MCP-интерфейс pypowsybl-mcp: агенты настраивают симуляции, запускают анализы и получают результаты типизированными tool calls. Отдельно формализованы human-in-the-loop, аудитируемость и оценка workflow по техническим и пользовательским метрикам; препринт принят на IJCAI AISE 2026 workshop.
- **Применение для AstroFinSentinelV5:** Оформить рыночные резолверы, backtest и simulation actions как типизированные MCP-like tools поверх `data_room`, с политиками доступа и подтверждением рискованных действий. Каждое выполнение должно связываться с `DecisionRecord`, чтобы KARL мог воспроизводимо сопоставлять сигнал, фактические данные и результат симуляции.

## Дополнительный отбор

- Reddit/X подтвердили практический интерес к stateful orchestration, dynamic tool routing, guardrails и observability; generic hype и материалы без проверяемой технической детали исключены.
- `antoinezambelli/forge` отмечен как полезный reliability layer для tool-calling, но не включён в топ: последняя подтверждённая release-метка — 10 июля, за пределами окна мониторинга, а сам проект прямо не является multi-agent orchestrator.
- Узкие или не multi-agent-specific свежие arXiv-материалы исключены, даже если их методы потенциально применимы к агентным системам.

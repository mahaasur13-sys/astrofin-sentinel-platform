# Multi-Agent AI Daily — 22 июля 2026

**Период мониторинга:** 15–22 июля 2026 (Europe/Samara). Проверены GitHub, arXiv, Hugging Face, Reddit, Cursor/LangChain community и X. В топ включены только свежие материалы с практическим вкладом в multi-agent/tool-use/coordination; неподтверждённые или старые обсуждения исключены.

## 1. Codex CLI 0.145.0: стабильный Multi-Agent V2

- **Источник:** X / Codex Releases, 21 июля 2026 — https://x.com/CodexReleases/status/2079634417299918949
- **Краткое описание:** В Codex CLI Multi-Agent V2 объявлен стабильным: появились настраиваемые модели и уровни reasoning для sub-agents, управление concurrency, а также пагинированная история тредов с resume, поиском и persistent memories. Дополнительно расширен импорт настроек, MCP-серверов, плагинов, сессий и memories из Cursor и Claude Code; пост собрал 44,4 тыс. просмотров и 527 likes.
- **Применение для AstroFinSentinelV5:** Идеи configurable sub-agent policies и bounded concurrency напрямую применимы к пулу агентов AstroFin: задавать модель/глубину reasoning по роли и ограничивать параллелизм через broker. Persistent thread/session memory можно сопоставить с SQLite history и audit trail, сохраняя возобновляемость анализа без смешивания контекстов.

## 2. RELIC: интерпретируемые composable skills при приватной координации

- **Источник:** arXiv, 18 июля 2026 — https://arxiv.org/abs/2607.16745
- **Краткое описание:** RELIC позволяет агентам улучшать собственные programmatic skills через приватный LLM-guided search, а доверенному оркестратору оценивать обновления только по командному результату. Вместо передачи исполняемого кода между агентами распространяются переносимые принципы, которые можно инстанцировать в гетерогенных интерфейсах; работа принята на LM4Plan @ ICML 2026.
- **Применение для AstroFinSentinelV5:** Это подходящая модель для независимой эволюции Quant/Fundamental/Sentiment-агентов без утечки внутренних политик: KARL публикует только проверенные принципы и метрики, а не необработанные промпты. Пригодится для controlled skill promotion через backtest, calibration и DecisionRecord, сохраняя R-07/R-08 governance.

## 3. Agentic ERP: Planner–Executor–Reflector–Responder и risk-tiered HITL

- **Источник:** arXiv, 19 июля 2026 — https://arxiv.org/abs/2607.17331
- **Краткое описание:** Agentic ERP соединяет role-aligned LLM-агентов с graph-based orchestrator, внешними grading criteria/sprint contracts и risk-tiered human-in-the-loop harness. Авторы сравнивают шесть парадигм orchestration и проводят 365-дневную симуляцию; заявленная система избегает stockouts, тогда как rule-based baseline на том же потоке накапливает сотни.
- **Применение для AstroFinSentinelV5:** Разделение Planner–Executor–Reflector хорошо ложится на pipeline «агенты → KARL → исполнение»: рефлектор проверяет конфликт, риск и качество evidence до торгового action. Risk-tiered HITL можно связать с динамическим `risk_pct`: экстремальный regime требует подтверждения, а низкорисковые наблюдения проходят автоматически с полным аудитом.

## Что исключено

- OpenAI Agents Python v0.18.3 — релевантный релиз от 17 июля, но в основном tracing, memory/session fixes и документация; вклад в orchestration меньше, чем у выбранных трёх материалов.
- GitHub Agentic Workflows v0.82.13 — полезные firewall, audit metadata и rootless runner updates, но это скорее инфраструктурное обновление CI-agent workflows, а не новый multi-agent coordination primitive.
- Coware и похожие Cursor threads — технически интересны, но найденные публикации датированы апрелем 2026, то есть не проходят 7-дневный фильтр.

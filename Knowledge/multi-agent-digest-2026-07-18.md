# Multi-Agent AI Daily — 2026-07-18

Ежедневный дайджест по multi-agent инструментам, исследованиям и community-обсуждениям. Окно мониторинга: 11–18 июля 2026 года.

## 1. Microsoft Agent Framework: графовая оркестрация AutoGen + Semantic Kernel

- **Источник:** X / community report, 17.07.2026 — https://x.com/_vmlops/status/2078052398904332447
- **Краткое описание:** В community-обсуждении сообщается о production-ориентированном Agent Framework от Microsoft, объединяющем направления AutoGen и Semantic Kernel. Выделены графовые workflow (sequential, concurrent, handoff, group collaboration), checkpointing, streaming, human-in-the-loop, time-travel, OpenTelemetry, YAML-декларации агентов и DevUI для тестирования workflow до deployment. Это особенно важно как готовый набор primitives для наблюдаемой и воспроизводимой мультиагентной оркестрации.
- **Применение для AstroFinSentinelV5:** Паттерны checkpoint/time-travel можно сопоставить с `core/checkpoint.py` и audit trail в `agents/_impl/amre/audit.py`; OpenTelemetry — с трассировкой прохождения сигнала через MACRO, ASTRO, TECHNICAL и KARL-синтез. Handoff/group collaboration пригодятся для явной маршрутизации конфликтов между Fundamental, Quant и AstroCouncil вместо неявного усреднения.
- **Ограничение:** В дайджесте это отмечено как community report; официальную release page Microsoft за окно поиска отдельно подтвердить не удалось.

## 2. DeepStress — стресс-тестирование поисковых агентов на ненадёжных доказательствах

- **Источник:** arXiv 2607.13920v1, 15.07.2026 — https://arxiv.org/abs/2607.13920v1
- **Краткое описание:** DeepStress заменяет обычный retrieval-контур контролируемой синтетической средой и независимо варьирует trustworthiness, relevance и factuality входных документов. Эксперименты на HotpotQA и BrowseCompPlus показывают заметную разницу в устойчивости агентов к плохим или конфликтующим данным; авторы предлагают метрики, учитывающие взаимодействие parametric knowledge и retrieved evidence.
- **Применение для AstroFinSentinelV5:** Метод можно адаптировать для тестирования RAG-first контура Sentiment/Macro и KARL-синтеза: намеренно подмешивать устаревшие, нерелевантные или противоречивые новости и измерять, снижает ли система confidence и корректно ли фиксирует конфликт в `DecisionRecord`. Это даст воспроизводимый robustness benchmark до подключения реальных SEC, Binance и Polygon-источников.

## 3. GitHub Agentic Workflows v0.82.8 — изолированные runtime для агентных workflow

- **Источник:** GitHub Agentic Workflows, 11.07.2026 — https://github.github.com/gh-aw/blog/2026-07-13-weekly-update/
- **Краткое описание:** Релиз добавляет запуск агентов в gVisor и KVM-изолированном `docker-sbx`, улучшает credential refresh перед выполнением и позволяет переиспользуемым partials объявлять sandbox mounts. Практический вклад — усиление isolation boundary и снижение сбоев в workflow, которые выполняют инструменты или обрабатывают недоверенные входные данные.
- **Применение для AstroFinSentinelV5:** При вынесении data fetchers, RAG ingestion и backtest workers в отдельные agent processes можно использовать аналогичный принцип: sandbox для внешнего tool use, отдельные mounts для datasets и явный refresh credentials перед запуском. Это снижает риск компрометации торгового контура через небезопасный MCP/data connector и хорошо сочетается с R-01/R-02 и auditability.

---

*Отфильтровано по релевантности к multi-agent/tool-use, новизне за последние 7 дней и практической технической значимости.*

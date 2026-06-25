# 🤖 Multi-Agent AI Daily — 2026-06-25

**Окно мониторинга:** 18–25 июня 2026 (последние 7 дней)
**Критерий отбора:** technical contribution → ценность для AstroFinSentinelV5 → community response

---

## 🥇 1. Sakana Fugu / Fugu Ultra — мультиагентная оркестрация как foundation model

- **Источник:** GitHub (technical report arXiv 2606.21228) + X/Twitter + VentureBeat + DataCamp + MarkTechPost
- **Дата релиза:** 22 июня 2026 (general availability)
- **Краткое описание:** Tokyo-based Sakana AI выпустил Fugu и Fugu Ultra — первую коммерческую систему, в которой мультиагентная оркестрация сама по себе является foundation model. Снаружи это один OpenAI-совместимый endpoint; внутри — обученный 7B Conductor + лёгкий 0.6B TRINITY-координатор (эволюционировал CMA-ES), которые динамически распределяют роли Thinker/Worker/Verifier между пулом подключаемых frontier-моделей и сами вызывают себя рекурсивно. Архитектура построена на двух ICLR 2026 paper'ах Sakana — TRINITY (role assignment) и Conductor (RL-обученный координатор коммуникационных паттернов). По собственным бенчмаркам: SWE-Bench Pro 73.7% (выше Claude Opus 4.8 69.2%, GPT-5.5 58.6%, Gemini 3.1 Pro 54.2%), LiveCodeBench 93.2, GPQA-D 95.5. Позиционируется как hedge против export controls (после 12 июня 2026 Anthropic закрыл Fable 5 и Mythos Preview). Доступ через Sakana Console и OpenRouter, подписки $20/$100/$200 в месяц. Недоступен в EU/EEA из-за GDPR.
- **Применение для AstroFinSentinelV5:** Прямой прообраз «learned orchestrator» паттерна, который можно адаптировать в `orchestration/sentinel_v5.py`. Текущая иерархия Planner → Executor → Verifier сейчас жёстко прописана в коде, но реальный контекст (новости vs backtest vs astro) требует динамического выбора — Fugu показывает, что эту логику можно выучить, а не писать руками. Конкретный прикладной шаг: посмотреть TRINITY/Conductor papers как reference для будущего перехода AstroCouncil на RL-trained routing вместо фиксированных весов `HYBRID_WEIGHTS`.

**Источники:**
- VentureBeat: https://venturebeat.com/orchestration/no-claude-fable-5-no-problem-sakana-achieves-frontier-performance-with-new-fugu-multi-model-auto-synthesis-system
- MarkTechPost: https://www.marktechpost.com/2026/06/22/sakana-ai-launches-sakana-fugu-an-orchestration-model-that-routes-tasks-across-a-swappable-pool-of-frontier-llms
- DataCamp: https://www.datacamp.com/blog/sakana-fugu
- arXiv technical report: https://arxiv.org/html/2606.21228v1
- X/Twitter @stretchcloud: https://x.com/stretchcloud/status/2069021330205495346

---

## 🥈 2. SelfCompact — когда агент сам решает, когда «забывать»

- **Источник:** arXiv 2606.23525 + Hugging Face Daily Papers + тематический блог-пост
- **Дата:** 24–25 июня 2026 (широко обсуждается в community)
- **Краткое описание:** SelfCompact — это inference-time scaffolding для long-horizon агентских traces, который передаёт модели решение о том, когда компактировать собственный контекст. Состоит из двух компонентов: (i) «compaction tool», который модель сама вызывает, чтобы суммаризовать накопленный контекст; (ii) лёгкая rubric, указывающая когда сжимать (подзадача решена, траектория сходится) и когда подавлять (в середине derivation или при застревании). Результат: на 6 бенчмарках с 7 моделями SelfCompact равен или превосходит fixed-interval суммаризацию при 30–70% снижении per-question token cost, и обходит no-summarization baseline на +18.1 п.п. по math и +5–9 п.п. по agentic search. Главный инсайт — модели без подсказки не умеют распознавать собственный context rot, но лёгкий rubric закрывает этот meta-cognitive gap без fine-tuning.
- **Применение для AstroFinSentinelV5:** Прямая замена текущего жёсткого token-threshold-based summarization в sentiment pipeline и trade-decision workflow. Сейчас при длинных traces `core/ephemeris.py` + MacroAgent + SentimentAgent быстро упираются в лимит окна, и compaction срабатывает в неподходящий момент (например, прямо во время Bradley seasonality calc — самом дорогом для восстановления шаге). SelfCompact rubric можно вшить в SynthesisAgent как pre-call hook и дать модели решать, сжимать ли trace после каждого sub-agent ответа. Это даст +18% эффективности без дополнительного обучения.

**Источники:**
- arXiv: https://arxiv.org/abs/2606.23525
- Hugging Face Daily Papers: https://huggingface.co/papers?q=compaction+tool
- Блог-разбор: https://blakecrosley.com/blog/agent-context-compaction

---

## 🥉 3. Block BuilderBot — Slack-native orchestration для many agents на одном canvas

- **Источник:** GitHub (block/goose) + SD Times + новости Anthropic MCP ecosystem
- **Дата:** 23–24 июня 2026 (публичный release от Block)
- **Краткое описание:** Block — авторы goose AI agent framework и co-developer MCP вместе с Anthropic — выпустили BuilderBot, оркестрационный слой для управления множеством агентов прямо в Slack. BuilderBot живёт в thread'е, читает описание задачи от пользователя и сам собирает нужный subgraph агентов (bug fix, new feature, refactor) без ручного wiring. Ключевая особенность — это первый production-инструмент, который эксплуатирует MCP-протокол как шину между агентами: каждый sub-agent экспонирует свои инструменты через MCP, а BuilderBot координирует их по графу зависимостей, оставаясь в одном execution canvas. Интегрируется с Block's существующей инфраструктурой кода и OpenTelemetry трейсингом.
- **Применение для AstroFinSentinelV5:** Архитектурный референс для перехода от hand-wired LangGraph к graph-driven runtime. Сейчас в `orchestration/sentinel_v5.py` каждый новый тип задачи (SWING vs INTRADAY vs SCALP) требует ручного добавления branch в графе. BuilderBot-паттерн «subgraph auto-assembly из user description» позволяет твоему оркестратору генерировать нужный набор агентов (Fundamental+Quant для SWING, только Technical+Sentiment для SCALP) на лету, без правки кода. Плюс MCP-as-bus подтверждает, что инвестиция в MCP-интеграцию окупится — стоит подумать обернуть свои data-agents (Polygon, CoinGecko, SEC EDGAR) в MCP-серверы для унификации.

**Источники:**
- SD Times: https://sdtimes.com/ai/block-introduces-builderbot-an-ai-agent-orchestration-layer
- Block/goose GitHub: https://github.com/block/goose

---

## 📊 Дополнительные сигналы (вне топ-3, но值得关注)

- **Agentic Time Machine (arXiv 2606.21013)** — evaluation-инфраструктура для мультиагентного прогнозирования будущих событий. Planner-solver-aggregator пайплайн топ-1 на FutureX live leaderboard за 8 недель. Полезно для stress-теста AstroFinSentinelV5 на forward-looking сценариях.
- **AOHP (arXiv 2606.23449)** — open-source OS-level harness для агентов на AOSP. +21.12% task completion, −51.55% token cost. Интересно как системный baseline для будущего on-device trading assistant.
- **Block BuilderBot + MCP ecosystem** — подтверждает MCP как emerging standard. Стоит в перспективе обернуть data-инструменты AstroFinSentinelV5 в MCP-серверы.
- **Hugging Face × Qualcomm partnership** — hybrid agentic orchestration между device и data center. Долгосрочно релевантно для mobile-интерфейса торговых алертов.

---

*Сгенерировано автоматически ежедневным агентом multi-agent-digest. Источники: arXiv, OpenReview, GitHub, X/Twitter, Reddit, SD Times, VentureBeat, MarkTechPost, DataCamp.*
# 🤖 Multi-Agent AI Daily — 2026-06-10

Ежедневный дайджест новостей из мира multi-agent AI-инструментов, фреймворков и исследований. Отобрано 3 самых значимых события за последние 7 дней по приоритетам: технический вклад > ценность для AstroFinSentinelV5 > community response.

---

## 1. Microsoft Agent Framework 1.8.0 — McpSkills, MCP long-running tasks (SEP-2663) и compaction stability

- **Источник:** GitHub — `microsoft/agent-framework` (Python 1.8.0, .NET 1.8.x)
- **Ссылка:** https://github.com/microsoft/agent-framework/releases/tag/python-1.8.0
- **Дата релиза:** 2026-06-04

**Краткое описание:** Крупный релиз вендорского multi-agent SDK сразу после BUILD 2026. В `agent-framework-core` добавлены **McpSkills** (загрузка навыков с MCP-сервера в формате `skill-md`/`mcp-resource-template`/`archive`) и экспериментальный async-resource lookup. Реализован **MCP long-running task support (SEP-2663)**: тулзы с `execution.taskSupport == "required"` прозрачно оборачиваются в `tools/call → tasks/get (polling) → tasks/result`, что важно для долгих агентных операций (анализ, backtest). PR #6299 починил **collision в auto-assigned message_id** и сделал compaction in-place, чтобы саммари не терялись между итерациями tool-loop. GitHub Copilot SDK поднят до стабильного v1.0.0.

**Применение для AstroFinSentinelV5:** McpSkills — это та самая переиспользуемая «библиотека навыков», которой не хватает для подключения внешних market data-провайдеров (Polygon, Unusual Whales, SEC EDGAR) как plug-in скиллов вместо хардкода. Long-running MCP-таски — прямой путь к «утреннему отчёту», который может идти 5–10 минут без таймаутов. In-place compaction критичен для KARL-backtest loop, где промежуточные summary часто терялись при перезаходе в tool-loop.

---

## 2. POISE — автономное открытие новых LLM-RL алгоритмов агентами-учёными

- **Источник:** arXiv / OpenReview (research paper, ACL ARR 2026)
- **Ссылка:** https://openreview.net/forum?id=EPWdJDKSXx
- **Дата:** июнь 2026

**Краткое описание:** Фреймворк, в котором LLM-агенты ведут **замкнутый цикл научного поиска** новых алгоритмов policy optimization: генеалогически связанный архив proposals → implementations → evaluations → reflections, переходящий от GRPO. Исследовано 64 кандидата; лучший вариант поднял weighted Overall с **47.8 → 52.5** (+4.6) и **AIME25 pass@32 с 26.7% до 43.3%** благодаря новым механизмам analytic-variance scaling и validity masking. Это первый убедительный результат, показывающий, что LLM-агентный loop может делать reproducible contributions в дизайне RL-алгоритмов.

**Применение для AstroFinSentinelV5:** Идея «агент-учёный» применима к твоему AMRE/KARL-циклу: можно завести отдельного `ResearchAgent`, который будет итерировать гипотезы о сигналах (предсказание drawdown, оптимальный Kelly multiplier) и оставлять в архиве только подтверждённые бэктестом варианты. Это превращает `oap_optimizer.py` + `backtest_loop.py` из ручной оптимизации в **agentic research loop** — ближе к AutoML, но с LLM в роли «руководителя лаборатории».

---

## 3. dySCo / Pi-Taskflow / Open-Multi-Agent — typed DAG и sparse-координация для verifiable мульти-агентов

- **Источник:** GitHub — `heggria/pi-taskflow` (v0.0.19, 10 июня), `open-multi-agent/open-multi-agent`, dySCo
- **Ссылки:** https://github.com/heggria/pi-taskflow, https://github.com/open-multi-agent/open-multi-agent
- **Дата:** 2026-06-03 — 2026-06-10

**Краткое описание:** Волна typed-DAG и verifiable-orchestration фреймворков: **pi-taskflow** (zero-dep, verifiable TS DAG с retries, joins, approvals, atomic writes; v0.0.19 от 10 июня); **open-multi-agent** (TypeScript-native, fix для memoryScope + retry config на plan-replay #287); **dySCo** (Dynamic Sparse Consensus — снижение O(N²) overhead в multi-agent debate до near-linear через budget-constrained edge selection). Общая идея: вместо «свободной дискуссии» агентов — формальный граф, который можно проверить до запуска и безопасно реплеить.

**Применение для AstroFinSentinelV5:** Verifiable typed-DAG — недостающая часть пайплайна: сейчас твои агенты скорее договариваются «на словах». Переход на формальный DAG (как у pi-taskflow) даст: (1) пред-execution проверку корректности цепочки Fundamental → Macro → Quant → Risk; (2) cross-session resume после сбоя; (3) replay plan-only snapshot с сохранением memoryScope. dySCo-идея sparse-coordination снизит стоимость ежедневного council-вызова — вместо 13 агентов одновременно активировать 4–5 в зависимости от market regime.

---

## Прочие заметные релизы (для контекста)

- **Cornucopia-Multi-Agent** — production-grade Python multi-agent framework с 6 режимами коллаборации, 6 топологиями, 8 built-in tools и WebSocket-стримингом.
- **agentic-mcp-gateway v0.2.0-beta** (06.06) — LangGraph-routing, multi-LLM, OpenTelemetry tracing.
- **TeamOlimpo** — Kubernetes-based meta-orchestrator, MCP-native, с mandatory handoff protocol и quality gates.
- **a2a-gateway-mcp v0.4.0** (05.06) — per-agent rate limiting через token bucket для A2A ↔ MCP моста.
- **LGRA (LLM-Guided Role Assignment in MARL)** — LLM-«учитель» назначает роли и выдаёт rationales, повышает SOTA в 13 из 14 MARL-задач.
- **Scaling Behavior of Single LLM-Driven MAS** — показывает, что добавление агентов не улучшает результат монотонно; есть sweet spot по типу задачи.
- **POISE / ReSkill / OpenSkill / GRAIL / ForgeTrain** — кластер работ 2026 года по автономному skill/policy discovery в LLM-RL.

---

*Источники: GitHub releases (microsoft/agent-framework, heggria/pi-taskflow, open-multi-agent, agentic-mcp-gateway, sinhphamvj), OpenReview (POISE, MMAD, R-HAN), arXiv, X/Twitter. Период: 2026-06-03 — 2026-06-10.*

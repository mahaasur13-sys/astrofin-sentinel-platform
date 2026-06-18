# Multi-Agent AI Daily — 2026-06-16

Ежедневный дайджест по multi-agent инструментам, исследованиям и community-обсуждениям. Окно: последние 7 дней.

---

## 1. OrchRM — self-supervised reward modeling для оркестратора multi-agent LLM-систем

- **Источник:** arXiv (2606.13598v1), Stanford / исследовательская работа
- **Описание:** OrchRM предлагает обучать reward model для оркестратора мульти-агентной системы без человеческой разметки и без дорогих sub-agent rollouts. Используя промежуточные артефакты multi-agent исполнения, фреймворк строит win-lose пары и тренирует Bradley-Terry reward model на уровне оркестрации. Метод даёт до 10× снижения расхода токенов при обучении и до +8% прироста точности на test-time scaling. Протестировано на math reasoning, web QA, multi-hop reasoning.
- **Применение для AstroFinSentinelV5:** Ключевая боль системы — SynthesisAgent (100%) координирует голоса 13 агентов. OrchRM даёт путь к обучению самого SynthesisAgent на исторических DecisionRecord'ах (уже пишутся в `agents/_impl/amre/audit.py`): можно тренировать reward model на win-lose парах по реальным исходам и автоматически калибровать `HYBRID_WEIGHTS` без ручного тюнинга весов.

---

## 2. ECC 2.0 — Agent Harness Operating System с cross-harness оркестрацией

- **Источник:** GitHub (affaan-m/ECC, v2.0.0), 12+ тыс. звёзд, release 13.06.2026
- **Описание:** ECC 2.0 объединяет Claude Code, Codex, OpenCode, Cursor, Gemini CLI и Zed под единой операционной поверхностью. Архитектура включает control-pane (work-items board, operator recall), harness-neutral session adapters (`ecc.session.v1`), MCP inventory с drift detection и secret redaction, worktree-lifecycle service для параллельных агентов, и orchestrator skill family `orch-*` для fan-out workflows. Включает 261 публичный skill, 64 агента и 84 команды. Позиционируется как Agent Harness Operating System с явным governance-слоем.
- **Применение для AstroFinSentinelV5:** Решает инфраструктурные задачи вокруг оркестратора: (1) `orch-*` skill family — переиспользуемый паттерн для fan-out вызовов сразу нескольких `_impl/*` агентов; (2) MCP inventory с drift detection — пригодится при подключении внешних data sources (CoinGecko, Binance, SEC EDGAR); (3) worktree-lifecycle — подходит для параллельного backtest-оптимизатора по разным активам. Особенно ценно, если в будущем AstroFinSentinelV5 будет использовать разные LLM-клиенты (Claude Code + локальный Ollama через aivyx-llm).

---

## 3. Swarms v13 "Kizuna 絆" — async GroupChats и streaming workflows для production multi-agent

- **Источник:** X/Twitter (swarms_corp, 12.06.2026) + GitHub (Kye Gomez / swarms)
- **Описание:** Релиз Kizuna принёс async self-selecting GroupChats, end-to-end streaming workflows, deterministic RoundRobinSwarm, улучшенный AgentRearrange и серьёзные апгрейды observability/логирования. Python-фреймворк Swarms — старейший из multi-agent фреймворков (>3 лет, 5000+ коммитов, ~7000 звёзд, 60+ harnesses) — продолжает наращивать production-готовность. Параллельно Hermes Agent (Nous Research, 190K звёзд) выпустил Hermes Desktop — нативный GUI, выводящий multi-agent из терминала на десктоп.
- **Применение для AstroFinSentinelV5:** Production-grade reference для scaling AstroCouncil: паттерн async self-selecting GroupChats подходит для случая, когда Bradley/Gann/Cycle/Electoral агенты сами решают, кто из них релевантен текущему таймфрейму. Streaming workflows полезны для дашборда (8050) — можно стримить промежуточные сигналы от каждого `_impl/*` агента в UI, не дожидаясь полного SynthesisAgent. Архитектурно подтверждает выбор в сторону LangGraph (который уже в V5) — Swarms развивает похожие примитивы.

---

*Сгенерировано автоматически утренним агентом. Источники: arXiv, GitHub, Reddit r/AI_Agents, X/Twitter #multiagent.*

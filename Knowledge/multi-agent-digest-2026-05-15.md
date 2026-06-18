# Multi-Agent AI Daily Digest — 2026-05-15

## Источники
- GitHub (multi-agent frameworks, 7 дней)
- arXiv (multi-agent LLM systems, 7 дней)
- X/Twitter (#multiagent, #AIagents, #agentframework)
- Reddit, Hugging Face Discussions

---

## Топ-3 за сегодня

---

**1. Microsoft Agent Framework (MAF) — dotnet-1.5.0**
- **Источник:** GitHub — microsoft/agent-framework
- **Краткое описание:** Обновление MAF (08.05.2026) приносит graph-based orchestration с поддержкой handoff, group collaboration, checkpointing, streaming и human-in-the-loop. Фреймворк работает на Python и .NET, интегрируется с Azure OpenAI, OpenAI, Foundry, Copilot SDK. Акцент на durability, restartability и governance делает его одним из самых зрелых enterprise-ready решений.
- **Применение для AstroFinSentinelV5:** Архитектура handoff-оркестрации MAF — отличный референс для реализации передачи задач между специализированными агентами (аналитик, риск-менеджер, торговый движок). Human-in-the-loop механизм пригодится для согласования сделок выше порога риска.

---

**2. REDEREF — Training-Free Agent Coordination Controller**
- **Источник:** arXiv — 2603.13256
- **Краткое описание:** REDEREF предлагает lightweight контроллер для координации multi-agent LLM без дообучения. Использует belief-guided delegation с Thompson sampling и reflection-driven re-routing для адаптивной маршрутизации. Демонстрирует снижение token usage на 28%, agent calls на 17%, time-to-success на 19% по сравнению с random recursive delegation.
- **Применение для AstroFinSentinelV5:** Механизм Thompson sampling для делегирования задач можно напрямую применить к выбору между агентами мониторинга, анализа и исполнения сделок. Снижение token usage критично для cost-efficient работы в реальном времени.

---

**3. Orloj — Declarative Multi-Agent Orchestration Framework**
- **Источник:** GitHub — OrlojHQ/orloj
- **Краткое описание:** Orloj — full-stack orchestration фреймворк с declarative YAML-манифестами для агентов, инструментов, моделей, памяти и политик. Включает runtime governance, scheduling с lease-based workers, трассировку, метрики и MCP/WASM/CLI интеграции. Создан для production-grade систем 2026+.
- **Применение для AstroFinSentinelV5:** Декларативный подход Orloj (агенты как YAML) упрощает конфигурацию мультиагентной системы. Политики runtime governance пригодятся для контроля доступа агентов к рыночным данным и торговым операциям.

---

*Дата формирования: 2026-05-15 08:05 (UTC)*

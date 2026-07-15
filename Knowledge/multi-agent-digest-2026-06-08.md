# Multi-Agent AI Daily — 2026-06-08

Период: последние 7 дней (2026-06-01 — 2026-06-08)
Источники: GitHub (категория), arXiv / OpenReview, X (Twitter), Microsoft DevBlog / Visual Studio Magazine

---

## 1. Microsoft Agent Framework — Handoff pattern + Foundry Hosted Agents (BUILD 2026)

- **Источник**: Microsoft DevBlog / GitHub (microsoft/agent-framework)
- **Ссылки**:
  - https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce
  - https://github.com/microsoft/agent-framework/issues/6240
  - https://github.com/microsoft/agent-framework/pull/6316

**Краткое описание:**
Microsoft на конференции BUILD 2026 (2-4 июня) объявил production-зрелость Microsoft Agent Framework. Ключевые новинки:
- **Handoff pattern** — first-class паттерн multi-agent оркестрации: агенты передают управление друг другу по явным правилам, без неявного «потопа» сообщений. Поддержан и в Python, и в .NET (обновлён HandoffWorkflowBuilder, +313 строк).
- **Foundry Hosted Agents** — контейнеризированные агенты, выполняемые в Microsoft-managed инфраструктуре с per-session sandbox, scale-to-zero, Entra-идентичностью и versioned deployments с traffic splitting.
- **Agent Harness** — production-паттерны «из коробки» (observability, recovery, retries, cost guardrails).
- **CodeAct** — агенты с кодовой action-логикой, которые делают меньше обращений к модели за счёт исполнения Python.
- **A2A-протокол** — реорганизованы samples: `a2a_server.py` (host A2A server, multi-agent), `agent_framework_to_a2a.py` (expose single agent as A2A server), `agent_with_a2a.py` (connect to A2A server). Это путь к интероперабельности между разными фреймворками.
- **Workflow-level OpenTelemetry** для HandoffWorkflowBuilder (issue #6320) — телеметрия routing-сигналов между агентами.
- Решена проблема Handoff-output semantics (issue #6240) — ранее каждый output участника пробрасывался вниз по цепочке и ломал Magentic/Concurrent; теперь есть `output_from` / `intermediate_output_from` для явного выбора.

**Применение для AstroFinSentinelV5:**
- Handoff-паттерн — отличный blueprint для роутинга задач между твоими агентами (например, `DataFetcher` → `Analyst` → `RiskManager` → `Executor`). Вместо «общего чата» — явный контракт передачи управления с понятным ownership-ом каждого шага.
- Foundry Hosted Agents — ориентир для production-деплоя: per-session sandbox полезен, если разные рыночные сессии (Asia/London/NY) должны быть изолированы; scale-to-zero экономит бюджет в нерабочие часы.
- A2A-протокол — возможность подключать внешние готовые агенты (например, специализированный backtester или risk-engine от третьих сторон) как полноценных участников твоей оркестрации.

---

## 2. Cloudflare Agents 0.14.0 — durable multi-agent orchestration + Skills engine

- **Источник**: GitHub (cloudflare/agents)
- **Ссылка**: https://github.com/cloudflare/agents/releases/tag/agents@0.14.0

**Краткое описание:**
Крупный релиз multi-agent фреймворка от Cloudflare (3 июня 2026). Главные фичи:
- **Framework-agnostic Skills engine** (`agents/skills`): SkillRegistry, skill sources, tools to activate/read/run skills. Skills можно импортировать через Vite-plugin (`agents:skills` specifier). Это превращает переиспользуемые «куски поведения» в первоклассный артефакт, разделяемый между агентами.
- **Durable think/workflow** — `ThinkWorkflow` с `step.prompt()` для workflow-driven thinking. Шаги переживают падения, при перезапуске не нужно прогонять заново.
- **Recoverable sub-agents** — при восстановлении родителя сабагенты re-attach к всё ещё работающим, а не стартуют с нуля. Это принципиально для долгих операций.
- **Unified progress tracking** — прогресс сабагента учитывается в progress родителя (а не как «0% началось»).
- **Backward-compatible client payloads** — `status` и `retryable` поля автоматически подхватываются на клиенте.
- **Inactivity watchdog** для streaming — раньше зависший read-стрим мог висеть вечно, теперь выкидывает terminal error.
- Bounded internal framework + startup/recovery safeguards против infinite loops.

**Применение для AstroFinSentinelV5:**
- **Skills engine** — концептуально то, что нужно: реестр capabilities, которые можно подключать к разным агентам по контексту. Например, skill `fetch_yahoo_finance` нужен и DataFetcher-у, и RiskManager-у — сейчас у тебя, скорее всего, это дублируется.
- **Recoverable sub-agents** — критически важно для долгих сессий рыночного мониторинга: если контейнер перезапустился посреди 4-часового бэктеста, сабагент продолжит с того же шага, а не начнёт заново и не потеряет уже вычисленные сигналы.
- **ThinkWorkflow с durable step.prompt()** — паттерн «план с шагами, которые можно перепрогнать» подходит для многоэтапного trade-decision pipeline: каждый шаг — отдельный durable task.

---

## 3. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems (ACL ARR 2026)

- **Источник**: OpenReview / arXiv (research paper)
- **Ссылка**: https://openreview.net/forum?id=wmucOCOBPq

**Краткое описание:**
Академическая работа, предлагающая архитектуру для LLM-based multi-agent систем, которая решает две известные проблемы: (1) одна топология ограничивает разнообразие рассуждений, (2) наивное объединение топологий порождает «шум» через рёбра, которые в данный момент нерелевантны.

Ключевые идеи:
- **Union MAS graph**: с помощью Monte Carlo Tree Search (MCTS) и Determinantal Point Process (DPP) выбирается набор разнообразных кандидатных топологий и объединяется в один граф. DPP обеспечивает, чтобы выбранные топологии были непохожи друг на друга, а не дублировали одну и ту же перспективу.
- **Hierarchical Sparse Coordination**: на каждом шаге активируется только sparse-подграф (а не весь union graph). Агенты обмениваются не сырыми сообщениями, а **compressed latent briefs** — это резко снижает noise propagation по нерелевантным связям.
- **Local Self-Refinement**: решение переписывается только если есть **discrepancy evidence** (несогласие с challenger-ом) **И** challenger-side improvement (предложенный вариант реально лучше по надёжному сигналу). Это двойной gate против «колебания» и capitulation.

**Результаты:**
- 8 бенчмарков, SOTA в среднем: **+2.98%** над сильнейшим baseline.
- На MMLU-Pro — **до +10.27%**.
- Больший выигрыш на более сложных задачах при разумном overhead-е.

**Применение для AstroFinSentinelV5:**
- **Sparse coordination + compressed briefs** — прямой способ снизить «шум» в твоём multi-agent пайплайне и одновременно сократить расход токенов на согласование. Сейчас, если у тебя 5 аналитических агентов «обсуждают» рынок, они шлют друг другу полные рассуждения; сжатые briefs заменят это на короткие summary-фразы, а sparse activation ограничит, какие агенты вообще участвуют в обсуждении.
- **DPP-отбор стратегий** — DPP — это инструмент для выбора разнообразного подмножества. Можно адаптировать для отбора подмножества **торговых стратегий-агентов**, активных в текущем режиме рынка: DPP подберёт такие стратегии, чтобы они были «ортогональны» по риску и не дублировали одну и ту же экспозицию.
- **Local Self-Refinement** — двухступенчатый gate перед пересмотром решения можно применить к финальному trade-decision агенту: он не отменяет сигнал, пока не получит и discrepancy, и подтверждённое improvement.

---

## Сводка по применению в AstroFinSentinelV5

| # | Что взять | Где применить |
|---|-----------|----------------|
| 1 | Handoff pattern + A2A | Архитектура роутинга задач между агентами; интеграция внешних агентов |
| 1 | Foundry Hosted Agents model | Per-session sandbox для разных торговых сессий |
| 2 | Skills engine | Реестр переиспользуемых capabilities (fetch, parse, score) |
| 2 | Recoverable sub-agents | Устойчивость долгих сессий мониторинга и бэктестов |
| 2 | ThinkWorkflow | Многоэтапный decision pipeline с durable steps |
| 3 | Sparse coordination + compressed briefs | Снижение шума и стоимости согласования между агентами |
| 3 | DPP-отбор | Выбор разнообразного подмножества активных стратегий-агентов |
| 3 | Local Self-Refinement | Gate перед отменой сигнала в trade-decision |

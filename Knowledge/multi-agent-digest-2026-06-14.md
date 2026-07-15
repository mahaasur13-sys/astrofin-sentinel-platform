# 🤖 Multi-Agent AI Daily — 2026-06-14

Утренний дайджест по multi-agent AI инструментам, фреймворкам и исследованиям за последние 7 дней.

---

## 1. ECC 2.0.0 — The Agent Harness Operating System

- **Источник:** GitHub — `affaan-m/ECC` (релиз v2.0.0)
- **Краткое описание:** Кросс-харнесс ОС для агентной работы: единые session adapters (`ecc.session.v1`) для Claude Code, Codex, OpenCode, Cursor, Gemini, Zed и terminal workflows. Включает 261 публичный skill, 64 агента, 84 команды, orch-* семейство для dynamic workflow team orchestration и multi-agent fan-out как first-class surface. Worktree-lifecycle service решает merge-conflict prediction и parallel worktree GC. MCP-инвентарь с drift detection и secret redaction (поймал реальную утечку ключа во время разработки).
- **Применение для AstroFinSentinelV5:** Идея harness-neutral session adapters сразу снимает вендор-лок в AFSV5 — можно держать Claude Code / Codex / OpenCode как взаимозаменяемые backends без переписывания оркестратора. Orch-* skill family даёт готовый паттерн fan-out для финансовых пайплайнов (новости → сентимент → риск-оценка → алерт). Worktree-lifecycle пригодится, когда несколько агентов параллельно меняют конфиги/скрипты.

## 2. MARS — Multi-Agent Review System (эффективный multi-agent debate)

- **Источник:** arXiv/OpenReview — `rG0PKKeYfI`
- **Краткое описание:** Переосмысляет Multi-Agent Debate (MAD) через role-based review: author agent предлагает решение, независимые reviewer agents дают решения и комментарии, meta-reviewer синтезирует фидбек. Показывает accuracy на уровне MAD при ~50% снижении token usage. Прямой ответ на главную боль MAD — дороговизну inter-reviewer общения.
- **Применение для AstroFinSentinelV5:** В AFSV5 есть debate-паттерн между аналитическими агентами (бычий/медвежий/нейтральный сценарии). MARS можно использовать как drop-in замену классического debate: тот же уровень качества выводов, но в 2 раза меньше расход токенов на дорогих reasoning-моделях. Особенно актуально для ежедневных утренних прогонов и high-frequency сигналов.

## 3. MASFactory — multi-agent workflow из natural language

- **Источник:** GitHub + X (BUPT-GAMMA, Apache-2.0). Обсуждение: @DanKornas
- **Краткое описание:** Python-фреймворк, который переворачивает порядок создания multi-agent workflow: сначала intent на естественном языке → сгенерированный граф → executable workflow. Поддерживает Node/Edge контракты, subgraphs, loops, switches, Human nodes, ContextBlock протокол для Memory/RAG/MCP контекста. В комплекте Python-пакет и VS Code Visualizer с runtime tracing и HITL-сессиями.
- **Применение для AstroFinSentinelV5:** Low-code подход к описанию новых финансовых пайплайнов: можно описывать intent ("оценить риск портфеля по макро-новостям + позициям") и получать готовый граф с правильными узлами. ContextBlock протокол — хороший шаблон для унификации передачи состояния портфеля, макро-индикаторов и исторических решений между агентами. Visualizer упрощает дебаг долгих multi-step workflows.

---

## Дополнительные находки (для контекста, не вошли в топ-3)

- **AgentOS** (`thinhkhuat/agent-os`) — TypeScript фреймворк с runtime tool forging (агенты создают TS-функции через Zod, проходят LLM-judge, исполняются в node:vm sandbox) и 6 стратегиями координации. Сильная memory-подсистема, 11 LLM-провайдеров через единый интерфейс.
- **HiveMind** (`ziyu111777/HiveMind`) — Python-first runtime layer поверх LangGraph/AutoGen/CrewAI с Run/Step/Message/ToolCall/Checkpoint в Postgres и SSE-streaming событий. Подходит как observability-обёртка над разными оркестраторами.
- **AgentFlow4J** (`abchavan/agentflow4j`) — Java-фреймворк с Squad/Graph API, governance (ApprovalGate, BudgetPolicy, ToolPolicy), checkpoint/resume, Micrometer. Для Java/Spring стеков.
- **Munder-Difflin** (`pdurlej/munder-difflin`) — локальный multi-agent harness для Claude Code с GOD-оркестратором, hive memory, atomic mailboxes, single-committer git backend, SQLite durability.
- **MMAD: Multi-Agent Mutual Awareness Debate** (arXiv) — двух-уровневый Theory-of-Mind фреймворк, устраняет sycophantic drift у small LMs (+73.3 pp на GSM8K). Учит агентов рассуждать о peer-выводах до обновления позиции.
- **Scaling Behavior of Single LLM-Driven MAS (SIMAS)** (arXiv) — scaling laws: добавление агентов даёт diminishing returns; тип задачи сильно влияет на оптимальное число агентов.
- **TRUST-SQL: Tool-Integrated Multi-Turn RL** (arXiv) — Dual-Track GRPO для text-to-SQL в unknown-schema, +9.9% над стандартным GRPO. Полезно для data-aware агентов.
- **LangGraph security advisory (The Hacker News, 09.06.2026)** — CVE-2026-28277 (unsafe msgpack deserialization, CVSS 6.8) + SQL injection + RCE chain в self-hosted LangGraph. Патч выпущен; LangSmith-hosted deployments не затронуты. Если AFSV5 использует self-hosted LangGraph — обязательно обновиться.

---

_Сгенерировано автоматически. Файл-архив утреннего дайджеста._

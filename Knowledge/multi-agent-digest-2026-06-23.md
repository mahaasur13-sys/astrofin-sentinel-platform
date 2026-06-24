# 🤖 Multi-Agent AI Daily — 2026-06-23

**Период:** 16–23 июня 2026
**Источники:** GitHub (10+ репозиториев), arXiv/OpenReview (5+ препринтов), X/Reddit (community обсуждения)

---

## 1. Foundry: Host-Owned Trust and Memory for Long-Horizon Agent Swarms

- **Источник:** arXiv/OpenReview — [MWLIRDa4DC](https://openreview.net/forum?id=MWLIRDa4DC)
- **Краткое описание:** Foundry предлагает архитектуру с разделением «ненадёжное предложение» (агент) и «доверенная верификация + персистентная память» (host). Центральный host-evaluator проверяет гипотезы агентов и сохраняет доказанные факты в shared registry, предотвращая reward-hacking и повторное «переоткрытие» уже опровергнутых идей. Эмпирически подтверждено на комбинаторной математике (улучшение Erdos-границ), оптимизации GPU-ядер на H100 и биоинформатике (single-cell denoising benchmark).
- **Применение для AstroFinSentinelV5:** Архитектурный паттерн «host-owned evaluator + established-facts registry» критически важен для финансового агента — можно выделить «финансовый sandbox-host», который валидирует торговые гипотезы агентов-исследователей и блокирует исполнение непроверенных стратегий, отсекая повторное тестирование уже опровергнутых сигналов. Это даёт AstroFin тот же protection от «reward hacking», что Foundry показывает в науке.

---

## 2. CAID: Centralized Asynchronous Isolated Delegation для SWE-агентов

- **Источник:** arXiv/OpenReview (CMU, Graham Neubig) — [zayaq7ssvH](https://openreview.net/forum?id=zayaq7ssvH)
- **Краткое описание:** CAID — фреймворк для координации нескольких агентов на длинных SWE-задачах через три примитива: централизованная делегация задач, асинхронное выполнение и изолированные workspace. Центральный manager строит план с учётом зависимостей, подзадачи исполняются в изолированных окружениях, а интеграция идёт через branch-and-merge с test-based верификацией. Эмпирический результат: **+26.7% абсолютной точности на PaperBench** и **+14.3% на Commit0** относительно single-agent baseline.
- **Применение для AstroFinSentinelV5:** Branch-and-merge workflow — почти готовый шаблон для финансового пайплайна, где несколько аналитических агентов (технический анализ, фундаменталка, sentiment) могут параллельно работать над разными аспектами одного тикера в изолированных контекстах, а «merge»-агент верифицирует согласованность выводов через test-based проверки (исторические бэктесты). Это сразу снижает риск cross-contamination контекстов и даёт аудит-trail по каждой рекомендации.

---

## 3. Salesforce Agentforce Multi-Agent Orchestration — General Availability

- **Источник:** TechTimes / Springvanta — [GA-релиз 15 июня 2026](https://www.techtimes.com/articles/318456/20260616/salesforce-agentforce-multi-agent-orchestration-hits-ga-agent-descriptions-now-drive-reliability.htm)
- **Краткое описание:** 15 июня 2026 Salesforce выпустил GA multi-agent orchestration как центральный элемент Summer '26. Atlas Reasoning Engine 3.0 маршрутизирует задачи к специализированным агентам (billing, scheduling, support) на основе их plain-language описания, а не жёстких decision trees. Метрики: **$800M ARR (+169% YoY), 29 000 closed deals, 2.4B agentic work units**. Построено на открытых стандартах MCP и A2A. В ту же неделю Adobe выпустил CX Enterprise Coworker (GA) и Microsoft — Conversation Orchestration для Dynamics 365.
- **Применение для AstroFinSentinelV5:** Валидация индустрией того, что plain-language agent descriptions становятся ключевым механизмом маршрутизации. Для AstroFin это значит: роутер на естественном языке (например, «агент по крипторынку», «агент по макро-индикаторам») может быть надёжнее хардкодных правил, но требует тщательного curation описаний — иначе misrouted запросы будут исполняться «верно, но не туда». Также стоит обратить внимание на MCP/A2A как emerging standard для межагентного протокола — рано или поздно AstroFin придётся поддерживать эти протоколы для интеграций.

---

## Сводка по применимости

| Item | Technical Contribution | Ценность для AstroFin | Community/Industry |
|------|:---:|:---:|:---:|
| Foundry | 🟢 Высокая (новая архитектура) | 🟢 Высокая (trust/memory pattern) | 🟡 Средняя (академический) |
| CAID | 🟢 Высокая (+26.7% PaperBench) | 🟢 Высокая (branch-and-merge) | 🟢 Высокая (X-обсуждения) |
| Agentforce GA | 🟡 Средняя (инженерный GA) | 🟡 Средняя (MCP/A2A standard) | 🟢 Очень высокая ($800M ARR) |

---

## Источники, отфильтрованные как вторичные

- **Hermes Agent** (NousResearch) — развитие memory-providers с OAuth, не multi-agent framework per se
- **AIPensieve42/EverMemoryOS** — форк с долгосрочной памятью, интересный, но скорее memory layer
- **scott-arne/hyperpowers-evals** — eval-framework для coding agents, полезен но узкий
- **BOAD (Bandit Optimization for Agent Design)** — академический, нет прямого переноса в продакшн
- **TEMPO (dual-agent test-time training)** — академический, ограниченный scope
- **researchflow-agent** (dongtingshuo) — узконишевый (paper reproduction), single contributor
- **herdr-plugin** (jbaham2) — терминальный multiplexer plugin, слишком узкая ниша
- **Fusion Agent Swarms** (X-анонс @I_Muhammadali44) — маркетинговый анонс без технических деталей

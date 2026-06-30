# Multi-Agent AI Daily Digest — 2026-04-23

**Источники:** GitHub, arXiv, X/Twitter, Reddit, Hugging Face  
**Период:** последние 7 дней

---

## Топ-3 за сегодня

---

** [OpenAI Agents Python v0.14.0 — Sandbox Agents] **
- Источник: GitHub — OpenAI
- Описание: Релиз v0.14.0 принёс долгожданную фичу — **Sandbox Agents** — персистентные изолированные workspaces для multi-agent workflows с реальными файлами, командами и артефактами между запусками. Поддерживается подключение хранилищ (S3, Cloudflare R2, GCS, Azure Blob), а также провайдеров-песочниц (E2B, Cloudflare, Daytona и др.). Появилась memory capability для уроков между запусками. Это серьёзный шаг к надёжным production multi-agent системам.
- Применение для AstroFinSentinelV5: Sandbox-isolation идеально подходит для финансовых агентов — каждый агент может работать в своём персистентном контексте с изолированным доступом к файлам и артефактам, а memory между запусками позволит накапливать знания о рыночных ситуациях.

---

** [Orloj v0.10.0 — Production-grade orchestration runtime] **
- Источник: GitHub — OrlojHQ/orloj
- Описание: Вышел Orloj v0.10.0 (2026-04-18) — production-ready orchestration runtime для multi-agent AI систем. Ключевые нововведения: интеграция с AWS Bedrock (Claude, Llama, Titan, Mistral, Nova), Human-in-the-loop через TaskApproval с checkpointed context и TTL,现代化的 UI/UX дашборд. В Orloj агенты, тулзы и политики описываются в YAML, а рантайм берёт на себя планирование, выполнение, роутинг и governance. Поддержка Go + Python/TypeScript SDKs.
- Применение для AstroFinSentinelV5: Orloj — это готовый backbone для оркестрации агент-флота: declarative agents-as-code подход упрощает управление большим количеством специализированных агентов (аналитик, риск-менеджер, торговый execution), а TaskApproval механизм критичен для financial compliance.

---

** [MARTI-v2 / MAGRPO — Multi-Agent RL for LLM Collaboration] **
- Источник: arXiv / ICLR 2026
- Описание: Исследование MARTI-v2 (принято на ICLR 2026) представляет **MAGRPO (Multi-Agent Group Relative Policy Optimization)** — алгоритм для обучения множества LLM агентов кооперативному поведению через reinforcement learning. Моделирует collaboration как Dec-POMDP с centralized training / decentralized execution. Эксперименты показали ~3× ускорение обработки задач, 98.7%一致性 в написании текстов, 74.6% pass rate в кодогенерации. Это фундаментальный вклад в области обучения кооперации между LLM агентами.
- Применение для AstroFinSentinelV5: MAGRPO подход можно адаптировать для обучения агентов FinSentinel работать в команде — например, агент-планировщик координирует агента-аналитика и агента-исполнителя, оптимизируя общую reward function вместо индивидуальных целей.

---

*Дата формирования: 2026-04-23 08:00 UTC*
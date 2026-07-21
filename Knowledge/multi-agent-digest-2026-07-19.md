# Multi-Agent AI Daily — 2026-07-19

Период мониторинга: 12–19 июля 2026. Проверены GitHub, arXiv, Hugging Face, Reddit и X; в итог включены только материалы с техническим вкладом и практической ценностью для AstroFinSentinelV5.

## 1. Route, Communicate, and Reason: Gated Routing and Adaptive Depth for Efficient Multi-Agent Reasoning

- **Источник:** arXiv — [2607.10836](https://arxiv.org/abs/2607.10836), опубликовано 12 июля 2026.
- **Краткое описание:** Работа представляет GRADE — иерархическую multi-agent систему с четырьмя обучаемыми gate-механизмами: выбор агентов, глубина иерархии, необходимость межагентной коммуникации и pruning ветвей. Метод CoGRPO распределяет общий advantage между участвовавшими агентами и gate-узлами; заявленное преимущество — более высокая точность при примерно вдвое меньшем active compute, включая +4,8 пункта на MMLUPro против сильнейшего baseline.
- **Применение для AstroFinSentinelV5:** Идея применима к динамическому выбору подмножества агентов Совета: при низкой неопределённости запускать только нужные Fundamental/Quant/Sentiment-пулы, а при конфликте углублять deliberation. Expert Registry и calibration maps можно адаптировать к hot-swap моделей без нарушения KARL-аудита.
- **Ссылка:** https://arxiv.org/abs/2607.10836

## 2. GitHub Agentic Workflows v0.82.8 и weekly update

- **Источник:** GitHub Agentic Workflows — [weekly update от 13 июля](https://github.github.com/gh-aw/blog/2026-07-13-weekly-update/).
- **Краткое описание:** Обновление добавляет gVisor runtime и KVM-изолированный docker-sbx для запуска агентов, поддержку переиспользуемых sandbox mounts, контроль private-to-public MCP flows и исправление обновления Docker credentials перед выполнением. Это не просто релиз API: он закрывает эксплуатационные риски multi-agent workflow — изоляцию недоверенного ввода, прозрачность safe outputs и воспроизводимость запуска.
- **Применение для AstroFinSentinelV5:** Подход стоит использовать в Sprint 4 для изоляции broker-потребителей и e2e-прогона 13 агентов: отдельный sandbox для tool execution, явные mount-политики и запрет несанкционированного вывода через MCP. Модель observability/failure-investigator также хорошо ложится на уже запланированные Tempo/Jaeger traces.
- **Ссылка:** https://github.github.com/gh-aw/blog/2026-07-13-weekly-update/

## 3. NVIDIA SkillSpector

- **Источник:** GitHub — [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector), активная разработка в июле 2026.
- **Краткое описание:** SkillSpector — сканер AI-agent skills и MCP-инструментов: статический анализ дополняется опциональной LLM-проверкой, OSV-проверкой зависимостей и YARA-сигнатурами. Он выявляет prompt injection, exfiltration, privilege escalation, tool misuse, rogue-agent behavior, memory poisoning, unsafe permissions и другие риски; отчёты поддерживают terminal, JSON, Markdown и SARIF, а baseline позволяет блокировать только новые находки.
- **Применение для AstroFinSentinelV5:** Его можно поставить как pre-install/pre-deploy gate для skills и MCP-серверов агентов, особенно для data_room и broker-интеграций. SARIF/JSON-отчёты стоит подключить к CI вместе с architecture_linter и audit trail, чтобы KARL не мог принять решение на базе непроверенного инструмента.
- **Ссылка:** https://github.com/NVIDIA/SkillSpector

## Отфильтровано

- Исключены общие анонсы курсов и книги без нового исполняемого инструмента или измеримого технического результата.
- Исключены узкие академические работы без прямого переноса в orchestration, tool use, evaluation или safety-пайплайн.
- Дубликаты обсуждений одного и того же релиза объединены.

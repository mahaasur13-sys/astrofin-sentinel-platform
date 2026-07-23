# ADD-2026-07-13: Разделение трёх слоёв гейтов (L8/L9/L10)

**Статус:** Принято
**Дата:** 2026-07-13
**Контекст:** В проекте существует три модуля, реализующих концепцию "гейта":

- `deploy/iac/ete/governance_gate.py` — L8 business gate (APPROVED/REJECTED/ESCALATED)
- `deploy/iac/l9_ebl/gate/gate.py` — L9 infra capability gate (ALLOW/DENY/REDIRECT/ESCALATE)
- `deploy/iac/ai_scheduler/policy.py` — L10 batch node selection (return dict)

Несмотря на общую семантику, они работают на разных уровнях стека и имеют разные аудитории.

**Решение:** Не объединять эти модули. Каждый остаётся в своём контексте (ete/, l9_ebl/, ai_scheduler/). Документировать это различие для будущих разработчиков.

**Последствия:** Упрощается понимание архитектуры, исключается риск ошибочного рефакторинга.

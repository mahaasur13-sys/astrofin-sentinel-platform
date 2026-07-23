# ATOMFEDERATION-OS — Функции агентов

> Система распределённого управления с детерминированными агентами.  
> Все агенты работают через `ExecutionGateway` и подчиняются ограничениям C1-C10.

---

## 1. ControlArbitrator (`orchestration/control_arbitrator.py`)

**Роль:** Арбитр сигналов управления — разрешает конфликты между сигналами от DRL/SBS/Coherence/Actuator.

**Функции:**
- `submit(signal)` — принимает `ControlSignal` от любого слоя
- `resolve()` — возвращает один выигравший сигнал (наивысший приоритет + стабильный tie-break по имени)
- `resolve_many()` — возвращает все сигналы отсортированные по приоритету
- `pending_count` — число ожидающих сигналов

**Детерминизм:** При равном приоритете победителя определяет стабильный порядок по `source` (лексикографический). Нет рандома.

---

## 2. MutationExecutor (`orchestration/mutation_executor.py`)

**Роль:** Единственная точка применения мутаций состояния. Все state mutations проходят через него.

**Функции:**
- `apply_mutation(mutation)` — применяет мутацию через `ExecutionGateway.mutation_context`
- Защищён метаклассом `MutationExecutorMetaclass`: нельзя инстанцировать вне Gateway-контекста
- Все публичные методы декорированы `@ExecutionGateway.requires_gateway`

**Детерминизм:** Все мутации идут через гейтвей, гарантирующий последовательный порядок.

---

## 3. ProofFeedbackController (`meta_control/proof_feedback_controller.py`)

**Роль:** Преобразует `TemporalVerificationReport` в корректировки весов арбитража. Реагирует на нестабильность доказательств.

**Функции:**
- `compute(report)` → `List[WeightDelta]` — анализирует отчёт верификатора и генерирует дельты весов
- Штрафует источники при: `source_switch`, `reasoning_collapse`, `causal_break`, `proof_regression`
- Награждает стабильные источники при: `is_stable == True`

**Детерминизм:** Фиксированные коэффициенты штрафов/наград, вычисления без рандома.

---

## 4. ConsensusResolver (`federation/consensus_resolver.py`)

**Роль:** Разрешение консенсуса в федерации узлов с голосованием и кворумом.

**Функции:**
- `register_node(node_id, weight)` — регистрация узла с весом
- `submit_vote(node_id, tick, vote)` — голосование ('approve'/'reject'/'abstain')
- `resolve_consensus(tick)` — принимает решение на основе голосов
- `_compute_signature()` — детерминированная подпись голоса (SHA-256)

**Детерминизм:** Подпись голоса хешируется, кворум считается по весам, решения воспроизводимы.

---

## 5. WorkerProjectionEngine (`swarm/worker_projection_engine.py`)

**Роль:** Проекция состояния воркеров в swarm-слое с детерминированным упорядочением.

**Функции:**
- `project_worker(tick, worker_id, raw_state)` — создаёт проекцию состояния воркера
- `get_projection(worker_id)` — извлекает проекцию по ID
- `AtomicQueue` — thread-safe очередь с детерминированным порядком

**Детерминизм:** Все операции через Gateway, очередь не использует рандом.

---

## 6. FeedbackPrioritySolver (`orchestration/feedback_priority_solver.py`)

**Роль:** Вычисляет глобальный приоритет feedback-сигналов от разных слоёв.

**Функции:**
- `compute_priority(signal)` → `urgency * 0.7 + stability_impact * 0.3`
- `rank(signals)` → `Dict[str, float]` — приоритеты всех сигналов
- `rank_sorted(signals)` → `List[(layer, priority)]` — отсортированный список

**Детерминизм:** Фиксированные веса (0.7 / 0.3), сортировка детерминирована.

---

## 7. StabilityWeightedArbitrator (`meta_control/stability_weighted_arbitrator.py`)

**Роль:** Арбитр с учётом стабильности — взвешивает источники по их исторической стабильности из `stability_ledger`.

**Функции:**
- Интегрирует `ProofFeedbackController` + `stability_ledger` + `state_window`
- `IntegrationReport integrate()` — объединяет данные в единый отчёт
- `GainModulator` — модулирует темпоральное усиление
- `WeightModulator` — модулирует веса на основе истории решений
- `CoherenceEnricher` — обогащает когерентность данными персистентности

**Детерминизм:** Все модуляции детерминированы, основаны на накопленных данных.

---

## 8. TemporalGainScheduler (`meta_control/temporal_gain_scheduler.py`)

**Роль:** Планировщик темпорального усиления — модулирует gain-функцию на основе горизонта планирования.

**Функции:**
- `schedule(tick, horizon)` — вычисляет gain с учётом горизонта
- Адаптирует коэффициенты усиления по мере роста горизонта

**Детерминизм:** tick → gain mapping без рандома.

---

## 9. DriftPolicyAdaptor (`meta_control/drift_policy_adaptor.py`)

**Роль:** Адаптер политики при обнаружении drift — корректирует политику при отклонении поведения.

**Функции:**
- `adapt(policy, drift_report)` — адаптирует политику на основе drift-отчёта
- Обновляет параметры политики при обнаружении систематического отклонения

**Детерминизм:** Детерминированная коррекция на основе drift-метрик.

---

## 10. CircuitBreaker (`orchestration/planning_observability/circuit_breaker.py`)

**Роль:** Прерыватель цепи — блокирует мутации при обнаружении нестабильности (oscillation, governor block).

**Функции:**
- Состояния: `CLOSED` → `OPEN` → `HALF` → `CLOSED`
- `can_mutate` — `True` только если `state == CLOSED` и нет governor block
- Триггеры: severity > threshold → OPEN; health >= recovery_threshold → HALF; health >= close_threshold → CLOSED

**Детерминизм:** Смена состояний детерминирована по health score и threshold.

---

## 11. InvariantChecker (`orchestration/v8_2a_safety_foundations/invariant_checker.py`)

**Роль:** Проверка ε-нормы, спектрального радиуса, PSD-инвариантов перед мутацией.

**Функции:**
- `check_invariants(state)` — проверяет математические инварианты
- `is_valid_transition(from_state, to_state)` — валидирует переход

**Детерминизм:** Математические проверки без рандома.

---

## 12. RollbackEngine (`orchestration/v8_2a_safety_foundations/rollback_engine.py`)

**Роль:** Откат к последнему валидному состоянию при нарушении инвариантов.

**Функции:**
- `checkpoint(state)` — сохраняет checkpoint
- `revert()` — откатывает к последнему checkpoint
- `append_to_ledger(action)` — добавляет действие в ledger

**Детерминизм:** Детерминированный rollback по ledger.

---

## 13. DeterministicScheduler (`orchestration/deterministic_scheduler.py`)

**Роль:** Детерминированный планировщик — заменяет рандом на hash-based ordering.

**Функции:**
- `schedule(tick)` — планирование без `random.*`
- `LockstepMode` — синхронное выполнение на всех узлах
- ПроверкиConstraints (C1-C10) на каждый schedule

**Детерминизм:** Все решения через hash, нет рандома.

---

## 14. ExecutionGateway (`orchestration/execution_gateway.py`)

**Роль:** Центральный гейтвей — синглтон, управляющий всеми мутациями и проверками безопасности.

**Функции:**
- `mutation_context(can_mutate)` — контекстный менеджер для мутаций
- `requires_gateway()` — декоратор для защиты методов
- `is_safe()` — проверка безопасности
- `SafetyViolationError` — исключение при нарушении

**Детерминизм:** Единая точка контроля, все операции сериализуются.

---

## 15. StateVector (`federation/state_vector.py`)

**Роль:** Вектор состояния федерации с детерминированными timestamp.

**Функции:**
- `merge(other)` — мерж векторов
- `tick()` — текущий тик
- `causal_order()` — каузальное упорядочение

**Детерминизм:** timestamps基于DeterministicClock.

---

## Архитектура взаимодействия агентов

```
ProofFeedbackController ──→ StabilityWeightedArbitrator ──→ ControlArbitrator
     ↑                                                    ↓
TemporalVerifier                                    MutationExecutor
                                                   ↓
                                          ExecutionGateway
                                                   ↓
                                      DeterministicScheduler
```

```
CircuitBreaker ──→ блокирует мутации при нестабильности
InvariantChecker ──→ проверяет перед мутацией
RollbackEngine ←── нарушение инвариантов
```

---

## Constraints (C1-C10) — обязательны для всех агентов

| # | Constraint | Применение |
|---|------------|-----------|
| C1 | Нет `time.time()` в control flow | Все агенты |
| C2 | Нет `uuid.uuid4()` для identity | Все агенты |
| C3 | Нет `random.*` в scheduling | DeterministicScheduler, FeedbackPrioritySolver |
| C4 | Нет `asyncio.sleep()` с недетерминированной задержкой | Все агенты |
| C5 | Все filesystem операции через `AtomicFileWrite` | Persistence agents |
| C6 | Все network сообщения через `ReplayableMessageQueue` | ConsensusResolver, WorkerProjectionEngine |
| C7 | Все tick boundaries через `GlobalExecutionBarrier` | DeterministicScheduler |
| C8 | Нет вероятностных политик scheduling | FeedbackPrioritySolver |
| C9 | Replay produces bitwise-identical output | Все агенты |
| C10 | Нет модификации RL-019/020/021 deterministic kernel | Все агенты |
# GLOBAL TASK LIFECYCLE SPEC — единый control plane

## Проблема (диагноз)

Две системы управления состоянием работают **с одним key prefix** (`task_state:`) и **，没有任何协调**:

| | TaskStateMachine (task_state.py) | state_machine.py |
|--|--|--|
| Атомарность | ✅ Lua | ❌ read→modify→write |
| Ownership | ✅ worker_id check | ❌ нет |
| Epoch/версия | ❌ нет | ❌ нет |
| Кто использует | DurableTaskQueue | engine.py, async_engine.py |
| **Результат** | | **гонки, дубли, хаос** |

---

## Архитектурное решение

### Единственный источник истины

```
┌─────────────────────────────────────────────────────┐
│                   TaskStore                         │
│  (заменяет TaskStateMachine + state_machine.py)     │
│                                                     │
│  ✅ Lua-атомарные переходы                          │
│  ✅ Ownership check перед каждым действием          │
│  ✅ Epoch versioning для retry                      │
│  ✅ engine.py НЕ трогает state напрямую             │
└─────────────────────────────────────────────────────┘
```

### Key schema

```
task_state:<task_id>        — Hash  (state, worker_id, epoch, attempt, ...)
task_result:<task_id>       — String (JSON, TTL 3600s)
task_epoch:<task_id>        — String (int, monotonic)
```

### State enum

```
PENDING  → RUNNING  (claim)
RUNNING  → DONE     (complete)
RUNNING  → FAILED   (fail, attempts exhausted)
RUNNING  → PENDING  (retry, новый epoch)
RUNNING  → CANCELLED
```

### TaskRecord

```python
task_id: str
state: TaskState
worker_id: str        # кто владеет
epoch: int            # версия (монотонно растёт при retry)
attempt: int
max_attempts: int
enqueued_at: float
started_at: Optional[float]
finished_at: Optional[float]
error: Optional[str]
payload: dict
```

---

## TaskStore API

```python
class TaskStore:
    async def create_task(task_id, payload, max_attempts) → TaskRecord
    async def claim_task(task_id, worker_id) → TaskRecord | None
    async def complete_task(task_id, worker_id, result) → bool
    async def fail_task(task_id, worker_id, error) → bool
    async def retry_task(task_id, worker_id) → bool  # new epoch, state→PENDING
    async def cancel_task(task_id, worker_id) → bool
    async def get_task(task_id) → TaskRecord | None
    async def get_result(task_id) → dict | None
    async def recover_stale_tasks(worker_id) → int
```

### Ownership semantics

- `claim_task` — проверяет state==PENDING, ставит worker_id + started_at
- `complete_task` — проверяет worker_id match + state==RUNNING
- `fail_task` — проверяет worker_id match + state==RUNNING
- `retry_task` — создаёт новый epoch, сбрасывает worker_id, state→PENDING
- `cancel_task` — проверяет worker_id match

### Epoch semantics (критично)

```
task_id="abc", epoch=1, state=RUNNING, worker_id=worker_A
    ↓ fail (attempt < max)
retry_task → epoch=2, state=PENDING, worker_id=""
    ↓ claim (любой worker)
claim_task → epoch=2, state=RUNNING, worker_id=worker_B
```

Стар Workers с epoch=1 автоматически **невалидны** — они видят что epoch изменился и не выполняют work.

### Fail policy

```
attempt < max_attempts → retry_task() → state=PENDING, новый epoch
attempt >= max_attempts → state=FAILED
```

---

## Что удаляем

- `state_machine.py` — полностью (сломан, не нужен)
- Все `from .state_machine import transition, TaskState` — заменить на TaskStore

---

## engine.py рефакторинг

**БЫЛО:**
```python
from .state_machine import transition, TaskState, store_result

await transition(task_id, TaskState.RUNNING)
await transition(task_id, TaskState.COMPLETED)
await transition(task_id, TaskState.FAILED, error=...)
```

**СТАЛО:**
```python
from .task_store import TaskStore, get_task_store

store = get_task_store()

record = await store.claim_task(task_id, worker_id)
if not record:
    return  # уже claimed другим

await store.complete_task(task_id, worker_id, result)
await store.retry_task(task_id, worker_id)  # вместо transition → RETRY
```

---

## DurableTaskQueue (минимальные правки)

Уже использует `TaskStateMachine` → достаточно:
- Переименовать `TaskStateMachine` → `TaskStore` (или адаптер)
- Добавить `retry_task(epoch-aware)`
- Убрать дублирование с `state_machine.py`

---

## Тесты

```bash
cd agent-runtime
pytest testing/test_task_store.py -v
```

至少:
- claim_task: только PENDING
- complete_task: только owner + RUNNING
- fail_task: проверка attempts
- retry_task: новый epoch, сброс worker_id
- recover_stale_tasks: stale RUNNING → recovered by new worker
- concurrent claim: только один winner

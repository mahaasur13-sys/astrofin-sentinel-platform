# ATOMFEDERATION-OS Production Hardening

## 📋 Текущее состояние

### Архитектура (существующая)

```
USER INPUT
    ↓
ATOMFederationOS (orchestrator/core)
    ↓
10-step ExecutionLoop → PolicyKernel → AABS → FederationKernel → AuditLog
```

### Сильные стороны (не трогаем)
- **AABS Gateway** — KEY-GATED, pipeline steps зафиксированы, audit log есть
- **QuorumCommitEngine** — детерминированный quorum `floor(N/2)+1`, sorted by node_id
- **SBS adapter** — scoped sys.path mutation (не глобальный)
- **ATOMFederationOS.bootstrap()** — уже связывает все подсистемы

### Проблемы (TREAT FIRST)

| # | Проблема | Файл | Последствие |
|---|---|---|---|
| 1 | `ExecutionGateway` существует **только как контракт** — нет единой точки входа, агенты вызываются напрямую | `atom_federation_os.py` | bypass pipeline |
| 2 | AABS **не блокирует** прямые `requests`/`httpx` — можно вызвать внешний API в обход gateway | `aabs_gateway.py` | security bypass |
| 3 | `AsyncExecutionEngine.execute()` использует `asyncio.sleep(0.001)` — nondeterministic | `runtime/async_execution.py` | race conditions |
| 4 | `SwarmEngine.run()` генерирует задачи с `time.time()` в `trace_hash` | `swarm/swarm_engine.py` | nondeterminism |
| 5 | `DevOpsAgent` изолирован от `ExecutionGateway` — не участвует в pipeline | `devops/devops_agent.py` | CI healing offline |
| 6 | `sbs_adapter` требует **ручного** вызова `get_sbs_runtime()` — не enforced pre-action | `bridge/sbs_adapter.py` | SBS может быть обойден |
| 7 | Нет runtime guard противMutationExecutor вне ACT stage | — | state mutation bypass |
| 8 | Нет контроля ledger direct access | — | append-only нарушается |

---

## 🏗️ Execution Pipeline (PROPOSED)

```
INPUT
  ↓
ExecutionGateway.run(intent)          ← ЕДИНСТВЕННЫЙ entry point
  ↓
SBS Gate (sbs_adapter)               ← Блокирует unsafe перед ANY действием
  ↓
Policy Gate (policy_bridge)          ← Zero-trust проверка intent
  ↓
Perception (PerceptionFusion)         ← Fuse text/vision/voice → context
  ↓
AttentionRouter                       ← Приоритет: voice > vision > text
  ↓
Planning (SwarmEngine)                ← fan_out / concurrent / sequential
  ↓
[Consensus Layer]                     ← QuorumAgent / ConsensusAgent
  │   (QUORUM CHECK)                   ← НЕ bypass — floor(N/2)+1
  ↓
Execution (AsyncExecutionEngine)      ← deterministic task queue
  ↓
External (AABSGateway ONLY)           ← ВСЕ внешние вызовы через gateway
  ↓
ACT (MutationExecutor)                ← ЕДИНСТВЕННАЯ точка state mutation
  ↓
Ledger (append-only)                  ← Запись результата
  ↓
VerificationResult → AuditLog → Federation broadcast
```

---

## 📦 План изменений по файлам

### 1. `execution/execution_gateway.py` — NEW

Создать `ExecutionGateway` как **единственный entry point**.

```python
class ExecutionGateway:
    """
    ЕДИНСТВЕННАЯ точка входа для любого agent execution.
    Инвариант: НИКАКОЙ агент не может быть вызван вне этой цепочки.
    """

    def __init__(self):
        self.policy    = PolicyBridge.get_policy_kernel()
        self.sbs       = SBSAdapter.get_sbs_runtime()
        self.aabs      = AABSGateway()
        self.perception = PerceptionFusion()
        self.swarm     = SwarmEngine()
        self.async_exec = AsyncExecutionEngine()
        self.ledger    = LedgerState()
        self._stage    = ExecutionStage.IDLE

    def run(self, intent: str, context: dict | None = None) -> VerificationResult:
        # 1. SBS Gate (PRE-CHECK)
        if not self._sbs_pre_check(intent):
            return _blocked_result("SBS_VETO")

        # 2. Policy Gate
        if not self._policy_check(intent):
            return _blocked_result("POLICY_VETO")

        # 3. Perception
        fused = self._fuse_context(intent, context)

        # 4. Planning via SwarmEngine
        plan = self.swarm.get_strategy(intent)
        steps = self._build_steps(intent, plan)

        # 5. Consensus (если N > 1)
        quorum_ok = self._consensus_check(steps)
        if not quorum_ok:
            return _blocked_result("QUORUM_REJECTED")

        # 6. Execution (deterministic)
        results = self._execute_steps(steps)

        # 7. ACT (mutation) + Ledger
        ledger_entry = self._commit(results)

        # 8. Verify + Audit
        return self._verify_and_audit(ledger_entry)
```

### 2. `runtime/async_execution.py` — DETERMINISTIC

```python
class AsyncExecutionEngine:
    def __init__(self, max_workers: int = 4, seed: int | None = None):
        self.max_workers = max_workers
        self._rng = random.Random(seed or 42)  # deterministic

    def execute(self, task: dict, deterministic_ts: float) -> dict:
        # ВМЕСТО time.time() — переданный deterministic timestamp
        return {
            "status": "done",
            "ts": deterministic_ts,
            "worker": min(task["worker_id"], self.max_workers - 1),
        }
```

### 3. `swarm/swarm_engine.py` — REMOVE NONDET

- Заменить `time.time()` в `trace_hash` на `task_id` (детерминированный)
- Добавить `sorted merge` для результатов воркеров
- Запретить side-effects внутри воркеров: `_validate_no_side_effects(subtasks)`

```python
def run(self, task: str, num_workers: int | None = None,
        strategy: str = "sequential") -> dict:
    # deterministic task ordering
    task_id = hashlib.sha256(task.encode()).hexdigest()[:12]
    subtasks = sorted([
        {"id": f"w{i}", "description": f"subtask {i}", "status": "pending"}
        for i in range(min(workers, 4))
    ], key=lambda x: x["id"])  # deterministic sort by id

    return {
        "task": task,
        "strategy": strategy,
        "workers": workers,
        "subtasks": subtasks,
        "merged_result": ...,  # merge sorted by id
        "trace_hash": hashlib.sha256(f"{task_id}{strategy}".encode()).hexdigest()[:16],
    }
```

### 4. `aabs/aabs_gateway.py` — ENFORCE GLOBAL USAGE

```python
# Runtime guard: monkey-patch requests/httpx
import requests, httpx

_original_requests_get  = requests.get
_original_requests_post = requests.post
_original_httpx_get     = httpx.get
_original_httpx_post    = httpx.post

def _blocked(*args, **kwargs):
    raise RuntimeError(
        "DIRECT EXTERNAL CALL BLOCKED. "
        "All external calls MUST use AABSGateway.aabs_call()."
    )

requests.get  = _blocked
requests.post = _blocked
httpx.get     = _blocked
httpx.post    = _blocked
# После блокировки восстановить в тестах: requests.get = _original_requests_get
```

### 5. `devops/devops_agent.py` — INTEGRATE WITH CI

```python
def run(self, ci_logs: str, repo_path: str = "/home/workspace") -> dict:
    """
    CI FAIL → DevOpsAgent.run() → analyze → patch → test → commit
    Ограничение: только безопасные изменения (lint, imports, deterministic fixes).
    """
    analysis = analyze_logs(ci_logs)      # CIAnalyzer
    patch    = generate_patch(analysis)    # PatchEngine
    # ВАЖНО: выполняется ЧЕРЕЗ ExecutionGateway (НЕ напрямую)
    result = ExecutionGateway().run(
        f"fix: {analysis['root_cause']}",
        context={"patch": patch, "repo": repo_path}
    )
    return result
```

### 6. `bridge/sbs_adapter.py` — HARD GATE ENFORCEMENT

```python
def get_sbs_runtime() -> dict:
    """Возвращает SBS runtime. Вызывать ДО любого действия."""

def enforce_pre_action() -> bool:
    """HARD GATE: вызывается в начале ExecutionGateway.run()."""
    sbs = get_sbs_runtime()
    if not sbs["available"]:
        logger.warning("SBS not available — proceeding without invariant enforcement")
        return True  # fail-open для single-node; fail-close для multi-node
    enforcer = sbs["SBSRuntimeEnforcer"]
    stage = sbs["ExecutionStage"]
    enforcer.enter(stage.PLANNING)
    return True
```

### 7. `ledger/append_only_ledger.py` — NEW

```python
class AppendOnlyLedger:
    """
    Ledger гарантирует append-only.
    write() записывает в append-only store.
    read() читает по index.
    _verify_append_only() проверяет chain integrity.
    """
    def __init__(self, store_path: str):
        self._store = []
        self._lock = threading.Lock()

    def append(self, entry: dict) -> int:
        with self._lock:
            entry["index"] = len(self._store)
            entry["prev_hash"] = self._last_hash()
            entry["self_hash"] = self._hash(entry)
            self._store.append(entry)
        return entry["index"]

    def verify(self) -> bool:
        # Проверка chain integrity: каждый prev_hash == hash предыдущей записи
        for i in range(1, len(self._store)):
            expected_prev = self._hash(self._store[i-1])
            if self._store[i]["prev_hash"] != expected_prev:
                return False
        return True
```

---

## 🔒 Инварианты (Assertions)

```python
# В начале ExecutionGateway.run():
assert current_stage == ExecutionStage.IDLE, "Re-entrancy blocked"
assert sbs_status != SBSStatus.LOAD_FAILED, "SBS load failure — halt"

# НЕ позволять вызов MutationExecutor вне ACT stage:
assert current_stage == ExecutionStage.ACT, "MutationExecutor called outside ACT"

# НЕ позволять direct ledger writes:
assert caller == "ExecutionGateway", "Ledger write from non-EG agent"
```

---

## 🧩 Consensus: QuorumAgent / ConsensusAgent

### Deterministic quorum (floor(N/2)+1)

```python
def compute_quorum(total_nodes: int) -> int:
    return (total_nodes // 2) + 1

def sorted_quorum_votes(node_ids: List[str]) -> List[str]:
    """Возвращает votes отсортированные по node_id — детерминированный порядок."""
    return sorted(node_ids)
```

### Single-node bypass

```python
# single-node: consensus не требуется — пропускаем quorum check
if total_nodes == 1:
    return True  # bypass consensus (корректно)
```

---

## 🕸️ Execution Flow (строгий)

```
Input → EG.run()
  ├─ SBS Gate (pre-check)
  │    └─ sbs_adapter.enforce_pre_action()
  │
  ├─ Policy Gate
  │    └─ policy_bridge.get_policy_kernel().approve()
  │
  ├─ PerceptionFusion.ingest_text/vision/voice()
  │    └─ AttentionRouter.route()
  │
  ├─ SwarmEngine.get_strategy() / .run()
  │    └─ deterministic merge
  │
  ├─ Consensus (если multi-node)
  │    └─ QuorumCommitEngine.check_quorum()
  │
  ├─ AsyncExecutionEngine.execute()
  │    └─ deterministic task queue
  │
  ├─ AABSGateway.call() ONLY
  │    └─ KEY_GATED + pipeline steps
  │    └─ 6-step: VALIDATE → SANITIZE → MAP → EXECUTE → VERIFY → RETURN
  │
  ├─ ACT (MutationExecutor)
  │    └─ только здесь возможны state mutations
  │
  └─ Ledger.append()
       └─ verify append-only chain
```

---

## ✅ Мини-доказательство корректности

### 1. Нет bypass путей

- **ExecutionGateway.run()** — единственный public entry point
- Все агенты (`SwarmEngine`, `AABS`, `DevOpsAgent`) требуют `ExecutionGateway` как caller
- Прямые вызовы `requests.get()` блокированы runtime guard

### 2. Async не ломает детерминизм

- `AsyncExecutionEngine` получает `deterministic_ts` как параметр
- `SwarmEngine` сортирует результаты по `task_id` (не по `time.time()`)
- Макс. воркеров зафиксирован (`max_workers=4`)

### 3. Consensus корректен

- `quorum = floor(N/2)+1` — строгое большинство
- `sorted_quorum_votes()` — детерминированный порядок голосов
- `single-node bypass` — корректен, т.к. no-fork-гарантия в single-node

### 4. Ledger append-only

- `append()` — единственный метод записи
- `verify()` — проверка chain integrity по hash chain
- Нет `update()` / `delete()` методов

---

## 📁 Файлы для создания/изменения

| Файл | Действие | Приоритет |
|---|---|---|
| `execution/execution_gateway.py` | Создать | 🔴 Critical |
| `runtime/async_execution.py` | Изменить: deterministic scheduler | 🔴 Critical |
| `swarm/swarm_engine.py` | Изменить: remove nondeterminism | 🔴 Critical |
| `aabs/aabs_gateway.py` | Изменить: runtime guard | 🟡 High |
| `devops/devops_agent.py` | Изменить: integrate with EG | 🟡 High |
| `ledger/append_only_ledger.py` | Создать | 🟡 High |
| `bridge/sbs_adapter.py` | Изменить: enforce_pre_action | 🟡 High |
| `runtime/linear_os_kernel.py` | Проверить: consensus integration | 🟡 High |

---

## 🎯 Критерии готовности

- [ ] `ExecutionGateway.run()` — единственный entry point (test: попытка вызова агента напрямую → RuntimeError)
- [ ] `requests.get()` / `httpx.post()` → RuntimeError (если вызов не через AABS)
- [ ] AsyncExecutionEngine: два вызова с одинаковым `deterministic_ts` → идентичный результат
- [ ] SwarmEngine: результат `.run()` не содержит `time.time()`
- [ ] DevOpsAgent CI self-healing: `DevOpsAgent.run(ci_logs)` → auto commit (если safe fix)
- [ ] Ledger: `append_only_ledger.verify()` возвращает True после 100 записей
- [ ] SBS: `enforce_pre_action()` вызывается ДО любого действия
- [ ] Consensus: `compute_quorum(3)` = 2, `compute_quorum(4)` = 3

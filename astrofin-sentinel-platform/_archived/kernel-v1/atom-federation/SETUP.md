# Установка и проверка atom-federation-os (HARDENING v2)

## Цель

Развернуть atom-federation-os на локальной машине, убедиться, что система работает, и проверить компоненты HARDENING Phase 2 — Failure Replay.

## Предварительные требования

- Python 3.10+ (рекомендуется 3.12)
- Git
- Виртуальное окружение (`venv`) или `pipx` (для изоляции CLI)

---

## Шаг 1: Клонирование и установка

```bash
git clone https://github.com/mahaasur13-sys/atom-federation-os.git
cd atom-federation-os
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

После установки команда `sbs` станет доступна в окружении.

---

## Шаг 2: Проверка базовой работоспособности

```bash
sbs doctor
```

**Ожидаемый вывод:** все пункты `pass`, итог `Overall: PASS`.

---

## Шаг 3: Запуск тестов

```bash
# Все тесты модуля alignment (52 теста, все зелёные)
python -m pytest alignment/ -v --tb=no

# ADLR (Hardening Phase 2 — RecoveryPolicy + FailureScenario)
python -m pytest alignment/test_adlr.py -v

# Failure Replay — API доступен напрямую (Python)
python -c "
from alignment.failure_replay import FailureRecorder, FailureParams, SandboxEngine

# Быстрая проверка API
params = FailureParams.from_violation(
    violation='QUORUM_VIOLATION [F2]: ratio=0.3',
    layer='F2',
    failure_type='QUORUM_VIOLATION',
    severity='HIGH'
)
recorder = FailureRecorder()
incident_id = recorder.record_violation(
    violation='QUORUM_VIOLATION [F2]: ratio=0.3',
    layer='F2',
    failure_type='QUORUM_VIOLATION',
    severity='HIGH',
    invariant_states={'QUORUM_SAFETY': False},
    layer_states={'F2': {'quorum_ratio': 0.3}}
)
result = recorder.replay_scenario(incident_id)
print('Success:', result['success'])
print('Action:', result.get('action', {}))
"
```

**Все alignment-тесты зелёные (52 теста):**
```
alignment/test_adlr.py       10 passed   (ADLR + RecoveryPolicy)
alignment/test_alignment.py   4 passed
alignment/test_bcil.py       4 passed
alignment/test_convergence.py 5 passed
alignment/test_gast.py       4 passed
alignment/test_gcpl.py      12 passed
alignment/test_gcst.py       5 passed
alignment/test_gsct.py       3 passed
alignment/test_mcpc.py       2 passed
alignment/test_rcf.py       10 passed
──────────────────────────────────────────────
TOTAL                       52 passed
```

---

## Шаг 4: Проверка CLI-команды `sbs replay`

```bash
sbs replay --list          # покажет все сохранённые сценарии (может быть пусто на свежей установке)
sbs replay <incident_id>    # воспроизведение конкретного инцидента
sbs replay <id> --json     # вывод в JSON
```

### Создание тестового сценария (если список пуст)

```python
from alignment.failure_replay import FailureRecorder

recorder = FailureRecorder()
incident_id = recorder.record_violation(
    violation="QUORUM_VIOLATION [F2]: ratio=0.3 (required=0.5)",
    layer="F2",
    failure_type="QUORUM_VIOLATION",
    severity="HIGH",
    invariant_states={"QUORUM_SAFETY": False},
    layer_states={"F2": {"quorum_ratio": 0.3}}
)
print(recorder.list_scenarios()[0])  # скопировать ID
```

Затем:

```bash
sbs replay <скопированный_id>
```

Увидите отчёт о восстановлении в красивом формате.

---

## Шаг 5: Пример программного использования API

```python
from alignment.failure_replay import FailureRecorder, FailureParams

recorder = FailureRecorder()

# Запись сценария (сохраняем в storage)
scenario = recorder.record_violation(
    violation="QUORUM_VIOLATION [F2]: ratio=0.3 (required=0.5)",
    layer="F2",
    failure_type="QUORUM_VIOLATION",
    severity="HIGH",
    invariant_states={"QUORUM_SAFETY": False},
    layer_states={"F2": {"quorum_ratio": 0.3}}
)
recorder.save(scenario.incident_id)   # сохраняем в файл

incident_id = scenario.incident_id    # получаем строковый ID

# Воспроизведение по строковому ID
result = recorder.replay_scenario(incident_id)

if result["success"]:
    print(f"Recovery successful with action: {result['action']}")
else:
    print(f"Recovery failed: {result['final_violations']}")
```

---

## Ожидаемые результаты

| Проверка | Ожидание |
|----------|----------|
| `sbs doctor` | `PASS` |
| Все тесты `failure_replay.py` | `PASS` |
| `sbs replay <id>` | Успешно воспроизводит отказ и запускает восстановление |
| Программный вызов `replay_scenario` | Детерминированный, изолированный результат без влияния на основную систему |

После этого этап Failure Replay можно считать полностью интегрированным и готовым к следующему шагу — **Chaos Integration**.

---

## Быстрый старт — одна команда

```bash
git clone https://github.com/mahaasur13-sys/atom-federation-os.git && \
cd atom-federation-os && \
python -m venv .venv && \
source .venv/bin/activate && \
pip install -e . && \
sbs doctor
```

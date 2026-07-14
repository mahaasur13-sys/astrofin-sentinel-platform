# atom-federation-os — Установка и быстрый старт

> v10.x (RL-022) | Kubernetes operator + deterministic multi-agent control plane
> Для: Pop!_OS 24.04 / Ubuntu 24.04

---

## 📦 Что это

**atom-federation-os** — распределённая система управления с детерминированными агентами. Состоит из:

| Компонент | Описание |
|-----------|----------|
| **Kubernetes Operator** | Контроллер для управления ATOMCluster (SBS/healing/drift/quorum/scale) |
| **Deterministic Kernel** | Детерминированный кернел (RL-019/020/021) — никакого рандома, time.time(), uuid4() |
| **GEB (GlobalExecutionBarrier)** | Синхронизация узлов перед каждым tick — гарантирует replay-identical execution |
| **Persistence Layer** | Atomic file writes, WAL, crash consistency, checkpoint management |
| **Observability** | Trace ledger с глобальным tick index + Replay certification |
| **Federation Layer** | Gossip-протокол, PBFT consensus, Byzantine detector, trust dynamics |
| **Orchestration** | ControlArbitrator, MutationExecutor, CircuitBreaker, InvariantChecker |

**Требования:** Python 3.10+, Kubernetes cluster (kind/minikube/k3s), Docker

---

## 🧩 Архитектура

```
atom-federation-os/
├── kubernetes/                    # K8s operator + manifests
│   ├── atom_operator/           # Python operator (controller + reconciler)
│   │   ├── main.py              # Entrypoint
│   │   ├── controller.py       # ATOMController
│   │   ├── reconciler.py       # SBS/healing/drift/quorum/scale
│   │   └── requirements.txt    # kubernetes==29.0.0, prometheus-api-client==0.5.1
│   ├── crd/atomcluster.yaml    # ATOMCluster CRD
│   └── manifests/               # install.yaml, deployment.yaml, sample.yaml
├── core/                         # Deterministic kernel (RL-019/020/021)
│   ├── deterministic.py          # DeterministicClock, DeterministicRNG, GlobalExecutionSequencer
│   └── runtime/geb.py          # GlobalExecutionBarrier — node sync before tick
├── orchestration/                # Control plane
│   ├── execution_gateway.py     # Singleton — mutation control
│   ├── deterministic_scheduler.py # LockstepMode + hash-based scheduling
│   ├── control_arbitrator.py    # Signal arbitration
│   ├── planning_observability/  # CircuitBreaker, DriftProfiler, EvaluationMetrics
│   └── v8_2a_safety_foundations/ # InvariantChecker, RollbackEngine, MutationLedger
├── federation/                   # Federated consensus
│   ├── bft_consensus.py         # PBFT consensus
│   ├── state_vector.py         # StateVector (DeterministicClock-based timestamps)
│   ├── gossip_protocol.py      # Proof-enriched gossip
│   └── trust_weighted/         # Trust dynamics, skew detection
├── persistence/                  # Crash-safe persistence
│   ├── atomic_fs.py             # AtomicFileWrite, AtomicMultiFileWrite
│   ├── stateful_recovery.py    # EventStore, MutationLedger, RecoveryManager
│   └── crash_consistency.py    # CrashSnapshot, CheckpointManager, WALRecoveryProtocol
└── observability/               # Trace + replay certification
    ├── trace_ledger.py          # Global tick-indexed event trace
    └── replay_certifier.py     # ReplayCertificationMode — verifies runtime == replay
```

---

## 🚀 Установка

### Шаг 1 — Проверка зависимостей

```bash
# Kubernetes (kind)
command -v kind && kind --version   # kind v0.20+
command -v kubectl && kubectl version --client  # v1.28+
command -v docker && docker --version  # Docker 24+

# Python
python3 --version  # 3.10+
```

### Шаг 2 — Создание Kind-кластера

```bash
export CLUSTER_NAME="${CLUSTER_NAME:-atom-os}"
kind create cluster --name "$CLUSTER_NAME" --wait 5m
kubectl cluster-info --context "kind-$CLUSTER_NAME"
```

### Шаг 3 — Установка operator

```bash
cd /home/workspace/atom-federation-os

# CRD + RBAC + Operator
kubectl apply -f kubernetes/manifests/install.yaml

# Проверка
kubectl get crd atomclusters.atom.io
kubectl get namespaces | grep atom-system
```

### Шаг 4 — Деплой ATOMCluster

```bash
kubectl apply -f kubernetes/manifests/sample.yaml

# Статус
kubectl get atomclusters -n default
kubectl describe atomcluster demo
```

### Шаг 5 — Валидация

```bash
# Полный тест (SBS, healing, scale drift, pod kill recovery, throttle)
bash /home/workspace/atom-federation-os/validate_local.sh
```

---

## 📋 Ручная установка (без kind)

### 1. Python environment

```bash
# Установка зависимостей operator
cd /home/workspace/atom-federation-os/kubernetes/atom_operator
pip install -r requirements.txt
# kubernetes==29.0.0
# prometheus-api-client==0.5.1

# Или из корня проекта
pip install kubernetes==29.0.0 prometheus-api-client==0.5.1
```

### 2. Kubernetes manifests

```bash
# Посмотреть что установлено
kubectl get all -n atom-system
kubectl get clusters,clusterrolebindings -A

# Логи operator
kubectl logs -n atom-system -l app=atom-operator --tail=50
```

### 3. HELM установка (альтернатива)

```bash
cd /home/workspace/atom-federation-os
helm install atom-os kubernetes/helm/atom-os/ \
  --set operator.image=ghcr.io/atom-federation/atom-operator:10.0.0 \
  --set operator.replicas=3
```

---

## 🔧 Конфигурация

### Переменные окружения operator

| Переменная | Default | Описание |
|-----------|---------|----------|
| `RECONCILE_INTERVAL` | `5s` | Частота опроса ATOMCluster |
| `WATCH_NAMESPACE` | `default` | Namespace для наблюдения |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING |
| `GEB_QUORUM_SIZE` | `2` | Минимальный кворум для GEB commit |
| `REPLAY_CERTIFICATION` | `false` | Включить режим сертификации replay |
| `LOCKSTEP_MODE` | `false` | Синхронное выполнение на всех узлах |

### ATOMCluster spec

```yaml
apiVersion: atom.io/v1
kind: ATOMCluster
metadata:
  name: demo
spec:
  replicas: 3
  healthThreshold: 0.99
  maxCoherenceDrift: 0.1
  sbsViolationThreshold: 0.05
  observeInterval: 5s
```

---

## ✅ Валидация после установки

```bash
# 1. CRD установлен
kubectl get crd atomclusters.atom.io

# 2. Operator запущен
kubectl get pods -n atom-system -l app=atom-operator
# Должен быть Running

# 3. ATOMCluster создан
kubectl get atomclusters
# STATUS = Running

# 4. StatefulSet развёрнут
kubectl get sts -n default -l app=atom-node

# 5. Проверка SBS healing
kubectl scale sts atom-node -n default --replicas=1
# Operator должен восстановить replicas через ~30s

# 6. Проверка circuit breaker
kubectl patch atomclusters demo -n default \
  --type=merge -p '{"metadata":{"annotations":{"coherence_drift":"0.95"}}}'
# Operator должен выставить throttled=true
```

---

## 📊 Структура файлов

| Путь | Что делает |
|------|-----------|
| `kubernetes/manifests/install.yaml` | Namespace + SA + CRD + RBAC + ClusterRoleBinding |
| `kubernetes/manifests/deployment.yaml` | Operator StatefulSet + Service |
| `kubernetes/manifests/sample.yaml` | Пример ATOMCluster |
| `validate_local.sh` | Полный тест: CRD → operator → reconciliation → healing → scale → throttle |
| `core/deterministic.py` | DeterministicClock, DeterministicRNG, GlobalTieBreaker |
| `core/runtime/geb.py` | GlobalExecutionBarrier (GEB) — node sync |
| `orchestration/execution_gateway.py` | Сиngлтон гейтвей с mutation_context |
| `orchestration/deterministic_scheduler.py` | Hash-based scheduling, LockstepMode |
| `persistence/atomic_fs.py` | AtomicFileWrite (2-phase commit) |
| `observability/trace_ledger.py` | Глобальный tick-indexed event trace |
| `observability/replay_certifier.py` | ReplayCertificationMode |

---

## 🧪 Тестирование

```bash
# Все тесты (259 passed / 38 failed — pre-existing)
cd /home/workspace/atom-federation-os
python3 -m pytest tests/ -v --tb=short

# Только operator
python3 -m pytest tests/test_p6_federation.py -v

# Deterministic kernel
python3 -c "
from core.deterministic import DeterministicClock, DeterministicRNG
clk = DeterministicClock()
print('tick:', clk.tick())
rng = DeterministicRNG(seed=42)
print('rand:', rng.random())
"
```

---

## 🔒 Constraints (C1-C10) — обязательны

| # | Constraint | Зачем |
|---|------------|-------|
| C1 | Нет `time.time()` / `time.time_ns()` в control flow | Tick determinism |
| C2 | Нет `uuid.uuid4()` для identity | Replay determinism |
| C3 | Нет `random.*` в scheduling/execution | Deterministic scheduling |
| C4 | Нет `asyncio.sleep()` с недетерминированной задержкой | Execution ordering |
| C5 | Все filesystem операции через `AtomicFileWrite` | Atomic commits |
| C6 | Все network сообщения через `ReplayableMessageQueue` | Message ordering |
| C7 | Все tick boundaries через `GlobalExecutionBarrier` | Node synchronization |
| C8 | Нет вероятностных scheduling policies | Determinism |
| C9 | Replay produces bitwise-identical output | Certification |
| C10 | Нет модификации RL-019/020/021 deterministic kernel | Core preservation |

---

## 📖 Документация

| Документ | Описание |
|----------|----------|
| `AGENTS.md` | Карта архитектуры + инварианты + ограничения |
| `AGENTS_FUNCTIONS.md` | Описание всех агентов и их функций |
| `ATOM-META-RL-022-PRODUCTION-FINALIZATION.md` | RL-022 — production hardening |
| `ATOM-META-RL-023-FORMAL-VERIFICATION.md` | RL-023 — формальная верификация |
| `kubernetes/README.md` | Kubernetes operator documentation |
| `CONTROL_LOOP_ARCHITECTURE.md` | Архитектура control loop |
| `CHANGELOG.md` | История версий |

---

## 🧹 Очистка

```bash
kind delete cluster --name atom-os

# Или вручную
kubectl delete -f kubernetes/manifests/install.yaml
```
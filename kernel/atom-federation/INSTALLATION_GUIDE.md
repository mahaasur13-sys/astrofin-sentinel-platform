# ATOMFederationOS — Установка и описание компонентов

> ver: **1.1** | repo: `atom-federation-os` | version: `0.6.0` | updated: 2026-04-26

---

## 🧠 Что это за экосистема

Набор распределённых модулей на Python для построения AI-инфраструктуры с формальной верификацией, deterministic execution и fault tolerance.

Все модули — Python-пакеты. Единая точка входа — CLI-команда `sbs`.

---

## 📦 Установка

### Быстрая (pip)

```bash
git clone https://github.com/mahaasur13-sys/atom-federation-os.git
cd atom-federation-os
pip install -e ".[dev]"
```

### Проверка

```bash
sbs --version    # → 0.6.0
sbs verify       # → SBS verification
```

### Дополнительные профили

```bash
pip install -e ".[cli]"     # → rich-вывод в CLI
pip install -e ".[all]"     # → dev + cli
```

---

## 🗂️ Структура пакетов (20 пакетов)

```
atom-federation-os/
├── sbs/              ← System Boundary Spec (CLI-команда sbs)
├── alignment/         ← Тесты выравнивания (52 passing)
├── core/              ← Детерминированное ядро (GEB, runtime)
├── federation/        ← Gossip, Byzantine-обнаружение, trust
├── meta_control/      ← Persistence bridge, temporal gain scheduler
├── orchestration/     ← Circuit breaker, safety foundations, planning
├── persistence/       ← Atomic FS, crash consistency, WAL
├── kubernetes/        ← K8s operator, CRD, deterministic scheduler
├── observability/     ← Trace ledger, replay certifier
├── proof/            ← Temporal verification, invariant registry
├── resilience/       ← Resilience-слой
├── actuator/         ← Исполнительный слой
├── swarm/            ← Swarm intelligence
├── cluster/          ← Node management
├── dag/              ← Directed Acyclic Graph planner
├── rpc/              ← RPC-коммуникация
├── formal/           ← Formal verification foundations
├── chaos/            ← Chaos engineering
├── local-ai-stack/   ← Agent runtime (тесты)
└── consistency/      ← Consistency v2/v3 (legacy)
```

---

## 📋 Описание компонентов

### ⭐ `sbs` — System Boundary Spec (CLI)

| | |
|---|---|
| **Что это** | Инструмент формальной верификации distributed systems |
| **Зачем** | Проверка корректности при сбоях: split-brain, quorum failure, stale reads |
| **Даёт** | `sbs verify`, `sbs status`, `sbs inspect`, `sbs doctor` |
| **Версия** | 0.6.0 |
| **Тип** | REQUIRED |
| **Установка** | `pip install -e .` (автоматически через `[project.scripts]`) |

**Как работает:** Задаёшь **specification** (граничные условия системы) и **contract** (ожидаемое поведение). SBS проверяет, что система не нарушает контракт при любом сценарии сбоя.

---

### 🔧 `core` — Детерминированное ядро

| | |
|---|---|
| **Что это** | Детерминированные примитивы: часы, RNG, UUID, барьеры исполнения |
| **Зачем** | Гарантия воспроизводимости: replay == runtime |
| **Даёт** | `DeterministicClock`, `DeterministicRNG`, `GlobalExecutionBarrier` (GEB) |
| **Версия** | v10.0 (RL-022) |
| **Тип** | REQUIRED |

**GEB (GlobalExecutionBarrier):** Координирует все узлы кластера — ни один узел не начинает тик N+1, пока все не зафиксировали тик N.

---

### 🌐 `federation` — Gossip-протокол и Byzantine-защита

| | |
|---|---|
| **Что это** | P2P-коммуникация между узлами + обнаружение неисправных узлов |
| **Зачем** | Cross-node связь, eventual consistency, Byzantine fault detection |
| **Даёт** | `GossipProtocol`, Byzantine detector, PBFT consensus, trust dynamics |
| **Подпакеты** | `federation/byzantine/`, `federation/trust_weighted/`, `federation/delta_gossip/` |
| **Тип** | FEDERATION |

---

### 🧠 `meta_control` — Persistence bridge и Meta-RL управление

| | |
|---|---|
| **Что это** | Связь между v7 coherence/gains и persistence-слоем |
| **Зачем** | Обогащение решений данными из истории (decision memory, stability ledger) |
| **Даёт** | `GainModulator`, `WeightModulator`, `CoherenceEnricher`, `PersistenceBridge` |
| **Подпакеты** | `meta_control/persistence/`, `meta_control/integration/` |
| **Тип** | AI STACK |

---

### 🛡️ `orchestration` — Planning, Circuit Breaker, Safety

| | |
|---|---|
| **Что это** | Управление планированием, защита от cascade-мутаций, safety gate |
| **Зачем** | Предотвращение oscillation, drift, нестабильности при мутациях |
| **Даёт** | `CircuitBreaker` (CLOSED→OPEN→HALF), `StabilityGovernor`, `InvariantChecker`, `RollbackEngine` |
| **Подпакеты** | `orchestration/planning_observability/`, `orchestration/v8_2a_safety_foundations/` |
| **Тип** | REQUIRED |

**Circuit Breaker:** Если система «осциллирует» — блокирует мутации, даёт восстановиться. Три состояния: CLOSED (норма), OPEN (блок), HALF (частичное восстановление).

---

### 💾 `persistence` — Atomic FS и Crash Consistency

| | |
|---|---|
| **Что это** | Персистентное хранение состояния с гарантией атомарности |
| **Зачем** | Корректное восстановление после crash: нет partial writes, no data loss |
| **Даёт** | `AtomicFileWrite`, `EventStore`, `MutationLedger`, `CheckpointManager`, `WALRecoveryProtocol` |
| **Версия** | v10.0 (RL-022) |
| **Тип** | REQUIRED |

---

### ☸️ `kubernetes` — Kubernetes Operator

| | |
|---|---|
| **Что это** | K8s-оператор для управления atom-кластером |
| **Зачем** | Декларативное управление через Kubernetes API |
| **Даёт** | `ATOMController` (SBS/healing/drift/quorum/scale), CRD `AtomCluster`, deterministic pod scheduling |
| **Подпакеты** | `kubernetes/crd/`, `kubernetes/helm/atom-os/`, `kubernetes/manifests/` |
| **Тип** | CLUSTER |

---

### 📊 `observability` — Trace Ledger и Replay Certification

| | |
|---|---|
| **Что это** | Полный tracing исполнения + сертификация replay |
| **Зачем** | Доказать, что replay produces bitwise-identical output |
| **Даёт** | `TraceLedger` (global tick ordering), `ReplayCertifier` (REPLAY_CERTIFICATION_MODE) |
| **Тип** | OBSERVABILITY |

---

### ⏱️ `proof` — Temporal Verification и Invariants

| | |
|---|---|
| **Что это** | Формальная верификация темпоральных свойств системы |
| **Зачем** | Доказать, что система удовлетворяет глобальным инвариантам |
| **Даёт** | `TemporalVerifier`, `InvariantRegistry`, `ProofChain`, `CausalProofGraph` |
| **Тесты** | 259 passing (alignment + unit) |
| **Тип** | VERIFICATION |

---

### 🔌 `resilience` — Resilience Layer

| | |
|---|---|
| **Что это** | Слой восстановления после сбоев |
| **Зачем** | Graceful degradation, fault isolation |
| **Тип** | SECURITY |

---

### 🔗 `actuator` — Actuator Layer

| | |
|---|---|
| **Что это** | Исполнительный слой — применение решений к системе |
| **Тип** | SYSTEM |

---

### 🐝 `swarm` — Swarm Intelligence

| | |
|---|---|
| **Что это** | Swarm-поведение для групп агентов |
| **Тип** | AI STACK |

---

### 🗺️ `cluster` — Node Management

| | |
|---|---|
| **Что это** | Управление узлами кластера |
| **Подпакеты** | `cluster/node/`, `cluster/shared/` |
| **Тип** | CLUSTER |

---

### 📐 `dag` — DAG Planner

| | |
|---|---|
| **Что это** | Long-horizon planning через направленный ациклический граф |
| **Статус** | Phase 2 pending |
| **Тип** | AI STACK |

---

### 🔄 `rpc` — RPC Communication

| | |
|---|---|
| **Что это** | RPC-протокол для межсервисной коммуникации |
| **Тип** | SYSTEM |

---

### 🔒 `formal` — Formal Verification Foundations

| | |
|---|---|
| **Что это** | Базовые формальные примитивы для верификации |
| **Тип** | VERIFICATION |

---

### 💥 `chaos` — Chaos Engineering

| | |
|---|---|
| **Что это** | Injected failure testing (chaos testing) |
| **Статус** | HARDENING PHASE 2 pending |
| **Тип** | SECURITY |

---

### 🧪 `alignment` — Alignment Testing Suite

| | |
|---|---|
| **Что это** | Тесты выравнивания (alignment tests) |
| **Зачем** | Проверка, что система ведёт себя корректно (52 passing) |
| **Даёт** | `test_gsct.py`, `test_adlr.py`, drift detection tests |
| **Тип** | VERIFICATION (TEST) |

---

### 🧩 `consistency` / `consistency_v2` / `consistency_v3`

| | |
|---|---|
| **Что это** | Legacy consistency layers (v1, v2, v3) |
| **Тип** | LEGACY |

---

## 📊 Таблица «Профиль → Компоненты»

| Компонент | Verification | Federation | Cluster | AI Stack | Security |
|-----------|:---:|:---:|:---:|:---:|:---:|
| `sbs` | ✅ | — | — | — | — |
| `core` (GEB) | ✅ | ✅ | ✅ | — | ✅ |
| `federation` | — | ✅ | ✅ | — | ✅ |
| `meta_control` | — | — | — | ✅ | — |
| `orchestration` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `persistence` | ✅ | ✅ | ✅ | — | ✅ |
| `kubernetes` | — | ✅ | ✅ | — | — |
| `observability` | ✅ | ✅ | ✅ | — | — |
| `proof` | ✅ | ✅ | ✅ | ✅ | — |
| `resilience` | — | ✅ | ✅ | — | ✅ |
| `actuator` | — | — | — | ✅ | — |
| `swarm` | — | — | — | ✅ | — |
| `cluster` | — | ✅ | ✅ | — | — |
| `alignment` (tests) | ✅ | — | — | ✅ | — |
| `chaos` | — | — | — | — | ✅ |

---

## 🔗 Архитектура связей

```
        ┌─────────────────────────────────────────────┐
        │              sbs (CLI)                      │
        └──────────────┬──────────────────────────────┘
                       │ verify / status / inspect
        ┌──────────────▼──────────────────────────────┐
        │     proof (Temporal Verification)          │
        │  InvariantRegistry / CausalProofGraph      │
        └──────────────┬──────────────────────────────┘
                       │ enforces
        ┌──────────────▼──────────────────────────────┐
        │   orchestration (CircuitBreaker + Governor) │
        │      StabilityGovernor / InvariantChecker   │
        └──────────────┬──────────────────────────────┘
                       │ gates mutation
        ┌──────────────▼──────────────────────────────┐
        │     core (Deterministic Kernel)             │
        │  GEB / DeterministicClock / ExecutionGateway│
        └──────────────┬──────────────────────────────┘
                       │ cross-node sync
        ┌──────────────▼──────────────────────────────┐
        │          federation (Gossip + PBFT)          │
        │  ByzantineDetector / TrustWeighted / SWIM   │
        └──────────────┬──────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   kubernetes                  observability
   (ATOMController)           (TraceLedger /
                                ReplayCertifier)
          │                         │
          ▼                         ▼
   persistence                 meta_control
   (AtomicFS / WAL)            (PersistenceBridge)
```

---

## ✅ Проверка установки

```bash
# 1. SBS CLI
sbs --version    # → 0.6.0
sbs verify       # → verification report

# 2. Python imports
python -c "import sbs, alignment, core, federation, orchestration; print('OK')"

# 3. Alignment tests
cd /home/workspace/atom-federation-os
pytest alignment/ -v --tb=short 2>&1 | tail -20

# 4. SBS tests
pytest sbs/tests/ -v --tb=short 2>&1 | tail -20
```

---

## 🔢 Зависимости

| Зависимость | Версия | Для чего |
|-------------|--------|----------|
| Python | ≥3.10 | Все модули |
| pytest | ≥8.0 | Тесты |
| pytest-asyncio | ≥0.23 | Async-тесты |
| rich | ≥13.0 | CLI-вывод |
| ruff | ≥0.3 | Линтинг |
| hypothesis | ≥6.90 | Property-based testing |

---

## 📌 Version History

| Версия | Дата | Что изменилось |
|--------|------|---------------|
| 1.1 | 2026-04-26 | Обновлена структура (v10.0), добавлены все 20 пакетов |
| 1.0 | 2026-04-16 | Initial release |

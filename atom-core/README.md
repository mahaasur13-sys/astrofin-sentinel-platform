# ATOM Core — Monorepo

> ⚠️ **Не удалять.** Это **живой Go-роутер** для AstroFinSentinelV5 (`packages/atom-router/`).
> Используется для: reflection-based routing, belief propagation, K8s operator (ROMA bridge pods).
> Замены нет. Если нужна правка — см. `Known Issues` ниже.

Координационный слой для AstroFinSentinelV5. Многоагентная система маршрутизации с deterministic execution.

## Архитектура

```
atom-core/
├── packages/
│   ├── atom-kernel/        # Deterministic execution engine
│   ├── atom-operator/      # K8s operator (Pod management)
│   ├── atom-federation/    # Multi-agent belief propagation
│   └── atom-router/        # Reflection-based routing
└── go.work                 # Workspace (Go 1.21+)
```

## Пакеты

| Пакет | Путь | Описание |
|-------|------|----------|
| atom-kernel | `pkg/deterministic/` | Deterministic RNG, GlobalExecutionSequencer, Clock |
| atom-operator | `cmd/` | K8s operator для ROMA bridge pods |
| atom-federation | `pkg/bridge/` | Belief propagation между агентами |
| atom-router | `pkg/reflection/` | ReRouter с reflection-based quality scoring |

## Сборка

```bash
# Требуется Go 1.21+
go build ./packages/atom-federation/... \
         ./packages/atom-kernel/... \
         ./packages/atom-operator/... \
         ./packages/atom-router/...
```

Или через make:

```bash
cd ~/mono-migration/atom-core
make build
```

## Тестирование

```bash
go test ./packages/atom-kernel/... 2>&1
```

## Интеграция с AstroFinSentinelV5

```
AstroFinSentinelV5 (Python)
         │
         ▼ ROMA bridge (port 3000)
    ┌─────────────┐
    │ atom-core   │◄── K8s operator
    │ (Go)        │
    └─────────────┘
         │
         ▼
  ROMA execution → Kubernetes Jobs
```

- **ROMA bridge**: `http://localhost:8050` → `http://localhost:3000`
- **atom-operator**: управляет lifecycle ROMA bridge pods в kind cluster `atom-test`
- **belief propagation**: `atom-federation/pkg/bridge/` — обновляет BeliefState агентов

## Контракты

```go
// atom-router/pkg/contracts/types.go
type RouteDecision struct {
    Tick     int64
    NodeID   string
    Quality  float64
    Decision string
}

type ReflectionResult struct {
    AgentID   string
    Success   bool
    Quality   float64
    Confidence float64
}
```

## Deterministic API

```go
// GlobalExecutionSequencer
type GlobalExecutionSequencer struct {
    nodeID    string
    tickOrder []string
    Timestamp int64  // wallclock seed
    mu        sync.Mutex
}

func (s *GlobalExecutionSequencer) Now() int64   // tick + timestamp
func (s *GlobalExecutionSequencer) GetRNG(task string) *DeterministicRNG

// DeterministicRNG
func (r *DeterministicRNG) Uint64() uint64
func (r *DeterministicRNG) Float64() float64
func (r *DeterministicRNG) Float64Range(min, max float64) float64
```

## Known Issues

- [x] `Next()` → `Uint64()` исправлено
- [x] `GlobalExecutionSequencer.Timestamp` добавлено
- [x] `GlobalExecutionSequencer.Now()` добавлено
- [x] `RouteDecision` импортирован из contracts
- [x] `belief.go` stubs для goa/routerapi
- [ ] MASFactory DISABLED (legacy)

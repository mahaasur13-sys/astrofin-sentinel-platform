# ADR-001: Distributed Multi-Agent Architecture

**Status:** Proposed  
**Date:** 2026-07-18  
**Author:** Felix (mahaasur13-sys) + Zo Computer  
**Supersedes:** In-process asyncio orchestration (`orchestration/sentinel_v5.py`)

---

## 1. Context

### Current State

| Layer | Mechanism | Limitation |
|-------|-----------|-----------|
| Agent execution | `asyncio.gather()` in single process | No horizontal scaling; CPU-bound agents block the event loop |
| Communication | Direct function calls (`run_*_agent(state)`) | Tight coupling; no async message passing |
| State sharing | Python dict passed by reference | No serialization boundary; cannot distribute |
| Error isolation | `return_exceptions=True` in gather | One agent crash kills the orchestrator's gather; no retry |
| LLM routing | Sync call to `route()` in `BaseAgent.generate()` | No circuit breaker; OpenRouter outage = cascading failure |

### Vision (Sprint 3-4)

Distribute AstroFin across multiple processes/containers, connected by a **message broker**
(Redis Pub/Sub initially, RabbitMQ for production), with rich lifecycle management
and circuit-breaker-based resilience.

---

## 2. Decision: Hub-and-Spoke with Event-Driven Worker Pool

### 2.1 Topology

```
                        ┌──────────────────────────┐
                        │     Message Broker        │
                        │   (Redis / RabbitMQ)      │
                        └──────┬────────┬───────────┘
                               │        │
              ┌────────────────┘        └────────────────┐
              ▼                                          ▼
    ┌─────────────────┐                    ┌─────────────────────┐
    │  SupervisorAgent │                    │   Worker Pool       │
    │  (Hub)           │                    │                     │
    │  - Task dispatch │                    │ ┌───────────────┐   │
    │  - Result merge  │                    │ │ Fundamental   │   │
    │  - Health check  │                    │ │ Worker        │   │
    │  - Circuit break │                    │ ├───────────────┤   │
    └────────┬─────────┘                    │ │ Macro Worker  │   │
             │                              │ ├───────────────┤   │
             │ receives results via         │ │ Quant Worker  │   │
             │ `agent.results.*` channel    │ ├───────────────┤   │
             │                              │ │ Synthesis     │   │
             │                              │ │ Worker        │   │
             │                              │ ├───────────────┤   │
             │                              │ │ HMMRegime     │   │
             │                              │ │ Worker        │   │
             └──────────────────────────────│ └───────────────┘   │
                                            └─────────────────────┘
```

**Chose Hub-and-Spoke over Choreography** because:
- AstroFin has a natural **synthesis step** (one agent needs all results)
- **SupervisorAgent** simplifies error handling and timeout management
- Easier to add Circuit Breakers at one point (Supervisor) vs. N peer agents
- Status dashboard needs a single aggregation point

### 2.2 Communication Protocol

| Channel | Direction | Payload |
|---------|-----------|---------|
| `agent.tasks.{type}` | Supervisor → Worker | `TaskEnvelope { task_id, agent_type, state_snapshot, deadline_epoch }` |
| `agent.results.{type}` | Worker → Supervisor | `ResultEnvelope { task_id, agent_type, response: AgentResponse, elapsed_ms }` |
| `agent.heartbeat.{worker_id}` | Worker → Supervisor | `{ worker_id, status, last_task_at }` every 15s |
| `agent.control.broadcast` | Supervisor → All | `{ command: "pause"|"resume"|"drain", reason }` |

**Serialization:** JSON for readability; msgpack for production (protobuf if adopting gRPC).

### 2.3 Circuit Breaker for LLM Calls

```python
# core/circuit_breaker.py (new module)
class LLMCircuitBreaker:
    """3-state breaker: CLOSED → OPEN → HALF_OPEN → CLOSED.

    Triggers on: 5 failures in 60s → OPEN (30s cooldown).
    Half-open: allows 1 probe request; success → CLOSED, failure → OPEN.
    """

    def __init__(self, name: str, failure_threshold: int = 5, cooldown: float = 30.0):
        self.name = name
        self._state = CircuitState.CLOSED
        self._failures = deque(maxlen=failure_threshold)
        self._cooldown = cooldown
        self._opened_at = 0.0

    async def call(self, fn, *args, **kwargs):
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at > self._cooldown:
                self._state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        try:
            result = await fn(*args, **kwargs)
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
            return result
        except Exception:
            self._failures.append(time.monotonic())
            if len(self._failures) >= self._failures.maxlen:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
            raise
```

**Integration points:**
- `core/llm_router.py::cloud_llm()` — wrap OpenRouter call
- Every agent's `generate()` — wrap all LLM calls
- Supervisor → Worker task submission — wrap broker publish

---

## 3. Agent Role Distribution

| Current Agent | New Role | Responsibilities |
|---------------|----------|-----------------|
| **SupervisorAgent** (new) | **Supervisor** | Task dispatch, result aggregation, health monitoring, circuit breaker orchestration, deadline enforcement |
| SynthesisAgent | **Router** | Merges 13 worker results → final `AgentResponse`; calls `resolve_conflict()` on KARL conflicts |
| FundamentalAgent | **Worker** | Domain-specific analysis; receives `TaskEnvelope`, returns `ResultEnvelope` |
| QuantAgent | **Worker** | ML + backtest; heaviest computation — may benefit from GPU worker pool |
| MacroAgent | **Worker** | Macro data (VIX, DXY); I/O-bound → suitable for async pool |
| OptionsFlowAgent | **Worker** | Options data; I/O-bound |
| SentimentAgent | **Worker** | NLP/social; LLM-heavy |
| TechnicalAgent | **Worker** | TA indicators; CPU-light |
| HMMRegimeAgent | **Worker** | Regime classification; CPU-bound |
| Bull/Bear Researchers | **Worker** | Narrative generation; LLM-light |
| ElectoralAgent | **Worker** | Muhurta timing; astro-compute |
| BradleyAgent, GannAgent, CycleAgent, TimeWindowAgent | **Worker** | Astro sub-computations; lightweight |
| KARLSynthesisAgent | **Validator** | Post-hoc validation: checks signal consistency, applies KARL rules |
| LLM Router | **Infrastructure** | Shared service: classifies prompts, routes to Ollama/OpenRouter with circuit breaker |

---

## 4. Agent Lifecycle State Machine

```
                    ┌──────────┐
           ┌───────►│  IDLE    │◄──────────────┐
           │        └────┬─────┘               │
           │             │ receive(TaskEnvelope)│
           │             ▼                      │
           │        ┌─────────┐                │
           │        │ SPAWNED │                │
           │        └────┬────┘                │
           │             │ init()              │
           │             ▼                     │
           │        ┌─────────┐    timeout     │
           │        │ RUNNING ├──────────────► │
           │        └──┬───┬──┘               │
           │    result │   │ error             │
           │           ▼   ▼                   │
           │    ┌─────────────┐               │
           │    │  COMPLETED  │               │
           │    │  (SUCCESS)  │               │
           │    └──────┬──────┘               │
           │           │ publish(Result)      │
           │           ▼                      │
           │    ┌─────────────┐               │
           │    │  AWAITING   │               │
           │    │  SYNTHESIS  │               │
           │    └──────┬──────┘               │
           │           │ synthesis complete   │
           │           ▼                      │
           │    ┌─────────────┐               │
           └────┤  TERMINATED │───────────────┘
                └─────────────┘
                    (graceful shutdown)
```

| State | Entry Action | Exit Action | Timeout |
|-------|-------------|-------------|---------|
| **IDLE** | Register heartbeat, subscribe to `agent.tasks.*` | — | ∞ |
| **SPAWNED** | Load instructions.md, init RAG index, warm LLM model | — | 10s |
| **RUNNING** | Execute `run(state)`, stream partial results via channel | Publish `ResultEnvelope` or `ErrorEnvelope` | 60s per agent |
| **COMPLETED** | Log result, increment metrics | — | — |
| **AWAITING_SYNTHESIS** | Wait for all agents in batch; receive synthesis trigger | — | 30s |
| **TERMINATED** | Drain queue, flush logs, close broker connections | Unsubscribe from channels | 5s |

---

## 5. Failure Modes & Resilience

| Failure | Detection | Recovery |
|---------|-----------|----------|
| LLM timeout (OpenRouter) | Circuit breaker (5 failures / 60s) | Fallback to Ollama local; Supervisor retries with degraded model |
| Worker crash | Heartbeat miss (15s) | Supervisor re-spawns worker; task re-queued with TTL |
| Broker partition | Supervisor detects stale heartbeats | Raise alert; agents buffer results locally (max 100 messages) |
| Supervisor crash | Worker heartbeats unanswered → self-terminate after 60s | Orchestrator restarted by process supervisor; workers reconnect |
| Dead letter (task times out) | Task TTL exceeded | Supervisor discards, logs, records in `audit_log.dead_letters` |

---

## 6. Implementation Plan (Sprint 3-4)

### Sprint 3 (Interface Layer)
1. Add `on_message(envelope: TaskEnvelope) -> ResultEnvelope` to `BaseAgent`
2. Add `publish_event(channel, payload)` to `BaseAgent`
3. Create `core/circuit_breaker.py` (LLM + Broker C/B)
4. Create `orchestration/message_broker.py` (Redis abstraction)
5. Create `orchestration/supervisor_agent.py` (new Hub)
6. Run existing 534 tests — must still pass (in-process compat)

### Sprint 4 (Distribution)
7. Move agents to worker pool (each agent = separate coroutine with its own channel)
8. Wire Redis Pub/Sub for inter-process communication
9. Add dead-letter queue and retry policy
10. Performance baseline: measure latency improvement vs. current `asyncio.gather()`
11. Add `docker-compose.workers.yml` (scalable worker instances)

### Backward Compatibility
All changes are **additive** — existing `run(state) -> AgentResponse` interface preserved.
Workers extend `BaseAgent` with optional `on_message()` / `publish_event()` methods.
In-process mode (`orchestration/sentinel_v5.py`) continues to work unchanged.

---

## 7. Consequences

**Positive:**
- Horizontal scaling: each agent type can have N workers
- Resilience: circuit breakers, retry, dead-letter queues
- Observability: per-channel tracing, heartbeat dashboards
- Testability: agents become isolated units connected by contract (envelope)

**Negative:**
- Added complexity: broker setup, envelope serialization
- Latency overhead: ~5-10ms per broker hop (acceptable for 1-15s agent run times)
- Operational burden: Redis/RabbitMQ must be managed, monitored, backed up

**Risks:**
- Schema evolution: `TaskEnvelope` / `ResultEnvelope` must be versioned (include `schema_version` field)
- Debug complexity: distributed tracing (Tempo/Jaeger) is now mandatory, not optional

---

## 8. References

- [Nygard, "Release It!" — Circuit Breaker pattern](https://pragprog.com/titles/mnee2/release-it-second-edition/)
- [Redis Pub/Sub documentation](https://redis.io/docs/latest/develop/interact/pubsub/)
- [RabbitMQ tutorial — Work Queues](https://www.rabbitmq.com/tutorials/tutorial-two-python)
- [PRODUCTION_BACKLOG.md § P3-06, P3-07, P5-05 — related performance/distribution tasks]

---

*ADR created: 2026-07-18. Next review: Sprint 3 kickoff.*

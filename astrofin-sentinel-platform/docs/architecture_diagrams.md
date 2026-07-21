# AstroFin Sentinel — Architecture Diagrams

> Generated: 2026-07-18 | Format: Mermaid.js | ADR: [ADR-001](./ADR-001-distributed-multi-agent.md)

---

## 1. Sequence Diagram: Full Request Lifecycle

```mermaid
sequenceDiagram
    participant UI as React UI (Vite :5173)
    participant API as FastAPI (api/main.py :8000)
    participant Broker as Message Broker (Redis)
    participant Sup as SupervisorAgent (Hub)
    participant FW as FundamentalWorker
    participant QW as QuantWorker
    participant MW as MacroWorker
    participant SW as SynthesisWorker
    participant CB as Circuit Breaker
    participant LLM as LLM Router (Ollama / OpenRouter)

    UI->>API: POST /api/v1/agent/run {agentId, prompt}
    API->>Sup: dispatch_task(TaskEnvelope)

    par Parallel Agent Dispatch
        Sup->>Broker: publish(agent.tasks.fundamental, task)
        Sup->>Broker: publish(agent.tasks.quant, task)
        Sup->>Broker: publish(agent.tasks.macro, task)
        Broker-->>FW: agent.tasks.fundamental
        Broker-->>QW: agent.tasks.quant
        Broker-->>MW: agent.tasks.macro
    end

    par Worker Execution
        FW->>FW: load instructions.md
        FW->>FW: init RAG index
        FW->>CB: call(LLM.generate, prompt)
        CB->>LLM: route(prompt) → Ollama/OpenRouter
        LLM-->>CB: response
        CB-->>FW: LLM result
        FW->>Broker: publish(agent.results.fundamental, ResultEnvelope)

        QW->>QW: load instructions.md
        QW->>QW: run_ml_model(state)
        QW->>Broker: publish(agent.results.quant, ResultEnvelope)

        MW->>MW: load instructions.md
        MW->>MW: fetch VIX/DXY data
        MW->>Broker: publish(agent.results.macro, ResultEnvelope)
    end

    Broker-->>Sup: agent.results.* (collect 3/3)

    Sup->>SW: dispatch_synthesis(task_id, results[])
    SW->>SW: merge 13 agent signals
    SW->>SW: resolve_conflict(KARL)
    SW->>Sup: final AgentResponse{sig, confidence}

    Sup->>CB: call(LLM.generate, augmented_prompt)
    CB->>LLM: route(augmented) → autoselect
    LLM-->>CB: final LLM response
    CB-->>Sup: enriched response

    Sup->>API: final_result
    API-->>UI: 200 {result, agents_stats, latency_ms}
```

---

## 2. State Diagram: Agent Lifecycle

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> SPAWNED: on_message(TaskEnvelope)

    SPAWNED --> RUNNING: init() complete
    SPAWNED --> TERMINATED: init() timeout (10s)

    RUNNING --> COMPLETED: result ready
    RUNNING --> TERMINATED: timeout (60s) or crash

    COMPLETED --> AWAITING_SYNTHESIS: publish(ResultEnvelope)

    AWAITING_SYNTHESIS --> TERMINATED: synthesis complete / batch finished

    TERMINATED --> [*]: flush logs, close broker

    note right of RUNNING
        Circuit Breaker wraps
        every LLM call:
        CLOSED → OPEN → HALF_OPEN → CLOSED
    end note

    note right of AWAITING_SYNTHESIS
        Supervisor waits for
        N/N results or deadline.
        Missing → deadline → degrade
        that agent (NEUTRAL, conf=0)
    end note
```

---

## 3. Component Diagram: System Topology

```mermaid
graph TB
    subgraph "Client Layer"
        UI[React UI<br/>Vite :5173]
    end

    subgraph "API Gateway"
        FastAPI[FastAPI<br/>api/main.py :8000]
        CORS[CORS Middleware]
    end

    subgraph "Message Bus"
        Broker[Redis Pub/Sub<br/>agent.tasks.*<br/>agent.results.*<br/>agent.heartbeat.*]
    end

    subgraph "Supervisor (Hub)"
        Sup[SupervisorAgent]
        Dispatch[Task Dispatcher]
        Collector[Result Collector]
        Health[Health Monitor]
        CB[Circuit Breaker]
    end

    subgraph "Worker Pool"
        FW[FundamentalWorker<br/>weight: 20%]
        QW[QuantWorker<br/>weight: 20%]
        MW[MacroWorker<br/>weight: 15%]
        OFW[OptionsFlowWorker<br/>weight: 15%]
        SW[SentimentWorker<br/>weight: 10%]
        TW[TechnicalWorker<br/>weight: 10%]
        SynW[SynthesisWorker<br/>Router]
    end

    subgraph "LLM Infrastructure"
        Ollama[Ollama<br/>llama3.2:1b<br/>local]
        OpenRouter[OpenRouter<br/>auto-model<br/>cloud]
    end

    UI --> FastAPI
    FastAPI --> Sup
    Sup --> Broker
    Broker --> FW
    Broker --> QW
    Broker --> MW
    Broker --> OFW
    Broker --> SW
    Broker --> TW
    FW --> CB
    QW --> CB
    MW --> CB
    CB --> Ollama
    CB --> OpenRouter
    Sup --> SynW

    style CB fill:#f96,stroke:#333
    style Broker fill:#9cf,stroke:#333
    style Sup fill:#6f6,stroke:#333
```

---

## 4. Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> CLOSED

    CLOSED --> OPEN: failures ≥ threshold (5 in 60s)
    OPEN --> HALF_OPEN: cooldown expired (30s)
    HALF_OPEN --> CLOSED: probe request succeeds
    HALF_OPEN --> OPEN: probe request fails

    note right of CLOSED
        Normal operation.
        Count failures in
        60s sliding window.
    end note

    note right of OPEN
        Fast-fail all requests.
        Return CircuitOpenError.
        Agent enters degraded mode.
    end note

    note right of HALF_OPEN
        Allow 1 (one) probe request.
        Success → CLOSED.
        Failure → OPEN.
    end note
```

---

## 5. Deployment Diagram (Sprint 4 Target)

```mermaid
graph TB
    subgraph "docker-compose.workers.yml"
        API[fastapi:8000]
        Redis[redis:6379]
        Sup[supervisor:1]
        W1[fundamental-worker:2]
        W2[quant-worker:2]
        W3[macro-worker:1]
        W4[synthesis-worker:1]
        Ollama[ollama:11434]
    end

    subgraph "External"
        OpenRouter[OpenRouter API]
    end

    API --> Sup
    Sup --> Redis
    Redis --> W1
    Redis --> W2
    Redis --> W3
    Redis --> W4
    W1 --> Ollama
    W2 --> OpenRouter
    W3 --> Ollama
    W4 --> Ollama

    style Redis fill:#9cf,stroke:#333
    style Sup fill:#6f6,stroke:#333
```

---

*Diagrams rendered with Mermaid.js. View in GitHub Markdown preview or any Mermaid-compatible viewer.*

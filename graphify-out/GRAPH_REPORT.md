# Graph Report — Compact (workspace, 2026-06-17)

> Compact form of `GRAPH_REPORT.md`. Full per-community blocks preserved in `GRAPH_REPORT.full.md`.
> Top-50 communities by node count are shown in full; the rest are summarised in the index.

## Quick Stats
- Files: 2,990 · ~1,697,459 words
- Nodes: 38,682 · Edges: 62,196 · Communities: 2,702 (2,285 shown)
- Extraction: 85% EXTRACTED · 15% INFERRED (9,601 edges, avg conf 0.52) · 0% AMBIGUOUS
- Token cost: 0 in / 0 out

## God Nodes (most connected - your core abstractions)
1. `AgentResponse` - 348 edges
2. `SignalDirection` - 321 edges
3. `BaseAgent` - 254 edges
4. `EphemerisUnavailableError` - 210 edges
5. `RiskEngineV2` - 151 edges
6. `DeterministicClock` - 134 edges
7. `DeterministicUUIDFactory` - 115 edges
8. `StrategyEvaluator` - 106 edges
9. `RiskConfigV2` - 103 edges
10. `MarketState` - 95 edges

## Surprising Connections (you probably didn't know these)
- `Any` --uses--> `EventType`  [INFERRED]
  AsurDev/acos/events/event.py → home-cluster-iac/acos/events/types.py
- `DeterministicTraceRecorder` --uses--> `ExecutionResult`  [INFERRED]
  AsurDev/acos/recorder/recorder.py → home-cluster-iac/acos/contracts/trace_contract.py
- `StateStore` --uses--> `StateStore`  [INFERRED]
  AsurDev/admission_controller/probabilistic.py → roma-execution-bridge/durability/state_store.py
- `Backend` --uses--> `WindowEngine`  [INFERRED]
  AsurDev/feature_pipeline/builder.py → home-cluster-iac/feature_pipeline/window_engine.py
- `StateStore` --uses--> `StateStore`  [INFERRED]
  AsurDev/scheduler_v3/api.py → roma-execution-bridge/durability/state_store.py

## Import Cycles
- 1-file cycle: `AsurDev/acos/storage/schema.py -> AsurDev/acos/storage/schema.py`
- 1-file cycle: `AsurDev/feature_pipeline/backfill.py -> AsurDev/feature_pipeline/backfill.py`
- 1-file cycle: `AsurDev/feature_pipeline/exporter.py -> AsurDev/feature_pipeline/exporter.py`
- 1-file cycle: `AsurDev/feature_pipeline/window_engine.py -> AsurDev/feature_pipeline/window_engine.py`
- 1-file cycle: `AsurDev/load_test/workload/generator.py -> AsurDev/load_test/workload/generator.py`
- 1-file cycle: `AsurDev/ml_engine/dataset/builder.py -> AsurDev/ml_engine/dataset/builder.py`
- 1-file cycle: `agents/_impl/technical_agent.py -> agents/_impl/technical_agent.py`
- 1-file cycle: `agents/astro_council_agent.py -> agents/astro_council_agent.py`
- 1-file cycle: `astrofin-sentinel-v5/agents/_impl/technical_agent.py -> astrofin-sentinel-v5/agents/_impl/technical_agent.py`
- 1-file cycle: `astrofin-sentinel-v5/agents/astro_council_agent.py -> astrofin-sentinel-v5/agents/astro_council_agent.py`
- 1-file cycle: `astrofin-sentinel-v5/astrology/vedic.py -> astrofin-sentinel-v5/astrology/vedic.py`
- 1-file cycle: `astrofin-sentinel-v5/backtest/engine.py -> astrofin-sentinel-v5/backtest/engine.py`
- 1-file cycle: `astrofin-sentinel-v5/core/ephemeris.py -> astrofin-sentinel-v5/core/ephemeris.py`
- 1-file cycle: `astrofin-sentinel-v5/core/houses.py -> astrofin-sentinel-v5/core/houses.py`
- 1-file cycle: `astrofin-sentinel-v5/core/online_trainer.py -> astrofin-sentinel-v5/core/online_trainer.py`
- 1-file cycle: `astrofin-sentinel-v5/core/panchanga.py -> astrofin-sentinel-v5/core/panchanga.py`
- 1-file cycle: `astrofin-sentinel-v5/integrations/__init__.py -> astrofin-sentinel-v5/integrations/__init__.py`
- 1-file cycle: `astrofin-sentinel-v5/mas_factory/visualizer.py -> astrofin-sentinel-v5/mas_factory/visualizer.py`
- 1-file cycle: `astrofin-sentinel-v5/meta_rl/calibration.py -> astrofin-sentinel-v5/meta_rl/calibration.py`
- 1-file cycle: `astrofin-sentinel-v5/muhurtha.py -> astrofin-sentinel-v5/muhurtha.py`

## Community Hub Index (by size)

| Rank | ID | Nodes | Cohesion | Top members |
|---:|---:|---:|---:|---|
| 1 | [Community 1](#c-1) | 235 | 0.01 | SignalDirection, RAGRetriever, SignalDirection, _load_weights(), AstroFin Sentinel v5 — Synthesis Agent AstroCouncil: координатор всех агентов, … (+4) |
| 2 | [Community 0](#c-0) | 227 | 0.01 | AgentResponse, AstroCouncilAgent, _build_agent_weights(), AstroFin Sentinel v5 — AstroCouncil Agent Главный координатор всех аналитических, Параллельно запускает Thompson-selected суб-агентов.          If context contain, … (+3) |
| 3 | [Community 2](#c-2) | 127 | 0.02 | AgentResponse, Any, CompromiseAgent, _next_long(), _next_short(), … (+3) |
| 4 | [Community 4](#c-4) | 115 | 0.02 | agents._impl.types — Unified types for AstroFin Sentinel v5., Map signal to numeric score for weighted calculation., Final trading signal from weighted agent responses., Signal, TradingSignal, … (+3) |
| 5 | [Community 6](#c-6) | 88 | 0.02 | Any, AtomicLedgerWriter, Append entry to WAL file.         WAL is fsync'd to ensure durability., Get hash of last committed entry (or GENESIS for empty)., Compute deterministic hash of WAL entry., … (+3) |
| 6 | [Community 11](#c-11) | 83 | 0.04 | AlignmentSnapshot, PolicyAction, BudgetDecision, CoherenceViolation, Raised when S-CI is violated (hard gate triggered)., … (+3) |
| 7 | [Community 26](#c-26) | 79 | 0.04 | AgentBelief, AgentBeliefHistory, AgentPool, AgentSelectionLog, AgentSignal, … (+3) |
| 8 | [Community 8](#c-8) | 74 | 0.03 | QuorumCertificate, Any, QuorumCertificate, VoteRecord, Any, … (+3) |
| 9 | [Community 17](#c-17) | 73 | 0.03 | Any, BasketMetrics, BasketEvaluator, correlation_penalty_matrix(), diversification_bonus(), … (+4) |
| 10 | [Community 13](#c-13) | 72 | 0.03 | Call, Any, ExecutionGateway, ExecutionGateway, Single mandatory entry point for ALL state mutations., … (+3) |
| 11 | [Community 10](#c-10) | 71 | 0.04 | CausalOrderDriftDetector, CompositeDriftReport, DriftEngine, DriftSeverity, DriftType, … (+3) |
| 12 | [Community 18](#c-18) | 71 | 0.03 | AgentResponse, BullResearcherAgent, Bull Researcher Agent — bullish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 13 | [Community 7](#c-7) | 70 | 0.03 | Any, DecisionRecord, Any, InvariantRegistry, Any, … (+3) |
| 14 | [Community 16](#c-16) | 69 | 0.05 | Branch, BranchPoint, BranchStatus, BranchStore, branch.py — v10.1 Causal Convergence Layer  Data models for branching-aware exec, … (+4) |
| 15 | [Community 12](#c-12) | 69 | 0.03 | AgentResponse, AstroCouncilAgent, AstroCouncilAgent — координационный слой астро-домена.  Агрегирует сигналы от Br, Совет астро-агентов с взвешенным голосованием., AgentResponse, … (+3) |
| 16 | [Community 5](#c-5) | 67 | 0.04 | ACOSContext, ACOSDecisionRequest, ACOSDecisionResponse, ACOSDecisionResult, ACOSGovernanceKernel, … (+3) |
| 17 | [Community 20](#c-20) | 67 | 0.03 | DriftController, DriftSnapshot, DriftStatus, v6.8 — Model–Reality Drift Controller.  Drift = |SelfModel(t) − Reality(t)|  Con, Compute drift and apply correction if threshold is breached.          Returns Dr, … (+3) |
| 18 | [Community 21](#c-21) | 66 | 0.04 | Any, ChaosScenario, Verdict, Any, ChaosScenario, … (+3) |
| 19 | [Community 3](#c-3) | 65 | 0.03 | tests/test_risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 Tests ==================, TestDrawdownKillSwitch, TestExposureControl, TestIntegration, TestLiquidityCheck, … (+3) |
| 20 | [Community 45](#c-45) | 64 | 0.04 | TemplateAgent, agent(), happy_state(), tests/_template_agent_test.py ============================== Canonical test temp, Wrong types in known fields must not raise., … (+5) |
| 21 | [Community 14](#c-14) | 61 | 0.05 | TemporalVerificationReport, WeightDelta, ProofChain, StabilityMetrics, TemporalVerificationReport, … (+3) |
| 22 | [Community 30](#c-30) | 60 | 0.05 | Any, Path, Path, Any, _act_stage(), … (+3) |
| 23 | [Community 28](#c-28) | 57 | 0.06 | DAGHashMode, SemanticProof, DAGHashMode, DAGHashMode, ProjectionStep dataclass and field ordering., … (+4) |
| 24 | [Community 43](#c-43) | 55 | 0.05 | cancel_task(), get_cb_registry(), get_circuit_breaker(), get_circuit_breakers(), get_queue_stats(), … (+3) |
| 25 | [Community 15](#c-15) | 51 | 0.03 | Any, Any, AtomicFileWrite, AtomicMultiFileWrite, DeterministicFsOrderingGuard, … (+3) |
| 26 | [Community 29](#c-29) | 50 | 0.03 | Jepsen-style invariant tests for SBS v1.  Tests verify that GlobalInvariantEngin, TestFailureClassifier, TestGlobalInvariantEngine, TestLayerState, TestSystemContract, … (+3) |
| 27 | [Community 49](#c-49) | 47 | 0.06 | _get_candidates(), _get_engine(), _get_ilp(), _get_policy(), _get_twin(), … (+3) |
| 28 | [Community 23](#c-23) | 47 | 0.04 | ClosedLoopResilienceController, PolicyAction, HealingAction, PolicyAction, ClosedLoopResilienceController, … (+3) |
| 29 | [Community 52](#c-52) | 45 | 0.07 | Connection, Path, Any, Event, Any, … (+3) |
| 30 | [Community 94](#c-94) | 45 | 0.07 | AgentState, astro_council_node(), build_graph(), electoral_node(), _pool_decide(), … (+4) |
| 31 | [Community 35](#c-35) | 45 | 0.06 | Connection, get_architect(), Intention, MASFactoryArchitect, mas_factory/architect.py - MASFactoryArchitect: builds topology from intention, … (+3) |
| 32 | [Community 48](#c-48) | 45 | 0.04 | Div, web/callbacks.py — All callbacks (ATOM-META-RL-004), Live data status panel for the dashboard header or Live tab., Register all app callbacks., register_callbacks(), … (+3) |
| 33 | [Community 103](#c-103) | 44 | 0.04 | 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, … (+3) |
| 34 | [Community 107](#c-107) | 44 | 0.04 | 10. EXISTING COMPONENTS PRESERVED, 11. MIGRATION NOTES, 1.1 The Post-Determinism Gap, 1.2 System State Before RL-022, 1.3 Goals, … (+3) |
| 35 | [Community 111](#c-111) | 44 | 0.04 | 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, … (+3) |
| 36 | [Community 113](#c-113) | 44 | 0.04 | 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, … (+3) |
| 37 | [Community 115](#c-115) | 44 | 0.04 | 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, … (+3) |
| 38 | [Community 19](#c-19) | 43 | 0.03 | IntegrationReport, Any, IntegrationReport, IntegrationReport, GoalMemory, … (+3) |
| 39 | [Community 22](#c-22) | 43 | 0.03 | InvariantResult, StabilitySnapshot, InvariantSetResult, Invariant, InvariantResult, … (+3) |
| 40 | [Community 42](#c-42) | 42 | 0.08 | MutationClass, ndarray, MutationClass, SeverityLevel, MutationPolicy, … (+3) |
| 41 | [Community 40](#c-40) | 42 | 0.05 | DAGHashMode, ConvergeQuorumResult, dag_hash_n(), DAGHashMode, dag_hash_modes.py — v8.5 Semantic separation of DAG hash contracts  Two distinct, … (+3) |
| 42 | [Community 128](#c-128) | 42 | 0.05 | 10. CI/CD Checks, 1. Network Topology, 2. Layer Architecture, 2-Node Configuration, 3. Node Inventory, … (+3) |
| 43 | [Community 55](#c-55) | 41 | 0.05 | DFAEvent, DFAExecutionGuard, DFAState, InvalidTransitionError, dfa_execution_guard.py — P6 Runtime DFA Enforcement Layer  M = (S, … (+7) |
| 44 | [Community 100](#c-100) | 40 | 0.07 | astro_agent(), fundamental_agent(), macro_agent(), optionsflow_agent(), quant_agent(), … (+3) |
| 45 | [Community 127](#c-127) | 39 | 0.07 | BaseModel, AuthConfig, BrandingConfig, GatewayConfig, RateLimitConfig, … (+3) |
| 46 | [Community 109](#c-109) | 39 | 0.05 | Any, config(), doctor(), inspect(), replay(), … (+3) |
| 47 | [Community 143](#c-143) | 39 | 0.05 | 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 1. Mission & non-goals, 2. Top-level architecture, … (+3) |
| 48 | [Community 144](#c-144) | 39 | 0.05 | Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), AMRE Flow, … (+3) |
| 49 | [Community 149](#c-149) | 39 | 0.05 | 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 1. Mission & non-goals, 2. Top-level architecture, … (+3) |
| 50 | [Community 150](#c-150) | 39 | 0.05 | Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), AMRE Flow, … (+3) |
| 51 | [Community 153](#c-153) | 39 | 0.05 | 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 1. Mission & non-goals, 2. Top-level architecture, … (+3) |
| 52 | [Community 155](#c-155) | 39 | 0.05 | Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), AMRE Flow, … (+3) |
| 53 | [Community 157](#c-157) | 39 | 0.05 | 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 1. Mission & non-goals, 2. Top-level architecture, … (+3) |
| 54 | [Community 158](#c-158) | 39 | 0.05 | Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), AMRE Flow, … (+3) |
| 55 | [Community 32](#c-32) | 39 | 0.04 | ChainLink, ProofChain, CausalProofGraph, ChainLink, ProofChain, … (+3) |
| 56 | [Community 24](#c-24) | 39 | 0.03 | Any, InvariantResult, EnforcementRecord, InvariantEnforcer, InvariantEvaluator, … (+3) |
| 57 | [Community 31](#c-31) | 38 | 0.05 | ExecutionGateway, Any, CausalMergeProtocol, ConsensusSignal, MergeResult, … (+3) |
| 58 | [Community 146](#c-146) | 38 | 0.05 | INV-AWG8: AmneziaWGManager requires trace_id (non-optional in context)., INV10: Event is frozen (frozen=True dataclass)., test_awg_deterministic_delay(), test_awg_events_written_to_eventlog(), test_awg_idempotent_start(), … (+3) |
| 59 | [Community 154](#c-154) | 38 | 0.05 | INV-AWG7: TunnelState enum has valid values., INV8: Engine writes, projections read. Never the twain shall meet., test_awg_deterministic_delay(), test_awg_events_written_to_eventlog(), … (+4) |
| 60 | [Community 47](#c-47) | 38 | 0.04 | get_karl_agent(), KARLSynthesisAgent, Run synthesis + AMRE post-processing.          Returns dict with:           - sy, Phase 3: EMA-smoothed reward with astro enrichment.         - 70% market reward, Compute reproducible state hash., … (+3) |
| 61 | [Community 79](#c-79) | 37 | 0.12 | FederationMessageSigning, FederationMessageSigning, MessageCategory, NonceSequenceValidator, OriginPolicy, … (+3) |
| 62 | [Community 82](#c-82) | 37 | 0.06 | CalibrationMetrics, compute_reward_from_outcome(), compute_trajectory_reward(), CorrelationPenalty, DrawdownState, … (+3) |
| 63 | [Community 83](#c-83) | 37 | 0.06 | CalibrationMetrics, compute_reward_from_outcome(), compute_trajectory_reward(), CorrelationPenalty, DrawdownState, … (+3) |
| 64 | [Community 85](#c-85) | 37 | 0.06 | CalibrationMetrics, compute_reward_from_outcome(), compute_trajectory_reward(), CorrelationPenalty, DrawdownState, … (+3) |
| 65 | [Community 86](#c-86) | 37 | 0.06 | CalibrationMetrics, compute_reward_from_outcome(), compute_trajectory_reward(), CorrelationPenalty, DrawdownState, … (+3) |
| 66 | [Community 166](#c-166) | 37 | 0.05 | 10. Success Criteria Verification, 11. Conclusion, 1.1 System State Definition, 1.2 Transition Function, 1.3 Key Invariants, … (+3) |
| 67 | [Community 9](#c-9) | 37 | 0.02 | TestScoredStrategy, tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 tests), TestEvaluationResult, TestEvolutionEngine, TestMetaAgent, … (+3) |
| 68 | [Community 106](#c-106) | 36 | 0.07 | datetime, Job, WorkloadGenerator, WorkloadStream, WorkloadProfile, … (+3) |
| 69 | [Community 36](#c-36) | 36 | 0.06 | AlwaysAllow, executor(), NoOpInvariantChecker, NoOpRollback, v8.2b Controlled Autocorrection — 17 tests (4 mandatory + 13 additional)., … (+3) |
| 70 | [Community 168](#c-168) | 36 | 0.05 | 1. Requirements Analysis, 2. Technology Comparison (2026), 3. Recommended Architecture, 4. Performance & Scalability, 5. Security & Compliance, … (+3) |
| 71 | [Community 172](#c-172) | 36 | 0.05 | 1. Requirements Analysis, 2. Technology Comparison (2026), 3. Recommended Architecture, 4. Performance & Scalability, 5. Security & Compliance, … (+3) |
| 72 | [Community 176](#c-176) | 36 | 0.05 | 1. Requirements Analysis, 2. Technology Comparison (2026), 3. Recommended Architecture, 4. Performance & Scalability, 5. Security & Compliance, … (+3) |
| 73 | [Community 178](#c-178) | 36 | 0.05 | 1. Requirements Analysis, 2. Technology Comparison (2026), 3. Recommended Architecture, 4. Performance & Scalability, 5. Security & Compliance, … (+3) |
| 74 | [Community 182](#c-182) | 35 | 0.06 | 10. SUCCESS CRITERIA — VERIFICATION CHECKLIST, 11. SUMMARY SCORECARD, 1.1 Complete Call Graph — Mutation Entry Points, 1.2 All Possible Bypass Paths Classified, 1. FORMAL BYPASS PATH ANALYSIS, … (+3) |
| 75 | [Community 54](#c-54) | 35 | 0.05 | StateVector, SemanticProof, DeltaGossipConfig, DeltaGossipMessage, PeerDeltaState, … (+3) |
| 76 | [Community 105](#c-105) | 34 | 0.17 | AccountBalance, Order, OrderSide, OrderType, Position, … (+3) |
| 77 | [Community 65](#c-65) | 34 | 0.10 | NodeWeightsSnapshot, ByzantineSignal, ConsensusShiftType, DampenerConfig, DynamicsReport, … (+3) |
| 78 | [Community 44](#c-44) | 34 | 0.06 | Any, BacktestEngineAdapter, BasketMetrics, EvaluationResult, meta_rl/strategy_evaluator.py -- ATOM-META-RL-010/003/007: Basket + Live Data +, … (+3) |
| 79 | [Community 57](#c-57) | 34 | 0.06 | ADLRecoveryLoop, ADLRecoveryOrchestrator, LivenessRecoveryFunction, OscillationMonitor, OscillationStage, … (+3) |
| 80 | [Community 84](#c-84) | 34 | 0.06 | Any, DivergenceEvent, DivergenceReport, DivergenceType, NonReplayableMarker, … (+4) |
| 81 | [Community 39](#c-39) | 34 | 0.05 | PolicyAction, PolicyEngine, ReactionTrigger, PolicyEngine, PolicyRule, … (+3) |
| 82 | [Community 187](#c-187) | 33 | 0.16 | AST, AsyncFunctionDef, ClassDef, FunctionDef, Path, … (+3) |
| 83 | [Community 193](#c-193) | 33 | 0.16 | AST, AsyncFunctionDef, ClassDef, FunctionDef, Path, … (+3) |
| 84 | [Community 201](#c-201) | 33 | 0.16 | AST, AsyncFunctionDef, ClassDef, FunctionDef, Path, … (+3) |
| 85 | [Community 204](#c-204) | 33 | 0.16 | AST, AsyncFunctionDef, ClassDef, FunctionDef, Path, … (+3) |
| 86 | [Community 209](#c-209) | 33 | 0.11 | ceph_osd_latency(), ceph_osd_replication_latency(), ceph_storage_total(), ceph_storage_used(), cpu_util(), … (+3) |
| 87 | [Community 215](#c-215) | 33 | 0.11 | ceph_osd_latency(), ceph_osd_replication_latency(), ceph_storage_total(), ceph_storage_used(), cpu_util(), … (+3) |
| 88 | [Community 123](#c-123) | 33 | 0.08 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 89 | [Community 125](#c-125) | 33 | 0.08 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 90 | [Community 129](#c-129) | 33 | 0.08 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 91 | [Community 130](#c-130) | 33 | 0.08 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 92 | [Community 41](#c-41) | 33 | 0.07 | StabilitySnapshot, Any, Random, callable, AssertionResult, … (+3) |
| 93 | [Community 163](#c-163) | 32 | 0.11 | AdaptiveScheduler, StepStatus, get_cancellation(), get_cb_registry(), get_dag_recorder(), … (+3) |
| 94 | [Community 213](#c-213) | 32 | 0.09 | build_api_secret(), build_certificate(), build_configmap(), build_ingress(), build_kong_consumer(), … (+3) |
| 95 | [Community 61](#c-61) | 32 | 0.07 | ReplayBuffer, BacktestRegime, BacktestResult, BacktestStep, ContinuousBacktest, … (+3) |
| 96 | [Community 101](#c-101) | 32 | 0.07 | Any, streaming_invariant_engine.py ============================== Continuous streamin, Args:             get_state_delta_exec:   fn(prev_state, curr_state) -> delta di, Compute normalized drift between two delta dicts., … (+4) |
| 97 | [Community 141](#c-141) | 32 | 0.07 | Action, ConsensusReport, Reality Consensus Fusion (RCF) layer — v11.1.  This layer observes the outputs o, Reality Consensus Fusion observer + decision layer., Compute reality consensus and pick actions., … (+3) |
| 98 | [Community 219](#c-219) | 32 | 0.06 | 🔗 `actuator` — Actuator Layer, 🧪 `alignment` — Alignment Testing Suite, ATOMFederationOS — Установка и описание компонентов, 💥 `chaos` — Chaos Engineering, 🗺️ `cluster` — Node Management, … (+3) |
| 99 | [Community 223](#c-223) | 32 | 0.06 | vars.sh script, CEPH_ADMIN_PASSWORD, CEPH_ADMIN_USER, CEPH_CLUSTER_NET, CEPH_PUBLIC_NET, … (+3) |
| 100 | [Community 224](#c-224) | 32 | 0.06 | vars.sh script, CEPH_ADMIN_PASSWORD, CEPH_ADMIN_USER, CEPH_CLUSTER_NET, CEPH_PUBLIC_NET, … (+3) |
| 101 | [Community 46](#c-46) | 32 | 0.04 | DeltaGossipMessage, StateVector, DAGHashMode, DeltaGossipMessage, StateVector, … (+3) |
| 102 | [Community 120](#c-120) | 31 | 0.10 | BrandingCache, saas/branding/cache.py, saas/branding/__init__.py — Branding Package, load_by_api_key(), load_by_tenant_id(), … (+3) |
| 103 | [Community 62](#c-62) | 31 | 0.09 | test_validator.py — ATOM-VALIDATE-001: Unit tests for AgentYamlValidator, test_print_report_all_pass(), test_print_report_quiet(), TestDirectoryValidation, validator(), … (+3) |
| 104 | [Community 50](#c-50) | 31 | 0.06 | DriftType, TemporalVerificationReport, DecisionRecord, DriftEvent, DriftReport, … (+3) |
| 105 | [Community 230](#c-230) | 31 | 0.06 | ATOM-KARL-015: Полная интеграция KARL в основной контур, Core Principle, DecisionRecord — расширенный, Execution Order, Expected Results (честно), … (+3) |
| 106 | [Community 231](#c-231) | 31 | 0.06 | jd_range(), mean_anomaly_360(), positive_eccentricity(), tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Testing (Hypothesis), Heliocentric longitude always ∈ [0, … (+8) |
| 107 | [Community 233](#c-233) | 31 | 0.06 | jd_range(), mean_anomaly_360(), positive_eccentricity(), tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Testing (Hypothesis), Heliocentric longitude always ∈ [0, … (+8) |
| 108 | [Community 238](#c-238) | 31 | 0.06 | ATOM-KARL-015: Полная интеграция KARL в основной контур, Core Principle, DecisionRecord — расширенный, Execution Order, Expected Results (честно), … (+3) |
| 109 | [Community 239](#c-239) | 31 | 0.06 | jd_range(), mean_anomaly_360(), positive_eccentricity(), tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Testing (Hypothesis), Heliocentric longitude always ∈ [0, … (+8) |
| 110 | [Community 243](#c-243) | 31 | 0.06 | 🔴 DAY 1 — Network Foundation, 🟠 DAY 2 — WireGuard Mesh Encryption, 🔵 DAY 3 — Compute Nodes, 🟢 DAY 4 — Slurm Cluster, 🟣 DAY 5 — Ray AI Runtime, … (+3) |
| 111 | [Community 245](#c-245) | 31 | 0.06 | ATOM-KARL-015: Полная интеграция KARL в основной контур, Core Principle, DecisionRecord — расширенный, Execution Order, Expected Results (честно), … (+3) |
| 112 | [Community 247](#c-247) | 31 | 0.06 | ATOM-KARL-015: Полная интеграция KARL в основной контур, Core Principle, DecisionRecord — расширенный, Execution Order, Expected Results (честно), … (+3) |
| 113 | [Community 248](#c-248) | 31 | 0.06 | jd_range(), mean_anomaly_360(), positive_eccentricity(), tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Testing (Hypothesis), Heliocentric longitude always ∈ [0, … (+8) |
| 114 | [Community 250](#c-250) | 31 | 0.06 | jd_range(), mean_anomaly_360(), positive_eccentricity(), tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Testing (Hypothesis), Heliocentric longitude always ∈ [0, … (+8) |
| 115 | [Community 92](#c-92) | 30 | 0.08 | Any, ExecutionRequest, ProofVerifier, Update the signing key (for key rotation)., Verify an ExecutionRequest proof.          Raises ProofVerificationError subclas, … (+4) |
| 116 | [Community 121](#c-121) | 30 | 0.07 | ROMA State Store — Current state management with event sourcing. Provides: save, Get list of all known job IDs from snapshots., Reconstruct full system state., Compare current state vs expected.         Returns list of differences., Key-value state store backed by the event log.     State = latest snapshot + rep, … (+3) |
| 117 | [Community 53](#c-53) | 30 | 0.06 | ChaosResult, ChaosHarness, ChaosResult, Save this chaos result to FailureReplay with correct stage progression., partition_half_cluster(), … (+3) |
| 118 | [Community 102](#c-102) | 30 | 0.06 | GeneratedStrategy, ScoredStrategy, _make_scored(), _make_strategy(), _make_stub_scored(), … (+3) |
| 119 | [Community 259](#c-259) | 30 | 0.06 | 0. Runtime Enforcement (P0.1 / P0.2 / P0.3 / P1.4), 10. FeedbackPrioritySolver, 11. ControlArbitrator, 12. GossipProtocol, 13. CausalMergeProtocol, … (+3) |
| 120 | [Community 67](#c-67) | 29 | 0.10 | FailureParams, FailureRecorder, FailureReplayer, FailureScenario, FailureSnapshot, … (+3) |
| 121 | [Community 68](#c-68) | 29 | 0.10 | GovernorSignal, GovernorSignal, DriftEpisode, ActuatorSignal, CircuitBreaker, … (+3) |
| 122 | [Community 289](#c-289) | 29 | 0.07 | 1. `core/runtime/determinism_guard.py` — ENFORCEMENT LAYER, 2. FILE-BY-FILE REPLACEMENT MAP (P0), 3. SWARM & FEDERATION HARDENING, `alignment/branch.py` — CRITICAL, `alignment/merge_engine.py` — CRITICAL, … (+3) |
| 123 | [Community 87](#c-87) | 29 | 0.04 | amre/test_risk_control.py — ATOM-KARL-015 Phase 5: Tests for risk_control.py  Te, lag внутри [-0.3, +0.3] → без изменений., lag = 0 → без изменений., Тест границ RISK_MIN_POSITION и RISK_MAX_POSITION., … (+4) |
| 124 | [Community 90](#c-90) | 29 | 0.04 | amre/test_risk_control.py — ATOM-KARL-015 Phase 5: Tests for risk_control.py  Te, lag внутри [-0.3, +0.3] → без изменений., lag = 0 → без изменений., Тест границ RISK_MIN_POSITION и RISK_MAX_POSITION., … (+4) |
| 125 | [Community 93](#c-93) | 29 | 0.04 | amre/test_risk_control.py — ATOM-KARL-015 Phase 5: Tests for risk_control.py  Te, lag внутри [-0.3, +0.3] → без изменений., lag = 0 → без изменений., Тест границ RISK_MIN_POSITION и RISK_MAX_POSITION., … (+4) |
| 126 | [Community 97](#c-97) | 29 | 0.04 | amre/test_risk_control.py — ATOM-KARL-015 Phase 5: Tests for risk_control.py  Te, lag внутри [-0.3, +0.3] → без изменений., lag = 0 → без изменений., Тест границ RISK_MIN_POSITION и RISK_MAX_POSITION., … (+4) |
| 127 | [Community 254](#c-254) | 28 | 0.10 | calculate_alcabitius_cusps(), calculate_ascendant(), calculate_equal_houses(), calculate_midheaven(), calculate_placidus_cusps(), … (+3) |
| 128 | [Community 262](#c-262) | 28 | 0.10 | calculate_alcabitius_cusps(), calculate_ascendant(), calculate_equal_houses(), calculate_midheaven(), calculate_placidus_cusps(), … (+3) |
| 129 | [Community 269](#c-269) | 28 | 0.10 | calculate_alcabitius_cusps(), calculate_ascendant(), calculate_equal_houses(), calculate_midheaven(), calculate_placidus_cusps(), … (+3) |
| 130 | [Community 276](#c-276) | 28 | 0.10 | calculate_alcabitius_cusps(), calculate_ascendant(), calculate_equal_houses(), calculate_midheaven(), calculate_placidus_cusps(), … (+3) |
| 131 | [Community 118](#c-118) | 28 | 0.08 | BufferEntry, get_default_buffer(), amre/replay_buffer.py — Replay Buffer for trajectory learning, ReplayBuffer, _select_best_trajectory(), … (+3) |
| 132 | [Community 37](#c-37) | 28 | 0.07 | Any, StabilityEnvelope, ChaosTrace, DivergenceReport, ReplayValidator — H-4: Deterministic replay & divergence detection for chaos tra, … (+3) |
| 133 | [Community 95](#c-95) | 28 | 0.06 | asymmetric_partition(), _AsymmetricPartition, byzantine_sender_injection(), _ByzantineSenderInjection, ChaosScenario, … (+3) |
| 134 | [Community 64](#c-64) | 28 | 0.05 | tests/test_risk_integration.py — ATOM-INTEGRATION-001: SafetyGate Integration Te, SafetyGate handles RiskEngineV2 portfolio without AttributeError., Pre-existing 8% + new 2.5% = 10.5% > 10% limit → rejected., New 5% position within 10% limit → accepted., Zero notional → allowed (edge case: no position change)., … (+3) |
| 135 | [Community 75](#c-75) | 28 | 0.05 | Any, DeterministicFanoutOrder, DeterministicMessageEnvelope, LogicalClock, OrderedMessage, … (+3) |
| 136 | [Community 256](#c-256) | 27 | 0.13 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 137 | [Community 265](#c-265) | 27 | 0.13 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 138 | [Community 272](#c-272) | 27 | 0.13 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 139 | [Community 140](#c-140) | 27 | 0.07 | check_rate_limit(), create_limiter(), _get_redis(), rate_limit_dependency(), Rate limiting — Token Bucket + SlowAPI + Redis backend., … (+3) |
| 140 | [Community 355](#c-355) | 26 | 0.24 | check_root(), gpu_check(), log(), logErr(), logOk(), … (+3) |
| 141 | [Community 329](#c-329) | 26 | 0.22 | check_reqs(), cmd(), cmd_sudo(), day1(), day2(), … (+3) |
| 142 | [Community 341](#c-341) | 26 | 0.22 | check_reqs(), cmd(), cmd_sudo(), day1(), day2(), … (+3) |
| 143 | [Community 186](#c-186) | 26 | 0.18 | AST, Path, ArchitectureLinter, check_base_agent_inheritance(), check_data_room_compliance(), … (+3) |
| 144 | [Community 192](#c-192) | 26 | 0.18 | AST, Path, ArchitectureLinter, check_base_agent_inheritance(), check_data_room_compliance(), … (+3) |
| 145 | [Community 200](#c-200) | 26 | 0.18 | AST, Path, ArchitectureLinter, check_base_agent_inheritance(), check_data_room_compliance(), … (+3) |
| 146 | [Community 203](#c-203) | 26 | 0.18 | AST, Path, ArchitectureLinter, check_base_agent_inheritance(), check_data_room_compliance(), … (+3) |
| 147 | [Community 304](#c-304) | 26 | 0.13 | create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), Idea, … (+3) |
| 148 | [Community 348](#c-348) | 26 | 0.13 | DataFrame, BlendResult, compute_mae(), compute_reversals(), compute_sharpe(), … (+3) |
| 149 | [Community 362](#c-362) | 26 | 0.13 | DataFrame, BlendResult, compute_mae(), compute_reversals(), compute_sharpe(), … (+3) |
| 150 | [Community 370](#c-370) | 26 | 0.13 | DataFrame, BlendResult, compute_mae(), compute_reversals(), compute_sharpe(), … (+3) |
| 151 | [Community 374](#c-374) | 26 | 0.13 | DataFrame, BlendResult, compute_mae(), compute_reversals(), compute_sharpe(), … (+3) |
| 152 | [Community 88](#c-88) | 26 | 0.08 | BCIL, BCILReport, BranchTrust, ByzantineConvergenceFunction, ByzantineFailureType, … (+3) |
| 153 | [Community 171](#c-171) | 26 | 0.08 | AST, Call, ClassDef, FunctionDef, Path, … (+3) |
| 154 | [Community 58](#c-58) | 26 | 0.07 | EconomicSecurityViolation, slashing_engine.py — atom-federation-os v9.0+P8 Slashing Engine., SlashingEngine, SlashingReason, SlashingRecord, … (+3) |
| 155 | [Community 351](#c-351) | 26 | 0.07 | 1. Pre-flight Checklist, 2. Step-by-Step Deployment, 3. Verification Commands, 4. Switching Monitoring Backends, 5. Troubleshooting, … (+3) |
| 156 | [Community 356](#c-356) | 26 | 0.07 | 1. `execution/execution_gateway.py` — NEW, 1. Нет bypass путей, 2. Async не ломает детерминизм, 2. `runtime/async_execution.py` — DETERMINISTIC, 3. Consensus корректен, … (+3) |
| 157 | [Community 367](#c-367) | 26 | 0.07 | 1. Pre-flight Checklist, 2. Step-by-Step Deployment, 3. Verification Commands, 4. Switching Monitoring Backends, 5. Troubleshooting, … (+3) |
| 158 | [Community 147](#c-147) | 26 | 0.06 | Any, Delta, NodeDelta, rolling_state_diff.py ===================== Computes minimal rolling diffs betwe, Compute delta between last replay state and current replay state., … (+3) |
| 159 | [Community 27](#c-27) | 26 | 0.05 | Any, DriftReport, EventStoreSnapshot, Tests for v9.10 — Semantic Consistency Lock Layer., Canonical cycle: gossip delta -> consensus decision -> proof -> bind all., … (+3) |
| 160 | [Community 38](#c-38) | 26 | 0.05 | Any, EvolutionEngine, EvolutionStats, meta_rl/evolution.py -- ATOM-META-RL-002/011, ATOM-META-RL-003: Detect alpha decay.          Alpha decay = reward is dropping, … (+4) |
| 161 | [Community 69](#c-69) | 26 | 0.05 | downsample_equity_curve(), any, EvaluationResult, meta_rl/strategy_pool.py — ATOM-META-RL-001: Strategy Pool with Diversity Contro, Remove lowest-reward strategy from pool., … (+3) |
| 162 | [Community 349](#c-349) | 25 | 0.11 | Test that legacy mode works identically to before changes., test_legacy_mode_produces_same_result(), importlib import of actuator outside gateway → blocked., Firewall install is idempotent., Uninstall removes firewall from meta_path., … (+3) |
| 163 | [Community 386](#c-386) | 25 | 0.10 | TemplateAgent, agent(), happy_state(), tests/_template_agent_test.py ============================== Canonical test temp, Wrong types in known fields must not raise., … (+5) |
| 164 | [Community 399](#c-399) | 25 | 0.10 | TemplateAgent, agent(), happy_state(), tests/_template_agent_test.py ============================== Canonical test temp, Wrong types in known fields must not raise., … (+5) |
| 165 | [Community 77](#c-77) | 25 | 0.09 | FederationMessageSigning, byzantine/__init__.py — v9.8 Byzantine Fault Tolerance Hardening Layer  Scope (m, FederationMessageSigning, MessageSignatureError, message_signatures.py — Federation-level HMAC-based message signing for v9.8, … (+3) |
| 166 | [Community 138](#c-138) | 25 | 0.08 | GossipConfig, QuorumConfig, ClusterSimulator, ClusterTrace, inject_degrade(), … (+3) |
| 167 | [Community 390](#c-390) | 25 | 0.08 | 1. Execution Algebra Definition, 2. Algebraic Properties, 3. Execution Algebra Laws, 4. Formal Verification Conditions, 5. Algebra Classification, … (+3) |
| 168 | [Community 136](#c-136) | 25 | 0.05 | Jepsen-style invariant tests for SBS v1.  Tests verify that GlobalInvariantEngin, TestGlobalInvariantEngine, TestSystemContract, InvariantType, SYSTEM_CONTRACT — hard constraints of ATOMFederationOS.  These invariants CANNOT, … (+3) |
| 169 | [Community 162](#c-162) | 25 | 0.05 | amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, Тест warmup phase: первые 20 решений используют blend=0.3., Первые 19 решений используют BLEND_WARMUP=0.3, 20th переходит в mature., После 20 решений используется BLEND_MATURE=0.15., … (+4) |
| 170 | [Community 33](#c-33) | 25 | 0.04 | PluginPriority, MLTrainingPlugin, ETLPipelinePlugin, get_plugin(), IExecutionContext, … (+3) |
| 171 | [Community 34](#c-34) | 25 | 0.03 | AdaptiveRouter, PeerRouteState, AdaptiveRouter v6.4 — DRL++: loss-aware, latency-aware routing.  Routes around d, Weight = 1 / (1 + normalized_latency * normalized_loss)         Normalized = val, … (+5) |
| 172 | [Community 321](#c-321) | 24 | 0.11 | Agent, Attempt, CycleState, Environment, gate(), … (+3) |
| 173 | [Community 56](#c-56) | 24 | 0.09 | Any, Action, FailureReport, FailureType, L11Verifier, … (+3) |
| 174 | [Community 89](#c-89) | 24 | 0.09 | GSL, InternalState, _kl(), ObservedState, gsl.py — v10.9 Global Soundness Layer Validates internal convergence against obs, … (+5) |
| 175 | [Community 181](#c-181) | 24 | 0.09 | causal_edit_distance(), ConvergenceFunction, ConvergenceSnapshot, GCPLCheckResult, GlobalConsistencyChecker, … (+3) |
| 176 | [Community 161](#c-161) | 24 | 0.08 | AST, Call, FunctionDef, Path, DotFormatter, … (+3) |
| 177 | [Community 414](#c-414) | 24 | 0.08 | 10. Conclusion, 1. System States, 2. Transition System (Before Fix), 3. Transition System (After Fix), 4.1 Safety Invariant (Before Fix — VIOLATED), … (+3) |
| 178 | [Community 416](#c-416) | 24 | 0.08 | Auth / JWT, ⚙️ Configuration, 📁 File Structure, GPU Nodes, GPU Workers, … (+3) |
| 179 | [Community 74](#c-74) | 24 | 0.06 | AuditVerdict, ConvergenceLayer, EntropyController, EntropyRegime, EntropySnapshot, … (+3) |
| 180 | [Community 110](#c-110) | 24 | 0.05 | SBS Runtime Enforcer — integration tests.  Verifies that SBSRuntimeEnforcer corr, TestExecutionLoopSBS, TestSBSRuntimeEnforcer, OFF mode → always returns False, no enforcement., … (+4) |
| 181 | [Community 117](#c-117) | 24 | 0.05 | SBS Runtime Enforcer — integration tests.  Verifies that SBSRuntimeEnforcer corr, TestExecutionLoopSBS, TestSBSRuntimeEnforcer, Quorum below threshold → pre_commit blocks in ENFORCED mode., Two layers with different leaders → detected as violation., … (+3) |
| 182 | [Community 401](#c-401) | 23 | 0.31 | check_deps(), check_files(), cleanup(), error(), generate_report(), … (+3) |
| 183 | [Community 415](#c-415) | 23 | 0.31 | check_deps(), check_files(), cleanup(), error(), generate_report(), … (+3) |
| 184 | [Community 425](#c-425) | 23 | 0.13 | enqueue(), _get_event_store(), _get_redis(), _get_task_store(), is_queue_saturated(), … (+3) |
| 185 | [Community 244](#c-244) | 23 | 0.11 | AP_exec(), AP_exec_and_not_nl(), AP_exec_or_replay(), AP_noncelocked(), AP_replay(), … (+3) |
| 186 | [Community 429](#c-429) | 23 | 0.08 | 10. Edge cases и обработка ошибок, 11. Success Metrics, 12. Риски, допущения и зависимости, 13. Definition of Done, … (+4) |
| 187 | [Community 435](#c-435) | 23 | 0.08 | 10. Edge cases и обработка ошибок, 11. Success Metrics, 12. Риски, допущения и зависимости, 13. Definition of Done, … (+4) |
| 188 | [Community 436](#c-436) | 23 | 0.08 | ACOS — Troubleshooting Guide, API returns 500, Ceph, Ceph OSDs down, CephFS mount fails, … (+3) |
| 189 | [Community 441](#c-441) | 23 | 0.08 | 10. Edge cases и обработка ошибок, 11. Success Metrics, 12. Риски, допущения и зависимости, 13. Definition of Done, … (+4) |
| 190 | [Community 443](#c-443) | 23 | 0.08 | 10. Edge cases и обработка ошибок, 11. Success Metrics, 12. Риски, допущения и зависимости, 13. Definition of Done, … (+4) |
| 191 | [Community 80](#c-80) | 23 | 0.07 | DurabilityLayer, Event, EventStore, EventType, ROMA Event Store — Append-only event log (SQLite/PostgreSQL). Every state change, … (+3) |
| 192 | [Community 108](#c-108) | 23 | 0.06 | Any, CertificationContext, CertificationReport, CertificationResult, CertificationStatus, … (+3) |
| 193 | [Community 180](#c-180) | 23 | 0.06 | EphemerisUnavailableError, require_ephemeris decorator and ephemeris utilities., Decorator that blocks agent execution if Swiss Ephemeris is unavailable.      Us, Raised when agent requires Swiss Ephemeris but it's not available., require_ephemeris(), … (+3) |
| 194 | [Community 71](#c-71) | 23 | 0.05 | ApiClient, AppsV1Api, K8sClient, Kubernetes API client wrapper for ATOM operator., ATOMController, … (+4) |
| 195 | [Community 72](#c-72) | 23 | 0.05 | Any, Event, event_store.py v8.0 — ATOM-META-RL-014  Changes from v7.0:   - Tick-based event_, Failure Replay Engine v7.0.  Modules:   event_store         — append-only event, Replay Engine v7.0 — Deterministic event replay for distributed OS debugging.  P, … (+3) |
| 196 | [Community 453](#c-453) | 22 | 0.14 | AgentState, astro_council_node(), build_graph(), electoral_node(), _pool_decide(), … (+4) |
| 197 | [Community 484](#c-484) | 22 | 0.14 | AgentState, astro_council_node(), build_graph(), electoral_node(), _pool_decide(), … (+4) |
| 198 | [Community 426](#c-426) | 22 | 0.12 | BufferEntry, clear_buffer(), get_all_buffer_entries(), get_buffer_entries_for_idea(), get_buffer_stats(), … (+3) |
| 199 | [Community 428](#c-428) | 22 | 0.12 | BufferEntry, clear_buffer(), get_all_buffer_entries(), get_buffer_entries_for_idea(), get_buffer_stats(), … (+3) |
| 200 | [Community 433](#c-433) | 22 | 0.12 | BufferEntry, clear_buffer(), get_all_buffer_entries(), get_buffer_entries_for_idea(), get_buffer_stats(), … (+3) |
| 201 | [Community 442](#c-442) | 22 | 0.12 | BufferEntry, clear_buffer(), get_all_buffer_entries(), get_buffer_entries_for_idea(), get_buffer_stats(), … (+3) |
| 202 | [Community 184](#c-184) | 22 | 0.11 | BacktestRegime, BacktestResult, BacktestStep, ContinuousBacktest, create_backtest_runner(), … (+3) |
| 203 | [Community 190](#c-190) | 22 | 0.11 | BacktestRegime, BacktestResult, BacktestStep, ContinuousBacktest, create_backtest_runner(), … (+3) |
| 204 | [Community 199](#c-199) | 22 | 0.11 | BacktestRegime, BacktestResult, BacktestStep, ContinuousBacktest, create_backtest_runner(), … (+3) |
| 205 | [Community 76](#c-76) | 22 | 0.10 | ConsensusResult, StateVector, ConsensusResult, StateVector, ConsensusResult, … (+3) |
| 206 | [Community 165](#c-165) | 22 | 0.10 | tests/data_room/test_data_room.py ================================= Tests for th, test_circuit_breaker_half_open_recovery(), test_circuit_breaker_opens_after_threshold(), test_circuit_breaker_short_circuits_when_open(), test_circuit_breaker_starts_closed(), … (+3) |
| 207 | [Community 236](#c-236) | 22 | 0.10 | DriftType, DriftType, Mirrors DriftType from drift_profiler.py (local re-export for this module)., drift_type_to_bridge(), make_moderate_oscillation(), … (+3) |
| 208 | [Community 122](#c-122) | 22 | 0.09 | _epoch_key(), _get_redis(), get_task_store(), TaskStore — единый источник истины для управления состоянием задач.  Заменяет: -, Единый источник истины для task lifecycle.      Все переходы — атомарные, … (+6) |
| 209 | [Community 169](#c-169) | 22 | 0.09 | Any, dj(), dl(), get_persistence(), ld(), … (+3) |
| 210 | [Community 173](#c-173) | 22 | 0.09 | Any, dj(), dl(), get_persistence(), ld(), … (+3) |
| 211 | [Community 177](#c-177) | 22 | 0.09 | Any, dj(), dl(), get_persistence(), ld(), … (+3) |
| 212 | [Community 179](#c-179) | 22 | 0.09 | Any, dj(), dl(), get_persistence(), ld(), … (+3) |
| 213 | [Community 445](#c-445) | 22 | 0.09 | 2026 Hybrid Signal Architecture, Agent Board — Final Weights, Agent Implementation Files, 🤖 AI Agent Rules, AMRE Modules (ATOM-KARL Framework), … (+3) |
| 214 | [Community 448](#c-448) | 22 | 0.09 | 2026 Hybrid Signal Architecture, Agent Board — Final Weights, Agent Implementation Files, 🤖 AI Agent Rules, AMRE Modules (ATOM-KARL Framework), … (+3) |
| 215 | [Community 456](#c-456) | 22 | 0.09 | При use_real_agents=True должен вызываться AstroCouncilAgent., При use_real_agents=True сигналы не должны содержать 'momentum=' из синтетическо, При use_real_agents=True и use_thompson=True вызывается ThompsonSampler.select., При use_real_agents=True должен вызываться SynthesisAgent и выдавать финальный с, При use_real_agents=True должен вызываться SentimentAgent., … (+3) |
| 216 | [Community 458](#c-458) | 22 | 0.09 | При use_real_agents=True должен вызываться AstroCouncilAgent., При use_real_agents=True сигналы не должны содержать 'momentum=' из синтетическо, При use_real_agents=True и use_thompson=True вызывается ThompsonSampler.select., При use_real_agents=True должен вызываться SynthesisAgent и выдавать финальный с, При use_real_agents=True должен вызываться SentimentAgent., … (+3) |
| 217 | [Community 461](#c-461) | 22 | 0.09 | Architecture Map, ATOM Federation OS — Agent Memory, Constraints (RL-022 HARD LIMITS), Current Version: v10.0-ATOM-META-RL-022, Federation Layer (v7.5+), … (+3) |
| 218 | [Community 463](#c-463) | 22 | 0.09 | 1. Python environment, 2. Kubernetes manifests, 3. HELM установка (альтернатива), atom-federation-os — Установка и быстрый старт, ATOMCluster spec, … (+3) |
| 219 | [Community 467](#c-467) | 22 | 0.09 | 1. Резюме, 2.10. Зависимости и воспроизводимость, 2.1. Общая архитектура и согласованность модулей, 2.2. Качество кода и стиль, 2.3. Глубокий анализ падающих тестов (приоритет №1), … (+3) |
| 220 | [Community 468](#c-468) | 22 | 0.09 | 2026 Hybrid Signal Architecture, Agent Board — Final Weights, Agent Implementation Files, 🤖 AI Agent Rules, AMRE Modules (ATOM-KARL Framework), … (+3) |
| 221 | [Community 475](#c-475) | 22 | 0.09 | При use_real_agents=True должен вызываться AstroCouncilAgent., При use_real_agents=True сигналы не должны содержать 'momentum=' из синтетическо, При use_real_agents=True и use_thompson=True вызывается ThompsonSampler.select., При use_real_agents=True должен вызываться SynthesisAgent и выдавать финальный с, При use_real_agents=True должен вызываться SentimentAgent., … (+3) |
| 222 | [Community 486](#c-486) | 22 | 0.09 | 2026 Hybrid Signal Architecture, Agent Board — Final Weights, Agent Implementation Files, 🤖 AI Agent Rules, AMRE Modules (ATOM-KARL Framework), … (+3) |
| 223 | [Community 495](#c-495) | 22 | 0.09 | При use_real_agents=True должен вызываться AstroCouncilAgent., При use_real_agents=True сигналы не должны содержать 'momentum=' из синтетическо, При use_real_agents=True и use_thompson=True вызывается ThompsonSampler.select., При use_real_agents=True должен вызываться SynthesisAgent и выдавать финальный с, При use_real_agents=True должен вызываться SentimentAgent., … (+3) |
| 224 | [Community 499](#c-499) | 22 | 0.09 | При use_real_agents=True должен вызываться AstroCouncilAgent., При use_real_agents=True сигналы не должны содержать 'momentum=' из синтетическо, При use_real_agents=True и use_thompson=True вызывается ThompsonSampler.select., При use_real_agents=True должен вызываться SynthesisAgent и выдавать финальный с, При use_real_agents=True должен вызываться SentimentAgent., … (+3) |
| 225 | [Community 70](#c-70) | 22 | 0.08 | DagNode, DagRetryEngine, DagStateStore, _get_redis(), NodeStatus, … (+3) |
| 226 | [Community 73](#c-73) | 22 | 0.08 | DeterministicReplay, Event, EventStore, EventType, JobAggregate, … (+3) |
| 227 | [Community 78](#c-78) | 22 | 0.08 | ExecutionGateway, StateVector, ConsensusDecision, ConsensusResolver, ConsensusVote, … (+3) |
| 228 | [Community 135](#c-135) | 22 | 0.06 | BarrierPhase, BarrierTicket, DeterministicTickSynchronizer, GlobalExecutionBarrier, GlobalExecutionBarrier (GEB) — core/runtime/geb.py ATOM-META-RL-022 P0  Synchron, … (+3) |
| 229 | [Community 526](#c-526) | 21 | 0.19 | main(), print_header(), print_test(), Test KARL self-improvement loop, Test Meta-Questioning Engine, … (+3) |
| 230 | [Community 353](#c-353) | 21 | 0.12 | Event, Event, Replay Observability Subscriber v7.0.  Bridges ReplayEngine → Prometheus + OTEL., Subscriber that emits Prometheus metrics + OTEL traces for each replayed event., ReplayObservabilitySubscriber, … (+4) |
| 231 | [Community 175](#c-175) | 21 | 0.10 | CrossLayerInvariantEngine, Verifies formal invariants I1–I4 across execution and replay domains.      Usage, Args:             cluster_state_fn:  fn() returning live cluster state dict, make_cluster_state(), make_replay_state(), … (+3) |
| 232 | [Community 160](#c-160) | 21 | 0.09 | TrustDelta, TrustVector, PeerTrustState, trust_sync_protocol.py — v9.5 TrustSyncProtocol  Purpose:   Gossip protocol for, Per-peer trust sync state.      Tracks what we know about each peer's trust vect, … (+3) |
| 233 | [Community 516](#c-516) | 21 | 0.09 | 1. `core/deterministic.py` — GTBP Addition, 2. `alignment/branch.py` — Deterministic IDs + Timestamps, 3. `alignment/convergence.py` — Tick-Based Oscillation + Entropy, 4. `alignment/drift_detector.py` — Timestamp Removal, 5. `alignment/plan_reality_comparator.py` — Deterministic Binding IDs, … (+3) |
| 234 | [Community 170](#c-170) | 21 | 0.08 | datetime, DatasetExporter, _label_from_outcome(), Map job/outcome string to label integer., MLBatch, … (+3) |
| 235 | [Community 124](#c-124) | 21 | 0.07 | any, EvaluationResult, meta_rl/strategy_pool.py — ATOM-META-RL-001: Strategy Pool with Diversity Contro, Manages population of ScoredStrategy instances.      Features:     - Deduplicati, Add ScoredStrategy to pool if not duplicate and pool has capacity.          Retu, … (+3) |
| 236 | [Community 126](#c-126) | 21 | 0.07 | any, EvaluationResult, meta_rl/strategy_pool.py — ATOM-META-RL-001: Strategy Pool with Diversity Contro, Manages population of ScoredStrategy instances.      Features:     - Deduplicati, Add ScoredStrategy to pool if not duplicate and pool has capacity.          Retu, … (+3) |
| 237 | [Community 145](#c-145) | 21 | 0.07 | datetime, _consecutive(), _derivative(), _last_age_min(), _mean(), … (+3) |
| 238 | [Community 96](#c-96) | 21 | 0.06 | AuditLogger, ExecutionGateway, Singleton gateway-guard для всех state mutations в системе.          Guarantees:, Return singleton instance., Reset singleton (for testing only)., … (+3) |
| 239 | [Community 207](#c-207) | 21 | 0.06 | amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, EMA продолжает работать после увеличения окна., EMA продолжает работать после уменьшения окна., Alpha пересчитывается при изменении window_size., Счётчик увеличивается при каждом add(), … (+4) |
| 240 | [Community 25](#c-25) | 21 | 0.03 | BacktestEngineAdapter, RiskEngineV2, StrategyEvaluator, TestStrategyEvaluator, TestScoredStrategy, … (+3) |
| 241 | [Community 552](#c-552) | 20 | 0.22 | apply_migration(), cmd_check(), cmd_init_single(), cmd_migrate(), cmd_plan(), … (+3) |
| 242 | [Community 571](#c-571) | 20 | 0.22 | apply_migration(), cmd_check(), cmd_init_single(), cmd_migrate(), cmd_plan(), … (+3) |
| 243 | [Community 584](#c-584) | 20 | 0.22 | apply_migration(), cmd_check(), cmd_init_single(), cmd_migrate(), cmd_plan(), … (+3) |
| 244 | [Community 592](#c-592) | 20 | 0.22 | apply_migration(), cmd_check(), cmd_init_single(), cmd_migrate(), cmd_plan(), … (+3) |
| 245 | [Community 544](#c-544) | 20 | 0.15 | calculate_panchanga(), get_choghadiya(), get_karana(), get_muhurta_score(), get_nakshatra(), … (+3) |
| 246 | [Community 564](#c-564) | 20 | 0.15 | calculate_panchanga(), get_choghadiya(), get_karana(), get_muhurta_score(), get_nakshatra(), … (+3) |
| 247 | [Community 574](#c-574) | 20 | 0.15 | calculate_panchanga(), get_choghadiya(), get_karana(), get_muhurta_score(), get_nakshatra(), … (+3) |
| 248 | [Community 585](#c-585) | 20 | 0.15 | calculate_panchanga(), get_choghadiya(), get_karana(), get_muhurta_score(), get_nakshatra(), … (+3) |
| 249 | [Community 218](#c-218) | 20 | 0.11 | AST, Path, BypassPath, Run full self-audit at system startup.                  Returns SelfAuditResult, Reset audit state (for testing only)., … (+4) |
| 250 | [Community 222](#c-222) | 20 | 0.11 | Any, AgentSignalRepository, AstroPositionRepository, AuditLogRepository, _d(), … (+3) |
| 251 | [Community 287](#c-287) | 20 | 0.11 | CorrectionAction, CorrectionCycleResult, CorrectionDecision, CorrectionLoop, CorrectionSignal, … (+3) |
| 252 | [Community 296](#c-296) | 20 | 0.11 | Execute one correction cycle.         Returns CorrectionCycleResult with decisio, Classification of fix required., STEP 1: Observe — detect deviations from SLO targets., STEP 2: Classify — determine fix type from signals., Concrete actions available to the correction loop., … (+3) |
| 253 | [Community 487](#c-487) | 20 | 0.11 | build_decision_record(), EnsembleMember, get_audit_log(), get_meta_rl_audit_log(), KPISnapshot, … (+3) |
| 254 | [Community 185](#c-185) | 20 | 0.10 | Any, Connection, Cursor, datetime, CalibrationReport, … (+3) |
| 255 | [Community 191](#c-191) | 20 | 0.10 | Any, Connection, Cursor, datetime, CalibrationReport, … (+3) |
| 256 | [Community 197](#c-197) | 20 | 0.10 | Any, Connection, Cursor, datetime, CalibrationReport, … (+3) |
| 257 | [Community 283](#c-283) | 20 | 0.10 | ControlAction, get_oap_optimizer(), KPIControlState, OAPConfig, OAPOptimizer, … (+3) |
| 258 | [Community 285](#c-285) | 20 | 0.10 | ControlAction, get_oap_optimizer(), KPIControlState, OAPConfig, OAPOptimizer, … (+3) |
| 259 | [Community 293](#c-293) | 20 | 0.10 | ControlAction, get_oap_optimizer(), KPIControlState, OAPConfig, OAPOptimizer, … (+3) |
| 260 | [Community 303](#c-303) | 20 | 0.10 | ControlAction, get_oap_optimizer(), KPIControlState, OAPConfig, OAPOptimizer, … (+3) |
| 261 | [Community 546](#c-546) | 20 | 0.10 | 1. LagWindow — Signal Smoothing, 2. Risk Controller — Dynamic Position Sizing, Acceptance Criteria Checklist, Adaptive Window Sizing, ATOM-KARL-015 Phase 5 — Lag Window Integration, … (+3) |
| 262 | [Community 566](#c-566) | 20 | 0.10 | 1. LagWindow — Signal Smoothing, 2. Risk Controller — Dynamic Position Sizing, Acceptance Criteria Checklist, Adaptive Window Sizing, ATOM-KARL-015 Phase 5 — Lag Window Integration, … (+3) |
| 263 | [Community 576](#c-576) | 20 | 0.10 | 1. LagWindow — Signal Smoothing, 2. Risk Controller — Dynamic Position Sizing, Acceptance Criteria Checklist, Adaptive Window Sizing, ATOM-KARL-015 Phase 5 — Lag Window Integration, … (+3) |
| 264 | [Community 587](#c-587) | 20 | 0.10 | 1. LagWindow — Signal Smoothing, 2. Risk Controller — Dynamic Position Sizing, Acceptance Criteria Checklist, Adaptive Window Sizing, ATOM-KARL-015 Phase 5 — Lag Window Integration, … (+3) |
| 265 | [Community 104](#c-104) | 20 | 0.08 | Any, Adapter, BiasSwitch, ConditionEvaluator, Connection, … (+3) |
| 266 | [Community 112](#c-112) | 20 | 0.08 | Any, Adapter, BiasSwitch, ConditionEvaluator, Connection, … (+3) |
| 267 | [Community 114](#c-114) | 20 | 0.08 | Any, Adapter, BiasSwitch, ConditionEvaluator, Connection, … (+3) |
| 268 | [Community 220](#c-220) | 20 | 0.08 | Any, Any, Any, GlobalInvariantEngine, _get_current_config(), … (+3) |
| 269 | [Community 133](#c-133) | 20 | 0.07 | Any, CheckpointManager, CrashConsistentState, CrashSnapshot, Save a snapshot at tick., … (+3) |
| 270 | [Community 253](#c-253) | 20 | 0.07 | amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, Тест warmup phase: первые 20 решений используют blend=0.3., Первые 19 решений используют BLEND_WARMUP=0.3, 20th переходит в mature., После 20 решений используется BLEND_MATURE=0.15., … (+4) |
| 271 | [Community 271](#c-271) | 20 | 0.07 | _cleanup_session_files(), fast_evolution_agent(), Integration test for the full evolutionary pipeline.  Closes: R6.3, R6.5, R6.6., … (+5) |
| 272 | [Community 275](#c-275) | 20 | 0.07 | amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, Тест вычисления lag_adj., lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)., lag_adj < 0 когда EMA ниже raw (сигнал опережает вверх)., lag_adj масштабируется корректно: |lag_adj| < 1 для разумных отклонений., … (+3) |
| 273 | [Community 51](#c-51) | 20 | 0.06 | GPULease, Job, JobStatus, ROMA Control Plane — Core Models, Worker, … (+3) |
| 274 | [Community 554](#c-554) | 19 | 0.32 | check_ceph_health(), check_cooldown(), check_gpu_available(), check_node(), check_scheduler_api(), … (+3) |
| 275 | [Community 578](#c-578) | 19 | 0.32 | check_ceph_health(), check_cooldown(), check_gpu_available(), check_node(), check_scheduler_api(), … (+3) |
| 276 | [Community 616](#c-616) | 19 | 0.20 | AST, Call, Path, build_execution_graph(), _collect_call_sites(), … (+3) |
| 277 | [Community 607](#c-607) | 19 | 0.18 | calculate_houses(), calculate_natal_chart(), calculate_planet(), get_current_positions(), get_planetary_positions(), … (+3) |
| 278 | [Community 621](#c-621) | 19 | 0.18 | calculate_houses(), calculate_natal_chart(), calculate_planet(), get_current_positions(), get_planetary_positions(), … (+3) |
| 279 | [Community 629](#c-629) | 19 | 0.18 | calculate_houses(), calculate_natal_chart(), calculate_planet(), get_current_positions(), get_planetary_positions(), … (+3) |
| 280 | [Community 431](#c-431) | 19 | 0.16 | Any, test_act_mismatch(), test_block_at_g2(), test_complex_federation_trace(), test_detail_mismatch(), … (+3) |
| 281 | [Community 345](#c-345) | 19 | 0.14 | _angle_diff(), Aspect, AspectReport, AspectsEngine, AspectType, … (+3) |
| 282 | [Community 252](#c-252) | 19 | 0.12 | FailureRecord, FailureReplay, Record → Save → Replay lifecycle for ADL failure incidents.      Usage:, Immutable trace of a single failure incident., Capture a failure incident trace., … (+3) |
| 283 | [Community 335](#c-335) | 19 | 0.12 | TrustDelta, TrustVector, ConflictReport, LedgerReconciliation, MergeDecision, … (+3) |
| 284 | [Community 246](#c-246) | 19 | 0.11 | AuditLogRecord, Immutable audit log record., Any, AgentSignalRepository, AstroPositionRepository, … (+3) |
| 285 | [Community 358](#c-358) | 19 | 0.11 | Any, Any, sbs/cli_schema.py — schema-check subcommand implementation., Validate state schema from JSON string or file., run_schema_check(), … (+3) |
| 286 | [Community 206](#c-206) | 19 | 0.10 | AdaptiveRetryController, AdmissionController, AdmissionDecision, DegradationLevel, _get_redis(), … (+3) |
| 287 | [Community 323](#c-323) | 19 | 0.10 | DAGDriftProfile, DriftProfiler, GoalDriftProfile, OscillationProfile, drift_profiler.py — planning_observability layer Detects and reports planning de, … (+3) |
| 288 | [Community 608](#c-608) | 19 | 0.10 | 1. Копировать env-файл, 2. Поднять инфраструктуру, 3. Инициализировать схему, 4. Запустить приложение, AstroFin Sentinel V5 — Database Layer, … (+3) |
| 289 | [Community 609](#c-609) | 19 | 0.10 | 10. Questions?, 1. Code of Conduct, 2. Quick start, 3.1 Architectural conformance, 3.2 Data Room compliance, … (+3) |
| 290 | [Community 622](#c-622) | 19 | 0.10 | 1. Копировать env-файл, 2. Поднять инфраструктуру, 3. Инициализировать схему, 4. Запустить приложение, AstroFin Sentinel V5 — Database Layer, … (+3) |
| 291 | [Community 623](#c-623) | 19 | 0.10 | 10. Questions?, 1. Code of Conduct, 2. Quick start, 3.1 Architectural conformance, 3.2 Data Room compliance, … (+3) |
| 292 | [Community 630](#c-630) | 19 | 0.10 | 1. Копировать env-файл, 2. Поднять инфраструктуру, 3. Инициализировать схему, 4. Запустить приложение, AstroFin Sentinel V5 — Database Layer, … (+3) |
| 293 | [Community 631](#c-631) | 19 | 0.10 | 10. Questions?, 1. Code of Conduct, 2. Quick start, 3.1 Architectural conformance, 3.2 Data Room compliance, … (+3) |
| 294 | [Community 633](#c-633) | 19 | 0.10 | Canonical Trace Format, Case 1: Full pass (all gates return PASS), Case 2: Block at gate Gi, Case 3: Behavioral divergence (falsify), Corollary: SAFE_P7, … (+3) |
| 295 | [Community 639](#c-639) | 19 | 0.10 | test_deterministic_scheduler.py ATOMS: ATOM-META-RL-014 — Deterministic Schedule, execution_order is deterministic across runs., schedule_fan_out is deterministic: same tick → same worker assignments., schedule_async_steps is deterministic across runs., Same name + same tick → same ID., … (+3) |
| 296 | [Community 645](#c-645) | 19 | 0.10 | 1. Копировать env-файл, 2. Поднять инфраструктуру, 3. Инициализировать схему, 4. Запустить приложение, AstroFin Sentinel V5 — Database Layer, … (+3) |
| 297 | [Community 646](#c-646) | 19 | 0.10 | 10. Questions?, 1. Code of Conduct, 2. Quick start, 3.1 Architectural conformance, 3.2 Data Room compliance, … (+3) |
| 298 | [Community 216](#c-216) | 19 | 0.09 | Any, AggregateConfidenceAdapter, ContextAdapter, ExtractSignalAdapter, FilterByConfidenceAdapter, … (+3) |
| 299 | [Community 217](#c-217) | 19 | 0.09 | BaseStrategy, crossover(), evolve(), fitness_from_backtest(), GAPopulation, … (+3) |
| 300 | [Community 221](#c-221) | 19 | 0.09 | Any, AggregateConfidenceAdapter, ContextAdapter, ExtractSignalAdapter, FilterByConfidenceAdapter, … (+3) |
| 301 | [Community 225](#c-225) | 19 | 0.09 | Any, AggregateConfidenceAdapter, ContextAdapter, ExtractSignalAdapter, FilterByConfidenceAdapter, … (+3) |
| 302 | [Community 227](#c-227) | 19 | 0.09 | Any, AggregateConfidenceAdapter, ContextAdapter, ExtractSignalAdapter, FilterByConfidenceAdapter, … (+3) |
| 303 | [Community 300](#c-300) | 19 | 0.09 | ConstraintGraph, CandidateGenerator, HardConstraintPruner, HybridSolver, ILPOptimizer, … (+4) |
| 304 | [Community 532](#c-532) | 19 | 0.09 | pump_nodes(), RPC chaos tests — prove the system works across real processes, not just in-memo, Start pump threads on both nodes., Basic unicast send/receive across two real processes., … (+6) |
| 305 | [Community 142](#c-142) | 19 | 0.08 | Connection, _belief_db_path(), BeliefState, BeliefTracker, get_belief_tracker(), … (+3) |
| 306 | [Community 148](#c-148) | 19 | 0.08 | Connection, _belief_db_path(), BeliefState, BeliefTracker, get_belief_tracker(), … (+3) |
| 307 | [Community 152](#c-152) | 19 | 0.08 | Connection, _belief_db_path(), BeliefState, BeliefTracker, get_belief_tracker(), … (+3) |
| 308 | [Community 156](#c-156) | 19 | 0.08 | Connection, _belief_db_path(), BeliefState, BeliefTracker, get_belief_tracker(), … (+3) |
| 309 | [Community 63](#c-63) | 19 | 0.07 | BacktestConfig, Backtester, BacktestResult, BacktestTrade, trading/backtester.py — ATOM-STEP-8: Backtesting Engine, … (+3) |
| 310 | [Community 195](#c-195) | 19 | 0.07 | BaseHTTPMiddleware, BrandingInjectorMiddleware, Response branding injection — headers + optional HTML., Injects branding into responses:     - Headers: X-Tenant-ID, X-Branding-Version, … (+4) |
| 311 | [Community 91](#c-91) | 19 | 0.06 | Any, NodeRPCStub, DRLBridge, Attempt to send `msg` across the (simulated) network.          Returns:, DRL = Dynamic Runtime Layer (network distortion / link perturbation).      Simul, … (+3) |
| 312 | [Community 663](#c-663) | 18 | 0.20 | _choghadiya_to_score(), _datetime_to_jd(), get_choghadiya(), get_current_nakshatra(), get_moon_sign(), … (+3) |
| 313 | [Community 672](#c-672) | 18 | 0.20 | _choghadiya_to_score(), _datetime_to_jd(), get_choghadiya(), get_current_nakshatra(), get_moon_sign(), … (+3) |
| 314 | [Community 685](#c-685) | 18 | 0.20 | _choghadiya_to_score(), _datetime_to_jd(), get_choghadiya(), get_current_nakshatra(), get_moon_sign(), … (+3) |
| 315 | [Community 711](#c-711) | 18 | 0.20 | _choghadiya_to_score(), _datetime_to_jd(), get_choghadiya(), get_current_nakshatra(), get_moon_sign(), … (+3) |
| 316 | [Community 679](#c-679) | 18 | 0.18 | Any, check_invariant(), compare_ledgers(), ledger_hash(), ledger_hash_from_normalized(), … (+3) |
| 317 | [Community 713](#c-713) | 18 | 0.18 | calculate_houses(), calculate_natal_chart(), calculate_planet(), get_current_positions(), get_planetary_positions(), … (+3) |
| 318 | [Community 452](#c-452) | 18 | 0.16 | fetch_current_price(), _fetch_metals_api(), fetch_multi_ohlcv(), fetch_ohlcv(), fetch_ohlcv_simple(), … (+3) |
| 319 | [Community 472](#c-472) | 18 | 0.16 | fetch_current_price(), _fetch_metals_api(), fetch_multi_ohlcv(), fetch_ohlcv(), fetch_ohlcv_simple(), … (+3) |
| 320 | [Community 481](#c-481) | 18 | 0.16 | fetch_current_price(), _fetch_metals_api(), fetch_multi_ohlcv(), fetch_ohlcv(), fetch_ohlcv_simple(), … (+3) |
| 321 | [Community 492](#c-492) | 18 | 0.16 | fetch_current_price(), _fetch_metals_api(), fetch_multi_ohlcv(), fetch_ohlcv(), fetch_ohlcv_simple(), … (+3) |
| 322 | [Community 610](#c-610) | 18 | 0.16 | AdmissionController, JobEngine, get_admission(), get_engine(), get_job(), … (+3) |
| 323 | [Community 674](#c-674) | 18 | 0.14 | all_detectors(), ceph_health_degraded(), ceph_osd_down(), gpu_available(), node_unreachable(), … (+3) |
| 324 | [Community 700](#c-700) | 18 | 0.14 | Check if a node is reachable via TCP (ssh port check)., Check if GPU is accessible and not in failure state., Check if Slurm controller is responsive., Run all detectors, return dict of results., … (+4) |
| 325 | [Community 384](#c-384) | 18 | 0.13 | _angle_diff(), Aspect, AspectReport, AspectsEngine, AspectType, … (+3) |
| 326 | [Community 389](#c-389) | 18 | 0.13 | _angle_diff(), Aspect, AspectReport, AspectsEngine, AspectType, … (+3) |
| 327 | [Community 396](#c-396) | 18 | 0.13 | _angle_diff(), Aspect, AspectReport, AspectsEngine, AspectType, … (+3) |
| 328 | [Community 375](#c-375) | 18 | 0.12 | crossover(), evolve(), fitness_from_backtest(), GAPopulation, generate_synthetic_history(), … (+3) |
| 329 | [Community 264](#c-264) | 18 | 0.11 | Any, AgentSignalRepository, AstroPositionRepository, AuditLogRepository, _d(), … (+3) |
| 330 | [Community 311](#c-311) | 18 | 0.11 | ConstraintGraph, HardConstraintPruner, HybridSolver, ILPOptimizer, PolicySelector, … (+3) |
| 331 | [Community 333](#c-333) | 18 | 0.11 | crossover(), evolve(), fitness_from_backtest(), GAPopulation, generate_synthetic_history(), … (+3) |
| 332 | [Community 339](#c-339) | 18 | 0.11 | crossover(), evolve(), fitness_from_backtest(), GAPopulation, generate_synthetic_history(), … (+3) |
| 333 | [Community 653](#c-653) | 18 | 0.11 | INV8: Complete write → read separation flow., INV9: TraceRecord normalization., INV1: Every action produces an event., INV2: Engine NEVER calls reducer (graph integrity)., INV3: StateReducer NEVER emits events (pure read-side)., … (+3) |
| 334 | [Community 654](#c-654) | 18 | 0.11 | INV8: Complete write → read separation flow., INV9: TraceRecord normalization., INV1: Every action produces an event., INV2: Engine NEVER calls reducer (graph integrity)., INV3: StateReducer NEVER emits events (pure read-side)., … (+3) |
| 335 | [Community 664](#c-664) | 18 | 0.11 | 10. DATA QUALITY, 1. АНАЛИЗ СИГНАЛОВ (Signal Distribution), 2. THOMPSON SAMPLING ЭФФЕКТИВНОСТЬ, 3. АНАЛИЗ АГЕНТНЫХ СИГНАЛОВ, 4. ВРЕМЕННОЙ АНАЛИЗ, … (+3) |
| 336 | [Community 668](#c-668) | 18 | 0.11 | 1.1 Core Concepts, 1.2 GitAgent Manifest Schema, 1. GitAgent Standard Overview, 2.1 Component Mapping, 2.2 Compatibility Score: 85%, … (+3) |
| 337 | [Community 678](#c-678) | 18 | 0.11 | 10. CircuitBreaker (`orchestration/planning_observability/circuit_breaker.py`), 11. InvariantChecker (`orchestration/v8_2a_safety_foundations/invariant_checker.py`), 12. RollbackEngine (`orchestration/v8_2a_safety_foundations/rollback_engine.py`), 13. DeterministicScheduler (`orchestration/deterministic_scheduler.py`), 14. ExecutionGateway (`orchestration/execution_gateway.py`), … (+3) |
| 338 | [Community 686](#c-686) | 18 | 0.11 | 10. DATA QUALITY, 1. АНАЛИЗ СИГНАЛОВ (Signal Distribution), 2. THOMPSON SAMPLING ЭФФЕКТИВНОСТЬ, 3. АНАЛИЗ АГЕНТНЫХ СИГНАЛОВ, 4. ВРЕМЕННОЙ АНАЛИЗ, … (+3) |
| 339 | [Community 689](#c-689) | 18 | 0.11 | 1.1 Core Concepts, 1.2 GitAgent Manifest Schema, 1. GitAgent Standard Overview, 2.1 Component Mapping, 2.2 Compatibility Score: 85%, … (+3) |
| 340 | [Community 693](#c-693) | 18 | 0.11 | 10. DATA QUALITY, 1. АНАЛИЗ СИГНАЛОВ (Signal Distribution), 2. THOMPSON SAMPLING ЭФФЕКТИВНОСТЬ, 3. АНАЛИЗ АГЕНТНЫХ СИГНАЛОВ, 4. ВРЕМЕННОЙ АНАЛИЗ, … (+3) |
| 341 | [Community 704](#c-704) | 18 | 0.11 | Agent Export/Import, Agents, Architecture, CLI Commands, Configuration, … (+3) |
| 342 | [Community 712](#c-712) | 18 | 0.11 | 10. DATA QUALITY, 1. АНАЛИЗ СИГНАЛОВ (Signal Distribution), 2. THOMPSON SAMPLING ЭФФЕКТИВНОСТЬ, 3. АНАЛИЗ АГЕНТНЫХ СИГНАЛОВ, 4. ВРЕМЕННОЙ АНАЛИЗ, … (+3) |
| 343 | [Community 714](#c-714) | 18 | 0.11 | Agent Export/Import, Agents, Architecture, CLI Commands, Configuration, … (+3) |
| 344 | [Community 719](#c-719) | 18 | 0.11 | 1.1 Core Concepts, 1.2 GitAgent Manifest Schema, 1. GitAgent Standard Overview, 2.1 Component Mapping, 2.2 Compatibility Score: 85%, … (+3) |
| 345 | [Community 723](#c-723) | 18 | 0.11 | 1.1 Core Concepts, 1.2 GitAgent Manifest Schema, 1. GitAgent Standard Overview, 2.1 Component Mapping, 2.2 Compatibility Score: 85%, … (+3) |
| 346 | [Community 164](#c-164) | 18 | 0.10 | DAGRecorder, ExecutionDAG, Execution DAG Recorder — v3 core component.  Captures: task → step graph → span, Create a new DAG for task_id + epoch. Returns dag_id., Load DAG by dag_id. Uses meta index for epoch-aware keys., … (+5) |
| 347 | [Community 274](#c-274) | 18 | 0.10 | _load_weights(), AstroFin Sentinel v5 — Synthesis Agent AstroCouncil: координатор всех агентов, ф, SynthesisAgent = Координатор финального синтеза.      Получает сигналы от ВСЕХ а, Public entry point. Wraps analyze() with the latency histogram         and defen, … (+4) |
| 348 | [Community 408](#c-408) | 18 | 0.10 | Any, AtomMessage, Queue, NodeMesh, Broadcast via DRL → RPC mesh., … (+3) |
| 349 | [Community 644](#c-644) | 18 | 0.10 | AgentBelief, AgentBeliefHistory, AgentPool, AgentSelectionLog, BacktestRun, … (+3) |
| 350 | [Community 134](#c-134) | 18 | 0.09 | Any, Backtester, EvaluationResult, BacktestEngineAdapter, meta_rl/backtest_adapter.py — ATOM-META-RL-003: BacktestEngine Adapter, … (+3) |
| 351 | [Community 137](#c-137) | 18 | 0.09 | EventStore, LamportClock, Append event to task's stream. Returns stream entry ID.         Also updates Lam, Convenience: emit STEP_EXECUTED with full step data., Per-task Lamport clock for causal ordering.      Each task_id has its own logica, … (+3) |
| 352 | [Community 211](#c-211) | 18 | 0.09 | Any, MisbehaviorEvidence, MisbehaviorType, slashing.py — atom-federation-os v9.0+P7 Slashing Engine for Byzantine Misbehavi, Return True if node is currently slashed., … (+4) |
| 353 | [Community 139](#c-139) | 18 | 0.08 | test_cross_origin_proof.py — v9.2 Cross-Origin Equivalence Proof Layer Tests, CROSS_ORIGIN_EQUIVALENCE invariant., Invariant should build its own proof when proof not provided., ProofOrigin enum values., SemanticProofEngine: prove_equivalence and prove_from_digests., … (+4) |
| 354 | [Community 60](#c-60) | 18 | 0.07 | StateVector, StateVector, GossipProtocol, PeerRecord, GossipProtocol — partial async state exchange between nodes.  No blocking RPC. E, … (+3) |
| 355 | [Community 99](#c-99) | 18 | 0.07 | get_queue(), Job, JobStatus, QueueManager, QueueManager, … (+3) |
| 356 | [Community 116](#c-116) | 18 | 0.07 | ContextMode, EnhancedExecutionContext, Reset singleton (for testing only)., Check if mutation is currently allowed., Get current context mode., … (+3) |
| 357 | [Community 59](#c-59) | 18 | 0.06 | ACOSCLI, main(), validate_all_contracts(), Compiles job submissions into executable DAGs.     Guarantees: every node has ex, DAG execution with:     - Topological ordering (parallel where possible)     - C, … (+3) |
| 358 | [Community 188](#c-188) | 18 | 0.06 | tests/test_risk_integration.py — ATOM-INTEGRATION-001: SafetyGate Integration Te, SafetyGate handles RiskEngineV2 portfolio without AttributeError., Pre-existing 8% + new 2.5% = 10.5% > 10% limit → rejected., New 5% position within 10% limit → accepted., Zero notional → allowed (edge case: no position change)., … (+3) |
| 359 | [Community 194](#c-194) | 18 | 0.06 | tests/test_risk_integration.py — ATOM-INTEGRATION-001: SafetyGate Integration Te, SafetyGate handles RiskEngineV2 portfolio without AttributeError., Pre-existing 8% + new 2.5% = 10.5% > 10% limit → rejected., New 5% position within 10% limit → accepted., Zero notional → allowed (edge case: no position change)., … (+3) |
| 360 | [Community 202](#c-202) | 18 | 0.06 | tests/test_risk_integration.py — ATOM-INTEGRATION-001: SafetyGate Integration Te, SafetyGate handles RiskEngineV2 portfolio without AttributeError., Pre-existing 8% + new 2.5% = 10.5% > 10% limit → rejected., New 5% position within 10% limit → accepted., Zero notional → allowed (edge case: no position change)., … (+3) |
| 361 | [Community 205](#c-205) | 18 | 0.06 | tests/test_risk_integration.py — ATOM-INTEGRATION-001: SafetyGate Integration Te, SafetyGate handles RiskEngineV2 portfolio without AttributeError., Pre-existing 8% + new 2.5% = 10.5% > 10% limit → rejected., New 5% position within 10% limit → accepted., Zero notional → allowed (edge case: no position change)., … (+3) |
| 362 | [Community 765](#c-765) | 17 | 0.19 | export_agent(), import_agent(), list_agents(), main(), mcp_install_cli(), … (+3) |
| 363 | [Community 770](#c-770) | 17 | 0.19 | export_agent(), import_agent(), list_agents(), main(), mcp_install_cli(), … (+3) |
| 364 | [Community 600](#c-600) | 17 | 0.17 | Fallback when Prometheus is unreachable — use static info + rough estimates., Data-driven job routing — queries Prometheus for live metrics, scores each a, Main routing endpoint., Live node status from Prometheus., … (+5) |
| 365 | [Community 601](#c-601) | 17 | 0.17 | Fallback when Prometheus is unreachable — use static info + rough estimates., Data-driven job routing — queries Prometheus for live metrics, scores each a, Main routing endpoint., Live node status from Prometheus., … (+5) |
| 366 | [Community 771](#c-771) | 17 | 0.16 | garbage_collect(), generate_ideas(), get_latest_brief(), ideas_to_tracker(), list_briefs(), … (+3) |
| 367 | [Community 447](#c-447) | 17 | 0.15 | AmneziaWGManager, Any, ContractViolation, Any, create_tunnel_incident(), … (+3) |
| 368 | [Community 450](#c-450) | 17 | 0.15 | CalibrationResult, CalibrationState, CalibrationTarget, _gradient_free_step(), KeplerCalibrator, … (+3) |
| 369 | [Community 470](#c-470) | 17 | 0.15 | CalibrationResult, CalibrationState, CalibrationTarget, _gradient_free_step(), KeplerCalibrator, … (+3) |
| 370 | [Community 479](#c-479) | 17 | 0.15 | CalibrationResult, CalibrationState, CalibrationTarget, _gradient_free_step(), KeplerCalibrator, … (+3) |
| 371 | [Community 490](#c-490) | 17 | 0.15 | CalibrationResult, CalibrationState, CalibrationTarget, _gradient_free_step(), KeplerCalibrator, … (+3) |
| 372 | [Community 305](#c-305) | 17 | 0.14 | BacktestRun, _db_path(), _get_db(), get_summary(), load_results(), … (+3) |
| 373 | [Community 313](#c-313) | 17 | 0.14 | BacktestRun, _db_path(), _get_db(), get_summary(), load_results(), … (+3) |
| 374 | [Community 317](#c-317) | 17 | 0.14 | BacktestRun, _db_path(), _get_db(), get_summary(), load_results(), … (+3) |
| 375 | [Community 343](#c-343) | 17 | 0.14 | get_agent_info(), get_registry(), GitAgentRegistry, list_agents(), main(), … (+6) |
| 376 | [Community 344](#c-344) | 17 | 0.14 | get_agent_info(), get_registry(), GitAgentRegistry, list_agents(), main(), … (+6) |
| 377 | [Community 359](#c-359) | 17 | 0.14 | get_agent_info(), get_registry(), GitAgentRegistry, list_agents(), main(), … (+6) |
| 378 | [Community 368](#c-368) | 17 | 0.14 | get_agent_info(), get_registry(), GitAgentRegistry, list_agents(), main(), … (+6) |
| 379 | [Community 730](#c-730) | 17 | 0.14 | build_decision_record(), EnsembleMember, EnsembleSelection, get_audit_log(), KPISnapshot, … (+3) |
| 380 | [Community 733](#c-733) | 17 | 0.14 | build_decision_record(), EnsembleMember, EnsembleSelection, get_audit_log(), KPISnapshot, … (+3) |
| 381 | [Community 748](#c-748) | 17 | 0.14 | build_decision_record(), EnsembleMember, EnsembleSelection, get_audit_log(), KPISnapshot, … (+3) |
| 382 | [Community 290](#c-290) | 17 | 0.13 | Any, Event, BridgeConfig, BridgeResult, ExecutionReplayBridge, … (+3) |
| 383 | [Community 346](#c-346) | 17 | 0.13 | Connection, _db_path(), get_db(), get_session(), HistoryDB, … (+3) |
| 384 | [Community 360](#c-360) | 17 | 0.13 | Connection, _db_path(), get_db(), get_session(), HistoryDB, … (+3) |
| 385 | [Community 366](#c-366) | 17 | 0.13 | Connection, _db_path(), get_db(), get_session(), HistoryDB, … (+3) |
| 386 | [Community 369](#c-369) | 17 | 0.13 | Connection, _db_path(), get_db(), get_session(), HistoryDB, … (+3) |
| 387 | [Community 257](#c-257) | 17 | 0.12 | AtomProposal, AtomProposer, main(), Generate ATOM proposals from analysis data., Create ATOM proposal from a single finding., … (+3) |
| 388 | [Community 266](#c-266) | 17 | 0.12 | AtomProposal, AtomProposer, main(), Generate ATOM proposals from analysis data., Create ATOM proposal from a single finding., … (+3) |
| 389 | [Community 273](#c-273) | 17 | 0.12 | AtomProposal, AtomProposer, main(), Generate ATOM proposals from analysis data., Create ATOM proposal from a single finding., … (+3) |
| 390 | [Community 277](#c-277) | 17 | 0.12 | AtomProposal, AtomProposer, main(), Generate ATOM proposals from analysis data., Create ATOM proposal from a single finding., … (+3) |
| 391 | [Community 413](#c-413) | 17 | 0.12 | PriceTick, Data Room Blueprint — fallback chain for data access., A point-in-time price observation., Any, T, … (+3) |
| 392 | [Community 255](#c-255) | 17 | 0.11 | KeplerOrbit, KeplerResult, OrbitalElements, propagate_kepler(), core/kepler.py — ATOM-STEP-1: Kepler Orbital Mechanics Engine ==================, … (+5) |
| 393 | [Community 263](#c-263) | 17 | 0.11 | KeplerOrbit, KeplerResult, OrbitalElements, propagate_kepler(), core/kepler.py — ATOM-STEP-1: Kepler Orbital Mechanics Engine ==================, … (+5) |
| 394 | [Community 270](#c-270) | 17 | 0.11 | KeplerOrbit, KeplerResult, OrbitalElements, propagate_kepler(), core/kepler.py — ATOM-STEP-1: Kepler Orbital Mechanics Engine ==================, … (+5) |
| 395 | [Community 286](#c-286) | 17 | 0.11 | Any, AgentSignalRepository, AstroPositionRepository, AuditLogRepository, _d(), … (+3) |
| 396 | [Community 312](#c-312) | 17 | 0.11 | Event, ChaosToReplayBridge, DeterminismChecker, DeterminismResult, DivergenceEvent, … (+3) |
| 397 | [Community 337](#c-337) | 17 | 0.11 | ndarray, Eigenstate, EigenstateDetector, EigenstateType, v6.7 — Stability Eigenstate Detector  Finds and tracks stable attractor states (, … (+3) |
| 398 | [Community 376](#c-376) | 17 | 0.11 | QuestionOutcome, amre/self_question.py — Self-Questioning Engine + Meta-Questioning (ATOM-016) Se, Answer the selected question., Tracks whether a question's answer correctly predicted outcome., ATOM-016: Meta-questioning — reflect on whether our questions are trustworthy., … (+3) |
| 399 | [Community 377](#c-377) | 17 | 0.11 | QuestionOutcome, amre/self_question.py — Self-Questioning Engine + Meta-Questioning (ATOM-016) Se, Answer the selected question., Tracks whether a question's answer correctly predicted outcome., ATOM-016: Meta-questioning — reflect on whether our questions are trustworthy., … (+3) |
| 400 | [Community 383](#c-383) | 17 | 0.11 | QuestionOutcome, amre/self_question.py — Self-Questioning Engine + Meta-Questioning (ATOM-016) Se, Answer the selected question., Tracks whether a question's answer correctly predicted outcome., ATOM-016: Meta-questioning — reflect on whether our questions are trustworthy., … (+3) |
| 401 | [Community 394](#c-394) | 17 | 0.11 | QuestionOutcome, amre/self_question.py — Self-Questioning Engine + Meta-Questioning (ATOM-016) Se, Answer the selected question., Tracks whether a question's answer correctly predicted outcome., ATOM-016: Meta-questioning — reflect on whether our questions are trustworthy., … (+3) |
| 402 | [Community 701](#c-701) | 17 | 0.11 | 1. `ansible/roles/slurm_ha/`, 2. `ansible/roles/edge-node/`, 3. `k8s/federation/`, 4. `.github/workflows/infra-ci.yml`, 5. Обновлённый `ansible/playbook.yml`, … (+3) |
| 403 | [Community 736](#c-736) | 17 | 0.11 | 1. Текущее состояние MAS (по факту репозитория), 2. Целевое состояние (что считаем "готово на 100%"), 3.1. CompromiseAgent (`agents/_impl/compromise_agent.py`) — НОВЫЙ, 3.2. Унификация Pattern A (12–14 агентов), 3.3. Per-agent Calibration & Attribution (`agents/_impl/calibration.py`) — НОВЫЙ, … (+4) |
| 404 | [Community 737](#c-737) | 17 | 0.11 | 1. Agents, 2. Core infrastructure, 3. Orchestration, 4. Web / API, 5. Tooling, … (+3) |
| 405 | [Community 738](#c-738) | 17 | 0.11 | Knowledge Base — Agents ✅ COMPLETED (2026-03-27), Knowledge Base — Bradley + Market Cycles ✅ DONE (2026-03-27), Knowledge Base ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts (Round 2) ✅ COMPLETED (2026-03-27), … (+3) |
| 406 | [Community 739](#c-739) | 17 | 0.11 | 0. Context, 10. Semantics, 11. Integration with Load Test, 1. Task Formalization, 2. Root Cause Analysis (RCA), … (+3) |
| 407 | [Community 744](#c-744) | 17 | 0.11 | 🟢 ACCEPTABLE (no control-flow impact), 🔴 CRITICAL FIXES (control flow — must be deterministic), Determinism Fix Plan — ATOMFederation-OS, 📁 Files to Modify, FIX-1: `execution_gateway.py` — Nonce generation, … (+3) |
| 408 | [Community 746](#c-746) | 17 | 0.11 | ATOMFederationOS v6.5 — Global Control Arbitrer + System Optimizer, Changelog, 🔴 GAP 1: Global Control Arbitrer, 🔴 GAP 2: System-Wide Optimization Objective, 🟡 GAP 3: Continuous Stability Engine (no batch mode), … (+3) |
| 409 | [Community 747](#c-747) | 17 | 0.11 | ATOMFederationOS v6.6 — Self-Modeling + Predictive Control + Decision Lattice, Changelog, 🔴 GAP 1: Self-Model (CRITICAL — missing entirely), 🔴 GAP 2: Predictive Control Loop, 🔴 GAP 3: Formal Decision Lattice, … (+3) |
| 410 | [Community 752](#c-752) | 17 | 0.11 | 1. Текущее состояние MAS (по факту репозитория), 2. Целевое состояние (что считаем "готово на 100%"), 3.1. CompromiseAgent (`agents/_impl/compromise_agent.py`) — НОВЫЙ, 3.2. Унификация Pattern A (12–14 агентов), 3.3. Per-agent Calibration & Attribution (`agents/_impl/calibration.py`) — НОВЫЙ, … (+4) |
| 411 | [Community 753](#c-753) | 17 | 0.11 | 1. Agents, 2. Core infrastructure, 3. Orchestration, 4. Web / API, 5. Tooling, … (+3) |
| 412 | [Community 754](#c-754) | 17 | 0.11 | Knowledge Base — Agents ✅ COMPLETED (2026-03-27), Knowledge Base — Bradley + Market Cycles ✅ DONE (2026-03-27), Knowledge Base ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts (Round 2) ✅ COMPLETED (2026-03-27), … (+3) |
| 413 | [Community 755](#c-755) | 17 | 0.11 | ACME account errors, Adding TLS to Existing Ingress, Architecture, Components, DNS-01 Challenge (for wildcard / custom domain), … (+3) |
| 414 | [Community 757](#c-757) | 17 | 0.11 | 1. Install dependencies, 2. Set model paths, 3. Run locally, 4. Test, API usage, … (+3) |
| 415 | [Community 758](#c-758) | 17 | 0.11 | 1. Текущее состояние MAS (по факту репозитория), 2. Целевое состояние (что считаем "готово на 100%"), 3.1. CompromiseAgent (`agents/_impl/compromise_agent.py`) — НОВЫЙ, 3.2. Унификация Pattern A (12–14 агентов), 3.3. Per-agent Calibration & Attribution (`agents/_impl/calibration.py`) — НОВЫЙ, … (+4) |
| 416 | [Community 759](#c-759) | 17 | 0.11 | 1. Agents, 2. Core infrastructure, 3. Orchestration, 4. Web / API, 5. Tooling, … (+3) |
| 417 | [Community 761](#c-761) | 17 | 0.11 | 0. Context, 10. Semantics, 11. Integration with Load Test, 1. Task Formalization, 2. Root Cause Analysis (RCA), … (+3) |
| 418 | [Community 762](#c-762) | 17 | 0.11 | 📋 Ansible Roles, 🎯 Architecture Overview, 👤 Author, 📦 Components, 🗓️ Day 0–7 Deployment, … (+3) |
| 419 | [Community 767](#c-767) | 17 | 0.11 | Knowledge Base — Agents ✅ COMPLETED (2026-03-27), Knowledge Base — Bradley + Market Cycles ✅ DONE (2026-03-27), Knowledge Base ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts (Round 2) ✅ COMPLETED (2026-03-27), … (+3) |
| 420 | [Community 768](#c-768) | 17 | 0.11 | 1. Текущее состояние MAS (по факту репозитория), 2. Целевое состояние (что считаем "готово на 100%"), 3.1. CompromiseAgent (`agents/_impl/compromise_agent.py`) — НОВЫЙ, 3.2. Унификация Pattern A (12–14 агентов), 3.3. Per-agent Calibration & Attribution (`agents/_impl/calibration.py`) — НОВЫЙ, … (+4) |
| 421 | [Community 769](#c-769) | 17 | 0.11 | 1. Agents, 2. Core infrastructure, 3. Orchestration, 4. Web / API, 5. Tooling, … (+3) |
| 422 | [Community 773](#c-773) | 17 | 0.11 | Knowledge Base — Agents ✅ COMPLETED (2026-03-27), Knowledge Base — Bradley + Market Cycles ✅ DONE (2026-03-27), Knowledge Base ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts ✅ COMPLETED (2026-03-27), Knowledge Base — Concepts (Round 2) ✅ COMPLETED (2026-03-27), … (+3) |
| 423 | [Community 226](#c-226) | 17 | 0.10 | ProofLedger, ProofOrigin, ProofRecord, proof_ledger.py — v9.4 ProofLedger: Time-Aware Trust Scoring  Key shift from v9., Time-aware proof trust ledger.      Tracks validation history for proofs and pro, … (+3) |
| 424 | [Community 511](#c-511) | 17 | 0.10 | If primary resolver raises, blueprint tries the secondary., If all resolvers in the chain fail, get_price() returns None., test_blueprint_falls_back_to_secondary_on_error(), … (+6) |
| 425 | [Community 151](#c-151) | 17 | 0.09 | ChaosEvent, ChaosFeedbackController, ControllerConfig, ImpactScorer, ImpactWeights, … (+3) |
| 426 | [Community 196](#c-196) | 17 | 0.09 | InMemoryPrometheusEmitter, Metrics Emitter v7.0 — Prometheus bridge for ATOMFederationOS.  Maps events → Pr, Stable key for (name, labels). Name may already carry the 'atom_' prefix., In-process Prometheus-compatible metric store.      Suitable for:       - Unit t, … (+4) |
| 427 | [Community 261](#c-261) | 17 | 0.09 | Any, DESCEventLogger, LayerStateAdapter, DESC Event Adapter — logs SBS events to DESC event log.  Every invariant violati, Return all logged events in append order., … (+4) |
| 428 | [Community 280](#c-280) | 17 | 0.09 | DESCEventLogger, LayerStateAdapter, Any, DESC Event Adapter — logs SBS events to DESC event log.  Every invariant violati, Return all logged events in append order., … (+4) |
| 429 | [Community 307](#c-307) | 17 | 0.09 | angular_sep(), tests/test_kepler_differential.py — ATOM-STEP-3: Differential Testing (Swiss Eph, After one orbital period, heliocentric longitude returns to same value., Earth radius should always be in physically plausible range., … (+5) |
| 430 | [Community 309](#c-309) | 17 | 0.09 | angular_sep(), tests/test_kepler_differential.py — ATOM-STEP-3: Differential Testing (Swiss Eph, After one orbital period, heliocentric longitude returns to same value., Earth radius should always be in physically plausible range., … (+5) |
| 431 | [Community 315](#c-315) | 17 | 0.09 | angular_sep(), tests/test_kepler_differential.py — ATOM-STEP-3: Differential Testing (Swiss Eph, After one orbital period, heliocentric longitude returns to same value., Earth radius should always be in physically plausible range., … (+5) |
| 432 | [Community 324](#c-324) | 17 | 0.09 | angular_sep(), tests/test_kepler_differential.py — ATOM-STEP-3: Differential Testing (Swiss Eph, After one orbital period, heliocentric longitude returns to same value., Earth radius should always be in physically plausible range., … (+5) |
| 433 | [Community 327](#c-327) | 17 | 0.09 | angular_sep(), tests/test_kepler_differential.py — ATOM-STEP-3: Differential Testing (Swiss Eph, After one orbital period, heliocentric longitude returns to same value., Earth radius should always be in physically plausible range., … (+5) |
| 434 | [Community 214](#c-214) | 17 | 0.08 | LogEntry, NodeState, Replicate to majority and commit., Simulated AppendEntries RPC. Returns True if success., Add new node to cluster. Requires consensus., … (+3) |
| 435 | [Community 81](#c-81) | 17 | 0.06 | get_bridge(), MetaRLTradingBridge, TradingExecutionResult, TestModeGating, get_bridge(), … (+3) |
| 436 | [Community 258](#c-258) | 17 | 0.06 | AgentTestContract, DegradedContract, tests/agent_test_base.py ======================== Shared test base class for all, An empty state is not allowed to raise — must degrade gracefully., Wrong types in known fields must not raise., … (+5) |
| 437 | [Community 267](#c-267) | 17 | 0.06 | AgentTestContract, DegradedContract, tests/agent_test_base.py ======================== Shared test base class for all, An empty state is not allowed to raise — must degrade gracefully., Wrong types in known fields must not raise., … (+5) |
| 438 | [Community 278](#c-278) | 17 | 0.06 | AgentTestContract, DegradedContract, tests/agent_test_base.py ======================== Shared test base class for all, An empty state is not allowed to raise — must degrade gracefully., Wrong types in known fields must not raise., … (+5) |
| 439 | [Community 281](#c-281) | 17 | 0.06 | AgentTestContract, DegradedContract, tests/agent_test_base.py ======================== Shared test base class for all, An empty state is not allowed to raise — must degrade gracefully., Wrong types in known fields must not raise., … (+5) |
| 440 | [Community 611](#c-611) | 16 | 0.35 | FAIL, info(), ok(), PASS, run_all(), … (+3) |
| 441 | [Community 635](#c-635) | 16 | 0.35 | FAIL, info(), ok(), PASS, run_all(), … (+3) |
| 442 | [Community 774](#c-774) | 16 | 0.18 | AMREOutput, apply_fallback(), check_delisted_fallback(), DelistFallback, get_karl_diagnostics(), … (+3) |
| 443 | [Community 775](#c-775) | 16 | 0.18 | AMREOutput, apply_fallback(), check_delisted_fallback(), DelistFallback, get_karl_diagnostics(), … (+3) |
| 444 | [Community 781](#c-781) | 16 | 0.18 | garbage_collect(), generate_ideas(), get_latest_brief(), ideas_to_tracker(), list_briefs(), … (+3) |
| 445 | [Community 800](#c-800) | 16 | 0.18 | garbage_collect(), generate_ideas(), get_latest_brief(), ideas_to_tracker(), list_briefs(), … (+3) |
| 446 | [Community 814](#c-814) | 16 | 0.18 | garbage_collect(), generate_ideas(), get_latest_brief(), ideas_to_tracker(), list_briefs(), … (+3) |
| 447 | [Community 393](#c-393) | 16 | 0.17 | Namespace, Any, cmd_activate(), cmd_create(), cmd_get(), … (+3) |
| 448 | [Community 792](#c-792) | 16 | 0.16 | adversarial_scheduling(), burst_load(), cascading_failure(), normal_baseline(), Named stress scenario = profile + duration + targets., … (+3) |
| 449 | [Community 558](#c-558) | 16 | 0.15 | Any, create_span(), event_to_span(), get_global_otel(), get_tracer(), … (+3) |
| 450 | [Community 782](#c-782) | 16 | 0.15 | EvaluationResult, calmar_ratio(), enrich_result(), max_consecutive_losses(), omega_ratio(), … (+3) |
| 451 | [Community 801](#c-801) | 16 | 0.15 | EvaluationResult, calmar_ratio(), enrich_result(), max_consecutive_losses(), omega_ratio(), … (+3) |
| 452 | [Community 817](#c-817) | 16 | 0.15 | EvaluationResult, calmar_ratio(), enrich_result(), max_consecutive_losses(), omega_ratio(), … (+3) |
| 453 | [Community 823](#c-823) | 16 | 0.15 | EvaluationResult, calmar_ratio(), enrich_result(), max_consecutive_losses(), omega_ratio(), … (+3) |
| 454 | [Community 235](#c-235) | 16 | 0.14 | Event, EventStore, Deterministic event ID: same inputs → same ID.          Replaces uuid.uuid4() in, Get next monotonic tick. Thread-safe under _lock., Get next sequence number for tick. Thread-safe under _lock., … (+4) |
| 455 | [Community 268](#c-268) | 16 | 0.13 | Reconciler, make_mock_k8s(), make_state(), Unit tests for ATOM Operator — reconciler logic (no K8s required)., Step 5 — Phase 5: quorum breach → Failed phase., … (+3) |
| 456 | [Community 322](#c-322) | 16 | 0.12 | EvaluationResult, meta_rl/reward.py — ATOM-META-RL-004: Risk-Adjusted Reward Function  This module, RewardCalculator, RewardConfig, Computes a scalar reward from an :class:`EvaluationResult` using     **only** ri, … (+3) |
| 457 | [Community 385](#c-385) | 16 | 0.12 | Connection, get_architect(), Intention, MASFactoryArchitect, mas_factory/architect.py - MASFactoryArchitect: builds topology from intention, … (+3) |
| 458 | [Community 398](#c-398) | 16 | 0.12 | Connection, get_architect(), Intention, MASFactoryArchitect, mas_factory/architect.py - MASFactoryArchitect: builds topology from intention, … (+3) |
| 459 | [Community 402](#c-402) | 16 | 0.12 | ActuationDirection, ActuationResult, ActuationSeverity, ActuationSignal, ActuatorCommand, … (+3) |
| 460 | [Community 446](#c-446) | 16 | 0.12 | _env_bool(), _env_float(), _env_int(), get_lag_window(), LagWindow, … (+3) |
| 461 | [Community 449](#c-449) | 16 | 0.12 | _env_bool(), _env_float(), _env_int(), get_lag_window(), LagWindow, … (+3) |
| 462 | [Community 469](#c-469) | 16 | 0.12 | _env_bool(), _env_float(), _env_int(), get_lag_window(), LagWindow, … (+3) |
| 463 | [Community 489](#c-489) | 16 | 0.12 | _env_bool(), _env_float(), _env_int(), get_lag_window(), LagWindow, … (+3) |
| 464 | [Community 778](#c-778) | 16 | 0.12 | #001 — BlackRock-inspired architectural practices in AstroFin Sentinel V5, 10. Reading list, 1. The "One BlackRock Rule" → "One Data Room", 2. Federated plugin architecture, not microservices, … (+6) |
| 465 | [Community 779](#c-779) | 16 | 0.12 | KI-001 — Data Room is a draft, not a runtime contract, KI-002 — Manual registry edits, KI-003 — No Postgres in dev environments, KI-004 — LangGraph and asyncio.gather both active, … (+5) |
| 466 | [Community 797](#c-797) | 16 | 0.12 | #001 — BlackRock-inspired architectural practices in AstroFin Sentinel V5, 10. Reading list, 1. The "One BlackRock Rule" → "One Data Room", 2. Federated plugin architecture, not microservices, … (+6) |
| 467 | [Community 798](#c-798) | 16 | 0.12 | KI-001 — Data Room is a draft, not a runtime contract, KI-002 — Manual registry edits, KI-003 — No Postgres in dev environments, KI-004 — LangGraph and asyncio.gather both active, … (+5) |
| 468 | [Community 805](#c-805) | 16 | 0.12 | #001 — BlackRock-inspired architectural practices in AstroFin Sentinel V5, 10. Reading list, 1. The "One BlackRock Rule" → "One Data Room", 2. Federated plugin architecture, not microservices, … (+6) |
| 469 | [Community 806](#c-806) | 16 | 0.12 | KI-001 — Data Room is a draft, not a runtime contract, KI-002 — Manual registry edits, KI-003 — No Postgres in dev environments, KI-004 — LangGraph and asyncio.gather both active, … (+5) |
| 470 | [Community 816](#c-816) | 16 | 0.12 | 10. Финальная мысль для обдумывания, 1. Суть loopcraft и сдвиг парадигмы, 2. Пример: Autoresearch (Андрей Карпати), 3. Иерархия уровней автономности, 4. Экономика и ограничения, … (+3) |
| 471 | [Community 820](#c-820) | 16 | 0.12 | #001 — BlackRock-inspired architectural practices in AstroFin Sentinel V5, 10. Reading list, 1. The "One BlackRock Rule" → "One Data Room", 2. Federated plugin architecture, not microservices, … (+6) |
| 472 | [Community 821](#c-821) | 16 | 0.12 | KI-001 — Data Room is a draft, not a runtime contract, KI-002 — Manual registry edits, KI-003 — No Postgres in dev environments, KI-004 — LangGraph and asyncio.gather both active, … (+5) |
| 473 | [Community 372](#c-372) | 16 | 0.11 | DriftEvent, DriftStatus, ModelRealityAligner, v6.7 — Model–Reality Alignment Engine  Closes the model ↔ reality gap:  - Tracks, Per-subsystem absolute error., … (+3) |
| 474 | [Community 306](#c-306) | 16 | 0.10 | atr_from_binance(), calculate_atr(), get_volatility_risk(), core/volatility.py — Dynamic Risk Engine (R-07)  Volatility-adaptive position si, Dynamic risk calculator.      Input (pick one):       - price + atr  → compute a, … (+3) |
| 475 | [Community 314](#c-314) | 16 | 0.10 | atr_from_binance(), calculate_atr(), get_volatility_risk(), core/volatility.py — Dynamic Risk Engine (R-07)  Volatility-adaptive position si, Dynamic risk calculator.      Input (pick one):       - price + atr  → compute a, … (+3) |
| 476 | [Community 318](#c-318) | 16 | 0.10 | atr_from_binance(), calculate_atr(), get_volatility_risk(), core/volatility.py — Dynamic Risk Engine (R-07)  Volatility-adaptive position si, Dynamic risk calculator.      Input (pick one):       - price + atr  → compute a, … (+3) |
| 477 | [Community 189](#c-189) | 16 | 0.09 | Any, Random, DeliveryModel, DRLTransport, FailureModel, … (+3) |
| 478 | [Community 282](#c-282) | 16 | 0.09 | AsyncPipeline, get_karl_optimizer(), KARLOptimizer, KARLPerfProfile, amre/karl_optimizer.py - ATOM-021: KARL Optimization & Parallelism, … (+3) |
| 479 | [Community 284](#c-284) | 16 | 0.09 | AsyncPipeline, get_karl_optimizer(), KARLOptimizer, KARLPerfProfile, amre/karl_optimizer.py - ATOM-021: KARL Optimization & Parallelism, … (+3) |
| 480 | [Community 292](#c-292) | 16 | 0.09 | AsyncPipeline, get_karl_optimizer(), KARLOptimizer, KARLPerfProfile, amre/karl_optimizer.py - ATOM-021: KARL Optimization & Parallelism, … (+3) |
| 481 | [Community 302](#c-302) | 16 | 0.09 | AsyncPipeline, get_karl_optimizer(), KARLOptimizer, KARLPerfProfile, amre/karl_optimizer.py - ATOM-021: KARL Optimization & Parallelism, … (+3) |
| 482 | [Community 260](#c-260) | 16 | 0.08 | TrustVector, NodeWeightEntry, NodeWeightRegistry, node_weights.py — v9.6 Node Weight Registry  Purpose:   Manages per-node weights, Computes and caches per-node weights from TrustVector state.      Weights are de, … (+4) |
| 483 | [Community 132](#c-132) | 16 | 0.07 | EnvelopeBounds, EnvelopeState, MetricBound, stress_envelope.py — chaos layer Stability Envelope: formal working range for th, Classify system into EnvelopeState.          COLLAPSE check (highest priority):, … (+4) |
| 484 | [Community 320](#c-320) | 16 | 0.07 | _check_inbound_message_authenticity(), _check_proof_trust_bounded(), _check_stale_proof_not_trusted(), _check_trust_convergence(), _check_trust_vector_consistency(), … (+3) |
| 485 | [Community 66](#c-66) | 16 | 0.04 | stability_ledger.py ~~~~~~~~~~~~~~~~~~~~ Long-term stability aggregates per sour, Record a stability sample for a source., True if source avg stability exceeds coherence_threshold., True if source violation rate exceeds violation_threshold., Compute global stability trend across all sources.         Compares current epoc, … (+3) |
| 486 | [Community 845](#c-845) | 15 | 0.24 | Any, AST, Path, _ast_node_to_hashable(), ASTStats, … (+3) |
| 487 | [Community 880](#c-880) | 15 | 0.23 | compute_env_hash(), get_lock_file_hash(), get_locked_python_version(), get_pip_freeze(), main(), … (+3) |
| 488 | [Community 833](#c-833) | 15 | 0.21 | main(), Test 4: Topology Visualizer, Test 5: Meta-Questioning Engine, Test 6: TopologyExecutor, Test 7: Parallel execution, … (+3) |
| 489 | [Community 850](#c-850) | 15 | 0.21 | main(), Test 4: Topology Visualizer, Test 5: Meta-Questioning Engine, Test 6: TopologyExecutor, Test 7: Parallel execution, … (+3) |
| 490 | [Community 865](#c-865) | 15 | 0.21 | main(), Test 4: Topology Visualizer, Test 5: Meta-Questioning Engine, Test 6: TopologyExecutor, Test 7: Parallel execution, … (+3) |
| 491 | [Community 875](#c-875) | 15 | 0.21 | main(), Test 4: Topology Visualizer, Test 5: Meta-Questioning Engine, Test 6: TopologyExecutor, Test 7: Parallel execution, … (+3) |
| 492 | [Community 405](#c-405) | 15 | 0.20 | Gene, StrategyResult, Gene, StrategyResult, Gene, … (+3) |
| 493 | [Community 741](#c-741) | 15 | 0.18 | ceph_exec(), CephExecutor, CephHealth, CephStatus, detect_split_brain(), … (+3) |
| 494 | [Community 756](#c-756) | 15 | 0.18 | Severity score for v8 Safety Kernel integration.     Higher = more severe., FIX 1.4: Proper split-brain detection.     Split-brain = different parts of clus, FIX 3.2: Structured recovery actions.     Each action: action, target, priority, … (+5) |
| 495 | [Community 395](#c-395) | 15 | 0.15 | BacktestRun, _get_db(), get_summary(), load_results(), MetricsAgent, … (+4) |
| 496 | [Community 555](#c-555) | 15 | 0.14 | MockJob, MockNode, MockStateStore, Test 3: Deduplication — scheduler must not double-submit., test_backpressure_throttles_queue(), … (+3) |
| 497 | [Community 579](#c-579) | 15 | 0.14 | MockJob, MockNode, MockStateStore, Test 3: Deduplication — scheduler must not double-submit., test_backpressure_throttles_queue(), … (+3) |
| 498 | [Community 382](#c-382) | 15 | 0.13 | NodeWeightsSnapshot, ConsensusCandidate, ConsensusResult, ConsensusShiftEvent, ConsensusShiftType, … (+4) |
| 499 | [Community 559](#c-559) | 15 | 0.13 | Any, classifier(), ClassifiedFailure, FailureCategory, FailureClassifier, … (+3) |
| 500 | [Community 392](#c-392) | 15 | 0.12 | main(), MCPAdapter, MCP Adapter for Smithery/GitHub Tools Integrates with Smithery MCP registry to s, Search Smithery registry for MCP servers matching query.                  Args:, MCP Adapter that integrates with Smithery registry to search, … (+5) |
| 501 | [Community 397](#c-397) | 15 | 0.12 | main(), MCPAdapter, MCP Adapter for Smithery/GitHub Tools Integrates with Smithery MCP registry to s, Search Smithery registry for MCP servers matching query.                  Args:, MCP Adapter that integrates with Smithery registry to search, … (+5) |
| 502 | [Community 404](#c-404) | 15 | 0.12 | create_live_provider(), _get_exchange(), LiveDataProvider, meta_rl/live_data.py — ATOM-META-RL-006: Production CCXT Integration  Supports b, Enforce rate limiting between requests., … (+5) |
| 503 | [Community 407](#c-407) | 15 | 0.12 | AdaptiveSlippageModel, OrderBookSimulator, AdaptiveSlippageModel, OrderBookSimulator, AdaptiveSlippageModel, … (+3) |
| 504 | [Community 410](#c-410) | 15 | 0.12 | create_live_provider(), _get_exchange(), LiveDataProvider, meta_rl/live_data.py — ATOM-META-RL-006: Production CCXT Integration  Supports b, Enforce rate limiting between requests., … (+5) |
| 505 | [Community 417](#c-417) | 15 | 0.12 | create_live_provider(), _get_exchange(), LiveDataProvider, meta_rl/live_data.py — ATOM-META-RL-006: Production CCXT Integration  Supports b, Enforce rate limiting between requests., … (+5) |
| 506 | [Community 826](#c-826) | 15 | 0.12 | DurableTaskQueue (минимальные правки), engine.py рефакторинг, Epoch semantics (критично), Fail policy, GLOBAL TASK LIFECYCLE SPEC — единый control plane, … (+3) |
| 507 | [Community 831](#c-831) | 15 | 0.12 | 10. История изменений, 1. Цель, 2.1. Trigger, 2.2. Audience, 2.3. Язык и стиль, … (+3) |
| 508 | [Community 848](#c-848) | 15 | 0.12 | 10. История изменений, 1. Цель, 2.1. Trigger, 2.2. Audience, 2.3. Язык и стиль, … (+3) |
| 509 | [Community 857](#c-857) | 15 | 0.12 | 10. История изменений, 1. Цель, 2.1. Trigger, 2.2. Audience, 2.3. Язык и стиль, … (+3) |
| 510 | [Community 860](#c-860) | 15 | 0.12 | 1. Создание Fine-grained PAT, 2. Настройка remote и push с PAT, 3. `.github/workflows/infra-ci.yml` (только проверки, без deploy), 4. `.github/workflows/deploy.yml` (self-hosted runner, … (+5) |
| 511 | [Community 872](#c-872) | 15 | 0.12 | 1. Восстановление из бэкапа, 2. Исправлены критические ошибки, 3. Production-ready pyproject.toml, 4. Обновлён README.md, 5. Обновлён .gitignore, … (+3) |
| 512 | [Community 874](#c-874) | 15 | 0.12 | 10. История изменений, 1. Цель, 2.1. Trigger, 2.2. Audience, 2.3. Язык и стиль, … (+3) |
| 513 | [Community 354](#c-354) | 15 | 0.11 | ndarray, Invariant, TestSpectralInvariant, InvariantChecker, InvariantViolation, … (+3) |
| 514 | [Community 291](#c-291) | 15 | 0.10 | Any, DeterministicTraceLedger, r'''         Append multiple events atomically (same tick).          Args:, r'''     A single entry in the DeterministicTraceLedger.      order_key format:, Get all entries for a specific tick, … (+5) |
| 515 | [Community 387](#c-387) | 15 | 0.10 | GlobalStateModel, GlobalStateRecord, Resolve conflict between two records using resolution strategy.         Returns, Verify consistency invariant for a job.         Returns dict of field -> is_cons, Returns GPU saturation 0.0-1.0 (VRAM used / VRAM available).         Used for ba, … (+4) |
| 516 | [Community 543](#c-543) | 15 | 0.10 | test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests + Constraints, 7.1 Конфликт: BUY vs SELL., Regime discount в EXTREME., В EXTREME regime agent получает ×0.4 influence.         A(BUY, EXTREME) и B(BUY, … (+8) |
| 517 | [Community 563](#c-563) | 15 | 0.10 | test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests + Constraints, 8. Ограничения: не менять signal., Signal не меняется после apply_pressure_field., 7.1 Конфликт: BUY vs SELL., Regime discount в EXTREME., … (+6) |
| 518 | [Community 573](#c-573) | 15 | 0.10 | test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests + Constraints, 8. Ограничения: не менять signal., Signal не меняется после apply_pressure_field., 7.1 Конфликт: BUY vs SELL., Regime discount в EXTREME., … (+6) |
| 519 | [Community 159](#c-159) | 15 | 0.09 | any, DAGHashMode, AntiEntropy, MerkleNode, AntiEntropy — merkle-tree reconciliation between federation peers.  Implements t, … (+3) |
| 520 | [Community 237](#c-237) | 15 | 0.09 | Any, ndarray, Path, LedgerEntry, MutationLedger, … (+3) |
| 521 | [Community 513](#c-513) | 15 | 0.09 | Any, ExecutionEngineContract, ACOS Engine Contract — enforced execution engine interface., validate_engine_contract(), Persist full execution trace. MUST return trace_id (str)., … (+3) |
| 522 | [Community 183](#c-183) | 15 | 0.08 | GossipConfig, QuorumConfig, SeverityLevel, StateVector, NodeMetrics, … (+3) |
| 523 | [Community 297](#c-297) | 15 | 0.08 | DeltaRouter, DeltaRouter — delta routing and sequence tracking.  Tracks per-peer fingerprint, Return list of peer IDs whose latest fingerprint differs from my_root_hash., Return (seq, root_hash) for a peer, … (+5) |
| 524 | [Community 198](#c-198) | 15 | 0.07 | Node entrypoint — runs inside container.  Usage (inside container):     python e, ClusterNode, On boot, each node:           1. Waits briefly for peers to also boot, Background: ping peers every 5s, … (+7) |
| 525 | [Community 208](#c-208) | 15 | 0.07 | tests/test_kepler.py — ATOM-STEP-1: Kepler Engine Tests Tests core/kepler.py: or, At epoch JD, M is mean_longitude - long_perihelion (mod 360)., Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., … (+4) |
| 526 | [Community 340](#c-340) | 15 | 0.07 | DeterministicTraceRecorder, ACOS TraceRecorder — fully contract-compliant implementation., DeterministicTraceRecorder, EventSourcedEngine, Clear all traces. For testing only., … (+3) |
| 527 | [Community 167](#c-167) | 15 | 0.06 | OrbitalElements, Keplerian orbital elements for a solar system body at epoch J2000.0., tests/test_kepler.py — ATOM-STEP-1: Kepler Engine Tests Tests core/kepler.py: or, At epoch JD, M is mean_longitude - long_perihelion (mod 360)., … (+4) |
| 528 | [Community 926](#c-926) | 14 | 0.42 | day6_ceph.sh script, create_mount_script(), create_pools(), deploy_ceph(), deploy_manual(), … (+3) |
| 529 | [Community 928](#c-928) | 14 | 0.41 | vault-init.sh script, apply_sealed_secret_templates(), check_prereq(), create_secrets_engine(), create_static_secrets(), … (+3) |
| 530 | [Community 924](#c-924) | 14 | 0.38 | day3_compute.sh script, detect_os(), info(), install_common(), install_docker(), … (+3) |
| 531 | [Community 835](#c-835) | 14 | 0.23 | Any, export_strategy(), ExportResult, load_strategy(), meta_rl/git_agent_exporter.py — ATOM-META-RL-013: GitAgent Export for Strategies, … (+3) |
| 532 | [Community 852](#c-852) | 14 | 0.23 | Any, export_strategy(), ExportResult, load_strategy(), meta_rl/git_agent_exporter.py — ATOM-META-RL-013: GitAgent Export for Strategies, … (+3) |
| 533 | [Community 867](#c-867) | 14 | 0.23 | Any, export_strategy(), ExportResult, load_strategy(), meta_rl/git_agent_exporter.py — ATOM-META-RL-013: GitAgent Export for Strategies, … (+3) |
| 534 | [Community 877](#c-877) | 14 | 0.23 | Any, export_strategy(), ExportResult, load_strategy(), meta_rl/git_agent_exporter.py — ATOM-META-RL-013: GitAgent Export for Strategies, … (+3) |
| 535 | [Community 894](#c-894) | 14 | 0.19 | Any, analyze_oap_drift(), get_adaptive_params_from_drift(), load_all_records(), load_session_records(), … (+3) |
| 536 | [Community 906](#c-906) | 14 | 0.19 | AMREOutput, apply_fallback(), check_delisted_fallback(), DelistFallback, get_karl_diagnostics(), … (+3) |
| 537 | [Community 913](#c-913) | 14 | 0.19 | Any, analyze_oap_drift(), get_adaptive_params_from_drift(), load_all_records(), load_session_records(), … (+3) |
| 538 | [Community 931](#c-931) | 14 | 0.19 | Any, analyze_oap_drift(), get_adaptive_params_from_drift(), load_all_records(), load_session_records(), … (+3) |
| 539 | [Community 934](#c-934) | 14 | 0.19 | AMREOutput, apply_fallback(), check_delisted_fallback(), DelistFallback, get_karl_diagnostics(), … (+3) |
| 540 | [Community 941](#c-941) | 14 | 0.19 | Any, analyze_oap_drift(), get_adaptive_params_from_drift(), load_all_records(), load_session_records(), … (+3) |
| 541 | [Community 326](#c-326) | 14 | 0.18 | Tenant, TenantCreate, saas/tenants/manager.py CRUD operations for tenant management., TenantManager, TenantNotFoundError, … (+3) |
| 542 | [Community 751](#c-751) | 14 | 0.16 | AgentResponse, Any, agents/_impl/_template_agent.py ================================ Canonical templ, # TODO: implement the actual analysis., Public entry point. Wraps `analyze` with the latency histogram         and a def, … (+4) |
| 543 | [Community 444](#c-444) | 14 | 0.13 | DivergenceResponsePolicy, InterventionLevel, Divergence Response Policy — v7.4 Threshold-driven intervention policy: decides, Main evaluation entry point.          Args:             global_coherence: overal, Compute rate of coherence change (per second).         Uses last 2 data points i, … (+4) |
| 544 | [Community 534](#c-534) | 14 | 0.13 | ControlPrimitive, ControlVector, Swarm Control Surface — v7.4 Maps global S_full (from distributed_tensor_alignme, Map the global S_full tensor (canonical + deltas) into control vectors., Resolve conflicts when multiple vectors target same worker+axis.         Resolut, … (+4) |
| 545 | [Community 550](#c-550) | 14 | 0.13 | get_alerter(), meta_rl/alerts.py — ATOM-META-RL-006: Telegram Alerts (P1.3)  Sends alerts to Te, Alert when a strategy exceeds min_reward threshold.          Use after each evol, Alert when evolution run completes.         Includes summary of all generations., Alert when walk-forward analysis detects overfitting., … (+3) |
| 546 | [Community 569](#c-569) | 14 | 0.13 | get_alerter(), meta_rl/alerts.py — ATOM-META-RL-006: Telegram Alerts (P1.3)  Sends alerts to Te, Alert when a strategy exceeds min_reward threshold.          Use after each evol, Alert when evolution run completes.         Includes summary of all generations., Alert when walk-forward analysis detects overfitting., … (+3) |
| 547 | [Community 582](#c-582) | 14 | 0.13 | get_alerter(), meta_rl/alerts.py — ATOM-META-RL-006: Telegram Alerts (P1.3)  Sends alerts to Te, Alert when a strategy exceeds min_reward threshold.          Use after each evol, Alert when evolution run completes.         Includes summary of all generations., Alert when walk-forward analysis detects overfitting., … (+3) |
| 548 | [Community 590](#c-590) | 14 | 0.13 | get_alerter(), meta_rl/alerts.py — ATOM-META-RL-006: Telegram Alerts (P1.3)  Sends alerts to Te, Alert when a strategy exceeds min_reward threshold.          Use after each evol, Alert when evolution run completes.         Includes summary of all generations., Alert when walk-forward analysis detects overfitting., … (+3) |
| 549 | [Community 667](#c-667) | 14 | 0.13 | analyze(), cli(), cprint(), main(), metrics(), … (+3) |
| 550 | [Community 688](#c-688) | 14 | 0.13 | analyze(), cli(), cprint(), main(), metrics(), … (+3) |
| 551 | [Community 707](#c-707) | 14 | 0.13 | analyze(), cli(), cprint(), main(), metrics(), … (+3) |
| 552 | [Community 718](#c-718) | 14 | 0.13 | analyze(), cli(), cprint(), main(), metrics(), … (+3) |
| 553 | [Community 884](#c-884) | 14 | 0.13 | INV1: Every action produces an event., INV2: No mutable truth — state is derived., INV3: Replay equivalence., INV4: Hash chain integrity., TraceRecorder = projection over event stream., … (+3) |
| 554 | [Community 885](#c-885) | 14 | 0.13 | INV1: Every action produces an event., INV2: No mutable truth — state is derived., INV3: Replay equivalence., INV5: Trace determinism — same events → identical result., Full trace: DAG_CREATED → TRACE_RECORDED., … (+3) |
| 555 | [Community 892](#c-892) | 14 | 0.13 | 1. Общее описание, 2. Архитектура системы, 3. 14 агентов — веса и задачи, 4. Meta-RL Engine — как работает, 5. Как запустить, … (+3) |
| 556 | [Community 902](#c-902) | 14 | 0.13 | Быстрый старт (итог), Если что-то пошло не так, Запутался в окружениях, Команды SBS, Ошибка: `command not found: sbs`, … (+3) |
| 557 | [Community 904](#c-904) | 14 | 0.13 | 🟢 ATOMFederation-OS Production Readiness Audit, ❌ CRITICAL-1: Determinism — not fully resolved, ❌ CRITICAL-2: SBS Dependency Isolation, ❌ CRITICAL-3: No CI/CD Enforcement, ❌ CRITICAL-4: Persistence Gap, … (+3) |
| 558 | [Community 911](#c-911) | 14 | 0.13 | 1. Общее описание, 2. Архитектура системы, 3. 14 агентов — веса и задачи, 4. Meta-RL Engine — как работает, 5. Как запустить, … (+3) |
| 559 | [Community 919](#c-919) | 14 | 0.13 | 1. 🔴 Network Partition (split-brain), 2. 🔴 Asymmetric Partition, 3. 🔴 Packet Corruption, 4. 🔴 Latency Spike (Jitter Storm), 5. 🔴 Node Isolation (C minority partition), … (+3) |
| 560 | [Community 939](#c-939) | 14 | 0.13 | 1. Общее описание, 2. Архитектура системы, 3. 14 агентов — веса и задачи, 4. Meta-RL Engine — как работает, 5. Как запустить, … (+3) |
| 561 | [Community 330](#c-330) | 14 | 0.12 | One-call factory for standard AstroFin policy., Compiles AstroFin YAML/policy text → executable Constraint DAG.     DAG structur, Any, AstroFinConstraintCompiler, build_astrofin_policy(), … (+3) |
| 562 | [Community 331](#c-331) | 14 | 0.12 | One-call factory for standard AstroFin policy., Compiles AstroFin YAML/policy text → executable Constraint DAG.     DAG structur, Any, AstroFinConstraintCompiler, build_astrofin_policy(), … (+3) |
| 563 | [Community 380](#c-380) | 14 | 0.12 | Constraint, ConstraintGraph, ConstraintType, NodeV, All constraints involving a specific node., … (+3) |
| 564 | [Community 388](#c-388) | 14 | 0.12 | Check if job can be placed on node.         Returns (valid, list_of_violation_re, Sum of resource usage by all jobs on node (excluding job_id)., Directed constraint graph G = (V, E).     V: compute nodes, … (+8) |
| 565 | [Community 430](#c-430) | 14 | 0.12 | PolicyGovernor, PolicySnapshot, PolicyUpdate, Return policy history, most recent first., … (+4) |
| 566 | [Community 439](#c-439) | 14 | 0.12 | PolicyGovernor, PolicySnapshot, PolicyUpdate, Exponential moving average., Queue a policy update for next cycle.         Returns True if update passes stab, … (+4) |
| 567 | [Community 229](#c-229) | 14 | 0.11 | trust_vector.py — v9.5 TrustVector  Purpose:   TrustVector is a compact, determi, Set or update a trust entry., Remove a proof_hash entry (proof pruned from ledger)., Return a deep copy of the current vector as an immutable snapshot., … (+4) |
| 568 | [Community 336](#c-336) | 14 | 0.11 | Any, ndarray, Path, v8.2a — Controlled Autocorrection Foundation Mutation Safety Kernel (MSK)  Modul, Checkpoint, … (+3) |
| 569 | [Community 457](#c-457) | 14 | 0.11 | MarketImpactModel, MarketImpactResult, OrderBookLevel, OrderBookSimulator, OrderBookSnapshot, … (+3) |
| 570 | [Community 476](#c-476) | 14 | 0.11 | MarketImpactModel, MarketImpactResult, OrderBookLevel, OrderBookSimulator, OrderBookSnapshot, … (+3) |
| 571 | [Community 496](#c-496) | 14 | 0.11 | MarketImpactModel, MarketImpactResult, OrderBookLevel, OrderBookSimulator, OrderBookSnapshot, … (+3) |
| 572 | [Community 234](#c-234) | 14 | 0.10 | Any, CausalSemanticVector, _dict_diff(), _l2_norm(), causal_semantic_space.py ======================== v7.2 — CausalSemanticSpace: em, … (+4) |
| 573 | [Community 406](#c-406) | 14 | 0.10 | AccountBalance, BaseBroker, Order, OrderSide, OrderStatus, … (+3) |
| 574 | [Community 411](#c-411) | 14 | 0.10 | AccountBalance, BaseBroker, Order, OrderSide, OrderStatus, … (+3) |
| 575 | [Community 412](#c-412) | 14 | 0.10 | BackpressureConfig, BackpressureStatus, BackpressureSystem, Backpressure System — GPU saturation control + queue throttling. Implements: loa, Record that a job started using VRAM., … (+3) |
| 576 | [Community 421](#c-421) | 14 | 0.10 | AccountBalance, BaseBroker, Order, OrderSide, OrderStatus, … (+3) |
| 577 | [Community 530](#c-530) | 14 | 0.09 | test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests + Constraints, Non-neutral agents always have magnitude 1.0., 7.1 Конфликт: BUY vs SELL., Regime discount в EXTREME., В EXTREME regime agent получает ×0.4 influence.         A(BUY, … (+8) |
| 578 | [Community 212](#c-212) | 14 | 0.08 | APIKeyManager, ROMA API Key System — Scoped keys with rotation., Organization, ROMA Organization Model — org → project → tenant hierarchy., ROMA RBAC Engine — Role-based permissions., … (+3) |
| 579 | [Community 228](#c-228) | 14 | 0.06 | Tests for TaskStore — единый source of truth.  Covers: - claim_task: only PENDIN, Zombie worker A (epoch=1) is stuck. Worker B recovers the task (epoch=2), co, Fresh store pointing to test DB., 10 workers racing to claim the same PENDING task.     Exactly 1 must win — all o, … (+5) |
| 580 | [Community 967](#c-967) | 13 | 0.46 | create_mount_script(), create_pools(), deploy_ceph(), deploy_manual(), info(), … (+3) |
| 581 | [Community 966](#c-966) | 13 | 0.42 | detect_os(), info(), install_common(), install_docker(), install_munge(), … (+3) |
| 582 | [Community 900](#c-900) | 13 | 0.38 | check_munge(), configure_worker(), create_cgroup_conf(), create_gres_conf(), create_slurm_conf(), … (+3) |
| 583 | [Community 925](#c-925) | 13 | 0.38 | day4_slurm.sh script, check_munge(), configure_worker(), create_cgroup_conf(), create_gres_conf(), … (+3) |
| 584 | [Community 889](#c-889) | 13 | 0.20 | AgentSignal, apply_pressure_field(), apply_pressure_field_with_metrics(), compute_similarity(), get_regime_multiplier(), … (+3) |
| 585 | [Community 908](#c-908) | 13 | 0.20 | AgentSignal, apply_pressure_field(), apply_pressure_field_with_metrics(), compute_similarity(), get_regime_multiplier(), … (+3) |
| 586 | [Community 921](#c-921) | 13 | 0.20 | AgentSignal, apply_pressure_field(), apply_pressure_field_with_metrics(), compute_similarity(), get_regime_multiplier(), … (+3) |
| 587 | [Community 936](#c-936) | 13 | 0.20 | AgentSignal, apply_pressure_field(), apply_pressure_field_with_metrics(), compute_similarity(), get_regime_multiplier(), … (+3) |
| 588 | [Community 960](#c-960) | 13 | 0.20 | create_test_app(), import pytest Unit tests for the Flask `require_api_key` decorator. These tests, When REQUIRE_AUTH=false, all requests should succeed., Create a Flask test app with a protected endpoint., … (+5) |
| 589 | [Community 981](#c-981) | 13 | 0.20 | create_test_app(), import pytest Unit tests for the Flask `require_api_key` decorator. These tests, When REQUIRE_AUTH=false, all requests should succeed., Create a Flask test app with a protected endpoint., … (+5) |
| 590 | [Community 1007](#c-1007) | 13 | 0.20 | create_test_app(), import pytest Unit tests for the Flask `require_api_key` decorator. These tests, When REQUIRE_AUTH=false, all requests should succeed., Create a Flask test app with a protected endpoint., … (+5) |
| 591 | [Community 1010](#c-1010) | 13 | 0.20 | create_test_app(), Unit tests for the Flask `require_api_key` decorator.  These tests verify authen, test_require_api_key_auth_disabled(), test_require_api_key_correct_key(), test_require_api_key_empty_env_key_should_reject_all(), … (+4) |
| 592 | [Community 603](#c-603) | 13 | 0.18 | AgentResponse, Any, CompromiseAgent, _next_long(), _next_short(), … (+3) |
| 593 | [Community 625](#c-625) | 13 | 0.18 | print_topology_viz(), Generate ASCII art topology, Generates Mermaid and DOT visualizations from Topology, Export topology as JSON, Save all visualizations to files, … (+3) |
| 594 | [Community 637](#c-637) | 13 | 0.18 | print_topology_viz(), Generate ASCII art topology, Generates Mermaid and DOT visualizations from Topology, Export topology as JSON, Save all visualizations to files, … (+3) |
| 595 | [Community 642](#c-642) | 13 | 0.18 | AgentResponse, Any, CompromiseAgent, _next_long(), _next_short(), … (+3) |
| 596 | [Community 958](#c-958) | 13 | 0.18 | Any, denormalize_symbol(), market_data_to_ohlcv(), normalize_symbol(), ohlcv_to_strategy_format(), … (+3) |
| 597 | [Community 979](#c-979) | 13 | 0.18 | Any, denormalize_symbol(), market_data_to_ohlcv(), normalize_symbol(), ohlcv_to_strategy_format(), … (+3) |
| 598 | [Community 994](#c-994) | 13 | 0.18 | Any, denormalize_symbol(), market_data_to_ohlcv(), normalize_symbol(), ohlcv_to_strategy_format(), … (+3) |
| 599 | [Community 1004](#c-1004) | 13 | 0.18 | Any, denormalize_symbol(), market_data_to_ohlcv(), normalize_symbol(), ohlcv_to_strategy_format(), … (+3) |
| 600 | [Community 556](#c-556) | 13 | 0.17 | DigitalTwin, JobState, NodeState, PredictedEvent, SimAction, … (+3) |
| 601 | [Community 784](#c-784) | 13 | 0.17 | Request, ab_compare(), auth_middleware(), check_postgres(), check_redis(), … (+3) |
| 602 | [Community 1025](#c-1025) | 13 | 0.17 | Any, DataFrame, _init_shap(), load_model(), _on_startup(), … (+5) |
| 603 | [Community 950](#c-950) | 13 | 0.16 | agent_counter(), agent_latency(), agents/metrics.py ================= Shared Prometheus metrics factory and `@trac, Return the canonical ``sentinel_<agent_snake>_latency_seconds`` Histogram., Decorator that times ``func`` and increments the per-agent run Counter.      Wor, … (+3) |
| 604 | [Community 953](#c-953) | 13 | 0.16 | agent_counter(), agent_latency(), agents/metrics.py ================= Shared Prometheus metrics factory and `@trac, Return the canonical ``sentinel_<agent_snake>_latency_seconds`` Histogram., Decorator that times ``func`` and increments the per-agent run Counter.      Wor, … (+3) |
| 605 | [Community 974](#c-974) | 13 | 0.16 | agent_counter(), agent_latency(), agents/metrics.py ================= Shared Prometheus metrics factory and `@trac, Return the canonical ``sentinel_<agent_snake>_latency_seconds`` Histogram., Decorator that times ``func`` and increments the per-agent run Counter.      Wor, … (+3) |
| 606 | [Community 997](#c-997) | 13 | 0.16 | agent_counter(), agent_latency(), agents/metrics.py ================= Shared Prometheus metrics factory and `@trac, Return the canonical ``sentinel_<agent_snake>_latency_seconds`` Histogram., Decorator that times ``func`` and increments the per-agent run Counter.      Wor, … (+3) |
| 607 | [Community 460](#c-460) | 13 | 0.15 | ClusterSnapshot, ScheduleAction, UtilityFunction, UtilityWeights, Epsilon-greedy exploration bonus for trying new configurations., … (+4) |
| 608 | [Community 491](#c-491) | 13 | 0.15 | KeplerOrbit, propagate_kepler(), core/kepler.py — ATOM-STEP-1: Kepler Orbital Mechanics Engine ==================, M = M₀ + n · (JD - JD₀)  [degrees], Solve M = E - e·sin(E) via Newton-Raphson.         M, … (+5) |
| 609 | [Community 551](#c-551) | 13 | 0.15 | any, meta_rl/walkforward.py — ATOM-META-RL-006: Walk-Forward Out-of-Sample Validation, Walk-forward analysis to detect overfitting in evolved strategies.      Usage:, Run full walk-forward analysis on a strategy.          Args:             strateg, Evaluate strategy on train and test windows., … (+3) |
| 610 | [Community 570](#c-570) | 13 | 0.15 | any, meta_rl/walkforward.py — ATOM-META-RL-006: Walk-Forward Out-of-Sample Validation, Walk-forward analysis to detect overfitting in evolved strategies.      Usage:, Run full walk-forward analysis on a strategy.          Args:             strateg, Evaluate strategy on train and test windows., … (+3) |
| 611 | [Community 583](#c-583) | 13 | 0.15 | any, meta_rl/walkforward.py — ATOM-META-RL-006: Walk-Forward Out-of-Sample Validation, Walk-forward analysis to detect overfitting in evolved strategies.      Usage:, Run full walk-forward analysis on a strategy.          Args:             strateg, Evaluate strategy on train and test windows., … (+3) |
| 612 | [Community 451](#c-451) | 13 | 0.14 | Experience, OnlineTrainer, PolicyParams, core/online_trainer.py — ATOM-STEP-6: Online RL Trainer ========================, Add experience to replay buffer., … (+3) |
| 613 | [Community 455](#c-455) | 13 | 0.14 | EvaluationResult, meta_rl/reward.py — ATOM-META-RL-004: Risk-Adjusted Reward Function, Map Sharpe ratio to reward. Cap at 5.0 (diminishing returns)., Normalize risk-adjusted PnL. 100% return -> 1.0, -100% -> 0.0.          ATOM-MET, … (+4) |
| 614 | [Community 471](#c-471) | 13 | 0.14 | Experience, OnlineTrainer, PolicyParams, core/online_trainer.py — ATOM-STEP-6: Online RL Trainer ========================, Add experience to replay buffer., … (+3) |
| 615 | [Community 474](#c-474) | 13 | 0.14 | EvaluationResult, meta_rl/reward.py — ATOM-META-RL-004: Risk-Adjusted Reward Function, Map Sharpe ratio to reward. Cap at 5.0 (diminishing returns)., Normalize risk-adjusted PnL. 100% return -> 1.0, -100% -> 0.0.          ATOM-MET, … (+4) |
| 616 | [Community 480](#c-480) | 13 | 0.14 | Experience, OnlineTrainer, PolicyParams, core/online_trainer.py — ATOM-STEP-6: Online RL Trainer ========================, Add experience to replay buffer., … (+3) |
| 617 | [Community 494](#c-494) | 13 | 0.14 | EvaluationResult, meta_rl/reward.py — ATOM-META-RL-004: Risk-Adjusted Reward Function, Map Sharpe ratio to reward. Cap at 5.0 (diminishing returns)., Normalize risk-adjusted PnL. 100% return -> 1.0, -100% -> 0.0.          ATOM-MET, … (+4) |
| 618 | [Community 514](#c-514) | 13 | 0.14 | MetricsCollector, MetricThresholds, Pull admission rates from scheduler API., Full system observation snapshot., SystemMetrics, … (+3) |
| 619 | [Community 528](#c-528) | 13 | 0.14 | MetricsCollector, MetricThresholds, Query Prometheus for real metrics., Full system observation snapshot., SystemMetrics, … (+3) |
| 620 | [Community 553](#c-553) | 13 | 0.14 | AdaptiveSlippageModel, trading/execution/twap.py — ATOM-STEP-10: TWAP Execution Strategy, TWAPConfig, TWAPExecutionReport, TWAPExecutor, … (+3) |
| 621 | [Community 957](#c-957) | 13 | 0.14 | ❌ AVOID (Score < 4.0):, ✅ ENTER (Score >= 6.5):, Muhurta — Искусство выбора времени, Overview, Trade Entry Rules, … (+3) |
| 622 | [Community 961](#c-961) | 13 | 0.14 | Application Inventory, Architecture, Deployment Workflow, GitOps Deployment with ArgoCD, Image Updates, … (+3) |
| 623 | [Community 971](#c-971) | 13 | 0.14 | Planned, Pop!_OS 24.04 — AI/Dev Workstation Setup, Release Notes, Stage Map, v1.0 — Initial (2026-03-28), … (+3) |
| 624 | [Community 978](#c-978) | 13 | 0.14 | ❌ AVOID (Score < 4.0):, ✅ ENTER (Score >= 6.5):, Muhurta — Искусство выбора времени, Overview, Trade Entry Rules, … (+3) |
| 625 | [Community 982](#c-982) | 13 | 0.14 | test_incremental_causal_verifier.py =================================== Tests fo, Fingerprint changes on add, is_identical works on same content., Different events produce different fingerprints., Verifier correctly detects equivalence., … (+4) |
| 626 | [Community 985](#c-985) | 13 | 0.14 | Adding a New Partner, Architecture, Branding in API Responses, Caching, Email Templates, … (+3) |
| 627 | [Community 991](#c-991) | 13 | 0.14 | Architecture Diagram, Conclusion, Dashboard Evaluation: LangGraph vs n8n, Executive Summary, Implementation Strategy, … (+3) |
| 628 | [Community 993](#c-993) | 13 | 0.14 | ❌ AVOID (Score < 4.0):, ✅ ENTER (Score >= 6.5):, Muhurta — Искусство выбора времени, Overview, Trade Entry Rules, … (+3) |
| 629 | [Community 1000](#c-1000) | 13 | 0.14 | Architecture Diagram, Conclusion, Dashboard Evaluation: LangGraph vs n8n, Executive Summary, Implementation Strategy, … (+3) |
| 630 | [Community 1002](#c-1002) | 13 | 0.14 | ❌ AVOID (Score < 4.0):, ✅ ENTER (Score >= 6.5):, Muhurta — Искусство выбора времени, Overview, Trade Entry Rules, … (+3) |
| 631 | [Community 381](#c-381) | 13 | 0.13 | Any, Singleton — only one guard instance per process., Get the singleton guard instance., Invariant 1: len(entry_points) == 1          Scans ALL loaded modules for 'execu, Invariant 2: ExecutionGateway dominates all mutation call stacks.          Verif, … (+3) |
| 632 | [Community 427](#c-427) | 13 | 0.13 | AgentResponse, Any, datetime, AstroFin Sentinel v5 — Technical Agent Технический анализ: RSI, MACD, … (+7) |
| 633 | [Community 434](#c-434) | 13 | 0.13 | AgentResponse, Any, datetime, AstroFin Sentinel v5 — Technical Agent Технический анализ: RSI, MACD, … (+7) |
| 634 | [Community 438](#c-438) | 13 | 0.13 | demo(), execute_on_gpu(), get_gpu_connector(), GPUWorkerPool, Check if any GPU worker is available., … (+3) |
| 635 | [Community 483](#c-483) | 13 | 0.13 | predict(), Predictor, Compute composite risk score from predictions., Decision recommendation based on risk., Path, … (+3) |
| 636 | [Community 500](#c-500) | 13 | 0.13 | AgentResponse, BearResearcherAgent, Bear Researcher Agent — bearish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram and defensive err, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 637 | [Community 501](#c-501) | 13 | 0.13 | AgentResponse, CycleAgent, Cycle Agent — market timing cycles analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 638 | [Community 502](#c-502) | 13 | 0.13 | AgentResponse, GannAgent, Gann Agent — Gann angles and time/price analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+5) |
| 639 | [Community 503](#c-503) | 13 | 0.13 | AgentResponse, MacroAgent, MacroAgent — macroeconomic & geopolitical risk analysis.  Indicators: - VIX (fea, Analyze VIX fear index., Analyze DXY (dollar index). Strong dollar → pressure on risk assets., … (+3) |
| 640 | [Community 506](#c-506) | 13 | 0.13 | AgentResponse, BearResearcherAgent, Bear Researcher Agent — bearish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram and defensive err, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 641 | [Community 507](#c-507) | 13 | 0.13 | AgentResponse, BullResearcherAgent, Bull Researcher Agent — bullish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 642 | [Community 508](#c-508) | 13 | 0.13 | AgentResponse, CycleAgent, Cycle Agent — market timing cycles analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 643 | [Community 509](#c-509) | 13 | 0.13 | AgentResponse, GannAgent, Gann Agent — Gann angles and time/price analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+5) |
| 644 | [Community 510](#c-510) | 13 | 0.13 | AgentResponse, MacroAgent, MacroAgent — macroeconomic & geopolitical risk analysis.  Indicators: - VIX (fea, Analyze VIX fear index., Analyze DXY (dollar index). Strong dollar → pressure on risk assets., … (+3) |
| 645 | [Community 519](#c-519) | 13 | 0.13 | AgentResponse, BearResearcherAgent, Bear Researcher Agent — bearish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram and defensive err, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 646 | [Community 520](#c-520) | 13 | 0.13 | AgentResponse, BullResearcherAgent, Bull Researcher Agent — bullish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 647 | [Community 521](#c-521) | 13 | 0.13 | AgentResponse, CycleAgent, Cycle Agent — market timing cycles analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+3) |
| 648 | [Community 522](#c-522) | 13 | 0.13 | AgentResponse, GannAgent, Gann Agent — Gann angles and time/price analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., … (+5) |
| 649 | [Community 523](#c-523) | 13 | 0.13 | AgentResponse, MacroAgent, MacroAgent — macroeconomic & geopolitical risk analysis.  Indicators: - VIX (fea, Analyze VIX fear index., Analyze DXY (dollar index). Strong dollar → pressure on risk assets., … (+3) |
| 650 | [Community 577](#c-577) | 13 | 0.13 | Determine label: did node fail within horizon_minutes?, Build MLBatch with train/val/test splits (time-based 80/10/10).         Returns, Export a split to CSV file. Returns path., Export full dataset to JSON. Returns path., Export full dataset to Parquet (if pyarrow available). Returns path., … (+3) |
| 651 | [Community 350](#c-350) | 13 | 0.12 | Any, get_safety_gate(), MarketMode, Synchronous check. Returns SafetyDecision immediately.          Если SAFETY_STAC, Async wrapper — delegates to sync check (all components are fast)., … (+3) |
| 652 | [Community 363](#c-363) | 13 | 0.12 | Any, get_safety_gate(), MarketMode, Synchronous check. Returns SafetyDecision immediately.          Если SAFETY_STAC, Async wrapper — delegates to sync check (all components are fast)., … (+3) |
| 653 | [Community 371](#c-371) | 13 | 0.12 | Any, get_safety_gate(), MarketMode, Synchronous check. Returns SafetyDecision immediately.          Если SAFETY_STAC, Async wrapper — delegates to sync check (all components are fast)., … (+3) |
| 654 | [Community 418](#c-418) | 13 | 0.12 | EvaluationMetricsCollector, Combined entropy of 4D score components., Fraction of ticks with at least one replan., Average number of coherence drops per tick.         A drop = consecutive decreas, Average number of coherence recoveries per tick.         A recovery = consecutiv, … (+4) |
| 655 | [Community 785](#c-785) | 13 | 0.12 | Any, Decision, ExecutionResult, ACOS Trace Contract — enforced TraceRecorder interface., Fetch trace. MUST return dict or None., … (+3) |
| 656 | [Community 251](#c-251) | 13 | 0.11 | Damped feedback controller for the actuator layer.      Monitors the error signa, StabilityFeedbackController, Tests for StabilityFeedbackController — v7.4 Oscillation prevention and damped f, Gain adjustment computation in each mode., Adaptive gain converges toward 1.0 when stable., … (+3) |
| 657 | [Community 400](#c-400) | 13 | 0.11 | Request, MockLedger, Tests for RevenueShareCalculator + Stripe Webhook., test_ledger_revenue_share_ext(), test_tiered_rates(), … (+5) |
| 658 | [Community 295](#c-295) | 13 | 0.09 | HostChaosAgent, NetworkPartitioner, NetworkPartitioner — nftables/iptables DOCKER-USER chain injector.  Provides a c, Remove all CHAOS_RULE-marked rules from DOCKER-USER.          Returns number of, Return list of CHAOS rules currently in DOCKER-USER., … (+3) |
| 659 | [Community 210](#c-210) | 13 | 0.08 | TestAmneziaWG, TestEventLog, TestPayloadToDict, TestReducerEdgeCases, TestSecurity, … (+3) |
| 660 | [Community 232](#c-232) | 13 | 0.06 | tests/test_kepler.py — ATOM-STEP-1: Kepler Engine Tests Tests core/kepler.py: or, At epoch JD, M is mean_longitude - long_perihelion (mod 360)., Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., … (+4) |
| 661 | [Community 240](#c-240) | 13 | 0.06 | tests/test_kepler.py — ATOM-STEP-1: Kepler Engine Tests Tests core/kepler.py: or, At epoch JD, M is mean_longitude - long_perihelion (mod 360)., Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., … (+4) |
| 662 | [Community 249](#c-249) | 13 | 0.06 | tests/test_kepler.py — ATOM-STEP-1: Kepler Engine Tests Tests core/kepler.py: or, At epoch JD, M is mean_longitude - long_perihelion (mod 360)., Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., … (+4) |
| 663 | [Community 1043](#c-1043) | 12 | 0.51 | integration-test.sh script, err(), header(), info(), main(), … (+3) |
| 664 | [Community 1027](#c-1027) | 12 | 0.41 | create_ai_scheduler(), create_slurm_ray_bridge(), final_summary(), health_check(), info(), … (+3) |
| 665 | [Community 1042](#c-1042) | 12 | 0.41 | day7_integration.sh script, create_ai_scheduler(), create_slurm_ray_bridge(), final_summary(), health_check(), … (+3) |
| 666 | [Community 1016](#c-1016) | 12 | 0.32 | Index, build_index(), cmd_build(), cmd_search(), cmd_stats(), … (+3) |
| 667 | [Community 1032](#c-1032) | 12 | 0.32 | Index, build_index(), cmd_build(), cmd_search(), cmd_stats(), … (+3) |
| 668 | [Community 1044](#c-1044) | 12 | 0.32 | Index, build_index(), cmd_build(), cmd_search(), cmd_stats(), … (+3) |
| 669 | [Community 1048](#c-1048) | 12 | 0.32 | Index, build_index(), cmd_build(), cmd_search(), cmd_stats(), … (+3) |
| 670 | [Community 1023](#c-1023) | 12 | 0.29 | reboot_node(), restart_ceph(), restart_ceph_manager(), restart_ceph_mon(), restart_ceph_osd(), … (+3) |
| 671 | [Community 1041](#c-1041) | 12 | 0.29 | reboot_node(), restart_ceph(), restart_ceph_manager(), restart_ceph_mon(), restart_ceph_osd(), … (+3) |
| 672 | [Community 1017](#c-1017) | 12 | 0.27 | check_protected_files_in_diff(), is_protected_file(), log_audit(), main(), Проверяет, … (+7) |
| 673 | [Community 1033](#c-1033) | 12 | 0.27 | check_protected_files_in_diff(), is_protected_file(), log_audit(), main(), Проверяет, … (+7) |
| 674 | [Community 1049](#c-1049) | 12 | 0.27 | check_protected_files_in_diff(), is_protected_file(), log_audit(), main(), Проверяет, … (+7) |
| 675 | [Community 1054](#c-1054) | 12 | 0.27 | check_protected_files_in_diff(), is_protected_file(), log_audit(), main(), Проверяет, … (+7) |
| 676 | [Community 1015](#c-1015) | 12 | 0.24 | _create_pg_engine(), get_database_url(), get_db_stats(), get_engine(), get_session_factory(), … (+3) |
| 677 | [Community 1031](#c-1031) | 12 | 0.24 | _create_pg_engine(), get_database_url(), get_db_stats(), get_engine(), get_session_factory(), … (+3) |
| 678 | [Community 1038](#c-1038) | 12 | 0.24 | _create_pg_engine(), get_database_url(), get_db_stats(), get_engine(), get_session_factory(), … (+3) |
| 679 | [Community 1047](#c-1047) | 12 | 0.24 | _create_pg_engine(), get_database_url(), get_db_stats(), get_engine(), get_session_factory(), … (+3) |
| 680 | [Community 948](#c-948) | 12 | 0.22 | compute_karl_health(), format_diagnostics_rich(), get_recommendations(), get_system_status(), KARLHealthMetrics, … (+3) |
| 681 | [Community 951](#c-951) | 12 | 0.22 | compute_karl_health(), format_diagnostics_rich(), get_recommendations(), get_system_status(), KARLHealthMetrics, … (+3) |
| 682 | [Community 972](#c-972) | 12 | 0.22 | compute_karl_health(), format_diagnostics_rich(), get_recommendations(), get_system_status(), KARLHealthMetrics, … (+3) |
| 683 | [Community 996](#c-996) | 12 | 0.22 | compute_karl_health(), format_diagnostics_rich(), get_recommendations(), get_system_status(), KARLHealthMetrics, … (+3) |
| 684 | [Community 1024](#c-1024) | 12 | 0.22 | DataFrame, label_failure(), label_from_job_outcome(), label_load_exceeded(), rolling_label(), … (+4) |
| 685 | [Community 964](#c-964) | 12 | 0.21 | predict(), _cache_get(), _cache_put(), _cached_predict(), _get_cache_ttl(), … (+3) |
| 686 | [Community 666](#c-666) | 12 | 0.19 | print_topology_viz(), Generate ASCII art topology, Generates Mermaid and DOT visualizations from Topology, Export topology as JSON, Save all visualizations to files, … (+3) |
| 687 | [Community 717](#c-717) | 12 | 0.19 | print_topology_viz(), Generate ASCII art topology, Generates Mermaid and DOT visualizations from Topology, Export topology as JSON, Save all visualizations to files, … (+3) |
| 688 | [Community 1028](#c-1028) | 12 | 0.17 | DataFrame, api_server(), _generate_synthetic_dataset(), Integration test — ML Pipeline (Train → Predict → Metrics)  Tests the full stack, Temporary directory for model artifacts (per test module)., … (+3) |
| 689 | [Community 347](#c-347) | 12 | 0.16 | Any, Backtester, EvaluationResult, BacktestEngineAdapter, meta_rl/backtest_adapter.py — ATOM-META-RL-003: BacktestEngine Adapter, … (+3) |
| 690 | [Community 361](#c-361) | 12 | 0.16 | Any, Backtester, EvaluationResult, BacktestEngineAdapter, meta_rl/backtest_adapter.py — ATOM-META-RL-003: BacktestEngine Adapter, … (+3) |
| 691 | [Community 791](#c-791) | 12 | 0.16 | InjectionResult, JobResult, NodeState, SyntheticScheduler, Job, … (+3) |
| 692 | [Community 812](#c-812) | 12 | 0.16 | InjectionResult, JobResult, NodeState, SyntheticScheduler, Job, … (+3) |
| 693 | [Community 545](#c-545) | 12 | 0.15 | MarketAdapter, OHLCV, data/market_adapter.py — ATOM-STEP-6: Market Data Adapter with live sources, cac, Get the latest closing price for a symbol., … (+4) |
| 694 | [Community 565](#c-565) | 12 | 0.15 | MarketAdapter, OHLCV, data/market_adapter.py — ATOM-STEP-6: Market Data Adapter with live sources, cac, Get the latest closing price for a symbol., … (+4) |
| 695 | [Community 575](#c-575) | 12 | 0.15 | MarketAdapter, OHLCV, data/market_adapter.py — ATOM-STEP-6: Market Data Adapter with live sources, cac, Get the latest closing price for a symbol., … (+4) |
| 696 | [Community 586](#c-586) | 12 | 0.15 | MarketAdapter, OHLCV, data/market_adapter.py — ATOM-STEP-6: Market Data Adapter with live sources, cac, Get the latest closing price for a symbol., … (+4) |
| 697 | [Community 1053](#c-1053) | 12 | 0.15 | Background, Commands, Dependencies, Environment, Progress, … (+3) |
| 698 | [Community 365](#c-365) | 12 | 0.14 | DivergenceRootCause, DivergenceRootCauseGraph, explainable_divergence_engine.py ================================ v7.2 — Explain, Main entry point: produce causal root-cause graph from divergence data., One node in the causal root-cause graph., … (+3) |
| 699 | [Community 537](#c-537) | 12 | 0.14 | AgentResponse, FundamentalAgent, Fundamental Agent — financial statement analysis, valuation metrics., Public entry point. Wraps analyze() with the latency histogram         and defen, … (+4) |
| 700 | [Community 538](#c-538) | 12 | 0.14 | AgentResponse, QuantAgent, Quant Agent — backtesting, strategy optimization, ML predictions., … (+5) |
| 701 | [Community 541](#c-541) | 12 | 0.14 | AgentResponse, FundamentalAgent, Fundamental Agent — financial statement analysis, valuation metrics., Public entry point. Wraps analyze() with the latency histogram         and defen, … (+4) |
| 702 | [Community 542](#c-542) | 12 | 0.14 | AgentResponse, QuantAgent, Quant Agent — backtesting, strategy optimization, ML predictions., … (+5) |
| 703 | [Community 561](#c-561) | 12 | 0.14 | AgentResponse, FundamentalAgent, Fundamental Agent — financial statement analysis, valuation metrics., Public entry point. Wraps analyze() with the latency histogram         and defen, … (+4) |
| 704 | [Community 562](#c-562) | 12 | 0.14 | AgentResponse, QuantAgent, Quant Agent — backtesting, strategy optimization, ML predictions., … (+5) |
| 705 | [Community 597](#c-597) | 12 | 0.14 | AgentResponse, ElliotAgent, Elliot Agent — Elliott Wave analysis., Fetch OHLCV data from OKX asynchronously., Simplified wave counting., … (+3) |
| 706 | [Community 598](#c-598) | 12 | 0.14 | AgentResponse, Risk Agent — position sizing and risk management., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Calculate Average True Range., … (+4) |
| 707 | [Community 604](#c-604) | 12 | 0.14 | AgentResponse, ElliotAgent, Elliot Agent — Elliott Wave analysis., Fetch OHLCV data from OKX asynchronously., Simplified wave counting., … (+3) |
| 708 | [Community 605](#c-605) | 12 | 0.14 | AgentResponse, Risk Agent — position sizing and risk management., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Calculate Average True Range., … (+4) |
| 709 | [Community 613](#c-613) | 12 | 0.14 | Any, CrossLayerReport, _inv_result(), InvariantResult, cross_layer_invariant_engine.py ============================== Formal invariant, … (+3) |
| 710 | [Community 618](#c-618) | 12 | 0.14 | AgentResponse, ElliotAgent, Elliot Agent — Elliott Wave analysis., Fetch OHLCV data from OKX asynchronously., Simplified wave counting., … (+3) |
| 711 | [Community 619](#c-619) | 12 | 0.14 | AgentResponse, Risk Agent — position sizing and risk management., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Calculate Average True Range., … (+4) |
| 712 | [Community 643](#c-643) | 12 | 0.14 | AgentResponse, Risk Agent — position sizing and risk management., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Calculate Average True Range., … (+4) |
| 713 | [Community 970](#c-970) | 12 | 0.14 | Any, Any, is_otel_setup(), OTEL Exporter v7.0 — OTLP trace (and optionally metrics) export.  Sets up:   - T, Return True if setup_otel_exporter() has been called successfully., … (+3) |
| 714 | [Community 459](#c-459) | 12 | 0.13 | MetaRLEngine, Strategy, submit_acos_job(), DISTRIBUTED EVALUATION:         Each strategy → ACOS job submitted to Slurm/Ray, Tournament selection + elitism., … (+3) |
| 715 | [Community 482](#c-482) | 12 | 0.13 | MetaRLEngine, Strategy, submit_acos_job(), DISTRIBUTED EVALUATION:         Each strategy → ACOS job submitted to Slurm/Ray, Tournament selection + elitism., … (+3) |
| 716 | [Community 498](#c-498) | 12 | 0.13 | GuardViolation, HARD ASSERT: Verify mutation is allowed.                  Called by:         - E, Verify Gateway context is active.                  Called at the START of every, Verify function is an allowed entry point., Return all logged violations., … (+3) |
| 717 | [Community 518](#c-518) | 12 | 0.13 | Any, Tests for unified_state_metric_tensor.py, TestDictL2Delta, TestHammingHex, _dict_l2_delta(), … (+3) |
| 718 | [Community 539](#c-539) | 12 | 0.13 | AttractorClass, ClosureProof, GSCT, gsct.py — v11.4 Global System Closure Theorem.  GSCT is the final theoretical la, Main entry point.          Args:             rcf_history: [{t, … (+5) |
| 719 | [Community 572](#c-572) | 12 | 0.13 | BackgroundTasks, build_docker_command(), execute_job(), execute_job_sync(), JobRequest, … (+3) |
| 720 | [Community 334](#c-334) | 12 | 0.12 | Any, CausalFingerprint, IncrementalCausalVerifier, incremental_causal_verifier.py ============================== Incrementally veri, O(1) causal equivalence check.         Returns (True, … (+5) |
| 721 | [Community 454](#c-454) | 12 | 0.12 | CCXTLiveProvider, get_live_provider(), MarketSnapshot, meta_rl/live_provider.py — ATOM-META-RL-012: Production CCXT Live Provider  Secu, Enforce rate limiting between requests., … (+3) |
| 722 | [Community 473](#c-473) | 12 | 0.12 | CCXTLiveProvider, get_live_provider(), MarketSnapshot, meta_rl/live_provider.py — ATOM-META-RL-012: Production CCXT Live Provider  Secu, Enforce rate limiting between requests., … (+3) |
| 723 | [Community 485](#c-485) | 12 | 0.12 | CCXTLiveProvider, get_live_provider(), MarketSnapshot, meta_rl/live_provider.py — ATOM-META-RL-012: Production CCXT Live Provider  Secu, Enforce rate limiting between requests., … (+3) |
| 724 | [Community 493](#c-493) | 12 | 0.12 | CCXTLiveProvider, get_live_provider(), MarketSnapshot, meta_rl/live_provider.py — ATOM-META-RL-012: Production CCXT Live Provider  Secu, Enforce rate limiting between requests., … (+3) |
| 725 | [Community 595](#c-595) | 12 | 0.12 | Actuator Layer — v7.4 Closed-loop causal control system for swarm dynamics.  Mod, ActuatorCommandCopy, OscillationMode, Stability Feedback Controller — v7.4 Prevents oscillation collapse: ensures the, Reset the controller state (e.g., … (+4) |
| 726 | [Community 364](#c-364) | 12 | 0.11 | APIKey, AuthEngine, AuthError, KeyStatus, KeyType, … (+3) |
| 727 | [Community 409](#c-409) | 12 | 0.11 | Any, Any, AtomMessage, Stateful connection to a single remote AtomNode.     Thread-safe: multiple threa, RPCClient, … (+3) |
| 728 | [Community 437](#c-437) | 12 | 0.11 | Sliding window for a single metric on a single node., Get all values within window ending at cutoff., Apply aggregation to current buffer (all data in window)., Central window management: stores SlidingWindows per (node, metric), … (+5) |
| 729 | [Community 650](#c-650) | 12 | 0.11 | MarketImpactModel, MarketImpactResult, OrderBookLevel, OrderBookSnapshot, trading/execution/order_book.py — ATOM-STEP-10: Order Book & Market Impact Model, … (+3) |
| 730 | [Community 419](#c-419) | 12 | 0.08 | NodeRPC, NodeRPCServicer, NodeRPCStub, ── Service Definition ────────────────────────────────────────────────────, ── Service Definition ────────────────────────────────────────────────────, … (+3) |
| 731 | [Community 423](#c-423) | 12 | 0.08 | client(), Unit tests for ml_engine/inference/api.py  Covers:     - GET  /health   — livene, Integration tests that require a real model on disk., Smoke test: /predict with valid data returns a float risk_score., Server should accept ?explain=true without crashing., … (+3) |
| 732 | [Community 1060](#c-1060) | 11 | 0.44 | enode(), make_plan(), make_trace(), pnode(), test_alignment.py — v10.0 Alignment Layer integration tests., … (+3) |
| 733 | [Community 1109](#c-1109) | 11 | 0.42 | day5_ray.sh script, create_ray_scripts(), info(), install_ray(), main(), … (+3) |
| 734 | [Community 1065](#c-1065) | 11 | 0.24 | compute_agent_rewards(), compute_raw_reward(), compute_reward_pipeline(), compute_smoothed_reward(), core/reward/reward_engine.py — ATOM-REWARD-001: Combined Reward Pipeline  Pipeli, … (+3) |
| 735 | [Community 1067](#c-1067) | 11 | 0.24 | apply_raw_sql_schema(), get_db_status(), init_db_if_needed(), init_schema_if_needed(), _init_sqlite_fallback(), … (+3) |
| 736 | [Community 1083](#c-1083) | 11 | 0.24 | compute_agent_rewards(), compute_raw_reward(), compute_reward_pipeline(), compute_smoothed_reward(), core/reward/reward_engine.py — ATOM-REWARD-001: Combined Reward Pipeline  Pipeli, … (+3) |
| 737 | [Community 1085](#c-1085) | 11 | 0.24 | apply_raw_sql_schema(), get_db_status(), init_db_if_needed(), init_schema_if_needed(), _init_sqlite_fallback(), … (+3) |
| 738 | [Community 1095](#c-1095) | 11 | 0.24 | compute_agent_rewards(), compute_raw_reward(), compute_reward_pipeline(), compute_smoothed_reward(), core/reward/reward_engine.py — ATOM-REWARD-001: Combined Reward Pipeline  Pipeli, … (+3) |
| 739 | [Community 1100](#c-1100) | 11 | 0.24 | apply_raw_sql_schema(), get_db_status(), init_db_if_needed(), init_schema_if_needed(), _init_sqlite_fallback(), … (+3) |
| 740 | [Community 1116](#c-1116) | 11 | 0.24 | compute_agent_rewards(), compute_raw_reward(), compute_reward_pipeline(), compute_smoothed_reward(), core/reward/reward_engine.py — ATOM-REWARD-001: Combined Reward Pipeline  Pipeli, … (+3) |
| 741 | [Community 1118](#c-1118) | 11 | 0.24 | apply_raw_sql_schema(), get_db_status(), init_db_if_needed(), init_schema_if_needed(), _init_sqlite_fallback(), … (+3) |
| 742 | [Community 888](#c-888) | 11 | 0.21 | _make_run(), backtest/test_metrics_agent.py — TDD tests for metrics_agent.py fixes  Tests:, test_list_respects_limit(), test_list_respects_symbol_filter(), test_list_returns_backtest_run_objects(), … (+3) |
| 743 | [Community 907](#c-907) | 11 | 0.21 | _make_run(), backtest/test_metrics_agent.py — TDD tests for metrics_agent.py fixes  Tests:, test_list_respects_limit(), test_list_respects_symbol_filter(), test_list_returns_backtest_run_objects(), … (+3) |
| 744 | [Community 918](#c-918) | 11 | 0.21 | _make_run(), backtest/test_metrics_agent.py — TDD tests for metrics_agent.py fixes  Tests:, test_list_respects_limit(), test_list_respects_symbol_filter(), test_list_returns_backtest_run_objects(), … (+3) |
| 745 | [Community 935](#c-935) | 11 | 0.21 | _make_run(), backtest/test_metrics_agent.py — TDD tests for metrics_agent.py fixes  Tests:, test_list_respects_limit(), test_list_respects_symbol_filter(), test_list_returns_backtest_run_objects(), … (+3) |
| 746 | [Community 703](#c-703) | 11 | 0.18 | ClusterSnapshot, UtilityFunction, Epsilon-greedy exploration bonus for trying new configurations., Compute total utility U(S)., Compute marginal utility delta for a single action., … (+4) |
| 747 | [Community 777](#c-777) | 11 | 0.18 | get_residual_model(), hybrid_propagate(), HybridResult, print_hybrid_comparison(), core/kepler_hybrid.py — ATOM-STEP-4: Kepler + ML Hybrid Model ==================, … (+4) |
| 748 | [Community 796](#c-796) | 11 | 0.18 | get_residual_model(), hybrid_propagate(), HybridResult, print_hybrid_comparison(), core/kepler_hybrid.py — ATOM-STEP-4: Kepler + ML Hybrid Model ==================, … (+4) |
| 749 | [Community 804](#c-804) | 11 | 0.18 | get_residual_model(), hybrid_propagate(), HybridResult, print_hybrid_comparison(), core/kepler_hybrid.py — ATOM-STEP-4: Kepler + ML Hybrid Model ==================, … (+4) |
| 750 | [Community 819](#c-819) | 11 | 0.18 | get_residual_model(), hybrid_propagate(), HybridResult, print_hybrid_comparison(), core/kepler_hybrid.py — ATOM-STEP-4: Kepler + ML Hybrid Model ==================, … (+4) |
| 751 | [Community 825](#c-825) | 11 | 0.18 | GovernorDecision, GovernorSignal, stability_governor.py — hard gate before mutation  v8.2a foundation #2 Blocks mu, Return only signals that pass (ALLOW)., Human-readable explanation of the decision., … (+3) |
| 752 | [Community 1158](#c-1158) | 11 | 0.18 | 10. LangGraph Belief-Guided Architecture, Changes from Old Graph, Conditional Routing (unchanged), Core Idea, File: `langgraph_schema.py` (rewritten), … (+3) |
| 753 | [Community 832](#c-832) | 11 | 0.17 | _embed(), RAGRetriever, AstroFin Sentinel v5 — RAG Retriever Unified knowledge retrieval interface for a, Return per-domain index statistics., Agent tool: semantic search over the knowledge base.      Agents call this when:, … (+5) |
| 754 | [Community 838](#c-838) | 11 | 0.17 | ACOSSubmissionGateway, main(), Single entry point for ALL AstroFin execution.     Flow: API request → Trace → L, Submit AstroFin job through ACOS governance pipeline.         Returns: trace_dic, AstroFinTrace, … (+3) |
| 755 | [Community 849](#c-849) | 11 | 0.17 | _embed(), RAGRetriever, AstroFin Sentinel v5 — RAG Retriever Unified knowledge retrieval interface for a, Return per-domain index statistics., Agent tool: semantic search over the knowledge base.      Agents call this when:, … (+5) |
| 756 | [Community 864](#c-864) | 11 | 0.17 | _embed(), RAGRetriever, AstroFin Sentinel v5 — RAG Retriever Unified knowledge retrieval interface for a, Return per-domain index statistics., Agent tool: semantic search over the knowledge base.      Agents call this when:, … (+5) |
| 757 | [Community 1061](#c-1061) | 11 | 0.17 | 1. Дедупликация агентов, 2. Фикс dual-mode теста, 3. Результаты тестов, 4. Канонический импорт, 5. Следующие ATОМы, … (+3) |
| 758 | [Community 1069](#c-1069) | 11 | 0.17 | tests/test_dual_mode.py - ATOM-R-027: Dual-Mode Backward Compatibility Tests, test_backward_compatibility_signatures(), test_dual_mode_detection(), test_legacy_mode_produces_same_result(), test_masfactory_fallback_on_error(), … (+3) |
| 759 | [Community 1072](#c-1072) | 11 | 0.17 | ml_engine — ACOS ML Prediction Layer (v5)  Dataset   → Models   → Training   → I, Evaluator, FailureXGBoost, FeedbackCollector, LabelEngine, … (+3) |
| 760 | [Community 1074](#c-1074) | 11 | 0.17 | Added, Architecture, Changelog — atom-federation-os, Guarantees, Invariants, … (+3) |
| 761 | [Community 1078](#c-1078) | 11 | 0.17 | Architecture, ATOMFederationOS — SBS v1, Installation, Quick Usage, Running Tests, … (+3) |
| 762 | [Community 1080](#c-1080) | 11 | 0.17 | Быстрый старт — одна команда, Ожидаемые результаты, Предварительные требования, Создание тестового сценария (если список пуст), Установка и проверка atom-federation-os (HARDENING v2), … (+3) |
| 763 | [Community 1087](#c-1087) | 11 | 0.17 | tests/test_dual_mode.py - ATOM-R-027: Dual-Mode Backward Compatibility Tests, Test that function signatures haven't changed., Test that legacy mode works identically to before changes., Test that MASFactory failure triggers graceful fallback., Test that CLI correctly detects --masfactory flag., … (+3) |
| 764 | [Community 1102](#c-1102) | 11 | 0.17 | 10. Version History, 1. Architectural Invariant (Formal), 2. Execution Algebra (Enforced Chain), 3. Dominator Tree, 4. MutationExecutor — Final Capability Interface, … (+3) |
| 765 | [Community 1103](#c-1103) | 11 | 0.17 | 10. Where to read next, 1. Mission, 2. Pipeline at a glance, 3. Reward function, 4. Evolution cycle, … (+3) |
| 766 | [Community 1108](#c-1108) | 11 | 0.17 | 🚀 Adding New Nodes, Contributing to home-cluster-iac, 🏗️ Directory Structure, 🆘 DR / Restore, 🛰️ GitOps (ArgoCD), … (+3) |
| 767 | [Community 1113](#c-1113) | 11 | 0.17 | AI Stack, Containers, Desktop, Dev Tools, pop-os-setup: Программы и компоненты установки, … (+3) |
| 768 | [Community 1121](#c-1121) | 11 | 0.17 | tests/test_dual_mode.py - ATOM-R-027: Dual-Mode Backward Compatibility Tests, Test that function signatures haven't changed., Test that legacy mode works identically to before changes., Test that MASFactory failure triggers graceful fallback., Test that CLI correctly detects --masfactory flag., … (+3) |
| 769 | [Community 1124](#c-1124) | 11 | 0.17 | Architecture Specification v1.0 (2026-04-17), Closed-Loop System Model, Comparison with Existing Systems, Core Innovation: Decision Gate, Execution Commands, … (+3) |
| 770 | [Community 1125](#c-1125) | 11 | 0.17 | tests/test_dual_mode.py - ATOM-R-027: Dual-Mode Backward Compatibility Tests, Test that function signatures haven't changed., Test that legacy mode works identically to before changes., Test that MASFactory failure triggers graceful fallback., Test that CLI correctly detects --masfactory flag., … (+3) |
| 771 | [Community 599](#c-599) | 11 | 0.16 | AgentResponse, Time Window Agent — entry timing and best trading windows., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Scan 4-hour windows for entry opportunity., … (+3) |
| 772 | [Community 606](#c-606) | 11 | 0.16 | AgentResponse, Time Window Agent — entry timing and best trading windows., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Scan 4-hour windows for entry opportunity., … (+3) |
| 773 | [Community 620](#c-620) | 11 | 0.16 | AgentResponse, Time Window Agent — entry timing and best trading windows., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Scan 4-hour windows for entry opportunity., … (+3) |
| 774 | [Community 676](#c-676) | 11 | 0.16 | PolicyOscillationScenario, PolicyState, run_all(), Simulate a policy decision with oscillating behavior., Compute key metrics for oscillation detection., … (+4) |
| 775 | [Community 702](#c-702) | 11 | 0.16 | PolicyOscillationScenario, PolicyState, run_all(), Simulate a policy decision with oscillating behavior., Compute key metrics for oscillation detection., … (+4) |
| 776 | [Community 731](#c-731) | 11 | 0.16 | AgentResponse, BradleyAgent, Bradley Agent — Bradley Model (S&P 500 seasonality/cyccles)., Fetch OHLCV data from OKX asynchronously., Calculate Bradley-like seasonality index.         Based on day-of-year performan, … (+3) |
| 777 | [Community 732](#c-732) | 11 | 0.16 | AgentResponse, Sentiment Agent — fear/greed and market sentiment analysis., Fetch funding rate from Bybit asynchronously., Analyze price momentum as sentiment proxy., SentimentAgent — анализ настроений рынка., … (+3) |
| 778 | [Community 734](#c-734) | 11 | 0.16 | AgentResponse, BradleyAgent, Bradley Agent — Bradley Model (S&P 500 seasonality/cyccles)., Fetch OHLCV data from OKX asynchronously., Calculate Bradley-like seasonality index.         Based on day-of-year performan, … (+3) |
| 779 | [Community 735](#c-735) | 11 | 0.16 | AgentResponse, Sentiment Agent — fear/greed and market sentiment analysis., Fetch funding rate from Bybit asynchronously., Analyze price momentum as sentiment proxy., SentimentAgent — анализ настроений рынка., … (+3) |
| 780 | [Community 743](#c-743) | 11 | 0.16 | AdmissionResult, DecisionContext, DecisionStatus, Environment snapshot at decision time., SafetyKernel, … (+4) |
| 781 | [Community 749](#c-749) | 11 | 0.16 | AgentResponse, BradleyAgent, Bradley Agent — Bradley Model (S&P 500 seasonality/cyccles)., Fetch OHLCV data from OKX asynchronously., Calculate Bradley-like seasonality index.         Based on day-of-year performan, … (+3) |
| 782 | [Community 750](#c-750) | 11 | 0.16 | AgentResponse, Sentiment Agent — fear/greed and market sentiment analysis., Fetch funding rate from Bybit asynchronously., Analyze price momentum as sentiment proxy., SentimentAgent — анализ настроений рынка., … (+3) |
| 783 | [Community 764](#c-764) | 11 | 0.16 | AdmissionResult, DecisionContext, DecisionStatus, Environment snapshot at decision time., SafetyKernel, … (+4) |
| 784 | [Community 869](#c-869) | 11 | 0.16 | BasketMetrics, EvaluationResult, Типы данных для meta_rl., Reconstruct an EvaluationResult from a dict produced by ``to_dict``.          ``, Safely convert a numeric value to float, … (+4) |
| 785 | [Community 547](#c-547) | 11 | 0.15 | DigestEntry, DigestLog, DigestStatus, main(), Update status for an entry., … (+3) |
| 786 | [Community 567](#c-567) | 11 | 0.15 | DigestEntry, DigestLog, DigestStatus, main(), Update status for an entry., … (+3) |
| 787 | [Community 580](#c-580) | 11 | 0.15 | DigestEntry, DigestLog, DigestStatus, main(), Update status for an entry., … (+3) |
| 788 | [Community 588](#c-588) | 11 | 0.15 | DigestEntry, DigestLog, DigestStatus, main(), Update status for an entry., … (+3) |
| 789 | [Community 612](#c-612) | 11 | 0.15 | ConstraintEngine, ConstraintViolation, PlacementContext, ViolationType, Validate all placements, … (+4) |
| 790 | [Community 628](#c-628) | 11 | 0.15 | Validate all placements, return {job_id: violations}., Return list of nodes that can satisfy this job (hard constraints only)., Check if node has lost connectivity to mesh., True if ALL placements satisfy hard constraints., … (+4) |
| 791 | [Community 655](#c-655) | 11 | 0.15 | AgentResponse, InsiderAgent, Insider Agent — insider trading and 13F filings analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch insider trading data.         Note: Real data requires paid API (OpenInsid, … (+3) |
| 792 | [Community 657](#c-657) | 11 | 0.15 | AgentResponse, MLPredictorAgent, ML Predictor Agent — ML-based price prediction and volatility forecasting., Fetch price data for ML model., Simple ML-like prediction using momentum and moving average crossover.         I, … (+3) |
| 793 | [Community 658](#c-658) | 11 | 0.15 | AgentResponse, OptionsFlowAgent, Options Flow Agent — options flow analysis, gamma exposure, unusual activity., … (+5) |
| 794 | [Community 659](#c-659) | 11 | 0.15 | AgentResponse, InsiderAgent, Insider Agent — insider trading and 13F filings analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch insider trading data.         Note: Real data requires paid API (OpenInsid, … (+3) |
| 795 | [Community 661](#c-661) | 11 | 0.15 | AgentResponse, MLPredictorAgent, ML Predictor Agent — ML-based price prediction and volatility forecasting., Fetch price data for ML model., Simple ML-like prediction using momentum and moving average crossover.         I, … (+3) |
| 796 | [Community 662](#c-662) | 11 | 0.15 | AgentResponse, OptionsFlowAgent, Options Flow Agent — options flow analysis, gamma exposure, unusual activity., … (+5) |
| 797 | [Community 670](#c-670) | 11 | 0.15 | trading/execution/vwap.py — ATOM-STEP-10: VWAP Execution Strategy, Get volume weight for a given slice number., Volume-Weighted Average Price execution strategy.      Executes orders proportio, Simulate market volume for a given slice (in base currency units).          Uses, Execute a VWAP order.          Args:             symbol: Trading pair, … (+3) |
| 798 | [Community 675](#c-675) | 11 | 0.15 | NodeEmbeddingBuilder, ndarray, NodeProfile, Simple K-means clustering of nodes by embedding similarity.         Returns {clu, Builds fixed-size embedding vectors for cluster nodes.     Combines: hardware pr, … (+3) |
| 799 | [Community 681](#c-681) | 11 | 0.15 | AgentResponse, InsiderAgent, Insider Agent — insider trading and 13F filings analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch insider trading data.         Note: Real data requires paid API (OpenInsid, … (+3) |
| 800 | [Community 683](#c-683) | 11 | 0.15 | AgentResponse, MLPredictorAgent, ML Predictor Agent — ML-based price prediction and volatility forecasting., Fetch price data for ML model., Simple ML-like prediction using momentum and moving average crossover.         I, … (+3) |
| 801 | [Community 684](#c-684) | 11 | 0.15 | AgentResponse, OptionsFlowAgent, Options Flow Agent — options flow analysis, gamma exposure, unusual activity., … (+5) |
| 802 | [Community 691](#c-691) | 11 | 0.15 | trading/execution/vwap.py — ATOM-STEP-10: VWAP Execution Strategy, Get volume weight for a given slice number., Volume-Weighted Average Price execution strategy.      Executes orders proportio, Simulate market volume for a given slice (in base currency units).          Uses, Execute a VWAP order.          Args:             symbol: Trading pair, … (+3) |
| 803 | [Community 709](#c-709) | 11 | 0.15 | AgentResponse, InsiderAgent, Insider Agent — insider trading and 13F filings analysis., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch insider trading data.         Note: Real data requires paid API (OpenInsid, … (+3) |
| 804 | [Community 721](#c-721) | 11 | 0.15 | trading/execution/vwap.py — ATOM-STEP-10: VWAP Execution Strategy, Get volume weight for a given slice number., Volume-Weighted Average Price execution strategy.      Executes orders proportio, Simulate market volume for a given slice (in base currency units).          Uses, Execute a VWAP order.          Args:             symbol: Trading pair, … (+3) |
| 805 | [Community 780](#c-780) | 11 | 0.15 | ab_compare(), auth_middleware(), check_postgres(), check_redis(), health_check(), … (+3) |
| 806 | [Community 799](#c-799) | 11 | 0.15 | ab_compare(), auth_middleware(), check_postgres(), check_redis(), health_check(), … (+3) |
| 807 | [Community 808](#c-808) | 11 | 0.15 | BFTQC, BFTThreshold, QCValidationResult, bft_quorum_certificate.py — atom-federation-os v9.0+P7 BFT Quorum Certificate., validate_bft_qc(), … (+3) |
| 808 | [Community 810](#c-810) | 11 | 0.15 | ab_compare(), auth_middleware(), check_postgres(), check_redis(), health_check(), … (+3) |
| 809 | [Community 822](#c-822) | 11 | 0.15 | ab_compare(), auth_middleware(), check_postgres(), check_redis(), health_check(), … (+3) |
| 810 | [Community 1018](#c-1018) | 11 | 0.15 | tests/architecture/test_architecture_linter.py =================================, When hard rules fail, the script returns non-zero., The template is hand-written to be conformant:, If a module imports ephemeris but no method has @require_ephemeris, … (+5) |
| 811 | [Community 1019](#c-1019) | 11 | 0.15 | tests/test_switch_nodes.py - ATOM-R-028: SwitchNode Tests import pytest All 4 ma, Test 3: OOS fail > 0.4 → tighten policy., Test 4: Correct rollback when SwitchNode fails., Test 1: uncertainty > 0.6 → adds GroundingLoop., Additional: ConditionEvaluator edge cases., … (+3) |
| 812 | [Community 1021](#c-1021) | 11 | 0.15 | tests/test_switch_nodes.py - ATOM-R-028: SwitchNode Tests All 4 mandatory tests, test_bias_switch_adds_critic(), test_condition_evaluator(), test_oos_fail_tightens_policy(), test_rollback_on_error(), … (+3) |
| 813 | [Community 1034](#c-1034) | 11 | 0.15 | tests/architecture/test_architecture_linter.py =================================, When hard rules fail, the script returns non-zero., The template is hand-written to be conformant:, If a module imports ephemeris but no method has @require_ephemeris, … (+5) |
| 814 | [Community 1035](#c-1035) | 11 | 0.15 | tests/test_switch_nodes.py - ATOM-R-028: SwitchNode Tests import pytest All 4 ma, Test 3: OOS fail > 0.4 → tighten policy., Test 4: Correct rollback when SwitchNode fails., Test 1: uncertainty > 0.6 → adds GroundingLoop., Additional: ConditionEvaluator edge cases., … (+3) |
| 815 | [Community 1050](#c-1050) | 11 | 0.15 | tests/architecture/test_architecture_linter.py =================================, When hard rules fail, the script returns non-zero., The template is hand-written to be conformant:, If a module imports ephemeris but no method has @require_ephemeris, … (+5) |
| 816 | [Community 1051](#c-1051) | 11 | 0.15 | tests/test_switch_nodes.py - ATOM-R-028: SwitchNode Tests import pytest All 4 ma, Test 3: OOS fail > 0.4 → tighten policy., Test 4: Correct rollback when SwitchNode fails., Test 1: uncertainty > 0.6 → adds GroundingLoop., Additional: ConditionEvaluator edge cases., … (+3) |
| 817 | [Community 1055](#c-1055) | 11 | 0.15 | tests/architecture/test_architecture_linter.py =================================, When hard rules fail, the script returns non-zero., The template is hand-written to be conformant:, If a module imports ephemeris but no method has @require_ephemeris, … (+5) |
| 818 | [Community 1057](#c-1057) | 11 | 0.15 | tests/test_switch_nodes.py - ATOM-R-028: SwitchNode Tests.  All 4 mandatory test, test_bias_switch_adds_critic(), test_condition_evaluator(), test_oos_fail_tightens_policy(), test_rollback_on_error(), … (+3) |
| 819 | [Community 790](#c-790) | 11 | 0.14 | CorrectionCycleResult, EvolutionEngine, EvolutionRecord, GenerationSummary, Return True if stuck pattern detected — meta-learner should intervene., … (+3) |
| 820 | [Community 807](#c-807) | 11 | 0.14 | Return True if stuck pattern detected — meta-learner should intervene., Generate full evolution report., Single evolution event., Summary of one generation (correction cycle batch)., Tracks system evolution over time.     Detects convergence, … (+4) |
| 821 | [Community 956](#c-956) | 11 | 0.14 | ATOM-R-041: Idea → Outcome Tracking, CLI, KPI, Scoring Formula, Self-Questioning Integration, … (+3) |
| 822 | [Community 977](#c-977) | 11 | 0.14 | ATOM-R-041: Idea → Outcome Tracking, CLI, KPI, Scoring Formula, Self-Questioning Integration, … (+3) |
| 823 | [Community 992](#c-992) | 11 | 0.14 | ATOM-R-041: Idea → Outcome Tracking, CLI, KPI, Scoring Formula, Self-Questioning Integration, … (+3) |
| 824 | [Community 1001](#c-1001) | 11 | 0.14 | ATOM-R-041: Idea → Outcome Tracking, CLI, KPI, Scoring Formula, Self-Questioning Integration, … (+3) |
| 825 | [Community 677](#c-677) | 11 | 0.13 | AlignmentResult, DriftAlignment, DriftSignals, Compute model error rate (MAPE).         Returns 0-1, higher = more drift., … (+5) |
| 826 | [Community 698](#c-698) | 11 | 0.13 | Compute model error rate (MAPE).         Returns 0-1, higher = more drift., Compute divergence: simulated vs actual cluster behavior.         Returns 0-1, h, Compute correlation across three drift signals.         Drift_Alignment = mean(c, … (+6) |
| 827 | [Community 488](#c-488) | 11 | 0.12 | AuditLog, DecisionRecord, Конвертация в dict для сериализации, Вычисляет хеш записи для верификации, Восстановление из dict, … (+3) |
| 828 | [Community 535](#c-535) | 11 | 0.12 | Main decision: reject if P(overload in next M min) > threshold.         Returns, Feed a new GPU utilization reading., Bootstrap rolling windows from historical GPU metrics in state_store.     Real i, Online rolling mean + variance (Welford's algorithm)., Computes P(overload | next M minutes) using online statistics.          Overload, … (+3) |
| 829 | [Community 536](#c-536) | 11 | 0.12 | Feed a new GPU utilization reading., Bootstrap rolling windows from historical GPU metrics in state_store.     Real i, Online rolling mean + variance (Welford's algorithm)., Computes P(overload | next M minutes) using online statistics.      Overload is, Compute P(GPU_util > OVERLOAD_THRESHOLD | history).         Uses Gaussian CDF ap, … (+3) |
| 830 | [Community 549](#c-549) | 11 | 0.12 | Any, AgentRegistry, BasicAgentRunner, get_agent_runner(), get_registry(), … (+3) |
| 831 | [Community 568](#c-568) | 11 | 0.12 | Any, AgentRegistry, BasicAgentRunner, get_agent_runner(), get_registry(), … (+3) |
| 832 | [Community 581](#c-581) | 11 | 0.12 | Any, AgentRegistry, BasicAgentRunner, get_agent_runner(), get_registry(), … (+3) |
| 833 | [Community 589](#c-589) | 11 | 0.12 | Any, AgentRegistry, BasicAgentRunner, get_agent_runner(), get_registry(), … (+3) |
| 834 | [Community 594](#c-594) | 11 | 0.11 | MutationExecutionSpec, MutationPlan, MutationPlanner — generates concrete mutation plans from policy intent., Build a MutationExecutionSpec given current system state.          Planning stra, RETUNE → bias gain scheduler on highest-drift dimensions., … (+3) |
| 835 | [Community 615](#c-615) | 11 | 0.10 | TestSystemBoundarySpec, Unit tests for SystemBoundarySpec.validate()., System with 1 partition should pass when allow_split_brain=False., System with 2 partitions must fail when allow_split_brain=False., Quorum ratio below threshold must fail., … (+3) |
| 836 | [Community 648](#c-648) | 11 | 0.10 | TestFailureClassifier, FailureClassifier taxonomy tests., partition' type → NETWORK_PARTITION, HIGH severity., drop' type → MESSAGE_LOSS., … (+6) |
| 837 | [Community 649](#c-649) | 11 | 0.10 | TestSystemBoundarySpec, Unit tests for SystemBoundarySpec.validate()., System with 1 partition should pass when allow_split_brain=False., System with 2 partitions must fail when allow_split_brain=False., Quorum ratio below threshold must fail., … (+3) |
| 838 | [Community 298](#c-298) | 11 | 0.09 | Job, JobRetryManager, JobState, PersistentExecutionGuarantee, Handle job failure. Returns action: 'retry' | 'fail' | 'unknown_job', … (+4) |
| 839 | [Community 1155](#c-1155) | 10 | 0.47 | create_ray_scripts(), info(), install_ray(), main(), ok(), … (+3) |
| 840 | [Community 1142](#c-1142) | 10 | 0.45 | _compute_oap_adjustments(), _fetch_price(), main(), run_astro_flow(), run_electoral_flow(), … (+3) |
| 841 | [Community 1168](#c-1168) | 10 | 0.45 | _compute_oap_adjustments(), _fetch_price(), main(), run_astro_flow(), run_electoral_flow(), … (+3) |
| 842 | [Community 1190](#c-1190) | 10 | 0.45 | _compute_oap_adjustments(), _fetch_price(), main(), run_astro_flow(), run_electoral_flow(), … (+3) |
| 843 | [Community 1199](#c-1199) | 10 | 0.45 | _compute_oap_adjustments(), _fetch_price(), main(), run_astro_flow(), run_electoral_flow(), … (+3) |
| 844 | [Community 1104](#c-1104) | 10 | 0.38 | choose_key(), error(), generate_key(), info(), main(), … (+3) |
| 845 | [Community 1131](#c-1131) | 10 | 0.35 | compute_trajectory_metrics(), market_state_hash(), MarketState, amre/trajectory.py — Market state + Trajectory + TrajectoryStep, Trajectory, … (+3) |
| 846 | [Community 1135](#c-1135) | 10 | 0.35 | compute_trajectory_metrics(), market_state_hash(), MarketState, amre/trajectory.py — Market state + Trajectory + TrajectoryStep, Trajectory, … (+3) |
| 847 | [Community 1161](#c-1161) | 10 | 0.35 | compute_trajectory_metrics(), market_state_hash(), MarketState, amre/trajectory.py — Market state + Trajectory + TrajectoryStep, Trajectory, … (+3) |
| 848 | [Community 1130](#c-1130) | 10 | 0.31 | _discover_agents(), export_agent(), export_all(), generate_agent_yaml(), generate_prompt_md(), … (+3) |
| 849 | [Community 1133](#c-1133) | 10 | 0.31 | _discover_agents(), export_agent(), export_all(), generate_agent_yaml(), generate_prompt_md(), … (+3) |
| 850 | [Community 1159](#c-1159) | 10 | 0.31 | _discover_agents(), export_agent(), export_all(), generate_agent_yaml(), generate_prompt_md(), … (+3) |
| 851 | [Community 1192](#c-1192) | 10 | 0.31 | _discover_agents(), export_agent(), export_all(), generate_agent_yaml(), generate_prompt_md(), … (+3) |
| 852 | [Community 1063](#c-1063) | 10 | 0.30 | bar_to_market_state(), compute_metrics(), generate_synthetic_signals(), get_march_2026_bars(), main(), … (+3) |
| 853 | [Community 1081](#c-1081) | 10 | 0.30 | bar_to_market_state(), compute_metrics(), generate_synthetic_signals(), get_march_2026_bars(), main(), … (+3) |
| 854 | [Community 1090](#c-1090) | 10 | 0.30 | bar_to_market_state(), compute_metrics(), generate_synthetic_signals(), get_march_2026_bars(), main(), … (+3) |
| 855 | [Community 1114](#c-1114) | 10 | 0.30 | bar_to_market_state(), compute_metrics(), generate_synthetic_signals(), get_march_2026_bars(), main(), … (+3) |
| 856 | [Community 1178](#c-1178) | 10 | 0.27 | Label failure events: 1 if node went down within horizon, 0 otherwise., Label load overrun: 1 if queue_depth or GPU util exceeded threshold within horiz, Label from job outcome stored in job_events table., Apply rolling label: look ahead `horizon` rows and compute aggregate., … (+4) |
| 857 | [Community 1026](#c-1026) | 10 | 0.22 | build_metrics(), get_ceph_df(), get_ceph_osd_dump(), get_ceph_pg_dump(), get_ceph_status(), … (+3) |
| 858 | [Community 1037](#c-1037) | 10 | 0.22 | ceph status --format json, ceph osd dump --format json, ceph pg dump --format json, ceph df --format json, build_metrics(), … (+3) |
| 859 | [Community 1140](#c-1140) | 10 | 0.22 | Any, core/safe_json.py — ATOM-017 FIX: Safe JSON operations with error handling, Safely dump data to JSON file. Returns True on success., Safely load JSON file. Returns default on failure., Append a record to a JSONL file safely., … (+3) |
| 860 | [Community 1166](#c-1166) | 10 | 0.22 | Any, core/safe_json.py — ATOM-017 FIX: Safe JSON operations with error handling, Safely dump data to JSON file. Returns True on success., Safely load JSON file. Returns default on failure., Append a record to a JSONL file safely., … (+3) |
| 861 | [Community 1177](#c-1177) | 10 | 0.22 | Any, core/safe_json.py — ATOM-017 FIX: Safe JSON operations with error handling, Safely dump data to JSON file. Returns True on success., Safely load JSON file. Returns default on failure., Append a record to a JSONL file safely., … (+3) |
| 862 | [Community 1197](#c-1197) | 10 | 0.22 | Any, core/safe_json.py — ATOM-017 FIX: Safe JSON operations with error handling, Safely dump data to JSON file. Returns True on success., Safely load JSON file. Returns default on failure., Append a record to a JSONL file safely., … (+3) |
| 863 | [Community 834](#c-834) | 10 | 0.21 | ABTest, ABTestConfig, ABTestResult, cohens_d(), meta_rl/ab_testing.py -- ATOM-META-RL-012: A/B Testing Framework, … (+4) |
| 864 | [Community 851](#c-851) | 10 | 0.21 | ABTest, ABTestConfig, ABTestResult, cohens_d(), meta_rl/ab_testing.py -- ATOM-META-RL-012: A/B Testing Framework, … (+4) |
| 865 | [Community 866](#c-866) | 10 | 0.21 | ABTest, ABTestConfig, ABTestResult, cohens_d(), meta_rl/ab_testing.py -- ATOM-META-RL-012: A/B Testing Framework, … (+4) |
| 866 | [Community 876](#c-876) | 10 | 0.21 | ABTest, ABTestConfig, ABTestResult, cohens_d(), meta_rl/ab_testing.py -- ATOM-META-RL-012: A/B Testing Framework, … (+4) |
| 867 | [Community 1232](#c-1232) | 10 | 0.20 | 5.1 All Nondeterministic Sources — Complete Inventory, 5.2 Implementation — Fix Each Source, 5. NONDETERMINISM ELIMINATION MAP, N11: adaptive_router.py — random.choices / random.choice, N1-N3: execution_context.py — uuid.uuid4() for context_id, … (+3) |
| 868 | [Community 1132](#c-1132) | 10 | 0.18 | ArgoCD Installation Role for k3s Cluster, Artifacts, Compatibility: home-cluster-iac (k3s, Kubernetes 1.29+), Dependencies, … (+4) |
| 869 | [Community 1154](#c-1154) | 10 | 0.18 | ✅ 10 Core Invariants, 🔧 3 Required Patches (v2 spec), Architecture Summary, Known Limitations, Links, … (+3) |
| 870 | [Community 1157](#c-1157) | 10 | 0.18 | 1. Agent Inventory, 2. Stubs / Empty Placeholders, 4. Code Quality Observations, 5. Recommendations, 6. Migration System, … (+3) |
| 871 | [Community 1179](#c-1179) | 10 | 0.18 | Default Credentials, MikroTik hEX S — Initial Setup Guide, Prerequisites, Reset to Factory Defaults, Step 1 — Change Default Password, … (+3) |
| 872 | [Community 1187](#c-1187) | 10 | 0.18 | ✅ 10 Core Invariants, 🔧 3 Required Patches (v2 spec), Architecture Summary, Known Limitations, Links, … (+3) |
| 873 | [Community 1201](#c-1201) | 10 | 0.18 | 3-Way Reconciliation, Failure Modes, How It Works, Integration, Metrics Exposed, … (+3) |
| 874 | [Community 1202](#c-1202) | 10 | 0.18 | 🏗️ Architecture Overview, ⚠️ Breaking Changes, Contributing to roma-execution-bridge, 🛠️ Dev Environment, 🛰️ GitOps (ArgoCD), … (+3) |
| 875 | [Community 591](#c-591) | 10 | 0.17 | Connection, Cursor, datetime, CalibrationTracker, Records agent predictions and resolves them with realized outcomes., … (+3) |
| 876 | [Community 651](#c-651) | 10 | 0.17 | Run ACOS correction loop: scenario → RCA → fix → validate., Generate YAML-formatted correction report., Implements ACOS Correction Prompt logic., Run a single load test scenario., CauseType, … (+3) |
| 877 | [Community 652](#c-652) | 10 | 0.17 | Run ACOS correction loop: scenario → RCA → fix → validate., Generate YAML-formatted correction report., Implements ACOS Correction Prompt logic., Run a single load test scenario., CauseType, … (+3) |
| 878 | [Community 1126](#c-1126) | 10 | 0.17 | ✅ Byzantine node (double-sign) is slashed and excluded from quorums., ✅ BFT threshold calculations., ❌ FederatedExecutionGateway rejects when quorum not reached., ✅ SlashingEngine records all misbehavior types., ✅ Double-sign detection → node slashed., … (+3) |
| 879 | [Community 515](#c-515) | 10 | 0.16 | ClusterSnapshot, RollbackEngine, RollbackEvent, RollbackLevel, L1: revert to previous policy version., … (+3) |
| 880 | [Community 529](#c-529) | 10 | 0.16 | ClusterSnapshot, RollbackEngine, RollbackEvent, RollbackLevel, L1: revert to previous policy version., … (+3) |
| 881 | [Community 656](#c-656) | 10 | 0.16 | AgentResponse, MarketAnalystAgent, AstroFin Sentinel v5 — Market Analyst Agent Technical analysis: RSI, MACD, Bolli, … (+5) |
| 882 | [Community 660](#c-660) | 10 | 0.16 | AgentResponse, MarketAnalystAgent, AstroFin Sentinel v5 — Market Analyst Agent Technical analysis: RSI, MACD, Bolli, … (+5) |
| 883 | [Community 682](#c-682) | 10 | 0.16 | AgentResponse, MarketAnalystAgent, AstroFin Sentinel v5 — Market Analyst Agent Technical analysis: RSI, MACD, Bolli, … (+5) |
| 884 | [Community 710](#c-710) | 10 | 0.16 | AgentResponse, MarketAnalystAgent, AstroFin Sentinel v5 — Market Analyst Agent Technical analysis: RSI, MACD, Bolli, … (+5) |
| 885 | [Community 1003](#c-1003) | 10 | 0.16 | Any, CalibrationReport, get_calibration_tracker(), meta_rl/calibration.py -- ATOM-META-RL-014: CalibrationTracker.  Tracks agent pr, Return the process-wide CalibrationTracker singleton., … (+3) |
| 886 | [Community 745](#c-745) | 10 | 0.15 | Call, FunctionDef, Path, JoinedStr, extract_from_file(), … (+3) |
| 887 | [Community 818](#c-818) | 10 | 0.15 | _make_result(), End-to-end ``compute()`` golden values., All-zero inputs → sharpe=0.5, pnl=0.5, dd_pen=0, … (+8) |
| 888 | [Community 478](#c-478) | 10 | 0.14 | estimate_cost(), PricingEngine, PricingTier, CostPredictor, Predicts execution cost BEFORE running task., … (+3) |
| 889 | [Community 462](#c-462) | 10 | 0.13 | Any, ExplainableDivergenceEngine, Converts fingerprint + state diff → human-readable divergence explanation., Register a known causal dependency for root-cause analysis., Field-level diff across all domains., … (+4) |
| 890 | [Community 870](#c-870) | 10 | 0.12 | DeterministicScheduler, Deterministic fan-out for swarm: assign tasks to workers round-robin.         Sa, Get primary worker for tick. Deterministic: same tick → same worker., Deterministically order async execution steps.          Args:             steps:, Deterministic task scheduler for Swarm/Async engines.      ALL scheduling decisi, … (+4) |
| 891 | [Community 294](#c-294) | 10 | 0.11 | BillingLedger, # NOTE: record_revenue_share, get_monthly_revenue, get_pending_revenue_share, Append-only ledger — every billing event is recorded, … (+6) |
| 892 | [Community 352](#c-352) | 10 | 0.11 | SeverityLevel, StateVector — core unit of exchange between federation nodes., Immutable snapshot of a node's control state for gossip exchange., Stable hash of a theta dict., StateVector, … (+3) |
| 893 | [Community 378](#c-378) | 10 | 0.11 | Any, get_default_pg_buffer(), PostgresReplayBuffer, db/karl_replay.py — PostgresReplayBuffer (ATOM-019) Stores KARL trajectories in, Any, … (+3) |
| 894 | [Community 527](#c-527) | 10 | 0.11 | ExecutionResult, GPUWorkerDeployment, Deployment configuration for GPU workers, Production worker loop with:     - Job retry on failure     - GPU lock managemen, Select worker with most available VRAM, … (+3) |
| 895 | [Community 705](#c-705) | 10 | 0.11 | Test suite for MCPAdapter., Test adapter initialization., Test that search returns actual MCP servers., Test search with category filter., Test fallback server database., … (+3) |
| 896 | [Community 715](#c-715) | 10 | 0.11 | Test suite for MCPAdapter., Test adapter initialization., Test that search returns actual MCP servers., Test search with category filter., Test fallback server database., … (+3) |
| 897 | [Community 119](#c-119) | 10 | 0.10 | HealingAction, StabilitySnapshot, HealingResult, Synchronous healing for critical paths., HealingAction, … (+3) |
| 898 | [Community 332](#c-332) | 10 | 0.10 | EvolutionConfig, KARLState, MetaAgent, meta_rl/meta_agent.py -- ATOM-META-RL-005/009: Bidirectional KARL + Cross-sessio, Meta-RL agent with bidirectional KARL integration (ATOM-META-RL-005/009).      A, … (+3) |
| 899 | [Community 338](#c-338) | 10 | 0.10 | EvolutionConfig, KARLState, MetaAgent, meta_rl/meta_agent.py -- ATOM-META-RL-005/009: Bidirectional KARL + Cross-sessio, Meta-RL agent with bidirectional KARL integration (ATOM-META-RL-005/009).      A, … (+3) |
| 900 | [Community 342](#c-342) | 10 | 0.10 | EvolutionConfig, KARLState, MetaAgent, meta_rl/meta_agent.py -- ATOM-META-RL-005/009: Bidirectional KARL + Cross-sessio, Meta-RL agent with bidirectional KARL integration (ATOM-META-RL-005/009).      A, … (+3) |
| 901 | [Community 1259](#c-1259) | 9 | 0.44 | setup.sh script, create_issuers(), err(), install_cert_manager(), log(), … (+3) |
| 902 | [Community 1221](#c-1221) | 9 | 0.36 | cmd_daily_brief(), cmd_idea_tracker(), cmd_leaderboard(), cmd_reset(), cmd_scores(), … (+3) |
| 903 | [Community 1244](#c-1244) | 9 | 0.36 | cmd_daily_brief(), cmd_idea_tracker(), cmd_leaderboard(), cmd_reset(), cmd_scores(), … (+3) |
| 904 | [Community 1279](#c-1279) | 9 | 0.36 | cmd_daily_brief(), cmd_idea_tracker(), cmd_leaderboard(), cmd_reset(), cmd_scores(), … (+3) |
| 905 | [Community 1282](#c-1282) | 9 | 0.36 | generate_in_toto_layout(), generate_in_toto_link(), generate_supply_chain_attestation(), h(), Generate complete supply chain attestation bundle., … (+3) |
| 906 | [Community 1288](#c-1288) | 9 | 0.36 | cmd_daily_brief(), cmd_idea_tracker(), cmd_leaderboard(), cmd_reset(), cmd_scores(), … (+3) |
| 907 | [Community 959](#c-959) | 9 | 0.27 | _data_dir(), get_versioned_storage(), _load_index(), meta_rl/versions_storage.py -- ATOM-META-RL-012: Versioned Elite Storage + A/B T, _save_index(), … (+3) |
| 908 | [Community 980](#c-980) | 9 | 0.27 | _data_dir(), get_versioned_storage(), _load_index(), meta_rl/versions_storage.py -- ATOM-META-RL-012: Versioned Elite Storage + A/B T, _save_index(), … (+3) |
| 909 | [Community 995](#c-995) | 9 | 0.27 | _data_dir(), get_versioned_storage(), _load_index(), meta_rl/versions_storage.py -- ATOM-META-RL-012: Versioned Elite Storage + A/B T, _save_index(), … (+3) |
| 910 | [Community 1005](#c-1005) | 9 | 0.27 | _data_dir(), get_versioned_storage(), _load_index(), meta_rl/versions_storage.py -- ATOM-META-RL-012: Versioned Elite Storage + A/B T, _save_index(), … (+3) |
| 911 | [Community 1170](#c-1170) | 9 | 0.24 | mismatched_replay_events(), MockEvent, Tests for cross_layer_invariant_engine.py — I1–I4 invariant verification., Two-node cluster with SBS violations and drift., Causal parents as list (not set) are handled correctly., … (+3) |
| 912 | [Community 1225](#c-1225) | 9 | 0.22 | create_tunnel_incident(), get_tunnel_metrics(), patch_engine_pre_execute(), ACOS AmneziaWG Integration — Patches for ACOS Core  Provides: - Patch 1a: DAGVal, validate_network_requirements(), … (+3) |
| 913 | [Community 1319](#c-1319) | 9 | 0.22 | 12. Thompson Hyperparameters, CLI Usage, exploration_bonus — unseen agent prior boost, Files, K — agents to select per pool, … (+5) |
| 914 | [Community 789](#c-789) | 9 | 0.21 | ControlEvent, ctrl(), EventStore, health(), main(), … (+3) |
| 915 | [Community 830](#c-830) | 9 | 0.21 | AgentPool, get_thompson_sampler(), AstroFin Sentinel v5 — Thompson Sampling Agent Selector FIXED: thread-safe singl, Thompson sampling — GUARANTEED to never return empty list., Get or create Thompson sampler — THREAD-SAFE., … (+3) |
| 916 | [Community 847](#c-847) | 9 | 0.21 | AgentPool, get_thompson_sampler(), AstroFin Sentinel v5 — Thompson Sampling Agent Selector FIXED: thread-safe singl, Thompson sampling — GUARANTEED to never return empty list., Get or create Thompson sampler — THREAD-SAFE., … (+3) |
| 917 | [Community 856](#c-856) | 9 | 0.21 | AgentPool, get_thompson_sampler(), AstroFin Sentinel v5 — Thompson Sampling Agent Selector FIXED: thread-safe singl, Thompson sampling — GUARANTEED to never return empty list., Get or create Thompson sampler — THREAD-SAFE., … (+3) |
| 918 | [Community 890](#c-890) | 9 | 0.20 | core/reward_engine.py — ATOM-STEP-6: Reward Engine for Online RL ===============, Compute discounted cumulative reward., Compute summary statistics from a list of rewards., Computes reward = PnL + AstroBonus - RiskPenalty - UncertaintyPenalty     AstroB, Compute composite reward from trade outcome + astro factors., … (+3) |
| 919 | [Community 909](#c-909) | 9 | 0.20 | core/reward_engine.py — ATOM-STEP-6: Reward Engine for Online RL ===============, Compute discounted cumulative reward., Compute summary statistics from a list of rewards., Computes reward = PnL + AstroBonus - RiskPenalty - UncertaintyPenalty     AstroB, Compute composite reward from trade outcome + astro factors., … (+3) |
| 920 | [Community 922](#c-922) | 9 | 0.20 | core/reward_engine.py — ATOM-STEP-6: Reward Engine for Online RL ===============, Compute discounted cumulative reward., Compute summary statistics from a list of rewards., Computes reward = PnL + AstroBonus - RiskPenalty - UncertaintyPenalty     AstroB, Compute composite reward from trade outcome + astro factors., … (+3) |
| 921 | [Community 937](#c-937) | 9 | 0.20 | core/reward_engine.py — ATOM-STEP-6: Reward Engine for Online RL ===============, Compute discounted cumulative reward., Compute summary statistics from a list of rewards., Computes reward = PnL + AstroBonus - RiskPenalty - UncertaintyPenalty     AstroB, Compute composite reward from trade outcome + astro factors., … (+3) |
| 922 | [Community 949](#c-949) | 9 | 0.20 | AgentResponse, ElectoralAgent, AstroFin Sentinel v5 — ElectoralAgent Electional astrology for trading entry tim, Calculate 0-10 muhurta score., Runner for orchestrator., … (+3) |
| 923 | [Community 952](#c-952) | 9 | 0.20 | AgentResponse, ElectoralAgent, AstroFin Sentinel v5 — ElectoralAgent Electional astrology for trading entry tim, Calculate 0-10 muhurta score., Runner for orchestrator., … (+3) |
| 924 | [Community 973](#c-973) | 9 | 0.20 | AgentResponse, ElectoralAgent, AstroFin Sentinel v5 — ElectoralAgent Electional astrology for trading entry tim, Calculate 0-10 muhurta score., Runner for orchestrator., … (+3) |
| 925 | [Community 1209](#c-1209) | 9 | 0.20 | Architecture Snapshot — v9.10, Design Invariants, External Dependencies, Known Limitations, Layer Architecture, … (+3) |
| 926 | [Community 1212](#c-1212) | 9 | 0.20 | A/B Testing — ATOM-META-RL-012, Confidence Levels, Iteration Over All Chromosomes, Key Functions, Main Class: `ABTestRunner`, … (+3) |
| 927 | [Community 1213](#c-1213) | 9 | 0.20 | 8 Типов Choghadiya, Choghadiya — Ведические периоды дня, Muhurta Score, Overview, Rahukaal (Рahu Kaal), … (+3) |
| 928 | [Community 1217](#c-1217) | 9 | 0.20 | 7 workflow files., Architecture Overview, AstroFin Sentinel V5, CI/CD, Development with Ralph Loop, … (+3) |
| 929 | [Community 1218](#c-1218) | 9 | 0.20 | tests/test_dual_mode.py - ATOM-R-027: Dual-Mode Backward Compatibility Tests, Test that function signatures haven't changed., Test that MASFactory failure triggers graceful fallback., Test that CLI correctly detects --masfactory flag., Test that return type hasn't changed., … (+3) |
| 930 | [Community 1227](#c-1227) | 9 | 0.20 | 📐 Code Style, Contributing to AsurDev, 🛠️ Development Setup, 🐳 Docker, ✅ PR Checklist, … (+3) |
| 931 | [Community 1231](#c-1231) | 9 | 0.20 | ATOM Core — Monorepo, Deterministic API, Known Issues, Архитектура, Интеграция с AstroFinSentinelV5, … (+3) |
| 932 | [Community 1236](#c-1236) | 9 | 0.20 | A/B Testing — ATOM-META-RL-012, Confidence Levels, Iteration Over All Chromosomes, Key Functions, Main Class: `ABTestRunner`, … (+3) |
| 933 | [Community 1237](#c-1237) | 9 | 0.20 | 8 Типов Choghadiya, Choghadiya — Ведические периоды дня, Muhurta Score, Overview, Rahukaal (Рahu Kaal), … (+3) |
| 934 | [Community 1241](#c-1241) | 9 | 0.20 | 7 workflow files., Architecture Overview, AstroFin Sentinel V5, CI/CD, Development with Ralph Loop, … (+3) |
| 935 | [Community 1248](#c-1248) | 9 | 0.20 | A/B Testing — ATOM-META-RL-012, Confidence Levels, Iteration Over All Chromosomes, Key Functions, Main Class: `ABTestRunner`, … (+3) |
| 936 | [Community 1249](#c-1249) | 9 | 0.20 | Canonical Root, CI Configuration, Execution Environment Consistency Guide, Problem, Running Tools, … (+3) |
| 937 | [Community 1250](#c-1250) | 9 | 0.20 | 1. Почему возникает ошибка `workflow scope`, 2.1 Генерация SSH-ключа, 2.2 Добавление публичного ключа на GitHub, 2.3 Проверка подключения, 2.4 Переключение remote URL на SSH, … (+3) |
| 938 | [Community 1256](#c-1256) | 9 | 0.20 | 1. Git Push & CI/CD Setup, 2. Inventory Variables (`ansible/group_vars/all.yml`), 3. `post_deploy.sh`, 4. `.env` for ML API, 5. Manual Verification Checklist (10 items), … (+3) |
| 939 | [Community 1261](#c-1261) | 9 | 0.20 | 8 Типов Choghadiya, Choghadiya — Ведические периоды дня, Muhurta Score, Overview, Rahukaal (Рahu Kaal), … (+3) |
| 940 | [Community 1271](#c-1271) | 9 | 0.20 | A/B Testing — ATOM-META-RL-012, Confidence Levels, Iteration Over All Chromosomes, Key Functions, Main Class: `ABTestRunner`, … (+3) |
| 941 | [Community 1273](#c-1273) | 9 | 0.20 | 8 Типов Choghadiya, Choghadiya — Ведические периоды дня, Muhurta Score, Overview, Rahukaal (Рahu Kaal), … (+3) |
| 942 | [Community 1276](#c-1276) | 9 | 0.20 | 7 workflow files., Architecture Overview, AstroFin Sentinel V5, CI/CD, Development with Ralph Loop, … (+3) |
| 943 | [Community 1280](#c-1280) | 9 | 0.20 | 7 workflow files., Architecture Overview, AstroFin Sentinel V5, CI/CD, Development with Ralph Loop, … (+3) |
| 944 | [Community 1281](#c-1281) | 9 | 0.20 | Architecture (Frozen, Layer 1), Files, Growth Targets (Layer 2 Active), Kubernetes Deployment (Sprint 1 — Complete, … (+5) |
| 945 | [Community 945](#c-945) | 9 | 0.19 | OriginCheckResult, OriginPolicy, origin_policy.py — v9.9 OriginPolicy  Enforces node-level origin restrictions on, Update trust score for a sender (used by trust sync)., Add a node to the whitelist., … (+3) |
| 946 | [Community 1106](#c-1106) | 9 | 0.18 | Specification for a single feature., Validate a feature vector. Returns list of warnings (not errors)., A single feature vector at a point in time for a specific node., FeatureSpec, FeatureVector, … (+3) |
| 947 | [Community 858](#c-858) | 9 | 0.17 | Find top-k most similar nodes to target_embedding.         Returns list of (node, Simple K-means clustering of nodes by embedding similarity.         Returns {clu, Builds fixed-size embedding vectors for cluster nodes.     Combines: hardware pr, Build embedding from hardware + historical profile.         Produces a 16-dimens, Build embedding from a feature vector (24h aggregates).         Maps raw feature, … (+3) |
| 948 | [Community 883](#c-883) | 9 | 0.17 | trading/execution/vwap.py — ATOM-STEP-10: VWAP Execution Strategy, Get volume weight for a given slice number., Simulate market volume for a given slice (in base currency units).          Uses, Execute a VWAP order.          Args:             symbol: Trading pair, VWAP execution configuration., … (+3) |
| 949 | [Community 929](#c-929) | 9 | 0.17 | InputContractValidator, ROMA Input Contract Layer — Strict validation (NOT generative). Rejects empty/fa, Raised when input fails validation., Check for dangerous command patterns. Returns pattern name or None., Validates input. Raises ROMAValidationError if invalid.         Returns stripped, … (+3) |
| 950 | [Community 766](#c-766) | 9 | 0.16 | IsolationLevel, main(), PluginInstance, PluginRuntime, PluginSpec, … (+3) |
| 951 | [Community 841](#c-841) | 9 | 0.16 | Any, DataFrame, FailureXGBoost, ndarray, Series, … (+3) |
| 952 | [Community 861](#c-861) | 9 | 0.16 | Any, DataFrame, FailureXGBoost, ndarray, Series, … (+3) |
| 953 | [Community 403](#c-403) | 9 | 0.15 | Any, EvolutionEngine, EvolutionStats, meta_rl/evolution.py -- ATOM-META-RL-002/011, ATOM-META-RL-003: Detect alpha decay.          Alpha decay = reward is dropping, … (+4) |
| 954 | [Community 420](#c-420) | 9 | 0.15 | Any, EvolutionEngine, EvolutionStats, meta_rl/evolution.py -- ATOM-META-RL-002/011, ATOM-META-RL-003: Detect alpha decay.          Alpha decay = reward is dropping, … (+4) |
| 955 | [Community 504](#c-504) | 9 | 0.15 | DriftKind, DriftReport, FunctionSpec, MCPC, MCPCReport, … (+3) |
| 956 | [Community 614](#c-614) | 9 | 0.14 | GovernorSignal, Tests for v8.2a Safety Foundations Module: orchestration.v8_2a_safety_foundation, Simulate a full safe mutation pipeline:         1. snapshot → 2. governor check, When governor blocks, no mutation should be recorded.         Simulates a blocke, … (+4) |
| 957 | [Community 742](#c-742) | 9 | 0.14 | PolicyVerifier, VerificationResult, Step 3 — compute regret upper bound., Stable hash for policy versioning., 3-step policy verification pipeline.     Runs BEFORE decision enters Safety Kern, … (+4) |
| 958 | [Community 763](#c-763) | 9 | 0.14 | PolicyVerifier, VerificationResult, Step 3 — compute regret upper bound., Stable hash for policy versioning., 3-step policy verification pipeline.     Runs BEFORE decision enters Safety Kern, … (+4) |
| 959 | [Community 776](#c-776) | 9 | 0.14 | AgentResponse, BaseAgent, Build a uniform degraded AgentResponse.          Args:             reason: One o, Запрос к RAG базе знаний.          Использовать когда:         - Вопрос выходит, Форматировать результаты RAG для включения в ответ., … (+3) |
| 960 | [Community 795](#c-795) | 9 | 0.14 | AgentResponse, BaseAgent, Build a uniform degraded AgentResponse.          Args:             reason: One o, Запрос к RAG базе знаний.          Использовать когда:         - Вопрос выходит, Форматировать результаты RAG для включения в ответ., … (+3) |
| 961 | [Community 803](#c-803) | 9 | 0.14 | AgentResponse, BaseAgent, Build a uniform degraded AgentResponse.          Args:             reason: One o, Запрос к RAG базе знаний.          Использовать когда:         - Вопрос выходит, Форматировать результаты RAG для включения в ответ., … (+3) |
| 962 | [Community 955](#c-955) | 9 | 0.14 | test_reward.py — ATOM-REWARD-001: Reward Pipeline Tests  Tests: 1. EMA stabiliza, Full reward pipeline., Pipeline always returns clamped values., RewardResult has all required fields., Smoothed reward should vary less than raw., … (+3) |
| 963 | [Community 976](#c-976) | 9 | 0.14 | test_reward.py — ATOM-REWARD-001: Reward Pipeline Tests  Tests: 1. EMA stabiliza, Full reward pipeline., Pipeline always returns clamped values., RewardResult has all required fields., Smoothed reward should vary less than raw., … (+3) |
| 964 | [Community 984](#c-984) | 9 | 0.14 | test_reward.py — ATOM-REWARD-001: Reward Pipeline Tests  Tests: 1. EMA stabiliza, Full reward pipeline., Pipeline always returns clamped values., RewardResult has all required fields., Smoothed reward should vary less than raw., … (+3) |
| 965 | [Community 999](#c-999) | 9 | 0.14 | test_reward.py — ATOM-REWARD-001: Reward Pipeline Tests  Tests: 1. EMA stabiliza, Full reward pipeline., Pipeline always returns clamped values., RewardResult has all required fields., Smoothed reward should vary less than raw., … (+3) |
| 966 | [Community 241](#c-241) | 9 | 0.13 | TestAxisVector, TestUnifiedStateMetricTensor, AxisVector, Full scalar metric: weighted sum of axis vector.         If axis_vec not provide, Human-readable severity level., … (+3) |
| 967 | [Community 638](#c-638) | 9 | 0.13 | PluginToOperatorConverter, CRDSpec, generate_controller_code(), generate_crd_yaml(), plugin_to_crd(), … (+3) |
| 968 | [Community 708](#c-708) | 9 | 0.13 | _MetaRLAuditLog, MetaRLDecisionRecord, ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations., Serialize to dict for storage., Deserialize from dict., … (+3) |
| 969 | [Community 859](#c-859) | 9 | 0.13 | Linear regression slope over data points., Rate of change: (last - first) / count., Count consecutive failures ending at current time., _consecutive(), _derivative(), … (+3) |
| 970 | [Community 634](#c-634) | 9 | 0.12 | GPULock, GPULockManager, Register callback to fire when GPU is released., Prevents two jobs from running on the same GPU simultaneously.     Uses in-memor, Acquire lock on GPU for job.         Returns True if acquired, … (+5) |
| 971 | [Community 680](#c-680) | 9 | 0.12 | True if ALL metrics are within their bounds., Return per-metric violation records (empty = all within bounds)., Aggregate violation score 0..1.          Uses max-severity across bounds: any si, Compute envelope violation score from DriftProfiler episodes.          Maps drif, Store violation records for trend analysis., … (+4) |
| 972 | [Community 786](#c-786) | 9 | 0.12 | DeterministicTraceRecorder, ACOS TraceRecorder — fully contract-compliant implementation., Clear all traces. For testing only., Idempotency check — returns True if trace exists. Patch 2., Contract-compliant TraceRecorder.          Guarantees:     - get_trace() always, … (+3) |
| 973 | [Community 827](#c-827) | 9 | 0.12 | Тест адаптивного изменения window_size., Создаём чистый LagWindow перед каждым тестом., При низкой волатильности (vol <= 0.005) окно увеличивается., При высокой волатильности (vol >= 0.02) окно уменьшается., При нормальной волатильности окно остаётся базовым., … (+3) |
| 974 | [Community 829](#c-829) | 9 | 0.12 | Тест адаптивного изменения window_size., Создаём чистый LagWindow перед каждым тестом., При низкой волатильности (vol <= 0.005) окно увеличивается., При высокой волатильности (vol >= 0.02) окно уменьшается., При нормальной волатильности окно остаётся базовым., … (+3) |
| 975 | [Community 846](#c-846) | 9 | 0.12 | Тест адаптивного изменения window_size., Создаём чистый LagWindow перед каждым тестом., При низкой волатильности (vol <= 0.005) окно увеличивается., При высокой волатильности (vol >= 0.02) окно уменьшается., При нормальной волатильности окно остаётся базовым., … (+3) |
| 976 | [Community 873](#c-873) | 9 | 0.12 | Тест адаптивного изменения window_size., Создаём чистый LagWindow перед каждым тестом., При низкой волатильности (vol <= 0.005) окно увеличивается., При высокой волатильности (vol >= 0.02) окно уменьшается., При нормальной волатильности окно остаётся базовым., … (+3) |
| 977 | [Community 464](#c-464) | 9 | 0.11 | ControlSignal, WeightDelta, Meta-Adaptive Control Layer — v7.8 Closes the loop: temporal proof output → cont, StabilityWeightedArbitrator — v7.8 ControlArbitrator that adjusts per-source wei, ControlArbitrator extended with per-source stability weights.     Weights are ad, … (+3) |
| 978 | [Community 525](#c-525) | 9 | 0.10 | DecisionGate, Cost Decision Gate — blocks/approves/requires_confirmation     before execution, Return aggregate gate statistics for tenant., t_auth_keys(), t_cost_gate(), … (+5) |
| 979 | [Community 557](#c-557) | 9 | 0.10 | Any, BFTConsensus, PBFT-like consensus engine tolerating f Byzantine nodes.      Thread-safety note, Number of nodes we assume are honest (n - f)., Returns True if we have received ≥ 2f+1 COMMIT votes., … (+3) |
| 980 | [Community 174](#c-174) | 9 | 0.09 | ChaosObservabilityBridge, DriftCorrelation, Unified API: owns correlation store, provides full chaos↔drift integration., Records a causal link between a chaos event and a detected drift episode., … (+4) |
| 981 | [Community 319](#c-319) | 9 | 0.09 | Any, ExecutionState, _payload_to_dict(), StateReducer, TestAmneziaWG, … (+3) |
| 982 | [Community 1304](#c-1304) | 8 | 0.58 | cprint(), main(), test_caching(), test_fallback(), test_meta_questioning_integration(), … (+3) |
| 983 | [Community 1328](#c-1328) | 8 | 0.58 | cprint(), main(), test_caching(), test_fallback(), test_meta_questioning_integration(), … (+3) |
| 984 | [Community 1346](#c-1346) | 8 | 0.58 | cprint(), main(), test_caching(), test_fallback(), test_meta_questioning_integration(), … (+3) |
| 985 | [Community 1358](#c-1358) | 8 | 0.58 | cprint(), main(), test_caching(), test_fallback(), test_meta_questioning_integration(), … (+3) |
| 986 | [Community 1289](#c-1289) | 8 | 0.53 | import_dashboards(), log(), main(), notify(), run_loadtest(), … (+3) |
| 987 | [Community 1341](#c-1341) | 8 | 0.53 | import_dashboards(), log(), main(), notify(), run_loadtest(), … (+3) |
| 988 | [Community 1293](#c-1293) | 8 | 0.36 | compute_astro_reward(), get_astro_market_phase(), get_lunar_phase_score(), get_nakshatra_score(), get_planetary_aspect_score(), … (+3) |
| 989 | [Community 1297](#c-1297) | 8 | 0.36 | compute_astro_reward(), get_astro_market_phase(), get_lunar_phase_score(), get_nakshatra_score(), get_planetary_aspect_score(), … (+3) |
| 990 | [Community 1321](#c-1321) | 8 | 0.36 | compute_astro_reward(), get_astro_market_phase(), get_lunar_phase_score(), get_nakshatra_score(), get_planetary_aspect_score(), … (+3) |
| 991 | [Community 1352](#c-1352) | 8 | 0.36 | compute_astro_reward(), get_astro_market_phase(), get_lunar_phase_score(), get_nakshatra_score(), get_planetary_aspect_score(), … (+3) |
| 992 | [Community 1206](#c-1206) | 8 | 0.33 | estimate_q_star(), is_similar_trajectory(), knn_q_star(), amre/similarity.py — Trajectory similarity + Q* estimation, select_top_k_trajectories(), … (+3) |
| 993 | [Community 1210](#c-1210) | 8 | 0.33 | estimate_q_star(), is_similar_trajectory(), knn_q_star(), amre/similarity.py — Trajectory similarity + Q* estimation, select_top_k_trajectories(), … (+3) |
| 994 | [Community 1234](#c-1234) | 8 | 0.33 | estimate_q_star(), is_similar_trajectory(), knn_q_star(), amre/similarity.py — Trajectory similarity + Q* estimation, select_top_k_trajectories(), … (+3) |
| 995 | [Community 1268](#c-1268) | 8 | 0.33 | estimate_q_star(), is_similar_trajectory(), knn_q_star(), amre/similarity.py — Trajectory similarity + Q* estimation, select_top_k_trajectories(), … (+3) |
| 996 | [Community 1302](#c-1302) | 8 | 0.33 | cmd_analyze(), cmd_log(), cmd_propose(), cmd_run(), main(), … (+3) |
| 997 | [Community 1310](#c-1310) | 8 | 0.33 | check_ollama(), check_postgresql(), check_venv(), main(), Проверка виртуального окружения., … (+3) |
| 998 | [Community 1326](#c-1326) | 8 | 0.33 | cmd_analyze(), cmd_log(), cmd_propose(), cmd_run(), main(), … (+3) |
| 999 | [Community 1334](#c-1334) | 8 | 0.33 | check_ollama(), check_postgresql(), check_venv(), main(), Проверка виртуального окружения., … (+3) |
| 1000 | [Community 1343](#c-1343) | 8 | 0.33 | cmd_analyze(), cmd_log(), cmd_propose(), cmd_run(), main(), … (+3) |
| 1001 | [Community 1356](#c-1356) | 8 | 0.33 | cmd_analyze(), cmd_log(), cmd_propose(), cmd_run(), main(), … (+3) |
| 1002 | [Community 1363](#c-1363) | 8 | 0.33 | check_ollama(), check_postgresql(), check_venv(), main(), Проверка виртуального окружения., … (+3) |
| 1003 | [Community 1369](#c-1369) | 8 | 0.33 | check_ollama(), check_postgresql(), check_venv(), main(), Проверка виртуального окружения., … (+3) |
| 1004 | [Community 1307](#c-1307) | 8 | 0.31 | Path, extract_comment_text(), main(), process_file(), Если строка является однострочным комментарием с кириллицей, … (+5) |
| 1005 | [Community 1331](#c-1331) | 8 | 0.31 | Path, extract_comment_text(), main(), process_file(), Если строка является однострочным комментарием с кириллицей, … (+5) |
| 1006 | [Community 1360](#c-1360) | 8 | 0.31 | Path, extract_comment_text(), main(), process_file(), Если строка является однострочным комментарием с кириллицей, … (+5) |
| 1007 | [Community 1365](#c-1365) | 8 | 0.31 | Path, extract_comment_text(), main(), process_file(), Если строка является однострочным комментарием с кириллицей, … (+5) |
| 1008 | [Community 1316](#c-1316) | 8 | 0.28 | Any, get_risk_score(), health_check(), _is_circuit_open(), ML Inference Client — thin wrapper around the /predict API.  Used by any compone, … (+3) |
| 1009 | [Community 1022](#c-1022) | 8 | 0.27 | escalate(), load_escalation(), load_state(), main(), RecoveryEngine, … (+3) |
| 1010 | [Community 1040](#c-1040) | 8 | 0.27 | escalate(), load_escalation(), load_state(), main(), RecoveryEngine, … (+3) |
| 1011 | [Community 1254](#c-1254) | 8 | 0.27 | AuthContext, get_auth_context(), FastAPI-native auth dependency — runs AFTER middleware chain completes., FastAPI dependency — reads auth state set by AuthMiddleware.     Runs after full, Require authentication: raises 401 if no valid auth found.     Use this as a Dep, … (+3) |
| 1012 | [Community 788](#c-788) | 8 | 0.25 | Capability, CapabilityDenied, CapabilitySet, enforce(), enforce_all(), … (+3) |
| 1013 | [Community 811](#c-811) | 8 | 0.25 | Capability, CapabilityDenied, CapabilitySet, enforce(), enforce_all(), … (+3) |
| 1014 | [Community 1406](#c-1406) | 8 | 0.25 | 11. Agent Selection Logging, API, Belief Update Still Primary, File: `core/belief.py` + `migrations/0007_agent_selection_log.sql`, How It Works, … (+3) |
| 1015 | [Community 1407](#c-1407) | 8 | 0.25 | 9. Thompson Sampling (Agent Selection), Agent Pools, Algorithm, CLI, Files, … (+3) |
| 1016 | [Community 1214](#c-1214) | 8 | 0.24 | APIKeyConfig, load_api_keys(), meta_rl/security.py — ATOM-META-RL-009: Secure API Key Management  Security requ, Validate that live mode can be safely enabled.      Returns:         (can_enable, Validated API key configuration., … (+3) |
| 1017 | [Community 1238](#c-1238) | 8 | 0.24 | APIKeyConfig, load_api_keys(), meta_rl/security.py — ATOM-META-RL-009: Secure API Key Management  Security requ, Validate that live mode can be safely enabled.      Returns:         (can_enable, Validated API key configuration., … (+3) |
| 1018 | [Community 1262](#c-1262) | 8 | 0.24 | APIKeyConfig, load_api_keys(), meta_rl/security.py — ATOM-META-RL-009: Secure API Key Management  Security requ, Validate that live mode can be safely enabled.      Returns:         (can_enable, Validated API key configuration., … (+3) |
| 1019 | [Community 1274](#c-1274) | 8 | 0.24 | APIKeyConfig, load_api_keys(), meta_rl/security.py — ATOM-META-RL-009: Secure API Key Management  Security requ, Validate that live mode can be safely enabled.      Returns:         (can_enable, Validated API key configuration., … (+3) |
| 1020 | [Community 548](#c-548) | 8 | 0.23 | AgentRegistry, Any, ExecutionMetrics, get_production_engine(), MASFactoryConfig, … (+3) |
| 1021 | [Community 699](#c-699) | 8 | 0.23 | EmailService, _brand(), test_console_all_types(), test_console_welcome(), test_no_cross_contamination(), … (+3) |
| 1022 | [Community 836](#c-836) | 8 | 0.22 | Any, generate_report(), HTMLReportGenerator, _js_array(), meta_rl/reports.py — ATOM-META-RL-006: HTML/PDF Report Generator (P1.2)  Auto-ge, … (+3) |
| 1023 | [Community 853](#c-853) | 8 | 0.22 | Any, generate_report(), HTMLReportGenerator, _js_array(), meta_rl/reports.py — ATOM-META-RL-006: HTML/PDF Report Generator (P1.2)  Auto-ge, … (+3) |
| 1024 | [Community 868](#c-868) | 8 | 0.22 | Any, generate_report(), HTMLReportGenerator, _js_array(), meta_rl/reports.py — ATOM-META-RL-006: HTML/PDF Report Generator (P1.2)  Auto-ge, … (+3) |
| 1025 | [Community 878](#c-878) | 8 | 0.22 | Any, generate_report(), HTMLReportGenerator, _js_array(), meta_rl/reports.py — ATOM-META-RL-006: HTML/PDF Report Generator (P1.2)  Auto-ge, … (+3) |
| 1026 | [Community 1216](#c-1216) | 8 | 0.22 | Any, observability/metrics.py ======================== Prometheus metrics for AstroFi, Idempotent: records a single agent run, including latency and confidence., Convenience timing context for ad-hoc measurements.      Yields the elapsed time, … (+4) |
| 1027 | [Community 1240](#c-1240) | 8 | 0.22 | Any, observability/metrics.py ======================== Prometheus metrics for AstroFi, Idempotent: records a single agent run, including latency and confidence., Convenience timing context for ad-hoc measurements.      Yields the elapsed time, … (+4) |
| 1028 | [Community 1266](#c-1266) | 8 | 0.22 | Any, observability/metrics.py ======================== Prometheus metrics for AstroFi, Idempotent: records a single agent run, including latency and confidence., Convenience timing context for ad-hoc measurements.      Yields the elapsed time, … (+4) |
| 1029 | [Community 1275](#c-1275) | 8 | 0.22 | Any, observability/metrics.py ======================== Prometheus metrics for AstroFi, Idempotent: records a single agent run, including latency and confidence., Convenience timing context for ad-hoc measurements.      Yields the elapsed time, … (+4) |
| 1030 | [Community 1299](#c-1299) | 8 | 0.22 | fastapi_require_api_key(), API Key authentication., Raise RuntimeError if auth is required but API_KEY is missing., Decorator for Flask: checks X-API-Key header., FastAPI dependency: checks X-API-Key., … (+3) |
| 1031 | [Community 1300](#c-1300) | 8 | 0.22 | 1. Финальный Backup (обязательно выполнить первым), 2. Локальный запуск (Linux/macOS/Windows+WSL), 3. Production deployment, 4. Активация live-режима (реальные деньги), 5. Следующие шаги, … (+3) |
| 1032 | [Community 1301](#c-1301) | 8 | 0.22 | 1. Папка `knowledge/daily_brief/`, 2. CLI-команда `python tools/thompson_cli.py daily-brief`, 3. Генерация ATOM-идей, ATOM-R-040: Интеграция ежедневного агента в рабочий процесс, Будущие расширения (R-040-FUTURE), … (+3) |
| 1033 | [Community 1303](#c-1303) | 8 | 0.22 | Agent Integration, Architecture, AstroFin Sentinel v5 — RAG Knowledge System, Domains, Index Build CLI, … (+3) |
| 1034 | [Community 1323](#c-1323) | 8 | 0.22 | fastapi_require_api_key(), API Key authentication., Raise RuntimeError if auth is required but API_KEY is missing., Decorator for Flask: checks X-API-Key header., FastAPI dependency: checks X-API-Key., … (+3) |
| 1035 | [Community 1324](#c-1324) | 8 | 0.22 | 1. Финальный Backup (обязательно выполнить первым), 2. Локальный запуск (Linux/macOS/Windows+WSL), 3. Production deployment, 4. Активация live-режима (реальные деньги), 5. Следующие шаги, … (+3) |
| 1036 | [Community 1325](#c-1325) | 8 | 0.22 | 1. Папка `knowledge/daily_brief/`, 2. CLI-команда `python tools/thompson_cli.py daily-brief`, 3. Генерация ATOM-идей, ATOM-R-040: Интеграция ежедневного агента в рабочий процесс, Будущие расширения (R-040-FUTURE), … (+3) |
| 1037 | [Community 1327](#c-1327) | 8 | 0.22 | Agent Integration, Architecture, AstroFin Sentinel v5 — RAG Knowledge System, Domains, Index Build CLI, … (+3) |
| 1038 | [Community 1335](#c-1335) | 8 | 0.22 | FAIL FAST — raise if object violates TraceRecorderContract., Validate trace has required fields., Any, Decision, ExecutionResult, … (+3) |
| 1039 | [Community 1336](#c-1336) | 8 | 0.22 | fastapi_require_api_key(), API Key authentication., Raise RuntimeError if auth is required but API_KEY is missing., Decorator for Flask: checks X-API-Key header., FastAPI dependency: checks X-API-Key., … (+3) |
| 1040 | [Community 1338](#c-1338) | 8 | 0.22 | 1. Финальный Backup (обязательно выполнить первым), 2. Локальный запуск (Linux/macOS/Windows+WSL), 3. Production deployment, 4. Активация live-режима (реальные деньги), 5. Следующие шаги, … (+3) |
| 1041 | [Community 1342](#c-1342) | 8 | 0.22 | 1. Папка `knowledge/daily_brief/`, 2. CLI-команда `python tools/thompson_cli.py daily-brief`, 3. Генерация ATOM-идей, ATOM-R-040: Интеграция ежедневного агента в рабочий процесс, Будущие расширения (R-040-FUTURE), … (+3) |
| 1042 | [Community 1344](#c-1344) | 8 | 0.22 | Agent Integration, Architecture, AstroFin Sentinel v5 — RAG Knowledge System, Domains, Index Build CLI, … (+3) |
| 1043 | [Community 1351](#c-1351) | 8 | 0.22 | 1. Pattern A: `from __future__ import annotations` added to 14 agents, 2. Pytest markers registered + applied to 33 test files, 3. `meta_rl/basket.py`, 4. `.bak` files, Changes, … (+3) |
| 1044 | [Community 1353](#c-1353) | 8 | 0.22 | fastapi_require_api_key(), API Key authentication., Raise RuntimeError if auth is required but API_KEY is missing., Decorator for Flask: checks X-API-Key header., FastAPI dependency: checks X-API-Key., … (+3) |
| 1045 | [Community 1354](#c-1354) | 8 | 0.22 | 1. Финальный Backup (обязательно выполнить первым), 2. Локальный запуск (Linux/macOS/Windows+WSL), 3. Production deployment, 4. Активация live-режима (реальные деньги), 5. Следующие шаги, … (+3) |
| 1046 | [Community 1355](#c-1355) | 8 | 0.22 | 1. Папка `knowledge/daily_brief/`, 2. CLI-команда `python tools/thompson_cli.py daily-brief`, 3. Генерация ATOM-идей, ATOM-R-040: Интеграция ежедневного агента в рабочий процесс, Будущие расширения (R-040-FUTURE), … (+3) |
| 1047 | [Community 1357](#c-1357) | 8 | 0.22 | Agent Integration, Architecture, AstroFin Sentinel v5 — RAG Knowledge System, Domains, Index Build CLI, … (+3) |
| 1048 | [Community 1364](#c-1364) | 8 | 0.22 | 🏗️ Architecture, ⚡ Commands, 📦 Core Modules, 🔑 Features, 🚀 Quick Start, … (+3) |
| 1049 | [Community 794](#c-794) | 8 | 0.20 | Queue, TransportAdapter — BRIDGE between DRL (fault layer) and real gRPC network.  CRIT, gRPC client — node-to-node unidirectional send. Thread-safe, connection-pooled, RPC package — real network transport for ATOMFederationOS.  Modules ------- prot, … (+4) |
| 1050 | [Community 893](#c-893) | 8 | 0.20 | Any, CompositeRankingEngine, rank_all_sessions(), meta_rl/ranking.py -- ATOM-META-RL-008: Composite Strategy Ranking (P1.2), Load all sessions and return top-n globally-ranked strategies., … (+3) |
| 1051 | [Community 912](#c-912) | 8 | 0.20 | Any, CompositeRankingEngine, rank_all_sessions(), meta_rl/ranking.py -- ATOM-META-RL-008: Composite Strategy Ranking (P1.2), Load all sessions and return top-n globally-ranked strategies., … (+3) |
| 1052 | [Community 930](#c-930) | 8 | 0.20 | Any, CompositeRankingEngine, rank_all_sessions(), meta_rl/ranking.py -- ATOM-META-RL-008: Composite Strategy Ranking (P1.2), Load all sessions and return top-n globally-ranked strategies., … (+3) |
| 1053 | [Community 940](#c-940) | 8 | 0.20 | Any, CompositeRankingEngine, rank_all_sessions(), meta_rl/ranking.py -- ATOM-META-RL-008: Composite Strategy Ranking (P1.2), Load all sessions and return top-n globally-ranked strategies., … (+3) |
| 1054 | [Community 1267](#c-1267) | 8 | 0.20 | Любая попытка мутации вне ExecutionGateway., SafetyViolationError, _block_direct_mutation(), MutationExecutorMetaclass, Called at module import time to prevent direct access.          If this module i, … (+3) |
| 1055 | [Community 1097](#c-1097) | 8 | 0.18 | ChangeType, DAGValidator, KahnSortValid, DAG Incremental Fingerprint — v8.5  Architecture:   DAGFingerprint         — ful, Formal DAG invariants (used by InvariantRegistry).      I1:  Acyclic           —, … (+4) |
| 1056 | [Community 1141](#c-1141) | 8 | 0.18 | BasketMetrics, EvaluationResult, Типы данных для meta_rl., Возвращает экземпляр с нулевыми метриками., Метрики корзины стратегий., … (+3) |
| 1057 | [Community 1144](#c-1144) | 8 | 0.18 | Any, ACOS Scheduler Contract — enforced scheduler interface., SchedulerContract, validate_scheduler_contract(), Route job to appropriate executor. MUST return executor name., … (+3) |
| 1058 | [Community 1167](#c-1167) | 8 | 0.18 | BasketMetrics, EvaluationResult, Типы данных для meta_rl., Возвращает экземпляр с нулевыми метриками., Метрики корзины стратегий., … (+3) |
| 1059 | [Community 1171](#c-1171) | 8 | 0.18 | Execute compiled DAG. MUST return dict with 'results' and 'state'., Return current engine state., FAIL FAST — raise if object violates ExecutionEngineContract., ENFORCED contract for execution engines., Any, … (+3) |
| 1060 | [Community 1172](#c-1172) | 8 | 0.18 | Compile DAG into executable schedule. MUST return dict with 'nodes'., Route job to appropriate executor. MUST return executor name., FAIL FAST — raise if object violates SchedulerContract., ENFORCED contract for all Scheduler implementations., Any, … (+3) |
| 1061 | [Community 1198](#c-1198) | 8 | 0.18 | BasketMetrics, EvaluationResult, Типы данных для meta_rl., Возвращает экземпляр с нулевыми метриками., Метрики корзины стратегий., … (+3) |
| 1062 | [Community 540](#c-540) | 8 | 0.17 | EvolutionRecord, Adapts UST thresholds based on observed system behavior., SystemState, test(), test_evolution(), … (+3) |
| 1063 | [Community 871](#c-871) | 8 | 0.17 | Select task by tick % len(tasks). Fully deterministic., Sort by (-priority, task_id) — deterministic tie-breaking.         tick is used, Weighted selection: higher weight → more frequent selection.         Uses tick a, Always select highest priority task. tick only for tie-breaking., … (+5) |
| 1064 | [Community 1086](#c-1086) | 8 | 0.17 | tests/data_room/test_data_room.py ================================= Tests for th, If primary resolver raises, blueprint tries the secondary., If all resolvers in the chain fail, get_price() returns None., … (+5) |
| 1065 | [Community 432](#c-432) | 8 | 0.16 | ExecutionGateway, AtomOperatorReconciler, CircuitBreaker, ClusterState, DriftProfiler, … (+3) |
| 1066 | [Community 665](#c-665) | 8 | 0.16 | Category, DigestAnalysis, DigestAnalyzer, Finding, Analyzes multi-agent digest files., … (+3) |
| 1067 | [Community 687](#c-687) | 8 | 0.16 | Category, DigestAnalysis, DigestAnalyzer, Finding, Analyzes multi-agent digest files., … (+3) |
| 1068 | [Community 706](#c-706) | 8 | 0.16 | Category, DigestAnalysis, DigestAnalyzer, Finding, Analyzes multi-agent digest files., … (+3) |
| 1069 | [Community 716](#c-716) | 8 | 0.16 | Category, DigestAnalysis, DigestAnalyzer, Finding, Analyzes multi-agent digest files., … (+3) |
| 1070 | [Community 881](#c-881) | 8 | 0.16 | NonceCheckResult, NonceWindow, replay_protection.py — v9.9 NonceSequenceValidator  Provides replay attack prote, Check whether (sender_id, seq) is a replay, … (+5) |
| 1071 | [Community 357](#c-357) | 8 | 0.15 | ControlSignal, DecisionRecord, ProofKernel, Return all signals sorted + DecisionRecord., Run full cross-layer verification on a DecisionRecord., … (+3) |
| 1072 | [Community 696](#c-696) | 8 | 0.15 | make_cost_gauge(), make_gpu_bar(), make_timeline(), refresh(), EventType, … (+3) |
| 1073 | [Community 740](#c-740) | 8 | 0.15 | Any, FailMode, FailureIsolator, FailureTrigger, Incident, … (+3) |
| 1074 | [Community 828](#c-828) | 8 | 0.15 | Create isolated replay engine seeded from scenario snapshot., Set engine state to reproduce the violation., Return list of active violations (empty = healthy)., Isolated engine for deterministic replay — no side effects on real system., Apply recovery from RecoveryActionObj., … (+3) |
| 1075 | [Community 897](#c-897) | 8 | 0.15 | AdaptiveSlippageModel, trading/execution/slippage.py — ATOM-STEP-10: Slippage Models, Fixed-percent slippage model — no market intelligence.      slippage_bps is cons, Calculate slippage for a trade.          Args:             side: "buy" or "sell", Slippage model with market microstructure intelligence.      Accounts for:     -, … (+3) |
| 1076 | [Community 917](#c-917) | 8 | 0.15 | AdaptiveSlippageModel, trading/execution/slippage.py — ATOM-STEP-10: Slippage Models, Fixed-percent slippage model — no market intelligence.      slippage_bps is cons, Calculate slippage for a trade.          Args:             side: "buy" or "sell", Slippage model with market microstructure intelligence.      Accounts for:     -, … (+3) |
| 1077 | [Community 944](#c-944) | 8 | 0.15 | AdaptiveSlippageModel, trading/execution/slippage.py — ATOM-STEP-10: Slippage Models, Fixed-percent slippage model — no market intelligence.      slippage_bps is cons, Calculate slippage for a trade.          Args:             side: "buy" or "sell", Slippage model with market microstructure intelligence.      Accounts for:     -, … (+3) |
| 1078 | [Community 466](#c-466) | 8 | 0.14 | DecisionRecord, InvariantRegistry, InvariantSpec, InvariantType, Run all enabled invariants against a DecisionRecord., … (+3) |
| 1079 | [Community 903](#c-903) | 8 | 0.14 | ndarray, Returns True if oscillation pattern is detected., Apply oscillation penalty to delta (scales magnitude down)., Rolling success rate over the signal window., Human-readable summary of recent signal history., … (+4) |
| 1080 | [Community 725](#c-725) | 8 | 0.13 | GatewayContext, _ImportFirewall, import_guard.py — atom-federation-os v9.0+P0.4  Import-time execution firewall v, Python 3.10+ meta_path hook., Remove the import firewall. Used only for testing., … (+3) |
| 1081 | [Community 891](#c-891) | 8 | 0.13 | 11.1: EMA stabilization — first value seeds, NOT 0., Oscillating values should NOT produce oscillating EMA., EMA should converge toward stable values., BTC and ETH should have separate EMA states., … (+5) |
| 1082 | [Community 910](#c-910) | 8 | 0.13 | 11.1: EMA stabilization — first value seeds, NOT 0., Oscillating values should NOT produce oscillating EMA., EMA should converge toward stable values., BTC and ETH should have separate EMA states., … (+5) |
| 1083 | [Community 923](#c-923) | 8 | 0.13 | 11.1: EMA stabilization — first value seeds, NOT 0., Oscillating values should NOT produce oscillating EMA., EMA should converge toward stable values., BTC and ETH should have separate EMA states., … (+5) |
| 1084 | [Community 938](#c-938) | 8 | 0.13 | 11.1: EMA stabilization — first value seeds, NOT 0., Oscillating values should NOT produce oscillating EMA., EMA should converge toward stable values., BTC and ETH should have separate EMA states., … (+5) |
| 1085 | [Community 373](#c-373) | 8 | 0.12 | GPUNode, GPUPolicyEngineV2, GPUPolicyResult, JobMetrics, JobState, … (+3) |
| 1086 | [Community 815](#c-815) | 8 | 0.12 | DeterministicStartupSequence, r'''     Deterministic cluster startup sequence.      Guarantees:       - Nodes, Get next node that should start (deterministic order)., Mark node as started., Mark node as ready to execute., … (+3) |
| 1087 | [Community 477](#c-477) | 8 | 0.11 | APIGateway, RateLimiter, Token bucket: returns (allowed, info_dict).         rate_limit = max tokens per, Middleware layer: validates keys, … (+8) |
| 1088 | [Community 279](#c-279) | 8 | 0.09 | ReactionAction, ClosedLoopResilienceController, Convenience: called after each RPC to feed router + metrics., Get best peer for routing., Get full routing state., … (+3) |
| 1089 | [Community 308](#c-308) | 8 | 0.07 | Router must correctly classify queries., AgentResponse must have all required fields and valid ranges., All modules should import without errors., Full pipeline — all agents run, final output is complete., … (+4) |
| 1090 | [Community 310](#c-310) | 8 | 0.07 | Router must correctly classify queries., AgentResponse must have all required fields and valid ranges., All modules should import without errors., Full pipeline — all agents run, final output is complete., … (+4) |
| 1091 | [Community 316](#c-316) | 8 | 0.07 | Router must correctly classify queries., AgentResponse must have all required fields and valid ranges., All modules should import without errors., Full pipeline — all agents run, final output is complete., … (+4) |
| 1092 | [Community 325](#c-325) | 8 | 0.07 | Router must correctly classify queries., AgentResponse must have all required fields and valid ranges., All modules should import without errors., Full pipeline — all agents run, final output is complete., … (+4) |
| 1093 | [Community 328](#c-328) | 8 | 0.07 | Router must correctly classify queries., AgentResponse must have all required fields and valid ranges., All modules should import without errors., Full pipeline — all agents run, final output is complete., … (+4) |
| 1094 | [Community 1401](#c-1401) | 7 | 0.64 | check_ceph(), check_nodes(), check_ray(), check_slurm(), check_wireguard(), … (+2) |
| 1095 | [Community 1433](#c-1433) | 7 | 0.64 | check_ceph(), check_nodes(), check_ray(), check_slurm(), check_wireguard(), … (+2) |
| 1096 | [Community 1390](#c-1390) | 7 | 0.54 | check_port(), cmd_status(), cmd_switch(), get_tunnel_status(), load_config(), … (+2) |
| 1097 | [Community 1427](#c-1427) | 7 | 0.54 | check_port(), cmd_status(), cmd_switch(), get_tunnel_status(), load_config(), … (+2) |
| 1098 | [Community 1380](#c-1380) | 7 | 0.39 | get_market_data_historical(), get_market_data_live(), main(), parse_args(), Generate historical market data using mock (for --mode=historical)., … (+2) |
| 1099 | [Community 1394](#c-1394) | 7 | 0.39 | main(), parse_args(), run_continuous(), run_embedding(), run_export(), … (+2) |
| 1100 | [Community 1413](#c-1413) | 7 | 0.39 | get_market_data_historical(), get_market_data_live(), main(), parse_args(), Generate historical market data using mock (for --mode=historical)., … (+2) |
| 1101 | [Community 1422](#c-1422) | 7 | 0.39 | Compute and display node embeddings., Continuously push metrics and build feature vectors., main(), parse_args(), run_continuous(), … (+2) |
| 1102 | [Community 1439](#c-1439) | 7 | 0.39 | get_market_data_historical(), get_market_data_live(), main(), parse_args(), Generate historical market data using mock (for --mode=historical)., … (+2) |
| 1103 | [Community 1449](#c-1449) | 7 | 0.39 | get_market_data_historical(), get_market_data_live(), main(), parse_args(), Generate historical market data using mock (for --mode=historical)., … (+2) |
| 1104 | [Community 1381](#c-1381) | 7 | 0.36 | _extract_paths(), main(), parse(), r'''Split KNOWN_ISSUES.md into (id, title, … (+6) |
| 1105 | [Community 1414](#c-1414) | 7 | 0.36 | _extract_paths(), main(), parse(), r'''Split KNOWN_ISSUES.md into (id, title, … (+6) |
| 1106 | [Community 1450](#c-1450) | 7 | 0.36 | _extract_paths(), main(), parse(), r'''Split KNOWN_ISSUES.md into (id, title, … (+6) |
| 1107 | [Community 1455](#c-1455) | 7 | 0.36 | _extract_paths(), main(), parse(), r'''Split KNOWN_ISSUES.md into (id, title, … (+6) |
| 1108 | [Community 1383](#c-1383) | 7 | 0.32 | ndarray, generate_training_data(), main(), training/train_residual_model.py — ATOM-STEP-4: Train Residual Model ===========, Generate training data: (features, … (+3) |
| 1109 | [Community 1392](#c-1392) | 7 | 0.32 | AstroFinTrace, build_trace(), ConstraintProfile, ExecutionNode, Factory to build a trace with standard ACOS AstroFin structure., … (+2) |
| 1110 | [Community 1399](#c-1399) | 7 | 0.32 | Any, _compute_score(), _filter_eligible(), score_and_select(), Stateful node selection:       1. Load nodes from DB (not Prometheus directly), … (+2) |
| 1111 | [Community 1416](#c-1416) | 7 | 0.32 | ndarray, generate_training_data(), main(), training/train_residual_model.py — ATOM-STEP-4: Train Residual Model ===========, Generate training data: (features, … (+3) |
| 1112 | [Community 1431](#c-1431) | 7 | 0.32 | Any, _compute_score(), _filter_eligible(), score_and_select(), Compute per-component score breakdown.     Higher available resources → higher s, … (+2) |
| 1113 | [Community 1452](#c-1452) | 7 | 0.32 | ndarray, generate_training_data(), main(), training/train_residual_model.py — ATOM-STEP-4: Train Residual Model ===========, Generate training data: (features, … (+3) |
| 1114 | [Community 1459](#c-1459) | 7 | 0.32 | ndarray, generate_training_data(), main(), training/train_residual_model.py — ATOM-STEP-4: Train Residual Model ===========, Generate training data: (features, … (+3) |
| 1115 | [Community 1219](#c-1219) | 7 | 0.31 | Run healthcheck as subprocess and return (stdout, stderr, exitcode)., run_healthcheck(), test_healthcheck_db_check(), … (+4) |
| 1116 | [Community 1222](#c-1222) | 7 | 0.31 | Run healthcheck as subprocess and return (stdout, stderr, exitcode)., run_healthcheck(), test_healthcheck_db_check(), … (+4) |
| 1117 | [Community 1242](#c-1242) | 7 | 0.31 | Run healthcheck as subprocess and return (stdout, stderr, exitcode)., run_healthcheck(), test_healthcheck_db_check(), … (+4) |
| 1118 | [Community 1277](#c-1277) | 7 | 0.31 | Run healthcheck as subprocess and return (stdout, stderr, exitcode)., run_healthcheck(), test_healthcheck_db_check(), … (+4) |
| 1119 | [Community 1284](#c-1284) | 7 | 0.31 | Run healthcheck as subprocess and return (stdout, stderr, exitcode)., run_healthcheck(), test_healthcheck_db_check(), … (+4) |
| 1120 | [Community 1208](#c-1208) | 7 | 0.29 | _enqueue_event(), Stripe Webhook Microservice — FastAPI app., stripe_webhook(), _sync_tenant(), _verify(), … (+2) |
| 1121 | [Community 1491](#c-1491) | 7 | 0.29 | 2.1 Architecture Overview, 2.2 API Specification, 2.3 Integration Points, 2. DETERMINISTIC KERNEL DESIGN, DeterministicClock, … (+2) |
| 1122 | [Community 1143](#c-1143) | 7 | 0.27 | ExecutionSanityChecker, MarketState, OrderRequest, trading/execution/sanity.py — ATOM-PRODUCTION: Execution Sanity Layer ==========, SanityConfig, … (+2) |
| 1123 | [Community 1169](#c-1169) | 7 | 0.27 | ExecutionSanityChecker, MarketState, OrderRequest, trading/execution/sanity.py — ATOM-PRODUCTION: Execution Sanity Layer ==========, SanityConfig, … (+2) |
| 1124 | [Community 1200](#c-1200) | 7 | 0.27 | ExecutionSanityChecker, MarketState, OrderRequest, trading/execution/sanity.py — ATOM-PRODUCTION: Execution Sanity Layer ==========, SanityConfig, … (+2) |
| 1125 | [Community 1257](#c-1257) | 7 | 0.27 | Path, Trainer, apply_smote(), Train XGBoost with RandomizedSearchCV hyperparameter tuning.     Handles class i, Balance classes using SMOTE oversampling., … (+2) |
| 1126 | [Community 1137](#c-1137) | 7 | 0.25 | AstroCouncil, build_council_result(), compute_weighted_signal(), core/council/council.py - AstroCouncil: Multi-Agent Voting System, resolve_conflict(), … (+2) |
| 1127 | [Community 1163](#c-1163) | 7 | 0.25 | AstroCouncil, build_council_result(), compute_weighted_signal(), core/council/council.py - AstroCouncil: Multi-Agent Voting System, resolve_conflict(), … (+2) |
| 1128 | [Community 1174](#c-1174) | 7 | 0.25 | AstroCouncil, build_council_result(), compute_weighted_signal(), core/council/council.py - AstroCouncil: Multi-Agent Voting System, resolve_conflict(), … (+2) |
| 1129 | [Community 1204](#c-1204) | 7 | 0.25 | Any, load_mult(), PriceQuote, PricingEngine, PricingTier, … (+2) |
| 1130 | [Community 1375](#c-1375) | 7 | 0.25 | EphemerisUnavailableError, require_ephemeris decorator and ephemeris utilities., Decorator that blocks agent execution if Swiss Ephemeris is unavailable.      Us, Raised when agent requires Swiss Ephemeris but it's not available., require_ephemeris(), … (+2) |
| 1131 | [Community 1376](#c-1376) | 7 | 0.25 | Alerts, AstroFin Sentinel V5 - Deployment Guide, Environment Variables, Health Checks, Kubernetes, … (+2) |
| 1132 | [Community 1377](#c-1377) | 7 | 0.25 | Nakshatras — 27 Лунных Мансионов, Overview, Pada (Четверти), Лучшие Nakshatras для трейдинга:, Правила для Muhurta, … (+2) |
| 1133 | [Community 1378](#c-1378) | 7 | 0.25 | 1. Anthropic представила "Dreaming" и multi-agent orchestration для Claude Managed Agents (Public Beta), 2. Graph-of-Agents: новый graph-based фреймворк для мультиагентной координации LLM, 3. OverMind-MCP v2.1.1 — мультифреймворк оркестрация (Claude + Kilo + Gemini + Qwen + Hermes), Multi-Agent AI Daily Digest, Дополнительные noteworthy фреймворки и исследования, … (+2) |
| 1134 | [Community 1379](#c-1379) | 7 | 0.25 | 1. MARS: Role-Based Multi-Agent Collaboration (~50% reduction in token usage), 2. EMS: Efficient Majority-then-Stopping для multi-agent voting (~32% fewer agents), 3. AgentScope v2.0.1: Agent Team service для multi-agent coordination, Multi-Agent AI Daily — 2026-06-12, Дополнительные сигналы (не вошли в топ-3, … (+3) |
| 1135 | [Community 1384](#c-1384) | 7 | 0.25 | build_comparison_chart(), build_comparison_table(), build_convergence_chart(), web/utils/comparison.py — Multi-strategy comparison utilities (ATOM-META-RL-004), Build a convergence line chart (mean + max reward per generation)., … (+2) |
| 1136 | [Community 1386](#c-1386) | 7 | 0.25 | Alerts, AstroFin Sentinel V5 - Deployment Guide, Environment Variables, Health Checks, Kubernetes, … (+2) |
| 1137 | [Community 1388](#c-1388) | 7 | 0.25 | build_comparison_chart(), build_comparison_table(), build_convergence_chart(), web/utils/comparison.py — Multi-strategy comparison utilities (ATOM-META-RL-004), Build a convergence line chart (mean + max reward per generation)., … (+2) |
| 1138 | [Community 1398](#c-1398) | 7 | 0.25 | ACOS — Autonomous Constrained Optimization System, Architecture, Data Flow, Git History, Layer Maturity, … (+2) |
| 1139 | [Community 1404](#c-1404) | 7 | 0.25 | 12. SUCCESS CRITERIA, 13. CI DETERMINISM GATE, 14. SUMMARY SCORECARD, 8.1 SwarmEngine / AsyncExecutionEngine, 8.2 DeterministicScheduler Integration, … (+2) |
| 1140 | [Community 1408](#c-1408) | 7 | 0.25 | EphemerisUnavailableError, require_ephemeris decorator and ephemeris utilities., Decorator that blocks agent execution if Swiss Ephemeris is unavailable.      Us, Raised when agent requires Swiss Ephemeris but it's not available., require_ephemeris(), … (+2) |
| 1141 | [Community 1409](#c-1409) | 7 | 0.25 | Alerts, AstroFin Sentinel V5 - Deployment Guide, Environment Variables, Health Checks, Kubernetes, … (+2) |
| 1142 | [Community 1410](#c-1410) | 7 | 0.25 | Nakshatras — 27 Лунных Мансионов, Overview, Pada (Четверти), Лучшие Nakshatras для трейдинга:, Правила для Muhurta, … (+2) |
| 1143 | [Community 1411](#c-1411) | 7 | 0.25 | 1. Anthropic представила "Dreaming" и multi-agent orchestration для Claude Managed Agents (Public Beta), 2. Graph-of-Agents: новый graph-based фреймворк для мультиагентной координации LLM, 3. OverMind-MCP v2.1.1 — мультифреймворк оркестрация (Claude + Kilo + Gemini + Qwen + Hermes), Multi-Agent AI Daily Digest, Дополнительные noteworthy фреймворки и исследования, … (+2) |
| 1144 | [Community 1412](#c-1412) | 7 | 0.25 | 1. MARS: Role-Based Multi-Agent Collaboration (~50% reduction in token usage), 2. EMS: Efficient Majority-then-Stopping для multi-agent voting (~32% fewer agents), 3. AgentScope v2.0.1: Agent Team service для multi-agent coordination, Multi-Agent AI Daily — 2026-06-12, Дополнительные сигналы (не вошли в топ-3, … (+3) |
| 1145 | [Community 1417](#c-1417) | 7 | 0.25 | build_comparison_chart(), build_comparison_table(), build_convergence_chart(), web/utils/comparison.py — Multi-strategy comparison utilities (ATOM-META-RL-004), Build a convergence line chart (mean + max reward per generation)., … (+2) |
| 1146 | [Community 1421](#c-1421) | 7 | 0.25 | Alerts, AstroFin Sentinel V5 - Deployment Guide, Environment Variables, Health Checks, Kubernetes, … (+2) |
| 1147 | [Community 1435](#c-1435) | 7 | 0.25 | Nakshatras — 27 Лунных Мансионов, Overview, Pada (Четверти), Лучшие Nakshatras для трейдинга:, Правила для Muhurta, … (+2) |
| 1148 | [Community 1436](#c-1436) | 7 | 0.25 | 1. Anthropic представила "Dreaming" и multi-agent orchestration для Claude Managed Agents (Public Beta), 2. Graph-of-Agents: новый graph-based фреймворк для мультиагентной координации LLM, 3. OverMind-MCP v2.1.1 — мультифреймворк оркестрация (Claude + Kilo + Gemini + Qwen + Hermes), Multi-Agent AI Daily Digest, Дополнительные noteworthy фреймворки и исследования, … (+2) |
| 1149 | [Community 1437](#c-1437) | 7 | 0.25 | 1. MARS: Role-Based Multi-Agent Collaboration (~50% reduction in token usage), 2. EMS: Efficient Majority-then-Stopping для multi-agent voting (~32% fewer agents), 3. AgentScope v2.0.1: Agent Team service для multi-agent coordination, Multi-Agent AI Daily — 2026-06-12, Дополнительные сигналы (не вошли в топ-3, … (+3) |
| 1150 | [Community 1438](#c-1438) | 7 | 0.25 | Healing cooldown, Kubernetes Operator v7.0 — ATOM Federation OS Control Plane, Как развернуть, Реакционный цикл, Режимы работы, … (+2) |
| 1151 | [Community 1445](#c-1445) | 7 | 0.25 | Alerts, AstroFin Sentinel V5 - Deployment Guide, Environment Variables, Health Checks, Kubernetes, … (+2) |
| 1152 | [Community 1446](#c-1446) | 7 | 0.25 | Nakshatras — 27 Лунных Мансионов, Overview, Pada (Четверти), Лучшие Nakshatras для трейдинга:, Правила для Muhurta, … (+2) |
| 1153 | [Community 1447](#c-1447) | 7 | 0.25 | 1. Anthropic представила "Dreaming" и multi-agent orchestration для Claude Managed Agents (Public Beta), 2. Graph-of-Agents: новый graph-based фреймворк для мультиагентной координации LLM, 3. OverMind-MCP v2.1.1 — мультифреймворк оркестрация (Claude + Kilo + Gemini + Qwen + Hermes), Multi-Agent AI Daily Digest, Дополнительные noteworthy фреймворки и исследования, … (+2) |
| 1154 | [Community 1448](#c-1448) | 7 | 0.25 | 1. MARS: Role-Based Multi-Agent Collaboration (~50% reduction in token usage), 2. EMS: Efficient Majority-then-Stopping для multi-agent voting (~32% fewer agents), 3. AgentScope v2.0.1: Agent Team service для multi-agent coordination, Multi-Agent AI Daily — 2026-06-12, Дополнительные сигналы (не вошли в топ-3, … (+3) |
| 1155 | [Community 1453](#c-1453) | 7 | 0.25 | build_comparison_chart(), build_comparison_table(), build_convergence_chart(), web/utils/comparison.py — Multi-strategy comparison utilities (ATOM-META-RL-004), Build a convergence line chart (mean + max reward per generation)., … (+2) |
| 1156 | [Community 1461](#c-1461) | 7 | 0.25 | build_comparison_chart(), build_comparison_table(), build_convergence_chart(), web/utils/comparison.py — Multi-strategy comparison utilities (ATOM-META-RL-004), Build a convergence line chart (mean + max reward per generation)., … (+2) |
| 1157 | [Community 1012](#c-1012) | 7 | 0.23 | GainAdjustment, Given a set of actuator commands and expected gain, compute gain adjustm, Apply the gain adjustment to a list of commands.         Modifies command magnit, A computed gain adjustment to apply to the actuator., … (+3) |
| 1158 | [Community 505](#c-505) | 7 | 0.22 | CrossLayerTheorem, LayerMetrics, LayerState, v107_cross_layer_proof.py — v10.7 Cross-Layer Consistency Theorem  FORMAL GOAL:, Formal cross-layer consistency checker.          Proves that layer states are co, … (+2) |
| 1159 | [Community 624](#c-624) | 7 | 0.22 | AgentRegistry, Any, ExecutionMetrics, get_production_engine(), MASFactoryConfig, … (+2) |
| 1160 | [Community 636](#c-636) | 7 | 0.22 | AgentRegistry, Any, ExecutionMetrics, get_production_engine(), MASFactoryConfig, … (+2) |
| 1161 | [Community 647](#c-647) | 7 | 0.22 | AgentRegistry, Any, ExecutionMetrics, get_production_engine(), MASFactoryConfig, … (+2) |
| 1162 | [Community 1127](#c-1127) | 7 | 0.22 | Check if any eligible node has enough free memory., Enforces cluster admission policy.     All job submissions MUST pass through her, Returns (decision, reason, job_id_or_None).         Decision is final — REJECT m, … (+4) |
| 1163 | [Community 1128](#c-1128) | 7 | 0.22 | Check if any eligible node has enough free memory., Enforces cluster admission policy.     All job submissions MUST pass through her, Returns (decision, reason, job_id_or_None).         Decision is final — REJECT m, … (+4) |
| 1164 | [Community 1253](#c-1253) | 7 | 0.22 | BFTVote, Receive a PREPARE vote from another node.         Accumulate until we reach prep, When we reach PREPARED, broadcast COMMIT vote., Receive a COMMIT vote from another node., … (+3) |
| 1165 | [Community 1294](#c-1294) | 7 | 0.22 | get_meta_rl_audit_log(), Get or create the Meta-RL audit log singleton., ATOM-META-RL-006: Factory — create and record a MetaRLDecisionRecord     from a, Статистика по всем решениям, Анализ OAP drift — деградирует ли система глобально, … (+2) |
| 1166 | [Community 1298](#c-1298) | 7 | 0.22 | get_meta_rl_audit_log(), Get or create the Meta-RL audit log singleton., ATOM-META-RL-006: Factory — create and record a MetaRLDecisionRecord     from a, Статистика по всем решениям, Анализ OAP drift — деградирует ли система глобально, … (+2) |
| 1167 | [Community 1322](#c-1322) | 7 | 0.22 | get_meta_rl_audit_log(), Get or create the Meta-RL audit log singleton., ATOM-META-RL-006: Factory — create and record a MetaRLDecisionRecord     from a, Статистика по всем решениям, Анализ OAP drift — деградирует ли система глобально, … (+2) |
| 1168 | [Community 1088](#c-1088) | 7 | 0.21 | AdaptiveSlippageModel, trading/execution/twap.py — ATOM-STEP-10: TWAP Execution Strategy, TWAPConfig, TWAPExecutionReport, TWAPExecutor, … (+2) |
| 1169 | [Community 1122](#c-1122) | 7 | 0.21 | AdaptiveSlippageModel, trading/execution/twap.py — ATOM-STEP-10: TWAP Execution Strategy, TWAPConfig, TWAPExecutionReport, TWAPExecutor, … (+2) |
| 1170 | [Community 963](#c-963) | 7 | 0.20 | Backend, build_features(), FeatureBuilder, Build a single feature vector for node_id.         Uses TimescaleDB if backend=', Convert raw metrics dict into a feature vector, … (+3) |
| 1171 | [Community 986](#c-986) | 7 | 0.20 | Build a single feature vector for node_id.         Uses TimescaleDB if backend=', Convert raw metrics dict into a feature vector, using window_engine aggregations, Computes feature vectors from either TimescaleDB (primary) or Prometheus (fallba, Query TimescaleDB continuous aggregate for a node., … (+3) |
| 1172 | [Community 1098](#c-1098) | 7 | 0.20 | DAGChange, DAGFingerprint, Compute delta between current and previous fingerprint.          Returns list of, Delta between two DAG fingerprints., Diff current fp against another (or None)., … (+2) |
| 1173 | [Community 1207](#c-1207) | 7 | 0.20 | Map failure_type → RecoveryActionObj with target and parameters., Выполняемое действие восстановления с target и parameters., Apply recovery to engine's layer state. Returns result summary., RecoveryActionObj, Any, … (+2) |
| 1174 | [Community 596](#c-596) | 7 | 0.18 | get_meta_engine(), MetaQuestion, MetaQuestionBank, MetaQuestioningEngine, QuestionEvolution, … (+2) |
| 1175 | [Community 602](#c-602) | 7 | 0.18 | get_meta_engine(), MetaQuestion, MetaQuestionBank, MetaQuestioningEngine, QuestionEvolution, … (+2) |
| 1176 | [Community 617](#c-617) | 7 | 0.18 | get_meta_engine(), MetaQuestion, MetaQuestionBank, MetaQuestioningEngine, QuestionEvolution, … (+2) |
| 1177 | [Community 626](#c-626) | 7 | 0.18 | simulate_usage(), UsageAggregator, BillingEventStore, BillingEvent, BillingEventStore, … (+2) |
| 1178 | [Community 641](#c-641) | 7 | 0.18 | get_meta_engine(), MetaQuestion, MetaQuestionBank, MetaQuestioningEngine, QuestionEvolution, … (+2) |
| 1179 | [Community 843](#c-843) | 7 | 0.18 | Policy, PolicyEvaluator, PolicyTrial, Evaluates policy performance using cumulative regret.     regret(t) = U_best(t), Return empirical performance stats for a policy., … (+2) |
| 1180 | [Community 863](#c-863) | 7 | 0.18 | Policy, PolicyEvaluator, PolicyTrial, Apply policy weights to action score., Evaluates policy performance using cumulative regret.     regret(t) = U_best(t), … (+2) |
| 1181 | [Community 886](#c-886) | 7 | 0.18 | AuditLog, DecisionRecord, Восстановление из dict, Хранилище всех DecisionRecord с индексами для быстрого поиска, Воспроизвести конкретное решение по хешу состояния, … (+2) |
| 1182 | [Community 887](#c-887) | 7 | 0.18 | AuditLog, DecisionRecord, Восстановление из dict, Хранилище всех DecisionRecord с индексами для быстрого поиска, Воспроизвести конкретное решение по хешу состояния, … (+2) |
| 1183 | [Community 899](#c-899) | 7 | 0.18 | Predictor, Compute composite risk score from predictions., Decision recommendation based on risk., Path, Batch inference for multiple nodes., … (+2) |
| 1184 | [Community 905](#c-905) | 7 | 0.18 | AuditLog, DecisionRecord, Восстановление из dict, Хранилище всех DecisionRecord с индексами для быстрого поиска, Воспроизвести конкретное решение по хешу состояния, … (+2) |
| 1185 | [Community 1064](#c-1064) | 7 | 0.18 | get_reward_ema(), core/reward/ema.py — ATOM-REWARD-001: Reward EMA Engine  Exponential smoothing o, Per-key EMA for reward stabilization.      Key design:     - First call with a k, Update EMA for key. First call seeds with `value` (NOT 0).          Returns clam, Get current EMA. Returns 0.0 for unknown keys., … (+2) |
| 1186 | [Community 1082](#c-1082) | 7 | 0.18 | get_reward_ema(), core/reward/ema.py — ATOM-REWARD-001: Reward EMA Engine  Exponential smoothing o, Per-key EMA for reward stabilization.      Key design:     - First call with a k, Update EMA for key. First call seeds with `value` (NOT 0).          Returns clam, Get current EMA. Returns 0.0 for unknown keys., … (+2) |
| 1187 | [Community 1094](#c-1094) | 7 | 0.18 | get_reward_ema(), core/reward/ema.py — ATOM-REWARD-001: Reward EMA Engine  Exponential smoothing o, Per-key EMA for reward stabilization.      Key design:     - First call with a k, Update EMA for key. First call seeds with `value` (NOT 0).          Returns clam, Get current EMA. Returns 0.0 for unknown keys., … (+2) |
| 1188 | [Community 1115](#c-1115) | 7 | 0.18 | get_reward_ema(), core/reward/ema.py — ATOM-REWARD-001: Reward EMA Engine  Exponential smoothing o, Per-key EMA for reward stabilization.      Key design:     - First call with a k, Update EMA for key. First call seeds with `value` (NOT 0).          Returns clam, Get current EMA. Returns 0.0 for unknown keys., … (+2) |
| 1189 | [Community 627](#c-627) | 7 | 0.17 | CausalSemanticSpace, Euclidean distance between the most recent exec and replay vectors., Per-axis |exec - replay| magnitude for the most recent tick., Returns (axis_index, magnitude) of the dominant divergence axis.         Axes: 0, … (+3) |
| 1190 | [Community 879](#c-879) | 7 | 0.17 | OptimizationResult, OptimizerWeights, SystemOptimizer v6.5 — Global optimization objective for ATOMFederationOS.  Prob, Compute the global objective J for a given snapshot.          Parameters:, Adjust weights based on observed outcomes of recent actions.          If stabili, … (+2) |
| 1191 | [Community 1066](#c-1066) | 7 | 0.17 | High confidence → larger magnitude., 11.2: Reward direction correctness., BUY + positive price → positive reward., BUY + negative price → negative reward., SELL + positive price → positive reward (price drops)., … (+2) |
| 1192 | [Community 1084](#c-1084) | 7 | 0.17 | High confidence → larger magnitude., 11.2: Reward direction correctness., BUY + positive price → positive reward., BUY + negative price → negative reward., SELL + positive price → positive reward (price drops)., … (+2) |
| 1193 | [Community 1093](#c-1093) | 7 | 0.17 | GlobalTieBreaker, Deterministic tie-breaking for alignment layer.          Invariant: same inputs, Choose winner by score, with deterministic tie-break on id hash., Choose winner from N entries by (score, … (+5) |
| 1194 | [Community 1096](#c-1096) | 7 | 0.17 | High confidence → larger magnitude., 11.2: Reward direction correctness., BUY + positive price → positive reward., BUY + negative price → negative reward., SELL + positive price → positive reward (price drops)., … (+2) |
| 1195 | [Community 1111](#c-1111) | 7 | 0.17 | End-to-end tests against the live FastAPI inference server., POST /predict → risk_score must be float in [0.0, 1.0]., Missing field → 422 validation error., GET /health → 'status' must be 'healthy'., … (+3) |
| 1196 | [Community 1117](#c-1117) | 7 | 0.17 | High confidence → larger magnitude., 11.2: Reward direction correctness., BUY + positive price → positive reward., BUY + negative price → negative reward., SELL + positive price → positive reward (price drops)., … (+2) |
| 1197 | [Community 783](#c-783) | 7 | 0.15 | BaseStrategy, PerformanceRecord, strategies/base.py — ATOM-STEP-11: Strategy Base Classes, Regime, Signal, … (+2) |
| 1198 | [Community 802](#c-802) | 7 | 0.15 | BaseStrategy, PerformanceRecord, strategies/base.py — ATOM-STEP-11: Strategy Base Classes, Regime, Signal, … (+2) |
| 1199 | [Community 824](#c-824) | 7 | 0.15 | BaseStrategy, PerformanceRecord, strategies/base.py — ATOM-STEP-11: Strategy Base Classes, Regime, Signal, … (+2) |
| 1200 | [Community 288](#c-288) | 7 | 0.13 | Any, JobState, JobStatus, NodeState, NodeStatus, … (+2) |
| 1201 | [Community 299](#c-299) | 7 | 0.13 | Any, JobState, JobStatus, NodeState, NodeStatus, … (+2) |
| 1202 | [Community 593](#c-593) | 7 | 0.13 | PredictiveController, PredictiveTickResult, Extends ClosedLoopResilienceController with predictive capabilities.      The pr, Synchronous single tick., Extended tick result with predictive fields.          Adds to TickResult:, … (+3) |
| 1203 | [Community 694](#c-694) | 7 | 0.12 | mock_cluster_ctx(), Mock cluster context for unit testing without a live cluster., ClusterHealthGraph, NodeState, PeerHealth, … (+2) |
| 1204 | [Community 497](#c-497) | 7 | 0.11 | Any, Invoice, StripeCustomer, StripeIntegration, Subscription, … (+2) |
| 1205 | [Community 697](#c-697) | 7 | 0.11 | BlackRock-style "Data Room" — single source of truth for all data., MetricsStore, Any, In-process metrics for Data Room access.  Replace with prometheus_client in prod, Thread-safe singleton. Track resolver usage + quality., … (+3) |
| 1206 | [Community 242](#c-242) | 7 | 0.10 | Predicts runtime duration for a task based on plugin type and historical events., RuntimeEstimator, CostExplainabilityEngine, ROMA Cost Explainability Engine — Why this costs what it costs., main(), … (+2) |
| 1207 | [Community 640](#c-640) | 7 | 0.10 | EvaluationMetrics, MetricsConfig, evaluation_metrics.py — planning_observability layer Metrics for measuring plann, Snapshot of planning system health at a given tick., Composite planning health score (0..1).          Combines:           - plan_stab, … (+2) |
| 1208 | [Community 98](#c-98) | 7 | 0.04 | tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 tests), TestEvaluationResult, TestEvolutionEngine, TestMetaAgent, TestRewardCalculator, … (+2) |
| 1209 | [Community 1528](#c-1528) | 6 | 0.62 | slurm_ha_failover.sh script, acquire_lock(), is_primary_alive(), log(), main(), … (+1) |
| 1210 | [Community 1529](#c-1529) | 6 | 0.62 | slurm_ha_failover.sh script, acquire_lock(), is_primary_alive(), log(), main(), … (+1) |
| 1211 | [Community 1526](#c-1526) | 6 | 0.57 | err(), log(), ok(), require(), warn(), … (+1) |
| 1212 | [Community 1473](#c-1473) | 6 | 0.52 | get_houses(), get_panchang(), jd_from_datetime(), print_muhurtha(), datetime, … (+1) |
| 1213 | [Community 1487](#c-1487) | 6 | 0.52 | adversarial_analysis(), classify(), compute_violations(), detect_dynamic(), get_imports(), … (+1) |
| 1214 | [Community 1492](#c-1492) | 6 | 0.52 | err(), log(), ok(), step(), warn(), … (+1) |
| 1215 | [Community 1504](#c-1504) | 6 | 0.52 | get_houses(), get_panchang(), jd_from_datetime(), print_muhurtha(), datetime, … (+1) |
| 1216 | [Community 1527](#c-1527) | 6 | 0.52 | adversarial_analysis(), classify(), compute_violations(), detect_dynamic(), get_imports(), … (+1) |
| 1217 | [Community 1535](#c-1535) | 6 | 0.52 | get_houses(), get_panchang(), jd_from_datetime(), print_muhurtha(), datetime, … (+1) |
| 1218 | [Community 1549](#c-1549) | 6 | 0.52 | get_houses(), get_panchang(), jd_from_datetime(), print_muhurtha(), datetime, … (+1) |
| 1219 | [Community 1400](#c-1400) | 6 | 0.50 | command_exists(), info(), install_wg(), ok(), warn(), … (+1) |
| 1220 | [Community 1432](#c-1432) | 6 | 0.50 | command_exists(), info(), install_wg(), ok(), warn(), … (+1) |
| 1221 | [Community 1466](#c-1466) | 6 | 0.48 | _init_schema(), main(), _migrate(), db/__main__.py — Entry point for: python -m db.init  ATOM-DB-MIGRATION-002 Usage, _reset(), … (+1) |
| 1222 | [Community 1497](#c-1497) | 6 | 0.48 | _init_schema(), main(), _migrate(), db/__main__.py — Entry point for: python -m db.init  ATOM-DB-MIGRATION-002 Usage, _reset(), … (+1) |
| 1223 | [Community 1517](#c-1517) | 6 | 0.48 | _init_schema(), main(), _migrate(), db/__main__.py — Entry point for: python -m db.init  ATOM-DB-MIGRATION-002 Usage, _reset(), … (+1) |
| 1224 | [Community 1542](#c-1542) | 6 | 0.48 | _init_schema(), main(), _migrate(), db/__main__.py — Entry point for: python -m db.init  ATOM-DB-MIGRATION-002 Usage, _reset(), … (+1) |
| 1225 | [Community 1467](#c-1467) | 6 | 0.43 | get_sqlite_sessions(), main(), migrate_sessions(), Read all sessions from SQLite history.db., Migrate sessions to PostgreSQL via DecisionRecordRepository., … (+1) |
| 1226 | [Community 1475](#c-1475) | 6 | 0.43 | compare(), main(), В CI мы не можем поднять реальных агентов, поэтому эмулируем результат, иден, … (+3) |
| 1227 | [Community 1498](#c-1498) | 6 | 0.43 | get_sqlite_sessions(), main(), migrate_sessions(), Read all sessions from SQLite history.db., Migrate sessions to PostgreSQL via DecisionRecordRepository., … (+1) |
| 1228 | [Community 1506](#c-1506) | 6 | 0.43 | compare(), main(), В CI мы не можем поднять реальных агентов, поэтому эмулируем результат, иден, … (+3) |
| 1229 | [Community 1518](#c-1518) | 6 | 0.43 | get_sqlite_sessions(), main(), migrate_sessions(), Read all sessions from SQLite history.db., Migrate sessions to PostgreSQL via DecisionRecordRepository., … (+1) |
| 1230 | [Community 1543](#c-1543) | 6 | 0.43 | get_sqlite_sessions(), main(), migrate_sessions(), Read all sessions from SQLite history.db., Migrate sessions to PostgreSQL via DecisionRecordRepository., … (+1) |
| 1231 | [Community 1551](#c-1551) | 6 | 0.43 | compare(), main(), В CI мы не можем поднять реальных агентов, поэтому эмулируем результат, иден, … (+3) |
| 1232 | [Community 1558](#c-1558) | 6 | 0.43 | compare(), main(), В CI мы не можем поднять реальных агентов, поэтому эмулируем результат, иден, … (+3) |
| 1233 | [Community 1444](#c-1444) | 6 | 0.36 | build_council_result(), compute_weighted_signal(), core/council/council.py - AstroCouncil: Multi-Agent Voting System, resolve_conflict(), _signal_val(), … (+1) |
| 1234 | [Community 1474](#c-1474) | 6 | 0.33 | QueryType, AstroFin Sentinel v5 — Router Agent Routes user queries to appropriate specialis, Типы запросов, которые роутер должен распознавать., Роутит пользовательский запрос в нужный тип.      Правила:     - Если спрашивают, … (+2) |
| 1235 | [Community 1494](#c-1494) | 6 | 0.33 | Replay recorded failure incidents., replay_cmd(), sbs/cli_replay.py — sbs replay CLI command., Replay recorded failure incidents., run_replay(), … (+1) |
| 1236 | [Community 1505](#c-1505) | 6 | 0.33 | QueryType, AstroFin Sentinel v5 — Router Agent Routes user queries to appropriate specialis, Типы запросов, которые роутер должен распознавать., Роутит пользовательский запрос в нужный тип.      Правила:     - Если спрашивают, … (+2) |
| 1237 | [Community 1536](#c-1536) | 6 | 0.33 | QueryType, AstroFin Sentinel v5 — Router Agent Routes user queries to appropriate specialis, Типы запросов, которые роутер должен распознавать., Роутит пользовательский запрос в нужный тип.      Правила:     - Если спрашивают, … (+2) |
| 1238 | [Community 1550](#c-1550) | 6 | 0.33 | QueryType, AstroFin Sentinel v5 — Router Agent Routes user queries to appropriate specialis, Типы запросов, которые роутер должен распознавать., Роутит пользовательский запрос в нужный тип.      Правила:     - Если спрашивают, … (+2) |
| 1239 | [Community 1385](#c-1385) | 6 | 0.29 | Div, Toast, make_toast(), make_toast_container(), web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005), … (+1) |
| 1240 | [Community 1389](#c-1389) | 6 | 0.29 | Div, Toast, make_toast(), make_toast_container(), web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005), … (+1) |
| 1241 | [Community 1418](#c-1418) | 6 | 0.29 | Div, Toast, make_toast(), make_toast_container(), web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005), … (+1) |
| 1242 | [Community 1454](#c-1454) | 6 | 0.29 | Div, Toast, make_toast(), make_toast_container(), web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005), … (+1) |
| 1243 | [Community 1462](#c-1462) | 6 | 0.29 | Div, Toast, make_toast(), make_toast_container(), web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005), … (+1) |
| 1244 | [Community 1465](#c-1465) | 6 | 0.29 | AsyncClient, close_http_client(), get_http_client(), Shared async HTTP client for agent data fetching., Return a reusable httpx AsyncClient singleton., … (+2) |
| 1245 | [Community 1468](#c-1468) | 6 | 0.29 | Audit Log, Authentication Flow, Monitoring & Alerts, Rate Limiting, Safety Gate (execution layer), … (+1) |
| 1246 | [Community 1469](#c-1469) | 6 | 0.29 | Agent Instruction Template — Эталон для всех агентов, 🤖 {AGENT_NAME}, Запреты, Обязанности, Пример, … (+1) |
| 1247 | [Community 1470](#c-1470) | 6 | 0.29 | Core Principle, Corrective Waves (3 waves), Elliott Wave Theory, Fibonacci Ratios, Impulse Waves (5 waves), … (+1) |
| 1248 | [Community 1471](#c-1471) | 6 | 0.29 | 1. **Graph-of-Agents (GoA) — масштабируемый graph-based фреймворк для мультиагентной коллаборации LLM**, 2. **Agent Q-Mix — RL-подход к динамическому выбору топологии коммуникации агентов**, 3. **ComposioHQ/agent-orchestrator — оркестратор параллельных AI-агентов для автоматизации CI/CD и code review**, Multi-Agent AI Daily Digest — 2026-05-09, Источники, … (+1) |
| 1249 | [Community 1472](#c-1472) | 6 | 0.29 | **1. Google ADK Python v2.0.0 — Production-grade Multi-Agent Workflow Engine**, **2. Claude Code v2.1.147 — Workflow Tool для Deterministic Multi-Agent Orchestration**, **3. Swarms Framework — Complete OS для Multi-Agent Systems**, Multi-Agent AI Daily Digest, Источники мониторинга, … (+1) |
| 1250 | [Community 1479](#c-1479) | 6 | 0.29 | После выбора агентов через _select_for_flow счётчик должен инкрементироваться., При получении сигнала от агента счётчик распределения должен инкрементироваться., После обновления belief параметры Thompson должны отражаться в Gauge., test_agent_selection_increments_counter(), test_signal_distribution_increments(), … (+1) |
| 1251 | [Community 1482](#c-1482) | 6 | 0.29 | test_agent_selection_increments_counter(), test_signal_distribution_increments(), test_thompson_params_gauge_updated(), При получении сигнала от агента счётчик распределения должен инкрементироваться., После обновления belief параметры Thompson должны отражаться в Gauge., … (+1) |
| 1252 | [Community 1496](#c-1496) | 6 | 0.29 | AsyncClient, close_http_client(), get_http_client(), Shared async HTTP client for agent data fetching., Return a reusable httpx AsyncClient singleton., … (+2) |
| 1253 | [Community 1499](#c-1499) | 6 | 0.29 | Audit Log, Authentication Flow, Monitoring & Alerts, Rate Limiting, Safety Gate (execution layer), … (+1) |
| 1254 | [Community 1500](#c-1500) | 6 | 0.29 | Agent Instruction Template — Эталон для всех агентов, 🤖 {AGENT_NAME}, Запреты, Обязанности, Пример, … (+1) |
| 1255 | [Community 1501](#c-1501) | 6 | 0.29 | Core Principle, Corrective Waves (3 waves), Elliott Wave Theory, Fibonacci Ratios, Impulse Waves (5 waves), … (+1) |
| 1256 | [Community 1502](#c-1502) | 6 | 0.29 | 1. **Graph-of-Agents (GoA) — масштабируемый graph-based фреймворк для мультиагентной коллаборации LLM**, 2. **Agent Q-Mix — RL-подход к динамическому выбору топологии коммуникации агентов**, 3. **ComposioHQ/agent-orchestrator — оркестратор параллельных AI-агентов для автоматизации CI/CD и code review**, Multi-Agent AI Daily Digest — 2026-05-09, Источники, … (+1) |
| 1257 | [Community 1503](#c-1503) | 6 | 0.29 | **1. Google ADK Python v2.0.0 — Production-grade Multi-Agent Workflow Engine**, **2. Claude Code v2.1.147 — Workflow Tool для Deterministic Multi-Agent Orchestration**, **3. Swarms Framework — Complete OS для Multi-Agent Systems**, Multi-Agent AI Daily Digest, Источники мониторинга, … (+1) |
| 1258 | [Community 1510](#c-1510) | 6 | 0.29 | После выбора агентов через _select_for_flow счётчик должен инкрементироваться., При получении сигнала от агента счётчик распределения должен инкрементироваться., После обновления belief параметры Thompson должны отражаться в Gauge., test_agent_selection_increments_counter(), test_signal_distribution_increments(), … (+1) |
| 1259 | [Community 1516](#c-1516) | 6 | 0.29 | AsyncClient, close_http_client(), get_http_client(), Shared async HTTP client for agent data fetching., Return a reusable httpx AsyncClient singleton., … (+2) |
| 1260 | [Community 1519](#c-1519) | 6 | 0.29 | Audit Log, Authentication Flow, Monitoring & Alerts, Rate Limiting, Safety Gate (execution layer), … (+1) |
| 1261 | [Community 1523](#c-1523) | 6 | 0.29 | Branch Protection -- AstroFin Sentinel V5, How to Add an Exemption, How to Configure, Required Settings, Required Status Checks (must pass before merge), … (+1) |
| 1262 | [Community 1530](#c-1530) | 6 | 0.29 | Agent Instruction Template — Эталон для всех агентов, 🤖 {AGENT_NAME}, Запреты, Обязанности, Пример, … (+1) |
| 1263 | [Community 1531](#c-1531) | 6 | 0.29 | Core Principle, Corrective Waves (3 waves), Elliott Wave Theory, Fibonacci Ratios, Impulse Waves (5 waves), … (+1) |
| 1264 | [Community 1532](#c-1532) | 6 | 0.29 | 1. **Graph-of-Agents (GoA) — масштабируемый graph-based фреймворк для мультиагентной коллаборации LLM**, 2. **Agent Q-Mix — RL-подход к динамическому выбору топологии коммуникации агентов**, 3. **ComposioHQ/agent-orchestrator — оркестратор параллельных AI-агентов для автоматизации CI/CD и code review**, Multi-Agent AI Daily Digest — 2026-05-09, Источники, … (+1) |
| 1265 | [Community 1533](#c-1533) | 6 | 0.29 | **1. Google ADK Python v2.0.0 — Production-grade Multi-Agent Workflow Engine**, **2. Claude Code v2.1.147 — Workflow Tool для Deterministic Multi-Agent Orchestration**, **3. Swarms Framework — Complete OS для Multi-Agent Systems**, Multi-Agent AI Daily Digest, Источники мониторинга, … (+1) |
| 1266 | [Community 1538](#c-1538) | 6 | 0.29 | PR1 — CompromiseAgent (preflight snapshot), Snapshot, Грабли / нюансы, Изменённые / новые файлы, Контракт сигналов, … (+1) |
| 1267 | [Community 1540](#c-1540) | 6 | 0.29 | AsyncClient, close_http_client(), get_http_client(), Shared async HTTP client for agent data fetching., Return a reusable httpx AsyncClient singleton., … (+2) |
| 1268 | [Community 1544](#c-1544) | 6 | 0.29 | Audit Log, Authentication Flow, Monitoring & Alerts, Rate Limiting, Safety Gate (execution layer), … (+1) |
| 1269 | [Community 1545](#c-1545) | 6 | 0.29 | Agent Instruction Template — Эталон для всех агентов, 🤖 {AGENT_NAME}, Запреты, Обязанности, Пример, … (+1) |
| 1270 | [Community 1546](#c-1546) | 6 | 0.29 | Core Principle, Corrective Waves (3 waves), Elliott Wave Theory, Fibonacci Ratios, Impulse Waves (5 waves), … (+1) |
| 1271 | [Community 1547](#c-1547) | 6 | 0.29 | 1. **Graph-of-Agents (GoA) — масштабируемый graph-based фреймворк для мультиагентной коллаборации LLM**, 2. **Agent Q-Mix — RL-подход к динамическому выбору топологии коммуникации агентов**, 3. **ComposioHQ/agent-orchestrator — оркестратор параллельных AI-агентов для автоматизации CI/CD и code review**, Multi-Agent AI Daily Digest — 2026-05-09, Источники, … (+1) |
| 1272 | [Community 1548](#c-1548) | 6 | 0.29 | **1. Google ADK Python v2.0.0 — Production-grade Multi-Agent Workflow Engine**, **2. Claude Code v2.1.147 — Workflow Tool для Deterministic Multi-Agent Orchestration**, **3. Swarms Framework — Complete OS для Multi-Agent Systems**, Multi-Agent AI Daily Digest, Источники мониторинга, … (+1) |
| 1273 | [Community 1555](#c-1555) | 6 | 0.29 | После выбора агентов через _select_for_flow счётчик должен инкрементироваться., При получении сигнала от агента счётчик распределения должен инкрементироваться., После обновления belief параметры Thompson должны отражаться в Gauge., test_agent_selection_increments_counter(), test_signal_distribution_increments(), … (+1) |
| 1274 | [Community 1557](#c-1557) | 6 | 0.29 | Architecture Freeze, Core Platform, Enterprise, Product, ROMA Changelog, … (+1) |
| 1275 | [Community 1563](#c-1563) | 6 | 0.29 | После выбора агентов через _select_for_flow счётчик должен инкрементироваться., При получении сигнала от агента счётчик распределения должен инкрементироваться., После обновления belief параметры Thompson должны отражаться в Gauge., test_agent_selection_increments_counter(), test_signal_distribution_increments(), … (+1) |
| 1276 | [Community 1077](#c-1077) | 6 | 0.26 | NodeWeightsSnapshot, ConsensusDominationAlert, skew_detector.py — v9.6 Trust Skew + Collapse Detector  Monitors weight distribu, TrustCollapseAlert, TrustSkewDetector, … (+1) |
| 1277 | [Community 965](#c-965) | 6 | 0.25 | DataFrame, LoadXGBoost, ndarray, Series, Train separate regressors for queue_depth, … (+3) |
| 1278 | [Community 989](#c-989) | 6 | 0.25 | DataFrame, LoadXGBoost, ndarray, Series, Train separate regressors for queue_depth, … (+3) |
| 1279 | [Community 1442](#c-1442) | 6 | 0.25 | DeterministicScheduler v1.0 — ATOM-META-RL-014  Fully deterministic task schedul, Deterministic scheduling strategies — no random., Verify scheduling is deterministic: same tick → same result across runs., Result of one scheduling decision., ScheduleResult, … (+1) |
| 1280 | [Community 1457](#c-1457) | 6 | 0.25 | Без заголовка X-API-Key защищённый эндпоинт возвращает 401., С неверным ключом возвращает 403, если ключ настроен., С верным ключом аутентификация проходит (не 401/403)., test_protected_endpoint_accepts_valid_key(), … (+2) |
| 1281 | [Community 1062](#c-1062) | 6 | 0.24 | BufferEntry, get_default_buffer(), amre/replay_buffer.py — Replay Buffer for trajectory learning, ReplayBuffer, _select_best_trajectory(), … (+1) |
| 1282 | [Community 1073](#c-1073) | 6 | 0.24 | MetaLearner, PolicyRecommendation, PolicyTrial, Meta-learning over policy performance.     Learns which policy to use given work, Return ranked policy recommendations given current context., … (+1) |
| 1283 | [Community 1076](#c-1076) | 6 | 0.24 | Any, DAGFingerprintBridge, Bridge: connects DAGFingerprint to InvariantContract kernel.      Provides check, Compute fingerprint; store as .fp., Check whether DAG fingerprint in state is valid/stable.         Used as invarian, … (+1) |
| 1284 | [Community 1079](#c-1079) | 6 | 0.24 | Ack, Any, AtomMessage, AtomServicer, gRPC servicer that bridges real network → local runtime receive queue.     SBS e, … (+1) |
| 1285 | [Community 1110](#c-1110) | 6 | 0.24 | MetaLearner, PolicyRecommendation, PolicyTrial, Meta-learning over policy performance.     Learns which policy to use given work, Return ranked policy recommendations given current context., … (+1) |
| 1286 | [Community 839](#c-839) | 6 | 0.22 | Any, Constraint, ConstraintGroup, ConstraintType, PolicyBlock, … (+1) |
| 1287 | [Community 901](#c-901) | 6 | 0.21 | Incident, IncidentManager, Severity, Route to appropriate response by severity., Auto-classifies incidents by severity.     Routes to appropriate response (rollb, … (+1) |
| 1288 | [Community 927](#c-927) | 6 | 0.21 | Incident, IncidentManager, Severity, Route to appropriate response by severity., Auto-classifies incidents by severity.     Routes to appropriate response (rollb, … (+1) |
| 1289 | [Community 1013](#c-1013) | 6 | 0.21 | _MetaRLAuditLog, MetaRLDecisionRecord, ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations., Separate audit log for Meta-RL strategy discovery records.     Decoupled from KA, Add a MetaRLDecisionRecord to the log., … (+1) |
| 1290 | [Community 1014](#c-1014) | 6 | 0.21 | _MetaRLAuditLog, MetaRLDecisionRecord, ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations., Separate audit log for Meta-RL strategy discovery records.     Decoupled from KA, Add a MetaRLDecisionRecord to the log., … (+1) |
| 1291 | [Community 1030](#c-1030) | 6 | 0.21 | _MetaRLAuditLog, MetaRLDecisionRecord, ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations., Separate audit log for Meta-RL strategy discovery records.     Decoupled from KA, Add a MetaRLDecisionRecord to the log., … (+1) |
| 1292 | [Community 842](#c-842) | 6 | 0.20 | Any, Path, ModelRegistry, Load model artifact from registry., Stable hash of model config + metrics for identity., … (+1) |
| 1293 | [Community 862](#c-862) | 6 | 0.20 | Any, Path, ModelRegistry, Load model artifact from registry., Stable hash of model config + metrics for identity., … (+1) |
| 1294 | [Community 920](#c-920) | 6 | 0.20 | CausalDAG, Check if two DAGs are structurally identical.         Returns (is_identical, rea, I2: Causal DAG from execution must be identical to causal DAG from replay., Lightweight causal ancestry graph for events., … (+2) |
| 1295 | [Community 1099](#c-1099) | 6 | 0.20 | IncrementalNodeHash, Compute content_hash and full_hash from content + parents., Layer = max(parent_layers) + 1; roots get layer=0., Per-node hash incorporating parent hashes.      hash = H(         content_hash, Tests for DAG incremental fingerprint — v8.5, … (+1) |
| 1296 | [Community 1120](#c-1120) | 6 | 0.20 | KARLState, meta_rl/meta_agent.py -- ATOM-META-RL-005/009: Bidirectional KARL + Cross-sessio, Bounded KARL state with automatic memory limits., Add Q-value with automatic cleanup (FIFO eviction)., Add chromosome with automatic truncation., … (+1) |
| 1297 | [Community 1205](#c-1205) | 6 | 0.20 | trading/execution/slippage.py — ATOM-STEP-10: Slippage Models, Fixed-percent slippage model — no market intelligence.      slippage_bps is cons, Calculate slippage for a trade.          Args:             side: "buy" or "sell", Adaptive slippage calculation.          Args:             side: "buy" or "sell", SlippageModel, … (+1) |
| 1298 | [Community 1211](#c-1211) | 6 | 0.20 | Astro reward component., Abhijit Muhurta should boost reward., Rahu Kaal should penalize reward., EXTREME regime should penalize reward., Astro reward always in [-1, … (+2) |
| 1299 | [Community 1235](#c-1235) | 6 | 0.20 | Astro reward component., Abhijit Muhurta should boost reward., Rahu Kaal should penalize reward., EXTREME regime should penalize reward., Astro reward always in [-1, … (+2) |
| 1300 | [Community 1246](#c-1246) | 6 | 0.20 | Persist full execution trace. MUST return trace_id (str)., Retrieve full trace by ID. MUST return dict or None., Query traces by filter. MUST return list[dict]., Append or patch trace data. MUST return None., ENFORCED contract for all TraceRecorder implementations., … (+1) |
| 1301 | [Community 1247](#c-1247) | 6 | 0.20 | Astro reward component., Abhijit Muhurta should boost reward., Rahu Kaal should penalize reward., EXTREME regime should penalize reward., Astro reward always in [-1, … (+2) |
| 1302 | [Community 1260](#c-1260) | 6 | 0.20 | Tests for MCP Adapter, Test mcp-recommended CLI command., Test mcp-search CLI command., Test CLI command execution., Test list-agents CLI command., … (+1) |
| 1303 | [Community 1264](#c-1264) | 6 | 0.20 | Weights within ±0.01 of 1.0 must NOT warn., RewardConfig invariants and warning behaviour., Vanilla RewardConfig() must have weights summing to 1.0 exactly.          Withou, Constructing RewardConfig() must not warn., Off-sum weights must warn (UserWarning) and renormalise., … (+1) |
| 1304 | [Community 1270](#c-1270) | 6 | 0.20 | Astro reward component., Abhijit Muhurta should boost reward., Rahu Kaal should penalize reward., EXTREME regime should penalize reward., Astro reward always in [-1, … (+2) |
| 1305 | [Community 1272](#c-1272) | 6 | 0.20 | Tests for MCP Adapter, Test mcp-recommended CLI command., Test mcp-search CLI command., Test CLI command execution., Test list-agents CLI command., … (+1) |
| 1306 | [Community 379](#c-379) | 6 | 0.19 | Job, JobEventHooks, JobState, TelemetryJobEngine, Write event to telemetry log (append-only, … (+2) |
| 1307 | [Community 391](#c-391) | 6 | 0.19 | Job, JobEventHooks, JobState, TelemetryJobEngine, Write event to telemetry log (append-only, … (+2) |
| 1308 | [Community 969](#c-969) | 6 | 0.18 | Any, DecisionRecord, decision_memory.py ~~~~~~~~~~~~~~~~~~~ Stores past decisions paired with their o, Find k decisions with payloads most similar to `payload`.         Similarity = f, Record a decision and optionally its outcome. Returns decision_id., … (+2) |
| 1309 | [Community 1134](#c-1134) | 6 | 0.18 | EMA продолжает работать после увеличения окна., EMA продолжает работать после уменьшения окна., Alpha пересчитывается при изменении window_size., Счётчик увеличивается при каждом add(), независимо от window changes., … (+2) |
| 1310 | [Community 1160](#c-1160) | 6 | 0.18 | EMA продолжает работать после увеличения окна., EMA продолжает работать после уменьшения окна., Alpha пересчитывается при изменении window_size., Счётчик увеличивается при каждом add(), независимо от window changes., … (+2) |
| 1311 | [Community 1188](#c-1188) | 6 | 0.18 | Get stable ID for registered pod., r'''     Stable replica identity across pod restarts.      Guarantees:       - S, r'''         Get stable identity for pod.          stable_id = hash(pod_uid + cl, Register a pod's stable identity., Verify pod's stable identity hasn't changed., … (+1) |
| 1312 | [Community 1193](#c-1193) | 6 | 0.18 | EMA продолжает работать после увеличения окна., EMA продолжает работать после уменьшения окна., Alpha пересчитывается при изменении window_size., Счётчик увеличивается при каждом add(), независимо от window changes., … (+2) |
| 1313 | [Community 632](#c-632) | 6 | 0.17 | EventLog, Any, AmneziaWGManager, TunnelEvent, Bring up tunnel. Idempotent. Invariant: write-side only., … (+1) |
| 1314 | [Community 844](#c-844) | 6 | 0.17 | Any, CompiledConstraint, ConstraintCompiler, ConstraintRegistry, Compiles DSL constraints into executable Python functions.          DSL examples, … (+1) |
| 1315 | [Community 855](#c-855) | 6 | 0.17 | Runtime registry of active compiled constraints.     Validates decisions against, Compiles DSL constraints into executable Python functions.      DSL examples:, Any, CompiledConstraint, ConstraintCompiler, … (+1) |
| 1316 | [Community 1071](#c-1071) | 6 | 0.17 | LabeledExample, MLBatch, A batch of labeled examples for training/validation., Export a split to CSV., A supervised learning example: features → label., … (+1) |
| 1317 | [Community 512](#c-512) | 6 | 0.15 | AssetPosition, trading/risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 ===========================, Adjust raw PnL by volatility regime and drawdown.          This is the core post, RiskConfigV2, RiskEngineV2, … (+1) |
| 1318 | [Community 524](#c-524) | 6 | 0.15 | AssetPosition, trading/risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 ===========================, Adjust raw PnL by volatility regime and drawdown.          This is the core post, RiskConfigV2, RiskEngineV2, … (+1) |
| 1319 | [Community 531](#c-531) | 6 | 0.15 | AssetPosition, trading/risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 ===========================, Adjust raw PnL by volatility regime and drawdown.          This is the core post, RiskConfigV2, RiskEngineV2, … (+1) |
| 1320 | [Community 809](#c-809) | 6 | 0.15 | Event, GatewayDFA, GatewayState, Deterministic finite automaton for ExecutionGateway., LTL: G(Exec -> NonceLocked U Act). Forward-only DFA: holds vacuously., … (+1) |
| 1321 | [Community 882](#c-882) | 6 | 0.12 | Integration tests for the full gateway stack., ACME tenant accepts a valid-length API key (>= 16 chars)., Free tier has require_api_key=False, so no key = OK., ACME tenant requires API key — no key = 401., … (+2) |
| 1322 | [Community 422](#c-422) | 6 | 0.11 | ClusterLogger, LogEntry, LogLevel, MetricsCollector, NodeMetrics, … (+1) |
| 1323 | [Community 728](#c-728) | 6 | 0.11 | PATCH 3: Enriched projection with node_graph_resolution and execution_order., PATCH 1: DAGValidator finds graph errors., PATCH 2: Idempotent execution — second call returns cached trace_id., test_patch1_dag_validator(), test_patch2_idempotent_engine(), … (+1) |
| 1324 | [Community 729](#c-729) | 6 | 0.11 | PATCH 3: Enriched projection with node_graph_resolution and execution_order., PATCH 1: DAGValidator finds graph errors., PATCH 2: Idempotent execution — second call returns cached trace_id., test_patch1_dag_validator(), test_patch2_idempotent_engine(), … (+1) |
| 1325 | [Community 131](#c-131) | 6 | 0.05 | tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 tests), TestEvaluationResult, TestEvolutionEngine, TestMetaAgent, TestRewardCalculator, … (+1) |
| 1326 | [Community 1569](#c-1569) | 5 | 0.60 | format_code_black(), is_valid_python(), normalize_code(), safe_write_code_file(), write_code_file() |
| 1327 | [Community 1602](#c-1602) | 5 | 0.60 | Path, EntryInfo, GateInfo, run(), safe_rel() |
| 1328 | [Community 1605](#c-1605) | 5 | 0.60 | format_code_black(), is_valid_python(), normalize_code(), safe_write_code_file(), write_code_file() |
| 1329 | [Community 1623](#c-1623) | 5 | 0.60 | format_code_black(), is_valid_python(), normalize_code(), safe_write_code_file(), write_code_file() |
| 1330 | [Community 1659](#c-1659) | 5 | 0.60 | format_code_black(), is_valid_python(), normalize_code(), safe_write_code_file(), write_code_file() |
| 1331 | [Community 1559](#c-1559) | 5 | 0.52 | check_cosign(), cosign_keyless_sign_attestation(), generate_attestation_bundle(), h(), verify_from_rekor() |
| 1332 | [Community 1566](#c-1566) | 5 | 0.47 | ensemble_diversity_score(), amre/ensemble_selection.py — Ensemble diversity selection, select_ensemble(), select_ensemble_by_confidence(), Any |
| 1333 | [Community 1568](#c-1568) | 5 | 0.47 | ensemble_diversity_score(), amre/ensemble_selection.py — Ensemble diversity selection, select_ensemble(), select_ensemble_by_confidence(), Any |
| 1334 | [Community 1594](#c-1594) | 5 | 0.47 | build_windows(), get_window_data(), TimeWindow, For a given metric + window, return aggregates.     In production: query Prometh, … (+1) |
| 1335 | [Community 1595](#c-1595) | 5 | 0.47 | compute_tag_stats(), main(), run_scenario(), Import and run a scenario by name., Aggregate counts per Zettelkasten tag across all results. |
| 1336 | [Community 1604](#c-1604) | 5 | 0.47 | ensemble_diversity_score(), amre/ensemble_selection.py — Ensemble diversity selection, select_ensemble(), select_ensemble_by_confidence(), Any |
| 1337 | [Community 1632](#c-1632) | 5 | 0.47 | For a given metric + window, return aggregates.     In production: query Prometh, Build all window aggregates for all metrics.     Returns: {metric_name: {window_, build_windows(), get_window_data(), … (+1) |
| 1338 | [Community 1637](#c-1637) | 5 | 0.47 | compute_tag_stats(), main(), run_scenario(), Import and run a scenario by name., Aggregate counts per Zettelkasten tag across all results. |
| 1339 | [Community 1658](#c-1658) | 5 | 0.47 | ensemble_diversity_score(), amre/ensemble_selection.py — Ensemble diversity selection, select_ensemble(), select_ensemble_by_confidence(), Any |
| 1340 | [Community 1480](#c-1480) | 5 | 0.43 | MockAgent, Concrete agent for testing., test_build_prompt_handles_ollama_unavailable(), test_build_prompt_includes_rag_results(), test_build_prompt_no_rag_when_disabled() |
| 1341 | [Community 1483](#c-1483) | 5 | 0.43 | MockAgent, test_build_prompt_handles_ollama_unavailable(), test_build_prompt_includes_rag_results(), test_build_prompt_no_rag_when_disabled(), Concrete agent for testing. |
| 1342 | [Community 1511](#c-1511) | 5 | 0.43 | MockAgent, Concrete agent for testing., test_build_prompt_handles_ollama_unavailable(), test_build_prompt_includes_rag_results(), test_build_prompt_no_rag_when_disabled() |
| 1343 | [Community 1556](#c-1556) | 5 | 0.43 | MockAgent, Concrete agent for testing., test_build_prompt_handles_ollama_unavailable(), test_build_prompt_includes_rag_results(), test_build_prompt_no_rag_when_disabled() |
| 1344 | [Community 1564](#c-1564) | 5 | 0.43 | MockAgent, Concrete agent for testing., test_build_prompt_handles_ollama_unavailable(), test_build_prompt_includes_rag_results(), test_build_prompt_no_rag_when_disabled() |
| 1345 | [Community 1599](#c-1599) | 5 | 0.40 | DataFrame, Split dataset respecting temporal order (no future-leaking).     Each node's tim, stratify_by_label(), time_aware_split(), Ensure label distribution is not too imbalanced.     If positive class < min_pos |
| 1346 | [Community 1626](#c-1626) | 5 | 0.40 | Ensure label distribution is not too imbalanced.     If positive class < min_pos, DataFrame, Split dataset respecting temporal order (no future-leaking).     Each node's tim, stratify_by_label(), time_aware_split() |
| 1347 | [Community 1641](#c-1641) | 5 | 0.40 | DataFrame, add_rolling_features(), build_advanced_features(), Adds sliding-window features, lag features, … (+2) |
| 1348 | [Community 1730](#c-1730) | 5 | 0.40 | 7.1 Current State, 7.2 Collapsed Architecture, 7.3 ExecutionToken — Immutable Capability, 7.4 Before/After Enforcement Comparison, 7. EXECUTION BOUNDARY COLLAPSE |
| 1349 | [Community 1731](#c-1731) | 5 | 0.40 | 9. DETERMINISM FIX IMPLEMENTATION ORDER, Phase 1: Core Deterministic Primitives (P0), Phase 2: Ledger Linearization (P0), Phase 3: Execution Boundary Collapse (P1), Phase 4: Async Determinism (P1) |
| 1350 | [Community 1735](#c-1735) | 5 | 0.40 | 2 SQLite DBs (post-consolidation 2026-03-26), 3. Databases, Issues, Schema: `backtest_runs` (authoritative), Schema: `sessions` |
| 1351 | [Community 1736](#c-1736) | 5 | 0.40 | 8. Belief Tracker (Bayesian), API, File: `core/belief.py` + `core/belief.db`, Model, Success Criteria |
| 1352 | [Community 1314](#c-1314) | 5 | 0.39 | Any, ContractViolation, DAGValidator, EventType, Validates DAG, … (+2) |
| 1353 | [Community 1397](#c-1397) | 5 | 0.36 | build_metrics(), get_slurm_nodes(), get_slurm_queue(), Handler, Build Prometheus text metrics. |
| 1354 | [Community 1430](#c-1430) | 5 | 0.36 | build_metrics(), get_slurm_nodes(), get_slurm_queue(), Handler, Build Prometheus text metrics. |
| 1355 | [Community 1229](#c-1229) | 5 | 0.33 | Any, ExecutionSandbox, SandboxResult, SandboxViolation, ViolationType |
| 1356 | [Community 1291](#c-1291) | 5 | 0.33 | Generates worst-case scenarios to stress-test policy robustness., Apply adversarial conditions to simulated cluster state., Run optimizer through adversarial scenarios, measure brittleness., AdversarialScenario, … (+1) |
| 1357 | [Community 1292](#c-1292) | 5 | 0.33 | Generates worst-case scenarios to stress-test policy robustness., Apply adversarial conditions to simulated cluster state., Run optimizer through adversarial scenarios, measure brittleness., AdversarialScenario, … (+1) |
| 1358 | [Community 1295](#c-1295) | 5 | 0.33 | Submit job to selected partition via slurm wrapper., schedule(), ScheduleRequest, ScheduleResponse, submit() |
| 1359 | [Community 1296](#c-1296) | 5 | 0.33 | Submit job to selected partition via slurm wrapper., schedule(), ScheduleRequest, ScheduleResponse, submit() |
| 1360 | [Community 1315](#c-1315) | 5 | 0.33 | DataFrame, DatasetBuilder, datetime, Query TimescaleDB for failure/load labels within horizon window., Build feature dataset with failure labels for ML training.          Args: |
| 1361 | [Community 1337](#c-1337) | 5 | 0.33 | Query TimescaleDB for failure/load labels within horizon window., Build feature dataset with failure labels for ML training.          Args:, DataFrame, DatasetBuilder, datetime |
| 1362 | [Community 1571](#c-1571) | 5 | 0.33 | ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, Components, Dependencies, Expected, Why P1? |
| 1363 | [Community 1572](#c-1572) | 5 | 0.33 | ATOM-DEDUP-001: Дедупликация агентов, Execution, Impact, Problem, Задача |
| 1364 | [Community 1573](#c-1573) | 5 | 0.33 | ATOM-GITAGENT-003: Phase 3 GitAgent, Components, Dependencies, Reason, When |
| 1365 | [Community 1574](#c-1574) | 5 | 0.33 | 1. **Pressure Field Coordination** (arXiv:2601.08129), 2. **CrewAI v2.3 — Enhanced Multi-Agent Orchestration**, 3. **AutoGen 0.4 — Universal Agent Communication Protocol**, 🌐 Multi-Agent AI Daily Brief — 2026-03-29, Ключевые находки |
| 1366 | [Community 1575](#c-1575) | 5 | 0.33 | 1. Microsoft Conductor — open-source YAML-оркестратор multi-agent систем, 2. REDEREF — training-free маршрутизация для multi-agent LLM систем, 3. CoalT — game theory coalition formation для multi-agent LLM, Multi-Agent AI Daily Digest, Топ-3 за сегодня |
| 1367 | [Community 1576](#c-1576) | 5 | 0.33 | 1. Microsoft Agent Framework — Handoff pattern + Foundry Hosted Agents (BUILD 2026), 2. Cloudflare Agents 0.14.0 — durable multi-agent orchestration + Skills engine, 3. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems (ACL ARR 2026), Multi-Agent AI Daily — 2026-06-08, Сводка по применению в AstroFinSentinelV5 |
| 1368 | [Community 1577](#c-1577) | 5 | 0.33 | 1. Microsoft Agent Framework Python 1.8.0 — стабилизация Magentic multi-agent оркестрации, 2. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems, 3. Hermes Agent v0.16.0 (Surface Release) — Kanban multi-agent swarm, 🤖 Multi-Agent AI Daily — 2026-06-09, Прочие заметные релизы (для контекста) |
| 1369 | [Community 1578](#c-1578) | 5 | 0.33 | 1. Microsoft Agent Framework 1.8.0 — McpSkills, MCP long-running tasks (SEP-2663) и compaction stability, 2. POISE — автономное открытие новых LLM-RL алгоритмов агентами-учёными, 3. dySCo / Pi-Taskflow / Open-Multi-Agent — typed DAG и sparse-координация для verifiable мульти-агентов, 🤖 Multi-Agent AI Daily — 2026-06-10, … (+1) |
| 1370 | [Community 1579](#c-1579) | 5 | 0.33 | 1. Arbor — Microsoft Research: мультиагентный фреймворк с Hypothesis-Tree Refinement, 2. MARS — Multi-Agent Review System: дебаты с -50% токенов, 3. DeLM — Decentralized Language Models: параллельные solver-ветки с общим контекстом, 🤖 Multi-Agent AI Daily — 2026-06-13, Краткий footer |
| 1371 | [Community 1580](#c-1580) | 5 | 0.33 | 1. ECC 2.0.0 — The Agent Harness Operating System, 2. MARS — Multi-Agent Review System (эффективный multi-agent debate), 3. MASFactory — multi-agent workflow из natural language, 🤖 Multi-Agent AI Daily — 2026-06-14, Дополнительные находки (для контекста, … (+1) |
| 1372 | [Community 1582](#c-1582) | 5 | 0.33 | Smoke test for Data Room API blueprint., Проверяем, что Blueprint зарегистрирован и имеет правильный префикс., При запросе /data-room/conflicts должен возвращаться JSON., test_blueprint_exists(), … (+1) |
| 1373 | [Community 1584](#c-1584) | 5 | 0.33 | _alpha_badge(), explorer_tab(), web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)  Enha, Color-coded alpha decay / out-of-sample health badge., Div |
| 1374 | [Community 1587](#c-1587) | 5 | 0.33 | cleanup(), test_agent_can_create_add_function(), Бенчмарк для Ralph Loop – минимальная задача, которую агент должен решить., Удаляем временные файлы до и после теста., … (+2) |
| 1375 | [Community 1589](#c-1589) | 5 | 0.33 | Phase 1 cleanup validation tests., test_core_auth_importable(), Проверяем, что старые модули больше не импортируются., Проверяем, … (+2) |
| 1376 | [Community 1590](#c-1590) | 5 | 0.33 | _alpha_badge(), explorer_tab(), web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)  Enha, Color-coded alpha decay / out-of-sample health badge., Div |
| 1377 | [Community 1601](#c-1601) | 5 | 0.33 | Bug Fixes, New CLI Commands, Phase 1-4 All Complete ✅, v0.4.0 — Phase 4 Complete: ALL PHASES DONE, What's New |
| 1378 | [Community 1606](#c-1606) | 5 | 0.33 | ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, Components, Dependencies, Expected, Why P1? |
| 1379 | [Community 1607](#c-1607) | 5 | 0.33 | ATOM-DEDUP-001: Дедупликация агентов, Execution, Impact, Problem, Задача |
| 1380 | [Community 1608](#c-1608) | 5 | 0.33 | ATOM-GITAGENT-003: Phase 3 GitAgent, Components, Dependencies, Reason, When |
| 1381 | [Community 1609](#c-1609) | 5 | 0.33 | 1. **Pressure Field Coordination** (arXiv:2601.08129), 2. **CrewAI v2.3 — Enhanced Multi-Agent Orchestration**, 3. **AutoGen 0.4 — Universal Agent Communication Protocol**, 🌐 Multi-Agent AI Daily Brief — 2026-03-29, Ключевые находки |
| 1382 | [Community 1610](#c-1610) | 5 | 0.33 | 1. Microsoft Conductor — open-source YAML-оркестратор multi-agent систем, 2. REDEREF — training-free маршрутизация для multi-agent LLM систем, 3. CoalT — game theory coalition formation для multi-agent LLM, Multi-Agent AI Daily Digest, Топ-3 за сегодня |
| 1383 | [Community 1611](#c-1611) | 5 | 0.33 | 1. Microsoft Agent Framework — Handoff pattern + Foundry Hosted Agents (BUILD 2026), 2. Cloudflare Agents 0.14.0 — durable multi-agent orchestration + Skills engine, 3. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems (ACL ARR 2026), Multi-Agent AI Daily — 2026-06-08, Сводка по применению в AstroFinSentinelV5 |
| 1384 | [Community 1612](#c-1612) | 5 | 0.33 | 1. Microsoft Agent Framework Python 1.8.0 — стабилизация Magentic multi-agent оркестрации, 2. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems, 3. Hermes Agent v0.16.0 (Surface Release) — Kanban multi-agent swarm, 🤖 Multi-Agent AI Daily — 2026-06-09, Прочие заметные релизы (для контекста) |
| 1385 | [Community 1613](#c-1613) | 5 | 0.33 | 1. Microsoft Agent Framework 1.8.0 — McpSkills, MCP long-running tasks (SEP-2663) и compaction stability, 2. POISE — автономное открытие новых LLM-RL алгоритмов агентами-учёными, 3. dySCo / Pi-Taskflow / Open-Multi-Agent — typed DAG и sparse-координация для verifiable мульти-агентов, 🤖 Multi-Agent AI Daily — 2026-06-10, … (+1) |
| 1386 | [Community 1614](#c-1614) | 5 | 0.33 | 1. Arbor — Microsoft Research: мультиагентный фреймворк с Hypothesis-Tree Refinement, 2. MARS — Multi-Agent Review System: дебаты с -50% токенов, 3. DeLM — Decentralized Language Models: параллельные solver-ветки с общим контекстом, 🤖 Multi-Agent AI Daily — 2026-06-13, Краткий footer |
| 1387 | [Community 1615](#c-1615) | 5 | 0.33 | 1. ECC 2.0.0 — The Agent Harness Operating System, 2. MARS — Multi-Agent Review System (эффективный multi-agent debate), 3. MASFactory — multi-agent workflow из natural language, 🤖 Multi-Agent AI Daily — 2026-06-14, Дополнительные находки (для контекста, … (+1) |
| 1388 | [Community 1618](#c-1618) | 5 | 0.33 | Smoke test for Data Room API blueprint., Проверяем, что Blueprint зарегистрирован и имеет правильный префикс., При запросе /data-room/conflicts должен возвращаться JSON., test_blueprint_exists(), … (+1) |
| 1389 | [Community 1620](#c-1620) | 5 | 0.33 | _alpha_badge(), explorer_tab(), web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)  Enha, Color-coded alpha decay / out-of-sample health badge., Div |
| 1390 | [Community 1627](#c-1627) | 5 | 0.33 | 2-Node Ceph Cluster, Ceph Storage, CephFS, Pool Configuration, RBD Usage |
| 1391 | [Community 1628](#c-1628) | 5 | 0.33 | DNS Records, Firewall Rules, Network Design, VLAN Architecture, WireGuard Mesh Overlay |
| 1392 | [Community 1629](#c-1629) | 5 | 0.33 | Cluster Layout, Connect to Ray, Ray AI Runtime, Ray Dashboard, Slurm + Ray Bridge |
| 1393 | [Community 1630](#c-1630) | 5 | 0.33 | Architecture, GPU Partition, HA Controller Setup (3 controllers), Slurm HA Setup, Useful Commands |
| 1394 | [Community 1642](#c-1642) | 5 | 0.33 | api_validate(), cli_validate(), Input Contract Middleware — strict validation for CLI., CLI entry point validator.      Returns task string if valid, exits with error i, … (+1) |
| 1395 | [Community 1644](#c-1644) | 5 | 0.33 | ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, Components, Dependencies, Expected, Why P1? |
| 1396 | [Community 1645](#c-1645) | 5 | 0.33 | ATOM-DEDUP-001: Дедупликация агентов, Execution, Impact, Problem, Задача |
| 1397 | [Community 1646](#c-1646) | 5 | 0.33 | ATOM-GITAGENT-003: Phase 3 GitAgent, Components, Dependencies, Reason, When |
| 1398 | [Community 1647](#c-1647) | 5 | 0.33 | 1. **Pressure Field Coordination** (arXiv:2601.08129), 2. **CrewAI v2.3 — Enhanced Multi-Agent Orchestration**, 3. **AutoGen 0.4 — Universal Agent Communication Protocol**, 🌐 Multi-Agent AI Daily Brief — 2026-03-29, Ключевые находки |
| 1399 | [Community 1648](#c-1648) | 5 | 0.33 | 1. Microsoft Conductor — open-source YAML-оркестратор multi-agent систем, 2. REDEREF — training-free маршрутизация для multi-agent LLM систем, 3. CoalT — game theory coalition formation для multi-agent LLM, Multi-Agent AI Daily Digest, Топ-3 за сегодня |
| 1400 | [Community 1649](#c-1649) | 5 | 0.33 | 1. Microsoft Agent Framework — Handoff pattern + Foundry Hosted Agents (BUILD 2026), 2. Cloudflare Agents 0.14.0 — durable multi-agent orchestration + Skills engine, 3. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems (ACL ARR 2026), Multi-Agent AI Daily — 2026-06-08, Сводка по применению в AstroFinSentinelV5 |
| 1401 | [Community 1650](#c-1650) | 5 | 0.33 | 1. Microsoft Agent Framework Python 1.8.0 — стабилизация Magentic multi-agent оркестрации, 2. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems, 3. Hermes Agent v0.16.0 (Surface Release) — Kanban multi-agent swarm, 🤖 Multi-Agent AI Daily — 2026-06-09, Прочие заметные релизы (для контекста) |
| 1402 | [Community 1651](#c-1651) | 5 | 0.33 | 1. Microsoft Agent Framework 1.8.0 — McpSkills, MCP long-running tasks (SEP-2663) и compaction stability, 2. POISE — автономное открытие новых LLM-RL алгоритмов агентами-учёными, 3. dySCo / Pi-Taskflow / Open-Multi-Agent — typed DAG и sparse-координация для verifiable мульти-агентов, 🤖 Multi-Agent AI Daily — 2026-06-10, … (+1) |
| 1403 | [Community 1652](#c-1652) | 5 | 0.33 | 1. Arbor — Microsoft Research: мультиагентный фреймворк с Hypothesis-Tree Refinement, 2. MARS — Multi-Agent Review System: дебаты с -50% токенов, 3. DeLM — Decentralized Language Models: параллельные solver-ветки с общим контекстом, 🤖 Multi-Agent AI Daily — 2026-06-13, Краткий footer |
| 1404 | [Community 1653](#c-1653) | 5 | 0.33 | 1. ECC 2.0.0 — The Agent Harness Operating System, 2. MARS — Multi-Agent Review System (эффективный multi-agent debate), 3. MASFactory — multi-agent workflow из natural language, 🤖 Multi-Agent AI Daily — 2026-06-14, Дополнительные находки (для контекста, … (+1) |
| 1405 | [Community 1661](#c-1661) | 5 | 0.33 | ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, Components, Dependencies, Expected, Why P1? |
| 1406 | [Community 1662](#c-1662) | 5 | 0.33 | ATOM-DEDUP-001: Дедупликация агентов, Execution, Impact, Problem, Задача |
| 1407 | [Community 1663](#c-1663) | 5 | 0.33 | ATOM-GITAGENT-003: Phase 3 GitAgent, Components, Dependencies, Reason, When |
| 1408 | [Community 1664](#c-1664) | 5 | 0.33 | 1. **Pressure Field Coordination** (arXiv:2601.08129), 2. **CrewAI v2.3 — Enhanced Multi-Agent Orchestration**, 3. **AutoGen 0.4 — Universal Agent Communication Protocol**, 🌐 Multi-Agent AI Daily Brief — 2026-03-29, Ключевые находки |
| 1409 | [Community 1665](#c-1665) | 5 | 0.33 | 1. Microsoft Conductor — open-source YAML-оркестратор multi-agent систем, 2. REDEREF — training-free маршрутизация для multi-agent LLM систем, 3. CoalT — game theory coalition formation для multi-agent LLM, Multi-Agent AI Daily Digest, Топ-3 за сегодня |
| 1410 | [Community 1666](#c-1666) | 5 | 0.33 | 1. Microsoft Agent Framework — Handoff pattern + Foundry Hosted Agents (BUILD 2026), 2. Cloudflare Agents 0.14.0 — durable multi-agent orchestration + Skills engine, 3. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems (ACL ARR 2026), Multi-Agent AI Daily — 2026-06-08, Сводка по применению в AstroFinSentinelV5 |
| 1411 | [Community 1667](#c-1667) | 5 | 0.33 | 1. Microsoft Agent Framework Python 1.8.0 — стабилизация Magentic multi-agent оркестрации, 2. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems, 3. Hermes Agent v0.16.0 (Surface Release) — Kanban multi-agent swarm, 🤖 Multi-Agent AI Daily — 2026-06-09, Прочие заметные релизы (для контекста) |
| 1412 | [Community 1668](#c-1668) | 5 | 0.33 | 1. Microsoft Agent Framework 1.8.0 — McpSkills, MCP long-running tasks (SEP-2663) и compaction stability, 2. POISE — автономное открытие новых LLM-RL алгоритмов агентами-учёными, 3. dySCo / Pi-Taskflow / Open-Multi-Agent — typed DAG и sparse-координация для verifiable мульти-агентов, 🤖 Multi-Agent AI Daily — 2026-06-10, … (+1) |
| 1413 | [Community 1669](#c-1669) | 5 | 0.33 | 1. Arbor — Microsoft Research: мультиагентный фреймворк с Hypothesis-Tree Refinement, 2. MARS — Multi-Agent Review System: дебаты с -50% токенов, 3. DeLM — Decentralized Language Models: параллельные solver-ветки с общим контекстом, 🤖 Multi-Agent AI Daily — 2026-06-13, Краткий footer |
| 1414 | [Community 1670](#c-1670) | 5 | 0.33 | 1. ECC 2.0.0 — The Agent Harness Operating System, 2. MARS — Multi-Agent Review System (эффективный multi-agent debate), 3. MASFactory — multi-agent workflow из natural language, 🤖 Multi-Agent AI Daily — 2026-06-14, Дополнительные находки (для контекста, … (+1) |
| 1415 | [Community 1673](#c-1673) | 5 | 0.33 | Smoke test for Data Room API blueprint., Проверяем, что Blueprint зарегистрирован и имеет правильный префикс., При запросе /data-room/conflicts должен возвращаться JSON., test_blueprint_exists(), … (+1) |
| 1416 | [Community 1675](#c-1675) | 5 | 0.33 | _alpha_badge(), explorer_tab(), web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)  Enha, Color-coded alpha decay / out-of-sample health badge., Div |
| 1417 | [Community 1677](#c-1677) | 5 | 0.33 | Smoke test for Data Room API blueprint., Проверяем, что Blueprint зарегистрирован и имеет правильный префикс., При запросе /data-room/conflicts должен возвращаться JSON., test_blueprint_exists(), … (+1) |
| 1418 | [Community 1680](#c-1680) | 5 | 0.33 | _alpha_badge(), explorer_tab(), web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)  Enha, Color-coded alpha decay / out-of-sample health badge., Div |
| 1419 | [Community 1372](#c-1372) | 5 | 0.32 | Agents that MUST pass L8+L9 before execution., AgentSpec, get_agent(), get_governance_gated_agents(), list_agents() |
| 1420 | [Community 1373](#c-1373) | 5 | 0.32 | Agents that MUST pass L8+L9 before execution., AgentSpec, get_agent(), get_governance_gated_agents(), list_agents() |
| 1421 | [Community 1405](#c-1405) | 5 | 0.32 | Ack, AtomMessage, Channel, Send an AtomMessage to the remote node.         Returns Ack on success, None on, … (+1) |
| 1422 | [Community 1419](#c-1419) | 5 | 0.32 | BaseHTTPRequestHandler, build_metrics(), Handler, parse_wg_show(), Parse `wg show wg0` output. |
| 1423 | [Community 1151](#c-1151) | 5 | 0.31 | JobResult, Simulate one job scheduling attempt., Tests P99 latency spikes from ILP + Twin + Beam under load., run_all(), SolverLatencyScenario |
| 1424 | [Community 1185](#c-1185) | 5 | 0.31 | JobResult, Simulate one job scheduling attempt., Tests P99 latency spikes from ILP + Twin + Beam under load., run_all(), SolverLatencyScenario |
| 1425 | [Community 1269](#c-1269) | 5 | 0.31 | OnlineTrainer, REINFORCE policy gradient update.         Computes gradient estimate from recent, Run a simulated episode of n_trades.         Returns: episode summary., REINFORCE-style online trainer for position sizing policy.     Updates PolicyPar, Decide position size based on current policy + exploration noise.         Return |
| 1426 | [Community 1091](#c-1091) | 5 | 0.30 | ByzantineDetector, ByzantineIndicator, byzantine_detector.py — Byzantine fault detection for v9.8  Integrates with:   -, Monitors trust+consensus state for Byzantine-adjacent patterns.      Signals emi, _test_byzantine_detector() |
| 1427 | [Community 1493](#c-1493) | 5 | 0.29 | Any, Return last recorded violations from validate()., Immutable specification of system hard boundaries.      These flags define the U, Hard boundary validation gate.          Evaluates the full system state against, SystemBoundarySpec |
| 1428 | [Community 1312](#c-1312) | 5 | 0.28 | Any, StateProjection, Read-side state projection.          PATCH 3: enrich_projection() adds node_grap, Rebuild standard state., PATCH 3: Returns state with node_graph_resolution and execution_order. |
| 1429 | [Community 1340](#c-1340) | 5 | 0.28 | Any, StateProjection, Read-side state projection.      PATCH 3: enrich_projection() adds node_graph_re, Rebuild standard state., PATCH 3: Returns state with node_graph_resolution and execution_order. |
| 1430 | [Community 1149](#c-1149) | 5 | 0.27 | Any, ExecutionContext, ActionResult, ExecutionGate, GateDecision |
| 1431 | [Community 1203](#c-1203) | 5 | 0.25 | Any, ROMASDK — Python client for ROMA Execution Platform. Usage:     from roma_sdk im, ROMAClient, ROMAException, ROMAJob |
| 1432 | [Community 1305](#c-1305) | 5 | 0.25 | MetaRLConfig, meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Produc, True if configured for real market data (not sandbox)., Return list of validation warnings. Empty = all good., Unified production configuration for Meta-RL engine. |
| 1433 | [Community 1306](#c-1306) | 5 | 0.25 | get_hyper_optimizer(), HyperOptimizer, meta_rl/hyperopt.py — ATOM-META-RL-015: Hyperparameter Optimization, ATOM-META-RL-015: Bayesian optimization of Meta-RL hyperparameters., Run a short evolution and return best reward. |
| 1434 | [Community 1329](#c-1329) | 5 | 0.25 | MetaRLConfig, meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Produc, True if configured for real market data (not sandbox)., Return list of validation warnings. Empty = all good., Unified production configuration for Meta-RL engine. |
| 1435 | [Community 1330](#c-1330) | 5 | 0.25 | get_hyper_optimizer(), HyperOptimizer, meta_rl/hyperopt.py — ATOM-META-RL-015: Hyperparameter Optimization, ATOM-META-RL-015: Bayesian optimization of Meta-RL hyperparameters., Run a short evolution and return best reward. |
| 1436 | [Community 1345](#c-1345) | 5 | 0.25 | DeterministicPodScheduler, r'''     Deterministic Kubernetes pod scheduling.      Guarantees:       - Pod s, r'''         Compute deterministic pod startup order.         Sort nodes by hash, r'''         Assign deterministic replica ID.         hash(pod_name) % total_rep, Get the primary node (first in startup order). |
| 1437 | [Community 1347](#c-1347) | 5 | 0.25 | MetaRLConfig, meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Produc, True if configured for real market data (not sandbox)., Return list of validation warnings. Empty = all good., Unified production configuration for Meta-RL engine. |
| 1438 | [Community 1348](#c-1348) | 5 | 0.25 | get_hyper_optimizer(), HyperOptimizer, meta_rl/hyperopt.py — ATOM-META-RL-015: Hyperparameter Optimization, ATOM-META-RL-015: Bayesian optimization of Meta-RL hyperparameters., Run a short evolution and return best reward. |
| 1439 | [Community 1359](#c-1359) | 5 | 0.25 | MetaRLConfig, meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Produc, True if configured for real market data (not sandbox)., Return list of validation warnings. Empty = all good., Unified production configuration for Meta-RL engine. |
| 1440 | [Community 1370](#c-1370) | 5 | 0.25 | Тест warmup phase: первые 20 решений используют blend=0.3., Первые 19 решений используют BLEND_WARMUP=0.3, 20th переходит в mature., После 20 решений используется BLEND_MATURE=0.15., В warmup phase больше вес на raw signal., … (+1) |
| 1441 | [Community 1371](#c-1371) | 5 | 0.25 | Тест вычисления lag_adj., lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)., lag_adj < 0 когда EMA ниже raw (сигнал опережает вверх)., lag_adj масштабируется корректно: |lag_adj| < 1 для разумных отклонений., TestLagAdjustment |
| 1442 | [Community 1374](#c-1374) | 5 | 0.25 | Тест вычисления lag_adj., lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)., lag_adj < 0 когда EMA ниже raw (сигнал опережает вверх)., lag_adj масштабируется корректно: |lag_adj| < 1 для разумных отклонений., TestLagAdjustment |
| 1443 | [Community 1420](#c-1420) | 5 | 0.25 | ENFORCED contract for all storage backends., Write trace. MUST return trace_id (str)., Fetch trace. MUST return dict or None., Query traces. MUST return list[dict]., StorageBackendContract |
| 1444 | [Community 1443](#c-1443) | 5 | 0.25 | Тест warmup phase: первые 20 решений используют blend=0.3., Первые 19 решений используют BLEND_WARMUP=0.3, 20th переходит в mature., После 20 решений используется BLEND_MATURE=0.15., В warmup phase больше вес на raw signal., … (+1) |
| 1445 | [Community 1045](#c-1045) | 5 | 0.24 | FeedbackPrioritySolver, FeedbackSignal, Computes global priority of feedback loops.     priority = urgency * 0.7 + stabi, Return [(layer, priority), … (+2) |
| 1446 | [Community 1156](#c-1156) | 5 | 0.24 | EnsembleDecision, EnsembleScheduler, Policy, Runs multiple policies simultaneously, selects best expected utility., … (+1) |
| 1447 | [Community 1180](#c-1180) | 5 | 0.24 | Runs multiple policies simultaneously, selects best expected utility., Select best policy based on expected utility.         final_action = argmax E[U(, EnsembleDecision, EnsembleScheduler, … (+1) |
| 1448 | [Community 1215](#c-1215) | 5 | 0.24 | Any, meta_rl/strategy.py — Strategy type for Meta-RL (ATOM-META-RL-008), Восстанавливает Strategy из словаря (для persistence)., Trading strategy with chromosome, generation tracking, … (+2) |
| 1449 | [Community 1239](#c-1239) | 5 | 0.24 | Any, meta_rl/strategy.py — Strategy type for Meta-RL (ATOM-META-RL-008), Восстанавливает Strategy из словаря (для persistence)., Trading strategy with chromosome, generation tracking, … (+2) |
| 1450 | [Community 1263](#c-1263) | 5 | 0.24 | Any, meta_rl/strategy.py — Strategy type for Meta-RL (ATOM-META-RL-008), Восстанавливает Strategy из словаря (для persistence)., Trading strategy with chromosome, generation tracking, … (+2) |
| 1451 | [Community 840](#c-840) | 5 | 0.23 | Any, DAGValidator, ValidationResult, Violation, ViolationType |
| 1452 | [Community 1223](#c-1223) | 5 | 0.22 | Any, Event, Immutable event record.      prev_hash is set by EventLog.append() at append tim, Serialize to dict for storage. Does NOT include prev_hash (set at append)., Deserialize from dict. Handles both dict and tuple payloads. |
| 1453 | [Community 1350](#c-1350) | 5 | 0.22 | _stability_bonus: trade-count * win-rate saturation., trades == threshold, win_rate = 0 → 0 bonus., trades >= stability_trade_norm and win_rate = 1 → full bonus., Half saturation in trades → half the bonus (with full win_rate)., … (+1) |
| 1454 | [Community 1011](#c-1011) | 5 | 0.21 | ABC, IEvaluator, IEvaluator, IEvaluator, IEvaluator |
| 1455 | [Community 1059](#c-1059) | 5 | 0.21 | K8s-style admission controller.     All decisions flow: decision → constraint →, Primary admission endpoint.         Request:             {                 "deci, Build DecisionContext from raw request., DecisionContext, AdmissionController |
| 1456 | [Community 1092](#c-1092) | 5 | 0.21 | K8sCompiler, ROMA Execution Bridge — JSON → Kubernetes Job Compiler Fixed: uses nvidia.com/gp, Transforms ROMA DAG into K8s Job manifest., Fallback to RayJob if cluster uses Ray operator., Security + correctness validation. |
| 1457 | [Community 1136](#c-1136) | 5 | 0.20 | Получить значение по ключу., Сохранить значение с TTL (секунд)., Очистить весь кэш (только fallback)., Async cache with Redis backend and in‑memory fallback., RedisCache |
| 1458 | [Community 1153](#c-1153) | 5 | 0.20 | Execute retraining and update last metrics., Call after each job completes — tracks toward retrain threshold., Retrainer, Path, Check if retraining conditions are met. |
| 1459 | [Community 1162](#c-1162) | 5 | 0.20 | Получить значение по ключу., Сохранить значение с TTL (секунд)., Очистить весь кэш (только fallback)., Async cache with Redis backend and in‑memory fallback., RedisCache |
| 1460 | [Community 1173](#c-1173) | 5 | 0.20 | Получить значение по ключу., Сохранить значение с TTL (секунд)., Очистить весь кэш (только fallback)., Async cache with Redis backend and in‑memory fallback., RedisCache |
| 1461 | [Community 1181](#c-1181) | 5 | 0.20 | Check if retraining conditions are met., Execute retraining and update last metrics., Call after each job completes — tracks toward retrain threshold., Retrainer, Path |
| 1462 | [Community 1194](#c-1194) | 5 | 0.20 | Получить значение по ключу., Сохранить значение с TTL (секунд)., Очистить весь кэш (только fallback)., Async cache with Redis backend and in‑memory fallback., RedisCache |
| 1463 | [Community 1224](#c-1224) | 5 | 0.20 | EventSourcedEngine, Emit governance event. Write-side ONLY., Write-side only execution engine.          INVARIANTS (enforced):     - emit() O, Execute DAG. Returns trace_id ONLY., Emit NODE_FAILED event. Write-side ONLY. |
| 1464 | [Community 1252](#c-1252) | 5 | 0.20 | Write-side only execution engine.      INVARIANTS (enforced):     - emit() ONLY, Execute DAG. Returns trace_id ONLY., Emit governance event. Write-side ONLY., EventSourcedEngine, Emit NODE_FAILED event. Write-side ONLY. |
| 1465 | [Community 1285](#c-1285) | 5 | 0.20 | High control saturation → SATURATED mode., Oscillation index computation and mode detection., Gain ratio near 1.0 → stable., Alternating overshoot/undershoot → oscillating., TestOscillationDetection |
| 1466 | [Community 673](#c-673) | 5 | 0.18 | Any, AmneziaWGManager, TunnelEvent, Manages AmneziaWG tunnel. C-8 refactored: start() = 7 lines., Bring up tunnel. Idempotent. Invariant: write-side only. |
| 1467 | [Community 787](#c-787) | 5 | 0.18 | Any, ExecutionTrace, TraceNode, TraceStore, TraceType |
| 1468 | [Community 932](#c-932) | 5 | 0.18 | ConflictResolutionMatrix, Set winning weight of 'a' over 'b'., Return the higher-priority layer between two., Formal resolution of inter-layer control conflicts.     Precedence matrix: highe, TestConflictResolutionMatrix |
| 1469 | [Community 1146](#c-1146) | 5 | 0.18 | DeterministicTraceRecorder, EventSourcedEngine, Idempotent execution.                  PATCH 2: Check has_trace() BEFORE executi, Emit NODE_FAILED event., Emit governance event. |
| 1470 | [Community 854](#c-854) | 5 | 0.17 | view_change.py — Cooperative view-change mechanism for PBFT-lite v9.8, Cooperative leader rotation. Lightweight (not full PBFT view-change)., ViewChangeEvent, ViewChangeManager, ViewChangeReason |
| 1471 | [Community 1039](#c-1039) | 5 | 0.17 | OVERLAY_ROOT, sandbox_init(), SANDBOX_STATE_DIR, SANDBOX_VERSION, engine_sandbox_runtime.sh script |
| 1472 | [Community 1112](#c-1112) | 5 | 0.17 | CycleRecord, plan_trace_logger.py — planning_observability layer Records full execution trace, ReplanRecord, ScoreEvolutionPoint, TraceEventType |
| 1473 | [Community 724](#c-724) | 5 | 0.16 | ContinuousStabilityEngine, ContinuousStabilityEngine v6.5 — Proactive 1Hz stability tick loop.  Problem:, Execute one stability tick synchronously.         Returns TickResult for the tic, Runs stability evaluation every TICK_MS milliseconds.      This is the "heartbea, TickResult |
| 1474 | [Community 301](#c-301) | 5 | 0.11 | PlanTraceLogger, Records full execution trace of the planning pipeline.      Provides:       - fu, TraceEvent, PlanTraceLogger: event recording and query., TestPlanTraceLogger |
| 1475 | [Community 669](#c-669) | 5 | 0.11 | Tests for MacroAgent — VIX, DXY, geopolitical risk., TestMacroAgentAggregate, TestMacroAgentDXY, … (+2) |
| 1476 | [Community 690](#c-690) | 5 | 0.11 | Tests for MacroAgent — VIX, DXY, geopolitical risk., TestMacroAgentAggregate, TestMacroAgentDXY, … (+2) |
| 1477 | [Community 720](#c-720) | 5 | 0.11 | Tests for MacroAgent — VIX, DXY, geopolitical risk., TestMacroAgentAggregate, TestMacroAgentDXY, … (+2) |
| 1478 | [Community 726](#c-726) | 5 | 0.11 | Tests for MacroAgent — VIX, DXY, geopolitical risk., TestMacroAgentAggregate, TestMacroAgentDXY, … (+2) |
| 1479 | [Community 424](#c-424) | 5 | 0.08 | tests/test_risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 Tests ==================, TestDrawdownKillSwitch, TestExposureControl, TestModeGating, TestVolatilityTargeting |
| 1480 | [Community 1784](#c-1784) | 4 | 0.80 | run_scenario1.sh script, check(), log(), -throughput() |
| 1481 | [Community 1732](#c-1732) | 4 | 0.70 | fail(), info(), warn(), build_push.sh script |
| 1482 | [Community 1734](#c-1734) | 4 | 0.70 | fail(), info(), warn(), validate_local.sh script |
| 1483 | [Community 1708](#c-1708) | 4 | 0.60 | generate_signals(), generate_synthetic_data(), main(), scripts/run_backtest.py — ATOM-STEP-8: Backtest Runner |
| 1484 | [Community 1717](#c-1717) | 4 | 0.60 | get_counts(), main(), Append a snapshot row to the backtest DB for trend tracking., save_snapshot() |
| 1485 | [Community 1718](#c-1718) | 4 | 0.60 | check_and_export(), Check strategy pool for new top strategies and export them., run_daemon(), run_once() |
| 1486 | [Community 1726](#c-1726) | 4 | 0.60 | _build_reason(), _node_to_partition(), select_node(), Select optimal node for a job.     Returns: {node, score, … (+2) |
| 1487 | [Community 1758](#c-1758) | 4 | 0.60 | generate_signals(), generate_synthetic_data(), main(), scripts/run_backtest.py — ATOM-STEP-8: Backtest Runner |
| 1488 | [Community 1767](#c-1767) | 4 | 0.60 | get_counts(), main(), Append a snapshot row to the backtest DB for trend tracking., save_snapshot() |
| 1489 | [Community 1768](#c-1768) | 4 | 0.60 | check_and_export(), Check strategy pool for new top strategies and export them., run_daemon(), run_once() |
| 1490 | [Community 1780](#c-1780) | 4 | 0.60 | _build_reason(), _node_to_partition(), select_node(), Select optimal node for a job.     Returns: {node, score, … (+2) |
| 1491 | [Community 1817](#c-1817) | 4 | 0.60 | generate_signals(), generate_synthetic_data(), main(), scripts/run_backtest.py — ATOM-STEP-8: Backtest Runner |
| 1492 | [Community 1826](#c-1826) | 4 | 0.60 | get_counts(), main(), Append a snapshot row to the backtest DB for trend tracking., save_snapshot() |
| 1493 | [Community 1827](#c-1827) | 4 | 0.60 | check_and_export(), Check strategy pool for new top strategies and export them., run_daemon(), run_once() |
| 1494 | [Community 1831](#c-1831) | 4 | 0.60 | generate_signals(), generate_synthetic_data(), main(), scripts/run_backtest.py — ATOM-STEP-8: Backtest Runner |
| 1495 | [Community 1840](#c-1840) | 4 | 0.60 | get_counts(), main(), Append a snapshot row to the backtest DB for trend tracking., save_snapshot() |
| 1496 | [Community 1841](#c-1841) | 4 | 0.60 | check_and_export(), Check strategy pool for new top strategies and export them., run_daemon(), run_once() |
| 1497 | [Community 1727](#c-1727) | 4 | 0.50 | rank_nodes(), score_node(), Compute suitability score for a node.     Higher = better. Range approximately 0, Return dict of node -> score, sorted descending. |
| 1498 | [Community 1781](#c-1781) | 4 | 0.50 | rank_nodes(), score_node(), Compute suitability score for a node.     Higher = better. Range approximately 0, Return dict of node -> score, sorted descending. |
| 1499 | [Community 1902](#c-1902) | 4 | 0.50 | 10.1 Why Replay Becomes Exact, 10.2 Why Race Conditions Are Eliminated, 10.3 Why Ledger Is Linearizable, 10. SAFETY PROOF (INFORMAL) |
| 1500 | [Community 1903](#c-1903) | 4 | 0.50 | 1. EXECUTIVE SUMMARY, Current State (v9.0+ATOM-META-RL-018), Goal, Target State (ATOM-META-RL-019) |
| 1501 | [Community 1904](#c-1904) | 4 | 0.50 | 3.1 Current Execution Graph (v9.0), 3.2 New Linearized Execution Graph (ATOM-META-RL-019), 3.3 Key Differences, 3. EXECUTION MODEL — BEFORE / AFTER |
| 1502 | [Community 1905](#c-1905) | 4 | 0.50 | 4.1 Before (Layered), 4.2 After (Linearized), 4.3 Global Execution Sequencer, 4. MUTATION FLOW REDESIGN |
| 1503 | [Community 1906](#c-1906) | 4 | 0.50 | 6.1 Problem, 6.2 Solution: AtomicLedgerWriter, 6.3 Integration, 6. LEDGER LINEARIZATION — HARD FIX |
| 1504 | [Community 1570](#c-1570) | 4 | 0.40 | CouncilMember, CouncilResult, core/council/types.py — AstroCouncil data types, Signal |
| 1505 | [Community 1624](#c-1624) | 4 | 0.40 | CouncilMember, CouncilResult, core/council/types.py — AstroCouncil data types, Signal |
| 1506 | [Community 1660](#c-1660) | 4 | 0.40 | Experience, core/online_trainer.py — ATOM-STEP-6: Online RL Trainer ========================, Add experience to replay buffer., datetime |
| 1507 | [Community 1682](#c-1682) | 4 | 0.40 | 🤖 AstroCouncil Agent, Запреты, Обязанности, Формат ответа |
| 1508 | [Community 1683](#c-1683) | 4 | 0.40 | 🤖 ElectoralAgent (Electional Astrologer), Запреты, Обязанности, Формат ответа |
| 1509 | [Community 1685](#c-1685) | 4 | 0.40 | amre/grounding.py — ATOM-KARL-015 Phase 5: Soft Degrade Grounding  Заменяет жёст, Domain grounding validation с мягким multiplicative degrade.      Parameters, validate_with_grounding(), Any |
| 1510 | [Community 1686](#c-1686) | 4 | 0.40 | 🤖 SynthesisAgent (Deliberium), Запреты, Обязанности, Формат ответа |
| 1511 | [Community 1687](#c-1687) | 4 | 0.40 | 🤖 AstroCouncil Agent, Запреты, Обязанности, Формат ответа |
| 1512 | [Community 1688](#c-1688) | 4 | 0.40 | 🤖 ElectoralAgent (Electional Astrologer), Запреты, Обязанности, Формат ответа |
| 1513 | [Community 1690](#c-1690) | 4 | 0.40 | amre/grounding.py — ATOM-KARL-015 Phase 5: Soft Degrade Grounding  Заменяет жёст, Domain grounding validation с мягким multiplicative degrade.      Parameters, validate_with_grounding(), Any |
| 1514 | [Community 1691](#c-1691) | 4 | 0.40 | 🤖 SynthesisAgent (Deliberium), Запреты, Обязанности, Формат ответа |
| 1515 | [Community 1693](#c-1693) | 4 | 0.40 | get_project_root(), AstroFin Sentinel v5 — Project Root Utility Provides the absolute path to the pr, Returns the absolute path to the AstroFinSentinelV5 project root.      Resolves, Path |
| 1516 | [Community 1696](#c-1696) | 4 | 0.40 | AstroFin Sentinel V5 — Обзор проекта, Вдохновение, Доменная структура (DDD), Ключевые возможности |
| 1517 | [Community 1697](#c-1697) | 4 | 0.40 | AstroFin Sentinel V5 – Бэклог для Ralph Loop, P0 (Критические), P1 (Важные), P2 (Желательные) |
| 1518 | [Community 1698](#c-1698) | 4 | 0.40 | ATOM-FIX-ROUTER: Исправление бага с timeframe, Execution, Impact, Problem |
| 1519 | [Community 1699](#c-1699) | 4 | 0.40 | ATOM-MODEL-SPEC: Единая спецификация модели, Components, Dependencies, Why P1? |
| 1520 | [Community 1700](#c-1700) | 4 | 0.40 | Bollinger Bands, MACD (Moving Average Convergence Divergence), RSI (Relative Strength Index), Technical Indicators — RSI, MACD, … (+1) |
| 1521 | [Community 1701](#c-1701) | 4 | 0.40 | Kelly Criterion, Position Sizing Rules, Risk-Based Sizing, Session Limits |
| 1522 | [Community 1702](#c-1702) | 4 | 0.40 | Core Rules, Drawdown Rules, Dynamic Risk Scaling, Risk Management Framework |
| 1523 | [Community 1703](#c-1703) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-04-27, Дополнительно (также релевантно), Источники, Топ-3 за неделю |
| 1524 | [Community 1704](#c-1704) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-05-03, Источники: GitHub, arXiv, Reddit, Hugging Face, … (+3) |
| 1525 | [Community 1705](#c-1705) | 4 | 0.40 | 1. Arbor — структурированный tree search как cognition layer для автономных агентов, 2. DeLM — децентрализованный multi-agent фреймворк с общим контекстом, 3. Citadel — open-source orchestration layer для Claude Code и Codex, Multi-Agent AI Daily — 2026-06-15 |
| 1526 | [Community 1706](#c-1706) | 4 | 0.40 | 1. OrchRM — self-supervised reward modeling для оркестратора multi-agent LLM-систем, 2. ECC 2.0 — Agent Harness Operating System с cross-harness оркестрацией, 3. Swarms v13 "Kizuna 絆" — async GroupChats и streaming workflows для production multi-agent, Multi-Agent AI Daily — 2026-06-16 |
| 1527 | [Community 1709](#c-1709) | 4 | 0.40 | cleanup(), Удаляем временные файлы до и после теста., Проверяем, что после Ralph Loop агент создал нужный файл., test_agent_can_create_add_function() |
| 1528 | [Community 1713](#c-1713) | 4 | 0.40 | Проверяем, что команда 'karl metrics serve' доступна., При флаге --with-metrics счётчики метрик должны увеличиваться.     (Проверяем че, test_metrics_serve_command_exists(), test_with_metrics_flag_registers_metrics() |
| 1529 | [Community 1714](#c-1714) | 4 | 0.40 | После retrieve должны обновиться метрики relevance_score и chunk_count., Повторный запрос с теми же параметрами должен вернуть кешированный результат., test_rag_query_cache_hits_increment(), test_rag_retrieve_updates_quality_metrics() |
| 1530 | [Community 1715](#c-1715) | 4 | 0.40 | Проверяем, что после 10 запросов с правильным ключом возвращается 429., Публичные эндпоинты не должны лимитироваться., test_health_endpoint_not_limited(), test_rate_limit_too_many_requests() |
| 1531 | [Community 1719](#c-1719) | 4 | 0.40 | flask_app(), Test Redis connection., Start Flask app in background with proper cleanup., redis_client() |
| 1532 | [Community 1723](#c-1723) | 4 | 0.40 | test_metrics_serve_command_exists(), test_with_metrics_flag_registers_metrics(), Проверяем, что команда 'karl metrics serve' доступна., При флаге --with-metrics счётчики метрик должны увеличиваться.     (Проверяем че |
| 1533 | [Community 1724](#c-1724) | 4 | 0.40 | test_rag_query_cache_hits_increment(), test_rag_retrieve_updates_quality_metrics(), Повторный запрос с теми же параметрами должен вернуть кешированный результат., После retrieve должны обновиться метрики relevance_score и chunk_count. |
| 1534 | [Community 1725](#c-1725) | 4 | 0.40 | test_health_endpoint_not_limited(), test_rate_limit_too_many_requests(), Проверяем, что после 10 запросов с правильным ключом возвращается 429., Публичные эндпоинты не должны лимитироваться. |
| 1535 | [Community 1733](#c-1733) | 4 | 0.40 | Any, sbs/cli_run.py — run subcommand implementation., Run a predefined test scenario., run_scenario() |
| 1536 | [Community 1737](#c-1737) | 4 | 0.40 | 🤖 AstroCouncil Agent, Запреты, Обязанности, Формат ответа |
| 1537 | [Community 1738](#c-1738) | 4 | 0.40 | 🤖 ElectoralAgent (Electional Astrologer), Запреты, Обязанности, Формат ответа |
| 1538 | [Community 1740](#c-1740) | 4 | 0.40 | amre/grounding.py — ATOM-KARL-015 Phase 5: Soft Degrade Grounding  Заменяет жёст, Domain grounding validation с мягким multiplicative degrade.      Parameters, validate_with_grounding(), Any |
| 1539 | [Community 1741](#c-1741) | 4 | 0.40 | 🤖 SynthesisAgent (Deliberium), Запреты, Обязанности, Формат ответа |
| 1540 | [Community 1743](#c-1743) | 4 | 0.40 | get_project_root(), AstroFin Sentinel v5 — Project Root Utility Provides the absolute path to the pr, Returns the absolute path to the AstroFinSentinelV5 project root.      Resolves, Path |
| 1541 | [Community 1746](#c-1746) | 4 | 0.40 | AstroFin Sentinel V5 — Обзор проекта, Вдохновение, Доменная структура (DDD), Ключевые возможности |
| 1542 | [Community 1747](#c-1747) | 4 | 0.40 | AstroFin Sentinel V5 – Бэклог для Ralph Loop, P0 (Критические), P1 (Важные), P2 (Желательные) |
| 1543 | [Community 1748](#c-1748) | 4 | 0.40 | ATOM-FIX-ROUTER: Исправление бага с timeframe, Execution, Impact, Problem |
| 1544 | [Community 1749](#c-1749) | 4 | 0.40 | ATOM-MODEL-SPEC: Единая спецификация модели, Components, Dependencies, Why P1? |
| 1545 | [Community 1750](#c-1750) | 4 | 0.40 | Bollinger Bands, MACD (Moving Average Convergence Divergence), RSI (Relative Strength Index), Technical Indicators — RSI, MACD, … (+1) |
| 1546 | [Community 1751](#c-1751) | 4 | 0.40 | Kelly Criterion, Position Sizing Rules, Risk-Based Sizing, Session Limits |
| 1547 | [Community 1752](#c-1752) | 4 | 0.40 | Core Rules, Drawdown Rules, Dynamic Risk Scaling, Risk Management Framework |
| 1548 | [Community 1753](#c-1753) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-04-27, Дополнительно (также релевантно), Источники, Топ-3 за неделю |
| 1549 | [Community 1754](#c-1754) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-05-03, Источники: GitHub, arXiv, Reddit, Hugging Face, … (+3) |
| 1550 | [Community 1755](#c-1755) | 4 | 0.40 | 1. Arbor — структурированный tree search как cognition layer для автономных агентов, 2. DeLM — децентрализованный multi-agent фреймворк с общим контекстом, 3. Citadel — open-source orchestration layer для Claude Code и Codex, Multi-Agent AI Daily — 2026-06-15 |
| 1551 | [Community 1756](#c-1756) | 4 | 0.40 | 1. OrchRM — self-supervised reward modeling для оркестратора multi-agent LLM-систем, 2. ECC 2.0 — Agent Harness Operating System с cross-harness оркестрацией, 3. Swarms v13 "Kizuna 絆" — async GroupChats и streaming workflows для production multi-agent, Multi-Agent AI Daily — 2026-06-16 |
| 1552 | [Community 1759](#c-1759) | 4 | 0.40 | cleanup(), Удаляем временные файлы до и после теста., Проверяем, что после Ralph Loop агент создал нужный файл., test_agent_can_create_add_function() |
| 1553 | [Community 1763](#c-1763) | 4 | 0.40 | Проверяем, что команда 'karl metrics serve' доступна., При флаге --with-metrics счётчики метрик должны увеличиваться.     (Проверяем че, test_metrics_serve_command_exists(), test_with_metrics_flag_registers_metrics() |
| 1554 | [Community 1764](#c-1764) | 4 | 0.40 | После retrieve должны обновиться метрики relevance_score и chunk_count., Повторный запрос с теми же параметрами должен вернуть кешированный результат., test_rag_query_cache_hits_increment(), test_rag_retrieve_updates_quality_metrics() |
| 1555 | [Community 1765](#c-1765) | 4 | 0.40 | Проверяем, что после 10 запросов с правильным ключом возвращается 429., Публичные эндпоинты не должны лимитироваться., test_health_endpoint_not_limited(), test_rate_limit_too_many_requests() |
| 1556 | [Community 1771](#c-1771) | 4 | 0.40 | get_project_root(), AstroFin Sentinel v5 — Project Root Utility Provides the absolute path to the pr, Returns the absolute path to the AstroFinSentinelV5 project root.      Resolves, Path |
| 1557 | [Community 1774](#c-1774) | 4 | 0.40 | AstroFin Sentinel V5 — Обзор проекта, Вдохновение, Доменная структура (DDD), Ключевые возможности |
| 1558 | [Community 1775](#c-1775) | 4 | 0.40 | AstroFin Sentinel V5 – Бэклог для Ralph Loop, P0 (Критические), P1 (Важные), P2 (Желательные) |
| 1559 | [Community 1778](#c-1778) | 4 | 0.40 | Self-Hosted Runner Setup (без токенов / GitHub App), Быстрый старт (SSH-only), Деплой через SSH (без GitHub App), Обновление раннера |
| 1560 | [Community 1783](#c-1783) | 4 | 0.40 | bootstrap_env.sh script, FORCE_BOOTSTRAP, PYTHONHASHSEED, PYTHONPATH |
| 1561 | [Community 1786](#c-1786) | 4 | 0.40 | ATOM-FIX-ROUTER: Исправление бага с timeframe, Execution, Impact, Problem |
| 1562 | [Community 1787](#c-1787) | 4 | 0.40 | ATOM-MODEL-SPEC: Единая спецификация модели, Components, Dependencies, Why P1? |
| 1563 | [Community 1788](#c-1788) | 4 | 0.40 | Bollinger Bands, MACD (Moving Average Convergence Divergence), RSI (Relative Strength Index), Technical Indicators — RSI, MACD, … (+1) |
| 1564 | [Community 1789](#c-1789) | 4 | 0.40 | Kelly Criterion, Position Sizing Rules, Risk-Based Sizing, Session Limits |
| 1565 | [Community 1790](#c-1790) | 4 | 0.40 | Core Rules, Drawdown Rules, Dynamic Risk Scaling, Risk Management Framework |
| 1566 | [Community 1791](#c-1791) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-04-27, Дополнительно (также релевантно), Источники, Топ-3 за неделю |
| 1567 | [Community 1792](#c-1792) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-05-03, Источники: GitHub, arXiv, Reddit, Hugging Face, … (+3) |
| 1568 | [Community 1793](#c-1793) | 4 | 0.40 | 1. Arbor — структурированный tree search как cognition layer для автономных агентов, 2. DeLM — децентрализованный multi-agent фреймворк с общим контекстом, 3. Citadel — open-source orchestration layer для Claude Code и Codex, Multi-Agent AI Daily — 2026-06-15 |
| 1569 | [Community 1794](#c-1794) | 4 | 0.40 | 1. OrchRM — self-supervised reward modeling для оркестратора multi-agent LLM-систем, 2. ECC 2.0 — Agent Harness Operating System с cross-harness оркестрацией, 3. Swarms v13 "Kizuna 絆" — async GroupChats и streaming workflows для production multi-agent, Multi-Agent AI Daily — 2026-06-16 |
| 1570 | [Community 1797](#c-1797) | 4 | 0.40 | 🤖 AstroCouncil Agent, Запреты, Обязанности, Формат ответа |
| 1571 | [Community 1798](#c-1798) | 4 | 0.40 | 🤖 ElectoralAgent (Electional Astrologer), Запреты, Обязанности, Формат ответа |
| 1572 | [Community 1800](#c-1800) | 4 | 0.40 | amre/grounding.py — ATOM-KARL-015 Phase 5: Soft Degrade Grounding  Заменяет жёст, Domain grounding validation с мягким multiplicative degrade.      Parameters, validate_with_grounding(), Any |
| 1573 | [Community 1801](#c-1801) | 4 | 0.40 | 🤖 SynthesisAgent (Deliberium), Запреты, Обязанности, Формат ответа |
| 1574 | [Community 1803](#c-1803) | 4 | 0.40 | get_project_root(), AstroFin Sentinel v5 — Project Root Utility Provides the absolute path to the pr, Returns the absolute path to the AstroFinSentinelV5 project root.      Resolves, Path |
| 1575 | [Community 1805](#c-1805) | 4 | 0.40 | AstroFin Sentinel V5 — Обзор проекта, Вдохновение, Доменная структура (DDD), Ключевые возможности |
| 1576 | [Community 1806](#c-1806) | 4 | 0.40 | AstroFin Sentinel V5 – Бэклог для Ralph Loop, P0 (Критические), P1 (Важные), P2 (Желательные) |
| 1577 | [Community 1807](#c-1807) | 4 | 0.40 | ATOM-FIX-ROUTER: Исправление бага с timeframe, Execution, Impact, Problem |
| 1578 | [Community 1808](#c-1808) | 4 | 0.40 | ATOM-MODEL-SPEC: Единая спецификация модели, Components, Dependencies, Why P1? |
| 1579 | [Community 1809](#c-1809) | 4 | 0.40 | Bollinger Bands, MACD (Moving Average Convergence Divergence), RSI (Relative Strength Index), Technical Indicators — RSI, MACD, … (+1) |
| 1580 | [Community 1810](#c-1810) | 4 | 0.40 | Kelly Criterion, Position Sizing Rules, Risk-Based Sizing, Session Limits |
| 1581 | [Community 1811](#c-1811) | 4 | 0.40 | Core Rules, Drawdown Rules, Dynamic Risk Scaling, Risk Management Framework |
| 1582 | [Community 1812](#c-1812) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-04-27, Дополнительно (также релевантно), Источники, Топ-3 за неделю |
| 1583 | [Community 1813](#c-1813) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-05-03, Источники: GitHub, arXiv, Reddit, Hugging Face, … (+3) |
| 1584 | [Community 1814](#c-1814) | 4 | 0.40 | 1. Arbor — структурированный tree search как cognition layer для автономных агентов, 2. DeLM — децентрализованный multi-agent фреймворк с общим контекстом, 3. Citadel — open-source orchestration layer для Claude Code и Codex, Multi-Agent AI Daily — 2026-06-15 |
| 1585 | [Community 1815](#c-1815) | 4 | 0.40 | 1. OrchRM — self-supervised reward modeling для оркестратора multi-agent LLM-систем, 2. ECC 2.0 — Agent Harness Operating System с cross-harness оркестрацией, 3. Swarms v13 "Kizuna 絆" — async GroupChats и streaming workflows для production multi-agent, Multi-Agent AI Daily — 2026-06-16 |
| 1586 | [Community 1818](#c-1818) | 4 | 0.40 | cleanup(), Удаляем временные файлы до и после теста., Проверяем, что после Ralph Loop агент создал нужный файл., test_agent_can_create_add_function() |
| 1587 | [Community 1822](#c-1822) | 4 | 0.40 | Проверяем, что команда 'karl metrics serve' доступна., При флаге --with-metrics счётчики метрик должны увеличиваться.     (Проверяем че, test_metrics_serve_command_exists(), test_with_metrics_flag_registers_metrics() |
| 1588 | [Community 1823](#c-1823) | 4 | 0.40 | После retrieve должны обновиться метрики relevance_score и chunk_count., Повторный запрос с теми же параметрами должен вернуть кешированный результат., test_rag_query_cache_hits_increment(), test_rag_retrieve_updates_quality_metrics() |
| 1589 | [Community 1824](#c-1824) | 4 | 0.40 | Проверяем, что после 10 запросов с правильным ключом возвращается 429., Публичные эндпоинты не должны лимитироваться., test_health_endpoint_not_limited(), test_rate_limit_too_many_requests() |
| 1590 | [Community 1828](#c-1828) | 4 | 0.40 | Ralph Loop Instructions for AstroFin Sentinel V5, Запрещено, Общие правила, Обязательные проверки |
| 1591 | [Community 1832](#c-1832) | 4 | 0.40 | cleanup(), Удаляем временные файлы до и после теста., Проверяем, что после Ralph Loop агент создал нужный файл., test_agent_can_create_add_function() |
| 1592 | [Community 1836](#c-1836) | 4 | 0.40 | Проверяем, что команда 'karl metrics serve' доступна., При флаге --with-metrics счётчики метрик должны увеличиваться.     (Проверяем че, test_metrics_serve_command_exists(), test_with_metrics_flag_registers_metrics() |
| 1593 | [Community 1837](#c-1837) | 4 | 0.40 | После retrieve должны обновиться метрики relevance_score и chunk_count., Повторный запрос с теми же параметрами должен вернуть кешированный результат., test_rag_query_cache_hits_increment(), test_rag_retrieve_updates_quality_metrics() |
| 1594 | [Community 1838](#c-1838) | 4 | 0.40 | Проверяем, что после 10 запросов с правильным ключом возвращается 429., Публичные эндпоинты не должны лимитироваться., test_health_endpoint_not_limited(), test_rate_limit_too_many_requests() |
| 1595 | [Community 1489](#c-1489) | 4 | 0.38 | build_metrics(), Handler, parse_wg_show(), Parse `wg show wg0` output. |
| 1596 | [Community 1313](#c-1313) | 4 | 0.36 | Any, ExecutionState, _payload_to_dict(), StateReducer |
| 1597 | [Community 1402](#c-1402) | 4 | 0.36 | ILPResult, ILPSolver, Solves: max U(x) subject to hard constraints.     Uses scipy minimize with penal, Greedy fallback when ILP is too large. |
| 1598 | [Community 1424](#c-1424) | 4 | 0.36 | Single entry point for ALL AstroFin execution.     Flow: API request → Trace → L, Submit AstroFin job through ACOS governance pipeline.         Returns: trace_dic, ACOSSubmissionGateway, main() |
| 1599 | [Community 1490](#c-1490) | 4 | 0.33 | Candidate, CandidateGenerator, Generates K-best placement candidates using beam search.     Stage 1: ML ranking, Generate ranked placement candidates for all pending jobs.         Returns top-K |
| 1600 | [Community 1513](#c-1513) | 4 | 0.33 | Generates K-best placement candidates using beam search.     Stage 1: ML ranking, Generate ranked placement candidates for all pending jobs.         Returns top-K, Candidate, CandidateGenerator |
| 1601 | [Community 1541](#c-1541) | 4 | 0.33 | PolicyParams, Trainable policy parameters., Reset parameters to best observed configuration., TrainingState |
| 1602 | [Community 1581](#c-1581) | 4 | 0.33 | Validated input for the Sentinel V5 orchestrator.      If Pydantic validation fa, Query must not be empty or whitespace-only., Symbol must be uppercase and non-empty., SentinelV5Request |
| 1603 | [Community 1585](#c-1585) | 4 | 0.33 | ab_compare(), live_enable(), A/B compare two sessions: ?sid_a=X&sid_b=Y     Supports both new-style sessions, Включает live-режим. Требует подтверждение и API-ключ. |
| 1604 | [Community 1586](#c-1586) | 4 | 0.33 | Common commands, Conventions, Friction notes, Quick map |
| 1605 | [Community 1617](#c-1617) | 4 | 0.33 | Validated input for the Sentinel V5 orchestrator.      If Pydantic validation fa, Query must not be empty or whitespace-only., Symbol must be uppercase and non-empty., SentinelV5Request |
| 1606 | [Community 1621](#c-1621) | 4 | 0.33 | ab_compare(), live_enable(), A/B compare two sessions: ?sid_a=X&sid_b=Y     Supports both new-style sessions, Включает live-режим. Требует подтверждение и API-ключ. |
| 1607 | [Community 1643](#c-1643) | 4 | 0.33 | Validate that trained models meet minimum quality thresholds., Trained failure model must achieve AUC >= 0.60 on hold-out set., Trained load model must achieve RMSE <= 10.0 on hold-out set., TestModelQuality |
| 1608 | [Community 1656](#c-1656) | 4 | 0.33 | Validated input for the Sentinel V5 orchestrator.      If Pydantic validation fa, Query must not be empty or whitespace-only., Symbol must be uppercase and non-empty., SentinelV5Request |
| 1609 | [Community 1657](#c-1657) | 4 | 0.33 | AtomNodeServicer, Minimal node-to-node message contract, Unary send — fire-and-wait ack, Streaming — for high-throughput feeds |
| 1610 | [Community 1672](#c-1672) | 4 | 0.33 | Validated input for the Sentinel V5 orchestrator.      If Pydantic validation fa, Query must not be empty or whitespace-only., Symbol must be uppercase and non-empty., SentinelV5Request |
| 1611 | [Community 1676](#c-1676) | 4 | 0.33 | ab_compare(), live_enable(), A/B compare two sessions: ?sid_a=X&sid_b=Y     Supports both new-style sessions, Включает live-режим. Требует подтверждение и API-ключ. |
| 1612 | [Community 1679](#c-1679) | 4 | 0.33 | Security Gate — validates ROMA JSON before compilation., Run all security checks. Return pass/fail., Filters ROMA JSON for dangerous patterns.     Returns {passed: bool, reason: str, SecurityGate |
| 1613 | [Community 1681](#c-1681) | 4 | 0.33 | ab_compare(), live_enable(), A/B compare two sessions: ?sid_a=X&sid_b=Y     Supports both new-style sessions, Включает live-режим. Требует подтверждение и API-ключ. |
| 1614 | [Community 1391](#c-1391) | 4 | 0.32 | datetime, TraceRecord, _utcnow(), Normalized trace record for persistent storage.     All fields are simple types |
| 1615 | [Community 1428](#c-1428) | 4 | 0.32 | datetime, TraceRecord, _utcnow(), Normalized trace record for persistent storage.     All fields are simple types |
| 1616 | [Community 1139](#c-1139) | 4 | 0.31 | main(), core/residual_model.py - ATOM-STEP-4: Residual Correction Model, ResidualCorrection, ResidualModel |
| 1617 | [Community 1165](#c-1165) | 4 | 0.31 | main(), core/residual_model.py - ATOM-STEP-4: Residual Correction Model, ResidualCorrection, ResidualModel |
| 1618 | [Community 1176](#c-1176) | 4 | 0.31 | main(), core/residual_model.py - ATOM-STEP-4: Residual Correction Model, ResidualCorrection, ResidualModel |
| 1619 | [Community 1196](#c-1196) | 4 | 0.31 | main(), core/residual_model.py - ATOM-STEP-4: Residual Correction Model, ResidualCorrection, ResidualModel |
| 1620 | [Community 1230](#c-1230) | 4 | 0.29 | ObjectiveReweighter, ObjectiveWeights, Self-adjusting objective function weights.     weights = weights + lr * gradient, Update weights using gradient ascent on negative regret.         performance: {t |
| 1621 | [Community 1258](#c-1258) | 4 | 0.29 | ObjectiveReweighter, ObjectiveWeights, Self-adjusting objective function weights.     weights = weights + lr * gradient, Update weights using gradient ascent on negative regret.         performance: {t |
| 1622 | [Community 1460](#c-1460) | 4 | 0.29 | FeedbackSignal, Ingest a new feedback signal., Single feedback observation from environment., Record a feedback signal and update internal distribution. |
| 1623 | [Community 1515](#c-1515) | 4 | 0.29 | core/council/runner.py — AstroCouncil Runner, run_council(), CouncilResult, AstroCouncil |
| 1624 | [Community 1521](#c-1521) | 4 | 0.29 | Called when this node receives a new execution request.         If we are the pr, Primary issues PRE-PREPARE for a validated request., Process a PRE-PREPARE vote (from primary or propagation)., RequestState |
| 1625 | [Community 1534](#c-1534) | 4 | 0.29 | DeterministicInitContainerOrder, r'''     Deterministic init container ordering for pod startup.      Ensures ini, r'''         Get deterministic init container execution order.          Order is, StartupState |
| 1626 | [Community 1058](#c-1058) | 4 | 0.28 | main(), ProofTrace, SymbolicExecutionChecker, ViolationRecord |
| 1627 | [Community 1150](#c-1150) | 4 | 0.27 | Any, ConstraintNode, GuardRule, PolicyCompiler |
| 1628 | [Community 1191](#c-1191) | 4 | 0.25 | Normalize then cap each layer gain individually., Prevents gain explosion across multiple feedback loops.     Normalizes so total, SystemWideGainScheduler, TestSystemWideGainScheduler |
| 1629 | [Community 1382](#c-1382) | 4 | 0.25 | 0° ≤ ν < 360° for all M., e=0.5, M=30° → E ≈ 47.6° (known reference)., Newton-Raphson produces bounded E for all M in [0, 360)., … (+1) |
| 1630 | [Community 1387](#c-1387) | 4 | 0.25 | 0° ≤ ν < 360° for all M., e=0.5, M=30° → E ≈ 47.6° (known reference)., Newton-Raphson produces bounded E for all M in [0, 360)., … (+1) |
| 1631 | [Community 1415](#c-1415) | 4 | 0.25 | 0° ≤ ν < 360° for all M., e=0.5, M=30° → E ≈ 47.6° (known reference)., Newton-Raphson produces bounded E for all M in [0, 360)., … (+1) |
| 1632 | [Community 1451](#c-1451) | 4 | 0.25 | 0° ≤ ν < 360° for all M., e=0.5, M=30° → E ≈ 47.6° (known reference)., Newton-Raphson produces bounded E for all M in [0, 360)., … (+1) |
| 1633 | [Community 1458](#c-1458) | 4 | 0.25 | 0° ≤ ν < 360° for all M., e=0.5, M=30° → E ≈ 47.6° (known reference)., Newton-Raphson produces bounded E for all M in [0, 360)., … (+1) |
| 1634 | [Community 1129](#c-1129) | 4 | 0.24 | K8s-style admission controller.     All decisions flow: decision → constraint →, Primary admission endpoint.         Request:             {                 "deci, Build DecisionContext from raw request., AdmissionController |
| 1635 | [Community 1020](#c-1020) | 4 | 0.23 | Portfolio, Position, PositionSide, trading/portfolio.py — ATOM-STEP-8: Portfolio & Position Tracking ============== |
| 1636 | [Community 1036](#c-1036) | 4 | 0.23 | Portfolio, Position, PositionSide, trading/portfolio.py — ATOM-STEP-8: Portfolio & Position Tracking ============== |
| 1637 | [Community 1052](#c-1052) | 4 | 0.23 | Portfolio, Position, PositionSide, trading/portfolio.py — ATOM-STEP-8: Portfolio & Position Tracking ============== |
| 1638 | [Community 1101](#c-1101) | 4 | 0.23 | Any, get_default_pg_buffer(), PostgresReplayBuffer, db/karl_replay.py — PostgresReplayBuffer (ATOM-019) Stores KARL trajectories in |
| 1639 | [Community 1119](#c-1119) | 4 | 0.23 | Any, get_default_pg_buffer(), PostgresReplayBuffer, db/karl_replay.py — PostgresReplayBuffer (ATOM-019) Stores KARL trajectories in |
| 1640 | [Community 968](#c-968) | 4 | 0.22 | BudgetCycle, ExecutionBudget, ExecutionBudgetController, StageResult |
| 1641 | [Community 987](#c-987) | 4 | 0.22 | GPUMetric, GPUObservabilityLayer, Tracks GPU metrics for observability.     Metrics: gpu_utilization, job_success_, WorkerHealthScore |
| 1642 | [Community 990](#c-990) | 4 | 0.22 | BudgetCycle, ExecutionBudget, ExecutionBudgetController, StageResult |
| 1643 | [Community 1290](#c-1290) | 4 | 0.22 | Observe the result of a control action and update stability state.          Args, Compute oscillation index from gain history.         Uses sign changes and varia, Compute damping factor based on oscillation index.         High oscillation → lo, Compute adaptive gain multiplier.         Reduces gain when oscillating or overs |
| 1644 | [Community 1068](#c-1068) | 4 | 0.20 | ModeEnforcer, ModeLimits, trading/mode.py — ATOM-PRODUCTION: Trading Mode System =========================, TradingMode |
| 1645 | [Community 1089](#c-1089) | 4 | 0.20 | ModeEnforcer, ModeLimits, trading/mode.py — ATOM-PRODUCTION: Trading Mode System =========================, TradingMode |
| 1646 | [Community 1107](#c-1107) | 4 | 0.20 | HeartbeatClient, Probe GPU info (mock for testing), Call after acquiring GPU lock, Call after job finishes |
| 1647 | [Community 1123](#c-1123) | 4 | 0.20 | ModeEnforcer, ModeLimits, trading/mode.py — ATOM-PRODUCTION: Trading Mode System =========================, TradingMode |
| 1648 | [Community 1228](#c-1228) | 4 | 0.20 | SchedulerAdapter, Determine scheduler for job., Compile DAG into executable schedule. Contract-required method., Routes jobs to Slurm or Ray based on workload type. |
| 1649 | [Community 954](#c-954) | 4 | 0.19 | AstroRLConfig, AstroRLLoop, AstroState, core/astro_rl_engine.py - ATOM-STEP-6: Astro RL Engine |
| 1650 | [Community 975](#c-975) | 4 | 0.19 | AstroRLConfig, AstroRLLoop, AstroState, core/astro_rl_engine.py - ATOM-STEP-6: Astro RL Engine |
| 1651 | [Community 983](#c-983) | 4 | 0.19 | AstroRLConfig, AstroRLLoop, AstroState, core/astro_rl_engine.py - ATOM-STEP-6: Astro RL Engine |
| 1652 | [Community 998](#c-998) | 4 | 0.19 | AstroRLConfig, AstroRLLoop, AstroState, core/astro_rl_engine.py - ATOM-STEP-6: Astro RL Engine |
| 1653 | [Community 772](#c-772) | 4 | 0.18 | Topology, TopologyChange, TopologyUpdater, TopologyVersion |
| 1654 | [Community 695](#c-695) | 4 | 0.17 | IncrementalFingerprint, Incremental DAG fingerprint with O(Δnodes) updates.      Only nodes whose conten, A → B, A → C, B → D, … (+2) |
| 1655 | [Community 671](#c-671) | 4 | 0.16 | Monitoring, MonitoringSnapshot, trading/monitoring.py — ATOM-PRODUCTION: Monitoring System =====================, TradeRecord |
| 1656 | [Community 692](#c-692) | 4 | 0.16 | Monitoring, MonitoringSnapshot, trading/monitoring.py — ATOM-PRODUCTION: Monitoring System =====================, TradeRecord |
| 1657 | [Community 722](#c-722) | 4 | 0.16 | Monitoring, MonitoringSnapshot, trading/monitoring.py — ATOM-PRODUCTION: Monitoring System =====================, TradeRecord |
| 1658 | [Community 727](#c-727) | 4 | 0.16 | Monitoring, MonitoringSnapshot, trading/monitoring.py — ATOM-PRODUCTION: Monitoring System =====================, TradeRecord |
| 1659 | [Community 1008](#c-1008) | 4 | 0.16 | Runtime SBS enforcement layer.      Integrates SystemBoundarySpec and GlobalInva, Policy applied when an invariant violation is detected., SBSRuntimeEnforcer, ViolationPolicy |
| 1660 | [Community 837](#c-837) | 4 | 0.14 | BinanceBroker, trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter, Binance spot/futures broker via CCXT., BaseBroker |
| 1661 | [Community 533](#c-533) | 4 | 0.11 | DeterminismGuard, DeterminismViolation, DeterministicIDProvider, DeterministicTimeProvider |
| 1662 | [Community 1871](#c-1871) | 3 | 1.00 | main(), p(), sec() |
| 1663 | [Community 1901](#c-1901) | 3 | 1.00 | create_vlan(), ros_api(), day1-network.sh script |
| 1664 | [Community 1930](#c-1930) | 3 | 1.00 | main(), p(), sec() |
| 1665 | [Community 1956](#c-1956) | 3 | 1.00 | create_vlan(), ros_api(), day1-network.sh script |
| 1666 | [Community 1959](#c-1959) | 3 | 1.00 | day1_network.sh script, create_vlan(), ros_api() |
| 1667 | [Community 1972](#c-1972) | 3 | 1.00 | main(), p(), sec() |
| 1668 | [Community 2000](#c-2000) | 3 | 1.00 | main(), p(), sec() |
| 1669 | [Community 1875](#c-1875) | 3 | 0.83 | agent_test_path(), has_function(), main() |
| 1670 | [Community 1934](#c-1934) | 3 | 0.83 | agent_test_path(), has_function(), main() |
| 1671 | [Community 1960](#c-1960) | 3 | 0.83 | kubeseal-encrypt.sh script, log(), ok() |
| 1672 | [Community 2004](#c-2004) | 3 | 0.83 | agent_test_path(), has_function(), main() |
| 1673 | [Community 2021](#c-2021) | 3 | 0.83 | agent_test_path(), has_function(), main() |
| 1674 | [Community 1874](#c-1874) | 3 | 0.67 | extract_metric_names(), main(), Naively extract metric names from a PromQL expression. |
| 1675 | [Community 1876](#c-1876) | 3 | 0.67 | _changed_files(), main(), Return files changed in the working tree under `scope`. |
| 1676 | [Community 1900](#c-1900) | 3 | 0.67 | datetime, backfill_range(), Reconstruct features from TimescaleDB continuous aggregates.     Queries metrics |
| 1677 | [Community 1933](#c-1933) | 3 | 0.67 | extract_metric_names(), main(), Naively extract metric names from a PromQL expression. |
| 1678 | [Community 1935](#c-1935) | 3 | 0.67 | _changed_files(), main(), Return files changed in the working tree under `scope`. |
| 1679 | [Community 1958](#c-1958) | 3 | 0.67 | Reconstruct features from TimescaleDB continuous aggregates.     Queries metrics, datetime, backfill_range() |
| 1680 | [Community 2003](#c-2003) | 3 | 0.67 | extract_metric_names(), main(), Naively extract metric names from a PromQL expression. |
| 1681 | [Community 2005](#c-2005) | 3 | 0.67 | _changed_files(), main(), Return files changed in the working tree under `scope`. |
| 1682 | [Community 2020](#c-2020) | 3 | 0.67 | extract_metric_names(), main(), Naively extract metric names from a PromQL expression. |
| 1683 | [Community 2022](#c-2022) | 3 | 0.67 | _changed_files(), main(), Return files changed in the working tree under `scope`. |
| 1684 | [Community 2048](#c-2048) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1685 | [Community 2049](#c-2049) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1686 | [Community 2050](#c-2050) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1687 | [Community 2051](#c-2051) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1688 | [Community 2052](#c-2052) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1689 | [Community 2053](#c-2053) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1690 | [Community 2054](#c-2054) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1691 | [Community 2055](#c-2055) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1692 | [Community 2056](#c-2056) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1693 | [Community 2057](#c-2057) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1694 | [Community 2058](#c-2058) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1695 | [Community 2059](#c-2059) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1696 | [Community 2060](#c-2060) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1697 | [Community 2061](#c-2061) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1698 | [Community 2062](#c-2062) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1699 | [Community 2063](#c-2063) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1700 | [Community 2064](#c-2064) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1701 | [Community 2065](#c-2065) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1702 | [Community 2066](#c-2066) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1703 | [Community 2067](#c-2067) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1704 | [Community 2068](#c-2068) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1705 | [Community 2069](#c-2069) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1706 | [Community 2070](#c-2070) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1707 | [Community 2071](#c-2071) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1708 | [Community 2072](#c-2072) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1709 | [Community 2073](#c-2073) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1710 | [Community 2074](#c-2074) | 3 | 0.67 | 2026-05-31, Commits, Environment Health |
| 1711 | [Community 2075](#c-2075) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1712 | [Community 2076](#c-2076) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1713 | [Community 2102](#c-2102) | 3 | 0.67 | health(), HealthResponse, Liveness probe — returns 'alive' when model is loaded. |
| 1714 | [Community 2103](#c-2103) | 3 | 0.67 | 11. FILES TO CREATE / MODIFY, Files to Modify, New Files |
| 1715 | [Community 2115](#c-2115) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1716 | [Community 2116](#c-2116) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1717 | [Community 2117](#c-2117) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1718 | [Community 2118](#c-2118) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1719 | [Community 2119](#c-2119) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1720 | [Community 2120](#c-2120) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1721 | [Community 2121](#c-2121) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1722 | [Community 2122](#c-2122) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1723 | [Community 2123](#c-2123) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1724 | [Community 2124](#c-2124) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1725 | [Community 2125](#c-2125) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1726 | [Community 2126](#c-2126) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1727 | [Community 2127](#c-2127) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1728 | [Community 2128](#c-2128) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1729 | [Community 2129](#c-2129) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1730 | [Community 2130](#c-2130) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1731 | [Community 2131](#c-2131) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1732 | [Community 2132](#c-2132) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1733 | [Community 2133](#c-2133) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1734 | [Community 2134](#c-2134) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1735 | [Community 2135](#c-2135) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1736 | [Community 2136](#c-2136) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1737 | [Community 2137](#c-2137) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1738 | [Community 2138](#c-2138) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1739 | [Community 2139](#c-2139) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1740 | [Community 2140](#c-2140) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1741 | [Community 2141](#c-2141) | 3 | 0.67 | 2026-05-31, Commits, Environment Health |
| 1742 | [Community 2142](#c-2142) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1743 | [Community 2143](#c-2143) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1744 | [Community 2144](#c-2144) | 3 | 0.67 | 2026-06-17, Commits, Environment Health |
| 1745 | [Community 2163](#c-2163) | 3 | 0.67 | ExplainResponse, explain_prediction(), Return SHAP values for a previously made prediction. |
| 1746 | [Community 2176](#c-2176) | 3 | 0.67 | metrics(), Custom application metrics in JSON (Prometheus-style fields)., MetricsResponse |
| 1747 | [Community 2192](#c-2192) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1748 | [Community 2193](#c-2193) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1749 | [Community 2194](#c-2194) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1750 | [Community 2195](#c-2195) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1751 | [Community 2196](#c-2196) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1752 | [Community 2197](#c-2197) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1753 | [Community 2198](#c-2198) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1754 | [Community 2199](#c-2199) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1755 | [Community 2200](#c-2200) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1756 | [Community 2201](#c-2201) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1757 | [Community 2202](#c-2202) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1758 | [Community 2203](#c-2203) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1759 | [Community 2204](#c-2204) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1760 | [Community 2205](#c-2205) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1761 | [Community 2206](#c-2206) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1762 | [Community 2207](#c-2207) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1763 | [Community 2208](#c-2208) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1764 | [Community 2209](#c-2209) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1765 | [Community 2210](#c-2210) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1766 | [Community 2211](#c-2211) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1767 | [Community 2212](#c-2212) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1768 | [Community 2213](#c-2213) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1769 | [Community 2214](#c-2214) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1770 | [Community 2215](#c-2215) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1771 | [Community 2216](#c-2216) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1772 | [Community 2217](#c-2217) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1773 | [Community 2218](#c-2218) | 3 | 0.67 | 2026-05-31, Commits, Environment Health |
| 1774 | [Community 2219](#c-2219) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1775 | [Community 2220](#c-2220) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1776 | [Community 2221](#c-2221) | 3 | 0.67 | 2026-06-17, Commits, Environment Health |
| 1777 | [Community 2222](#c-2222) | 3 | 0.67 | 2026-06-17, Commits, Environment Health |
| 1778 | [Community 2223](#c-2223) | 3 | 0.67 | 2026-06-17, Commits, Environment Health |
| 1779 | [Community 2235](#c-2235) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1780 | [Community 2236](#c-2236) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1781 | [Community 2237](#c-2237) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1782 | [Community 2238](#c-2238) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1783 | [Community 2239](#c-2239) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1784 | [Community 2240](#c-2240) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1785 | [Community 2241](#c-2241) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1786 | [Community 2242](#c-2242) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1787 | [Community 2243](#c-2243) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1788 | [Community 2244](#c-2244) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1789 | [Community 2245](#c-2245) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1790 | [Community 2246](#c-2246) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1791 | [Community 2247](#c-2247) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1792 | [Community 2248](#c-2248) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1793 | [Community 2249](#c-2249) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1794 | [Community 2250](#c-2250) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1795 | [Community 2251](#c-2251) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1796 | [Community 2252](#c-2252) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1797 | [Community 2253](#c-2253) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1798 | [Community 2254](#c-2254) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1799 | [Community 2255](#c-2255) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1800 | [Community 2256](#c-2256) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1801 | [Community 2257](#c-2257) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1802 | [Community 2258](#c-2258) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| 1803 | [Community 2259](#c-2259) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1804 | [Community 2260](#c-2260) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| 1805 | [Community 2261](#c-2261) | 3 | 0.67 | 2026-05-31, Commits, Environment Health |
| 1806 | [Community 2262](#c-2262) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1807 | [Community 2263](#c-2263) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| 1808 | [Community 1692](#c-1692) | 3 | 0.60 | main(), print_table(), run_query() |
| 1809 | [Community 1742](#c-1742) | 3 | 0.60 | main(), print_table(), run_query() |
| 1810 | [Community 1769](#c-1769) | 3 | 0.60 | main(), print_table(), run_query() |
| 1811 | [Community 1785](#c-1785) | 3 | 0.60 | init-kong.sh script, err(), log() |
| 1812 | [Community 1802](#c-1802) | 3 | 0.60 | main(), print_table(), run_query() |
| 1813 | [Community 1596](#c-1596) | 3 | 0.53 | FalsePositiveScenario, OSDState, run() |
| 1814 | [Community 1598](#c-1598) | 3 | 0.53 | ExecutedAction, IdempotencyScenario, run() |
| 1815 | [Community 1638](#c-1638) | 3 | 0.53 | FalsePositiveScenario, OSDState, run() |
| 1816 | [Community 1640](#c-1640) | 3 | 0.53 | ExecutedAction, IdempotencyScenario, run() |
| 1817 | [Community 1842](#c-1842) | 3 | 0.50 | Convert Event.payload to dict. Handles tuple (frozen dataclass) and dict., payload_to_dict(), Any |
| 1818 | [Community 1843](#c-1843) | 3 | 0.50 | Convert Event.payload to dict. Handles tuple (frozen dataclass) and dict., payload_to_dict(), Any |
| 1819 | [Community 1846](#c-1846) | 3 | 0.50 | apply_position_lag_risk(), amre/risk_control.py — ATOM-KARL-015 Phase 5: Risk Controller via position_lag, Adjust position size based on position_lag metric.      Parameters     --------- |
| 1820 | [Community 1847](#c-1847) | 3 | 0.50 | estimate_uncertainty(), amre/uncertainty.py — Uncertainty quantification, Any |
| 1821 | [Community 1850](#c-1850) | 3 | 0.50 | apply_position_lag_risk(), amre/risk_control.py — ATOM-KARL-015 Phase 5: Risk Controller via position_lag, Adjust position size based on position_lag metric.      Parameters     --------- |
| 1822 | [Community 1851](#c-1851) | 3 | 0.50 | estimate_uncertainty(), amre/uncertainty.py — Uncertainty quantification, Any |
| 1823 | [Community 1852](#c-1852) | 3 | 0.50 | Claude instructions for AstroFinSentinelV5, Hermes Agent (via Ollama) can also follow these instructions., See AGENTS.md for the complete project context and AI rules. |
| 1824 | [Community 1853](#c-1853) | 3 | 0.50 | 8. Ограничения: не менять signal., Signal не меняется после apply_pressure_field., TestConstraints |
| 1825 | [Community 1854](#c-1854) | 3 | 0.50 | core/council/runner.py — AstroCouncil Runner, run_council(), CouncilResult |
| 1826 | [Community 1855](#c-1855) | 3 | 0.50 | Метрики производительности агентов., Декоратор, замеряющий время выполнения агента., track_agent_duration() |
| 1827 | [Community 1856](#c-1856) | 3 | 0.50 | is_redis_backed(), Rate limiting configuration with optional Redis backend., Return True if rate limiter is using Redis. |
| 1828 | [Community 1857](#c-1857) | 3 | 0.50 | compute_astro_reward(), core/reward/astro_reward.py — ATOM-REWARD-001: Astro-Based Reward  Astro-based r, Compute astro-based reward component.      Parameters     ----------     muhurta |
| 1829 | [Community 1858](#c-1858) | 3 | 0.50 | Инициализация OpenTelemetry с экспортом в Jaeger (OTLP gRPC). Добавлено автомати, setup_tracing(), Tracer |
| 1830 | [Community 1860](#c-1860) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-25, Источники, Топ-3 за сегодня |
| 1831 | [Community 1861](#c-1861) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-26, Источники, Топ-3 за последние 7 дней |
| 1832 | [Community 1862](#c-1862) | 3 | 0.50 | Multi-Agent AI Daily Digest, Источники мониторинга, Топ-3 за сегодня |
| 1833 | [Community 1863](#c-1863) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-01, Источники мониторинга, Топ-3 за сегодня |
| 1834 | [Community 1864](#c-1864) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-08, Источники, Топ-3 за сегодня |
| 1835 | [Community 1865](#c-1865) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-15, Источники, Топ-3 за сегодня |
| 1836 | [Community 1866](#c-1866) | 3 | 0.50 | Multi-Agent AI Daily — 2026-05-29, Источники, Топ-3 за сегодня |
| 1837 | [Community 1867](#c-1867) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-05, Топ-3 за неделю |
| 1838 | [Community 1868](#c-1868) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-06, Топ-3 за неделю |
| 1839 | [Community 1869](#c-1869) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-07, Топ-3 за неделю |
| 1840 | [Community 1870](#c-1870) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-11, Топ-3 за неделю |
| 1841 | [Community 1872](#c-1872) | 3 | 0.50 | meta_rl/distributed/types.py -- ATOM-META-RL-024: Worker task types, StrategyTask, WorkerResult |
| 1842 | [Community 1873](#c-1873) | 3 | 0.50 | generate_all_charts(), meta_rl/visualization.py — ATOM-META-RL-011: Evolution Charts, Generate all evolution visualization charts.      Returns dict of chart_name → o |
| 1843 | [Community 1881](#c-1881) | 3 | 0.50 | Phase 1 cleanup validation tests., Проверяем, что core.auth импортируется без ошибок., test_core_auth_importable() |
| 1844 | [Community 1886](#c-1886) | 3 | 0.50 | evolution_tab(), web/components/evolution.py — Evolution tab (ATOM-META-RL-004)  Enhanced with re, Div |
| 1845 | [Community 1887](#c-1887) | 3 | 0.50 | web/components/sessions.py — Sessions tab (ATOM-META-RL-004), sessions_tab(), Div |
| 1846 | [Community 1888](#c-1888) | 3 | 0.50 | list_conflicts(), web/data_room.py  Data Room API endpoints., Return conflict journal contents as JSON. |
| 1847 | [Community 1889](#c-1889) | 3 | 0.50 | web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004), Register all Sessions tab callbacks., register_sessions_callbacks() |
| 1848 | [Community 1896](#c-1896) | 3 | 0.50 | evolution_tab(), web/components/evolution.py — Evolution tab (ATOM-META-RL-004)  Enhanced with re, Div |
| 1849 | [Community 1897](#c-1897) | 3 | 0.50 | web/components/sessions.py — Sessions tab (ATOM-META-RL-004), sessions_tab(), Div |
| 1850 | [Community 1898](#c-1898) | 3 | 0.50 | web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004), Register all Sessions tab callbacks., register_sessions_callbacks() |
| 1851 | [Community 1909](#c-1909) | 3 | 0.50 | apply_position_lag_risk(), amre/risk_control.py — ATOM-KARL-015 Phase 5: Risk Controller via position_lag, Adjust position size based on position_lag metric.      Parameters     --------- |
| 1852 | [Community 1910](#c-1910) | 3 | 0.50 | estimate_uncertainty(), amre/uncertainty.py — Uncertainty quantification, Any |
| 1853 | [Community 1911](#c-1911) | 3 | 0.50 | Claude instructions for AstroFinSentinelV5, Hermes Agent (via Ollama) can also follow these instructions., See AGENTS.md for the complete project context and AI rules. |
| 1854 | [Community 1912](#c-1912) | 3 | 0.50 | 7.2 Консенсус: BUY + BUY усиливают друг друга., Консенсус: оба усиливаются.         A(BUY, eff=60) ← B(BUY, eff=75): score = +0., TestConsensus |
| 1855 | [Community 1913](#c-1913) | 3 | 0.50 | core/council/runner.py — AstroCouncil Runner, run_council(), CouncilResult |
| 1856 | [Community 1914](#c-1914) | 3 | 0.50 | Метрики производительности агентов., Декоратор, замеряющий время выполнения агента., track_agent_duration() |
| 1857 | [Community 1915](#c-1915) | 3 | 0.50 | is_redis_backed(), Rate limiting configuration with optional Redis backend., Return True if rate limiter is using Redis. |
| 1858 | [Community 1916](#c-1916) | 3 | 0.50 | compute_astro_reward(), core/reward/astro_reward.py — ATOM-REWARD-001: Astro-Based Reward  Astro-based r, Compute astro-based reward component.      Parameters     ----------     muhurta |
| 1859 | [Community 1917](#c-1917) | 3 | 0.50 | Инициализация OpenTelemetry с экспортом в Jaeger (OTLP gRPC). Добавлено автомати, setup_tracing(), Tracer |
| 1860 | [Community 1919](#c-1919) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-25, Источники, Топ-3 за сегодня |
| 1861 | [Community 1920](#c-1920) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-26, Источники, Топ-3 за последние 7 дней |
| 1862 | [Community 1921](#c-1921) | 3 | 0.50 | Multi-Agent AI Daily Digest, Источники мониторинга, Топ-3 за сегодня |
| 1863 | [Community 1922](#c-1922) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-01, Источники мониторинга, Топ-3 за сегодня |
| 1864 | [Community 1923](#c-1923) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-08, Источники, Топ-3 за сегодня |
| 1865 | [Community 1924](#c-1924) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-15, Источники, Топ-3 за сегодня |
| 1866 | [Community 1925](#c-1925) | 3 | 0.50 | Multi-Agent AI Daily — 2026-05-29, Источники, Топ-3 за сегодня |
| 1867 | [Community 1926](#c-1926) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-05, Топ-3 за неделю |
| 1868 | [Community 1927](#c-1927) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-06, Топ-3 за неделю |
| 1869 | [Community 1928](#c-1928) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-07, Топ-3 за неделю |
| 1870 | [Community 1929](#c-1929) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-11, Топ-3 за неделю |
| 1871 | [Community 1931](#c-1931) | 3 | 0.50 | meta_rl/distributed/types.py -- ATOM-META-RL-024: Worker task types, StrategyTask, WorkerResult |
| 1872 | [Community 1932](#c-1932) | 3 | 0.50 | generate_all_charts(), meta_rl/visualization.py — ATOM-META-RL-011: Evolution Charts, Generate all evolution visualization charts.      Returns dict of chart_name → o |
| 1873 | [Community 1940](#c-1940) | 3 | 0.50 | Phase 1 cleanup validation tests., Проверяем, что core.auth импортируется без ошибок., test_core_auth_importable() |
| 1874 | [Community 1945](#c-1945) | 3 | 0.50 | evolution_tab(), web/components/evolution.py — Evolution tab (ATOM-META-RL-004)  Enhanced with re, Div |
| 1875 | [Community 1946](#c-1946) | 3 | 0.50 | web/components/sessions.py — Sessions tab (ATOM-META-RL-004), sessions_tab(), Div |
| 1876 | [Community 1947](#c-1947) | 3 | 0.50 | list_conflicts(), web/data_room.py  Data Room API endpoints., Return conflict journal contents as JSON. |
| 1877 | [Community 1948](#c-1948) | 3 | 0.50 | web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004), Register all Sessions tab callbacks., register_sessions_callbacks() |
| 1878 | [Community 1949](#c-1949) | 3 | 0.50 | Notes, Role: ceph, Variables |
| 1879 | [Community 1950](#c-1950) | 3 | 0.50 | Claude instructions for AstroFinSentinelV5, Hermes Agent (via Ollama) can also follow these instructions., See AGENTS.md for the complete project context and AI rules. |
| 1880 | [Community 1951](#c-1951) | 3 | 0.50 | 7.3 Outlier: SELL не игнорируется., SELL не игнорируется, BUY теряет confidence.          A(BUY, eff=70) ← B(BUY, ef, … (+1) |
| 1881 | [Community 1952](#c-1952) | 3 | 0.50 | Метрики производительности агентов., Декоратор, замеряющий время выполнения агента., track_agent_duration() |
| 1882 | [Community 1953](#c-1953) | 3 | 0.50 | is_redis_backed(), Rate limiting configuration with optional Redis backend., Return True if rate limiter is using Redis. |
| 1883 | [Community 1954](#c-1954) | 3 | 0.50 | compute_astro_reward(), core/reward/astro_reward.py — ATOM-REWARD-001: Astro-Based Reward  Astro-based r, Compute astro-based reward component.      Parameters     ----------     muhurta |
| 1884 | [Community 1955](#c-1955) | 3 | 0.50 | Инициализация OpenTelemetry с экспортом в Jaeger (OTLP gRPC). Добавлено автомати, setup_tracing(), Tracer |
| 1885 | [Community 1961](#c-1961) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-25, Источники, Топ-3 за сегодня |
| 1886 | [Community 1962](#c-1962) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-26, Источники, Топ-3 за последние 7 дней |
| 1887 | [Community 1963](#c-1963) | 3 | 0.50 | Multi-Agent AI Daily Digest, Источники мониторинга, Топ-3 за сегодня |
| 1888 | [Community 1964](#c-1964) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-01, Источники мониторинга, Топ-3 за сегодня |
| 1889 | [Community 1965](#c-1965) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-08, Источники, Топ-3 за сегодня |
| 1890 | [Community 1966](#c-1966) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-15, Источники, Топ-3 за сегодня |
| 1891 | [Community 1967](#c-1967) | 3 | 0.50 | Multi-Agent AI Daily — 2026-05-29, Источники, Топ-3 за сегодня |
| 1892 | [Community 1968](#c-1968) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-05, Топ-3 за неделю |
| 1893 | [Community 1969](#c-1969) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-06, Топ-3 за неделю |
| 1894 | [Community 1970](#c-1970) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-07, Топ-3 за неделю |
| 1895 | [Community 1971](#c-1971) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-11, Топ-3 за неделю |
| 1896 | [Community 1973](#c-1973) | 3 | 0.50 | meta_rl/distributed/types.py -- ATOM-META-RL-024: Worker task types, StrategyTask, WorkerResult |
| 1897 | [Community 1974](#c-1974) | 3 | 0.50 | generate_all_charts(), meta_rl/visualization.py — ATOM-META-RL-011: Evolution Charts, Generate all evolution visualization charts.      Returns dict of chart_name → o |
| 1898 | [Community 1977](#c-1977) | 3 | 0.50 | AtomNodeStub, Minimal node-to-node message contract, Constructor.          Args:             channel: A grpc.Channel. |
| 1899 | [Community 1978](#c-1978) | 3 | 0.50 | apply_position_lag_risk(), amre/risk_control.py — ATOM-KARL-015 Phase 5: Risk Controller via position_lag, Adjust position size based on position_lag metric.      Parameters     --------- |
| 1900 | [Community 1979](#c-1979) | 3 | 0.50 | estimate_uncertainty(), amre/uncertainty.py — Uncertainty quantification, Any |
| 1901 | [Community 1980](#c-1980) | 3 | 0.50 | Claude instructions for AstroFinSentinelV5, Hermes Agent (via Ollama) can also follow these instructions., See AGENTS.md for the complete project context and AI rules. |
| 1902 | [Community 1981](#c-1981) | 3 | 0.50 | 8. Ограничения: не менять signal., Signal не меняется после apply_pressure_field., TestConstraints |
| 1903 | [Community 1982](#c-1982) | 3 | 0.50 | 7.3 Outlier: SELL не игнорируется., SELL не игнорируется, BUY теряет confidence.          A(BUY, eff=70) ← B(BUY, ef, … (+1) |
| 1904 | [Community 1983](#c-1983) | 3 | 0.50 | core/council/runner.py — AstroCouncil Runner, run_council(), CouncilResult |
| 1905 | [Community 1984](#c-1984) | 3 | 0.50 | Метрики производительности агентов., Декоратор, замеряющий время выполнения агента., track_agent_duration() |
| 1906 | [Community 1985](#c-1985) | 3 | 0.50 | is_redis_backed(), Rate limiting configuration with optional Redis backend., Return True if rate limiter is using Redis. |
| 1907 | [Community 1986](#c-1986) | 3 | 0.50 | compute_astro_reward(), core/reward/astro_reward.py — ATOM-REWARD-001: Astro-Based Reward  Astro-based r, Compute astro-based reward component.      Parameters     ----------     muhurta |
| 1908 | [Community 1987](#c-1987) | 3 | 0.50 | Инициализация OpenTelemetry с экспортом в Jaeger (OTLP gRPC). Добавлено автомати, setup_tracing(), Tracer |
| 1909 | [Community 1989](#c-1989) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-25, Источники, Топ-3 за сегодня |
| 1910 | [Community 1990](#c-1990) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-26, Источники, Топ-3 за последние 7 дней |
| 1911 | [Community 1991](#c-1991) | 3 | 0.50 | Multi-Agent AI Daily Digest, Источники мониторинга, Топ-3 за сегодня |
| 1912 | [Community 1992](#c-1992) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-01, Источники мониторинга, Топ-3 за сегодня |
| 1913 | [Community 1993](#c-1993) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-08, Источники, Топ-3 за сегодня |
| 1914 | [Community 1994](#c-1994) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-15, Источники, Топ-3 за сегодня |
| 1915 | [Community 1995](#c-1995) | 3 | 0.50 | Multi-Agent AI Daily — 2026-05-29, Источники, Топ-3 за сегодня |
| 1916 | [Community 1996](#c-1996) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-05, Топ-3 за неделю |
| 1917 | [Community 1997](#c-1997) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-06, Топ-3 за неделю |
| 1918 | [Community 1998](#c-1998) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-07, Топ-3 за неделю |
| 1919 | [Community 1999](#c-1999) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-11, Топ-3 за неделю |
| 1920 | [Community 2001](#c-2001) | 3 | 0.50 | meta_rl/distributed/types.py -- ATOM-META-RL-024: Worker task types, StrategyTask, WorkerResult |
| 1921 | [Community 2002](#c-2002) | 3 | 0.50 | generate_all_charts(), meta_rl/visualization.py — ATOM-META-RL-011: Evolution Charts, Generate all evolution visualization charts.      Returns dict of chart_name → o |
| 1922 | [Community 2010](#c-2010) | 3 | 0.50 | Phase 1 cleanup validation tests., Проверяем, что core.auth импортируется без ошибок., test_core_auth_importable() |
| 1923 | [Community 2015](#c-2015) | 3 | 0.50 | evolution_tab(), web/components/evolution.py — Evolution tab (ATOM-META-RL-004)  Enhanced with re, Div |
| 1924 | [Community 2016](#c-2016) | 3 | 0.50 | web/components/sessions.py — Sessions tab (ATOM-META-RL-004), sessions_tab(), Div |
| 1925 | [Community 2017](#c-2017) | 3 | 0.50 | list_conflicts(), web/data_room.py  Data Room API endpoints., Return conflict journal contents as JSON. |
| 1926 | [Community 2018](#c-2018) | 3 | 0.50 | web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004), Register all Sessions tab callbacks., register_sessions_callbacks() |
| 1927 | [Community 2019](#c-2019) | 3 | 0.50 | Architecture, Role: ray, Test |
| 1928 | [Community 2027](#c-2027) | 3 | 0.50 | Phase 1 cleanup validation tests., Проверяем, что core.auth импортируется без ошибок., test_core_auth_importable() |
| 1929 | [Community 2032](#c-2032) | 3 | 0.50 | evolution_tab(), web/components/evolution.py — Evolution tab (ATOM-META-RL-004)  Enhanced with re, Div |
| 1930 | [Community 2033](#c-2033) | 3 | 0.50 | web/components/sessions.py — Sessions tab (ATOM-META-RL-004), sessions_tab(), Div |
| 1931 | [Community 2034](#c-2034) | 3 | 0.50 | list_conflicts(), web/data_room.py  Data Room API endpoints., Return conflict journal contents as JSON. |
| 1932 | [Community 2035](#c-2035) | 3 | 0.50 | web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004), Register all Sessions tab callbacks., register_sessions_callbacks() |
| 1933 | [Community 2036](#c-2036) | 3 | 0.50 | Role: wireguard, Usage, Variables |
| 1934 | [Community 1597](#c-1597) | 3 | 0.47 | Decision, GovernanceFailureScenario, run() |
| 1935 | [Community 1639](#c-1639) | 3 | 0.47 | Decision, GovernanceFailureScenario, run() |
| 1936 | [Community 1396](#c-1396) | 3 | 0.43 | MLRiskIgnoredScenario, Node, run() |
| 1937 | [Community 1429](#c-1429) | 3 | 0.43 | MLRiskIgnoredScenario, Node, run() |
| 1938 | [Community 1600](#c-1600) | 3 | 0.40 | Path, Trainer, Full training pipeline: build → split → train → evaluate → register.          Re |
| 1939 | [Community 1616](#c-1616) | 3 | 0.40 | meta_rl/quant/regime.py -- ATOM-META-RL-024: Market regime detection, Regime, RegimeDetector |
| 1940 | [Community 1622](#c-1622) | 3 | 0.40 | build(), Benchmark diversity_filter at n=1000 candidates x n=1000 pool., ScoredStrategy_shim |
| 1941 | [Community 1655](#c-1655) | 3 | 0.40 | meta_rl/quant/regime.py -- ATOM-META-RL-024: Market regime detection, Regime, RegimeDetector |
| 1942 | [Community 1671](#c-1671) | 3 | 0.40 | meta_rl/quant/regime.py -- ATOM-META-RL-024: Market regime detection, Regime, RegimeDetector |
| 1943 | [Community 1684](#c-1684) | 3 | 0.40 | CounterfactualEngine, amre/counterfactual.py — Counterfactual reasoning, Any |
| 1944 | [Community 1689](#c-1689) | 3 | 0.40 | CounterfactualEngine, amre/counterfactual.py — Counterfactual reasoning, Any |
| 1945 | [Community 1707](#c-1707) | 3 | 0.40 | DecisionLogger, meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail, AutonomousDecision |
| 1946 | [Community 1729](#c-1729) | 3 | 0.40 | CandidateGenerator, Returns list of (node_id, score) for top-k candidates.         Score = base_scor, Layer 1: Generate k-best candidate placements per job.     Uses ML risk scores f |
| 1947 | [Community 1739](#c-1739) | 3 | 0.40 | CounterfactualEngine, amre/counterfactual.py — Counterfactual reasoning, Any |
| 1948 | [Community 1757](#c-1757) | 3 | 0.40 | DecisionLogger, meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail, AutonomousDecision |
| 1949 | [Community 1776](#c-1776) | 3 | 0.40 | PreparedCertificate, Return PreparedCertificate if quorum reached, else None., Proof that ≥ 2f+1 nodes have prepared the request. |
| 1950 | [Community 1777](#c-1777) | 3 | 0.40 | CommitCertificate, Finalize the commit. Returns CommitCertificate for the distributed ledger., Proof that the request is irreversibly committed. |
| 1951 | [Community 1795](#c-1795) | 3 | 0.40 | DecisionLogger, meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail, AutonomousDecision |
| 1952 | [Community 1796](#c-1796) | 3 | 0.40 | EvaluationResult, reward > reward_clip_max is clipped down to the ceiling.          The default pe, reward < reward_clip_min is clipped up to the floor.          Symmetric counterp |
| 1953 | [Community 1799](#c-1799) | 3 | 0.40 | CounterfactualEngine, amre/counterfactual.py — Counterfactual reasoning, Any |
| 1954 | [Community 1816](#c-1816) | 3 | 0.40 | DecisionLogger, meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail, AutonomousDecision |
| 1955 | [Community 1317](#c-1317) | 3 | 0.39 | EnvelopeBounds, StabilityEnvelope, EnvelopeReport |
| 1956 | [Community 1395](#c-1395) | 3 | 0.39 | Any, compute_deterministic_hash(), HashChain |
| 1957 | [Community 1147](#c-1147) | 3 | 0.38 | DAGCompiler, DAGNode, Compiles job submissions into executable DAGs.     Guarantees: every node has ex |
| 1958 | [Community 1484](#c-1484) | 3 | 0.38 | ConstraintCompiler, ConstraintType, Injects governance constraints into DAG as executable nodes.     L9 is NOT optio |
| 1959 | [Community 1512](#c-1512) | 3 | 0.38 | Invoice, InvoicingEngine, ROMA Invoicing — Invoice generation, payment tracking. |
| 1960 | [Community 1514](#c-1514) | 3 | 0.38 | Injects governance constraints into DAG as executable nodes.     L9 is NOT optio, ConstraintCompiler, ConstraintType |
| 1961 | [Community 1520](#c-1520) | 3 | 0.38 | MarketplaceListing, PluginMarketplace, ROMA Plugin Marketplace — Publishing, signing, lifecycle governance. |
| 1962 | [Community 1537](#c-1537) | 3 | 0.38 | Fraction of plans that have eval_score events (0..1)., Fraction of consecutive eval scores within ±0.1 (0..1)., Composite trace health score (0..1).          Combines:           - completeness |
| 1963 | [Community 1152](#c-1152) | 3 | 0.33 | DriftSample, run(), StateDriftScenario |
| 1964 | [Community 1186](#c-1186) | 3 | 0.33 | DriftSample, run(), StateDriftScenario |
| 1965 | [Community 1463](#c-1463) | 3 | 0.33 | HierarchicalPolicy, amre/hierarchical_policy.py — Hierarchical Policy + Regime Detection, Any |
| 1966 | [Community 1464](#c-1464) | 3 | 0.33 | HierarchicalPolicy, amre/hierarchical_policy.py — Hierarchical Policy + Regime Detection, Any |
| 1967 | [Community 1495](#c-1495) | 3 | 0.33 | HierarchicalPolicy, amre/hierarchical_policy.py — Hierarchical Policy + Regime Detection, Any |
| 1968 | [Community 1539](#c-1539) | 3 | 0.33 | HierarchicalPolicy, amre/hierarchical_policy.py — Hierarchical Policy + Regime Detection, Any |
| 1969 | [Community 1565](#c-1565) | 3 | 0.33 | Deserialize from dict., Добавить запись решения, Импорт записей из JSON |
| 1970 | [Community 1567](#c-1567) | 3 | 0.33 | Deserialize from dict., Добавить запись решения, Импорт записей из JSON |
| 1971 | [Community 1593](#c-1593) | 3 | 0.33 | Feature, FeatureFunc, Typed feature with name, description, unit. |
| 1972 | [Community 1603](#c-1603) | 3 | 0.33 | Deserialize from dict., Добавить запись решения, Импорт записей из JSON |
| 1973 | [Community 1625](#c-1625) | 3 | 0.33 | Compute fingerprint from node list.          If prev_fp is provided and a node h, Kahn's algorithm + layer assignment.         Returns node_id → layer (position i, Root hash = SHA256 of all node hashes concatenated in topological order. |
| 1974 | [Community 1631](#c-1631) | 3 | 0.33 | Typed feature with name, description, unit., Feature, FeatureFunc |
| 1975 | [Community 1423](#c-1423) | 3 | 0.32 | BFTQCBuilder, ✅ BFTQCBuilder builds QC only when threshold reached., test_bftqc_builder_threshold() |
| 1976 | [Community 1182](#c-1182) | 3 | 0.31 | AuthMiddleware, Unified auth middleware — API Key + optional JWT., Request |
| 1977 | [Community 1226](#c-1226) | 3 | 0.29 | PostgresTraceStorage, ACOS PostgreSQL Storage Backend — primary persistent storage., PostgreSQL-backed trace storage. Requires DATABASE_URL env var. |
| 1978 | [Community 1255](#c-1255) | 3 | 0.29 | PostgresTraceStorage, ACOS PostgreSQL Storage Backend — primary persistent storage., PostgreSQL-backed trace storage. Requires DATABASE_URL env var. |
| 1979 | [Community 1393](#c-1393) | 3 | 0.29 | Decision, GovernanceGate, L8 + L9 mandatory gate. NO execution without approval.     Every DAG passes thro |
| 1980 | [Community 1403](#c-1403) | 3 | 0.29 | BeamPruner, PrunedCandidate, Prunes candidate space using beam search with variance estimation.     score = E |
| 1981 | [Community 1434](#c-1434) | 3 | 0.29 | BeamPruner, PrunedCandidate, Prunes candidate space using beam search with variance estimation.     score = E |
| 1982 | [Community 1476](#c-1476) | 3 | 0.29 | tests/architecture/test_validate_agent.py ======================================, The template is hand-written to pass all 9 checks., test_validator_passes_on_template() |
| 1983 | [Community 1488](#c-1488) | 3 | 0.29 | FeedbackCollector, Pull completed jobs from PostgreSQL state_store, write to TimescaleDB.         R, Record a single job outcome to TimescaleDB for ML training. |
| 1984 | [Community 1507](#c-1507) | 3 | 0.29 | tests/architecture/test_validate_agent.py ======================================, The template is hand-written to pass all 9 checks., test_validator_passes_on_template() |
| 1985 | [Community 1522](#c-1522) | 3 | 0.29 | Pull completed jobs from PostgreSQL state_store, write to TimescaleDB.         R, Record a single job outcome to TimescaleDB for ML training., FeedbackCollector |
| 1986 | [Community 1552](#c-1552) | 3 | 0.29 | tests/architecture/test_validate_agent.py ======================================, The template is hand-written to pass all 9 checks., test_validator_passes_on_template() |
| 1987 | [Community 1560](#c-1560) | 3 | 0.29 | tests/architecture/test_validate_agent.py ======================================, The template is hand-written to pass all 9 checks., test_validator_passes_on_template() |
| 1988 | [Community 1046](#c-1046) | 3 | 0.27 | TestStabilityGovernor, GovernorThresholds, Tunable thresholds for the stability governor. |
| 1989 | [Community 1189](#c-1189) | 3 | 0.27 | ControlArbitrator, Resolves competing actuator signals across control layers:     DRL / SBS / Coher, TestControlArbitratorBasics |
| 1990 | [Community 1318](#c-1318) | 3 | 0.25 | Any, ExecutionGateway, AtomicQueue |
| 1991 | [Community 1441](#c-1441) | 3 | 0.25 | _drawdown_penalty: scale * dd^2 with NaN/Inf fallback., Quadratic: dd = 0.5 → scale * 0.25., TestDrawdownPenalty |
| 1992 | [Community 1006](#c-1006) | 3 | 0.24 | mock_response(), Integration tests for AstroCouncilAgent aggregation logic., TestAstroCouncilBasic |
| 1993 | [Community 1009](#c-1009) | 3 | 0.24 | mock_response(), Integration tests for AstroCouncilAgent aggregation logic., TestAstroCouncilBasic |
| 1994 | [Community 1070](#c-1070) | 3 | 0.24 | Event, EventLog, Append-only log with O(1) trace index. |
| 1995 | [Community 1105](#c-1105) | 3 | 0.24 | Append-only log with O(1) trace index., Event, EventLog |
| 1996 | [Community 1251](#c-1251) | 3 | 0.24 | PluginMetadata, PluginRegistry, ROMA Plugin Registry — Discovery, versioning, dependency resolution. |
| 1997 | [Community 895](#c-895) | 3 | 0.22 | mock_response(), Integration tests for AstroCouncilAgent aggregation logic., TestAstroCouncilBasic |
| 1998 | [Community 914](#c-914) | 3 | 0.22 | mock_response(), Integration tests for AstroCouncilAgent aggregation logic., TestAstroCouncilBasic |
| 1999 | [Community 962](#c-962) | 3 | 0.22 | Any, DeterminismController, ExecutionContext |
| 2000 | [Community 988](#c-988) | 3 | 0.22 | Any, DeterminismController, ExecutionContext |
| 2001 | [Community 1283](#c-1283) | 3 | 0.22 | Update this node's layer state snapshot., Evaluate invariants across quorum of nodes.          peer_states: {, SBSDistributedClient |
| 2002 | [Community 1349](#c-1349) | 3 | 0.22 | meta_rl/test_reward.py — Golden tests for RewardCalculator.  Golden tests that p, _execution_cost_penalty: clipped cost., TestExecutionCostPenalty |
| 2003 | [Community 793](#c-793) | 3 | 0.21 | MetricPoint, PrometheusCollector, TimescaleWriter |
| 2004 | [Community 813](#c-813) | 3 | 0.21 | MetricPoint, PrometheusCollector, TimescaleWriter |
| 2005 | [Community 1233](#c-1233) | 3 | 0.20 | v7.5 — Control Orchestration Layer Deterministic supervisory arbitration over al, ControlSignal, Return all signals sorted by priority (highest first), no clear. |
| 2006 | [Community 1265](#c-1265) | 3 | 0.20 | _sharpe_component: logistic over clipped Sharpe., Closed-form: 1 / (1 + exp(-steepness * clip(s, ±clip)))., TestSharpeComponent |
| 2007 | [Community 1056](#c-1056) | 3 | 0.19 | test_application_fee(), AsyncWebhookQueue, calculate_application_fee() |
| 2008 | [Community 1145](#c-1145) | 3 | 0.18 | MemoryTraceStorage, Thread-safe in-memory storage with idempotency support., Idempotency check — O(1) lookup. Patch 2. |
| 2009 | [Community 1183](#c-1183) | 3 | 0.18 | MemoryTraceStorage, Thread-safe in-memory storage with idempotency support., Idempotency check — O(1) lookup. Patch 2. |
| 2010 | [Community 1029](#c-1029) | 3 | 0.17 | ClusterState, NodeState, ATOMCluster controller — custom ATOM state snapshot. |
| 2011 | [Community 916](#c-916) | 3 | 0.15 | BinanceBroker, trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter, Binance spot/futures broker via CCXT. |
| 2012 | [Community 943](#c-943) | 3 | 0.15 | BinanceBroker, trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter, Binance spot/futures broker via CCXT. |
| 2013 | [Community 947](#c-947) | 3 | 0.15 | BinanceBroker, trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter, Binance spot/futures broker via CCXT. |
| 2014 | [Community 760](#c-760) | 3 | 0.14 | Return list of dead worker IDs, WorkerRegistry, WorkerStatus |
| 2015 | [Community 933](#c-933) | 3 | 0.13 | test_observability.py — planning_observability layer tests. All 30 tests for tra, DriftProfiler: degradation detection., TestDriftProfiler |
| 2016 | [Community 517](#c-517) | 3 | 0.11 | _MockAsyncExecutionEngine, _MockExecutionLoop, _MockSwarmEngine |
| 2017 | [Community 560](#c-560) | 3 | 0.11 | _MockAsyncExecutionEngine, _MockExecutionLoop, _MockSwarmEngine |

---

## Top 50 Communities (full detail)

<a id="c-1"></a>
### Community 1 — "Community 1"
Cohesion: 0.01
Nodes (235): SignalDirection, RAGRetriever, SignalDirection, _load_weights(), AstroFin Sentinel v5 — Synthesis Agent AstroCouncil: координатор всех агентов, ф, SynthesisAgent = Координатор финального синтеза.          Получает сигналы от ВС, Финальный синтез всех агентов.                  Args:             state: Sentine, Get attribute or dict key from signal (handles both AgentResponse and dict). (+227 more)

<a id="c-0"></a>
### Community 0 — "Community 0"
Cohesion: 0.01
Nodes (227): AgentResponse, AstroCouncilAgent, _build_agent_weights(), AstroFin Sentinel v5 — AstroCouncil Agent Главный координатор всех аналитических, Параллельно запускает Thompson-selected суб-агентов.          If context contain, Регистрация всех суб-агентов., Критичный вызов Swiss Ephemeris., Runner для оркестратора. (+219 more)

<a id="c-2"></a>
### Community 2 — "Community 2"
Cohesion: 0.02
Nodes (127): AgentResponse, Any, CompromiseAgent, _next_long(), _next_short(), Compromise Agent — explicit trade-off resolver for conflicting agent signals.  W, Public entry point. Wraps `analyze` with the latency histogram         and a def, Fallback when no real conflict exists (defer to SynthesisAgent). (+119 more)

<a id="c-4"></a>
### Community 4 — "Community 4"
Cohesion: 0.02
Nodes (115): agents._impl.types — Unified types for AstroFin Sentinel v5., Map signal to numeric score for weighted calculation., Final trading signal from weighted agent responses., Signal, TradingSignal, ADLRState, all_reachable_states(), COROLLARIES (+107 more)

<a id="c-6"></a>
### Community 6 — "Community 6"
Cohesion: 0.02
Nodes (88): Any, AtomicLedgerWriter, Append entry to WAL file.         WAL is fsync'd to ensure durability., Get hash of last committed entry (or GENESIS for empty)., Compute deterministic hash of WAL entry., Replay WAL file on startup to recover committed entries.         Called only whe, Return all entries from from_tick onwards.         Thread-safe read (makes copy), Get entry at specific tick.                  Args:             tick: Tick to loo (+80 more)

<a id="c-11"></a>
### Community 11 — "Community 11"
Cohesion: 0.04
Nodes (83): AlignmentSnapshot, PolicyAction, BudgetDecision, CoherenceViolation, Raised when S-CI is violated (hard gate triggered)., StabilizerSnapshot, _decision_distance(), v6.8 — Temporal Coherence Smoother.  Prevents oscillation between consecutive de (+75 more)

<a id="c-26"></a>
### Community 26 — "Community 26"
Cohesion: 0.04
Nodes (79): AgentBelief, AgentBeliefHistory, AgentPool, AgentSelectionLog, AgentSignal, AstroPosition, AuditLogRecord, BacktestRun (+71 more)

<a id="c-8"></a>
### Community 8 — "Community 8"
Cohesion: 0.03
Nodes (74): QuorumCertificate, Any, QuorumCertificate, VoteRecord, Any, VoteRecord, ConsensusRound, NodeRole (+66 more)

<a id="c-17"></a>
### Community 17 — "Community 17"
Cohesion: 0.03
Nodes (73): Any, BasketMetrics, BasketEvaluator, correlation_penalty_matrix(), diversification_bonus(), meta_rl/basket.py -- ATOM-META-RL-010: Multi-symbol Basket Evaluation, Evaluate a strategy across a basket of assets.          Args:             strate, Aggregate multiple equity curves (equal weight, normalized). (+65 more)

<a id="c-13"></a>
### Community 13 — "Community 13"
Cohesion: 0.03
Nodes (72): Call, Any, ExecutionGateway, ExecutionGateway, Single mandatory entry point for ALL state mutations., MutationExecutor, MutationExecutor, MutationPayload (+64 more)

<a id="c-10"></a>
### Community 10 — "Community 10"
Cohesion: 0.04
Nodes (71): CausalOrderDriftDetector, CompositeDriftReport, DriftEngine, DriftSeverity, DriftType, ExecutedNode, ExecutionTrace, Layer1Result (+63 more)

<a id="c-18"></a>
### Community 18 — "Community 18"
Cohesion: 0.03
Nodes (71): AgentResponse, BullResearcherAgent, Bull Researcher Agent — bullish case for trading opportunities., Public entry point. Wraps analyze() with the latency histogram         and defen, Fetch OHLCV data from OKX asynchronously., Detect bullish candlestick patterns., BullResearcher — ищет бычий кейс для актива.      Responsibilities:     1. Scan, Analyze volume for bullish confirmation. (+63 more)

<a id="c-7"></a>
### Community 7 — "Community 7"
Cohesion: 0.03
Nodes (70): Any, DecisionRecord, Any, InvariantRegistry, Any, Any, DecisionRecord, InvariantRegistry (+62 more)

<a id="c-16"></a>
### Community 16 — "Community 16"
Cohesion: 0.05
Nodes (69): Branch, BranchPoint, BranchStatus, BranchStore, branch.py — v10.1 Causal Convergence Layer  Data models for branching-aware exec, Find Lowest Common Ancestor of two branches.         Walks the parent chain of b, A divergence point: the checkpoint from which two branches diverged.          Im, A causal history of committed events, originating from a shared checkpoint. (+61 more)

<a id="c-12"></a>
### Community 12 — "Community 12"
Cohesion: 0.03
Nodes (69): AgentResponse, AstroCouncilAgent, AstroCouncilAgent — координационный слой астро-домена.  Агрегирует сигналы от Br, Совет астро-агентов с взвешенным голосованием., AgentResponse, AstroCouncilAgent, AstroCouncilAgent — координационный слой астро-домена.  Агрегирует сигналы от Br, Совет астро-агентов с взвешенным голосованием. (+61 more)

<a id="c-5"></a>
### Community 5 — "Community 5"
Cohesion: 0.04
Nodes (67): ACOSContext, ACOSDecisionRequest, ACOSDecisionResponse, ACOSDecisionResult, ACOSGovernanceKernel, ACOSOrchestrator, Any, Main orchestrator for ACOS decision flow.     HARD ENFORCED: Every infra action (+59 more)

<a id="c-20"></a>
### Community 20 — "Community 20"
Cohesion: 0.03
Nodes (67): DriftController, DriftSnapshot, DriftStatus, v6.8 — Model–Reality Drift Controller.  Drift = |SelfModel(t) − Reality(t)|  Con, Compute drift and apply correction if threshold is breached.          Returns Dr, Force a correction even if drift is within threshold., Weighted L2 distance between real and model state.     Only considers keys prese, Event-triggered P-controller with hysteresis for model–reality alignment.      P (+59 more)

<a id="c-21"></a>
### Community 21 — "Community 21"
Cohesion: 0.04
Nodes (66): Any, ChaosScenario, Verdict, Any, ChaosScenario, Verdict, Any, SystemBoundarySpec (+58 more)

<a id="c-3"></a>
### Community 3 — "Community 3"
Cohesion: 0.03
Nodes (65): tests/test_risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 Tests ==================, TestDrawdownKillSwitch, TestExposureControl, TestIntegration, TestLiquidityCheck, TestNaNSafety, TestSanityNaNSafety, TestSlippageThreshold (+57 more)

<a id="c-45"></a>
### Community 45 — "Community 45"
Cohesion: 0.04
Nodes (64): TemplateAgent, agent(), happy_state(), tests/_template_agent_test.py ============================== Canonical test temp, Wrong types in known fields must not raise., If a data source raises, the response is degraded with a machine reason., # TODO: replace the patch target with the function your agent actually calls., @require_ephemeris must convert to a degraded response, not a crash. (+56 more)

<a id="c-14"></a>
### Community 14 — "Community 14"
Cohesion: 0.05
Nodes (61): TemporalVerificationReport, WeightDelta, ProofChain, StabilityMetrics, TemporalVerificationReport, ExecutionGateway, TemporalVerificationReport, TemporalVerificationReport (+53 more)

<a id="c-30"></a>
### Community 30 — "Community 30"
Cohesion: 0.05
Nodes (60): Any, Path, Path, Any, _act_stage(), _g10_rollback_engine(), _g1_adversarial_detector(), _g2_policy_kernel() (+52 more)

<a id="c-28"></a>
### Community 28 — "Community 28"
Cohesion: 0.06
Nodes (57): DAGHashMode, SemanticProof, DAGHashMode, DAGHashMode, ProjectionStep dataclass and field ordering., TestProjectionStep, dag_hash(), Combine two parent digests into a parent digest, respecting mode.      CONSENSUS (+49 more)

<a id="c-43"></a>
### Community 43 — "Community 43"
Cohesion: 0.05
Nodes (55): cancel_task(), get_cb_registry(), get_circuit_breaker(), get_circuit_breakers(), get_queue_stats(), get_task_status(), _get_task_store(), handle_task() (+47 more)

<a id="c-15"></a>
### Community 15 — "Community 15"
Cohesion: 0.03
Nodes (51): Any, Any, AtomicFileWrite, AtomicMultiFileWrite, DeterministicFsOrderingGuard, FileOp, Phase 1: Write all files to .staging/{hash}/ directory         Phase 2: Rename ., Discard all staged files. (+43 more)

<a id="c-29"></a>
### Community 29 — "Community 29"
Cohesion: 0.03
Nodes (50): Jepsen-style invariant tests for SBS v1.  Tests verify that GlobalInvariantEngin, TestFailureClassifier, TestGlobalInvariantEngine, TestLayerState, TestSystemContract, LayerState, Any, Return full result dict from last evaluate() call. (+42 more)

<a id="c-49"></a>
### Community 49 — "Community 49"
Cohesion: 0.06
Nodes (47): _get_candidates(), _get_engine(), _get_ilp(), _get_policy(), _get_twin(), OptimizationRequest, OptimizationResult, optimize() (+39 more)

<a id="c-23"></a>
### Community 23 — "Community 23"
Cohesion: 0.04
Nodes (47): ClosedLoopResilienceController, PolicyAction, HealingAction, PolicyAction, ClosedLoopResilienceController, PolicyAction, StabilitySnapshot, StabilitySnapshot (+39 more)

<a id="c-52"></a>
### Community 52 — "Community 52"
Cohesion: 0.07
Nodes (45): Connection, Path, Any, Event, Any, CoherenceStateSnapshot, ObservabilityEmitter, ObservabilityEmitter v7.0 — Unified single-point observability for ATOMFederatio (+37 more)

<a id="c-94"></a>
### Community 94 — "Community 94"
Cohesion: 0.07
Nodes (45): AgentState, astro_council_node(), build_graph(), electoral_node(), _pool_decide(), AstroFin Sentinel v5 — LangGraph Schema (Belief-Guided)  BeliefTracker + Thompso, Run Thompson-selected technical agents in parallel., Thompson-sampled technical team node.      Decision: should_run, selected = _poo (+37 more)

<a id="c-35"></a>
### Community 35 — "Community 35"
Cohesion: 0.06
Nodes (45): Connection, get_architect(), Intention, MASFactoryArchitect, mas_factory/architect.py - MASFactoryArchitect: builds topology from intention, Parse natural language into structured Intention, Select roles based on required capabilities, Build data flow connections between roles (+37 more)

<a id="c-48"></a>
### Community 48 — "Community 48"
Cohesion: 0.04
Nodes (45): Div, web/callbacks.py — All callbacks (ATOM-META-RL-004), Live data status panel for the dashboard header or Live tab., Register all app callbacks., register_callbacks(), render_live_status(), Div, web/callbacks.py — All callbacks (ATOM-META-RL-004) (+37 more)

<a id="c-103"></a>
### Community 103 — "Community 103"
Cohesion: 0.04
Nodes (44): 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, ATOM-GITAGENT-003: Phase 3 GitAgent (MCP + Dashboard), ATOM-KARL-015: Полная интеграция KARL в основной контур, ATOM-MODEL-SPEC: Единая спецификация модели (+36 more)

<a id="c-107"></a>
### Community 107 — "Community 107"
Cohesion: 0.04
Nodes (44): 10. EXISTING COMPONENTS PRESERVED, 11. MIGRATION NOTES, 1.1 The Post-Determinism Gap, 1.2 System State Before RL-022, 1.3 Goals, 1. CONTEXT & MOTIVATION, 2. ARCHITECTURE — FINAL PRODUCTION LAYER, 3.1 Global Execution Barrier (GEB) — `core/runtime/geb.py` (NEW) (+36 more)

<a id="c-111"></a>
### Community 111 — "Community 111"
Cohesion: 0.04
Nodes (44): 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, ATOM-GITAGENT-003: Phase 3 GitAgent (MCP + Dashboard), ATOM-KARL-015: Полная интеграция KARL в основной контур, ATOM-MODEL-SPEC: Единая спецификация модели (+36 more)

<a id="c-113"></a>
### Community 113 — "Community 113"
Cohesion: 0.04
Nodes (44): 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, ATOM-GITAGENT-003: Phase 3 GitAgent (MCP + Dashboard), ATOM-KARL-015: Полная интеграция KARL в основной контур, ATOM-MODEL-SPEC: Единая спецификация модели (+36 more)

<a id="c-115"></a>
### Community 115 — "Community 115"
Cohesion: 0.04
Nodes (44): 2-Week Priority Order, Active ATOMs Status, ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, ATOM-DEDUP-001: Дедупликация 6 пар агентов, ATOM-FIX-ROUTER: Исправление бага с timeframe, ATOM-GITAGENT-003: Phase 3 GitAgent (MCP + Dashboard), ATOM-KARL-015: Полная интеграция KARL в основной контур, ATOM-MODEL-SPEC: Единая спецификация модели (+36 more)

<a id="c-19"></a>
### Community 19 — "Community 19"
Cohesion: 0.03
Nodes (43): IntegrationReport, Any, IntegrationReport, IntegrationReport, GoalMemory, IntegrationReport, GoalMemory, GoalRecord (+35 more)

<a id="c-22"></a>
### Community 22 — "Community 22"
Cohesion: 0.03
Nodes (43): InvariantResult, StabilitySnapshot, InvariantSetResult, Invariant, InvariantResult, InvariantsEngine, InvariantSet, InvariantSetResult (+35 more)

<a id="c-42"></a>
### Community 42 — "Community 42"
Cohesion: 0.08
Nodes (42): MutationClass, ndarray, MutationClass, SeverityLevel, MutationPolicy, PolicySelector, SeverityActionMapper, v8.2b Controlled Autocorrection Kernel (+34 more)

<a id="c-40"></a>
### Community 40 — "Community 40"
Cohesion: 0.05
Nodes (42): DAGHashMode, ConvergeQuorumResult, dag_hash_n(), DAGHashMode, dag_hash_modes.py — v8.5 Semantic separation of DAG hash contracts  Two distinct, Check whether two digests are equal under the same mode semantics.      Useful f, Hash mode determines the semantic of combining parent digests.      CONSENSUS  —, Combine N children into one parent digest (binary tree reduction).      CONSENSU (+34 more)

<a id="c-128"></a>
### Community 128 — "Community 128"
Cohesion: 0.05
Nodes (42): 10. CI/CD Checks, 1. Network Topology, 2. Layer Architecture, 2-Node Configuration, 3. Node Inventory, 4. Day-by-Day Build Guide, 5. Quick Start, 6. Variables Reference (`group_vars/all.yml`) (+34 more)

<a id="c-55"></a>
### Community 55 — "Community 55"
Cohesion: 0.05
Nodes (41): DFAEvent, DFAExecutionGuard, DFAState, InvalidTransitionError, dfa_execution_guard.py — P6 Runtime DFA Enforcement Layer  M = (S, Σ, δ, s₀, F), Runtime DFA enforcement for ExecutionGateway.     Every state transition passes, audit_L0_workspace(), audit_L1_algebra() (+33 more)

<a id="c-100"></a>
### Community 100 — "Community 100"
Cohesion: 0.07
Nodes (40): astro_agent(), fundamental_agent(), macro_agent(), optionsflow_agent(), quant_agent(), core/council/agents.py — AstroCouncil agents, sentiment_agent(), technical_agent() (+32 more)

<a id="c-127"></a>
### Community 127 — "Community 127"
Cohesion: 0.07
Nodes (39): BaseModel, AuthConfig, BrandingConfig, GatewayConfig, RateLimitConfig, RateLimitStrategy, Gateway configuration schemas., TenantGatewayConfig (+31 more)

<a id="c-109"></a>
### Community 109 — "Community 109"
Cohesion: 0.05
Nodes (39): Any, config(), doctor(), inspect(), replay(), run(), status(), verify() (+31 more)

<a id="c-143"></a>
### Community 143 — "Community 143"
Cohesion: 0.05
Nodes (39): 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 1. Mission & non-goals, 2. Top-level architecture, 3. DDD bounded contexts, 4.1. Why a Data Room?, 4.2. Data Room structure (+31 more)

<a id="c-144"></a>
### Community 144 — "Community 144"
Cohesion: 0.05
Nodes (39): Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), AMRE Flow, API Reference, Architecture Overview, Astro vs Fundamental+Quant (+31 more)

<a id="c-149"></a>
### Community 149 — "Community 149"
Cohesion: 0.05
Nodes (39): 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 1. Mission & non-goals, 2. Top-level architecture, 3. DDD bounded contexts, 4.1. Why a Data Room?, 4.2. Data Room structure (+31 more)

<a id="c-150"></a>
### Community 150 — "Community 150"
Cohesion: 0.05
Nodes (39): Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), AMRE Flow, API Reference, Architecture Overview, Astro vs Fundamental+Quant (+31 more)

---

## Remaining Communities (one-liner)

_973 unique member-sets · 1967 communities_

| Communities | Nodes | Cohesion | Members |
|---|---:|---:|---|
| `#9` | 37 | 0.02 | EvolutionConfig, TestEvaluationResult, TestEvolutionEngine, TestMetaAgent, TestRewardCalculator, TestScoredStrategy, TestStrategyPool, tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 ... |
| `#24` | 39 | 0.03 | Any, EnforcementRecord, InvariantEnforcer, InvariantEvaluator, InvariantRegistry, InvariantResult, InvariantResult, InvariantViolation |
| `#25` | 21 | 0.03 | BacktestEngineAdapter, RiskEngineV2, StrategyEvaluator, TestEvaluationResult, TestScoredStrategy, TestStrategyEvaluator, TestStrategyEvaluator, tests/test_meta_rl.py — ATOM-META-RL-001: Full Test S... |
| `#27` | 26 | 0.05 | Any, Canonical cycle: gossip delta -> consensus decision -> proof -> bind all., DriftReport, EventStoreSnapshot, Multiple events can reference the same entity_hash across layers., TestDriftDetector... |
| `#31` | 38 | 0.05 | AlignmentConstraint, Any, CausalMergeProtocol, ConsensusSignal, DistributedTensorAlignment, ExecutionGateway, MergeResult, TickSnapshot |
| `#32` | 39 | 0.04 | CausalProofGraph, CausalProofGraph, ChainLink, ChainLink, DriftEvent, ProofChain, ProofChain, ProofChain |
| `#33` | 25 | 0.04 | ETLPipelinePlugin, IExecutionContext, IPlugin, InferencePlugin, MLTrainingPlugin, MLTrainingPlugin, PluginPriority, get_plugin() |
| `#34` | 25 | 0.03 | AdaptiveRouter, AdaptiveRouter v6.4 — DRL++: loss-aware, Called after each RPC attempt to update peer state., DRL++ layer: loss-aware and latency-aware routing.      Wraps the raw DRL transp, Manua... |
| `#36` | 36 | 0.06 | AlwaysAllow, NoOpInvariantChecker, NoOpRollback, RecordingLedger, TestAggressiveMode, Verify ingest populates _direction_history (unit-level test)., executor(), v8.2b Controlled Autocorrection — 17... |
| `#37` | 28 | 0.07 | Any, ChaosTrace, Comparison report between an original trace and a replayed trace., Complete recorded trace of one chaos experiment run., DivergenceReport, ReplayValidator — H-4: Deterministic repl... |
| `#38` | 26 | 0.05 | ATOM-META-RL-003: Detect alpha decay.          Alpha decay = reward is dropping, ATOM-META-RL-003: Force-reset the evolution.          When alpha decay is detect, Any, EvolutionEngine, EvolutionSta... |
| `#39` | 34 | 0.05 | Find the first matching rule for `trigger` and return its action.          Rules, Maps ReactionTrigger events to PolicyAction responses using     a priority-order, PolicyAction, PolicyEngine, Polic... |
| `#41` | 33 | 0.07 | Any, AssertionResult, ChaosRunner, ChaosScenario, Random, StabilitySnapshot, _cascade_assertions(), callable |
| `#44` | 34 | 0.06 | ATOM-META-RL-007: Full WalkForwardValidator integration., Any, Any, BacktestEngineAdapter, BasketMetrics, EvaluationResult, StrategyEvaluator, meta_rl/strategy_evaluator.py -- ATOM-META-RL-010/003/... |
| `#46` | 32 | 0.04 | ConvergeConsensus, ConvergeQuorumResult, DAGHashMode, DeltaConsensusConfig, DeltaGossipMessage, DeltaGossipMessage, StateVector, StateVector |
| `#47` | 38 | 0.04 | Apply LagWindow smoothing to confidence and compute position_lag metrics., Compute reproducible state hash., KARLSynthesisAgent, Manual trigger: sync_with_audit().         Periodic self-assessment ... |
| `#50` | 31 | 0.06 | DecisionRecord, DriftEvent, DriftPolicyAdaptor, DriftReport, DriftType, StabilityMetrics, TemporalVerificationReport, TemporalVerificationReport |
| `#51` | 20 | 0.06 | GPULease, Job, Job Store — Durable State Machine, JobStatus, JobStore, ROMA Control Plane — Core Models, Worker, WorkerStatus |
| `#53` | 30 | 0.06 | ChaosHarness, ChaosResult, ChaosResult, Save this chaos result to FailureReplay with correct stage progression., TestChaosHarness, TestChaosValidator, partition_half_cluster(), pytest chaos test su... |
| `#54` | 35 | 0.05 | DeltaGossip Protocol — delta-driven federation gossip.  Replaces GossipProtocol., DeltaGossipConfig, DeltaGossipMessage, PeerDeltaState, Per-peer state for delta gossip.      Tracks what we know ab... |
| `#56` | 24 | 0.09 | Action, Any, Any, DAGValidator, FailureReport, FailureType, L11Verifier, VerificationReport |
| `#57` | 34 | 0.06 | ADLRecoveryLoop, ADLRecoveryOrchestrator, LivenessRecoveryFunction, LivenessRecoveryFunction placeholder., OscillationMonitor, OscillationMonitor — delegates to ADLRecoveryOrchestrator., Oscillatio... |
| `#58` | 26 | 0.07 | EconomicSecurityViolation, NodeStake, SlashingEngine, SlashingReason, SlashingRecord, ValidationSlashingError, slashing_engine.py — atom-federation-os v9.0+P8 Slashing Engine., stake_registry.py — ... |
| `#59` | 18 | 0.06 | ACOSCLI, ACOSCLI, Compiles job submissions into executable DAGs.     Guarantees: every node has ex, DAG execution with:     - Topological ordering (parallel where possible)     - C, L8 + L9 mandato... |
| `#60` | 18 | 0.07 | Async partial-sync gossip. Callbacks on new vector arrival., GossipProtocol, GossipProtocol — partial async state exchange between nodes.  No blocking RPC. E, Handle peer's response to our pull req... |
| `#61` | 32 | 0.07 | BacktestRegime, BacktestResult, BacktestStep, ContinuousBacktest, ReplayBuffer, amre/backtest_loop.py — Backtest-as-a-Service (ATOM-KARL-010) Непрерывный backte, create_backtest_runner(), Запустить... |
| `#62` | 31 | 0.09 | TestDirectoryValidation, test_print_report_all_pass(), test_print_report_all_pass(), test_print_report_quiet(), test_print_report_quiet(), test_validator.py — ATOM-VALIDATE-001: Unit tests for Agen... |
| `#63` | 19 | 0.07 | BacktestConfig, BacktestConfig, BacktestResult, BacktestResult, BacktestTrade, Backtester, Backtester, trading/backtester.py — ATOM-STEP-8: Backtesting Engine |
| `#64` | 28 | 0.05 | BACKTEST mode → APPROVED., CLOSE_ONLY mode → ModeEnforcer checked (REJECTED or APPROVED)., Dict signal is parsed without error., New 5% position within 10% limit → accepted., Pre-existing 8% + new ... |
| `#65` | 34 | 0.10 | ByzantineSignal, ConsensusShiftType, DampenerConfig, DynamicsReport, EntropyStats, Immutable snapshot of all node weights at a point in time.      Used for determi, NodeWeightsSnapshot, NodeWeights... |
| `#66` | 16 | 0.04 | Accumulated stability stats for a single source over current epoch., Compute global stability trend across all sources.         Compares current epoc, Global stability trend across all sources., Qu... |
| `#67` | 29 | 0.10 | FailureParams, FailureRecorder, FailureReplayer, FailureScenario, FailureSnapshot, failure_replay.py — HARDENING v2: Failure Replay System  Контракт сценария отказ, instrument_engine(), Одно действ... |
| `#68` | 29 | 0.10 | ActuatorSignal, CircuitBreaker, CircuitBreakerConfig, CircuitBreakerSignal, CircuitState, DriftEpisode, GovernorSignal, GovernorSignal |
| `#69` | 26 | 0.05 | EvaluationResult, Remove lowest-reward strategy from pool., ScoredStrategy, StrategyPool, any, downsample_equity_curve(), meta_rl/strategy_pool.py — ATOM-META-RL-001: Strategy Pool with Diversity C... |
| `#70` | 22 | 0.08 | DAG-Aware Retry Engine — Layer B.  Provides: - DagNode / RetryStrategy model - P, DagNode, DagRetryEngine, DagStateStore, NodeStatus, PartialRecomputeStore, _NodeWithInputs, _get_redis() |
| `#71` | 23 | 0.05 | ATOM Operator — watches ATOMCluster CRDs, ATOMController, ApiClient, AppsV1Api, K8sClient, Kubernetes API client wrapper for ATOM operator., Runs one background reconciliation thread per ATOMCluste... |
| `#72` | 23 | 0.05 | Add an event handler called for each replayed event., Any, Event, Failure Replay Engine v7.0.  Modules:   event_store         — append-only event, Generator that yields events in deterministic orde... |
| `#73` | 22 | 0.08 | Append-only event log. Single source of truth.     SQLite backend with WAL mode, DeterministicReplay, Event, EventStore, EventType, JobAggregate, JobProjection, JobState |
| `#74` | 24 | 0.06 | AuditVerdict, ConvergenceLayer, EntropyController, EntropyRegime, EntropySnapshot, GlobalConsistencyOrder, MergeAuditResult, MergeAuditor |
| `#75` | 28 | 0.05 | Any, Deterministic hash of message payload., Deterministic message queue with full replay support.      Guarantees:       - A, DeterministicFanoutOrder, DeterministicMessageEnvelope, LogicalClock, ... |
| `#76` | 22 | 0.10 | ConsensusResult, ConsensusResult, ConsensusResult, PolicySync, PolicySync — applies remote theta through local replay validation (H-4).  CRITIC, QuarantineEntry, StateVector, StateVector |
| `#77` | 25 | 0.09 | ConsensusOutcome, FederationMessageSigning, FederationMessageSigning, MessageSignatureError, SignedMessage, Simplified signature layer (HMAC-SHA256 over node_id+payload)., byzantine/__init__.py — v... |
| `#78` | 22 | 0.08 | 2 vs 2 split-brain → highest stability wins., ConsensusDecision, ConsensusResolver, ConsensusVote, ExecutionGateway, StateVector, Tests for federation.consensus_resolver., make_vector() |
| `#79` | 37 | 0.12 | FederationInboundSecurityGate, FederationMessageSigning, FederationMessageSigning, General security gate violation., MessageCategory, NonceSequenceValidator, OriginPolicy, federation/security/inbou... |
| `#80` | 23 | 0.07 | Append an event to the log. Returns the event with sequence number., Convenience method to emit a new event., DurabilityLayer, Event, EventStore, EventType, ROMA Event Store — Append-only event log... |
| `#81` | 17 | 0.06 | MetaRLTradingBridge, MetaRLTradingBridge, TestModeGating, TradingExecutionResult, TradingExecutionResult, get_bridge(), get_bridge(), get_bridge() |
| `#82–86` (4) | 37 | 0.06 | CalibrationMetrics, CorrelationPenalty, DrawdownState, DrawdownTracker, FalseCorrelationDetector, compute_reward_from_outcome(), compute_trajectory_reward(), get_calibrator() |
| `#84` | 34 | 0.06 | Any, Compact fingerprint of a cluster state, DivergenceEvent, DivergenceReport, DivergenceType, NonReplayableMarker, excluding wallclock-dependent fields., realtime_divergence_detector.py =========... |
| `#87–97` (4) | 29 | 0.04 | +0.3] → без изменений., 0.012 * 0.8 = 0.0096.clip(0.01) = 0.01., amre/test_risk_control.py — ATOM-KARL-015 Phase 5: Tests for risk_control.py  Te, lag = 0 → без изменений., lag внутри [-0.3, При in... |
| `#88` | 26 | 0.08 | BCIL, BCILReport, BranchTrust, ByzantineConvergenceFunction, ByzantineFailureType, ByzantineRiskAssessment, ByzantineRiskAssessor, MergeDecision |
| `#89` | 24 | 0.09 | ADLR liveness, BCIL safety, GSL, Global Soundness Layer.      Reads: GCPL convergence, InternalState, ObservedState, _kl(), gsl.py — v10.9 Global Soundness Layer Validates internal convergence agai... |
| `#91` | 19 | 0.06 | Any, Attempt to send `msg` across the (simulated) network.          Returns:, ConnectionPool, DRL = Dynamic Runtime Layer (network distortion / link perturbation).      Simul, DRLBridge, NodeRPCSer... |
| `#92` | 30 | 0.08 | Any, Current head of the ledger hash chain., ExecutionRequest, ProofVerifier, Stateless verification (no ledger, Update the signing key (for key rotation)., Verify an ExecutionRequest proof.       ... |
| `#95` | 28 | 0.06 | ChaosScenario, _AsymmetricPartition, _ByzantineSenderInjection, _ClockSkewEscalation, asymmetric_partition(), byzantine_sender_injection(), clock_skew_escalation(), latency_spike() |
| `#96` | 21 | 0.06 | AuditLogger, Enter mutation context., ExecutionGateway, Reset singleton (for testing only)., Return singleton instance., Singleton gateway-guard для всех state mutations в системе.          Guarant... |
| `#98` | 7 | 0.04 | TestEvaluationResult, TestEvolutionEngine, TestMetaAgent, TestRewardCalculator, TestStrategyEvaluator, TestStrategyPool, tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 tests) |
| `#99` | 18 | 0.07 | Check if plan fits in available VRAM., GPU-aware scheduler — VRAM enforcement + priority decisions., GPUScheduler, Job, JobStatus, QueueManager, QueueManager, get_queue() |
| `#101` | 32 | 0.07 | Any, Args:             get_state_delta_exec:   fn(prev_state, Compute normalized drift between two delta dicts., curr_state) -> delta di, sI1: State delta equivalence — the deltas themselves must b... |
| `#102` | 30 | 0.06 | GeneratedStrategy, ScoredStrategy, Unit tests — StrategyPool diversity/top_k + Persistence scored/versions.  Closes, _make_scored(), _make_strategy(), _make_stub_scored(), _make_unique_ids(), _purge() |
| `#104–114` (3) | 20 | 0.08 | Adapter, Any, BiasSwitch, ConditionEvaluator, Connection, LowConfidenceSwitch, Message, NodeType |
| `#105` | 34 | 0.17 | AccountBalance, AccountBalance, Order, Order, OrderSide, OrderSide, OrderType, Position |
| `#106` | 36 | 0.07 | Job, Job, WorkloadGenerator, WorkloadGenerator, WorkloadProfile, WorkloadStream, datetime, datetime |
| `#108` | 23 | 0.06 | Any, CertificationContext, CertificationReport, CertificationResult, CertificationStatus, DivergencePoint, certify_replay_output(), certify_runtime_output() |
| `#110` | 24 | 0.05 | Custom WARNING policy → logs but does not raise., OFF mode → always returns False, Quorum below threshold → pre_commit blocks in ENFORCED mode., SBS Runtime Enforcer — integration tests.  Verifies ... |
| `#116` | 18 | 0.07 | Advance tick counter. Returns new tick., Check if mutation is currently allowed., ContextMode, EnhancedExecutionContext, Get current context mode., Get current context nesting depth., Reset singlet... |
| `#117` | 24 | 0.05 | Audit log accumulates across multiple enforce() calls., Custom WARNING policy → logs but does not raise., Per-stage policy overrides default., Quorum below threshold → pre_commit blocks in ENFORCED... |
| `#118` | 28 | 0.08 | BufferEntry, EMA state for reward smoothing — ATOM-KARL-015 Phase 3., ReplayBuffer, RewardState, Trajectory, _select_best_trajectory(), amre/replay_buffer.py — Replay Buffer for trajectory learning... |
| `#119` | 10 | 0.10 | HealingAction, HealingAction, HealingResult, HealingResult, QuorumConfig, SelfHealingControlPlane v6.4 — Node lifecycle + reconfiguration.  Healing action, StabilitySnapshot, Synchronous healing fo... |
| `#120` | 31 | 0.10 | BrandingCache, Default ROMA VEGA brand., load_by_api_key(), load_by_tenant_id(), load_default(), saas/branding/__init__.py — Branding Package, saas/branding/cache.py, saas/branding/loader.py |
| `#121` | 30 | 0.07 | Compare current state vs expected.         Returns list of differences., Export full state (snapshots + events) as dict., Get list of all known job IDs from snapshots., Import state from dict (for ... |
| `#122` | 22 | 0.09 | TaskStore — единый источник истины для управления состоянием задач.  Заменяет: -, _epoch_key(), _get_redis(), get_task_store(), Единый источник истины для task lifecycle.      Все переходы — атомар... |
| `#123–130` (4) | 33 | 0.08 | Idea, IdeaStatus, create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), inject_idea(), list_ideas() |
| `#124–126` (2) | 21 | 0.07 | A strategy paired with its evaluation metadata.      Supports: generation tracki, Add ScoredStrategy to pool if not duplicate and pool has capacity.          Retu, EvaluationResult, Manages populat... |
| `#131` | 6 | 0.05 | TestEvaluationResult, TestEvolutionEngine, TestMetaAgent, TestRewardCalculator, TestStrategyPool, tests/test_meta_rl.py — ATOM-META-RL-001: Full Test Suite (31 tests) |
| `#132` | 16 | 0.07 | Build bounds from dict of {metric_name: (lower, Classify system into EnvelopeState.          COLLAPSE check (highest priority):, Complete set of stability bounds.      Defaults calibrated for auton... |
| `#133` | 20 | 0.07 | Any, CheckpointManager, CrashConsistentState, CrashSnapshot, Recover to most recent committed snapshot state., Save a snapshot at tick., r'''         Verify state_after == state_before for all comm... |
| `#134` | 18 | 0.09 | Any, Apply ExecutionSanityChecker to backtest result., BacktestEngineAdapter, Backtester, Build price series dict for Backtester., EvaluationResult, Production backtest adapter.      Converts Gener... |
| `#135` | 22 | 0.06 | BarrierPhase, BarrierTicket, Check if ALL nodes have arrived at barrier(tick)., Check if QUORUM of nodes have arrived at barrier(tick)., DeterministicTickSynchronizer, GlobalExecutionBarrier, Globa... |
| `#136` | 25 | 0.05 | Canonical list of system-wide invariants., InvariantType, Jepsen-style invariant tests for SBS v1.  Tests verify that GlobalInvariantEngin, Return True if contract is loaded (always true; for futur... |
| `#137` | 18 | 0.09 | Append event to task's stream. Returns stream entry ID.         Also updates Lam, Convenience: emit STEP_EXECUTED with full step data., EventStore, Get latest stream entry ID (for replay cursor)., ... |
| `#138` | 25 | 0.08 | ClusterSimulator, ClusterSimulator — simulates N-node federation cluster with fault injection.  Us, ClusterTrace, GossipConfig, QuorumConfig, inject_degrade(), inject_malicious_theta(), inject_part... |
| `#139` | 18 | 0.08 | Both trees project to same CONSENSUS, CROSS_ORIGIN_EQUIVALENCE invariant., Invariant should build its own proof when proof not provided., ProofOrigin enum values., SemanticProofEngine: prove_equiva... |
| `#140` | 27 | 0.07 | In-memory token bucket for single-instance rate limiting., Rate limiting — Token Bucket + SlowAPI + Redis backend., Redis-backed token bucket for distributed rate limiting., RedisTokenBucket, _get_... |
| `#141` | 32 | 0.07 | Action, Compute reality consensus and pick actions., ConsensusReport, RCF, Reality Consensus Fusion (RCF) layer — v11.1.  This layer observes the outputs o, Reality Consensus Fusion observer + deci... |
| `#142–156` (4) | 19 | 0.08 | Approximate Bayesian credible interval via Wilson score.         Falls back to m, AstroFin Sentinel v5 — Agent Belief Tracker (Bayesian)  Stores per-agent accurac, BeliefState, BeliefTracker, Conne... |
| `#145` | 21 | 0.07 | SlidingWindow, _consecutive(), _derivative(), _last_age_min(), _mean(), _slope(), _std(), datetime |
| `#146` | 38 | 0.05 | INV-AWG8: AmneziaWGManager requires trace_id (non-optional in context)., INV10: Event is frozen (frozen=True dataclass)., test_awg_deterministic_delay(), test_awg_events_written_to_eventlog(), test... |
| `#147` | 26 | 0.06 | Any, Clear all internal state (use for test reset or divergence recovery)., Compute delta between last replay state and current replay state., Compute minimal diff between prev and curr.          R... |
| `#151` | 17 | 0.09 | ChaosEvent, ChaosFeedbackController, ControllerConfig, Human-readable breakdown of impact components., ImpactScorer, ImpactWeights, Tunable parameters for ChaosFeedbackController., chaos/observabil... |
| `#153–157` (2) | 39 | 0.05 | 1. Mission & non-goals, 10. Security & secrets, 11. Graceful degradation contract, 12. Roadmap, 2. Top-level architecture, 3. DDD bounded contexts, 4.1. Why a Data Room?, 4.2. Data Room structure |
| `#154` | 38 | 0.05 | INV-AWG7: TunnelState enum has valid values., INV8: Engine writes, projections read. Never the twain shall meet., test_awg_deterministic_delay(), test_awg_events_written_to_eventlog(), test_awg_ide... |
| `#155–158` (2) | 39 | 0.05 | AMRE Flow, API Reference, Agent Beliefs (core/belief.db), Agent Registry, Agent Weights, Agent Weights (config/agent_weights.yaml), Architecture Overview, Astro vs Fundamental+Quant |
| `#159` | 15 | 0.09 | AntiEntropy, AntiEntropy — merkle-tree reconciliation between federation peers.  Implements t, Compare my DAG state with a peer's DAG state.          Returns (missing_on_my_si, Compute layered merk... |
| `#160` | 21 | 0.09 | Build the next outbound TrustSyncMessage for peer_id.          Args:, Decide whether to send a full TRUST_VECTOR or TRUST_DELTA.          Full sync if, Gossip protocol for distributing trust state ... |
| `#161` | 24 | 0.08 | AST, Call, DotFormatter, ExecutionGraph, ExecutionGraphBuilder, FunctionDef, JsonFormatter, Path |
| `#162` | 25 | 0.05 | 20th переходит в mature., amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)., В warmup phase больше вес на raw s... |
| `#163` | 32 | 0.11 | AdaptiveScheduler, StepStatus, _get_session(), get_cancellation(), get_cb_registry(), get_dag_recorder(), get_retry_engine(), get_scheduler() |
| `#164` | 18 | 0.10 | Create a new DAG for task_id + epoch. Returns dag_id., DAGRecorder, Execution DAG Recorder — v3 core component.  Captures: task → step graph → span, ExecutionDAG, Load DAG by dag_id. Uses meta inde... |
| `#165` | 22 | 0.10 | BreakerState, CircuitBreaker, call_with_breaker(), test_circuit_breaker_half_open_recovery(), test_circuit_breaker_opens_after_threshold(), test_circuit_breaker_short_circuits_when_open(), test_cir... |
| `#166` | 37 | 0.05 | 1. Formal Model of the System, 1.1 System State Definition, 1.2 Transition Function, 1.3 Key Invariants, 10. Success Criteria Verification, 11. Conclusion, 2. Replay Equivalence Proof, 3. Split-Bra... |
| `#167` | 15 | 0.06 | At epoch JD, Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., Keplerian orbital elements for a solar system body at epoch J2000.0., Longitude 0° ≤ λ < 360°., M is mean_... |
| `#168–178` (4) | 36 | 0.05 | 1. Requirements Analysis, 2. Technology Comparison (2026), 3. Recommended Architecture, 4. Performance & Scalability, 5. Security & Compliance, 6. Integration with Project, 7. Risks & Alternatives,... |
| `#169–179` (4) | 22 | 0.09 | Any, Load all scored strategy records for a session., MetaRLPersistence, dj(), dl(), get_persistence(), ld(), meta_rl/persistence.py — ATOM-META-RL-007/009/012/013: Full Persistence |
| `#170` | 21 | 0.08 | Build MLBatch with train/val/test splits (time-based 80/10/10).         Returns, DatasetExporter, Export a split to CSV file. Returns path., MLBatch, Map job/outcome string to label integer., Windo... |
| `#171` | 26 | 0.08 | AST, Call, ClassDef, FunctionDef, Import, ImportFrom, Module, Path |
| `#174` | 9 | 0.09 | ChaosObservabilityBridge, Critical: feedback must mutate _current_intensity for next cycle., DriftCorrelation, Records a causal link between a chaos event and a detected drift episode., TestFeedbac... |
| `#175` | 21 | 0.10 | Args:             cluster_state_fn:  fn() returning live cluster state dict, CrossLayerInvariantEngine, I1: different node keys → FAIL with node_drift report., I1: identical cluster and replay stat... |
| `#180` | 23 | 0.06 | Decorator that blocks agent execution if Swiss Ephemeris is unavailable.      Us, EphemerisUnavailableError, P, Raised when agent requires Swiss Ephemeris but it's not available., T, require_epheme... |
| `#181` | 24 | 0.09 | C(t) = mean pairwise distance over all active branches., ConvergenceFunction, ConvergenceSnapshot, GCPLCheckResult, GlobalConsistencyChecker, GlobalInvariant, causal_edit_distance(), gcpl.py — v10.... |
| `#182` | 35 | 0.06 | 1. FORMAL BYPASS PATH ANALYSIS, 1.1 Complete Call Graph — Mutation Entry Points, 1.2 All Possible Bypass Paths Classified, 10. SUCCESS CRITERIA — VERIFICATION CHECKLIST, 11. SUMMARY SCORECARD, 2. I... |
| `#183` | 15 | 0.08 | GossipConfig, Local replay validation — core of H-4 invariant.          In simulation: theta i, NodeMetrics, NodeRuntime, NodeRuntime — per-node runtime for federation cluster simulation.  Each nod... |
| `#184–199` (3) | 22 | 0.11 | BacktestRegime, BacktestResult, BacktestStep, ContinuousBacktest, Rolling backtest — окно двигается на 1 шаг за раз.         Возвращает generator, amre/backtest_loop.py — Backtest-as-a-Service (ATO... |
| `#185–197` (3) | 20 | 0.10 | Any, CalibrationReport, CalibrationTracker, Connection, Cursor, datetime, get_calibration_tracker(), meta_rl/calibration.py -- ATOM-META-RL-014: CalibrationTracker.  Tracks agent pr |
| `#186–203` (4) | 26 | 0.18 | AST, ArchitectureLinter, Path, check_base_agent_inheritance(), check_data_room_compliance(), check_docstrings(), check_no_fstring_sql(), check_no_top_level_print() |
| `#187–204` (4) | 33 | 0.16 | AST, AsyncFunctionDef, Check, ClassDef, FunctionDef, Path, _camel_to_snake(), check_A1_has_agent_class() |
| `#188–205` (4) | 18 | 0.06 | BACKTEST mode → APPROVED., CLOSE_ONLY mode → ModeEnforcer checked (REJECTED or APPROVED)., Dict signal is parsed without error., New 5% position within 10% limit → accepted., Pre-existing 8% + new ... |
| `#189` | 16 | 0.09 | Any, DRL (Data Replication Layer) — in-memory message passing with fault injection. T, DRLTransport, DeliveryModel, FailureModel, Message, Random, _make_uuid() |
| `#195` | 19 | 0.07 | BaseHTTPMiddleware, BrandingInjectorMiddleware, Gateway middleware assembly., Injects branding into responses:     - Headers: X-Tenant-ID, Response branding injection — headers + optional HTML., Wi... |
| `#196` | 17 | 0.09 | Auto-map event type → metric increments.         Used when wiring is not explici, In-process Prometheus-compatible metric store.      Suitable for:       - Unit t, InMemoryPrometheusEmitter, Metric... |
| `#198` | 15 | 0.07 | Background: ping peers every 5s, ClusterNode, Node entrypoint — runs inside container.  Usage (inside container):     python e, On boot, Send a Ping to peer, each node:           1. Waits briefly f... |
| `#206` | 19 | 0.10 | AdaptiveRetryController, AdmissionController, AdmissionDecision, DegradationLevel, GlobalDegradationController, LoadShedDecision, LoadShedder, _get_redis() |
| `#207` | 21 | 0.06 | Alpha пересчитывается при изменении window_size., EMA продолжает работать после увеличения окна., EMA продолжает работать после уменьшения окна., amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5:... |
| `#208` | 15 | 0.07 | At epoch JD, Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., Longitude 0° ≤ λ < 360°., Longitude at different times must differ (unless full period)., M is mean_longit... |
| `#209–215` (2) | 33 | 0.11 | ceph_osd_latency(), ceph_osd_replication_latency(), ceph_storage_total(), ceph_storage_used(), cpu_util(), disk_io_time(), get_node_metrics(), gpu_mem_util() |
| `#210` | 13 | 0.08 | Deserialize from dict. Handles both dict and tuple payloads., Immutable event record.      prev_hash is set by EventLog.append() at append tim, Serialize to dict for storage. Does NOT include prev_... |
| `#211` | 18 | 0.09 | Any, MisbehaviorEvidence, MisbehaviorType, Report and slash a double-signing incident.          This is the primary slashin, Return True if node is currently slashed., Return slash records, optiona... |
| `#212` | 14 | 0.08 | APIKeyManager, Organization, RBACEngine, ROMA API Key System — Scoped keys with rotation., ROMA Organization Model — org → project → tenant hierarchy., ROMA RBAC Engine — Role-based permissions., R... |
| `#213` | 32 | 0.09 | build_api_secret(), build_certificate(), build_configmap(), build_ingress(), build_kong_consumer(), build_kong_credential(), build_namespace(), build_rate_limit_plugin() |
| `#214` | 17 | 0.08 | Add new node to cluster. Requires consensus., Create snapshot up to last_included_index., LogEntry, NodeState, Raft cluster manager — coordinates leader election and replication., Remove node from ... |
| `#216–227` (4) | 19 | 0.09 | AggregateConfidenceAdapter, Any, ContextAdapter, ExtractSignalAdapter, FilterByConfidenceAdapter, MergeSignalsAdapter, get_adapter(), get_message_bus() |
| `#217` | 19 | 0.09 | BaseStrategy, GAPopulation, GeneratedStrategy, crossover(), evolve(), fitness_from_backtest(), generate_synthetic_history(), mutate() |
| `#218` | 20 | 0.11 | AST, BypassPath, Execute full audit:             1. Module scan             2. Mutation point dis, Iterate all Python files, Path, Reset audit state (for testing only)., Run full self-audit at syst... |
| `#219` | 32 | 0.06 | ATOMFederationOS — Установка и описание компонентов, 💥 `chaos` — Chaos Engineering, 📐 `dag` — DAG Planner, 🔗 `actuator` — Actuator Layer, 🔧 `core` — Детерминированное ядро, 🗺️ `cluster` — Node Mana... |
| `#220` | 20 | 0.08 | Any, Any, Any, GlobalInvariantEngine, Show/edit SBS configuration., _get_current_config(), run_config(), sbs/cli_config.py — config subcommand implementation. |
| `#222` | 20 | 0.11 | AgentSignalRepository, Any, AstroPositionRepository, AuditLogRepository, DecisionRecordRepository, _d(), get_all_stats(), is_postgres_available() |
| `#223–224` (2) | 32 | 0.06 | CEPH_ADMIN_PASSWORD, CEPH_ADMIN_USER, CEPH_CLUSTER_NET, CEPH_PUBLIC_NET, CLUSTER_SUBNET, CLUSTER_VLAN_ID, DOCKER_NETWORK, vars.sh script |
| `#226` | 17 | 0.10 | Compute trust score for proof_hash.          Returns 0.0 if proof_hash is unknow, ProofLedger, ProofOrigin, ProofRecord, Record a validation result for an existing proof.          Creates a new rec... |
| `#228` | 14 | 0.06 | 10 workers racing to claim the same PENDING task.     Exactly 1 must win — all o, First call returns True (key set), Fresh store pointing to test DB., Idempotency key follows expected format: idem:... |
| `#229` | 14 | 0.11 | Compute the difference between self (newer) and other (older).          Returns, Deserialize from plain dict., Remove a proof_hash entry (proof pruned from ledger)., Return a deep copy of the curre... |
| `#230–247` (4) | 31 | 0.06 | ATOM-KARL-015: Полная интеграция KARL в основной контур, Core Principle, DecisionRecord — расширенный, Execution Order, Expected Results (честно), Feature Flags (обязательно), Files to Modify, Impa... |
| `#231–250` (5) | 31 | 0.06 | 360)., 360)., Heliocentric longitude always ∈ [0, Mean anomaly always ∈ [0, jd_range(), mean_anomaly_360(), positive_eccentricity(), tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Test... |
| `#232–249` (3) | 13 | 0.06 | At epoch JD, Earth's radius should be near 1 AU., Jupiter's radius should be near 5.2 AU., Longitude 0° ≤ λ < 360°., Longitude at different times must differ (unless full period)., M is mean_longit... |
| `#234` | 14 | 0.10 | Any, CausalSemanticVector, Embed both systems into the semantic space., Field-level diff: curr - prev, L2 norm of a dict's values (handles numeric types)., _dict_diff(), _l2_norm(), causal_semantic... |
| `#235` | 16 | 0.14 | Append a single event. Returns event_id.          If event.event_id is already s, Append multiple events atomically. Returns list of event_ids.          All event, Deterministic event ID: same inpu... |
| `#236` | 22 | 0.10 | DriftType, DriftType, Mirrors DriftType from drift_profiler.py (local re-export for this module)., drift_type_to_bridge(), make_moderate_oscillation(), make_oscillating_coherence(), make_stable_coh... |
| `#237` | 15 | 0.09 | Any, Append a new mutation entry. Always appends; never modifies., LedgerEntry, MutationLedger, Mutations per slot over last `window` entries., Path, mutation_ledger.py — immutable audit log of all... |
| `#241` | 9 | 0.13 | AxisVector, Full scalar metric: weighted sum of axis vector.         If axis_vec not provide, Human-readable severity level., Per-tick divergence vector across all 5 axes.      Each axis is normali... |
| `#242` | 7 | 0.10 | CostExplainabilityEngine, Predicts runtime duration for a task based on plugin type and historical events., ROMA Cost Explainability Engine — Why this costs what it costs., ROMA Developer Onboardin... |
| `#243` | 31 | 0.06 | Deployment Guide: Day 1 → Day 7, ⚫ DAY 7 — Integration, 🔴 DAY 1 — Network Foundation, 🔵 DAY 3 — Compute Nodes, 🟠 DAY 2 — WireGuard Mesh Encryption, 🟢 DAY 4 — Slurm Cluster, 🟣 DAY 5 — Ray AI Runtime... |
| `#244` | 23 | 0.11 | AP_exec(), AP_exec_and_not_nl(), AP_exec_or_replay(), AP_noncelocked(), AP_replay(), MC, labels(), main() |
| `#246` | 19 | 0.11 | AgentSignalRepository, Any, AstroPositionRepository, AuditLogRecord, AuditLogRepository, DecisionRecordRepository, Immutable audit log record., _d() |
| `#251` | 13 | 0.11 | Adaptive gain converges toward 1.0 when stable., Basic initialization and reset., Damped feedback controller for the actuator layer.      Monitors the error signa, Damping factor stays within bound... |
| `#252` | 19 | 0.12 | Capture a failure incident trace., FailureRecord, FailureReplay, Immutable trace of a single failure incident., List all saved replay files., Load an incident from a JSON file., Record → Save → Rep... |
| `#253` | 20 | 0.07 | 20th переходит в mature., amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, position_lag ≈ 0 когда недостаточно истории (< 5)., В warmup phase больше вес на raw signa... |
| `#254–276` (4) | 28 | 0.10 | HouseCalculator, calculate_alcabitius_cusps(), calculate_ascendant(), calculate_equal_houses(), calculate_midheaven(), calculate_placidus_cusps(), calculate_porphyry_cusps(), calculate_whole_sign_h... |
| `#255–270` (3) | 17 | 0.11 | E in degrees. Converts to, KeplerOrbit, KeplerResult, M = M₀ + n · (JD - JD₀)  [degrees], OrbitalElements, Solve M = E - e·sin(E) via Newton-Raphson.         M, core/kepler.py — ATOM-STEP-1: Kepler... |
| `#256–272` (3) | 27 | 0.13 | Idea, IdeaStatus, create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), inject_idea(), list_ideas() |
| `#257–277` (4) | 17 | 0.12 | A proposed ATOM card., ATOM proposal: CrewAI integration., ATOM proposal: Pressure Field Coordination., AtomProposal, AtomProposer, Create ATOM proposal from a single finding., Generate ATOM propos... |
| `#258–281` (4) | 17 | 0.06 | @require_ephemeris must convert to a degraded response, AgentTestContract, An empty state is not allowed to raise — must degrade gracefully., DegradedContract, If a data source raises, Wrong types ... |
| `#259` | 30 | 0.06 | 0. Runtime Enforcement (P0.1 / P0.2 / P0.3 / P1.4), 1. DriftProfiler, 10. FeedbackPrioritySolver, 11. ControlArbitrator, 12. GossipProtocol, 13. CausalMergeProtocol, 14. DeterministicScheduler, 2. ... |
| `#260` | 16 | 0.08 | Associate a single proof_hash with a node_id., Associate proof_hashes with a node_id. Idempotent., Computes and caches per-node weights from TrustVector state.      Weights are de, NodeWeightEntry,... |
| `#261–280` (2) | 17 | 0.09 | Any, DESC Event Adapter — logs SBS events to DESC event log.  Every invariant violati, DESCEventLogger, LayerStateAdapter, Return all logged events in append order., Return only INVARIANT_VIOLATION... |
| `#264` | 18 | 0.11 | AgentSignalRepository, Any, AstroPositionRepository, AuditLogRepository, DecisionRecordRepository, _d(), get_all_stats(), is_postgres_available() |
| `#268` | 16 | 0.13 | Heal/scale cooldowns prevent restart storms., Reconciler, Step 5 — Phase 3: Pending → bootstrap creates StatefulSet., Step 5 — Phase 5: quorum breach → Failed phase., Step 5 — Phase 5: scale-up on ... |
| `#271` | 20 | 0.07 | Generate → evolve → export → persist → reload → verify metrics., Integration test for the full evolutionary pipeline.  Closes: R6.3, No ohlcv → StrategyEvaluator short-circuits to a fail() result.,... |
| `#274` | 18 | 0.10 | AstroFin Sentinel v5 — Synthesis Agent AstroCouncil: координатор всех агентов, Get attribute or dict key from signal (handles both AgentResponse and dict)., Load and normalize weights from config/a... |
| `#275` | 20 | 0.07 | amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow  Tests:, lag_adj < 0 когда EMA ниже raw (сигнал опережает вверх)., lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)., la... |
| `#279` | 8 | 0.09 | ClosedLoopResilienceController, Convenience: called after each RPC to feed router + metrics., Get best peer for routing., Get full routing state., Get list of currently healthy (non-violating) peer... |
| `#282–302` (4) | 16 | 0.09 | Adjust exploration rate based on reward trend., AsyncPipeline, Dynamically adjust TTC (Time To Commit) depth based on conditions., KARLOptimizer, KARLPerfProfile, Main optimizer for KARL loop perfo... |
| `#283–303` (4) | 20 | 0.10 | ControlAction, KPIControlState, OAPConfig, OAPOptimizer, OptimizationStatus, amre/oap_optimizer.py — OAP + KPI Control Loop (ATOM-KARL-010) Оптимизация позиц, get_oap_optimizer(), Валидирует решени... |
| `#286` | 17 | 0.11 | AgentSignalRepository, Any, AstroPositionRepository, AuditLogRepository, DecisionRecordRepository, _d(), get_all_stats(), is_postgres_available() |
| `#287` | 20 | 0.11 | Classification of fix required., CorrectionAction, CorrectionCycleResult, CorrectionDecision, CorrectionLoop, CorrectionSignal, Execute one correction cycle.         Returns CorrectionCycleResult w... |
| `#288–299` (2) | 7 | 0.13 | Any, JobState, JobStatus, NodeState, NodeStatus, Prevent duplicate Slurm submissions for same job., StateStore |
| `#289` | 29 | 0.07 | 1. `core/runtime/determinism_guard.py` — ENFORCEMENT LAYER, 2. FILE-BY-FILE REPLACEMENT MAP (P0), 3. SWARM & FEDERATION HARDENING, ATOM-META-RL-020 — FULL DETERMINISM ELIMINATION & RACE CONDITION H... |
| `#290` | 17 | 0.13 | Any, BridgeConfig, BridgeResult, Check that causation chain is preserved through the causal_parents field., Check that replay event preserves the same relative ordering as execution., Event, Execut... |
| `#291` | 15 | 0.10 | Any, DeterministicTraceLedger, Get all entries for a specific tick, Get all entries sorted by order_key (deterministic)., Return all entries with global_tick >= N, in deterministic order., r'''    ... |
| `#294` | 10 | 0.11 | # NOTE: record_revenue_share, Append-only ledger — every billing event is recorded, BillingLedger, Handles Stripe webhook events → ROMA billing state updates., get_monthly_revenue, get_pending_reve... |
| `#295` | 13 | 0.09 | Agent that runs on the Docker host and injects iptables rules     on behalf of c, HostChaosAgent, Manage network partition rules in iptables DOCKER-USER chain.      The DOCKER-US, NetworkPartitione... |
| `#296` | 20 | 0.11 | Classification of fix required., Concrete actions available to the correction loop., Execute one correction cycle.         Returns CorrectionCycleResult with decisio, STEP 1: Observe — detect devia... |
| `#297` | 15 | 0.08 | DeltaRouter, DeltaRouter — delta routing and sequence tracking.  Tracks per-peer fingerprint, Mark a peer as stale (no updates recently)., Return (seq, Return list of peer IDs whose latest fingerpr... |
| `#298` | 11 | 0.09 | Ensures jobs are never lost.     STARTED → RUNNING → COMPLETED → COMMITTED     I, Handle job failure. Returns action: 'retry' | 'fail' | 'unknown_job', Job, JobRetryManager, JobState, Mark job as c... |
| `#300` | 19 | 0.09 | CandidateGenerator, ConstraintGraph, HardConstraintPruner, HybridSolver, ILPOptimizer, PolicySelector, Returns list of (node_id, score) for top-k candidates.         Score = base_scor, … (+1) |
| `#301` | 5 | 0.11 | PlanTraceLogger, PlanTraceLogger: event recording and query., Records full execution trace of the planning pipeline.      Provides:       - fu, TestPlanTraceLogger, TraceEvent |
| `#304` | 26 | 0.13 | Idea, create_idea(), evaluate_idea(), get_ideas_by_status(), get_kpi(), inject_idea(), list_ideas(), load_ideas() |
| `#305–317` (3) | 17 | 0.14 | BacktestRun, MetricsAgent, MetricsDB, MetricsSummary, _db_path(), _get_db(), get_summary(), load_results() |
| `#306–318` (3) | 16 | 0.10 | Classify volatility regime from ATR%., Create engine pre-computing atr_pct., Create engine with explicit regime (bypasses ATR calc)., Dynamic risk calculator.      Input (pick one):       - price +... |
| `#307–327` (5) | 17 | 0.09 | After one orbital period, Earth radius should always be in physically plausible range., For any elliptic orbit: r(ν=0°) < r(ν=180°)., No NaN/Inf in Keplerian or Swiss calculations., Sanity checks t... |
| `#308–328` (5) | 8 | 0.07 | AgentResponse must have all required fields and valid ranges., All modules should import without errors., Full pipeline — all agents run, Router must correctly classify queries., TestAgentResponseM... |
| `#311` | 18 | 0.11 | ConstraintGraph, HardConstraintPruner, HybridSolver, ILPOptimizer, Layer 2: Remove candidates that violate hard constraints., Layer 3: Exact ILP solver on pruned candidate subset.     Maximizes U(S... |
| `#312` | 17 | 0.11 | ChaosToReplayBridge, Check if applying the same event sequence twice produces same state.         Ide, Check if two runs with same events converge to same final state.         This is, Determinism ... |
| `#319` | 9 | 0.09 | Any, ExecutionState, StateReducer, TestAmneziaWG, TestEventLog, TestPayloadToDict, TestReducerEdgeCases, _payload_to_dict() |
| `#320` | 16 | 0.07 | _check_inbound_message_authenticity(), _check_proof_trust_bounded(), _check_stale_proof_not_trusted(), _check_trust_convergence(), _check_trust_vector_consistency(), _check_trust_weighted_stability... |
| `#321` | 24 | 0.11 | Agent, Attempt, CycleState, Environment, gate(), load_state(), main(), print_report() |
| `#322` | 16 | 0.12 | Compute the scalar reward for ``result``.          Returns ``config.base_reward`, Computes a scalar reward from an :class:`EvaluationResult` using     **only** ri, EvaluationResult, Pre-flight chec... |
| `#323` | 19 | 0.10 | DAGDriftProfile, Detect goal drift across replans.          Goal drift = consistent directional c, Detect oscillating replan pattern.          Oscillation = replans that consisten, Detect unstable ... |
| `#326` | 14 | 0.18 | Tenant, Tenant, TenantCreate, TenantManager, TenantNotFoundError, generate_tenant_id(), saas/tenants/manager.py CRUD operations for tenant management., saas/tenants/models.py Tenant model for white... |
| `#329–341` (2) | 26 | 0.22 | check_reqs(), cmd(), cmd_sudo(), day1(), day2(), day3(), day4(), day5() |
| `#330–331` (2) | 14 | 0.12 | Any, AstroFinConstraintCompiler, Compiles AstroFin YAML/policy text → executable Constraint DAG.     DAG structur, Constraint, ConstraintOp, ConstraintType, One-call factory for standard AstroFin p... |
| `#332–342` (3) | 10 | 0.10 | ATOM-META-RL-009: Load past sessions and update internal state., Add Q-value with automatic cleanup (FIFO eviction)., Bounded KARL state with automatic memory limits., EvolutionConfig, KARLState, M... |
| `#333–339` (2) | 18 | 0.11 | GAPopulation, GeneratedStrategy, crossover(), evolve(), fitness_from_backtest(), generate_synthetic_history(), mutate(), random_chromosome() |
| `#334` | 12 | 0.12 | "identical") if causal gra, Any, CausalFingerprint, IncrementalCausalVerifier, Incrementally maintains causal fingerprints for exec and replay domains.     Equ, O(1) causal equivalence check.      ... |
| `#335` | 19 | 0.12 | Analyze differences between local and remote vectors.          Returns ConflictR, ConflictReport, Deterministic merge of local and remote TrustVectors.          Returns a new Tru, LedgerReconciliat... |
| `#336` | 14 | 0.11 | Any, Checkpoint, Path, Restore state to the checkpoint identified by checkpoint_id.          Args:, Revert the last applied mutation by finding the pre-mutation checkpoint., ndarray, rollback_engin... |
| `#337` | 17 | 0.11 | Classify the current state.         If model not ready → learn (create new eigen, Create a new eigenstate from the current feature vector., Eigenstate, EigenstateDetector, EigenstateType, Rolling-w... |
| `#340` | 15 | 0.07 | ACOS TraceRecorder — fully contract-compliant implementation., Clear all traces. For testing only., Contract-compliant TraceRecorder.      Guarantees:     - get_trace() always exis, DeterministicTr... |
| `#343–368` (4) | 17 | 0.14 | GitAgentRegistry, Unified registry for all AstroFin agents.     Provides run(), agents/gitagent_registry.py — ATOM-GITAGENT-004/005: Agent Registry + Output Ada, get_agent_info(), get_registry(), l... |
| `#345` | 19 | 0.14 | Aspect, AspectReport, AspectType, AspectsEngine, _angle_diff(), _normalize_angle(), calculate_aspects(), essential_dignity() |
| `#346–369` (4) | 17 | 0.13 | AstroFin Sentinel v5 — Persistent Session History (R-08)  SQLite-backed session, Connection, HistoryDB, Retrieve a session by session_id. Returns None if not found., _db_path(), get_db(), get_sessi... |
| `#347–361` (2) | 12 | 0.16 | Any, Apply ExecutionSanityChecker to backtest result., BacktestEngineAdapter, Backtester, Build price series dict for Backtester., EvaluationResult, Production backtest adapter.      Converts Gener... |
| `#348–374` (4) | 26 | 0.13 | BlendResult, DataFrame, compute_mae(), compute_reversals(), compute_sharpe(), compute_stability(), evaluate_blend(), generate_demo_data() |
| `#349` | 25 | 0.11 | Firewall install is idempotent., Test that legacy mode works identically to before changes., Uninstall removes firewall from meta_path., alignment module blocked outside gateway., cluster.node.node... |
| `#350–371` (3) | 13 | 0.12 | Any, Async wrapper — delegates to sync check (all components are fast)., ExecutionSanityChecker check., MarketMode, ModeEnforcer (TradingMode) check — validates operational mode constraints., RiskE... |
| `#351–367` (2) | 26 | 0.07 | 1. Pre-flight Checklist, 2. Step-by-Step Deployment, 3. Verification Commands, 4. Switching Monitoring Backends, 5. Troubleshooting, 6. All Services Reference, 7. Quick Reference, AmneziaWG Network |
| `#352` | 10 | 0.11 | Immutable snapshot of a node's control state for gossip exchange., SeverityLevel, Stable hash of a theta dict., StateVector, StateVector — core unit of exchange between federation nodes., TestState... |
| `#353` | 21 | 0.12 | Event, Event, Replay Observability Subscriber v7.0.  Bridges ReplayEngine → Prometheus + OTEL., ReplayObservabilitySubscriber, ReplayObservabilitySubscriber Tests v7.0.  Tests the bridge: ReplayEng... |
| `#354` | 15 | 0.11 | Invariant, InvariantChecker, InvariantViolation, PositiveSemidefiniteInvariant, Pre-mutation safety validator.      Runs all registered invariants before a muta, TestSpectralInvariant, invariant_ch... |
| `#355` | 26 | 0.24 | check_root(), gpu_check(), log(), logErr(), logOk(), logWarn(), main(), stage10_ai() |
| `#356` | 26 | 0.07 | 1. `execution/execution_gateway.py` — NEW, 1. Нет bypass путей, 2. Async не ломает детерминизм, 2. `runtime/async_execution.py` — DETERMINISTIC, 3. Consensus корректен, 3. `swarm/swarm_engine.py` —... |
| `#357` | 8 | 0.15 | ControlSignal, DecisionRecord, ProofKernel, Resolve pending signals and produce a proof trace DAG.         Returns (winner_s, Return all signals sorted + DecisionRecord., Run full cross-layer verif... |
| `#358` | 19 | 0.11 | Any, Any, Raised when state fails schema validation., SBS State Schema Validator — enforces required layer + version contract., Validate state schema from JSON string or file., collect_state(), run... |
| `#364` | 12 | 0.11 | APIKey, AuthEngine, AuthError, Create HMAC signature for request signing., KeyStatus, KeyType, Validate or raise AuthError., Verify HMAC signature. Reject if >5 min old. |
| `#365` | 12 | 0.14 | DAG of divergence propagation across domains.      Nodes: DivergenceRootCause en, DivergenceRootCause, DivergenceRootCauseGraph, Kahn's algorithm — returns node keys in propagation order., Main ent... |
| `#372` | 16 | 0.11 | Aggregate error vector → scalar 0..1., DriftEvent, DriftStatus, Manually trigger a model rebuild., ModelRealityAligner, Per-subsystem absolute error., Trigger appropriate correction based on drift ... |
| `#373` | 8 | 0.12 | GPUNode, GPUPolicyEngineV2, GPUPolicyResult, JobMetrics, JobState, RTX3060Config, SchedulingDecision, VRAMAllocation |
| `#375` | 18 | 0.12 | GAPopulation, GeneratedStrategy, crossover(), evolve(), fitness_from_backtest(), generate_synthetic_history(), mutate(), random_chromosome() |
| `#376–394` (4) | 17 | 0.11 | ATOM-016: Meta-improvement — analyze question bank and propose improvements., ATOM-016: Meta-questioning — reflect on whether our questions are trustworthy., Answer the selected question., Question... |
| `#378` | 10 | 0.11 | Any, Any, PostgresReplayBuffer, PostgresReplayBuffer, db/karl_replay.py — PostgresReplayBuffer (ATOM-019) Stores KARL trajectories in, db/karl_replay.py — PostgresReplayBuffer (ATOM-019) Stores KAR... |
| `#379–391` (2) | 6 | 0.19 | Job, Job engine with built-in telemetry generation.     Every transition writes to th, JobEventHooks, JobState, TelemetryJobEngine, Write event to telemetry log (append-only, immutable). |
| `#380` | 14 | 0.12 | All constraints involving a specific node., Constraint, ConstraintGraph, ConstraintType, Job can only run on specific nodes., NodeV, P(latency > max_latency) < target_p., Vertex in constraint graph. |
| `#381` | 13 | 0.13 | Any, Called from INSIDE MutationExecutor.apply_mutation().          Returns True if i, Get the singleton guard instance., Invariant 1: len(entry_points) == 1          Scans ALL loaded modules for '... |
| `#382` | 15 | 0.13 | Apply node weight: effective_vote = weight × vote, ConsensusCandidate, ConsensusResult, ConsensusShiftEvent, ConsensusShiftType, NodeWeightsSnapshot, consensus_resolver.py — v9.6 Trust-Weighted Con... |
| `#384–396` (3) | 18 | 0.13 | Aspect, AspectReport, AspectType, AspectsEngine, _angle_diff(), _normalize_angle(), calculate_aspects(), essential_dignity() |
| `#385–398` (2) | 16 | 0.12 | Build data flow connections between roles, Connection, Intention, MASFactoryArchitect, Parse natural language into structured Intention, Select roles based on required capabilities, get_architect()... |
| `#386–399` (2) | 25 | 0.10 | # TODO: replace the patch target with the function your agent actually calls., If a data source raises, TemplateAgent, Wrong types in known fields must not raise., agent(), happy_state(), tests/_te... |
| `#387` | 15 | 0.10 | Get current queue depth from Redis., GlobalStateModel, GlobalStateRecord, Queue admission control.         Returns (admit: bool, Resolve conflict between two records using resolution strategy.     ... |
| `#388` | 14 | 0.12 | Check if job can be placed on node.         Returns (valid, Directed constraint graph G = (V, E).     V: compute nodes, Sum of resource usage by all jobs on node (excluding job_id)., jobs, list_of_... |
| `#390` | 25 | 0.08 | 1. Execution Algebra Definition, 2. Algebraic Properties, 3. Execution Algebra Laws, 4. Formal Verification Conditions, 5. Algebra Classification, 6. System Theorems, 7. Compliance Statement, algeb... |
| `#392–397` (2) | 15 | 0.12 | Install an MCP server from Smithery registry.                  Args:, MCP Adapter for Smithery/GitHub Tools Integrates with Smithery MCP registry to s, MCP Adapter that integrates with Smithery reg... |
| `#393` | 16 | 0.17 | Any, Namespace, cmd_activate(), cmd_create(), cmd_get(), cmd_list(), cmd_stripe_onboard(), cmd_suspend() |
| `#395` | 15 | 0.15 | BacktestRun, MetricsAgent, MetricsDB, MetricsSummary, _get_db(), backtest/metrics_agent.py — G-01, get_summary(), load_results(), … (+1) |
| `#400` | 13 | 0.11 | MockLedger, Request, Revenue Share Calculator — tiered, Tests for RevenueShareCalculator + Stripe Webhook., per month, per partner, test_ledger_revenue_share_ext(), test_tiered_rates(), … (+2) |
| `#401–415` (2) | 23 | 0.31 | check_deps(), check_files(), cleanup(), error(), generate_report(), info(), is_done(), load_env() |
| `#402` | 16 | 0.12 | ActuationDirection, ActuationResult, ActuationSeverity, ActuationSignal, ActuatorCommand, Causal Actuation Engine — v7.4 Maps divergence field (from swarm/swarm_divergenc, CausalActuationEngine, Co... |
| `#403–420` (2) | 9 | 0.15 | ATOM-META-RL-003: Detect alpha decay.          Alpha decay = reward is dropping, ATOM-META-RL-003: Force-reset the evolution.          When alpha decay is detect, Any, EvolutionEngine, EvolutionSta... |
| `#404–417` (3) | 15 | 0.12 | 24h change, Enforce rate limiting between requests., Fetch OHLCV bars from exchange or generate sandbox data.          Args:, Fetch current ticker (last price, LiveDataProvider, _get_exchange(), cr... |
| `#405` | 15 | 0.20 | BaseStrategy, Gene, Gene, Gene, PerformanceRecord, StrategyResult, StrategyResult, StrategyResult |
| `#406–421` (3) | 14 | 0.10 | AccountBalance, BaseBroker, Order, OrderSide, OrderStatus, OrderType, Position, trading/broker/base.py — ATOM-STEP-9: Base broker interface |
| `#407` | 15 | 0.12 | AdaptiveSlippageModel, AdaptiveSlippageModel, AdaptiveSlippageModel, AdaptiveSlippageModel, OrderBookSimulator, OrderBookSimulator, OrderBookSimulator, Slippage model with market microstructure int... |
| `#408` | 18 | 0.10 | Any, AtomMessage, Bridges local DRL fault layer to remote nodes via gRPC.      DRL remains the aut, Broadcast via DRL → RPC mesh., Called by the local gRPC server's AtomServicer when a message arri... |
| `#409` | 12 | 0.11 | Any, Any, AtomMessage, NodeEndpoint, NodeMesh, RPCClient, Stateful connection to a single remote AtomNode.     Thread-safe: multiple threa, Static or dynamically discovered peer. |
| `#412` | 14 | 0.10 | Backpressure System — GPU saturation control + queue throttling. Implements: loa, BackpressureConfig, BackpressureStatus, BackpressureSystem, Record that a job completed and released VRAM., Record ... |
| `#413` | 17 | 0.12 | A point-in-time price observation., Any, Any, Data Room Blueprint — fallback chain for data access., PriceTick, PriceTick, T, data_room/resolvers/base.py ============================ Abstract base ... |
| `#414` | 24 | 0.08 | 1. System States, 10. Conclusion, 2. Transition System (Before Fix), 3. Transition System (After Fix), 4.1 Safety Invariant (Before Fix — VIOLATED), 4.2 Safety Invariant (After Fix — SATISFIED), 4.... |
| `#416` | 24 | 0.08 | Auth / JWT, GPU Nodes, GPU Workers, Grafana Dashboards, ⚙️ Configuration, 🎯 Helm Chart Deploy (production / white-label), 🏠 Home Cluster (k3s + Pop!_OS), 📁 File Structure |
| `#418` | 13 | 0.12 | Average children per node., Average number of coherence drops per tick.         A drop = consecutive decreas, Average number of coherence recoveries per tick.         A recovery = consecutiv, Combi... |
| `#419` | 12 | 0.08 | Constructor.          Args:             channel: A grpc.Channel., Missing associated documentation comment in .proto file., NodeRPC, NodeRPCServicer, NodeRPCStub, ── Service Definition ────────────... |
| `#422` | 6 | 0.11 | ClusterLogger, LogEntry, LogLevel, MetricsCollector, NodeMetrics, Observability layer — structured logging + cluster metrics. |
| `#423` | 12 | 0.08 | Build a TestClient against the FastAPI app.      Note: the real app loads a mode, Integration tests that require a real model on disk., Server should accept ?explain=true without crashing., Smoke t... |
| `#424` | 5 | 0.08 | TestDrawdownKillSwitch, TestExposureControl, TestModeGating, TestVolatilityTargeting, tests/test_risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 Tests ================== |
| `#425` | 23 | 0.13 | _get_event_store(), _get_redis(), _get_task_store(), _is_task_cancelled(), enqueue(), is_queue_saturated(), process_message(), queue_depth() |
| `#426–442` (4) | 22 | 0.12 | BufferEntry, clear_buffer(), get_all_buffer_entries(), get_buffer_entries_for_idea(), get_buffer_stats(), ideas_to_self_questioning_prompts(), inject_idea_to_buffer(), karl_evaluate_idea() |
| `#427–434` (2) | 13 | 0.13 | AgentResponse, Any, AstroFin Sentinel v5 — Technical Agent Технический анализ: RSI, Bollinger, Fetch OHLCV data from OKX asynchronously., MACD, datetime, Расчёт RSI, … (+4) |
| `#429–443` (4) | 23 | 0.08 | 1. Цель и ценность продукта, 10. Edge cases и обработка ошибок, 11. Success Metrics, 12. Риски, 13. Definition of Done, 2. Целевая аудитория и ключевые User Stories, 3. Стек технологий, допущения и... |
| `#430–439` (2) | 14 | 0.12 | Apply pending update using EMA smoothing.         P_t = (1 - α) * P_{t-1} + α *, Exponential moving average., PolicyGovernor, PolicySnapshot, PolicyUpdate, Queue a policy update for next cycle.    ... |
| `#431` | 19 | 0.16 | Any, test_act_mismatch(), test_block_at_g2(), test_complex_federation_trace(), test_detail_mismatch(), test_eg_normalize(), test_equivalent_traces(), test_feg_normalize() |
| `#432` | 8 | 0.16 | AtomOperatorReconciler, CircuitBreaker, ClusterState, DriftProfiler, ExecutionGateway, InvariantChecker, ReconciliationResult, StabilityGovernor |
| `#436` | 23 | 0.08 | ACOS — Troubleshooting Guide, API returns 500, Ceph, Ceph OSDs down, CephFS mount fails, Full Cluster Reset, GPU not visible in srun, MikroTik / Network |
| `#437` | 12 | 0.11 | Apply aggregation to current buffer (all data in window)., Central window management: stores SlidingWindows per (node, Get all aggregated features for a node across all metrics/windows/aggregates.,... |
| `#438` | 13 | 0.13 | Check if any GPU worker is available., Execute a job on GPU worker pool., GPUWorkerPool, Get GPU pool metrics., High-level API: send job to GPU worker pool., demo(), execute_on_gpu(), get_gpu_conne... |
| `#444` | 14 | 0.13 | Clear coherence history (e.g., Compute rate of coherence change (per second).         Uses last 2 data points i, Determine which workers and axes to target based on intervention level., Divergence ... |
| `#445–486` (4) | 22 | 0.09 | 2026 Hybrid Signal Architecture, AMRE Modules (ATOM-KARL Framework), ATOM-KARL-009: Decision Audit Trail, Agent Board — Final Weights, Agent Implementation Files, Astro-Sub-Agents Detail (AstroCoun... |
| `#446–489` (4) | 16 | 0.12 | LagWindow, _env_bool(), _env_float(), _env_int(), amre/lag_windowing.py — ATOM-KARL-015 Phase 5: Adaptive Lag Windowing  Сглаживан, get_lag_window(), Адаптивно изменить window_size на основе волати... |
| `#447` | 17 | 0.15 | ACOS AmneziaWG Integration — Patches for ACOS Core  Provides: - Patch 1a: DAGVal, AmneziaWGManager, Any, Any, ContractViolation, create_tunnel_incident(), get_tunnel_metrics(), patch_engine_pre_exe... |
| `#450–490` (4) | 17 | 0.15 | CalibrationResult, CalibrationState, CalibrationTarget, KeplerCalibrator, _gradient_free_step(), _mae_loss(), core/kepler_calibrator.py — ATOM-STEP-5: RL-Style Parameter Calibration ========, main() |
| `#451–480` (3) | 13 | 0.14 | Add experience to replay buffer., Experience, OnlineTrainer, PolicyParams, REINFORCE policy gradient update.         Computes gradient estimate from recent, Reset parameters to best observed config... |
| `#452–492` (4) | 18 | 0.16 | _fetch_metals_api(), _fetch_twelve_data(), _fetch_yahoo_v8(), _fetch_yfinance_lib(), fetch_current_price(), fetch_multi_ohlcv(), fetch_ohlcv(), fetch_ohlcv_simple() |
| `#453–484` (2) | 22 | 0.14 | AgentState, AstroFin Sentinel v5 — LangGraph Schema (Belief-Guided)  BeliefTracker + Thompso, Run Thompson-selected technical agents in parallel., Thompson-sampled technical team node.      Decisio... |
| `#454–493` (4) | 12 | 0.12 | CCXTLiveProvider, Enforce rate limiting between requests., Fast regime detection using 24h change from ticker., Fetch with retry + exponential backoff., Get current market snapshot (live or sandbox... |
| `#455–494` (3) | 13 | 0.14 | -100% -> 0.0.          ATOM-MET, Bonus for consistent performance across many trades.         Rewards high win_ra, EvaluationResult, Map Sharpe ratio to reward. Cap at 5.0 (diminishing returns)., N... |
| `#456–499` (5) | 22 | 0.09 | При use_real_agents=True должен вызываться AstroCouncilAgent., При use_real_agents=True должен вызываться ElliotAgent., При use_real_agents=True должен вызываться MLPredictorAgent., При use_real_ag... |
| `#457–496` (3) | 14 | 0.11 | Estimate market impact using Almgren-Chriss model.          Args:             si, MarketImpactModel, MarketImpactResult, OrderBookLevel, OrderBookSimulator, OrderBookSnapshot, Simulate executing a ... |
| `#459–482` (2) | 12 | 0.13 | Bridge: MetaRL → ACOS submission gateway.     Submits strategy evaluation as ACO, Crossover + mutation → next generation., DISTRIBUTED EVALUATION:         Each strategy → ACOS job submitted to Slur... |
| `#460` | 13 | 0.15 | ClusterSnapshot, Compute marginal utility delta for a single action., Compute total utility U(S)., Epsilon-greedy exploration bonus for trying new configurations., Global utility U(S, ScheduleActio... |
| `#461` | 22 | 0.09 | ATOM Federation OS — Agent Memory, Architecture Map, Constraints (RL-022 HARD LIMITS), Current Version: v10.0-ATOM-META-RL-022, Federation Layer (v7.5+), HARDENING PHASE 1 — Circuit Breaker (✅ NEW)... |
| `#462` | 10 | 0.13 | Any, Build a single DivergenceRootCause from diff info + causal depth., Converts fingerprint + state diff → human-readable divergence explanation., ExplainableDivergenceEngine, Field-level diff acr... |
| `#463` | 22 | 0.09 | 1. Python environment, 2. Kubernetes manifests, 3. HELM установка (альтернатива), ATOMCluster spec, atom-federation-os — Установка и быстрый старт, ✅ Валидация после установки, 🔒 Constraints (C1-C1... |
| `#464` | 9 | 0.11 | ControlArbitrator extended with per-source stability weights.     Weights are ad, ControlSignal, Meta-Adaptive Control Layer — v7.8 Closes the loop: temporal proof output → cont, Resolve using effe... |
| `#466` | 8 | 0.14 | Central registry for all formal invariants.      Built-in invariants:     - I1 (, DecisionRecord, InvariantRegistry, InvariantSpec, InvariantType, Return per-invariant results with full metadata., ... |
| `#467` | 22 | 0.09 | 1. Резюме, 2.1. Общая архитектура и согласованность модулей, 2.10. Зависимости и воспроизводимость, 2.2. Качество кода и стиль, 2.3. Глубокий анализ падающих тестов (приоритет №1), 2.4. Сериализаци... |
| `#477` | 8 | 0.11 | APIGateway, Middleware layer: validates keys, RateLimiter, Token bucket: returns (allowed, attaches usa, enforces quotas, info_dict).         rate_limit = max tokens per, rate limits, … (+5) |
| `#478` | 10 | 0.14 | CostPredictor, Predicts execution cost BEFORE running task., PricingEngine, PricingTier, ROMA SaaS API — POST /run endpoint, RunRequest, estimate_cost(), run_endpoint() |
| `#483` | 13 | 0.13 | BatchPredictRequest, Compute composite risk score from predictions., Decision recommendation based on risk., Path, Predictor, get_predictor(), predict(), predict_batch() |
| `#487` | 20 | 0.11 | EnsembleMember, Get or create the Meta-RL audit log singleton., KPISnapshot, amre/audit.py — Decision Audit Trail (ATOM-KARL-009) Воспроизводимая трассировка, build_decision_record(), get_audit_log... |
| `#488` | 11 | 0.12 | AuditLog, DecisionRecord, Воспроизвести конкретное решение по хешу состояния, Восстановление из dict, Вычисляет хеш записи для верификации, Добавить запись решения, Конвертация в dict для сериализа... |
| `#491` | 13 | 0.15 | E in degrees. Converts to, KeplerOrbit, M = M₀ + n · (JD - JD₀)  [degrees], Solve M = E - e·sin(E) via Newton-Raphson.         M, core/kepler.py — ATOM-STEP-1: Kepler Orbital Mechanics Engine =====... |
| `#497` | 7 | 0.11 | Any, Invoice, StripeCustomer, StripeIntegration, Subscription, UsageRecord, WebhookSimulator |
| `#498` | 12 | 0.13 | Capture current call stack., Check if call stack contains ExecutionGateway., Format stack as readable string., GuardViolation, HARD ASSERT: Verify mutation is allowed.                  Called by:  ... |
| `#500–519` (3) | 13 | 0.13 | AgentResponse, Analyze volume for bearish confirmation., Bear Researcher Agent — bearish case for trading opportunities., BearResearcher — ищет медвежий кейс для актива.      Responsibilities:     ... |
| `#501–521` (3) | 13 | 0.13 | AgentResponse, Cycle Agent — market timing cycles analysis., CycleAgent, CycleAgent — анализ рыночных циклов.      Responsibilities:     1. Detect domina, Determine current phase within the cycle.,... |
| `#502–522` (3) | 13 | 0.13 | 1x2 = 26.5°, 2x1 = 63., AgentResponse, Calculate Gann angles from price data.         1x1 = 45°, Fetch OHLCV data from OKX asynchronously., Gann Agent — Gann angles and time/price analysis., GannAg... |
| `#503–523` (3) | 13 | 0.13 | AgentResponse, Aggregate multiple macro signals into a single direction.          Weights: VIX=, Analyze DXY (dollar index). Strong dollar → pressure on risk assets., Analyze VIX fear index., Analy... |
| `#504` | 9 | 0.15 | DriftKind, DriftReport, FunctionSpec, MCPC, MCPCReport, MCPCStatus, ThresholdSpec, mcpc.py — v10.3 Model Consistency Proof Checker |
| `#505` | 7 | 0.22 | CrossLayerTheorem, Formal cross-layer consistency checker.          Proves that layer states are co, Isolated COROLLARY check: branch_count ≤ T * max_branches., LayerMetrics, LayerState, _run_tests... |
| `#507–520` (2) | 13 | 0.13 | AgentResponse, Analyze volume for bullish confirmation., Bull Researcher Agent — bullish case for trading opportunities., BullResearcher — ищет бычий кейс для актива.      Responsibilities:     1. ... |
| `#511` | 17 | 0.10 | Anything that has an async resolve() method., Blueprint, If all resolvers in the chain fail, If primary resolver raises, blueprint tries the secondary., get_price() returns None., test_blueprint_fa... |
| `#512–531` (3) | 6 | 0.15 | Adjust raw PnL by volatility regime and drawdown.          This is the core post, AssetPosition, RiskConfigV2, RiskEngineV2, RiskState, trading/risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 ========... |
| `#513` | 15 | 0.09 | ACOS Engine Contract — enforced execution engine interface., Any, ExecutionEngineContract, FAIL FAST — raise if object violates ExecutionEngineContract., Persist full execution trace. MUST return t... |
| `#514–528` (2) | 13 | 0.14 | Full system observation snapshot., Generate realistic synthetic baseline when no real data., MetricThresholds, MetricsCollector, Pull admission rates from scheduler API., Pull queue depth and const... |
| `#515` | 10 | 0.16 | 3-level rollback with snapshot persistence.          Snapshot triggers:, ClusterSnapshot, L1: revert to previous policy version., L2: reset optimizer to last known good., L3: full cluster state res... |
| `#516` | 21 | 0.09 | 1. `core/deterministic.py` — GTBP Addition, 2. `alignment/branch.py` — Deterministic IDs + Timestamps, 3. `alignment/convergence.py` — Tick-Based Oscillation + Entropy, 4. `alignment/drift_detector... |
| `#517–560` (2) | 3 | 0.11 | _MockAsyncExecutionEngine, _MockExecutionLoop, _MockSwarmEngine |
| `#518` | 12 | 0.13 | Any, Compute the per-axis divergence vector for the current tick and store it., TestDictL2Delta, TestHammingHex, Tests for unified_state_metric_tensor.py, _dict_l2_delta(), _hamming_hex(), unified_... |
| `#525` | 9 | 0.10 | Cost Decision Gate — blocks/approves/requires_confirmation     before execution, DecisionGate, Manages tenant lifecycle, Return aggregate gate statistics for tenant., t_auth_keys(), t_cost_gate(), ... |
| `#526` | 21 | 0.19 | Test KARL self-improvement loop, Test MAS Factory Topology, Test Meta-Questioning Engine, Test Topology Visualization, Test Uncertainty Engine, main(), print_header(), print_test() |
| `#527` | 10 | 0.11 | Deployment configuration for GPU workers, Execute job in Docker container with GPU isolation, ExecutionResult, GPUWorkerDeployment, Handle job failure with retry, Production worker loop with:     -... |
| `#529` | 10 | 0.16 | 3-level rollback with snapshot persistence.      Snapshot triggers:         - Pe, ClusterSnapshot, L1: revert to previous policy version., L2: reset optimizer to last known good., L3: full cluster ... |
| `#530` | 14 | 0.09 | 7.1 Конфликт: BUY vs SELL., EXTREME) и B(BUY, Non-neutral agents always have magnitude 1.0., Regime discount в EXTREME., eff=70) ← B(SELL, test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests ... |
| `#532` | 19 | 0.09 | Basic unicast send/receive across two real processes., DRL delay layer applied to real RPC — verify added latency., DRL drop layer applied to real RPC — messages disappear., DRL duplicate model cau... |
| `#533` | 4 | 0.11 | DeterminismGuard, DeterminismViolation, DeterministicIDProvider, DeterministicTimeProvider |
| `#534` | 14 | 0.13 | Apply a control cycle: record commands, Atomic control operations available to the actuator., ControlPrimitive, ControlVector, Map the global S_full tensor (canonical + deltas) into control vectors... |
| `#535` | 11 | 0.12 | Approximation of standard normal CDF at z., Bootstrap rolling windows from historical GPU metrics in state_store.     Real i, Compute P(GPU_util > OVERLOAD_THRESHOLD | history).         Uses Gaussi... |
| `#536` | 11 | 0.12 | Approximation of standard normal CDF at z., Bootstrap rolling windows from historical GPU metrics in state_store.     Real i, Compute P(GPU_util > OVERLOAD_THRESHOLD | history).         Uses Gaussi... |
| `#537–561` (3) | 12 | 0.14 | AgentResponse, Analyze valuation metrics., Fetch basic crypto metadata from CoinGecko., Fetch on-chain metrics (simplified)., Fundamental Agent — financial statement analysis, FundamentalAgent, Pub... |
| `#538–562` (3) | 12 | 0.14 | AgentResponse, Calculate momentum indicators., Fetch OHLCV data from Binance., ML predictions., Public entry point. Wraps analyze() with the latency histogram         and defen, Quant Agent — backt... |
| `#539` | 12 | 0.13 | AttractorClass, ClosureProof, GSCT, Main entry point.          Args:             rcf_history: [{t, Partition the state space into attractor classes., conv, drift_score, gsct.py — v11.4 Global Syste... |
| `#540` | 8 | 0.17 | Adapts UST thresholds based on observed system behavior., EvolutionRecord, SystemState, ThresholdConfig, ThresholdEvolver, UST, test(), test_evolution() |
| `#543` | 15 | 0.10 | 7.1 Конфликт: BUY vs SELL., EXTREME) и B(BUY, Regime discount в EXTREME., eff=60):, eff=70) ← B(SELL, test_pressure_field.py — ATOM-COORD-001: 3 Critical Tests + Constraints, В EXTREME regime agent... |
| `#544–585` (4) | 20 | 0.15 | _julian_day(), calculate_panchanga(), get_choghadiya(), get_karana(), get_muhurta_score(), get_nakshatra(), get_tithi(), get_yoga() |
| `#545–586` (4) | 12 | 0.15 | Build ordered list of sources based on configured source., Dispatch to correct fetcher., Fetch candles from Binance public API., Get the latest closing price for a symbol., MarketAdapter, OHLCV, ca... |
| `#546–587` (4) | 20 | 0.10 | 1. LagWindow — Signal Smoothing, 2. Risk Controller — Dynamic Position Sizing, ATOM-KARL-015 Phase 5 — Lag Window Integration, Acceptance Criteria Checklist, Adaptive Window Sizing, Backward Compat... |
| `#547–588` (4) | 11 | 0.15 | A single digest log entry., DigestEntry, DigestLog, DigestStatus, Get entries by status., Tracks digest processing history., Update status for an entry., main() |
| `#548` | 8 | 0.23 | AgentRegistry, Any, ExecutionMetrics, MASFactoryConfig, ProductionMASEngine, Role, Topology, get_production_engine() |
| `#549–589` (4) | 11 | 0.12 | AgentRegistry, Any, BasicAgentRunner, Get roles by pool category, Registry of available agents with capabilities and constraints, get_agent_runner(), get_registry(), mas_factory/registry.py - Agent... |
| `#550–590` (4) | 14 | 0.13 | Alert when KARL state is updated with key metrics., Alert when a strategy exceeds min_reward threshold.          Use after each evol, Alert when evolution run completes.         Includes summary of... |
| `#551–583` (3) | 13 | 0.15 | Aggregate per-split metrics into a full report., Evaluate strategy on train and test windows., Metrics for a single train/test split., Run full walk-forward analysis on a strategy.          Args:  ... |
| `#552–592` (4) | 20 | 0.22 | apply_migration(), cmd_check(), cmd_init_single(), cmd_migrate(), cmd_plan(), cmd_rollback(), cmd_status(), discover_migrations() |
| `#553` | 13 | 0.14 | AdaptiveSlippageModel, OrderBookSimulator, OrderBookSimulator, TWAPConfig, TWAPExecutionReport, TWAPExecutor, TWAPSlice, trading/execution/twap.py — ATOM-STEP-10: TWAP Execution Strategy |
| `#554–578` (2) | 19 | 0.32 | check_ceph_health(), check_cooldown(), check_gpu_available(), check_node(), check_scheduler_api(), check_service(), escalate(), inc_failure() |
| `#555–579` (2) | 15 | 0.14 | MockJob, MockNode, MockStateStore, Test 3: Deduplication — scheduler must not double-submit., test_backpressure_throttles_queue(), test_duplicate_submission_prevented(), test_failure_penalty_affect... |
| `#556` | 13 | 0.17 | Deterministic forward simulation over horizon_minutes.         Returns final sta, DigitalTwin, JobState, NodeState, PredictedEvent, SimAction, SimState, Vectorized batch simulation — runs all actio... |
| `#557` | 9 | 0.10 | Any, BFTConsensus, Mark a node as slashed (excluded from future quorums)., Number of nodes we assume are honest (n - f)., PBFT-like consensus engine tolerating f Byzantine nodes.      Thread-safety... |
| `#558` | 16 | 0.15 | Any, Get the current thread-local OTelInstrumentation instance., OTelInstrumentation, OpenTelemetry Instrumentation v7.0.  Provides:   - TracerProvider setup (OTLP ex, create_span(), event_to_span(... |
| `#559` | 15 | 0.13 | Any, ClassifiedFailure, Classify multiple failure events., FailureCategory, FailureClassifier, FailureClassifier — converts DRL failure events into SBS-level semantic categori, FailureSeverity, cla... |
| `#563–573` (2) | 15 | 0.10 | 7.1 Конфликт: BUY vs SELL., 8. Ограничения: не менять signal., EXTREME) и B(BUY, Regime discount в EXTREME., Signal не меняется после apply_pressure_field., test_pressure_field.py — ATOM-COORD-001:... |
| `#572` | 12 | 0.13 | BackgroundTasks, Execute a single GPU job synchronously., JobRequest, JobResult, build_docker_command(), execute_job(), execute_job_sync(), metrics() |
| `#577` | 13 | 0.13 | Build MLBatch with train/val/test splits (time-based 80/10/10).         Returns, Builds ML datasets from state_store + window_engine.      Flow:         1. Load, Determine label: did node fail with... |
| `#591` | 10 | 0.17 | CalibrationTracker, Compute calibration metrics over a recent window., Connection, Cursor, Record a prediction. Returns its ID (used to record the outcome)., Records agent predictions and resolves ... |
| `#593` | 7 | 0.13 | Extended tick result with predictive fields.          Adds to TickResult:, Extends ClosedLoopResilienceController with predictive capabilities.      The pr, PredictiveController, PredictiveTickResu... |
| `#594` | 11 | 0.11 | Build a MutationExecutionSpec given current system state.          Planning stra, Concrete mutation to be applied to a parameter region.      Fields     ------, MutationExecutionSpec, MutationPlan,... |
| `#595` | 12 | 0.12 | Actuator Layer — v7.4 Closed-loop causal control system for swarm dynamics.  Mod, ActuatorCommandCopy, Current stability state of the feedback loop., OscillationMode, Reset the controller state (e.... |
| `#596–641` (4) | 7 | 0.18 | Any, MetaQuestion, MetaQuestionBank, MetaQuestioningEngine, QuestionEvolution, amre/meta_questioning.py - ATOM-022: Meta-Questioning Engine Self-Improvement: A, get_meta_engine() |
| `#597–618` (3) | 12 | 0.14 | AgentResponse, Calculate Fibonacci retracement/extension targets., Detect if we're in a corrective phase., Elliot Agent — Elliott Wave analysis., ElliotAgent, ElliotAgent — анализ волн Эллиотта.   ... |
| `#598–643` (4) | 12 | 0.14 | AgentResponse, Assess overall risk score (0-1, Calculate Average True Range., Calculate position size using simplified Kelly + volatility adjustment., Fetch OHLCV data from OKX asynchronously., Pub... |
| `#599–620` (3) | 11 | 0.16 | AgentResponse, Check astro timing windows., Fetch OHLCV data from OKX asynchronously., Public entry point. Wraps analyze() with the latency histogram         and defen, Runner for orchestrator., Sc... |
| `#600–601` (2) | 17 | 0.17 | Data-driven job routing — queries Prometheus for live metrics, Data-driven scoring — queries Prometheus for live metrics., Fallback when Prometheus is unreachable — use static info + rough estimate... |
| `#603–642` (2) | 13 | 0.18 | AgentResponse, Any, Compromise Agent — explicit trade-off resolver for conflicting agent signals.  W, CompromiseAgent, Fallback when no real conflict exists (defer to SynthesisAgent)., Public entry... |
| `#607–629` (3) | 19 | 0.18 | HouseCusps, NatalChart, _julian_day(), calculate_houses(), calculate_natal_chart(), calculate_planet(), get_current_positions(), get_planetary_positions() |
| `#608–645` (4) | 19 | 0.10 | 1. Копировать env-файл, 2. Поднять инфраструктуру, 3. Инициализировать схему, 4. Запустить приложение, AstroFin Sentinel V5 — Database Layer, CI/CD, PostgreSQL connection refused, SQLite fallback a... |
| `#609–646` (4) | 19 | 0.10 | 1. Code of Conduct, 10. Questions?, 2. Quick start, 3.1 Architectural conformance, 3.2 Data Room compliance, 3.3 Security, 3.4 Testing, 3.5 Metrics & observability |
| `#610` | 18 | 0.16 | AdmissionController, JobEngine, get_admission(), get_engine(), get_job(), get_scores(), get_state(), get_store() |
| `#611–635` (2) | 16 | 0.35 | FAIL, PASS, SKIP, info(), ok(), run_all(), separator(), test_l1_network() |
| `#612` | 11 | 0.15 | Check if node has lost connectivity to mesh., ConstraintEngine, ConstraintViolation, PlacementContext, Return list of nodes that can satisfy this job (hard constraints only)., Validate all placemen... |
| `#613` | 12 | 0.14 | Any, CrossLayerReport, I1: ClusterState and StateReconstructor must produce identical results., I3: The set/count of SBS violations in cluster must match replay.         Both d, I4: Coherence drift... |
| `#614` | 9 | 0.14 | GovernorSignal, Simulate a full safe mutation pipeline:         1. snapshot → 2. governor check, TestFullPipeline, TestInvariantChecker, TestNormInvariant, Tests for v8.2a Safety Foundations Module... |
| `#615–649` (2) | 11 | 0.10 | Duplicate ACK signals Byzantine behavior., Quorum ratio at exact threshold should pass., Quorum ratio below threshold must fail., System with 1 partition should pass when allow_split_brain=False., ... |
| `#616` | 19 | 0.20 | AST, Call, ExecNode, Path, _collect_call_sites(), _collect_entry_points(), _extract_caller_name(), build_execution_graph() |
| `#624–647` (3) | 7 | 0.22 | AgentRegistry, Any, ExecutionMetrics, MASFactoryConfig, ProductionMASEngine, Topology, get_production_engine() |
| `#625–637` (2) | 13 | 0.18 | Export topology as JSON, Generate ASCII art topology, Generate Mermaid flowchart from Topology, Generates Mermaid and DOT visualizations from Topology, Print all visualizations to console, Quick fu... |
| `#626` | 7 | 0.18 | BillingEvent, BillingEventStore, BillingEventStore, BillingEventType, Invoice, UsageAggregator, simulate_usage() |
| `#627` | 7 | 0.17 | CausalSemanticSpace, Euclidean distance between the most recent exec and replay vectors., Human-readable classification of the dominant divergence mode., Per-axis |exec - replay| magnitude for the ... |
| `#628` | 11 | 0.15 | Check if node has lost connectivity to mesh., Load cluster topology from state dict., Return list of nodes that can satisfy this job (hard constraints only)., Set current allocations from job list.... |
| `#632` | 6 | 0.17 | AmneziaWGManager, Any, Bring up tunnel. Idempotent. Invariant: write-side only., EventLog, Manages AmneziaWG tunnel. C-8 refactored: start() = 7 lines., TunnelEvent |
| `#633` | 19 | 0.10 | Canonical Trace Format, Case 1: Full pass (all gates return PASS), Case 2: Block at gate Gi, Case 3: Behavioral divergence (falsify), Corollary: SAFE_P7, Definitions, Execution Equivalence Proof — ... |
| `#634` | 9 | 0.12 | Acquire lock on GPU for job.         Returns True if acquired, False if GPU is a, GPULock, GPULockManager, Prevents two jobs from running on the same GPU simultaneously.     Uses in-memor, Register... |
| `#638` | 9 | 0.13 | Auto-generate CRD spec from plugin capabilities., CRDSpec, ML Training Plugin — standalone module for operator SDK conversion., PluginToOperatorConverter, RomaOperator, generate_controller_code(), ... |
| `#639` | 19 | 0.10 | Different tasks at different ticks give different IDs., Same name + same tick → same ID., execution_order is deterministic across runs., schedule() on empty scheduler returns None selected., schedu... |
| `#640` | 7 | 0.10 | Composite planning health score (0..1).          Combines:           - plan_stab, EvaluationMetrics, EvaluationMetricsCollector: metrics computation., MetricsConfig, Snapshot of planning system hea... |
| `#644` | 18 | 0.10 | AgentBelief, AgentBeliefHistory, AgentPool, AgentSelectionLog, BacktestRun, KARLTrajectoryStep, KPIMetrics, OAPValidationHistory |
| `#648` | 11 | 0.10 | CRITICAL., FailureClassifier taxonomy tests., HIGH severity., TestFailureClassifier, byzantine' type → BYZANTINE_BEHAVIOR, clock_skew' type → TEMPORAL_DRIFT., drop' type → MESSAGE_LOSS., partition'... |
| `#650` | 12 | 0.11 | Estimate market impact using Almgren-Chriss model.          Args:             si, Full order book state., MarketImpactModel, MarketImpactResult, OrderBookLevel, OrderBookSnapshot, Simulate executin... |
| `#651–652` (2) | 10 | 0.17 | Apply ACOS Correction Prompt to a scenario result., CauseType, Criticality, Generate YAML-formatted correction report., Implements ACOS Correction Prompt logic., Run ACOS correction loop: scenario ... |
| `#653–654` (2) | 18 | 0.11 | INV1: Every action produces an event., INV2: Engine NEVER calls reducer (graph integrity)., INV3: StateReducer NEVER emits events (pure read-side)., INV4: Hash chain integrity., INV5: Trace determi... |
| `#655–709` (4) | 11 | 0.15 | AgentResponse, Analyze 13F institutional holdings., Analyze insider trading activity., Fetch 13F filings data.         Note: SEC EDGAR is free but parsing is complex., Fetch insider trading data.  ... |
| `#656–710` (4) | 10 | 0.16 | AgentResponse, AstroFin Sentinel v5 — Market Analyst Agent Technical analysis: RSI, Bolli, Calculate Bollinger Bands., Fetch OHLCV data from OKX asynchronously., MACD, MarketAnalyst — главный техни... |
| `#657–683` (3) | 11 | 0.15 | AgentResponse, Calculate 95% confidence interval., Fetch price data for ML model., ML Predictor Agent — ML-based price prediction and volatility forecasting., MLPredictorAgent, MLPredictorAgent — M... |
| `#658–684` (3) | 11 | 0.15 | AgentResponse, Analyze gamma exposure., Fetch options data.         Note: Real options data requires paid APIs (Tradier, Options Flow Agent — options flow analysis, OptionsFlowAgent, Public entry p... |
| `#663–711` (4) | 18 | 0.20 | _choghadiya_to_score(), _datetime_to_jd(), get_choghadiya(), get_current_nakshatra(), get_moon_sign(), get_muhurta_score(), get_sidereal_longitude(), is_trading_muhurta() |
| `#664–712` (4) | 18 | 0.11 | 1. АНАЛИЗ СИГНАЛОВ (Signal Distribution), 10. DATA QUALITY, 2. THOMPSON SAMPLING ЭФФЕКТИВНОСТЬ, 3. АНАЛИЗ АГЕНТНЫХ СИГНАЛОВ, 4. ВРЕМЕННОЙ АНАЛИЗ, 5. SYMBOL / TIMEFRAME АНАЛИЗ, 6. BACKTEST PERFORMAN... |
| `#665–716` (4) | 8 | 0.16 | Analyzes multi-agent digest files., Category, DigestAnalysis, DigestAnalyzer, Finding, Parse digest content into structured findings., Relevance scoring for AstroFinSentinelV5., RelevanceScore |
| `#666–717` (2) | 12 | 0.19 | Export topology as JSON, Generate ASCII art topology, Generate Mermaid flowchart from Topology, Generates Mermaid and DOT visualizations from Topology, Print all visualizations to console, Quick fu... |
| `#667–718` (4) | 14 | 0.13 | analyze(), cli(), cprint(), main(), metrics(), print_banner(), print_decision_ascii(), print_decision_rich() |
| `#668–723` (4) | 18 | 0.11 | 1. GitAgent Standard Overview, 1.1 Core Concepts, 1.2 GitAgent Manifest Schema, 2. AstroFin MASFactory Compatibility Analysis, 2.1 Component Mapping, 2.2 Compatibility Score: 85%, 3.1 Phase 1: GitA... |
| `#669–726` (4) | 5 | 0.11 | DXY, TestMacroAgentAggregate, TestMacroAgentDXY, TestMacroAgentGeopolitical, TestMacroAgentVIX, Tests for MacroAgent — VIX, geopolitical risk. |
| `#670–721` (3) | 11 | 0.15 | Default intraday volume curve (24 hourly weights).          Based on typical equ, Execute a VWAP order.          Args:             symbol: Trading pair, Get volume weight for a given slice number.,... |
| `#671–727` (4) | 4 | 0.16 | Monitoring, MonitoringSnapshot, TradeRecord, trading/monitoring.py — ATOM-PRODUCTION: Monitoring System ===================== |
| `#673` | 5 | 0.18 | AmneziaWGManager, Any, Bring up tunnel. Idempotent. Invariant: write-side only., Manages AmneziaWG tunnel. C-8 refactored: start() = 7 lines., TunnelEvent |
| `#674` | 18 | 0.14 | all_detectors(), ceph_health_degraded(), ceph_osd_down(), gpu_available(), node_unreachable(), ray_head_down(), slurm_controller_down(), slurm_worker_down() |
| `#675` | 11 | 0.15 | Build embedding from a feature vector (24h aggregates).         Maps raw feature, Build embedding from hardware + historical profile.         Produces a 16-dimens, Builds fixed-size embedding vecto... |
| `#676–702` (2) | 11 | 0.16 | Apply corrective action: increase smoothing, Check if oscillation failure condition is met., Compute key metrics for oscillation detection., PolicyOscillationScenario, PolicyState, Simulate a polic... |
| `#677` | 11 | 0.13 | AlignmentResult, Compute correlation across three drift signals.         Drift_Alignment = mean(c, Compute divergence: simulated vs actual cluster behavior.         Returns 0-1, Compute model error... |
| `#678` | 18 | 0.11 | 1. ControlArbitrator (`orchestration/control_arbitrator.py`), 10. CircuitBreaker (`orchestration/planning_observability/circuit_breaker.py`), 11. InvariantChecker (`orchestration/v8_2a_safety_found... |
| `#679` | 18 | 0.18 | Any, NormalizedLedgerEntry, check_invariant(), compare_ledgers(), ledger_hash(), ledger_hash_from_normalized(), normalize_entry(), normalize_ledger() |
| `#680` | 9 | 0.12 | Aggregate violation score 0..1.          Uses max-severity across bounds: any si, Compute envelope violation score from DriftProfiler episodes.          Maps drif, Compute violation trend over rece... |
| `#694` | 7 | 0.12 | Cluster Health Graph — per-node state: reachable / lag / last_seen / violation_s, ClusterHealthGraph, Maintains live health state for all peers of a node.      Usage:         health, Mock cluster c... |
| `#695` | 4 | 0.17 | A → B, A → C, B → D, C → D, Incremental DAG fingerprint with O(Δnodes) updates.      Only nodes whose conten, IncrementalFingerprint, TestIncrementalFingerprint |
| `#696` | 8 | 0.15 | EventType, Figure, JobProjection, ProjectionEngine, make_cost_gauge(), make_gpu_bar(), make_timeline(), refresh() |
| `#697` | 7 | 0.11 | Any, BlackRock-style "Data Room" — single source of truth for all data., Convenience:         if success=True, In-process metrics for Data Room access.  Replace with prometheus_client in prod, Metr... |
| `#698` | 11 | 0.13 | Compute correlation across three drift signals.         Drift_Alignment = mean(c, Compute divergence: simulated vs actual cluster behavior.         Returns 0-1, Compute model error rate (MAPE).    ... |
| `#699` | 8 | 0.23 | Any, EmailService, MIMEMultipart, _brand(), test_console_all_types(), test_console_welcome(), test_no_cross_contamination(), test_templates_render() |
| `#700` | 18 | 0.14 | Check Ceph cluster health status., Check if GPU is accessible and not in failure state., Check if Slurm controller is responsive., Check if a Slurm compute node is DOWN or DRAINED., Check if a node... |
| `#701` | 17 | 0.11 | 1. `ansible/roles/slurm_ha/`, 2. `ansible/roles/edge-node/`, 3. `k8s/federation/`, 4. `.github/workflows/infra-ci.yml`, 5. Обновлённый `ansible/playbook.yml`, `defaults/main.yml`, `federated-deploy... |
| `#703` | 11 | 0.18 | ClusterSnapshot, Compute marginal utility delta for a single action., Compute total utility U(S)., Epsilon-greedy exploration bonus for trying new configurations., Global utility U(S, Jobs complete... |
| `#704–714` (2) | 18 | 0.11 | Agent Export/Import, Agents, Architecture, CLI Commands, Configuration, Dashboard Evaluation, Exported Agents (Phase 1), Exported Agents (Phase 2) |
| `#705–715` (2) | 10 | 0.11 | Test adapter initialization., Test fallback server database., Test install returns proper structure., Test list tools with no installed servers., Test recommended servers list., Test search with ca... |
| `#708` | 9 | 0.13 | ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations., Add a MetaRLDecisionRecord to the log., Deserialize from dict., MetaRLDecisionRecord, Separate audit log for Meta-RL st... |
| `#713` | 18 | 0.18 | HouseCusps, NatalChart, _julian_day(), calculate_houses(), calculate_natal_chart(), calculate_planet(), get_current_positions(), get_planetary_positions() |
| `#724` | 5 | 0.16 | ContinuousStabilityEngine, ContinuousStabilityEngine v6.5 — Proactive 1Hz stability tick loop.  Problem:, Execute one stability tick synchronously.         Returns TickResult for the tic, Runs stab... |
| `#725` | 8 | 0.13 | GatewayContext, Process-wide execution context flag.          Active ONLY during ExecutionGatewa, Python 3.10+ meta_path hook., Remove the import firewall. Used only for testing., _ImportFirewall, ... |
| `#728–729` (2) | 6 | 0.11 | PATCH 1: DAGValidator finds graph errors., PATCH 2: Idempotent execution — second call returns cached trace_id., PATCH 3: Enriched projection with node_graph_resolution and execution_order., test_p... |
| `#730–748` (3) | 17 | 0.14 | EnsembleMember, EnsembleSelection, KPISnapshot, MarketSnapshot, amre/audit.py — Decision Audit Trail (ATOM-KARL-009) Воспроизводимая трассировка, build_decision_record(), get_audit_log(), Один шаг ... |
| `#731–749` (3) | 11 | 0.16 | AgentResponse, Bradley Agent — Bradley Model (S&P 500 seasonality/cyccles)., BradleyAgent, BradleyAgent — модель Брэдли (сезонность S&P 500).      Responsibilities:     1., Calculate Bradley-like s... |
| `#732–750` (3) | 11 | 0.16 | AgentResponse, Analyze market sentiment., Analyze price momentum as sentiment proxy., Fetch funding rate from Bybit asynchronously., Public entry point. Wraps analyze() with the latency histogram a... |
| `#736–768` (4) | 17 | 0.11 | 1. Текущее состояние MAS (по факту репозитория), 2. Целевое состояние (что считаем "готово на 100%"), 3. Дизайн четырёх компонентов, 3.1. CompromiseAgent (`agents/_impl/compromise_agent.py`) — НОВЫ... |
| `#737–769` (4) | 17 | 0.11 | 1. Agents, 2. Core infrastructure, 3. Orchestration, 4. Web / API, 5. Tooling, 6. CI / CD, 7. Documentation, 8. Roadmap (next 90 days) |
| `#738–773` (4) | 17 | 0.11 | Knowledge Base — Agents ✅ COMPLETED (2026-03-27), Knowledge Base — Bradley + Market Cycles ✅ DONE (2026-03-27), Knowledge Base — Concepts (Round 2) ✅ COMPLETED (2026-03-27), Knowledge Base — Concep... |
| `#739–761` (2) | 17 | 0.11 | 0. Context, 1. Task Formalization, 10. Semantics, 11. Integration with Load Test, 2. Root Cause Analysis (RCA), 3. Correction Loop (Core), 4. Invariants (MUST NOT VIOLATE), 5. Validation Block |
| `#740` | 8 | 0.15 | Any, FailMode, FailureIsolator, FailureTrigger, Incident, IncidentSeverity, Prevent cascade failures by checking if new incident could trigger others., RollbackAction |
| `#741` | 15 | 0.18 | CephExecutor, CephHealth, CephStatus, ceph_exec(), detect_split_brain(), diagnose_ceph(), get_ceph_status_detail(), get_recovery_priority() |
| `#742–763` (2) | 9 | 0.14 | 3-step policy verification pipeline.     Runs BEFORE decision enters Safety Kern, Full verification pipeline.         Returns (approved, PolicyVerifier, Stable hash for policy versioning., Step 1 —... |
| `#743–764` (2) | 11 | 0.16 | 1]., AdmissionResult, Attempt degraded admission instead of hard reject., Compute composite risk score [0, DecisionContext, DecisionStatus, Environment snapshot at decision time., SafetyKernel, … (+1) |
| `#744` | 17 | 0.11 | Determinism Fix Plan — ATOMFederation-OS, FIX-1: `execution_gateway.py` — Nonce generation, FIX-2: `mutation_executor.py` — MutationExecutor RNG, FIX-3: `feedback_injection.py` — Feedback noise inj... |
| `#745` | 10 | 0.15 | Call, Extract DFA transitions from ExecutionGateway source., FunctionDef, JoinedStr, Path, Run extraction and return structured result., extract_from_file(), runtime_dfa_extractor.py — Extract tran... |
| `#746` | 17 | 0.11 | ATOMFederationOS v6.5 — Global Control Arbitrer + System Optimizer, Changelog, Implementation Sequence, Status, 🔴 GAP 1: Global Control Arbitrer, 🔴 GAP 2: System-Wide Optimization Objective, 🟡 GAP ... |
| `#747` | 17 | 0.11 | ATOMFederationOS v6.6 — Self-Modeling + Predictive Control + Decision Lattice, Changelog, Implementation Sequence, Status, 🔴 GAP 1: Self-Model (CRITICAL — missing entirely), 🔴 GAP 2: Predictive Con... |
| `#751` | 14 | 0.16 | # NOTE: `_degraded(reason, # TODO: implement the actual analysis., AgentResponse, Any, Convenience runner used by `agents/gitagent_registry.py`., Public entry point. Wraps `analyze` with the latenc... |
| `#755` | 17 | 0.11 | ACME account errors, Adding TLS to Existing Ingress, Architecture, Components, DNS-01 Challenge (for wildcard / custom domain), DNS-01 not working, Files, Next Steps |
| `#756` | 15 | 0.18 | Abstraction: reuse SSH host. EBC-compliant., FIX 1.4: Proper split-brain detection.     Split-brain = different parts of clus, FIX 3.2: Structured recovery actions.     Each action: action, Main en... |
| `#757` | 17 | 0.11 | 1. Install dependencies, 2. Set model paths, 3. Run locally, 4. Test, API usage, Configuration, Docker, End-to-end flow |
| `#760` | 3 | 0.14 | Return list of dead worker IDs, WorkerRegistry, WorkerStatus |
| `#762` | 17 | 0.11 | Distributed mini-AWS cluster: Ceph + Slurm + Ray + Kubernetes + AmneziaWG, Gates, home-cluster-iac, 🎯 Architecture Overview, 👤 Author, 📋 Ansible Roles, 📦 Components, 🗓️ Day 0–7 Deployment |
| `#765–770` (2) | 17 | 0.19 | export_agent(), import_agent(), list_agents(), main(), mcp_install_cli(), mcp_list_cli(), mcp_search_cli(), mcp_tools_cli() |
| `#766` | 9 | 0.16 | Any, IsolationLevel, PluginInstance, PluginRuntime, PluginSpec, PluginVersion, Sync wrapper for plugin execution., main() |
| `#771` | 17 | 0.16 | Import ideas into idea_tracker., garbage_collect(), generate_ideas(), get_latest_brief(), ideas_to_tracker(), list_briefs(), main(), parse_brief_content() |
| `#772` | 4 | 0.18 | Topology, TopologyChange, TopologyUpdater, TopologyVersion |
| `#774–775` (2) | 16 | 0.18 | AMREOutput, DelistFallback, Run full AMRE post-processing on agent signals:     1. Delisted ticker check, amre/karl_integration.py — KARL-010 Integration Layer Встраивает AMRE-контур (un, apply_fal... |
| `#776–803` (3) | 9 | 0.14 | AgentResponse, BaseAgent, Build a uniform degraded AgentResponse.          Args:             reason: One o, Build system prompt for the agent.          Includes:         1. Instructions.md, Главный... |
| `#777–819` (4) | 11 | 0.18 | Hybrid propagation: pure Kepler + optional ML residual correction.      Args:, HybridResult, ML model that predicts Kepler-vs-SwissEph residuals.     Trained on (JD, Print comparison table of Keple... |
| `#778–820` (4) | 16 | 0.12 | #001 — BlackRock-inspired architectural practices in AstroFin Sentinel V5, 1. The "One BlackRock Rule" → "One Data Room", 10. Reading list, 2. Federated plugin architecture, 3. The `@require_epheme... |
| `#779–821` (4) | 16 | 0.12 | KI-001 — Data Room is a draft, KI-002 — Manual registry edits, KI-003 — No Postgres in dev environments, KI-004 — LangGraph and asyncio.gather both active, KI-005 — 7 archived root-level agent dupl... |
| `#780–822` (4) | 11 | 0.15 | HealthResponse, Request, ab_compare(), auth_middleware(), check_postgres(), check_redis(), health_check(), karl_status() |
| `#781–814` (3) | 16 | 0.18 | Import ideas into idea_tracker., garbage_collect(), generate_ideas(), get_latest_brief(), ideas_to_tracker(), list_briefs(), main(), parse_brief_content() |
| `#782–823` (4) | 16 | 0.15 | Calmar: annualized return / max drawdown. Higher is better., EvaluationResult, Sortino: return / downside deviation. Higher is better., calmar_ratio(), enrich_result(), max_consecutive_losses(), me... |
| `#783–824` (3) | 7 | 0.15 | BaseStrategy, PerformanceRecord, Regime, Signal, StrategyConfig, StrategyResult, strategies/base.py — ATOM-STEP-11: Strategy Base Classes |
| `#784` | 13 | 0.17 | HealthResponse, Request, ab_compare(), auth_middleware(), check_postgres(), check_redis(), health_check(), karl_metrics() |
| `#785` | 13 | 0.12 | ACOS Trace Contract — enforced TraceRecorder interface., Any, Decision, ExecutionResult, FAIL FAST — raise if object violates TraceRecorderContract., Fetch trace. MUST return dict or None., Query t... |
| `#786` | 9 | 0.12 | ACOS TraceRecorder — fully contract-compliant implementation., Clear all traces. For testing only., Contract-compliant TraceRecorder.          Guarantees:     - get_trace() always, DeterministicTra... |
| `#787` | 5 | 0.18 | Any, ExecutionTrace, TraceNode, TraceStore, TraceType |
| `#788–811` (2) | 8 | 0.25 | Capability, CapabilityDenied, CapabilitySet, ExecutionContext, enforce(), enforce_all(), enforce_any(), register_role() |
| `#789` | 9 | 0.21 | ControlEvent, EventStore, Node, ctrl(), health(), main(), orch(), run_act() |
| `#790` | 11 | 0.14 | CorrectionCycleResult, EvolutionEngine, EvolutionRecord, Generate full evolution report., GenerationSummary, Return True if stuck pattern detected — meta-learner should intervene., Single evolution... |
| `#791–812` (2) | 12 | 0.16 | InjectionResult, Job, JobResult, NodeState, Result of job execution in simulator., Simulated compute node., SyntheticScheduler, Try to assign job to a node. Returns True if scheduled. |
| `#792` | 16 | 0.16 | Named stress scenario = profile + duration + targets., StressScenario, adversarial_scheduling(), burst_load(), cascading_failure(), normal_baseline(), skewed_hotspot(), sustained_overload() |
| `#793–813` (2) | 3 | 0.21 | MetricPoint, PrometheusCollector, TimescaleWriter |
| `#794` | 8 | 0.20 | Node mesh — manages the full connection graph of an ATOM cluster. Discovers peer, Queue, RPC package — real network transport for ATOMFederationOS.  Modules ------- prot, Synchronous entrypoint — b... |
| `#807` | 11 | 0.14 | End current generation and compute summary., Generate full evolution report., Record correction cycle result for evolution tracking., Return True if stuck pattern detected — meta-learner should int... |
| `#808` | 11 | 0.15 | BFTQC, BFTThreshold, QCValidationResult, bft_quorum_certificate.py — atom-federation-os v9.0+P7 BFT Quorum Certificate., validate_bft_qc(), ✅ BFTQC valid when ≥ 2f+1 signatures., ❌ BFTQC invalid if... |
| `#809` | 6 | 0.15 | Deterministic finite automaton for ExecutionGateway., Event, GatewayDFA, GatewayState, LTL: G(Exec -> NonceLocked U Act). Forward-only DFA: holds vacuously., LTL: not EF(Replay and Exec). G1 must p... |
| `#815` | 8 | 0.12 | Check if cluster is ready to execute.         Ready when quorum of nodes have st, Compute deterministic hash of startup sequence.         Same cluster config + sa, DeterministicStartupSequence, Get... |
| `#816` | 16 | 0.12 | 1. Суть loopcraft и сдвиг парадигмы, 10. Финальная мысль для обдумывания, 2. Пример: Autoresearch (Андрей Карпати), 3. Иерархия уровней автономности, 4. Экономика и ограничения, 5. Четыре условия э... |
| `#818` | 10 | 0.15 | All-zero inputs → sharpe=0.5, Build an EvaluationResult with ATOM-META-RL-004 fields populated., End-to-end ``compute()`` golden values., _make_result(), cost=0, dd_pen=0, pnl=0.5, stability=scale,... |
| `#825` | 11 | 0.18 | Decision input bundle from v8.1 observability layer., Governor gate decision., GovernorDecision, GovernorSignal, Hard gate evaluated before every mutation.      Combines:       - system health, Hum... |
| `#826` | 15 | 0.12 | DurableTaskQueue (минимальные правки), Epoch semantics (критично), Fail policy, GLOBAL TASK LIFECYCLE SPEC — единый control plane, Key schema, Ownership semantics, State enum, engine.py рефакторинг |
| `#827–873` (4) | 9 | 0.12 | Окно не может быть больше max_window_size., Окно не может быть меньше min_window_size., При высокой волатильности (vol >= 0.02) окно уменьшается., При низкой волатильности (vol <= 0.005) окно увели... |
| `#828` | 8 | 0.15 | Apply recovery from RecoveryActionObj., Create isolated replay engine seeded from scenario snapshot., Isolated engine for deterministic replay — no side effects on real system., RecoveryActionObj, ... |
| `#830–856` (3) | 9 | 0.21 | AgentPool, AstroFin Sentinel v5 — Thompson Sampling Agent Selector FIXED: thread-safe singl, Defines which agents participate in Thompson sampling., Get or create Thompson sampler — THREAD-SAFE., T... |
| `#831–874` (4) | 15 | 0.12 | 1. Цель, 10. История изменений, 2. Конфигурация ревью, 2.1. Trigger, 2.2. Audience, 2.3. Язык и стиль, 3. Overlap Matrix — кто что делает, 4.1. Soft rules (S1–S3) |
| `#832–864` (3) | 11 | 0.17 | Agent tool: semantic search over the knowledge base.      Agents call this when:, AstroFin Sentinel v5 — RAG Retriever Unified knowledge retrieval interface for a, FAISS-backed RAG retrieval.      ... |
| `#833–875` (4) | 15 | 0.21 | Test 1: All Switch Node types, Test 2: Switch routing logic, Test 3: Topology building with actual API, Test 4: Topology Visualizer, Test 5: Meta-Questioning Engine, Test 6: TopologyExecutor, Test ... |
| `#834–876` (4) | 10 | 0.21 | ABTest, ABTestConfig, ABTestResult, ATOM-META-RL-012: A/B testing for strategy versions., Public API: A/B test between two versions. market_data_b defaults to market_data, Welch t-test: returns (t_... |
| `#835–877` (4) | 14 | 0.23 | Any, ExportResult, Generate a deterministic slug from chromosome hash or UUID., Lazy-load AgentYamlValidator to avoid hard dependency on integrations.gitagent., _regime_label(), export_strategy(), ... |
| `#836–878` (4) | 8 | 0.22 | Any, Convenience function — generate HTML report., Generate HTML report for a completed evolution session.          Returns:, Generates standalone HTML reports for evolution sessions.      Usage:  ... |
| `#837` | 4 | 0.14 | BaseBroker, Binance spot/futures broker via CCXT., BinanceBroker, trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter |
| `#838` | 11 | 0.17 | ACOSSubmissionGateway, AstroFinTrace, ConstraintProfile, ExecutionNode, Single entry point for ALL AstroFin execution.     Flow: API request → Trace → L, Submit AstroFin job through ACOS governance... |
| `#839` | 6 | 0.22 | Any, Constraint, ConstraintGroup, ConstraintType, PolicyBlock, PolicyParser |
| `#840` | 5 | 0.23 | Any, DAGValidator, ValidationResult, Violation, ViolationType |
| `#841–861` (2) | 9 | 0.16 | Any, Binary prediction at given threshold., DataFrame, FailureXGBoost, Return P(failure) per sample., Series, Train XGBoost failure classifier., ndarray |
| `#842–862` (2) | 6 | 0.20 | Any, Load model artifact from registry., ModelRegistry, Path, Register a trained model version.          Returns:             version_id: e.g., Stable hash of model config + metrics for identity. |
| `#843–863` (2) | 7 | 0.18 | Apply policy weights to action score., Evaluates policy performance using cumulative regret.     regret(t) = U_best(t), Policy, PolicyEvaluator, PolicyTrial, Return empirical performance stats for ... |
| `#844` | 6 | 0.17 | Any, CompiledConstraint, Compiles DSL constraints into executable Python functions.          DSL examples, ConstraintCompiler, ConstraintRegistry, Runtime registry of active compiled constraints.  ... |
| `#845` | 15 | 0.24 | AST, ASTStats, Any, Path, _ast_node_to_hashable(), _hash_file_content(), generate_ast_hash(), main() |
| `#854` | 5 | 0.17 | Cooperative leader rotation. Lightweight (not full PBFT view-change)., ViewChangeEvent, ViewChangeManager, ViewChangeReason, view_change.py — Cooperative view-change mechanism for PBFT-lite v9.8 |
| `#855` | 6 | 0.17 | Any, CompiledConstraint, Compiles DSL constraints into executable Python functions.      DSL examples:, ConstraintCompiler, ConstraintRegistry, Runtime registry of active compiled constraints.     ... |
| `#858` | 9 | 0.17 | Build embedding from a feature vector (24h aggregates).         Maps raw feature, Build embedding from hardware + historical profile.         Produces a 16-dimens, Builds fixed-size embedding vecto... |
| `#859` | 9 | 0.13 | Count consecutive failures ending at current time., Linear regression slope over data points., Rate of change: (last - first) / count., _consecutive(), _derivative(), _mean(), _slope(), _std() |
| `#860` | 15 | 0.12 | 1. Создание Fine-grained PAT, 2. Настройка remote и push с PAT, 3. `.github/workflows/infra-ci.yml` (только проверки, 4. `.github/workflows/deploy.yml` (self-hosted runner, 5. Регистрация Self-Host... |
| `#869` | 11 | 0.16 | BasketMetrics, EvaluationResult, Reconstruct an EvaluationResult from a dict produced by ``to_dict``.          ``, Safely convert a numeric value to float, replacing NaN/Inf with None.      ATOM-, ... |
| `#870` | 10 | 0.12 | Deterministic fan-out for swarm: assign tasks to workers round-robin.         Sa, Deterministic task scheduler for Swarm/Async engines.      ALL scheduling decisi, DeterministicScheduler, Determini... |
| `#871` | 8 | 0.17 | Always select highest priority task. tick only for tie-breaking., Deterministic schedule for current tick.          Args:             tick: monoto, Deterministically order remaining tasks by (prior... |
| `#872` | 15 | 0.12 | 1. Восстановление из бэкапа, 2. Исправлены критические ошибки, 3. Production-ready pyproject.toml, 4. Обновлён README.md, 5. Обновлён .gitignore, AstroFin Sentinel V5 — Production Restore Report, C... |
| `#879` | 7 | 0.17 | Adjust weights based on observed outcomes of recent actions.          If stabili, Compute the global objective J for a given snapshot.          Parameters:, Global optimization objective for the AT... |
| `#880` | 15 | 0.23 | Bind env_hash to the existing system_snapshot.json., Compute and save env hash to formal_model/env_hash.json., Validate current environment against locked requirements.      Returns (is_valid, comp... |
| `#881` | 8 | 0.16 | Check whether (sender_id, Clear all state for a sender (used after view change or key rotation)., NonceCheckResult, NonceWindow, Per-sender sliding window of recent sequence numbers.      Fields:  ... |
| `#882` | 6 | 0.12 | ACME tenant accepts a valid-length API key (>= 16 chars)., ACME tenant requires API key — no key = 401., ACME tenant requires API key — short key rejected (len < 16)., Free tier has require_api_key... |
| `#883` | 9 | 0.17 | Default intraday volume curve (24 hourly weights).          Based on typical equ, Execute a VWAP order.          Args:             symbol: Trading pair, Get volume weight for a given slice number.,... |
| `#884–885` (2) | 14 | 0.13 | Full trace: DAG_CREATED → TRACE_RECORDED., INV1: Every action produces an event., INV2: No mutable truth — state is derived., INV3: Replay equivalence., INV4: Hash chain integrity., INV5: Trace det... |
| `#886–905` (3) | 7 | 0.18 | AuditLog, DecisionRecord, Воспроизвести конкретное решение по хешу состояния, Восстановление из dict, Найти похожие решения для анализа, Полная запись решения — воспроизводимая трассировка, Хранили... |
| `#888–935` (4) | 11 | 0.21 | _make_run(), backtest/test_metrics_agent.py — TDD tests for metrics_agent.py fixes  Tests:, test_list_respects_limit(), test_list_respects_symbol_filter(), test_list_returns_backtest_run_objects(),... |
| `#889–936` (4) | 13 | 0.20 | AgentSignal, Pressure Field Coordination (sandbox version).      Influence агента B на агента, apply_pressure_field + возвращает метрики для аналитики.      Returns:         (, apply_pressure_field... |
| `#890–937` (4) | 9 | 0.20 | Compute composite reward from trade outcome + astro factors., Compute discounted cumulative reward., Compute rewards for a batch of trades., Compute summary statistics from a list of rewards., Comp... |
| `#891–938` (4) | 8 | 0.13 | 11.1: EMA stabilization — first value seeds, 1]., BTC and ETH should have separate EMA states., EMA should clamp output to [-1, EMA should converge toward stable values., NOT 0., Oscillating values... |
| `#892–939` (3) | 14 | 0.13 | 1. Общее описание, 2. Архитектура системы, 3. 14 агентов — веса и задачи, 4. Meta-RL Engine — как работает, 5. Как запустить, 6. Дашборд — вкладки, 7. Переход в live-режим, A/B Testing |
| `#893–940` (4) | 8 | 0.20 | ATOM-META-RL-006: Composite ranking across 5 dimensions.     Accepts both Scored, Any, CompositeRankingEngine, Load all sessions and return top-n globally-ranked strategies., Ranked strategy with c... |
| `#894–941` (4) | 14 | 0.19 | ATOM-META-RL-009: Convert OAP drift report to adaptive GA params.      When drif, Any, OAPDriftReport, analyze_oap_drift(), get_adaptive_params_from_drift(), load_all_records(), load_session_record... |
| `#895–914` (2) | 3 | 0.22 | Integration tests for AstroCouncilAgent aggregation logic., TestAstroCouncilBasic, mock_response() |
| `#897–944` (3) | 8 | 0.15 | Adaptive slippage calculation.          Args:             side: "buy" or "sell", AdaptiveSlippageModel, Calculate slippage for a trade.          Args:             side: "buy" or "sell", Fixed-perce... |
| `#899` | 7 | 0.18 | Batch inference for multiple nodes., Compute composite risk score from predictions., Decision recommendation based on risk., Fetch latest features for node from TimescaleDB., Online inference for a... |
| `#900` | 13 | 0.38 | check_munge(), configure_worker(), create_cgroup_conf(), create_gres_conf(), create_slurm_conf(), info(), install_slurm(), main() |
| `#901–927` (2) | 6 | 0.21 | Auto-classifies incidents by severity.     Routes to appropriate response (rollb, Factory: create + classify + route incident., Incident, IncidentManager, Route to appropriate response by severity.... |
| `#902` | 14 | 0.13 | Быстрый старт (итог), Если что-то пошло не так, Запутался в окружениях, Команды SBS, Ошибка: `No module named 'typer'`, Ошибка: `command not found: sbs`, Руководство по установке ATOM Federation OS... |
| `#903` | 8 | 0.14 | Apply oscillation penalty to delta (scales magnitude down)., Get current state of the feedback loop., Human-readable summary of recent signal history., Returns (exploration_scale, Returns True if o... |
| `#904` | 14 | 0.13 | ✅ FIXES APPLIED (2026-04-16), ❌ CRITICAL-1: Determinism — not fully resolved, ❌ CRITICAL-2: SBS Dependency Isolation, ❌ CRITICAL-3: No CI/CD Enforcement, ❌ CRITICAL-4: Persistence Gap, ❌ CRITICAL-5... |
| `#906–934` (2) | 14 | 0.19 | AMREOutput, DelistFallback, Run full AMRE post-processing on agent signals:     1. Delisted ticker check, amre/karl_integration.py — KARL-010 Integration Layer Встраивает AMRE-контур (un, apply_fal... |
| `#916–947` (3) | 3 | 0.15 | Binance spot/futures broker via CCXT., BinanceBroker, trading/broker/binance.py — ATOM-STEP-9: Binance broker adapter |
| `#919` | 14 | 0.13 | 1. 🔴 Network Partition (split-brain), 2. 🔴 Asymmetric Partition, 3. 🔴 Packet Corruption, 4. 🔴 Latency Spike (Jitter Storm), 5. 🔴 Node Isolation (C minority partition), 6. 🔴 Message Loss Storm, 7. 🔴... |
| `#920` | 6 | 0.20 | CausalDAG, Check if two DAGs are structurally identical.         Returns (is_identical, I2: Causal DAG from execution must be identical to causal DAG from replay., Lightweight causal ancestry graph... |
| `#924` | 14 | 0.38 | day3_compute.sh script, detect_os(), info(), install_common(), install_docker(), install_munge(), install_nvidia(), install_nvidia_container_toolkit() |
| `#925` | 13 | 0.38 | check_munge(), configure_worker(), create_cgroup_conf(), create_gres_conf(), create_slurm_conf(), day4_slurm.sh script, info(), install_slurm() |
| `#926` | 14 | 0.42 | create_mount_script(), create_pools(), day6_ceph.sh script, deploy_ceph(), deploy_manual(), info(), install_ceph(), main() |
| `#928` | 14 | 0.41 | apply_sealed_secret_templates(), check_prereq(), create_secrets_engine(), create_static_secrets(), deploy_sealed_secrets(), deploy_vault(), err(), vault-init.sh script |
| `#929` | 9 | 0.17 | Check for dangerous command patterns. Returns pattern name or None., InputContractValidator, ROMA Input Contract Layer — Strict validation (NOT generative). Rejects empty/fa, ROMAValidationError, R... |
| `#932` | 5 | 0.18 | ConflictResolutionMatrix, Formal resolution of inter-layer control conflicts.     Precedence matrix: highe, Return the higher-priority layer between two., Set winning weight of 'a' over 'b'., TestC... |
| `#933` | 3 | 0.13 | DriftProfiler: degradation detection., TestDriftProfiler, test_observability.py — planning_observability layer tests. All 30 tests for tra |
| `#945` | 9 | 0.19 | Add a node to the whitelist., Check whether sender_id is permitted to send under this policy.          Args:, Enforces node-level sender restrictions on inbound messages.      Modes:       A, Origi... |
| `#948–996` (4) | 12 | 0.22 | Comprehensive health metrics for KARL system., Determine overall system status from health metrics., KARLHealthMetrics, amre/karl_diagnostics.py - ATOM-021: Enhanced KARL Diagnostics, compute_karl_... |
| `#949–973` (3) | 9 | 0.20 | AgentResponse, AstroFin Sentinel v5 — ElectoralAgent Electional astrology for trading entry tim, Calculate 0-10 muhurta score., ElectoralAgent, ElectoralAgent — Muhurta specialist for trading.     ... |
| `#950–997` (4) | 13 | 0.16 | Decorator that times ``func`` and increments the per-agent run Counter.      Wor, Return the canonical ``sentinel_<agent_snake>_latency_seconds`` Histogram., Return the canonical ``sentinel_<agent_... |
| `#954–998` (4) | 4 | 0.19 | AstroRLConfig, AstroRLLoop, AstroState, core/astro_rl_engine.py - ATOM-STEP-6: Astro RL Engine |
| `#955–999` (4) | 9 | 0.14 | Different agents should have independent keys., Full reward pipeline., Per-agent reward breakdown., Pipeline always returns clamped values., RewardResult has all required fields., Smoothed reward s... |
| `#956–1001` (4) | 11 | 0.14 | ATOM-R-041: Idea → Outcome Tracking, CLI, KPI, Scoring Formula, Self-Questioning Integration, Жизненный цикл, Интеграция в KARL, Следующие шаги |
| `#957–1002` (4) | 13 | 0.14 | Muhurta — Искусство выбора времени, Overview, Trade Entry Rules, Yoga (не путать с физическими упражнениями), Благоприятные Yoga для трейдинга:, ⚠️ WAIT (Score 4.0-6.4):, ✅ ENTER (Score >= 6.5):, ❌... |
| `#958–1004` (4) | 13 | 0.18 | Any, Convert List[OHLCV] → market_data dict for StrategyEvaluator.      Compatible wi, Reverse converter: market_data dict → List[OHLCV].      Used when meta_rl output, denormalize_symbol(), market... |
| `#959–1005` (4) | 9 | 0.27 | VersionedEliteStorage, _data_dir(), _load_index(), _save_index(), _vdir(), _vindex_path(), get_versioned_storage(), meta_rl/versions_storage.py -- ATOM-META-RL-012: Versioned Elite Storage + A/B T |
| `#960–1007` (3) | 13 | 0.20 | Create a Flask test app with a protected endpoint., Missing API key should return 401 with JSON error., Valid API key should allow access., When REQUIRE_AUTH=false, Wrong API key should return 403.... |
| `#961` | 13 | 0.14 | Application Inventory, Architecture, Deployment Workflow, GitOps Deployment with ArgoCD, Image Updates, Manifest Labels, Manual sync, Monitoring |
| `#962–988` (2) | 3 | 0.22 | Any, DeterminismController, ExecutionContext |
| `#963–986` (2) | 7 | 0.20 | Backend, Build a single feature vector for node_id.         Uses TimescaleDB if backend=', Computes feature vectors from either TimescaleDB (primary) or Prometheus (fallba, Convert raw metrics dict... |
| `#964` | 12 | 0.21 | Cache lookup — returns cached risk_score for a given input hash., ML Inference API — FastAPI application for real-time risk scoring.  Endpoints:, _cache_get(), _cache_put(), _cached_predict(), _get... |
| `#965–989` (2) | 6 | 0.25 | DataFrame, LoadXGBoost, Return predictions for all targets., Series, Train separate regressors for queue_depth, gpu_util, memory_util., ndarray |
| `#966` | 13 | 0.42 | detect_os(), info(), install_common(), install_docker(), install_munge(), install_nvidia(), install_nvidia_container_toolkit(), install_python_ml() |
| `#967` | 13 | 0.46 | create_mount_script(), create_pools(), deploy_ceph(), deploy_manual(), info(), install_ceph(), main(), mount_cephfs() |
| `#968–990` (2) | 4 | 0.22 | BudgetCycle, ExecutionBudget, ExecutionBudgetController, StageResult |
| `#969` | 6 | 0.18 | Any, DecisionRecord, Find k decisions with payloads most similar to `payload`.         Similarity = f, Last N records, Record a decision and optionally its outcome. Returns decision_id., decision_m... |
| `#970` | 12 | 0.14 | Any, Any, Configure the global TracerProvider + MeterProvider with OTLP export.      Idemp, OTEL Exporter v7.0 — OTLP trace (and optionally metrics) export.  Sets up:   - T, Reset OTel state (for t... |
| `#971` | 13 | 0.14 | Planned, Pop!_OS 24.04 — AI/Dev Workstation Setup, Release Notes, Stage Map, v1.0 — Initial (2026-03-28), v1.1 — Full Stack (2026-04-02), v1.2 — CUDA + Docker + k3s (2026-04-04), v1.3 — k3s Multi-N... |
| `#982` | 13 | 0.14 | CausalFingerprint.to_dict() serializes correctly., Different events produce different fingerprints., Fingerprint changes on add, Verifier correctly detects divergence., Verifier correctly detects e... |
| `#985` | 13 | 0.14 | Adding a New Partner, Architecture, Branding in API Responses, Caching, Email Templates, Example Partners, Overview, Priority Chain |
| `#987` | 4 | 0.22 | GPUMetric, GPUObservabilityLayer, Tracks GPU metrics for observability.     Metrics: gpu_utilization, WorkerHealthScore, job_success_ |
| `#991–1000` (2) | 13 | 0.14 | Architecture Diagram, Conclusion, Dashboard Evaluation: LangGraph vs n8n, Executive Summary, Implementation Strategy, Integration Points, LangGraph Evaluation, Limitations |
| `#1003` | 10 | 0.16 | Any, CalibrationReport, Drop the singleton (used by tests)., One reliability-diagram bin: predicted vs. observed frequency., ReliabilityBin, Return the process-wide CalibrationTracker singleton., g... |
| `#1006–1009` (2) | 3 | 0.24 | Integration tests for AstroCouncilAgent aggregation logic., TestAstroCouncilBasic, mock_response() |
| `#1008` | 4 | 0.16 | Policy applied when an invariant violation is detected., Runtime SBS enforcement layer.      Integrates SystemBoundarySpec and GlobalInva, SBSRuntimeEnforcer, ViolationPolicy |
| `#1010` | 13 | 0.20 | Unit tests for the Flask `require_api_key` decorator.  These tests verify authen, When REQUIRE_AUTH=false, create_test_app(), test_require_api_key_auth_disabled(), test_require_api_key_correct_key(... |
| `#1011` | 5 | 0.21 | ABC, IEvaluator, IEvaluator, IEvaluator, IEvaluator |
| `#1012` | 7 | 0.23 | A computed gain adjustment to apply to the actuator., Any, Apply the gain adjustment to a list of commands.         Modifies command magnit, Gain adjustment applied to command magnitudes., GainAdju... |
| `#1013–1030` (3) | 6 | 0.21 | ATOM-META-RL-006: Lightweight audit record for Meta-RL strategy evaluations., Add a MetaRLDecisionRecord to the log., MetaRLDecisionRecord, Separate audit log for Meta-RL strategy discovery records... |
| `#1015–1047` (4) | 12 | 0.24 | Wait for PostgreSQL to become available with retry logic.     Logs each attempt., _create_pg_engine(), get_database_url(), get_db_stats(), get_engine(), get_session_factory(), is_postgres_available... |
| `#1016–1048` (4) | 12 | 0.32 | Index, build_index(), cmd_build(), cmd_search(), cmd_stats(), get_embedding(), load_chunks(), load_index() |
| `#1017–1054` (4) | 12 | 0.27 | check_protected_files_in_diff(), is_protected_file(), log_audit(), main(), Возвращает True, Проверяет, если в рабочем дереве нет изменений защищённых файлов., относится ли файл к защищённым., … (+4) |
| `#1018–1055` (4) | 11 | 0.15 | A class with name ending in 'Agent' must inherit BaseAgent., Archived files are exempt from the inherit check., If a module imports ephemeris but no method has @require_ephemeris, The template is h... |
| `#1019–1051` (3) | 11 | 0.15 | Additional: ConditionEvaluator edge cases., Test 1: uncertainty > 0.6 → adds GroundingLoop., Test 2: bias detected → adds Critic role., Test 3: OOS fail > 0.4 → tighten policy., Test 4: Correct rol... |
| `#1020–1052` (3) | 4 | 0.23 | Portfolio, Position, PositionSide, trading/portfolio.py — ATOM-STEP-8: Portfolio & Position Tracking ============== |
| `#1021` | 11 | 0.15 | Test 3: OOS fail > 0.4 → tighten policy., Test 4: Correct rollback when SwitchNode fails., test_bias_switch_adds_critic(), test_condition_evaluator(), test_oos_fail_tightens_policy(), test_rollback... |
| `#1022–1040` (2) | 8 | 0.27 | RecoveryEngine, escalate(), load_escalation(), load_state(), main(), run_cycle(), save_escalation(), save_state() |
| `#1023–1041` (2) | 12 | 0.29 | reboot_node(), restart_ceph(), restart_ceph_manager(), restart_ceph_mon(), restart_ceph_osd(), restart_nvidia_driver(), restart_ray_head(), restart_ray_worker() |
| `#1024` | 12 | 0.22 | DataFrame, Label failure events: 1 if node went down within horizon, LabelEngine, Series, label_failure(), label_from_job_outcome(), label_load_exceeded(), rolling_label(), … (+1) |
| `#1025` | 13 | 0.17 | Any, DataFrame, Load XGBoost model + feature list. Returns (model, Return a synthetic sample for SHAP tree explainer initialisation., _init_shap(), _on_startup(), feature_names, load_model(), … (+2) |
| `#1026` | 10 | 0.22 | Handler, build_metrics(), ceph osd dump --format json, ceph status --format json, get_ceph_df(), get_ceph_osd_dump(), get_ceph_pg_dump(), get_ceph_status() |
| `#1027` | 12 | 0.41 | create_ai_scheduler(), create_slurm_ray_bridge(), final_summary(), health_check(), info(), main(), ok(), setup_ceph_ray_integration() |
| `#1028` | 12 | 0.17 | DataFrame, End-to-end training: split → train failure + load models → register.     Returns, Generate a synthetic dataset once per test module., Integration test — ML Pipeline (Train → Predict → Me... |
| `#1029` | 3 | 0.17 | ATOMCluster controller — custom ATOM state snapshot., ClusterState, NodeState |
| `#1037` | 10 | 0.22 | build_metrics(), ceph df --format json, ceph osd dump --format json, ceph pg dump --format json, ceph status --format json, get_ceph_df(), get_ceph_osd_dump(), get_ceph_pg_dump() |
| `#1039` | 5 | 0.17 | OVERLAY_ROOT, SANDBOX_STATE_DIR, SANDBOX_VERSION, engine_sandbox_runtime.sh script, sandbox_init() |
| `#1042` | 12 | 0.41 | create_ai_scheduler(), create_slurm_ray_bridge(), day7_integration.sh script, final_summary(), health_check(), info(), main(), ok() |
| `#1043` | 12 | 0.51 | err(), header(), info(), integration-test.sh script, main(), ok(), stage1_preflight(), stage2_deploy() |
| `#1045` | 5 | 0.24 | ...] sorted highest-first., Computes global priority of feedback loops.     priority = urgency * 0.7 + stabi, FeedbackPrioritySolver, FeedbackSignal, Return [(layer, TestFeedbackPrioritySolver, pri... |
| `#1046` | 3 | 0.27 | GovernorThresholds, TestStabilityGovernor, Tunable thresholds for the stability governor. |
| `#1053` | 12 | 0.15 | Background, Commands, Dependencies, Environment, Progress, Scope: 5 Tasks, Sprint 2 — Production Hardening, Task 1 — Vault / Sealed Secrets (🔴 Critical) |
| `#1056` | 3 | 0.19 | AsyncWebhookQueue, calculate_application_fee(), test_application_fee() |
| `#1057` | 11 | 0.15 | Test 3: OOS fail > 0.4 → tighten policy., Test 4: Correct rollback when SwitchNode fails., test_bias_switch_adds_critic(), test_condition_evaluator(), test_oos_fail_tightens_policy(), test_rollback... |
| `#1058` | 4 | 0.28 | ProofTrace, SymbolicExecutionChecker, ViolationRecord, main() |
| `#1059` | 5 | 0.21 | AdmissionController, Build DecisionContext from raw request., DecisionContext, K8s-style admission controller.     All decisions flow: decision → constraint →, Primary admission endpoint.         R... |
| `#1060` | 11 | 0.44 | ExecutedNode with defaults., enode(), make_plan(), make_trace(), pnode(), test_alignment.py — v10.0 Alignment Layer integration tests., test_composite(), test_l1_structural() |
| `#1061` | 11 | 0.17 | 1. Дедупликация агентов, 2. Фикс dual-mode теста, 3. Результаты тестов, 4. Канонический импорт, 5. Следующие ATОМы, DEDUP-001 + Dual-Mode Test Fix — Итоговый отчёт, Импорты обновлены (7 файлов), Ис... |
| `#1062` | 6 | 0.24 | BufferEntry, ReplayBuffer, Trajectory, _select_best_trajectory(), amre/replay_buffer.py — Replay Buffer for trajectory learning, get_default_buffer() |
| `#1063–1114` (4) | 10 | 0.30 | Simulated BTC data for stress testing (Binance 451 unavailable)., backtest/atom_014_stress_test.py — ATOM-014: KARL Stress Test, bar_to_market_state(), compute_metrics(), generate_synthetic_signals... |
| `#1064–1115` (4) | 7 | 0.18 | Get current EMA. Returns 0.0 for unknown keys., Per-key EMA for reward stabilization.      Key design:     - First call with a k, Reset one key or all keys., RewardEMA, Update EMA for key. First ca... |
| `#1065–1116` (4) | 11 | 0.24 | Apply EMA smoothing to raw reward.      key : str         Symbol (e.g. "BTCUSDT", Full reward breakdown., Full reward pipeline: raw → EMA → clamped.      Returns RewardResult with full b, compute_a... |
| `#1066–1117` (4) | 7 | 0.17 | 11.2: Reward direction correctness., BUY + negative price → negative reward., BUY + positive price → positive reward., High confidence → larger magnitude., NEUTRAL → 0 regardless of price., SELL + ... |
| `#1067–1118` (4) | 11 | 0.24 | Get current database status for monitoring., Main entry point for DB initialization.     Call this once at application startu, _init_sqlite_fallback(), apply_raw_sql_schema(), db/init.py - ATOM-DB-... |
| `#1068–1123` (3) | 4 | 0.20 | ModeEnforcer, ModeLimits, TradingMode, trading/mode.py — ATOM-PRODUCTION: Trading Mode System ========================= |
| `#1069` | 11 | 0.17 | Test that function signatures haven't changed., Test that legacy mode works identically to before changes., test_backward_compatibility_signatures(), test_dual_mode_detection(), test_legacy_mode_pr... |
| `#1070–1105` (2) | 3 | 0.24 | Append-only log with O(1) trace index., Event, EventLog |
| `#1071` | 6 | 0.17 | A batch of labeled examples for training/validation., A supervised learning example: features → label., Convert to flat dict for CSV export., Export a split to CSV., LabeledExample, MLBatch |
| `#1072` | 11 | 0.17 | Evaluator, FailureXGBoost, FeedbackCollector, LabelEngine, LoadModel, ModelRegistry, Predictor, ml_engine — ACOS ML Prediction Layer (v5)  Dataset   → Models   → Training   → I |
| `#1073–1110` (2) | 6 | 0.24 | Fallback: simplest heuristic — lowest average regret., Meta-learning over policy performance.     Learns which policy to use given work, MetaLearner, PolicyRecommendation, PolicyTrial, Return ranke... |
| `#1074` | 11 | 0.17 | Added, Architecture, Changelog — atom-federation-os, Guarantees, Invariants, System Type, Tests, v9.0 — Federation Core |
| `#1076` | 6 | 0.24 | Any, Bridge: connects DAGFingerprint to InvariantContract kernel.      Provides check, Check whether DAG fingerprint in state is valid/stable.         Used as invarian, Compute fingerprint; store a... |
| `#1077` | 6 | 0.26 | ConsensusDominationAlert, NodeWeightsSnapshot, TrustCollapseAlert, TrustSkewDetector, TrustSkewReport, skew_detector.py — v9.6 Trust Skew + Collapse Detector  Monitors weight distribu |
| `#1078` | 11 | 0.17 | ATOMFederationOS — SBS v1, Architecture, Installation, Quick Usage, Running Tests, SBS v1 Components, Stack Layers, ✅ Status |
| `#1079` | 6 | 0.24 | Ack, Any, AtomMessage, AtomServicer, ServicerContext, gRPC servicer that bridges real network → local runtime receive queue.     SBS e |
| `#1080` | 11 | 0.17 | Быстрый старт — одна команда, Ожидаемые результаты, Предварительные требования, Создание тестового сценария (если список пуст), Установка и проверка atom-federation-os (HARDENING v2), Цель, Шаг 1: ... |
| `#1086` | 8 | 0.17 | If all resolvers in the chain fail, If primary resolver raises, blueprint tries the secondary., get_price() returns None., test_blueprint_falls_back_to_secondary_on_error(), test_blueprint_returns_... |
| `#1087–1125` (3) | 11 | 0.17 | Test that CLI correctly detects --masfactory flag., Test that MASFactory failure triggers graceful fallback., Test that function signatures haven't changed., Test that legacy mode works identically... |
| `#1088–1122` (2) | 7 | 0.21 | AdaptiveSlippageModel, OrderBookSimulator, TWAPConfig, TWAPExecutionReport, TWAPExecutor, TWAPSlice, trading/execution/twap.py — ATOM-STEP-10: TWAP Execution Strategy |
| `#1091` | 5 | 0.30 | ByzantineDetector, ByzantineIndicator, Monitors trust+consensus state for Byzantine-adjacent patterns.      Signals emi, _test_byzantine_detector(), byzantine_detector.py — Byzantine fault detectio... |
| `#1092` | 5 | 0.21 | Fallback to RayJob if cluster uses Ray operator., K8sCompiler, ROMA Execution Bridge — JSON → Kubernetes Job Compiler Fixed: uses nvidia.com/gp, Security + correctness validation., Transforms ROMA ... |
| `#1093` | 7 | 0.17 | Choose winner by score, Choose winner from N entries by (score, Deterministic tie-breaking for alignment layer.          Invariant: same inputs, GlobalTieBreaker, Sort items by score descending, ha... |
| `#1097` | 8 | 0.18 | ChangeType, DAG Incremental Fingerprint — v8.5  Architecture:   DAGFingerprint         — ful, DAGValidator, Formal DAG invariants (used by InvariantRegistry).      I1:  Acyclic           —, KahnSor... |
| `#1098` | 7 | 0.20 | Compute delta between current and previous fingerprint.          Returns list of, DAGChange, DAGFingerprint, Delta between two DAG fingerprints., Diff current fp against another (or None)., Immutab... |
| `#1099` | 6 | 0.20 | Compute content_hash and full_hash from content + parents., IncrementalNodeHash, Layer = max(parent_layers) + 1; roots get layer=0., Per-node hash incorporating parent hashes.      hash = H(       ... |
| `#1101–1119` (2) | 4 | 0.23 | Any, PostgresReplayBuffer, db/karl_replay.py — PostgresReplayBuffer (ATOM-019) Stores KARL trajectories in, get_default_pg_buffer() |
| `#1102` | 11 | 0.17 | 1. Architectural Invariant (Formal), 10. Version History, 2. Execution Algebra (Enforced Chain), 3. Dominator Tree, 4. MutationExecutor — Final Capability Interface, 5. ExecutionGateway — Construct... |
| `#1103` | 11 | 0.17 | 1. Mission, 10. Where to read next, 2. Pipeline at a glance, 3. Reward function, 4. Evolution cycle, 5. Walk-forward validation, 6. Strategy pool & diversity, 7. Persistence & replay |
| `#1104` | 10 | 0.38 | choose_key(), error(), generate_key(), info(), main(), show_key(), update_remote(), verify() |
| `#1106` | 9 | 0.18 | A single feature vector at a point in time for a specific node., FeatureSpec, FeatureVector, JobType, LabelType, NodeRole, Specification for a single feature., Validate a feature vector. Returns li... |
| `#1107` | 4 | 0.20 | Call after acquiring GPU lock, Call after job finishes, HeartbeatClient, Probe GPU info (mock for testing) |
| `#1108` | 11 | 0.17 | Contributing to home-cluster-iac, ✅ PR Checklist, 🆘 DR / Restore, 🏗️ Directory Structure, 🔧 Initial Setup, 🚀 Adding New Nodes, 🛠️ Prerequisites, 🛰️ GitOps (ArgoCD) |
| `#1109` | 11 | 0.42 | create_ray_scripts(), day5_ray.sh script, info(), install_ray(), main(), ok(), start_head(), start_workers() |
| `#1111` | 7 | 0.17 | 1.0]., End-to-end tests against the live FastAPI inference server., GET / → must return JSON with at least a 'version' field., GET /health → 'status' must be 'healthy'., GET /metrics → must contain... |
| `#1112` | 5 | 0.17 | CycleRecord, ReplanRecord, ScoreEvolutionPoint, TraceEventType, plan_trace_logger.py — planning_observability layer Records full execution trace |
| `#1113` | 11 | 0.17 | AI Stack, Containers, Desktop, Dev Tools, Security, pop-os-setup: Программы и компоненты установки, Как работает установка, Критичность компонентов |
| `#1120` | 6 | 0.20 | Add Q-value with automatic cleanup (FIFO eviction)., Add chromosome with automatic truncation., Bounded KARL state with automatic memory limits., KARLState, Return memory usage stats for monitoring... |
| `#1124` | 11 | 0.17 | Architecture Specification v1.0 (2026-04-17), Closed-Loop System Model, Comparison with Existing Systems, Core Innovation: Decision Gate, Execution Commands, Four Coupled State Systems, Layer Inven... |
| `#1126` | 10 | 0.17 | test_bft_byzantine_node_slashed(), test_bft_thresholds(), test_double_sign_detection(), ✅ BFT threshold calculations., ✅ Byzantine node (double-sign) is slashed and excluded from quorums., ✅ Double... |
| `#1127–1128` (2) | 7 | 0.22 | AdmissionController, AdmitDecision, AdmitResult, Check if any eligible node has enough free memory., Enforces cluster admission policy.     All job submissions MUST pass through her, Returns (decis... |
| `#1129` | 4 | 0.24 | AdmissionController, Build DecisionContext from raw request., K8s-style admission controller.     All decisions flow: decision → constraint →, Primary admission endpoint.         Request:          ... |
| `#1130–1192` (4) | 10 | 0.31 | _discover_agents(), export_agent(), export_all(), generate_agent_yaml(), generate_prompt_md(), generate_schema_py(), generate_tests_yaml(), generate_tools_py() |
| `#1131–1161` (3) | 10 | 0.35 | MarketState, Trajectory, amre/trajectory.py — Market state + Trajectory + TrajectoryStep, compute_trajectory_metrics(), market_state_hash(), trajectory_from_dict(), trajectory_from_state(), traject... |
| `#1132` | 10 | 0.18 | ArgoCD Installation Role for k3s Cluster, Artifacts, Compatibility: home-cluster-iac (k3s, Dependencies, Kubernetes 1.29+), Overview, Required Variables, file: ansible/roles/argocd/README.md, … (+1) |
| `#1134–1193` (3) | 6 | 0.18 | Alpha пересчитывается при изменении window_size., EMA продолжает работать после увеличения окна., EMA продолжает работать после уменьшения окна., TestEMAWorksAfterWindowChange, Счётчик увеличиваетс... |
| `#1136–1194` (4) | 5 | 0.20 | Async cache with Redis backend and in‑memory fallback., RedisCache, Очистить весь кэш (только fallback)., Получить значение по ключу., Сохранить значение с TTL (секунд). |
| `#1137–1174` (3) | 7 | 0.25 | AstroCouncil, Signal, _signal_val(), build_council_result(), compute_weighted_signal(), core/council/council.py - AstroCouncil: Multi-Agent Voting System, resolve_conflict() |
| `#1139–1196` (4) | 4 | 0.31 | ResidualCorrection, ResidualModel, core/residual_model.py - ATOM-STEP-4: Residual Correction Model, main() |
| `#1140–1197` (4) | 10 | 0.22 | Any, Append a record to a JSONL file safely., Load all records from a JSONL file safely., Safely dump data to JSON file. Returns True on success., Safely load JSON file. Returns default on failure.... |
| `#1141–1198` (3) | 8 | 0.18 | BasketMetrics, EvaluationResult, ScoredStrategy, Возвращает экземпляр с нулевыми метриками., Метрики корзины стратегий., Результат оценки стратегии., Стратегия с оценкой (используется в эволюции и ... |
| `#1142–1199` (4) | 10 | 0.45 | _compute_oap_adjustments(), _fetch_price(), main(), run_astro_flow(), run_electoral_flow(), run_karl_sentinel_v5(), run_macro_flow(), run_sentinel_v5() |
| `#1143–1200` (3) | 7 | 0.27 | ExecutionSanityChecker, MarketState, OrderRequest, SanityConfig, SanityResult, ValidationStatus, trading/execution/sanity.py — ATOM-PRODUCTION: Execution Sanity Layer ========== |
| `#1144–1172` (2) | 8 | 0.18 | ACOS Scheduler Contract — enforced scheduler interface., Any, Compile DAG into executable schedule. MUST return dict with 'nodes'., ENFORCED contract for all Scheduler implementations., FAIL FAST —... |
| `#1145–1183` (2) | 3 | 0.18 | Idempotency check — O(1) lookup. Patch 2., MemoryTraceStorage, Thread-safe in-memory storage with idempotency support. |
| `#1146` | 5 | 0.18 | DeterministicTraceRecorder, Emit NODE_FAILED event., Emit governance event., EventSourcedEngine, Idempotent execution.                  PATCH 2: Check has_trace() BEFORE executi |
| `#1147` | 3 | 0.38 | Compiles job submissions into executable DAGs.     Guarantees: every node has ex, DAGCompiler, DAGNode |
| `#1149` | 5 | 0.27 | ActionResult, Any, ExecutionContext, ExecutionGate, GateDecision |
| `#1150` | 4 | 0.27 | Any, ConstraintNode, GuardRule, PolicyCompiler |
| `#1151–1185` (2) | 5 | 0.31 | JobResult, Simulate one job scheduling attempt., SolverLatencyScenario, Tests P99 latency spikes from ILP + Twin + Beam under load., run_all() |
| `#1152–1186` (2) | 3 | 0.33 | DriftSample, StateDriftScenario, run() |
| `#1153–1181` (2) | 5 | 0.20 | Call after each job completes — tracks toward retrain threshold., Check if retraining conditions are met., Execute retraining and update last metrics., Path, Retrainer |
| `#1154–1187` (2) | 10 | 0.18 | Architecture Summary, Known Limitations, Links, Overview, Performance Benchmark, Release Notes — ACOS SCL v6.0.0, ✅ 10 Core Invariants, 🔧 3 Required Patches (v2 spec) |
| `#1155` | 10 | 0.47 | create_ray_scripts(), info(), install_ray(), main(), ok(), start_head(), start_workers(), test_ray() |
| `#1156–1180` (2) | 5 | 0.24 | EnsembleDecision, EnsembleScheduler, Policy, Runs multiple policies simultaneously, Select best policy based on expected utility.         final_action = argmax E[U(, selects best expected utility. |
| `#1157` | 10 | 0.18 | 1. Agent Inventory, 2. Stubs / Empty Placeholders, 4. Code Quality Observations, 5. Recommendations, 6. Migration System, 7. RAG Knowledge System, AstroFin Sentinel V5 — System Audit Report, Coverage |
| `#1158` | 11 | 0.18 | 10. LangGraph Belief-Guided Architecture, Changes from Old Graph, Conditional Routing (unchanged), Core Idea, File: `langgraph_schema.py` (rewritten), How BeliefGuard Works, Logs Example, Pool Thre... |
| `#1170` | 9 | 0.24 | Causal parents as list (not set) are handled correctly., Identical event sequence from replay., MockEvent, Same sequence but SBS count and drift_score differ., Tests for cross_layer_invariant_engin... |
| `#1171` | 8 | 0.18 | ACOS Engine Contract — enforced execution engine interface., Any, ENFORCED contract for execution engines., Execute compiled DAG. MUST return dict with 'results' and 'state'., ExecutionEngineContra... |
| `#1178` | 10 | 0.27 | 0 otherwise., Apply rolling label: look ahead `horizon` rows and compute aggregate., DataFrame, Label failure events: 1 if node went down within horizon, Label from job outcome stored in job_events... |
| `#1179` | 10 | 0.18 | Default Credentials, MikroTik hEX S — Initial Setup Guide, Prerequisites, Reset to Factory Defaults, Step 1 — Change Default Password, Step 2 — Configure WAN (ether1), Step 3 — Enable REST API (Req... |
| `#1182` | 3 | 0.31 | AuthMiddleware, Request, Unified auth middleware — API Key + optional JWT. |
| `#1188` | 6 | 0.18 | Get stable ID for registered pod., Register a pod's stable identity., ReplicaIdentityStabilityMapping, Verify pod's stable identity hasn't changed., r'''         Get stable identity for pod.       ... |
| `#1189` | 3 | 0.27 | ControlArbitrator, Resolves competing actuator signals across control layers:     DRL / SBS / Coher, TestControlArbitratorBasics |
| `#1191` | 4 | 0.25 | Normalize then cap each layer gain individually., Prevents gain explosion across multiple feedback loops.     Normalizes so total, SystemWideGainScheduler, TestSystemWideGainScheduler |
| `#1201` | 10 | 0.18 | 3-Way Reconciliation, Failure Modes, How It Works, Integration, Metrics Exposed, Orphan Job Recovery, Purpose, ROMA Reconciliation Engine — Architecture |
| `#1202` | 10 | 0.18 | Contributing to roma-execution-bridge, ⚠️ Breaking Changes, ✅ PR Checklist, 🏗️ Architecture Overview, 📊 Observability, 🚀 Release Process, 🛠️ Dev Environment, 🛰️ GitOps (ArgoCD) |
| `#1203` | 5 | 0.25 | Any, ROMAClient, ROMAException, ROMAJob, ROMASDK — Python client for ROMA Execution Platform. Usage:     from roma_sdk im |
| `#1204` | 7 | 0.25 | Any, PriceQuote, PricingEngine, PricingTier, ProfitCalculator, ROMA SaaS Pricing Engine — Dynamic GPU compute pricing., load_mult() |
| `#1205` | 6 | 0.20 | Adaptive slippage calculation.          Args:             side: "buy" or "sell", Calculate slippage for a trade.          Args:             side: "buy" or "sell", Fixed-percent slippage model — no ... |
| `#1206–1268` (4) | 8 | 0.33 | MarketState, Trajectory, amre/similarity.py — Trajectory similarity + Q* estimation, estimate_q_star(), is_similar_trajectory(), knn_q_star(), select_top_k_trajectories(), trajectory_distance() |
| `#1207` | 7 | 0.20 | Any, Apply recovery to engine's layer state. Returns result summary., FailureScenario, Map failure_type → RecoveryActionObj with target and parameters., RecoveryActionObj, RecoveryActionObj, Выполн... |
| `#1208` | 7 | 0.29 | Request, Stripe Webhook Microservice — FastAPI app., WebhookResponse, _enqueue_event(), _sync_tenant(), _verify(), stripe_webhook() |
| `#1209` | 9 | 0.20 | Architecture Snapshot — v9.10, Design Invariants, External Dependencies, Known Limitations, Layer Architecture, Next: v10 — Evolution / Versioned Semantics, System Type, Test Coverage |
| `#1211–1270` (4) | 6 | 0.20 | 1]., Abhijit Muhurta should boost reward., Astro reward always in [-1, Astro reward component., EXTREME regime should penalize reward., Rahu Kaal should penalize reward., TestAstroReward |
| `#1212–1271` (4) | 9 | 0.20 | A/B Testing — ATOM-META-RL-012, Confidence Levels, Iteration Over All Chromosomes, Key Functions, Main Class: `ABTestRunner`, Overview, Result Interpretation, Statistical Tests |
| `#1213–1273` (4) | 9 | 0.20 | 8 Типов Choghadiya, Choghadiya — Ведические периоды дня, Muhurta Score, Overview, Rahukaal (Рahu Kaal), Дневные vs Ночные, ✅ Благоприятно (ENTER):, ❌ Неблагоприятно (AVOID): |
| `#1214–1274` (4) | 8 | 0.24 | APIKeyConfig, Load and validate API keys from environment.      Security rules:     1. Keys NE, Return masked key for logging (NEVER the real key)., Validate that live mode can be safely enabled.  ... |
| `#1215–1263` (3) | 5 | 0.24 | Any, Strategy, Trading strategy with chromosome, and full serialization., generation tracking, meta_rl/strategy.py — Strategy type for Meta-RL (ATOM-META-RL-008), Восстанавливает Strategy из словар... |
| `#1216–1275` (4) | 8 | 0.22 | Any, Convenience timing context for ad-hoc measurements.      Yields the elapsed time, Decorator: record latency + confidence of an agent's run() method.      Usage:, Idempotent: records a single a... |
| `#1217–1280` (4) | 9 | 0.20 | 7 workflow files., Architecture Overview, AstroFin Sentinel V5, CI/CD, Development with Ralph Loop, Documentation, Monitoring Links, Quick Start |
| `#1218` | 9 | 0.20 | Test that CLI correctly detects --masfactory flag., Test that MASFactory failure triggers graceful fallback., Test that function signatures haven't changed., Test that return type hasn't changed., ... |
| `#1219–1284` (5) | 7 | 0.31 | Run healthcheck as subprocess and return (stdout, exitcode)., run_healthcheck(), stderr, test_healthcheck_db_check(), test_healthcheck_exit_code_ok_when_all_good(), test_healthcheck_ollama_check(),... |
| `#1221–1288` (4) | 9 | 0.36 | cmd_daily_brief(), cmd_idea_tracker(), cmd_leaderboard(), cmd_reset(), cmd_scores(), cmd_select(), cmd_simulate(), main() |
| `#1223` | 5 | 0.22 | Any, Deserialize from dict. Handles both dict and tuple payloads., Event, Immutable event record.      prev_hash is set by EventLog.append() at append tim, Serialize to dict for storage. Does NOT i... |
| `#1224` | 5 | 0.20 | Emit NODE_FAILED event. Write-side ONLY., Emit governance event. Write-side ONLY., EventSourcedEngine, Execute DAG. Returns trace_id ONLY., Write-side only execution engine.          INVARIANTS (en... |
| `#1225` | 9 | 0.22 | ACOS AmneziaWG Integration — Patches for ACOS Core  Provides: - Patch 1a: DAGVal, PATCH 1a: DAGValidator network check.      Before scheduling a DAG that requires, PATCH 3a: Get Prometheus-compatib... |
| `#1226–1255` (2) | 3 | 0.29 | ACOS PostgreSQL Storage Backend — primary persistent storage., PostgreSQL-backed trace storage. Requires DATABASE_URL env var., PostgresTraceStorage |
| `#1227` | 9 | 0.20 | Contributing to AsurDev, ✅ PR Checklist, 🏗️ Project Structure, 🐳 Docker, 📐 Code Style, 📦 Release Process, 🔒 Security, 🛠️ Development Setup |
| `#1228` | 4 | 0.20 | Compile DAG into executable schedule. Contract-required method., Determine scheduler for job., Routes jobs to Slurm or Ray based on workload type., SchedulerAdapter |
| `#1229` | 5 | 0.33 | Any, ExecutionSandbox, SandboxResult, SandboxViolation, ViolationType |
| `#1230–1258` (2) | 4 | 0.29 | ObjectiveReweighter, ObjectiveWeights, Self-adjusting objective function weights.     weights = weights + lr * gradient, Update weights using gradient ascent on negative regret.         performance... |
| `#1231` | 9 | 0.20 | ATOM Core — Monorepo, Deterministic API, Known Issues, Архитектура, Интеграция с AstroFinSentinelV5, Контракты, Пакеты, Сборка |
| `#1232` | 10 | 0.20 | 5. NONDETERMINISM ELIMINATION MAP, 5.1 All Nondeterministic Sources — Complete Inventory, 5.2 Implementation — Fix Each Source, N1-N3: execution_context.py — uuid.uuid4() for context_id, N11: adapt... |
| `#1233` | 3 | 0.20 | ControlSignal, Return all signals sorted by priority (highest first), no clear., v7.5 — Control Orchestration Layer Deterministic supervisory arbitration over al |
| `#1246` | 6 | 0.20 | Append or patch trace data. MUST return None., ENFORCED contract for all TraceRecorder implementations., Persist full execution trace. MUST return trace_id (str)., Query traces by filter. MUST retu... |
| `#1249` | 9 | 0.20 | CI Configuration, Canonical Root, Execution Environment Consistency Guide, Problem, Running Tools, Single Source of Truth Rules, Tool Inventory, sys.path Order |
| `#1250` | 9 | 0.20 | 1. Почему возникает ошибка `workflow scope`, 2. Ручная настройка SSH, 2.1 Генерация SSH-ключа, 2.2 Добавление публичного ключа на GitHub, 2.3 Проверка подключения, 2.4 Переключение remote URL на SS... |
| `#1251` | 3 | 0.24 | PluginMetadata, PluginRegistry, ROMA Plugin Registry — Discovery, dependency resolution., versioning |
| `#1252` | 5 | 0.20 | Emit NODE_FAILED event. Write-side ONLY., Emit governance event. Write-side ONLY., EventSourcedEngine, Execute DAG. Returns trace_id ONLY., Write-side only execution engine.      INVARIANTS (enforc... |
| `#1253` | 7 | 0.22 | BFTVote, Receive a COMMIT vote from another node., Receive a PREPARE vote from another node.         Accumulate until we reach prep, RequestState, When we reach PREPARED, broadcast COMMIT vote., te... |
| `#1254` | 8 | 0.27 | Auth info populated by middleware and readable via Depends()., AuthContext, FastAPI dependency — reads auth state set by AuthMiddleware.     Runs after full, FastAPI-native auth dependency — runs A... |
| `#1256` | 9 | 0.20 | 1. Git Push & CI/CD Setup, 2. Inventory Variables (`ansible/group_vars/all.yml`), 3. `post_deploy.sh`, 4. `.env` for ML API, 5. Manual Verification Checklist (10 items), 6. Roadmap (Optional Improv... |
| `#1257` | 7 | 0.27 | Balance classes using SMOTE oversampling., Full training pipeline: build → split → train → evaluate → register.          Ar, Path, Train XGBoost with RandomizedSearchCV hyperparameter tuning.     H... |
| `#1259` | 9 | 0.44 | create_issuers(), err(), install_cert_manager(), log(), main(), patch_kong_tls(), setup.sh script, validate() |
| `#1260–1272` (2) | 6 | 0.20 | Test CLI command execution., Test list-agents CLI command., Test mcp-recommended CLI command., Test mcp-search CLI command., TestCLICommands, Tests for MCP Adapter |
| `#1264` | 6 | 0.20 | Constructing RewardConfig() must not warn., Off-sum weights must warn (UserWarning) and renormalise., RewardConfig invariants and warning behaviour., TestRewardConfig, Vanilla RewardConfig() must h... |
| `#1265` | 3 | 0.20 | Closed-form: 1 / (1 + exp(-steepness * clip(s, TestSharpeComponent, _sharpe_component: logistic over clipped Sharpe., ±clip))). |
| `#1267` | 8 | 0.20 | Called at module import time to prevent direct access.          If this module i, Intercept instantiation — verify Gateway context is active.                  Thi, Metaclass for MutationExecutor — ... |
| `#1269` | 5 | 0.31 | Decide position size based on current policy + exploration noise.         Return, OnlineTrainer, REINFORCE policy gradient update.         Computes gradient estimate from recent, REINFORCE-style on... |
| `#1281` | 9 | 0.20 | 2026-04-18), Architecture (Frozen, Files, Growth Targets (Layer 2 Active), Kubernetes Deployment (Sprint 1 — Complete, Layer 1), Maturity State, ROMA — Agent Memory, … (+2) |
| `#1282` | 9 | 0.36 | Generate SLSA v1 provenance predicate., Generate complete supply chain attestation bundle., Generate in-toto Layout for multi-step supply chain., Generate in-toto Link metadata for a single step., ... |
| `#1283` | 3 | 0.22 | Evaluate invariants across quorum of nodes.          peer_states: {, SBSDistributedClient, Update this node's layer state snapshot. |
| `#1285` | 5 | 0.20 | Alternating overshoot/undershoot → oscillating., Gain ratio near 1.0 → stable., High control saturation → SATURATED mode., Oscillation index computation and mode detection., TestOscillationDetection |
| `#1289–1341` (2) | 8 | 0.53 | import_dashboards(), log(), main(), notify(), post_deploy.sh script, run_loadtest(), setup_alerts(), verify_cluster() |
| `#1290` | 4 | 0.22 | Compute adaptive gain multiplier.         Reduces gain when oscillating or overs, Compute damping factor based on oscillation index.         High oscillation → lo, Compute oscillation index from ga... |
| `#1291–1292` (2) | 5 | 0.33 | AdversarialScenario, AdversarialSimulator, Apply adversarial conditions to simulated cluster state., Generates worst-case scenarios to stress-test policy robustness., Run optimizer through adversar... |
| `#1293–1352` (4) | 8 | 0.36 | Any, MarketState, amre/astro_reward.py - ATOM-021: Astro-enhanced Reward Function, compute_astro_reward(), get_astro_market_phase(), get_lunar_phase_score(), get_nakshatra_score(), get_planetary_as... |
| `#1294–1322` (3) | 7 | 0.22 | ATOM-META-RL-006: Factory — create and record a MetaRLDecisionRecord     from a, Any, Get or create the Meta-RL audit log singleton., get_meta_rl_audit_log(), record_meta_rl_decision(), Анализ OAP ... |
| `#1295–1296` (2) | 5 | 0.33 | ScheduleRequest, ScheduleResponse, Submit job to selected partition via slurm wrapper., schedule(), submit() |
| `#1299–1353` (4) | 8 | 0.22 | API Key authentication., Decorator for Flask: checks X-API-Key header., FastAPI dependency: checks X-API-Key., Raise RuntimeError if auth is required but API_KEY is missing., Request, fastapi_requi... |
| `#1300–1354` (4) | 8 | 0.22 | 1. Финальный Backup (обязательно выполнить первым), 2. Локальный запуск (Linux/macOS/Windows+WSL), 3. Production deployment, 4. Активация live-режима (реальные деньги), 5. Следующие шаги, Docker, s... |
| `#1301–1355` (4) | 8 | 0.22 | 1. Папка `knowledge/daily_brief/`, 2. CLI-команда `python tools/thompson_cli.py daily-brief`, 3. Генерация ATOM-идей, ATOM-R-040: Интеграция ежедневного агента в рабочий процесс, Будущие расширения... |
| `#1302–1356` (4) | 8 | 0.33 | Analyze a digest file., Generate ATOM proposals from analysis., Run full pipeline: analyze → propose → log., cmd_analyze(), cmd_log(), cmd_propose(), cmd_run(), main() |
| `#1303–1357` (4) | 8 | 0.22 | Agent Integration, Architecture, AstroFin Sentinel v5 — RAG Knowledge System, Domains, Index Build CLI, RAG Index Structure, Retrieval Flow, Retriever CLI |
| `#1304–1358` (4) | 8 | 0.58 | cprint(), main(), test_caching(), test_fallback(), test_meta_questioning_integration(), test_metrics(), test_parallel_execution(), test_visualization() |
| `#1305–1359` (4) | 5 | 0.25 | MetaRLConfig, Return list of validation warnings. Empty = all good., True if configured for real market data (not sandbox)., Unified production configuration for Meta-RL engine., meta_rl/config.py ... |
| `#1306–1348` (3) | 5 | 0.25 | ATOM-META-RL-015: Bayesian optimization of Meta-RL hyperparameters., HyperOptimizer, Run a short evolution and return best reward., get_hyper_optimizer(), meta_rl/hyperopt.py — ATOM-META-RL-015: Hy... |
| `#1307–1365` (4) | 8 | 0.31 | Path, extract_comment_text(), main(), process_file(), Если строка является однострочным комментарием с кириллицей, Обрабатывает один .py файл, Переводит текст комментария на английский., возвращает... |
| `#1310–1369` (4) | 8 | 0.33 | check_ollama(), check_postgresql(), check_venv(), main(), run_all_checks(), Проверка виртуального окружения., Проверка доступности Ollama API., Проверка доступности PostgreSQL (попытка docker-compo... |
| `#1312` | 5 | 0.28 | Any, PATCH 3: Returns state with node_graph_resolution and execution_order., Read-side state projection.          PATCH 3: enrich_projection() adds node_grap, Rebuild standard state., StateProjection |
| `#1313` | 4 | 0.36 | Any, ExecutionState, StateReducer, _payload_to_dict() |
| `#1314` | 5 | 0.39 | Any, ContractViolation, DAGValidator, Event, EventType, Validates DAG, and Trace contracts.          Guarantees:     - validate_d |
| `#1315–1337` (2) | 5 | 0.33 | Build feature dataset with failure labels for ML training.          Args:, DataFrame, DatasetBuilder, Query TimescaleDB for failure/load labels within horizon window., datetime |
| `#1316` | 8 | 0.28 | Any, Call POST /predict on the ML Inference API and return risk_score.      Args:, ML Inference Client — thin wrapper around the /predict API.  Used by any compone, Return True if the ML API is rea... |
| `#1317` | 3 | 0.39 | EnvelopeBounds, EnvelopeReport, StabilityEnvelope |
| `#1318` | 3 | 0.25 | Any, AtomicQueue, ExecutionGateway |
| `#1319` | 9 | 0.22 | 12. Thompson Hyperparameters, CLI Usage, Files, K — agents to select per pool, Recommended Tuning Workflow, Simulation: bonus=1.0 vs bonus=0.0 (k=3, exploration_bonus — unseen agent prior boost, mi... |
| `#1335` | 8 | 0.22 | ACOS Trace Contract — enforced TraceRecorder interface., Any, Decision, ExecutionResult, FAIL FAST — raise if object violates TraceRecorderContract., Validate trace has required fields., validate_t... |
| `#1340` | 5 | 0.28 | Any, PATCH 3: Returns state with node_graph_resolution and execution_order., Read-side state projection.      PATCH 3: enrich_projection() adds node_graph_re, Rebuild standard state., StateProjection |
| `#1345` | 5 | 0.25 | DeterministicPodScheduler, Get the primary node (first in startup order)., r'''         Assign deterministic replica ID.         hash(pod_name) % total_rep, r'''         Compute deterministic pod s... |
| `#1349` | 3 | 0.22 | TestExecutionCostPenalty, _execution_cost_penalty: clipped cost., meta_rl/test_reward.py — Golden tests for RewardCalculator.  Golden tests that p |
| `#1350` | 5 | 0.22 | Half saturation in trades → half the bonus (with full win_rate)., TestStabilityBonus, _stability_bonus: trade-count * win-rate saturation., trades == threshold, trades >= stability_trade_norm and w... |
| `#1351` | 8 | 0.22 | 1. Pattern A: `from __future__ import annotations` added to 14 agents, 2. Pytest markers registered + applied to 33 test files, 3. `meta_rl/basket.py`, 4. `.bak` files, Changes, Note on Pattern A i... |
| `#1364` | 8 | 0.22 | ROMA — Distributed Execution Platform, ⚡ Commands, 🏗️ Architecture, 📄 Version, 📐 System Classes, 📦 Core Modules, 🔑 Features, 🚀 Quick Start |
| `#1370–1443` (2) | 5 | 0.25 | 20th переходит в mature., TestWarmupBlend, В warmup phase больше вес на raw signal., Первые 19 решений используют BLEND_WARMUP=0.3, После 20 решений используется BLEND_MATURE=0.15., Тест warmup pha... |
| `#1371–1374` (2) | 5 | 0.25 | TestLagAdjustment, lag_adj < 0 когда EMA ниже raw (сигнал опережает вверх)., lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)., lag_adj масштабируется корректно: |lag_adj| < 1 для разумных отк... |
| `#1372–1373` (2) | 5 | 0.32 | AgentSpec, Agents that MUST pass L8+L9 before execution., get_agent(), get_governance_gated_agents(), list_agents() |
| `#1375–1408` (2) | 7 | 0.25 | Decorator that blocks agent execution if Swiss Ephemeris is unavailable.      Us, EphemerisUnavailableError, P, Raised when agent requires Swiss Ephemeris but it's not available., T, require_epheme... |
| `#1376–1445` (5) | 7 | 0.25 | Alerts, AstroFin Sentinel V5 - Deployment Guide, Environment Variables, Health Checks, Kubernetes, Quick Start, Services |
| `#1377–1446` (4) | 7 | 0.25 | Nakshatras — 27 Лунных Мансионов, Overview, Pada (Четверти), Лучшие Nakshatras для трейдинга:, Правила для Muhurta, Таблица Nakshatras, Худшие Nakshatras для трейдинга: |
| `#1378–1447` (4) | 7 | 0.25 | 1. Anthropic представила "Dreaming" и multi-agent orchestration для Claude Managed Agents (Public Beta), 2. Graph-of-Agents: новый graph-based фреймворк для мультиагентной координации LLM, 3. OverM... |
| `#1379–1448` (4) | 7 | 0.25 | 1. MARS: Role-Based Multi-Agent Collaboration (~50% reduction in token usage), 2. EMS: Efficient Majority-then-Stopping для multi-agent voting (~32% fewer agents), 3. AgentScope v2.0.1: Agent Team ... |
| `#1380–1449` (4) | 7 | 0.39 | ATOM-META-RL-003: Fetch live/paper market data via CCXT., Generate historical market data using mock (for --mode=historical)., get_market_data_historical(), get_market_data_live(), main(), parse_ar... |
| `#1381–1455` (4) | 7 | 0.36 | _extract_paths(), body) tuples., main(), parse(), r'''Parse KNOWN_ISSUES.md text into a list of {id, r'''Pull file paths out of the 'Affected' line; fall back to body scan., r'''Split KNOWN_ISSUES.... |
| `#1382–1458` (5) | 4 | 0.25 | 0° ≤ ν < 360° for all M., 360)., M=30° → E ≈ 47.6° (known reference)., Newton-Raphson produces bounded E for all M in [0, TestKeplerEquation, e=0.5 |
| `#1383–1459` (4) | 7 | 0.32 | Generate training data: (features, Train a RandomForestRegressor on residual data., generate_training_data(), main(), ndarray, residuals_arcmin)., train_residual_model(), training/train_residual_mo... |
| `#1384–1461` (5) | 7 | 0.25 | Build a convergence line chart (mean + max reward per generation)., Build a grouped bar chart comparing sessions., Build an HTML comparison table for selected strategies., build_comparison_chart(),... |
| `#1385–1462` (5) | 6 | 0.29 | Div, Toast, Wrap multiple toasts., make_toast(), make_toast_container(), web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005) |
| `#1390–1427` (2) | 7 | 0.54 | check_port(), cmd_status(), cmd_switch(), get_tunnel_status(), load_config(), main(), save_config() |
| `#1391–1428` (2) | 4 | 0.32 | Normalized trace record for persistent storage.     All fields are simple types, TraceRecord, _utcnow(), datetime |
| `#1392` | 7 | 0.32 | AstroFinTrace, ConstraintProfile, ExecutionNode, Factory to build a trace with standard ACOS AstroFin structure., Serialize trace to dict for JSON / TSDB / Ceph storage., build_trace(), trace_to_di... |
| `#1393` | 3 | 0.29 | Decision, GovernanceGate, L8 + L9 mandatory gate. NO execution without approval.     Every DAG passes thro |
| `#1394–1422` (2) | 7 | 0.39 | Compute and display node embeddings., Continuously push metrics and build feature vectors., main(), parse_args(), run_continuous(), run_embedding(), run_export() |
| `#1395` | 3 | 0.39 | Any, HashChain, compute_deterministic_hash() |
| `#1396–1429` (2) | 3 | 0.43 | MLRiskIgnoredScenario, Node, run() |
| `#1397–1430` (2) | 5 | 0.36 | Build Prometheus text metrics., Handler, build_metrics(), get_slurm_nodes(), get_slurm_queue() |
| `#1398` | 7 | 0.25 | ACOS — Autonomous Constrained Optimization System, Architecture, Data Flow, Git History, Layer Maturity, Quick Start, Repo |
| `#1399–1431` (2) | 7 | 0.32 | Any, Compute per-component score breakdown.     Higher available resources → higher s, Filter nodes by job type + memory., Stateful node selection:       1. Load nodes from DB (not Prometheus direc... |
| `#1400–1432` (2) | 6 | 0.50 | command_exists(), day2-vpn.sh script, info(), install_wg(), ok(), warn() |
| `#1401–1433` (2) | 7 | 0.64 | check_ceph(), check_nodes(), check_ray(), check_slurm(), check_wireguard(), health_check.sh script, log() |
| `#1402` | 4 | 0.36 | Greedy fallback when ILP is too large., ILPResult, ILPSolver, Solves: max U(x) subject to hard constraints.     Uses scipy minimize with penal |
| `#1403–1434` (2) | 3 | 0.29 | BeamPruner, PrunedCandidate, Prunes candidate space using beam search with variance estimation.     score = E |
| `#1404` | 7 | 0.25 | 12. SUCCESS CRITERIA, 13. CI DETERMINISM GATE, 14. SUMMARY SCORECARD, 8. ASYNC DETERMINISM FIX, 8.1 SwarmEngine / AsyncExecutionEngine, 8.2 DeterministicScheduler Integration, ATOM-META-RL-019 — De... |
| `#1405` | 5 | 0.32 | Ack, AtomMessage, Channel, None on, Send an AtomMessage to the remote node.         Returns Ack on success, Streaming send for batched delivery. |
| `#1406` | 8 | 0.25 | 11. Agent Selection Logging, API, Belief Update Still Primary, File: `core/belief.py` + `migrations/0007_agent_selection_log.sql`, How It Works, New Table: `agent_selection_log`, Pool Inference Map... |
| `#1407` | 8 | 0.25 | 9. Thompson Sampling (Agent Selection), Agent Pools, Algorithm, CLI, Files, Key Decisions, Selection Order (dependency-aware), Thompson vs Static Weights |
| `#1419` | 5 | 0.32 | BaseHTTPRequestHandler, Handler, Parse `wg show wg0` output., build_metrics(), parse_wg_show() |
| `#1420` | 5 | 0.25 | ENFORCED contract for all storage backends., Fetch trace. MUST return dict or None., Query traces. MUST return list[dict]., StorageBackendContract, Write trace. MUST return trace_id (str). |
| `#1423` | 3 | 0.32 | BFTQCBuilder, test_bftqc_builder_threshold(), ✅ BFTQCBuilder builds QC only when threshold reached. |
| `#1424` | 4 | 0.36 | ACOSSubmissionGateway, Single entry point for ALL AstroFin execution.     Flow: API request → Trace → L, Submit AstroFin job through ACOS governance pipeline.         Returns: trace_dic, main() |
| `#1438` | 7 | 0.25 | Healing cooldown, Kubernetes Operator v7.0 — ATOM Federation OS Control Plane, Как развернуть, Реакционный цикл, Режимы работы, Структура, Что сделано |
| `#1441` | 3 | 0.25 | Quadratic: dd = 0.5 → scale * 0.25., TestDrawdownPenalty, _drawdown_penalty: scale * dd^2 with NaN/Inf fallback. |
| `#1442` | 6 | 0.25 | Deterministic scheduling strategies — no random., DeterministicScheduler v1.0 — ATOM-META-RL-014  Fully deterministic task schedul, Result of one scheduling decision., ScheduleResult, SchedulingStr... |
| `#1444` | 6 | 0.36 | Signal, _signal_val(), build_council_result(), compute_weighted_signal(), core/council/council.py - AstroCouncil: Multi-Agent Voting System, resolve_conflict() |
| `#1457` | 6 | 0.25 | test_protected_endpoint_accepts_valid_key(), test_protected_endpoint_rejects_wrong_key(), test_protected_endpoint_requires_auth(), Без заголовка X-API-Key защищённый эндпоинт возвращает 401., С вер... |
| `#1460` | 4 | 0.29 | FeedbackSignal, Ingest a new feedback signal., Record a feedback signal and update internal distribution., Single feedback observation from environment. |
| `#1463–1539` (4) | 3 | 0.33 | Any, HierarchicalPolicy, amre/hierarchical_policy.py — Hierarchical Policy + Regime Detection |
| `#1465–1540` (4) | 6 | 0.29 | AsyncClient, Close the shared client (e.g., Return a reusable httpx AsyncClient singleton., Shared async HTTP client for agent data fetching., close_http_client(), get_http_client(), on shutdown). |
| `#1466–1542` (4) | 6 | 0.48 | _init_schema(), _migrate(), _reset(), _show_status(), db/__main__.py — Entry point for: python -m db.init  ATOM-DB-MIGRATION-002 Usage, main() |
| `#1467–1543` (4) | 6 | 0.43 | Migrate sessions to PostgreSQL via DecisionRecordRepository., Path, Read all sessions from SQLite history.db., get_sqlite_sessions(), main(), migrate_sessions() |
| `#1468–1544` (4) | 6 | 0.29 | Audit Log, Authentication Flow, Monitoring & Alerts, Rate Limiting, Safety Gate (execution layer), Security Architecture |
| `#1469–1545` (4) | 6 | 0.29 | Agent Instruction Template — Эталон для всех агентов, Запреты, Обязанности, Пример, Стиль ответов, 🤖 {AGENT_NAME} |
| `#1470–1546` (4) | 6 | 0.29 | Core Principle, Corrective Waves (3 waves), Elliott Wave Theory, Fibonacci Ratios, Impulse Waves (5 waves), Trading Application |
| `#1471–1547` (4) | 6 | 0.29 | 1. **Graph-of-Agents (GoA) — масштабируемый graph-based фреймворк для мультиагентной коллаборации LLM**, 2. **Agent Q-Mix — RL-подход к динамическому выбору топологии коммуникации агентов**, 3. **C... |
| `#1472–1548` (4) | 6 | 0.29 | **1. Google ADK Python v2.0.0 — Production-grade Multi-Agent Workflow Engine**, **2. Claude Code v2.1.147 — Workflow Tool для Deterministic Multi-Agent Orchestration**, **3. Swarms Framework — Comp... |
| `#1473–1549` (4) | 6 | 0.52 | Muhurtha — Electoral Astrology Calculator Based on B.V. Raman's "Muhurtha" princ, datetime, get_houses(), get_panchang(), jd_from_datetime(), print_muhurtha() |
| `#1474–1550` (4) | 6 | 0.33 | AstroFin Sentinel v5 — Router Agent Routes user queries to appropriate specialis, QueryType, RouterOutput, route_query(), Роутит пользовательский запрос в нужный тип.      Правила:     - Если спраш... |
| `#1475–1558` (4) | 6 | 0.43 | Run both modes and return comparison dict., _run_real_mocked(), _run_synthetic(), compare(), main(), В CI мы не можем поднять реальных агентов, иден, поэтому эмулируем результат |
| `#1476–1560` (4) | 3 | 0.29 | The template is hand-written to pass all 9 checks., test_validator_passes_on_template(), tests/architecture/test_validate_agent.py ====================================== |
| `#1479–1563` (5) | 6 | 0.29 | test_agent_selection_increments_counter(), test_signal_distribution_increments(), test_thompson_params_gauge_updated(), После выбора агентов через _select_for_flow счётчик должен инкрементироваться... |
| `#1480–1564` (5) | 5 | 0.43 | Concrete agent for testing., MockAgent, test_build_prompt_handles_ollama_unavailable(), test_build_prompt_includes_rag_results(), test_build_prompt_no_rag_when_disabled() |
| `#1484–1514` (2) | 3 | 0.38 | ConstraintCompiler, ConstraintType, Injects governance constraints into DAG as executable nodes.     L9 is NOT optio |
| `#1487–1527` (2) | 6 | 0.52 | adversarial_analysis(), classify(), compute_violations(), detect_dynamic(), get_imports(), run() |
| `#1488–1522` (2) | 3 | 0.29 | FeedbackCollector, Pull completed jobs from PostgreSQL state_store, Record a single job outcome to TimescaleDB for ML training., write to TimescaleDB.         R |
| `#1489` | 4 | 0.38 | Handler, Parse `wg show wg0` output., build_metrics(), parse_wg_show() |
| `#1490–1513` (2) | 4 | 0.33 | Candidate, CandidateGenerator, Generate ranked placement candidates for all pending jobs.         Returns top-K, Generates K-best placement candidates using beam search.     Stage 1: ML ranking |
| `#1491` | 7 | 0.29 | 2. DETERMINISTIC KERNEL DESIGN, 2.1 Architecture Overview, 2.2 API Specification, 2.3 Integration Points, DeterministicClock, DeterministicRNG, DeterministicUUIDFactory |
| `#1492` | 6 | 0.52 | err(), log(), ok(), pop-os-setup.sh script, step(), warn() |
| `#1493` | 5 | 0.29 | Any, Hard boundary validation gate.          Evaluates the full system state against, Immutable specification of system hard boundaries.      These flags define the U, Return last recorded violatio... |
| `#1494` | 6 | 0.33 | Replay recorded failure incidents., Replay recorded failure incidents., _run_replay_json(), replay_cmd(), run_replay(), sbs/cli_replay.py — sbs replay CLI command. |
| `#1512` | 3 | 0.38 | Invoice, InvoicingEngine, ROMA Invoicing — Invoice generation, payment tracking. |
| `#1515` | 4 | 0.29 | AstroCouncil, CouncilResult, core/council/runner.py — AstroCouncil Runner, run_council() |
| `#1520` | 3 | 0.38 | MarketplaceListing, PluginMarketplace, ROMA Plugin Marketplace — Publishing, lifecycle governance., signing |
| `#1521` | 4 | 0.29 | Called when this node receives a new execution request.         If we are the pr, Primary issues PRE-PREPARE for a validated request., Process a PRE-PREPARE vote (from primary or propagation)., Req... |
| `#1523` | 6 | 0.29 | Branch Protection -- AstroFin Sentinel V5, How to Add an Exemption, How to Configure, Required Settings, Required Status Checks (must pass before merge), Why These Settings? |
| `#1526` | 6 | 0.57 | dr-drill.sh script, err(), log(), ok(), require(), warn() |
| `#1528–1529` (2) | 6 | 0.62 | acquire_lock(), is_primary_alive(), log(), main(), promote_backup(), slurm_ha_failover.sh script |
| `#1534` | 4 | 0.29 | DeterministicInitContainerOrder, StartupState, r'''         Get deterministic init container execution order.          Order is, r'''     Deterministic init container ordering for pod startup.     ... |
| `#1537` | 3 | 0.38 | Composite trace health score (0..1).          Combines:           - completeness, Fraction of consecutive eval scores within ±0.1 (0..1)., Fraction of plans that have eval_score events (0..1). |
| `#1538` | 6 | 0.29 | PR1 — CompromiseAgent (preflight snapshot), Snapshot, Грабли / нюансы, Изменённые / новые файлы, Контракт сигналов, Тесты |
| `#1541` | 4 | 0.33 | PolicyParams, Reset parameters to best observed configuration., Trainable policy parameters., TrainingState |
| `#1557` | 6 | 0.29 | Architecture Freeze, Core Platform, Enterprise, Product, ROMA Changelog, v1.0.0 (2026-04-17) — First Stable Release |
| `#1559` | 5 | 0.52 | check_cosign(), cosign_keyless_sign_attestation(), generate_attestation_bundle(), h(), verify_from_rekor() |
| `#1565–1603` (3) | 3 | 0.33 | Deserialize from dict., Добавить запись решения, Импорт записей из JSON |
| `#1566–1658` (4) | 5 | 0.47 | Any, amre/ensemble_selection.py — Ensemble diversity selection, ensemble_diversity_score(), select_ensemble(), select_ensemble_by_confidence() |
| `#1569–1659` (4) | 5 | 0.60 | format_code_black(), is_valid_python(), normalize_code(), safe_write_code_file(), write_code_file() |
| `#1570–1624` (2) | 4 | 0.40 | CouncilMember, CouncilResult, Signal, core/council/types.py — AstroCouncil data types |
| `#1571–1661` (4) | 5 | 0.33 | ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector, Components, Dependencies, Expected, Why P1? |
| `#1572–1662` (4) | 5 | 0.33 | ATOM-DEDUP-001: Дедупликация агентов, Execution, Impact, Problem, Задача |
| `#1573–1663` (4) | 5 | 0.33 | ATOM-GITAGENT-003: Phase 3 GitAgent, Components, Dependencies, Reason, When |
| `#1574–1664` (4) | 5 | 0.33 | 1. **Pressure Field Coordination** (arXiv:2601.08129), 2. **CrewAI v2.3 — Enhanced Multi-Agent Orchestration**, 3. **AutoGen 0.4 — Universal Agent Communication Protocol**, Ключевые находки, 🌐 Mult... |
| `#1575–1665` (4) | 5 | 0.33 | 1. Microsoft Conductor — open-source YAML-оркестратор multi-agent систем, 2. REDEREF — training-free маршрутизация для multi-agent LLM систем, 3. CoalT — game theory coalition formation для multi-a... |
| `#1576–1666` (4) | 5 | 0.33 | 1. Microsoft Agent Framework — Handoff pattern + Foundry Hosted Agents (BUILD 2026), 2. Cloudflare Agents 0.14.0 — durable multi-agent orchestration + Skills engine, 3. R-HAN: Reliable Hierarchical... |
| `#1577–1667` (4) | 5 | 0.33 | 1. Microsoft Agent Framework Python 1.8.0 — стабилизация Magentic multi-agent оркестрации, 2. R-HAN: Reliable Hierarchical Coordination for Multi-Agent Systems, 3. Hermes Agent v0.16.0 (Surface Rel... |
| `#1578–1668` (4) | 5 | 0.33 | 1. Microsoft Agent Framework 1.8.0 — McpSkills, 2. POISE — автономное открытие новых LLM-RL алгоритмов агентами-учёными, 3. dySCo / Pi-Taskflow / Open-Multi-Agent — typed DAG и sparse-координация д... |
| `#1579–1669` (4) | 5 | 0.33 | 1. Arbor — Microsoft Research: мультиагентный фреймворк с Hypothesis-Tree Refinement, 2. MARS — Multi-Agent Review System: дебаты с -50% токенов, 3. DeLM — Decentralized Language Models: параллельн... |
| `#1580–1670` (4) | 5 | 0.33 | 1. ECC 2.0.0 — The Agent Harness Operating System, 2. MARS — Multi-Agent Review System (эффективный multi-agent debate), 3. MASFactory — multi-agent workflow из natural language, Дополнительные нах... |
| `#1581–1672` (4) | 4 | 0.33 | Query must not be empty or whitespace-only., SentinelV5Request, Symbol must be uppercase and non-empty., Validated input for the Sentinel V5 orchestrator.      If Pydantic validation fa |
| `#1582–1677` (4) | 5 | 0.33 | Smoke test for Data Room API blueprint., test_blueprint_exists(), test_conflicts_endpoint_returns_json(), При запросе /data-room/conflicts должен возвращаться JSON., Проверяем, что Blueprint зареги... |
| `#1584–1680` (5) | 5 | 0.33 | Color-coded alpha decay / out-of-sample health badge., Div, _alpha_badge(), explorer_tab(), web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)  Enha |
| `#1585–1681` (4) | 4 | 0.33 | A/B compare two sessions: ?sid_a=X&sid_b=Y     Supports both new-style sessions, ab_compare(), live_enable(), Включает live-режим. Требует подтверждение и API-ключ. |
| `#1586` | 4 | 0.33 | Common commands, Conventions, Friction notes, Quick map |
| `#1587` | 5 | 0.33 | cleanup(), test_agent_can_create_add_function(), Бенчмарк для Ralph Loop – минимальная задача, Проверяем, Удаляем временные файлы до и после теста., которую агент должен решить., что после Ralph Lo... |
| `#1589` | 5 | 0.33 | Phase 1 cleanup validation tests., test_core_auth_importable(), test_no_dead_imports(), Проверяем, Проверяем, что core.auth импортируется без ошибок., что старые модули больше не импортируются. |
| `#1593–1631` (2) | 3 | 0.33 | Feature, FeatureFunc, Typed feature with name, description, unit. |
| `#1594–1632` (2) | 5 | 0.47 | Build all window aggregates for all metrics.     Returns: {metric_name: {window_, For a given metric + window, TimeWindow, build_windows(), get_window_data(), return aggregates.     In production: ... |
| `#1595–1637` (2) | 5 | 0.47 | Aggregate counts per Zettelkasten tag across all results., Import and run a scenario by name., compute_tag_stats(), main(), run_scenario() |
| `#1596–1638` (2) | 3 | 0.53 | FalsePositiveScenario, OSDState, run() |
| `#1597–1639` (2) | 3 | 0.47 | Decision, GovernanceFailureScenario, run() |
| `#1598–1640` (2) | 3 | 0.53 | ExecutedAction, IdempotencyScenario, run() |
| `#1599–1626` (2) | 5 | 0.40 | DataFrame, Ensure label distribution is not too imbalanced.     If positive class < min_pos, Split dataset respecting temporal order (no future-leaking).     Each node's tim, stratify_by_label(), t... |
| `#1600` | 3 | 0.40 | Full training pipeline: build → split → train → evaluate → register.          Re, Path, Trainer |
| `#1601` | 5 | 0.33 | Bug Fixes, New CLI Commands, Phase 1-4 All Complete ✅, What's New, v0.4.0 — Phase 4 Complete: ALL PHASES DONE |
| `#1602` | 5 | 0.60 | EntryInfo, GateInfo, Path, run(), safe_rel() |
| `#1616–1671` (3) | 3 | 0.40 | Regime, RegimeDetector, meta_rl/quant/regime.py -- ATOM-META-RL-024: Market regime detection |
| `#1622` | 3 | 0.40 | Benchmark diversity_filter at n=1000 candidates x n=1000 pool., ScoredStrategy_shim, build() |
| `#1625` | 3 | 0.33 | Compute fingerprint from node list.          If prev_fp is provided and a node h, Kahn's algorithm + layer assignment.         Returns node_id → layer (position i, Root hash = SHA256 of all node ha... |
| `#1627` | 5 | 0.33 | 2-Node Ceph Cluster, Ceph Storage, CephFS, Pool Configuration, RBD Usage |
| `#1628` | 5 | 0.33 | DNS Records, Firewall Rules, Network Design, VLAN Architecture, WireGuard Mesh Overlay |
| `#1629` | 5 | 0.33 | Cluster Layout, Connect to Ray, Ray AI Runtime, Ray Dashboard, Slurm + Ray Bridge |
| `#1630` | 5 | 0.33 | Architecture, GPU Partition, HA Controller Setup (3 controllers), Slurm HA Setup, Useful Commands |
| `#1641` | 5 | 0.40 | Add rolling mean/std features for configurable windows., Adds sliding-window features, DataFrame, add_rolling_features(), and temporal features.      Args:, build_advanced_features(), lag features |
| `#1642` | 5 | 0.33 | API validation — returns JSON response., CLI entry point validator.      Returns task string if valid, Input Contract Middleware — strict validation for CLI., api_validate(), cli_validate(), exits ... |
| `#1643` | 4 | 0.33 | TestModelQuality, Trained failure model must achieve AUC >= 0.60 on hold-out set., Trained load model must achieve RMSE <= 10.0 on hold-out set., Validate that trained models meet minimum quality t... |
| `#1657` | 4 | 0.33 | AtomNodeServicer, Minimal node-to-node message contract, Streaming — for high-throughput feeds, Unary send — fire-and-wait ack |
| `#1660` | 4 | 0.40 | Add experience to replay buffer., Experience, core/online_trainer.py — ATOM-STEP-6: Online RL Trainer ========================, datetime |
| `#1679` | 4 | 0.33 | Filters ROMA JSON for dangerous patterns.     Returns {passed: bool, Run all security checks. Return pass/fail., Security Gate — validates ROMA JSON before compilation., SecurityGate, reason: str |
| `#1682–1797` (4) | 4 | 0.40 | Запреты, Обязанности, Формат ответа, 🤖 AstroCouncil Agent |
| `#1683–1798` (4) | 4 | 0.40 | Запреты, Обязанности, Формат ответа, 🤖 ElectoralAgent (Electional Astrologer) |
| `#1684–1799` (4) | 3 | 0.40 | Any, CounterfactualEngine, amre/counterfactual.py — Counterfactual reasoning |
| `#1685–1800` (4) | 4 | 0.40 | Any, Domain grounding validation с мягким multiplicative degrade.      Parameters, amre/grounding.py — ATOM-KARL-015 Phase 5: Soft Degrade Grounding  Заменяет жёст, validate_with_grounding() |
| `#1686–1801` (4) | 4 | 0.40 | Запреты, Обязанности, Формат ответа, 🤖 SynthesisAgent (Deliberium) |
| `#1692–1802` (4) | 3 | 0.60 | main(), print_table(), run_query() |
| `#1693–1803` (4) | 4 | 0.40 | AstroFin Sentinel v5 — Project Root Utility Provides the absolute path to the pr, Path, Returns the absolute path to the AstroFinSentinelV5 project root.      Resolves, get_project_root() |
| `#1696–1805` (4) | 4 | 0.40 | AstroFin Sentinel V5 — Обзор проекта, Вдохновение, Доменная структура (DDD), Ключевые возможности |
| `#1697–1806` (4) | 4 | 0.40 | AstroFin Sentinel V5 – Бэклог для Ralph Loop, P0 (Критические), P1 (Важные), P2 (Желательные) |
| `#1698–1807` (4) | 4 | 0.40 | ATOM-FIX-ROUTER: Исправление бага с timeframe, Execution, Impact, Problem |
| `#1699–1808` (4) | 4 | 0.40 | ATOM-MODEL-SPEC: Единая спецификация модели, Components, Dependencies, Why P1? |
| `#1700–1809` (4) | 4 | 0.40 | Bollinger, Bollinger Bands, MACD, MACD (Moving Average Convergence Divergence), RSI (Relative Strength Index), Technical Indicators — RSI |
| `#1701–1810` (4) | 4 | 0.40 | Kelly Criterion, Position Sizing Rules, Risk-Based Sizing, Session Limits |
| `#1702–1811` (4) | 4 | 0.40 | Core Rules, Drawdown Rules, Dynamic Risk Scaling, Risk Management Framework |
| `#1703–1812` (4) | 4 | 0.40 | Multi-Agent AI Daily Digest — 2026-04-27, Дополнительно (также релевантно), Источники, Топ-3 за неделю |
| `#1704–1813` (4) | 4 | 0.40 | Hugging Face, Multi-Agent AI Daily Digest — 2026-05-03, Reddit, Twitter/X, arXiv, Источники: GitHub, Период: последние 7 дней (26 апреля — 3 мая 2026), Топ-3 значимых события |
| `#1705–1814` (4) | 4 | 0.40 | 1. Arbor — структурированный tree search как cognition layer для автономных агентов, 2. DeLM — децентрализованный multi-agent фреймворк с общим контекстом, 3. Citadel — open-source orchestration la... |
| `#1706–1815` (4) | 4 | 0.40 | 1. OrchRM — self-supervised reward modeling для оркестратора multi-agent LLM-систем, 2. ECC 2.0 — Agent Harness Operating System с cross-harness оркестрацией, 3. Swarms v13 "Kizuna 絆" — async Group... |
| `#1707–1816` (4) | 3 | 0.40 | AutonomousDecision, DecisionLogger, meta_rl/autonomous/decision.py -- ATOM-META-RL-024: Decision audit trail |
| `#1708–1831` (4) | 4 | 0.60 | generate_signals(), generate_synthetic_data(), main(), scripts/run_backtest.py — ATOM-STEP-8: Backtest Runner |
| `#1709–1832` (4) | 4 | 0.40 | cleanup(), test_agent_can_create_add_function(), Проверяем, Удаляем временные файлы до и после теста., что после Ralph Loop агент создал нужный файл. |
| `#1713–1836` (5) | 4 | 0.40 | test_metrics_serve_command_exists(), test_with_metrics_flag_registers_metrics(), При флаге --with-metrics счётчики метрик должны увеличиваться.     (Проверяем че, Проверяем, что команда 'karl metri... |
| `#1714–1837` (5) | 4 | 0.40 | test_rag_query_cache_hits_increment(), test_rag_retrieve_updates_quality_metrics(), Повторный запрос с теми же параметрами должен вернуть кешированный результат., После retrieve должны обновиться м... |
| `#1715–1838` (5) | 4 | 0.40 | test_health_endpoint_not_limited(), test_rate_limit_too_many_requests(), Проверяем, Публичные эндпоинты не должны лимитироваться., что после 10 запросов с правильным ключом возвращается 429. |
| `#1717–1840` (4) | 4 | 0.60 | Append a snapshot row to the backtest DB for trend tracking., get_counts(), main(), save_snapshot() |
| `#1718–1841` (4) | 4 | 0.60 | Check strategy pool for new top strategies and export them., check_and_export(), run_daemon(), run_once() |
| `#1719` | 4 | 0.40 | Start Flask app in background with proper cleanup., Test Redis connection., flask_app(), redis_client() |
| `#1726–1780` (2) | 4 | 0.60 | Select optimal node for a job.     Returns: {node, _build_reason(), _node_to_partition(), partition}, reason, score, select_node() |
| `#1727–1781` (2) | 4 | 0.50 | Compute suitability score for a node.     Higher = better. Range approximately 0, Return dict of node -> score, rank_nodes(), score_node(), sorted descending. |
| `#1729` | 3 | 0.40 | CandidateGenerator, Layer 1: Generate k-best candidate placements per job.     Uses ML risk scores f, Returns list of (node_id, score) for top-k candidates.         Score = base_scor |
| `#1730` | 5 | 0.40 | 7. EXECUTION BOUNDARY COLLAPSE, 7.1 Current State, 7.2 Collapsed Architecture, 7.3 ExecutionToken — Immutable Capability, 7.4 Before/After Enforcement Comparison |
| `#1731` | 5 | 0.40 | 9. DETERMINISM FIX IMPLEMENTATION ORDER, Phase 1: Core Deterministic Primitives (P0), Phase 2: Ledger Linearization (P0), Phase 3: Execution Boundary Collapse (P1), Phase 4: Async Determinism (P1) |
| `#1732` | 4 | 0.70 | build_push.sh script, fail(), info(), warn() |
| `#1733` | 4 | 0.40 | Any, Run a predefined test scenario., run_scenario(), sbs/cli_run.py — run subcommand implementation. |
| `#1734` | 4 | 0.70 | fail(), info(), validate_local.sh script, warn() |
| `#1735` | 5 | 0.40 | 2 SQLite DBs (post-consolidation 2026-03-26), 3. Databases, Issues, Schema: `backtest_runs` (authoritative), Schema: `sessions` |
| `#1736` | 5 | 0.40 | 8. Belief Tracker (Bayesian), API, File: `core/belief.py` + `core/belief.db`, Model, Success Criteria |
| `#1776` | 3 | 0.40 | PreparedCertificate, Proof that ≥ 2f+1 nodes have prepared the request., Return PreparedCertificate if quorum reached, else None. |
| `#1777` | 3 | 0.40 | CommitCertificate, Finalize the commit. Returns CommitCertificate for the distributed ledger., Proof that the request is irreversibly committed. |
| `#1778` | 4 | 0.40 | Self-Hosted Runner Setup (без токенов / GitHub App), Быстрый старт (SSH-only), Деплой через SSH (без GitHub App), Обновление раннера |
| `#1783` | 4 | 0.40 | FORCE_BOOTSTRAP, PYTHONHASHSEED, PYTHONPATH, bootstrap_env.sh script |
| `#1784` | 4 | 0.80 | -throughput(), check(), log(), run_scenario1.sh script |
| `#1785` | 3 | 0.60 | err(), init-kong.sh script, log() |
| `#1796` | 3 | 0.40 | EvaluationResult, reward < reward_clip_min is clipped up to the floor.          Symmetric counterp, reward > reward_clip_max is clipped down to the ceiling.          The default pe |
| `#1828` | 4 | 0.40 | Ralph Loop Instructions for AstroFin Sentinel V5, Запрещено, Общие правила, Обязательные проверки |
| `#1842–1843` (2) | 3 | 0.50 | Any, Convert Event.payload to dict. Handles tuple (frozen dataclass) and dict., payload_to_dict() |
| `#1846–1978` (4) | 3 | 0.50 | Adjust position size based on position_lag metric.      Parameters     ---------, amre/risk_control.py — ATOM-KARL-015 Phase 5: Risk Controller via position_lag, apply_position_lag_risk() |
| `#1847–1979` (4) | 3 | 0.50 | Any, amre/uncertainty.py — Uncertainty quantification, estimate_uncertainty() |
| `#1852–1980` (4) | 3 | 0.50 | Claude instructions for AstroFinSentinelV5, Hermes Agent (via Ollama) can also follow these instructions., See AGENTS.md for the complete project context and AI rules. |
| `#1853–1981` (2) | 3 | 0.50 | 8. Ограничения: не менять signal., Signal не меняется после apply_pressure_field., TestConstraints |
| `#1854–1983` (3) | 3 | 0.50 | CouncilResult, core/council/runner.py — AstroCouncil Runner, run_council() |
| `#1855–1984` (4) | 3 | 0.50 | track_agent_duration(), Декоратор, Метрики производительности агентов., замеряющий время выполнения агента. |
| `#1856–1985` (4) | 3 | 0.50 | Rate limiting configuration with optional Redis backend., Return True if rate limiter is using Redis., is_redis_backed() |
| `#1857–1986` (4) | 3 | 0.50 | Compute astro-based reward component.      Parameters     ----------     muhurta, compute_astro_reward(), core/reward/astro_reward.py — ATOM-REWARD-001: Astro-Based Reward  Astro-based r |
| `#1858–1987` (4) | 3 | 0.50 | Tracer, setup_tracing(), Инициализация OpenTelemetry с экспортом в Jaeger (OTLP gRPC). Добавлено автомати |
| `#1860–1989` (4) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-25, Источники, Топ-3 за сегодня |
| `#1861–1990` (4) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-04-26, Источники, Топ-3 за последние 7 дней |
| `#1862–1991` (4) | 3 | 0.50 | Multi-Agent AI Daily Digest, Источники мониторинга, Топ-3 за сегодня |
| `#1863–1992` (4) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-01, Источники мониторинга, Топ-3 за сегодня |
| `#1864–1993` (4) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-08, Источники, Топ-3 за сегодня |
| `#1865–1994` (4) | 3 | 0.50 | Multi-Agent AI Daily Digest — 2026-05-15, Источники, Топ-3 за сегодня |
| `#1866–1995` (4) | 3 | 0.50 | Multi-Agent AI Daily — 2026-05-29, Источники, Топ-3 за сегодня |
| `#1867–1996` (4) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-05, Топ-3 за неделю |
| `#1868–1997` (4) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-06, Топ-3 за неделю |
| `#1869–1998` (4) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-07, Топ-3 за неделю |
| `#1870–1999` (4) | 3 | 0.50 | Honorable mentions (не вошли в топ-3), Multi-Agent AI Daily — 2026-06-11, Топ-3 за неделю |
| `#1871–2000` (4) | 3 | 1.00 | main(), p(), sec() |
| `#1872–2001` (4) | 3 | 0.50 | StrategyTask, WorkerResult, meta_rl/distributed/types.py -- ATOM-META-RL-024: Worker task types |
| `#1873–2002` (4) | 3 | 0.50 | Generate all evolution visualization charts.      Returns dict of chart_name → o, generate_all_charts(), meta_rl/visualization.py — ATOM-META-RL-011: Evolution Charts |
| `#1874–2020` (4) | 3 | 0.67 | Naively extract metric names from a PromQL expression., extract_metric_names(), main() |
| `#1875–2021` (4) | 3 | 0.83 | agent_test_path(), has_function(), main() |
| `#1876–2022` (4) | 3 | 0.67 | Return files changed in the working tree under `scope`., _changed_files(), main() |
| `#1881–2027` (4) | 3 | 0.50 | Phase 1 cleanup validation tests., test_core_auth_importable(), Проверяем, что core.auth импортируется без ошибок. |
| `#1886–2032` (5) | 3 | 0.50 | Div, evolution_tab(), web/components/evolution.py — Evolution tab (ATOM-META-RL-004)  Enhanced with re |
| `#1887–2033` (5) | 3 | 0.50 | Div, sessions_tab(), web/components/sessions.py — Sessions tab (ATOM-META-RL-004) |
| `#1888–2034` (4) | 3 | 0.50 | Return conflict journal contents as JSON., list_conflicts(), web/data_room.py  Data Room API endpoints. |
| `#1889–2035` (5) | 3 | 0.50 | Register all Sessions tab callbacks., register_sessions_callbacks(), web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004) |
| `#1900–1958` (2) | 3 | 0.67 | Reconstruct features from TimescaleDB continuous aggregates.     Queries metrics, backfill_range(), datetime |
| `#1901–1956` (2) | 3 | 1.00 | create_vlan(), day1-network.sh script, ros_api() |
| `#1902` | 4 | 0.50 | 10. SAFETY PROOF (INFORMAL), 10.1 Why Replay Becomes Exact, 10.2 Why Race Conditions Are Eliminated, 10.3 Why Ledger Is Linearizable |
| `#1903` | 4 | 0.50 | 1. EXECUTIVE SUMMARY, Current State (v9.0+ATOM-META-RL-018), Goal, Target State (ATOM-META-RL-019) |
| `#1904` | 4 | 0.50 | 3. EXECUTION MODEL — BEFORE / AFTER, 3.1 Current Execution Graph (v9.0), 3.2 New Linearized Execution Graph (ATOM-META-RL-019), 3.3 Key Differences |
| `#1905` | 4 | 0.50 | 4. MUTATION FLOW REDESIGN, 4.1 Before (Layered), 4.2 After (Linearized), 4.3 Global Execution Sequencer |
| `#1906` | 4 | 0.50 | 6. LEDGER LINEARIZATION — HARD FIX, 6.1 Problem, 6.2 Solution: AtomicLedgerWriter, 6.3 Integration |
| `#1912` | 3 | 0.50 | 7.2 Консенсус: BUY + BUY усиливают друг друга., TestConsensus, eff=60) ← B(BUY, eff=75): score = +0., Консенсус: оба усиливаются.         A(BUY |
| `#1949` | 3 | 0.50 | Notes, Role: ceph, Variables |
| `#1951–1982` (2) | 3 | 0.50 | 7.3 Outlier: SELL не игнорируется., BUY теряет confidence.          A(BUY, SELL не игнорируется, TestOutlier, ef, eff=70) ← B(BUY |
| `#1959` | 3 | 1.00 | create_vlan(), day1_network.sh script, ros_api() |
| `#1960` | 3 | 0.83 | kubeseal-encrypt.sh script, log(), ok() |
| `#1977` | 3 | 0.50 | AtomNodeStub, Constructor.          Args:             channel: A grpc.Channel., Minimal node-to-node message contract |
| `#2019` | 3 | 0.50 | Architecture, Role: ray, Test |
| `#2036` | 3 | 0.50 | Role: wireguard, Usage, Variables |
| `#2048–2258` (96) | 3 | 0.67 | 2026-05-26, Commits, Environment Health |
| `#2072–2260` (8) | 3 | 0.67 | 2026-05-30, Commits, Environment Health |
| `#2074–2261` (4) | 3 | 0.67 | 2026-05-31, Commits, Environment Health |
| `#2075–2263` (8) | 3 | 0.67 | 2026-06-03, Commits, Environment Health |
| `#2102` | 3 | 0.67 | HealthResponse, Liveness probe — returns 'alive' when model is loaded., health() |
| `#2103` | 3 | 0.67 | 11. FILES TO CREATE / MODIFY, Files to Modify, New Files |
| `#2144–2223` (4) | 3 | 0.67 | 2026-06-17, Commits, Environment Health |
| `#2163` | 3 | 0.67 | ExplainResponse, Return SHAP values for a previously made prediction., explain_prediction() |
| `#2176` | 3 | 0.67 | Custom application metrics in JSON (Prometheus-style fields)., MetricsResponse, metrics() |

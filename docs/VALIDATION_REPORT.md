# VALIDATION_REPORT.md

Stratified validation of N=538 INFERRED edges from `graphify-out/graph.json` (snapshot 2026-06-17).

**Verdict legend:**
- `valid` — link is real and current
- `false` — link does not exist in code

**Verdict summary (N=538):** `false`=224 (42%), `valid`=185 (34%), `ambiguous`=117 (22%), `outdated`=12 (2%)

- `moved` — entity exists, but in a different file (new path noted)
- `outdated` — was true at some point, now dead (e.g. `_archived/`, removed submodules)
- `ambiguous` — needs human review

---

## Bucket: relation = `imports` (50 edges)

### INFERRED #imports-1
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL37 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/federation/quorum_certificate.py:L20 :: federation_quorum_certificate_quorumcertificate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:51:    We verify the gateway code CONSISTENCY with the DFA spec:
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:87:    # P6 federated gateway — has its own DFA but delegates through ExecutionGateway
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:103:    # apply_mutation in mutation_executor is PERMITTED (internal gateway wrapper)
    ```

### INFERRED #imports-2
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/async_engine.py:LL244 :: agent_runtime_async_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:L127 :: agent_runtime_task_store_taskstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/models/job.py:2:from db.engine import Base
    ```
    ```
    /home/workspace/roma-execution-bridge/cost/predictor.py:2:"""ROMA Cost Predictor — Pre-execution cost estimation engine."""
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/arch.py:28:print("Week 5-6:  Connect existing execution engine to SaaS auth")
    ```

### INFERRED #imports-3
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L84 :: alignment_drift_detector_executiontrace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:67:        # Build K8s Job (single-pod with init containers for DAG)
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:79:            # Multi-step DAG — use init containers + main
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:82:                ic["name"] = f"init-{step['name']}"
    ```

### INFERRED #imports-4
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L449 :: alignment_drift_detector_driftengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:67:        # Build K8s Job (single-pod with init containers for DAG)
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:79:            # Multi-step DAG — use init containers + main
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:82:                ic["name"] = f"init-{step['name']}"
    ```

### INFERRED #imports-5
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL15 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/load_simulator.py:L200 :: testing_load_simulator_loadsimulator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:338:    """Runs a suite of federation scenarios and produces a report."""
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_rcf.py:1:"""Test suite for RCF — Reality Consensus Fusion layer v11.1."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```

### INFERRED #imports-6
- **Source:** `astrofin-sentinel-v5/db/models.py:LL7 :: astrofin_sentinel_v5_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-7
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL30 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/equivalence.py:L94 :: alignment_equivalence_equivalencechecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/test_ci.py:23:    from rbac.engine import RBACEngine, Role
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli_status.py:19:                "engine": "SBSRuntimeEnforcer",
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli_status.py:28:        "engine": "GlobalInvariantEngine",
    ```

### INFERRED #imports-8
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L33 :: alignment_drift_detector_drifttype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/coherence/objective_stabilizer.py:111:        (enforced on init).
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-9
- **Source:** `atom-federation-os/federation/byzantine/pbft_consensus.py:LL17 :: byzantine_pbft_consensus`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L23 :: byzantine_message_signatures_federationmessagesigning`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:115:    """Phase 2: proof-weighted consensus ranking."""
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:296:    """Full v9.3 pipeline: gossip → policy_sync → consensus."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:5:  Phase 2: consensus weighted by proof_valid + stability + drift
    ```

### INFERRED #imports-10
- **Source:** `atom-federation-os/alignment/__init__.py:LL27 :: alignment_init`
- **Target:** `atom-federation-os/alignment/plan_reality_comparator.py:L75 :: alignment_plan_reality_comparator_planrealitybinding`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-11
- **Source:** `audit_repo/db/models.py:LL7 :: audit_repo_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-12
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L151 :: alignment_drift_detector_layer1result`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:67:        # Build K8s Job (single-pod with init containers for DAG)
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:79:            # Multi-step DAG — use init containers + main
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:82:                ic["name"] = f"init-{step['name']}"
    ```

### INFERRED #imports-13
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL15 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/load_simulator.py:L28 :: testing_load_simulator_burstpattern`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:338:    """Runs a suite of federation scenarios and produces a report."""
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_rcf.py:1:"""Test suite for RCF — Reality Consensus Fusion layer v11.1."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```

### INFERRED #imports-14
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL14 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/invariant_checker.py:L113 :: v8_2a_safety_foundations_invariant_checker_invariantchecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:78:    def init(self) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_orchestration_v75.py:156:        # re-init clears
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```

### INFERRED #imports-15
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:LL13 :: v8_2b_controlled_autocorrection_mutation_executor`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L19 :: v8_2b_controlled_autocorrection_severity_mapper_mutationclass`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:90:    logger.info("executor.running_topology")
    ```
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:91:    executor = TopologyExecutor(topology, state)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:92:    results = await executor.run()
    ```

### INFERRED #imports-16
- **Source:** `atom-federation-os/rpc/mesh.py:LL14 :: rpc_mesh`
- **Target:** `atom-federation-os/rpc/client.py:L19 :: rpc_client_rpcclient`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:28:from .mesh import NodeMesh
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:58:    def attach_mesh(self, mesh: NodeMesh) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:59:        self._mesh = mesh
    ```

### INFERRED #imports-17
- **Source:** `data_room/__init__.py:LL2 :: data_room_init`
- **Target:** `data_room/observability.py:L12 :: data_room_observability_metricsstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-18
- **Source:** `astrofin-sentinel-v5/tests/test_validator.py:LL10 :: astrofin_sentinel_v5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/models.py:9:from pydantic import BaseModel, Field, validator
    ```
    ```
    /home/workspace/orchestration/models.py:42:    @validator("user_query")
    ```
    ```
    /home/workspace/orchestration/models.py:49:    @validator("symbol")
    ```

### INFERRED #imports-19
- **Source:** `tests/data_room/test_data_room.py:LL18 :: tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L79 :: data_room_circuit_breaker_call_with_breaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:326:            '# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:352:# ── circuit breaker registry (singleton) ───────────────────────────────────────
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:375:    """Manually reset a circuit breaker to CLOSED state."""
    ```

### INFERRED #imports-20
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL18 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L19 :: v8_2b_controlled_autocorrection_severity_mapper_mutationclass`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-21
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L178 :: alignment_drift_detector_layer3result`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-22
- **Source:** `atom-federation-os/cluster/node/node.py:LL15 :: node_node`
- **Target:** `atom-federation-os/proto/atom_os_pb2_grpc.py:L1 :: proto_atom_os_pb2_grpc`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/client.py:13:import grpc
    ```
    ```
    /home/workspace/atom-federation-os/rpc/client.py:14:from grpc import Channel
    ```
    ```
    /home/workspace/atom-federation-os/rpc/client.py:45:                self._channel = grpc.insecure_channel(
    ```

### INFERRED #imports-23
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL13 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:L50 :: v8_2b_controlled_autocorrection_policy_selector_mutationpolicy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-24
- **Source:** `push/tests/data_room/test_data_room.py:LL115 :: push_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L12 :: data_room_blueprint_pricetick`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/web/data_room.py:18:@data_room_bp.route("/data-room/conflicts", methods=["GET"])
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```

### INFERRED #imports-25
- **Source:** `audit_repo/meta_rl/basket.py:LL15 :: audit_repo_meta_rl_basket_py_meta_rl_basket`
- **Target:** `meta_rl/types.py:L149 :: meta_rl_types_symbolmetrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_integration.py:29:    "FAANG",  # FAANG basket (split into individual tickers)
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_integration.py:64:                reason="FAANG basket deprecated — using QQQ as proxy",
    ```
    ```
    /home/workspace/push/meta_rl/strategy_evaluator.py:58:                from meta_rl.basket import BasketEvaluator
    ```

### INFERRED #imports-26
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL18 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L9 :: v8_2b_controlled_autocorrection_severity_mapper_severitylevel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-27
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL115 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L12 :: data_room_blueprint_pricetick`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/web/data_room.py:18:@data_room_bp.route("/data-room/conflicts", methods=["GET"])
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```

### INFERRED #imports-28
- **Source:** `atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:LL36 :: trust_weighted_trust_dynamics_stabilizer`
- **Target:** `atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:L59 :: trust_weighted_trust_feedback_dampener_trustupdateresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:358:    stabilizer = TrustDynamicsStabilizer(
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:368:    report = stabilizer.stabilize(
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:414:    report3 = stabilizer.stabilize(
    ```

### INFERRED #imports-29
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL22 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:L19 :: agent_runtime_event_sourcing_eventtype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/models/job.py:2:from db.engine import Base
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:2:pbft_consensus.py — PBFT-lite consensus engine for v9.8
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:310:    engine = PBFTLiteConsensusEngine(node_id="node_0", n_nodes=4, signer=signer, max_rounds=3)
    ```

### INFERRED #imports-30
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL13 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:L20 :: v8_2b_controlled_autocorrection_policy_selector_policycontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-31
- **Source:** `atom-federation-os/cluster/shared/rpc_server.py:LL22 :: shared_rpc_server`
- **Target:** `atom-federation-os/proto/atom_os_pb2.py:L1 :: proto_atom_os_pb2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:14:import proto.atom_os_pb2 as pb2
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:167:            resp = stub.Ping(pb2.PingRequest(), timeout=3.0)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:228:            resp = stub.Forward(pb2.ForwardRequest(
    ```

### INFERRED #imports-32
- **Source:** `atom-federation-os/alignment/__init__.py:LL33 :: alignment_init`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L29 :: alignment_rollback_engine_v2_rollbacktype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-33
- **Source:** `astrofin-sentinel-v5/meta_rl/git_agent_exporter.py:LL26 :: astrofin_sentinel_v5_meta_rl_git_agent_exporter_py_meta_rl_git_agent_exporter`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/tracing.py:5:from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    ```
    ```
    /home/workspace/orchestration/tracing.py:15:    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    ```
    ```
    /home/workspace/orchestration/tracing.py:16:    provider.add_span_processor(SimpleSpanProcessor(exporter))
    ```

### INFERRED #imports-34
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL28 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L12 :: byzantine_message_signatures_signedmessage`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```

### INFERRED #imports-35
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL14 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/invariant_checker.py:L59 :: v8_2a_safety_foundations_invariant_checker_spectralinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #imports-36
- **Source:** `atom-federation-os/federation/byzantine/pbft_consensus.py:LL18 :: byzantine_pbft_consensus`
- **Target:** `atom-federation-os/federation/byzantine/quorum.py:L34 :: byzantine_quorum_quorumcalculator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/raft_consensus.py:2:"""ROMA Raft Consensus Layer — True distributed consensus implementation."""
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/raft_consensus.py:29:    """True Raft consensus node — leader election + log replication + membership."""
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/raft_consensus.py:142:        """Add new node to cluster. Requires consensus."""
    ```

### INFERRED #imports-37
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL23 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/stability_governor.py:L33 :: v8_2a_safety_foundations_stability_governor_governorsignal`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```

### INFERRED #imports-38
- **Source:** `atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:LL36 :: trust_weighted_trust_dynamics_stabilizer`
- **Target:** `atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:L46 :: trust_weighted_trust_feedback_dampener_dampenerconfig`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:358:    stabilizer = TrustDynamicsStabilizer(
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:368:    report = stabilizer.stabilize(
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:414:    report3 = stabilizer.stabilize(
    ```

### INFERRED #imports-39
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL18 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L100 :: data_room_circuit_breaker_circuitbreakeropen`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/web/data_room.py:18:@data_room_bp.route("/data-room/conflicts", methods=["GET"])
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```

### INFERRED #imports-40
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL15 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/load_simulator.py:L374 :: testing_load_simulator_make_cascade_failure_scenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_enforcement_layer.py:167:        # In real scenario, this would be called from the function itself
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:9:Integration scenario:
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:105:    """N-node federation cluster with scenario-based fault injection."""
    ```

### INFERRED #imports-41
- **Source:** `tests/data_room/test_data_room.py:LL115 :: tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L36 :: data_room_blueprint_blueprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/architecture_linter.py:179:            "use data_room.blueprint.get_price(...)",
    ```
    ```
    /home/workspace/agents/_impl/_template_agent.py:21:    5. Consume all data through data_room.blueprint (R3, R4).
    ```
    ```
    /home/workspace/agents/_impl/_template_agent.py:123:        #     tick = data_room.blueprint.get_price(symbol, asof=state.get("asof"))
    ```

### INFERRED #imports-42
- **Source:** `atom-federation-os/core/federation/quorum_certificate.py:LL16 :: federation_quorum_certificate`
- **Target:** `atom-federation-os/core/federation/consensus.py:L18 :: federation_consensus_votevalue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:189:        - certificate = hash(sorted([all_prepare_digests])) → ensures all voters committed to same digest
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:205:            # Prepare certificate: hash of sorted prepare digests for commit binding
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/core/federation/distributed_ledger.py:29:    qc: QuorumCertificate    # quorum certificate for this entry
    ```

### INFERRED #imports-43
- **Source:** `astrofin-sentinel-v5/tests/test_validator.py:LL10 :: astrofin_sentinel_v5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/models.py:9:from pydantic import BaseModel, Field, validator
    ```
    ```
    /home/workspace/orchestration/models.py:42:    @validator("user_query")
    ```
    ```
    /home/workspace/orchestration/models.py:49:    @validator("symbol")
    ```

### INFERRED #imports-44
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL3 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:L161 :: v8_2b_controlled_autocorrection_feedback_injection_feedbackinjectionloop`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/v6/solver/optimizer_api.py:51:# Helpers (lazy init to avoid import errors)
    ```
    ```
    /home/workspace/AsurDev/tests/integration/test_ml_pipeline.py:214:        # Import the app factory (lazy init — model loads on startup)
    ```
    ```
    /home/workspace/AsurDev/scheduler_v3/api.py:37:# Globals (lazy init)
    ```

### INFERRED #imports-45
- **Source:** `atom-federation-os/orchestration/ExecutionGateway/__init__.py:LL10 :: executiongateway_init`
- **Target:** `atom-federation-os/orchestration/ExecutionGateway/execution_gateway.py:L157 :: executiongateway_execution_gateway_executiongateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/static_mutation_analyzer.py:25:    'orchestration.executiongateway',
    ```
    ```
    /home/workspace/atom-federation-os/scripts/static_mutation_analyzer.py:96:            for allowed in ('orchestration/execution_gateway', 'orchestration/executiongateway',
    ```
    ```
    /home/workspace/atom-federation-os/scripts/visualize_execution_graph.py:60:            'execution_gateway', 'executiongateway',
    ```

### INFERRED #imports-46
- **Source:** `atom-federation-os/core/federation/distributed_ledger.py:LL18 :: federation_distributed_ledger`
- **Target:** `atom-federation-os/core/federation/quorum_certificate.py:L20 :: federation_quorum_certificate_quorumcertificate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/test_ci.py:48:    from billing.ledger import BillingLedger
    ```
    ```
    /home/workspace/roma-execution-bridge/test_ci.py:52:    assert bal >= 0, "ledger failed"
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/auth.py:7:from billing.ledger import BillingLedger
    ```

### INFERRED #imports-47
- **Source:** `data_room/resolvers/__init__.py:LL13 :: resolvers_init`
- **Target:** `data_room/resolvers/base.py:L23 :: resolvers_base_resolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_consensus.py:126:    Consensus resolver with proof-aware candidate ranking.
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_consensus.py:132:        resolver = ProofAwareConsensusResolver(node_id="node_1")
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_consensus.py:137:        winner = resolver.rank_candidates(candidates)
    ```

### INFERRED #imports-48
- **Source:** `astrofin-sentinel-v5/tests/test_validator.py:LL10 :: astrofin_sentinel_v5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L11 :: validators_agent_validator_severity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:102:            log("WARN", "L2-DFA", f"  {h['severity']}: {h['file']}:{h['line']} {h['method']}()")
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:234:    other = [h for h in hidden if h.get("severity") != "PERMITTED"]
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:149:                            "in_gateway": is_gw, "severity": "PERMITTED",
    ```

### INFERRED #imports-49
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL24 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/observability.py:L12 :: data_room_observability_metricsstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/web/data_room.py:18:@data_room_bp.route("/data-room/conflicts", methods=["GET"])
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```

### INFERRED #imports-50
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL29 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/pbft_consensus.py:L21 :: byzantine_pbft_consensus_pbftphase`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

---

## Bucket: relation = `method` (50 edges)

### INFERRED #method-1
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL155 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testheliocentriclongitude`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L155 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testheliocentriclongitude_test_longitude_in_range`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-2
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL400 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testscoredstrategy`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L400 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testscoredstrategy_test_to_from_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-3
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL173 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testnormalizesignal`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L173 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testnormalizesignal_test_none_signal_defaults`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #method-4
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL61 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L61 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/__main__.py:24:    query = " ".join(clean_args) if clean_args else "Analyze BTC"
    ```
    ```
    /home/workspace/orchestration/__main__.py:36:                    user_query=query,
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:492:    parser.add_argument("--query", default="", help="User query")
    ```

### INFERRED #method-5
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL118 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L118 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml_test_valid_karllike_agent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #method-6
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL140 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L140 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_all_agents`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-7
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL105 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L105 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator_test_evaluate_returns_result`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-8
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL18 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testrouter`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L18 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testrouter_test_route_single_symbol`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-9
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL210 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L210 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration_test_all_signals_in_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-10
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL307 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testinvalidagentyaml`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L307 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testinvalidagentyaml_test_temperature_out_of_range`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #method-11
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL160 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testnormalizesignal`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L160 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testnormalizesignal_test_dict_signal_parsed`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #method-12
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL13 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L13 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_majority_long`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-13
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL137 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L137 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator_test_positive_sharpe_reward`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-14
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL62 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L62 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml_test_valid_with_temperature`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #method-15
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL119 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testnansafety`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L119 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testnansafety_test_inf_size_clamped`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-16
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL127 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskenginev2direct`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L127 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskenginev2direct_test_zero_notional_accepted`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #method-17
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL38 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L38 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract_get_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/tracing.py:4:from opentelemetry import trace
    ```
    ```
    /home/workspace/orchestration/tracing.py:7:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/orchestration/tracing.py:8:from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    ```

### INFERRED #method-18
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL175 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L175 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator_test_no_nan_on_weird_inputs`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-19
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL144 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L144 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius_test_radius_positive`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-20
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL33 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L33 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel_test_signal_direction_enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-21
- **Source:** `AsurDev/acos/contracts/scheduler_contract.py:LL7 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_schedulercontract`
- **Target:** `AsurDev/acos/contracts/scheduler_contract.py:L7 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_schedulercontract_schedule`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/test_deterministic_scheduler.py:38:    """schedule() with PRIORITY_ORDER is deterministic across multiple calls."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/test_deterministic_scheduler.py:46:    # Run schedule 5 times at tick=42 — should always return same result
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/test_deterministic_scheduler.py:49:        r = scheduler.schedule(tick=42, strategy=SchedulingStrategy.PRIORITY_ORDER)
    ```

### INFERRED #method-22
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL120 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L120 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_earth_radius_physical`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #method-23
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL202 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testnonan`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L202 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testnonan_test_no_nan_in_earth_results`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-24
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL135 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L135 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_no_nan`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #method-25
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL103 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L103 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_enabled_smooths_confidence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-26
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL122 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskenginev2direct`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L122 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskenginev2direct_test_accepts_within_exposure_limit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #method-27
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL132 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L132 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius_test_earth_radius_near_1au`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-28
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL151 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testliquiditycheck`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L151 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testliquiditycheck_test_small_order_approved`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-29
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL217 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testnonan`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L217 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testnonan_test_no_nan_in_saturn_results`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-30
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL180 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L180 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration_test_symbol_in_output`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-31
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL11 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testimports`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L11 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testimports_test_all_imports`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-32
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL214 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategypool`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L214 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategypool_test_top_k`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-33
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL170 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolregime`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L170 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolregime_test_rejects_extreme_regime`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-34
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL166 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L166 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator_test_summary_breakdown`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-35
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL70 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L70 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation_test_eccentric_anomaly_known_value`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-36
- **Source:** `AsurDev/acos/contracts/engine_contract.py:LL7 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract`
- **Target:** `AsurDev/acos/contracts/engine_contract.py:L7 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract_execute`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/main.py:94:            dag=["validate", "dispatch", "execute", "commit"],
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:131:        conn.execute("PRAGMA journal_mode=WAL")
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:132:        conn.execute("PRAGMA synchronous=NORMAL")
    ```

### INFERRED #method-37
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL194 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testsanitynansafety`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L194 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testsanitynansafety_test_zero_price_rejected`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-38
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL111 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L111 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator_test_evaluate_insufficient_data`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-39
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL168 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L168 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration_test_timestamp_is_iso_format`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-40
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL46 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L46 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel_test_confidence_out_of_range_rejected`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #method-41
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL283 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testinvalidagentyaml`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L283 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testinvalidagentyaml_test_empty_capabilities`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #method-42
- **Source:** `AsurDev/acos.py:LL168 :: asurdev_acos_acosorchestrator`
- **Target:** `AsurDev/acos.py:L168 :: asurdev_acos_acosorchestrator_load_policy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:53:    and resolves the preferred mutation class based on policy mode.
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_planner.py:1:"""MutationPlanner — generates concrete mutation plans from policy intent."""
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_planner.py:85:    Generates concrete MutationExecutionSpec from policy + state context.
    ```

### INFERRED #method-43
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL26 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testorbitalelements`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L26 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testorbitalelements_test_earth_elements_exist`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-44
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL303 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L303 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent_test_evolve_returns_correct_size`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-45
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL310 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L310 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow_test_lag_disabled_no_smoothing`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-46
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL43 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L43 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_majority_short`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-47
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL10 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:L10 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rag_agent_integration.py
    ```

### INFERRED #method-48
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL250 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testintegration`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L250 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testintegration_test_full_pipeline`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-49
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL77 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskengineintegration`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L77 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskengineintegration_test_reduced_on_high_exposure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #method-50
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL86 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L86 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel_test_confidence_zero_valid`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

---

## Bucket: relation = `re_exports` (38 edges)

### INFERRED #re_exports-1
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL4 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/models.py:L1 :: branding_models`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/models.py:2:Pydantic models for input validation.
    ```
    ```
    /home/workspace/atom-federation-os/federation/models.py:4:from .models import ConsensusResult
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/branch.py:4:Data models for branching-aware execution.
    ```

### INFERRED #re_exports-2
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L1 :: alignment_drift_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/consistency_v2/test_realtime_divergence_detector.py:31:    detector = RealtimeDivergenceDetector(
    ```
    ```
    /home/workspace/atom-federation-os/consistency_v2/test_realtime_divergence_detector.py:35:    report = detector.verify()
    ```
    ```
    /home/workspace/atom-federation-os/consistency_v2/test_realtime_divergence_detector.py:41:    report = detector.verify()
    ```

### INFERRED #re_exports-3
- **Source:** `audit_repo/db/__init__.py:LL12 :: audit_repo_db_init_py_db_init`
- **Target:** `audit_repo/db/init.py:L1 :: audit_repo_db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/v106_liveness_proof.py:119:    init = ADLRState(RecoveryAction.REWEIGHT, 1, OscillationStage.ATTEMPT, 0.0, 1)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/v106_liveness_proof.py:120:    frontier = {init}
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```

### INFERRED #re_exports-4
- **Source:** `push/db/__init__.py:LL12 :: push_db_init_py_db_init`
- **Target:** `push/db/init.py:L1 :: push_db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    cross_submodule: push/db/__init__.py -> push/db/init.py
    ```

### INFERRED #re_exports-5
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL6 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/loader.py:L1 :: branding_loader`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas/branding/__init__.py:6:from .loader import load_by_tenant_id, load_by_api_key, load_default
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/branding/loader.py:2:saas/branding/loader.py
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/branding/service.py:4:from .loader import load_by_tenant_id, load_by_api_key, load_default
    ```

### INFERRED #re_exports-6
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL28 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L1 :: byzantine_message_signatures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/security/inbound_security_gate.py:7:  - Verify signatures via FederationMessageSigning (HMAC-SHA256)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_resilience_v65.py:2:Tests for v6.5 resilience modules — matched to actual API signatures.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/observability/tests/test_replay_subscriber.py:10:  - backward-compatible: accepts (event) and (event, lag_ms=..., speed=...) signatures
    ```

### INFERRED #re_exports-7
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL23 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/stability_governor.py:L1 :: v8_2a_safety_foundations_stability_governor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/tests/test_v67_meta_coherence.py:273:    assert mc.governor.mode == GovernorMode.STRICT
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/meta_coherence_controller.py:104:        self.governor = ObjectiveStabilityGovernor(mode=governor_mode)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/meta_coherence_controller.py:210:        governor_decision = self.governor.evaluate(J_raw, confidence=0.8)
    ```

### INFERRED #re_exports-8
- **Source:** `atom-federation-os/rpc/__init__.py:LL34 :: rpc_init`
- **Target:** `atom-federation-os/rpc/client.py:L1 :: rpc_client`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:179:    async with httpx.AsyncClient() as client:
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:183:                resp = await client.get(url, timeout=5)
    ```
    ```
    /home/workspace/roma-execution-bridge/consistency/global_state_model.py:206:        # Placeholder — integrate with kubernetes client
    ```

### INFERRED #re_exports-9
- **Source:** `astrofin-sentinel-v5/db/__init__.py:LL12 :: astrofin_sentinel_v5_db_init_py_db_init`
- **Target:** `astrofin-sentinel-v5/db/init.py:L1 :: astrofin_sentinel_v5_db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #re_exports-10
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL7 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/middleware.py:L1 :: branding_middleware`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas_api/middleware.py:3:from starlette.middleware.base import BaseHTTPMiddleware
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/middleware.py:16:    app.middleware("http")(LogRequestMiddleware)
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/server.py:13:from saas_api.middleware import LogRequestMiddleware
    ```

### INFERRED #re_exports-11
- **Source:** `atom-federation-os/alignment/__init__.py:LL33 :: alignment_init`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L1 :: alignment_rollback_engine_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:78:        v2 = rng2.random()
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:79:        assert v1 == v2, f"Same seed produced different values: {v1} != {v2}"
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:89:        v2 = rng2.random()
    ```

### INFERRED #re_exports-12
- **Source:** `atom-federation-os/rpc/__init__.py:LL35 :: rpc_init`
- **Target:** `atom-federation-os/rpc/mesh.py:L1 :: rpc_mesh`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:28:from .mesh import NodeMesh
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:58:    def attach_mesh(self, mesh: NodeMesh) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:59:        self._mesh = mesh
    ```

### INFERRED #re_exports-13
- **Source:** `db/__init__.py:LL12 :: db_init_py_db_init`
- **Target:** `db/init.py:L1 :: db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:97:    _coherence_history: list[float] = field(default_factory=list, init=False)
    ```
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:98:    _history_timestamps: list[int] = field(default_factory=list, init=False)
    ```
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:99:    _last_decision: ResponseDecision | None = field(default=None, init=False)
    ```

### INFERRED #re_exports-14
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL21 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/mutation_ledger.py:L1 :: v8_2a_safety_foundations_mutation_ledger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/trust/trust_sync_protocol.py:14:  - Outbound: aggregate local ledger changes since last sync → delta
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust/trust_sync_protocol.py:15:  - Inbound: merge remote delta into local ledger via LedgerReconciliation
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust/trust_sync_protocol.py:24:       merge into local ledger
    ```

### INFERRED #re_exports-15
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL30 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/quorum.py:L1 :: byzantine_quorum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation.consensus_resolver.py:80:                source="quorum",
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_operator_reconciler.py:126:    """Step 5 — Phase 5: quorum breach → Failed phase."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/consensus_resolver.py:71:        # quorum threshold
    ```

### INFERRED #re_exports-16
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL3 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/rpc_server.py:L1 :: shared_rpc_server`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/karl_cli.py:134:@click.option("--with-metrics", is_flag=True, help="Start Prometheus /metrics server on port 9091")
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:142:        click.echo("Metrics server started on 0.0.0.0:9091")
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:155:    """Prometheus /metrics server commands."""
    ```

### INFERRED #re_exports-17
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL14 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/invariant_checker.py:L1 :: v8_2a_safety_foundations_invariant_checker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/merge_engine.py:139:        # In practice these come from the equivalence checker context
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/v107_cross_layer_proof.py:120:    Formal cross-layer consistency checker.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/merge_engine.py:139:        # In practice these come from the equivalence checker context
    ```

### INFERRED #re_exports-18
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL12 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/explainable_divergence_engine.py:L1 :: consistency_v3_explainable_divergence_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/web/callbacks.py:352:            engine = EvolutionEngine(
    ```
    ```
    /home/workspace/web/callbacks.py:360:            get_engine_ref._engine = engine
    ```
    ```
    /home/workspace/web/callbacks.py:416:        engine = getattr(get_engine_ref, "_engine", None)
    ```

### INFERRED #re_exports-19
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL13 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/unified_state_metric_tensor.py:L1 :: consistency_v3_unified_state_metric_tensor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/unified_state_metric_tensor.py:4:v7.2 — UnifiedStateMetricTensor: combines all divergence axes into one tensor metric.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/unified_state_metric_tensor.py:13:The tensor is a rank-0 (scalar) metric: S_full = w · axis_vector
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/__init__.py:8:- unified_state_metric_tensor.py  : S(exec, replay) → tensor metric combining all divergence axes
    ```

### INFERRED #re_exports-20
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL5 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/service.py:L1 :: branding_service`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/health.py:7:    return {"status": "ok", "service": "ROMA SaaS API", "version": "1.0.0"}
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/server.py:206:        "service": "ROMA GPU Worker",
    ```
    ```
    /home/workspace/atom-federation-os/rpc/server.py:2:gRPC server — exposes AtomNode service.
    ```

### INFERRED #re_exports-21
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL2 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/drl_bridge.py:L1 :: shared_drl_bridge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/__init__.py:10:adapter      TransportAdapter (DRL ↔ gRPC bridge)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/integration/persistence_bridge.py:322:        bridge = PersistenceBridge(tick=42)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/integration/persistence_bridge.py:325:        bridge.state_window.record_tick(
    ```

### INFERRED #re_exports-22
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL22 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/rollback_engine.py:L1 :: v8_2a_safety_foundations_rollback_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:2:pbft_consensus.py — PBFT-lite consensus engine for v9.8
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:310:    engine = PBFTLiteConsensusEngine(node_id="node_0", n_nodes=4, signer=signer, max_rounds=3)
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:314:    pre_prep = engine.send_pre_prepare(digest)
    ```

### INFERRED #re_exports-23
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL29 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/pbft_consensus.py:L1 :: byzantine_pbft_consensus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/ha/raft_consensus.py:2:"""ROMA Raft Consensus Layer — True distributed consensus implementation."""
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/raft_consensus.py:29:    """True Raft consensus node — leader election + log replication + membership."""
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/raft_consensus.py:142:        """Add new node to cluster. Requires consensus."""
    ```

### INFERRED #re_exports-24
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL8 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L1 :: v8_2b_controlled_autocorrection_mutation_executor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:90:    logger.info("executor.running_topology")
    ```
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:91:    executor = TopologyExecutor(topology, state)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:92:    results = await executor.run()
    ```

### INFERRED #re_exports-25
- **Source:** `atom-federation-os/rpc/__init__.py:LL37 :: rpc_init`
- **Target:** `atom-federation-os/rpc/server.py:L1 :: rpc_server`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/karl_cli.py:134:@click.option("--with-metrics", is_flag=True, help="Start Prometheus /metrics server on port 9091")
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:142:        click.echo("Metrics server started on 0.0.0.0:9091")
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:155:    """Prometheus /metrics server commands."""
    ```

### INFERRED #re_exports-26
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL3 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:L1 :: v8_2b_controlled_autocorrection_feedback_injection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:1:"""ClusterSimulator — simulates N-node federation cluster with fault injection.
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:105:    """N-node federation cluster with scenario-based fault injection."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:315:        """Apply scenario-based fault injection."""
    ```

### INFERRED #re_exports-27
- **Source:** `data_room/resolvers/__init__.py:LL13 :: resolvers_init`
- **Target:** `data_room/resolvers/base.py:L1 :: resolvers_base`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:446:        logger.error(f"[KARLSynthesisAgent] Fell back to base synthesis: {e}")
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/middleware.py:3:from starlette.middleware.base import BaseHTTPMiddleware
    ```
    ```
    /home/workspace/roma-execution-bridge/cost/predictor.py:72:        base = benchmarks.get(plugin_type, 3600)
    ```

### INFERRED #re_exports-28
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL11 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/causal_semantic_space.py:L1 :: consistency_v3_causal_semantic_space`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/test_causal_semantic_space.py:78:        space = CausalSemanticSpace(domain="test")
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/test_causal_semantic_space.py:79:        e_vec, r_vec = space.embed(
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/test_causal_semantic_space.py:87:        space = CausalSemanticSpace(domain="test")
    ```

### INFERRED #re_exports-29
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL13 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:L1 :: v8_2b_controlled_autocorrection_policy_selector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/config/crd/controller/operator.py:241:            "selector": {"roma.io/tenant": tenant_id},
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:1:"""Policy synthesis: context + mutation policy + selector."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:12:    """Operating mode for the policy selector."""
    ```

### INFERRED #re_exports-30
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL27 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/byzantine_detector.py:L1 :: byzantine_byzantine_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/byzantine/byzantine_detector.py:210:    detector = ByzantineDetector(n_nodes=3, suspicion_threshold=0.25)
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/byzantine_detector.py:218:    indicator = detector.assess(report, entropy, [], dom_fraction=0.35)
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/byzantine_detector.py:220:    assert detector.is_consensus_safe(indicator) is True
    ```

### INFERRED #re_exports-31
- **Source:** `data_room/__init__.py:LL2 :: data_room_init`
- **Target:** `data_room/observability.py:L1 :: data_room_observability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:301:# ── observability ──────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:297:        "observability": await dag.get_observability_report(dag_id),
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/governance.py:257:        # Persist current state to Redis for observability
    ```

### INFERRED #re_exports-32
- **Source:** `roma-execution-bridge/saas/webhooks/__init__.py:LL1 :: webhooks_init`
- **Target:** `roma-execution-bridge/saas/webhooks/revenue_share.py:L1 :: webhooks_revenue_share`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/tests/test_revenue_share.py:60:    print("\n✅ All revenue-share tests passed")
    ```
    ```
    /home/workspace/atom-federation-os/federation/semantic/v910.py:409:        # If GOSSIP and CONSENSUS events share entity_hash, they agree by definition.
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gsl.py:267:        """Branch-observation entropy: how many branches share observations."""
    ```

### INFERRED #re_exports-33
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL31 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/view_change.py:L1 :: byzantine_view_change`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:314:    Documentation of schema change needed in DeltaGossipMessage (protocol.py).
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/node_weights.py:51:      - weights do NOT change during consensus round
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:53:    max_trust_delta: float = 0.15 # maximum trust change per epoch per node
    ```

### INFERRED #re_exports-34
- **Source:** `atom-federation-os/rpc/__init__.py:LL33 :: rpc_init`
- **Target:** `atom-federation-os/rpc/adapter.py:L1 :: rpc_adapter`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:42:    This adapter translates DRL's decisions to real network I/O.
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:71:        then adapter sends the result over real RPC.
    ```
    ```
    /home/workspace/atom-federation-os/rpc/server.py:20:    SBS enforcement, ordering, and DRL processing happen upstream in the adapter.
    ```

### INFERRED #re_exports-35
- **Source:** `atom-federation-os/orchestration/ExecutionGateway/__init__.py:LL10 :: executiongateway_init`
- **Target:** `atom-federation-os/orchestration/ExecutionGateway/execution_gateway.py:L1 :: executiongateway_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:51:    We verify the gateway code CONSISTENCY with the DFA spec:
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:87:    # P6 federated gateway — has its own DFA but delegates through ExecutionGateway
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:103:    # apply_mutation in mutation_executor is PERMITTED (internal gateway wrapper)
    ```

### INFERRED #re_exports-36
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL18 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L1 :: v8_2b_controlled_autocorrection_severity_mapper`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```

### INFERRED #re_exports-37
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL8 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/cache.py:L1 :: branding_cache`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:28:    nu: bool          # nonce_used: nonce recorded in cache
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:62:    Both exec() calls pass gates because cache not yet updated.
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:73:        # nonce_used=FALSE here means: NOT YET in cache (will be after first exec)
    ```

### INFERRED #re_exports-38
- **Source:** `atom-federation-os/alignment/__init__.py:LL27 :: alignment_init`
- **Target:** `atom-federation-os/alignment/plan_reality_comparator.py:L1 :: alignment_plan_reality_comparator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

---

## Bucket: relation = `uses` (50 edges)

### INFERRED #uses-1
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL32 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testnormalizesignal`
- **Target:** `trading/risk_v2.py:L57 :: trading_risk_v2_py_trading_risk_v2_riskenginev2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskenginev2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-2
- **Source:** `audit_repo/langgraph_schema.py:LL309 :: audit_repo_langgraph_schema_py_agentpool`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-3
- **Source:** `audit_repo/backtest/engine.py:LL20 :: audit_repo_backtest_engine_py_backtest_engine_trade`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-4
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testdrawdownkillswitch`
- **Target:** `trading/risk_v2.py:L38 :: trading_risk_v2_py_trading_risk_v2_assetposition`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'assetposition' not found in trading/risk_v2.py
    ```

### INFERRED #uses-5
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolatilitytargeting`
- **Target:** `trading/risk_v2.py:L57 :: trading_risk_v2_py_trading_risk_v2_riskenginev2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskenginev2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-6
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-7
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL3 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testagentresponsemodel`
- **Target:** `push/core/base_agent.py:L41 :: push_core_base_agent_py_core_base_agent_signaldirection`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'signaldirection' not found in push/core/base_agent.py
    ```

### INFERRED #uses-8
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL11 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testscoredstrategy`
- **Target:** `push/meta_rl/strategy_evaluator.py:L38 :: push_meta_rl_strategy_evaluator_py_meta_rl_strategy_evaluator_strategyevaluator`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'strategyevaluator' not found in push/meta_rl/strategy_evaluator.py
    ```

### INFERRED #uses-9
- **Source:** `astrofin-sentinel-v5/agents/karl_synthesis.py:LL44 :: astrofin_sentinel_v5_agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-10
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL4 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `push/core/base_agent.py:L49 :: push_core_base_agent_py_core_base_agent_agentresponse`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'agentresponse' not found in push/core/base_agent.py
    ```

### INFERRED #uses-11
- **Source:** `push/langgraph_schema.py:LL309 :: push_langgraph_schema_py_stategraph`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-12
- **Source:** `astrofin-sentinel-v5/backtest/engine.py:LL20 :: astrofin_sentinel_v5_backtest_engine_py_backtest_engine_trade`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-13
- **Source:** `astrofin-sentinel-v5/langgraph_schema.py:LL309 :: astrofin_sentinel_v5_langgraph_schema_agentstate`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-14
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL26 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolatilitytargeting`
- **Target:** `trading/mode.py:L38 :: trading_mode_py_trading_mode_modeenforcer`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'modeenforcer' not found in trading/mode.py
    ```

### INFERRED #uses-15
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testheliocentriclongitude`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-16
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL32 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskenginev2direct`
- **Target:** `trading/risk_v2.py:L57 :: trading_risk_v2_py_trading_risk_v2_riskenginev2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskenginev2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-17
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL32 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testsafetygatemodes`
- **Target:** `trading/risk_v2.py:L21 :: trading_risk_v2_py_trading_risk_v2_riskconfigv2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskconfigv2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-18
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testdrawdownkillswitch`
- **Target:** `trading/execution/sanity.py:L11 :: trading_execution_sanity_py_execution_sanity_validationstatus`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'validationstatus' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-19
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL315 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `push/core/base_agent.py:L49 :: push_core_base_agent_py_core_base_agent_agentresponse`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'agentresponse' not found in push/core/base_agent.py
    ```

### INFERRED #uses-20
- **Source:** `backtest/engine.py:LL20 :: backtest_engine_py_backtest_engine_trade`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-21
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL11 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testevaluationresult`
- **Target:** `push/meta_rl/strategy_evaluator.py:L38 :: push_meta_rl_strategy_evaluator_py_meta_rl_strategy_evaluator_strategyevaluator`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'strategyevaluator' not found in push/meta_rl/strategy_evaluator.py
    ```

### INFERRED #uses-22
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation`
- **Target:** `push/core/kepler.py:L26 :: push_core_kepler_py_core_kepler_orbitalelements`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'orbitalelements' not found in push/core/kepler.py
    ```

### INFERRED #uses-23
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolatilitytargeting`
- **Target:** `trading/execution/sanity.py:L55 :: trading_execution_sanity_py_execution_sanity_executionsanitychecker`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'executionsanitychecker' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-24
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL103 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testsafetygatemodes`
- **Target:** `trading/safety_gate.py:L78 :: trading_safety_gate_py_trading_safety_gate_safetygate`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'safetygate' not found in trading/safety_gate.py
    ```

### INFERRED #uses-25
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testorbitalelements`
- **Target:** `push/core/kepler.py:L26 :: push_core_kepler_py_core_kepler_orbitalelements`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'orbitalelements' not found in push/core/kepler.py
    ```

### INFERRED #uses-26
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testexposurecontrol`
- **Target:** `trading/risk_v2.py:L57 :: trading_risk_v2_py_trading_risk_v2_riskenginev2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskenginev2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-27
- **Source:** `agents/karl_synthesis.py:LL44 :: agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-28
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testdrawdownkillswitch`
- **Target:** `trading/execution/sanity.py:L18 :: trading_execution_sanity_py_execution_sanity_marketstate`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'marketstate' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-29
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL11 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator`
- **Target:** `push/meta_rl/strategy_evaluator.py:L69 :: push_meta_rl_strategy_evaluator_py_evaluationresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'evaluationresult' not found in push/meta_rl/strategy_evaluator.py
    ```

### INFERRED #uses-30
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL315 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow`
- **Target:** `push/core/base_agent.py:L41 :: push_core_base_agent_py_core_base_agent_signaldirection`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'signaldirection' not found in push/core/base_agent.py
    ```

### INFERRED #uses-31
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testnansafety`
- **Target:** `trading/execution/sanity.py:L18 :: trading_execution_sanity_py_execution_sanity_marketstate`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'marketstate' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-32
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL26 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testexposurecontrol`
- **Target:** `trading/mode.py:L10 :: trading_mode_py_trading_mode_tradingmode`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'tradingmode' not found in trading/mode.py
    ```

### INFERRED #uses-33
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL26 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testdrawdownkillswitch`
- **Target:** `trading/mode.py:L10 :: trading_mode_py_trading_mode_tradingmode`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'tradingmode' not found in trading/mode.py
    ```

### INFERRED #uses-34
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL4 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `push/core/base_agent.py:L41 :: push_core_base_agent_py_core_base_agent_signaldirection`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'signaldirection' not found in push/core/base_agent.py
    ```

### INFERRED #uses-35
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolatilitytargeting`
- **Target:** `trading/risk_v2.py:L21 :: trading_risk_v2_py_trading_risk_v2_riskconfigv2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskconfigv2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-36
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL26 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testexposurecontrol`
- **Target:** `trading/mode.py:L38 :: trading_mode_py_trading_mode_modeenforcer`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'modeenforcer' not found in trading/mode.py
    ```

### INFERRED #uses-37
- **Source:** `astrofin-sentinel-v5/orchestration/sentinel_v5.py:LL21 :: astrofin_sentinel_v5_orchestration_sentinel_v5_py_agentpool`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-38
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL9 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent`
- **Target:** `push/meta_rl/meta_agent.py:L103 :: push_meta_rl_meta_agent_py_meta_rl_meta_agent_metaagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'metaagent' not found in push/meta_rl/meta_agent.py
    ```

### INFERRED #uses-39
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testdrawdownkillswitch`
- **Target:** `trading/risk_v2.py:L21 :: trading_risk_v2_py_trading_risk_v2_riskconfigv2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskconfigv2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-40
- **Source:** `push/agents/karl_synthesis.py:LL44 :: push_agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-41
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL32 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testsafetydisabled`
- **Target:** `trading/risk_v2.py:L57 :: trading_risk_v2_py_trading_risk_v2_riskenginev2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskenginev2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-42
- **Source:** `astrofin-sentinel-v5/backtest/engine.py:LL20 :: astrofin_sentinel_v5_backtest_engine_py_backtest_engine_backtestresult`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-43
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL9 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testevaluationresult`
- **Target:** `push/meta_rl/meta_agent.py:L103 :: push_meta_rl_meta_agent_py_meta_rl_meta_agent_metaagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'metaagent' not found in push/meta_rl/meta_agent.py
    ```

### INFERRED #uses-44
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testnonan`
- **Target:** `push/core/kepler.py:L90 :: push_core_kepler_py_core_kepler_keplerorbit`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerorbit' not found in push/core/kepler.py
    ```

### INFERRED #uses-45
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL3 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testrouter`
- **Target:** `push/core/base_agent.py:L49 :: push_core_base_agent_py_core_base_agent_agentresponse`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'agentresponse' not found in push/core/base_agent.py
    ```

### INFERRED #uses-46
- **Source:** `astrofin-sentinel-v5/backtest/engine.py:LL20 :: astrofin_sentinel_v5_backtest_engine_py_backtest_engine_ohlcv`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-47
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL9 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent`
- **Target:** `push/meta_rl/meta_agent.py:L81 :: push_meta_rl_meta_agent_py_meta_rl_meta_agent_evolutionconfig`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'evolutionconfig' not found in push/meta_rl/meta_agent.py
    ```

### INFERRED #uses-48
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL345 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration`
- **Target:** `push/agents/karl_synthesis.py:L70 :: push_agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'karlsynthesisagent' not found in push/agents/karl_synthesis.py
    ```

### INFERRED #uses-49
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL315 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration`
- **Target:** `push/core/base_agent.py:L49 :: push_core_base_agent_py_core_base_agent_agentresponse`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'agentresponse' not found in push/core/base_agent.py
    ```

### INFERRED #uses-50
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL12 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testevolutionengine`
- **Target:** `push/meta_rl/strategy_pool.py:L16 :: push_meta_rl_strategy_pool_py_meta_rl_strategy_pool_scoredstrategy`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'scoredstrategy' not found in push/meta_rl/strategy_pool.py
    ```

---

## Bucket: relation = `defines` (50 edges)

### INFERRED #defines-1
- **Source:** `AsurDev/scripts/day1-network.sh:LL33 :: asurdev_scripts_day1_network_sh_scripts_day1_network`
- **Target:** `AsurDev/scripts/day1-network.sh:L33 :: asurdev_scripts_day1_network_sh_scripts_day1_network_ros_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:182:                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    ```
    ```
    /home/workspace/atom-federation-os/observability/core/__init__.py:5:  pip install prometheus_client opentelemetry-api opentelemetry-sdk
    ```
    ```
    /home/workspace/atom-federation-os/observability/core/otel_instrumentation.py:10:This is the ONLY module that imports opentelemetry-api/sdk.
    ```

### INFERRED #defines-2
- **Source:** `atom-federation-os/build_push.sh:LL13 :: atom_federation_os_build_push`
- **Target:** `atom-federation-os/build_push.sh:L13 :: atom_federation_os_build_push_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/__main__.py:29:        logger.info("masfactory.mode_enabled")
    ```
    ```
    /home/workspace/orchestration/__main__.py:30:        logger.info("masfactory.attempting_topology")
    ```
    ```
    /home/workspace/orchestration/__main__.py:41:            logger.info("masfactory.completed_successfully")
    ```

### INFERRED #defines-3
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/__main__.py:29:        logger.info("masfactory.mode_enabled")
    ```
    ```
    /home/workspace/orchestration/__main__.py:30:        logger.info("masfactory.attempting_topology")
    ```
    ```
    /home/workspace/orchestration/__main__.py:41:            logger.info("masfactory.completed_successfully")
    ```

### INFERRED #defines-4
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL48 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L48 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_gen_keys`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:265:            axes = list(axis_coherences.keys())
    ```
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:268:            axes = list(axis_coherences.keys())
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:175:    sk = set(spec.keys())
    ```

### INFERRED #defines-5
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL48 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L48 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_install_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler_v2.py:91:    """Submit job to selected partition via slurm wrapper."""
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py:156:    "rtx-node": {"ip": "10.20.20.10", "capabilities": ["gpu", "slurm", "ceph_osd", "ray_head"]},
    ```

### INFERRED #defines-6
- **Source:** `home-cluster-iac/deploy.sh:LL116 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L116 :: home_cluster_iac_deploy_day7`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:131:    # goal="deploy" overlaps with step_name "deploy" → L3≈0
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:132:    plan_deg = make_plan("pd", "deploy", [pnode("n2","deploy","t","n1")], ["n1","n2"])
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:133:    trace_deg = make_trace("td", "pd", "deploy", [
    ```

### INFERRED #defines-7
- **Source:** `AsurDev/scripts/day5-ray.sh:LL21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray`
- **Target:** `AsurDev/scripts/day5-ray.sh:L21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:319:        ok = "✅" if result == (not expect_vulnerable) else "❌"
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:321:        print(f"  {ok} {prop}: {result} {expected}")
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:123:        ok = passed == total
    ```

### INFERRED #defines-8
- **Source:** `engine_sandbox_runtime.sh:LL18 :: engine_sandbox_runtime`
- **Target:** `engine_sandbox_runtime.sh:L18 :: engine_sandbox_runtime_overlay_root`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:54:def _safe_relative(p: pathlib.Path, root: pathlib.Path) -> str:
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:56:        return str(p.relative_to(root))
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:203:                        help="Repository root (default: script parent)")
    ```

### INFERRED #defines-9
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL30 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L30 :: atom_federation_os_pop_os_ai_dev_setup_gpu_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation.consensus_resolver.py:102:    # safety check
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:89:    # P2-wrapped internal method — MUST delegate to Gateway (verified by check)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:160:# ── LTL re-check ────────────────────────────────────────────────────────────────
    ```

### INFERRED #defines-10
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:88:        self.assertIn("wg-quick", mgr._available_binaries())
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:113:    ok, msg = _run(["wg-quick", "down", interface])
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:117:    ok2, msg2 = _run(["wg-quick", "up", interface])
    ```

### INFERRED #defines-11
- **Source:** `home-cluster-iac/deploy.sh:LL104 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L104 :: home_cluster_iac_deploy_day3`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:131:    # goal="deploy" overlaps with step_name "deploy" → L3≈0
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:132:    plan_deg = make_plan("pd", "deploy", [pnode("n2","deploy","t","n1")], ["n1","n2"])
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:133:    trace_deg = make_trace("td", "pd", "deploy", [
    ```

### INFERRED #defines-12
- **Source:** `AsurDev/scripts/day3-compute.sh:LL94 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L94 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia_container_toolkit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:172:# ── compute Δ ────────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:186:        m = prover.compute(chain)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:201:        m = prover.compute(chain)
    ```

### INFERRED #defines-13
- **Source:** `atom-federation-os/scripts/bootstrap_env.sh:LL18 :: scripts_bootstrap_env`
- **Target:** `atom-federation-os/scripts/bootstrap_env.sh:L18 :: scripts_bootstrap_env_pythonhashseed`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/environment_hash.py:153:        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/core/runtime/runtime_guard.py:567:        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
    ```
    ```
    /home/workspace/atom-federation-os/core/runtime/runtime_guard.py:567:        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
    ```

### INFERRED #defines-14
- **Source:** `AsurDev/scripts/test_suite.sh:LL84 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L84 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l2_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler_v2.py:91:    """Submit job to selected partition via slurm wrapper."""
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py:156:    "rtx-node": {"ip": "10.20.20.10", "capabilities": ["gpu", "slurm", "ceph_osd", "ray_head"]},
    ```

### INFERRED #defines-15
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL37 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L37 :: atom_federation_os_pop_os_ai_dev_setup_stage1_preflight`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/middleware.py:27:    4. CORS                 — outermost, handles preflight
    ```

### INFERRED #defines-16
- **Source:** `AsurDev/self_healing/watchdog.sh:LL61 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L61 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_inc_failure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:125:        for failure in result.get("failures", []):
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:126:            log("FAIL", "L3-Proof", f"  {failure}")
    ```
    ```
    /home/workspace/atom-federation-os/scripts/verify_workspace_root.py:47:    Returns (module, path_used) or None on failure.
    ```

### INFERRED #defines-17
- **Source:** `AsurDev/scripts/day3-compute.sh:LL135 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L135 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_update_hosts`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/config/crd/controller/operator.py:117:                "hosts": [f"{subdomain}.{domain}", domain],
    ```

### INFERRED #defines-18
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL144 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L144 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_cgroup_conf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:170:    conf = result["final_recommendation"].get("confidence", 0)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5_mas.py:171:    logger.info("masfactory.result", signal=sig, confidence=conf)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/otl.py:117:        conf = self.tracker.get(sensor_id)
    ```

### INFERRED #defines-19
- **Source:** `AsurDev/scripts/day7-integration.sh:LL22 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L22 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_create_slurm_ray_bridge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/__init__.py:10:adapter      TransportAdapter (DRL ↔ gRPC bridge)
    ```
    ```
    /home/workspace/atom-federation-os/alignment/plan_reality_comparator.py:7:This is the bridge: planner output ↔ execution reality.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/integration/persistence_bridge.py:322:        bridge = PersistenceBridge(tick=42)
    ```

### INFERRED #defines-20
- **Source:** `AsurDev/scripts/day5-ray.sh:LL27 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray`
- **Target:** `AsurDev/scripts/day5-ray.sh:L27 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_install_ray`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:124:            "apiVersion": "ray.io/v1alpha1",
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:139:                                    "name": "ray-head",
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:140:                                    "image": "rayproject/ray:latest-gpu",
    ```

### INFERRED #defines-21
- **Source:** `AsurDev/self_healing/health_check.sh:LL20 :: asurdev_self_healing_health_check_sh_self_healing_health_check`
- **Target:** `AsurDev/self_healing/health_check.sh:L20 :: asurdev_self_healing_health_check_sh_self_healing_health_check_log`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/audit/event_log.py:1:"""ROMA Audit Log — Immutable append-only event log."""
    ```
    ```
    /home/workspace/roma-execution-bridge/audit/event_log.py:61:    log = AuditLog()
    ```
    ```
    /home/workspace/roma-execution-bridge/audit/event_log.py:62:    log.log_event("alice", "org_acme", "JOB_EXECUTED", {"job_id": "j001", "cost": 2.50})
    ```

### INFERRED #defines-22
- **Source:** `AsurDev/self_healing/watchdog.sh:LL268 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L268 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_check_gpu_available`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:342:                logger.info("[DB] PostgreSQL not available, using SQLite")
    ```
    ```
    /home/workspace/atom-federation-os/cluster/node/healthcheck.py:7:from a context that may not have the rest of the codebase available
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:182:# ── Add paths for real packages when available ───────────────────────
    ```

### INFERRED #defines-23
- **Source:** `AsurDev/scripts/day3-compute.sh:LL54 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L54 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/consistency/global_state_model.py:163:        # Placeholder — integrate with nvidia-smi or K8s metrics
    ```
    ```
    /home/workspace/roma-execution-bridge/consistency/backpressure.py:127:        """Update GPU VRAM stats (called from nvidia-smi or K8s metrics)."""
    ```
    ```
    /home/workspace/roma-execution-bridge/k8s/roma_controller.py:81:                            "limits": {"nvidia.com/gpu": "1"} if gpu_required else {},
    ```

### INFERRED #defines-24
- **Source:** `AsurDev/scripts/day3-compute.sh:LL113 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L113 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_python_ml`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/ecosystem/plugin_registry.py:57:    print("Search ml:", reg.search("ml"))
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/candidates/generator.py:31:        self.ml = ml_predictor
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/pipeline.py:8:    python pipeline.py --export-csv --output /data/ml
    ```

### INFERRED #defines-25
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL183 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L183 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_create_mount_script`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:203:                        help="Repository root (default: script parent)")
    ```
    ```
    /home/workspace/atom-federation-os/scripts/ast_snapshot.py:204:                        help="Repository root (default: script parent)")
    ```
    ```
    /home/workspace/atom-federation-os/scripts/visualize_execution_graph.py:288:                        help='Repository root (default: script directory parent)')
    ```

### INFERRED #defines-26
- **Source:** `AsurDev/scripts/test_suite.sh:LL25 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L20 :: asurdev_scripts_test_suite_sh_scripts_test_suite_skip`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:20:  - Peers can skip re-proving if they already have proof_hash
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/routing.py:13:  3. If equal → skip (peer already has this state)
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/routing.py:55:      - If peer.last_root_hash == my_root_hash → peer is in sync, skip
    ```

### INFERRED #defines-27
- **Source:** `AsurDev/self_healing/watchdog.sh:LL55 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L55 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_reset_failures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:120:        result = {'passed': r.stdout.count('[PASS]'), 'total': r.stdout.count('[PASS]') + r.stdout.count('[FAIL]'), 'failures': []}
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:125:        for failure in result.get("failures", []):
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:141:        result = {'passed': r.stdout.count('[PASS]'), 'total': r.stdout.count('[PASS]') + r.stdout.count('[FAIL]'), 'failures': []}
    ```

### INFERRED #defines-28
- **Source:** `AsurDev/scripts/test_suite.sh:LL389 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L389 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l7`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:338:    """Runs a suite of federation scenarios and produces a report."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:1:"""Test suite for RCF — Reality Consensus Fusion layer v11.1."""
    ```

### INFERRED #defines-29
- **Source:** `home-cluster-iac/deploy.sh:LL113 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L113 :: home_cluster_iac_deploy_day6`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:131:    # goal="deploy" overlaps with step_name "deploy" → L3≈0
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:132:    plan_deg = make_plan("pd", "deploy", [pnode("n2","deploy","t","n1")], ["n1","n2"])
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:133:    trace_deg = make_trace("td", "pd", "deploy", [
    ```

### INFERRED #defines-30
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL32 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L32 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_check_munge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/tests/integration/test_ml_pipeline.py:49:      - 18 feature columns  (cpu, mem, gpu, disk, net, slurm, proc)
    ```
    ```
    /home/workspace/AsurDev/astrofin/trace_schema/trace.py:41:    scheduler_path: str = "slurm"   # slurm | ray | mixed
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:87:        trace.scheduler_path = "mixed" if (gpu_agents and cpu_agents) else ("slurm" if cpu_agents else "ray")
    ```

### INFERRED #defines-31
- **Source:** `AsurDev/scripts/test_suite.sh:LL33 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L33 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l1_network`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/gossip_protocol.py:83:            # Simulate network delivery — peer updates their state
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust/trust_vector.py:223:        """Serialize to plain dict for network transmission."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:149:        """Simulate network split: groups can't talk to each other."""
    ```

### INFERRED #defines-32
- **Source:** `AsurDev/cluster_status.sh:LL15 :: asurdev_cluster_status`
- **Target:** `AsurDev/cluster_status.sh:L15 :: asurdev_cluster_status_check_port`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/karl_cli.py:134:@click.option("--with-metrics", is_flag=True, help="Start Prometheus /metrics server on port 9091")
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:140:        t = threading.Thread(target=run_server, kwargs={"port": 9091, "host": "0.0.0.0"}, daemon=True)
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:160:@click.option("--port", default=9091, help="Port for /metrics server (default: 9091)")
    ```

### INFERRED #defines-33
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL61 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L61 :: atom_federation_os_pop_os_ai_dev_setup_stage3_nvidia`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/consistency/global_state_model.py:163:        # Placeholder — integrate with nvidia-smi or K8s metrics
    ```
    ```
    /home/workspace/roma-execution-bridge/consistency/backpressure.py:127:        """Update GPU VRAM stats (called from nvidia-smi or K8s metrics)."""
    ```
    ```
    /home/workspace/roma-execution-bridge/k8s/roma_controller.py:81:                            "limits": {"nvidia.com/gpu": "1"} if gpu_required else {},
    ```

### INFERRED #defines-34
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL60 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L60 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_deploy_ceph`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:51:    log.warning(f"Recovery: restarting ceph-osd.{osd_id}")
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:52:    ok, msg = _run(["systemctl", "restart", f"ceph-osd@{osd_id}"])
    ```

### INFERRED #defines-35
- **Source:** `home-cluster-iac/deploy.sh:LL58 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L58 :: home_cluster_iac_deploy_log_step`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:82:    def step(self, event: Event) -> GatewayState:
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:90:            self.step(e)
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:153:    dfa.step(Event.REQUEST_IN)
    ```

### INFERRED #defines-36
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL30 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L30 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:34:        warnings.warn(
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/shared/observability.py:62:    def warn(self, event: str, **details):
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:122:                self.logger.warn("peer_unreachable", peer=peer)
    ```

### INFERRED #defines-37
- **Source:** `AsurDev/scripts/test_suite.sh:LL26 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L26 :: asurdev_scripts_test_suite_sh_scripts_test_suite_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:34:        warnings.warn(
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:122:                self.logger.warn("peer_unreachable", peer=peer)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:154:                    self.logger.warn("peer_ping_fail", peer=peer)
    ```

### INFERRED #defines-38
- **Source:** `home-cluster-iac/deploy_and_verify.sh:LL318 :: home_cluster_iac_deploy_and_verify`
- **Target:** `home-cluster-iac/deploy_and_verify.sh:L318 :: home_cluster_iac_deploy_and_verify_generate_report`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:90:        report = json.load(open(repo / "formal_model" / "dfa_diff_report.json"))
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:91:        missing = report["delta"]["missing_count"]
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:92:        extra = report["delta"]["extra_count"]
    ```

### INFERRED #defines-39
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL322 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L322 :: atom_federation_os_pop_os_ai_dev_setup_stage14_k3s_multinode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust/trust_sync_protocol.py:381:    # ── setup ─────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/observability/core/otel_exporter.py:38:# Lock to make setup idempotent and thread-safe
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/observability/core/otel_exporter.py:63:        The current tracer (or None if OTel libs not installed / setup failed).
    ```

### INFERRED #defines-40
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL152 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L152 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_mount_cephfs`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/monitoring/exporters/ceph/ceph_exporter.py:12:CEPH_CMD = ["ceph", "-f", "json"]
    ```
    ```
    /home/workspace/home-cluster-iac/monitoring/exporters/ceph/ceph_exporter.py:17:    """ceph status --format json"""
    ```

### INFERRED #defines-41
- **Source:** `home-cluster-iac/deploy.sh:LL98 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L98 :: home_cluster_iac_deploy_day1`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:131:    # goal="deploy" overlaps with step_name "deploy" → L3≈0
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:132:    plan_deg = make_plan("pd", "deploy", [pnode("n2","deploy","t","n1")], ["n1","n2"])
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:133:    trace_deg = make_trace("td", "pd", "deploy", [
    ```

### INFERRED #defines-42
- **Source:** `AsurDev/scripts/test_suite.sh:LL278 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L278 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l6_ai_scheduler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/gossip_protocol.py:70:    # manual sync (called by external scheduler)                         #
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/connector.py:2:"""ROMA GPU Connector — Connects ROMA scheduler to GPU workers
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/connector.py:195:# Convenience function for scheduler
    ```

### INFERRED #defines-43
- **Source:** `AsurDev/scripts/test_suite.sh:LL22 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L22 :: asurdev_scripts_test_suite_sh_scripts_test_suite_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/__main__.py:29:        logger.info("masfactory.mode_enabled")
    ```
    ```
    /home/workspace/orchestration/__main__.py:30:        logger.info("masfactory.attempting_topology")
    ```
    ```
    /home/workspace/orchestration/__main__.py:41:            logger.info("masfactory.completed_successfully")
    ```

### INFERRED #defines-44
- **Source:** `home-cluster-iac/deploy_and_verify.sh:LL157 :: home_cluster_iac_deploy_and_verify`
- **Target:** `home-cluster-iac/deploy_and_verify.sh:L157 :: home_cluster_iac_deploy_and_verify_load_env`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:1:#!/usr/bin/env python3
    ```
    ```
    /home/workspace/roma-execution-bridge/billing/stripe_client.py:1:#!/usr/bin/env python3
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/server.py:1:#!/usr/bin/env python3
    ```

### INFERRED #defines-45
- **Source:** `home-cluster-iac/deploy.sh:LL35 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L35 :: home_cluster_iac_deploy_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:34:        warnings.warn(
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/shared/observability.py:62:    def warn(self, event: str, **details):
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:122:                self.logger.warn("peer_unreachable", peer=peer)
    ```

### INFERRED #defines-46
- **Source:** `AsurDev/scripts/day7-integration.sh:LL17 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L17 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:34:        warnings.warn(
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/shared/observability.py:62:    def warn(self, event: str, **details):
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/node/node.py:122:                self.logger.warn("peer_unreachable", peer=peer)
    ```

### INFERRED #defines-47
- **Source:** `AsurDev/scripts/day3-compute.sh:LL19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/tests/test_policy_sync.py:55:        ps = PolicySync("n1", replay_validator=lambda t: (True, "ok"))
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_policy_sync.py:59:        ps = PolicySync("n1", replay_validator=lambda t: (True, "ok"))
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_policy_sync.py:64:        ps = PolicySync("n1", replay_validator=lambda t: (True, "ok"))
    ```

### INFERRED #defines-48
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL28 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L28 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/__main__.py:29:        logger.info("masfactory.mode_enabled")
    ```
    ```
    /home/workspace/orchestration/__main__.py:30:        logger.info("masfactory.attempting_topology")
    ```
    ```
    /home/workspace/orchestration/__main__.py:41:            logger.info("masfactory.completed_successfully")
    ```

### INFERRED #defines-49
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL50 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L50 :: atom_federation_os_pop_os_ai_dev_setup_stage2_update`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/otl.py:49:    def update(self, readings):
    ```
    ```
    /home/workspace/atom-federation-os/alignment/otl.py:123:        rep = self.fusion.update(self._sensor_readings)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:162:        hasher.update(f"{node.file}:{node.line}:{node.name}".encode())
    ```

### INFERRED #defines-50
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL93 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L93 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_deploy_manual`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/gossip_protocol.py:70:    # manual sync (called by external scheduler)                         #
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/federation/gossip_protocol.py:70:    # manual sync (called by external scheduler)                         #
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/meta_coherence_controller.py:337:    def force_model_rebuild(self, reason: str = "manual") -> AlignmentSnapshot:
    ```

---

## Bucket: relation = `references` (50 edges)

### INFERRED #references-1
- **Source:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:LL105 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failureisolator_plan_rollback`
- **Target:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:L25 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failuretrigger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_algebra_validator.py:32:    ("G10", "RollbackEngine",              ("RollbackEngine","rollback","checkpoint")),
    ```
    ```
    /home/workspace/atom-federation-os/alignment/rcf.py:103:            actions.append(Action("ROLLBACK_SHADOW", "RCF detected critical drift", ("rollback", "shadow")))
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gsl.py:323:    # T3: high drift → rollback
    ```

### INFERRED #references-2
- **Source:** `AsurDev/ete/store/trace_store.py:LL76 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace_to_dict`
- **Target:** `AsurDev/ete/store/trace_store.py:L35 :: asurdev_ete_store_trace_store_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/roma-execution-bridge/operator_sdk/operator_base.py:39:    gpu = any("GPU" in str(c) for c in caps)
    ```

### INFERRED #references-3
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL119 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_any`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L75 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'executioncontext' not found in AsurDev/l9_ebl/capabilities/registry.py
    ```

### INFERRED #references-4
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL133 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_slidingwindow_get_window`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L67 :: asurdev_feature_pipeline_window_engine_py_datetime`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:10:from datetime import datetime, timezone
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:234:        "started_at": datetime.now(timezone.utc).isoformat(),
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:304:        "timestamp": datetime.now(timezone.utc).isoformat(),
    ```

### INFERRED #references-5
- **Source:** `AsurDev/feature_pipeline/embedding.py:LL91 :: asurdev_feature_pipeline_embedding_py_feature_pipeline_embedding_nodeembeddingbuilder_find_similar_nodes`
- **Target:** `AsurDev/feature_pipeline/embedding.py:L24 :: asurdev_feature_pipeline_embedding_py_ndarray`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/eigenstate_detector.py:93:    def _build_features(self, state: dict[str, float]) -> np.ndarray:
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/eigenstate_detector.py:102:    def _distance_to_eigenstate(self, feat: np.ndarray, es: Eigenstate) -> float:
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/eigenstate_detector.py:184:    def _learn_eigenstate(self, feat: np.ndarray) -> Eigenstate:
    ```

### INFERRED #references-6
- **Source:** `AsurDev/job_engine/engine.py:LL70 :: asurdev_job_engine_engine_py_job_engine_engine_jobeventhooks_on_retry`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:10:    job = _job_store.get(job_id)
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:11:    if not job:
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:14:    return {"job": job, "logs_url": f"/jobs/{job_id}/logs"}
    ```

### INFERRED #references-7
- **Source:** `AsurDev/job_engine/engine.py:LL64 :: asurdev_job_engine_engine_py_job_engine_engine_jobeventhooks_on_state_change`
- **Target:** `AsurDev/job_engine/engine.py:L20 :: asurdev_job_engine_engine_py_job_engine_engine_jobstate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:314:    Documentation of schema change needed in DeltaGossipMessage (protocol.py).
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/node_weights.py:51:      - weights do NOT change during consensus round
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:53:    max_trust_delta: float = 0.15 # maximum trust change per epoch per node
    ```

### INFERRED #references-8
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL231 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_schedule_job`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L68 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_jobrequest`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/adaptive_router.py:157:              (but NOT evicted from cluster — that's the healer's job)
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:10:    job = _job_store.get(job_id)
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:11:    if not job:
    ```

### INFERRED #references-9
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL55 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_init`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L55 :: asurdev_feature_pipeline_exporter_py_windowengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #references-10
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL76 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_default_fitness`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L16 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/trust/ledger_reconciliation.py:12:Merge strategy (per proof_hash):
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:92:    def run(self, task: str, num_workers: int | None = None, strategy: str = 'sequential') -> dict:
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:96:            'strategy': strategy,
    ```

### INFERRED #references-11
- **Source:** `AsurDev/feature_pipeline/embedding.py:LL57 :: asurdev_feature_pipeline_embedding_py_feature_pipeline_embedding_nodeembeddingbuilder_build_from_features`
- **Target:** `AsurDev/feature_pipeline/embedding.py:L24 :: asurdev_feature_pipeline_embedding_py_ndarray`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:73:    _recent_deltas: list[np.ndarray] = field(default_factory=list, init=False)
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:75:    _last_theta: np.ndarray | None = field(default=None, init=False)
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:128:    def dampen_oscillation(self, delta: np.ndarray) -> np.ndarray:
    ```

### INFERRED #references-12
- **Source:** `AsurDev/acos.py:LL285 :: asurdev_acos_acosorchestrator_architecture_summary`
- **Target:** `AsurDev/acos.py:L285 :: asurdev_acos_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:259:            # All workers on the most divergent axis + any axis below threshold
    ```

### INFERRED #references-13
- **Source:** `AsurDev/job_engine/engine.py:LL90 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_create_job`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:10:    job = _job_store.get(job_id)
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:11:    if not job:
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:14:    return {"job": job, "logs_url": f"/jobs/{job_id}/logs"}
    ```

### INFERRED #references-14
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL46 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator_validate_dag`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L29 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_contractviolation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/proof/proof_trace.py:122:        dag = trace.export_dag(record)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_proof_v76.py:83:        dag = pt.export_dag(record)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_proof_v76.py:84:        assert dag["decision_id"] == "d0"
    ```

### INFERRED #references-15
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL96 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L60 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctioncycleresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/auth/quota_engine.py:8:    Enforces GPU-second quotas per billing cycle.
    ```
    ```
    /home/workspace/roma-execution-bridge/auth/quota_engine.py:24:        self.cycle_start: Dict[str, float] = {} # tenant_id → cycle start
    ```
    ```
    /home/workspace/atom-federation-os/federation/semantic/test_v910.py:212:        """Canonical cycle: gossip delta -> consensus decision -> proof -> bind all."""
    ```

### INFERRED #references-16
- **Source:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:LL128 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failureisolator_cascade_check`
- **Target:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:L41 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_incident`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:10:  - FailureRecord: record + serialize/deserialize incident traces
    ```
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:41:    """Immutable trace of a single failure incident."""
    ```
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:434:        """Capture a failure incident trace."""
    ```

### INFERRED #references-17
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL44 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint_evaluate`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L44 :: asurdev_astrofin_constraint_compiler_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:12:  i.e., once past S1, nonce is locked before any gate runs
    ```

### INFERRED #references-18
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL133 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_all`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L75 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/models.py:3:FIXED (audit 15.05.2026): Validates all inputs BEFORE they reach the orchestrator.
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_enforcement_layer.py:19:    '''Reset all singletons before each test.'''
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_enforcement_layer.py:331:        '''Gateway logs all operations.'''
    ```

### INFERRED #references-19
- **Source:** `AsurDev/ai_scheduler/scheduler_v2.py:LL45 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_schedule`
- **Target:** `AsurDev/ai_scheduler/scheduler_v2.py:L20 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_schedulerequest`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/test_deterministic_scheduler.py:38:    """schedule() with PRIORITY_ORDER is deterministic across multiple calls."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/test_deterministic_scheduler.py:46:    # Run schedule 5 times at tick=42 — should always return same result
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/test_deterministic_scheduler.py:49:        r = scheduler.schedule(tick=42, strategy=SchedulingStrategy.PRIORITY_ORDER)
    ```

### INFERRED #references-20
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL249 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_decide`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L36 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionsignal`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/resilience/tests/test_resilience_v66.py:137:        decision1 = lattice.decide(state)
    ```
    ```
    /home/workspace/atom-federation-os/resilience/tests/test_resilience_v66.py:138:        decision2 = lattice.decide(state)
    ```
    ```
    /home/workspace/atom-federation-os/resilience/tests/test_resilience_v66.py:139:        decision3 = lattice.decide(state)
    ```

### INFERRED #references-21
- **Source:** `AsurDev/ete/store/trace_store.py:LL63 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace_add_node`
- **Target:** `AsurDev/ete/store/trace_store.py:L25 :: asurdev_ete_store_trace_store_py_store_trace_store_tracenode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/rpc/mesh.py:35:    Each NodeMesh instance is owned by one local node.
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:8:Layout (per node):
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:139:        Called by the local node's event loop.
    ```

### INFERRED #references-22
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL38 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_register_role`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L24 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capabilityset`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/self_model.py:54:    role: NodeRole
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/self_model.py:68:      - node_roles: current role of each node
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/self_model.py:367:                    role = self._state.node_roles.get(dep, NodeRole.UNKNOWN)
    ```

### INFERRED #references-23
- **Source:** `AsurDev/job_engine/engine.py:LL194 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_on_state_change`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/dashboard/projection_engine.py:137:                   "payload": {"job_id": "job-001", "tenant_id": "acme",
    ```
    ```
    /home/workspace/roma-execution-bridge/dashboard/projection_engine.py:164:    print("\n=== Job Forensic (job-001) ===")
    ```
    ```
    /home/workspace/roma-execution-bridge/dashboard/projection_engine.py:165:    jp = pe.project_job("job-001")
    ```

### INFERRED #references-24
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL229 :: monitoring_health_endpoints_system_metrics`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-25
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL52 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L52 :: asurdev_execution_sandbox_sandbox_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/formal_model/execution_equivalence/ledger_normalizer.py:38:    Convert any ledger entry to NormalizedLedgerEntry.
    ```

### INFERRED #references-26
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL81 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_policyblock_all_constraints`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L31 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:81:    Anti-monopoly constraint:
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/proof/invariant_registry.py:13:    SAFETY = "safety"          # never violated (hard constraint)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/proof/invariant_registry.py:14:    LIVENESS = "liveness"      # eventually holds (soft constraint)
    ```

### INFERRED #references-27
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL100 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_parse_text`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L84 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyblock`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:13:    from rich.text import Text
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:126:            text = py_path.read_text(errors="ignore")
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:131:            tree = ast.parse(text, filename=str(py_path))
    ```

### INFERRED #references-28
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL180 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_summary`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L28 :: asurdev_constraint_compiler_parser_parser_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:12:  i.e., once past S1, nonce is locked before any gate runs
    ```

### INFERRED #references-29
- **Source:** `AsurDev/ete/store/trace_store.py:LL117 :: asurdev_ete_store_trace_store_py_store_trace_store_tracestore_get_trace`
- **Target:** `AsurDev/ete/store/trace_store.py:L48 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/tracing.py:4:from opentelemetry import trace
    ```
    ```
    /home/workspace/orchestration/tracing.py:7:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/orchestration/tracing.py:8:from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    ```

### INFERRED #references-30
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL79 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute_batch`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L52 :: asurdev_execution_sandbox_sandbox_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:17:# Configure deterministic primitives before any imports
    ```

### INFERRED #references-31
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL115 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_create_from_state_store`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L49 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/replicated_event_store.py:49:    store = ReplicatedEventStore(3)
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/replicated_event_store.py:51:        r = store.write({"type": f"event-{i}", "tick": i})
    ```
    ```
    /home/workspace/roma-execution-bridge/ha/replicated_event_store.py:53:    print(store.get_state())
    ```

### INFERRED #references-32
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL226 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_classify`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L15 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_fixtype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/v8/incident/model.py:66:        """Factory: create + classify + route incident."""
    ```
    ```
    /home/workspace/AsurDev/v8/incident/model.py:71:        # Auto-classify severity
    ```
    ```
    /home/workspace/AsurDev/governance.py:38:def classify(fp):
    ```

### INFERRED #references-33
- **Source:** `AsurDev/job_engine/engine.py:LL169 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_write_event`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/resilience/adaptive_router.py:157:              (but NOT evicted from cluster — that's the healer's job)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/adaptive_router.py:157:              (but NOT evicted from cluster — that's the healer's job)
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/jobs.py:10:    job = _job_store.get(job_id)
    ```

### INFERRED #references-34
- **Source:** `AsurDev/acos/validators/engine_v6.py:LL23 :: asurdev_acos_validators_engine_v6_py_validators_engine_v6_eventsourcedengine_init`
- **Target:** `AsurDev/acos/validators/engine_v6.py:L23 :: asurdev_acos_validators_engine_v6_py_deterministictracerecorder`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/core/runtime/runtime_guard.py:16:    RuntimeExecutionGuard.assert_not_in_module_import() # called at module init
    ```
    ```
    /home/workspace/atom-federation-os/core/runtime/runtime_guard.py:135:        # Scan entry points once on init
    ```
    ```
    /home/workspace/atom-federation-os/core/runtime/execution_context.py:102:        self._async_lock = None  # Lazy init for async support
    ```

### INFERRED #references-35
- **Source:** `AsurDev/feature_pipeline/features.py:LL13 :: asurdev_feature_pipeline_features_py_feature_pipeline_features_feature_init`
- **Target:** `AsurDev/feature_pipeline/features.py:L13 :: asurdev_feature_pipeline_features_py_featurefunc`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```

### INFERRED #references-36
- **Source:** `AsurDev/determinism_controller/controller.py:LL58 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_compute_state_hash`
- **Target:** `AsurDev/determinism_controller/controller.py:L47 :: asurdev_determinism_controller_controller_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/conftest.py:7:#   1. Mock atomos modules at the earliest possible moment (before any imports)
    ```

### INFERRED #references-37
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL106 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator_validate_trace`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L46 :: asurdev_acos_validator_contract_validator_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/connector.py:85:                "gpu": job.get("gpu", "any"),
    ```

### INFERRED #references-38
- **Source:** `AsurDev/hash_chain/chain.py:LL48 :: asurdev_hash_chain_chain_py_hash_chain_chain_compute_deterministic_hash`
- **Target:** `AsurDev/hash_chain/chain.py:L19 :: asurdev_hash_chain_chain_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:66:            is_entry = any(
    ```

### INFERRED #references-39
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL249 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_decide`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L47 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctiondecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/cost/gate.py:68:    def decide(self, task: str, plugin_type: str = "default",
    ```
    ```
    /home/workspace/roma-execution-bridge/roma_cli.py:108:        decision = self.gate.decide(
    ```
    ```
    /home/workspace/roma-execution-bridge/scheduler/gpu_scheduler.py:9:    Uses VRAM tracking to decide which job gets the GPU.
    ```

### INFERRED #references-40
- **Source:** `AsurDev/acos/state/reducer.py:LL27 :: asurdev_acos_state_reducer_py_state_reducer_statereducer_reduce`
- **Target:** `AsurDev/acos/state/reducer.py:L7 :: asurdev_acos_state_reducer_py_state_reducer_executionstate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:294:    assert r6.new_trust < 0.70, f"Decay should reduce high trust, got {r6.new_trust}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/temporal_gain_scheduler.py:25:    Unstable window → decrease gain budget (reduce exposure to bad decisions)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/temporal_gain_scheduler.py:26:    Drifting source → reduce that specific source's gain
    ```

### INFERRED #references-41
- **Source:** `AsurDev/dag_validator/validator.py:LL51 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L51 :: asurdev_dag_validator_validator_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/router.py:97:    has_electional = any(kw in query_lower for kw in electional_keywords)
    ```
    ```
    /home/workspace/orchestration/router.py:98:    has_technical = any(kw in query_lower for kw in technical_keywords)
    ```
    ```
    /home/workspace/atom-federation-os/rpc/test_rpc.py:223:        assert any(m.payload == b"direct" for m in received[1])
    ```

### INFERRED #references-42
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL103 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_add_constraint`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L31 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:81:    Anti-monopoly constraint:
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/proof/invariant_registry.py:13:    SAFETY = "safety"          # never violated (hard constraint)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/proof/invariant_registry.py:14:    LIVENESS = "liveness"      # eventually holds (soft constraint)
    ```

### INFERRED #references-43
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL33 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_init`
- **Target:** `AsurDev/l10_self_healing/watchdog/watchdog.py:L33 :: asurdev_l10_self_healing_watchdog_watchdog_py_failureisolator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:78:    def init(self) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_orchestration_v75.py:156:        # re-init clears
    ```

### INFERRED #references-44
- **Source:** `AsurDev/admission_controller/controller.py:LL42 :: asurdev_admission_controller_controller_py_admission_controller_controller_admissioncontroller_admit`
- **Target:** `AsurDev/admission_controller/controller.py:L26 :: asurdev_admission_controller_controller_py_admission_controller_controller_admitresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/consistency/global_state_model.py:169:        Returns (admit: bool, reason: str)
    ```
    ```
    /home/workspace/roma-execution-bridge/consistency/backpressure.py:83:        Returns (admit: bool, reason: str)
    ```
    ```
    /home/workspace/home-cluster-iac/tests/unit/test_determinism.py:111:    result = controller.admit(
    ```

### INFERRED #references-45
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL292 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_governance_approval`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L47 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctiondecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/policy_sync.py:54:    """Applies remote θ only after local ReplayValidator approval."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/federation/policy_sync.py:54:    """Applies remote θ only after local ReplayValidator approval."""
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:306:            approved=False,  # Needs governance approval
    ```

### INFERRED #references-46
- **Source:** `AsurDev/l9_ebl/policy_compiler/compiler.py:LL42 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_guardrule_validate`
- **Target:** `AsurDev/l9_ebl/policy_compiler/compiler.py:L17 :: asurdev_l9_ebl_policy_compiler_compiler_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/test_rpc.py:223:        assert any(m.payload == b"direct" for m in received[1])
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:12:  i.e., once past S1, nonce is locked before any gate runs
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:48:        # Block at any gate -> REJECT
    ```

### INFERRED #references-47
- **Source:** `AsurDev/l9_ebl/gate/gate.py:LL90 :: asurdev_l9_ebl_gate_gate_py_gate_gate_executiongate_log_decision`
- **Target:** `AsurDev/l9_ebl/gate/gate.py:L22 :: asurdev_l9_ebl_gate_gate_py_gate_gate_gatedecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/core/federation/federated_gateway.py:206:        decision = self._consensus.get_decision()
    ```
    ```
    /home/workspace/atom-federation-os/core/federation/federated_gateway.py:208:        if decision is None:
    ```
    ```
    /home/workspace/atom-federation-os/core/federation/federated_gateway.py:218:        outcome, all_votes = decision
    ```

### INFERRED #references-48
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL173 :: monitoring_health_endpoints_karl_metrics`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-49
- **Source:** `AsurDev/job_engine/engine.py:LL145 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get_jobs_by_state`
- **Target:** `AsurDev/job_engine/engine.py:L20 :: asurdev_job_engine_engine_py_job_engine_engine_jobstate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:81:async def run_technical_flow(state: dict, selected_agents: list | None = None) -> dict:
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:85:        tasks.append(run_market_analyst(state))
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:88:        tasks.append(run_bull_researcher(state))
    ```

### INFERRED #references-50
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL98 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_check`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L11 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/durability/event_store.py:58:    Append-only event store with replay capability.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/persistence/stateful_recovery.py:348:      - Full checkpoint/restore capability
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/core/deterministic.py:466:    Immutable capability token for mutation authorization.
    ```

---

## Bucket: relation = `contains` (50 edges)

### INFERRED #contains-1
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL15 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L15 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testrouter`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #contains-2
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL51 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L51 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_dual_mode_detection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #contains-3
- **Source:** `AstroFinSentinelV5/tests/test_auth_middleware.py:LL14 :: tests_test_auth_middleware`
- **Target:** `AstroFinSentinelV5/tests/test_auth_middleware.py:L14 :: tests_test_auth_middleware_test_protected_endpoint_requires_auth`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth_middleware.py
    ```

### INFERRED #contains-4
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL22 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L22 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_validator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #contains-5
- **Source:** `AstroFinSentinelV5/tests/test_backtest_mode_comparison.py:LL13 :: astrofinsentinelv5_tests_test_backtest_mode_comparison_py_tests_test_backtest_mode_comparison`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_mode_comparison.py:L13 :: astrofinsentinelv5_tests_test_backtest_mode_comparison_py_tests_test_backtest_mode_comparison_test_comparison_script_ci_mode_succeeds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_mode_comparison.py
    ```

### INFERRED #contains-6
- **Source:** `AstroFinSentinelV5/tests/test_metrics_endpoint.py:LL8 :: astrofinsentinelv5_tests_test_metrics_endpoint_py_tests_test_metrics_endpoint`
- **Target:** `AstroFinSentinelV5/tests/test_metrics_endpoint.py:L8 :: astrofinsentinelv5_tests_test_metrics_endpoint_py_tests_test_metrics_endpoint_test_metrics_server_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_metrics_endpoint.py
    ```

### INFERRED #contains-7
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL147 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L147 :: monitoring_health_endpoints_ab_compare`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-8
- **Source:** `AstroFinSentinelV5/tests/test_observability_ollama.py:LL7 :: astrofinsentinelv5_tests_test_observability_ollama_py_tests_test_observability_ollama`
- **Target:** `AstroFinSentinelV5/tests/test_observability_ollama.py:L7 :: astrofinsentinelv5_tests_test_observability_ollama_py_tests_test_observability_ollama_test_ollama_available_sets_status_to_one`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_observability_ollama.py
    ```

### INFERRED #contains-9
- **Source:** `AstroFinSentinelV5/tests/test_auth.py:LL25 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth`
- **Target:** `AstroFinSentinelV5/tests/test_auth.py:L25 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth_test_public_health_returns_200`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth.py
    ```

### INFERRED #contains-10
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL83 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L83 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #contains-11
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL33 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L33 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_masfactory_fallback_on_error`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #contains-12
- **Source:** `AstroFinSentinelV5/tests/conftest.py:LL8 :: astrofinsentinelv5_tests_conftest_py_tests_conftest`
- **Target:** `AstroFinSentinelV5/tests/conftest.py:L8 :: tests_conftest_flask_app`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/conftest.py
    ```

### INFERRED #contains-13
- **Source:** `AstroFinSentinelV5/tests/test_http_client.py:LL40 :: astrofinsentinelv5_tests_test_http_client_py_tests_test_http_client`
- **Target:** `AstroFinSentinelV5/tests/test_http_client.py:L40 :: astrofinsentinelv5_tests_test_http_client_py_tests_test_http_client_test_retry_on_5xx`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_http_client.py
    ```

### INFERRED #contains-14
- **Source:** `AstroFinSentinelV5/tests/test_auth_middleware.py:LL27 :: tests_test_auth_middleware`
- **Target:** `AstroFinSentinelV5/tests/test_auth_middleware.py:L27 :: tests_test_auth_middleware_test_protected_endpoint_accepts_valid_key`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth_middleware.py
    ```

### INFERRED #contains-15
- **Source:** `AstroFinSentinelV5/web/app.py:LL62 :: astrofinsentinelv5_web_app_py_web_app`
- **Target:** `AstroFinSentinelV5/web/app.py:L62 :: astrofinsentinelv5_web_app_py_web_app_engineref`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/app.py
    ```

### INFERRED #contains-16
- **Source:** `AstroFinSentinelV5/tests/test_switch_nodes.py:LL135 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes`
- **Target:** `AstroFinSentinelV5/tests/test_switch_nodes.py:L135 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes_test_oos_fail_tightens_policy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_switch_nodes.py
    ```

### INFERRED #contains-17
- **Source:** `AstroFinSentinelV5/tests/test_update_progress.py:LL29 :: astrofinsentinelv5_tests_test_update_progress_py_tests_test_update_progress`
- **Target:** `AstroFinSentinelV5/tests/test_update_progress.py:L29 :: astrofinsentinelv5_tests_test_update_progress_py_tests_test_update_progress_test_update_progress_script_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_update_progress.py
    ```

### INFERRED #contains-18
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL23 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L23 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_mock_karl_dependencies`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #contains-19
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL60 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L60 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_both_modes_return_same_structure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #contains-20
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL87 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L87 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolatilitytargeting`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #contains-21
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL49 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L49 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #contains-22
- **Source:** `AstroFinSentinelV5/tests/e2e/test_api_endpoints.py:LL10 :: astrofinsentinelv5_tests_e2e_test_api_endpoints_py_e2e_test_api_endpoints`
- **Target:** `AstroFinSentinelV5/tests/e2e/test_api_endpoints.py:L10 :: e2e_test_api_endpoints_test_health_endpoint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/e2e/test_api_endpoints.py
    ```

### INFERRED #contains-23
- **Source:** `AstroFinSentinelV5/tests/test_auth_middleware.py:LL20 :: tests_test_auth_middleware`
- **Target:** `AstroFinSentinelV5/tests/test_auth_middleware.py:L20 :: tests_test_auth_middleware_test_protected_endpoint_rejects_wrong_key`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth_middleware.py
    ```

### INFERRED #contains-24
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL246 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L246 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_ml_predictor_agent_called_in_real_mode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #contains-25
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL27 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L27 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_tmp_agent_dir`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #contains-26
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL128 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L128 :: monitoring_health_endpoints_metrics_endpoint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-27
- **Source:** `AstroFinSentinelV5/tests/test_observability_rag_quality.py:LL11 :: astrofinsentinelv5_tests_test_observability_rag_quality_py_tests_test_observability_rag_quality`
- **Target:** `AstroFinSentinelV5/tests/test_observability_rag_quality.py:L11 :: astrofinsentinelv5_tests_test_observability_rag_quality_py_tests_test_observability_rag_quality_test_rag_query_cache_hits_increment`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_observability_rag_quality.py
    ```

### INFERRED #contains-28
- **Source:** `AstroFinSentinelV5/tests/test_switch_nodes.py:LL269 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes`
- **Target:** `AstroFinSentinelV5/tests/test_switch_nodes.py:L269 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_switch_nodes.py
    ```

### INFERRED #contains-29
- **Source:** `AstroFinSentinelV5/tests/test_auth_middleware.py:LL8 :: tests_test_auth_middleware`
- **Target:** `AstroFinSentinelV5/tests/test_auth_middleware.py:L8 :: tests_test_auth_middleware_client`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth_middleware.py
    ```

### INFERRED #contains-30
- **Source:** `AstroFinSentinelV5/tests/test_http_client.py:LL8 :: astrofinsentinelv5_tests_test_http_client_py_tests_test_http_client`
- **Target:** `AstroFinSentinelV5/tests/test_http_client.py:L8 :: astrofinsentinelv5_tests_test_http_client_py_tests_test_http_client_reset_client`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_http_client.py
    ```

### INFERRED #contains-31
- **Source:** `AstroFinSentinelV5/tests/test_update_progress.py:LL33 :: astrofinsentinelv5_tests_test_update_progress_py_tests_test_update_progress`
- **Target:** `AstroFinSentinelV5/tests/test_update_progress.py:L33 :: astrofinsentinelv5_tests_test_update_progress_py_tests_test_update_progress_test_generates_progress_file`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_update_progress.py
    ```

### INFERRED #contains-32
- **Source:** `AstroFinSentinelV5/tests/test_rate_limit.py:LL13 :: astrofinsentinelv5_tests_test_rate_limit_py_tests_test_rate_limit`
- **Target:** `AstroFinSentinelV5/tests/test_rate_limit.py:L13 :: astrofinsentinelv5_tests_test_rate_limit_py_tests_test_rate_limit_test_rate_limit_too_many_requests`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rate_limit.py
    ```

### INFERRED #contains-33
- **Source:** `AstroFinSentinelV5/tests/test_switch_nodes.py:LL22 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes`
- **Target:** `AstroFinSentinelV5/tests/test_switch_nodes.py:L22 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes_test_uncertainty_switch_adds_grounding`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_switch_nodes.py
    ```

### INFERRED #contains-34
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL276 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L276 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #contains-35
- **Source:** `AstroFinSentinelV5/tests/test_cache.py:LL23 :: astrofinsentinelv5_tests_test_cache_py_tests_test_cache`
- **Target:** `AstroFinSentinelV5/tests/test_cache.py:L23 :: astrofinsentinelv5_tests_test_cache_py_tests_test_cache_test_get_missing_key`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_cache.py
    ```

### INFERRED #contains-36
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #contains-37
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL187 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L187 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testsafetydisabled`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #contains-38
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL229 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L229 :: monitoring_health_endpoints_system_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-39
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL67 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L67 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_agent_with_mocks`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #contains-40
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL112 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L112 :: monitoring_health_endpoints_readiness_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-41
- **Source:** `AstroFinSentinelV5/tests/test_observability_rag_quality.py:LL7 :: astrofinsentinelv5_tests_test_observability_rag_quality_py_tests_test_observability_rag_quality`
- **Target:** `AstroFinSentinelV5/tests/test_observability_rag_quality.py:L7 :: astrofinsentinelv5_tests_test_observability_rag_quality_py_tests_test_observability_rag_quality_test_rag_retrieve_updates_quality_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_observability_rag_quality.py
    ```

### INFERRED #contains-42
- **Source:** `AstroFinSentinelV5/tests/test_cache.py:LL9 :: astrofinsentinelv5_tests_test_cache_py_tests_test_cache`
- **Target:** `AstroFinSentinelV5/tests/test_cache.py:L9 :: astrofinsentinelv5_tests_test_cache_py_tests_test_cache_cache`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_cache.py
    ```

### INFERRED #contains-43
- **Source:** `AstroFinSentinelV5/tests/test_orchestrator.py:LL96 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator`
- **Target:** `AstroFinSentinelV5/tests/test_orchestrator.py:L96 :: astrofinsentinelv5_tests_test_orchestrator_py_tests_test_orchestrator_testorchestratorintegration`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_orchestrator.py
    ```

### INFERRED #contains-44
- **Source:** `AstroFinSentinelV5/tests/test_phase1_cleanup.py:LL4 :: astrofinsentinelv5_tests_test_phase1_cleanup_py_tests_test_phase1_cleanup`
- **Target:** `AstroFinSentinelV5/tests/test_phase1_cleanup.py:L4 :: astrofinsentinelv5_tests_test_phase1_cleanup_py_tests_test_phase1_cleanup_test_core_auth_importable`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_phase1_cleanup.py
    ```

### INFERRED #contains-45
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL66 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L66 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_ollama_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #contains-46
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL115 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L115 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_backward_compatibility_signatures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #contains-47
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL31 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L31 :: monitoring_health_endpoints_healthresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-48
- **Source:** `AstroFinSentinelV5/tests/test_auth.py:LL20 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth`
- **Target:** `AstroFinSentinelV5/tests/test_auth.py:L20 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth_test_flask_unauthenticated_returns_401`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth.py
    ```

### INFERRED #contains-49
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL76 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L76 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_handle_missing_docker_compose`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #contains-50
- **Source:** `AstroFinSentinelV5/tests/test_switch_nodes.py:LL80 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes`
- **Target:** `AstroFinSentinelV5/tests/test_switch_nodes.py:L80 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes_test_bias_switch_adds_critic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_switch_nodes.py
    ```

---

## Bucket: relation = `imports_from` (50 edges)

### INFERRED #imports_from-1
- **Source:** `atom-federation-os/sbs/cli_replay.py:LL11 :: atom_federation_os_sbs_cli_replay_py_sbs_cli_replay`
- **Target:** `atom-federation-os/alignment/adlr.py:L1 :: alignment_adlr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:1:"""adlr.py — v10.5 Anti-Deadlock Liveness Recovery Layer.
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_adlr.py:5:from alignment.adlr import ADLRecoveryOrchestrator, OscillationMonitor, OscillationStage, RecoveryAction, RecoveryPolicy
    ```
    ```
    /home/workspace/atom-federation-os/alignment/failure_replay.py:349:        from alignment.adlr import RecoveryPolicy
    ```

### INFERRED #imports_from-2
- **Source:** `atom-federation-os/alignment/plan_reality_comparator.py:LL27 :: alignment_plan_reality_comparator`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:5:Builds a deterministic DAG of all execution entry points and their call-sites,
    ```
    ```
    /home/workspace/atom-federation-os/scripts/ast_snapshot.py:7:serialized to produce a deterministic SHA256 hash.
    ```
    ```
    /home/workspace/atom-federation-os/scripts/environment_hash.py:42:    """Get deterministic pip freeze output."""
    ```

### INFERRED #imports_from-3
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL11 :: consistency_test_cross_layer_invariant_engine`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L1 :: consistency_cross_layer_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:66:    A decision made by the policy engine.
    ```
    ```
    /home/workspace/atom-federation-os/actuator/divergence_response_policy.py:81:    Threshold-driven policy engine for swarm divergence response.
    ```
    ```
    /home/workspace/atom-federation-os/actuator/causal_actuation_engine.py:87:    Core engine that translates divergence field measurements
    ```

### INFERRED #imports_from-4
- **Source:** `atom-federation-os/chaos/__init__.py:LL22 :: chaos_init`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L1 :: sbs_global_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/web/callbacks.py:352:            engine = EvolutionEngine(
    ```
    ```
    /home/workspace/web/callbacks.py:360:            get_engine_ref._engine = engine
    ```
    ```
    /home/workspace/web/callbacks.py:416:        engine = getattr(get_engine_ref, "_engine", None)
    ```

### INFERRED #imports_from-5
- **Source:** `atom-federation-os/persistence/stateful_recovery.py:LL11 :: persistence_stateful_recovery`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:5:Builds a deterministic DAG of all execution entry points and their call-sites,
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:6:# CRD state = projection from event log. Replay = deterministic rebuild.
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:69:    tick: int              # global monotonic tick (deterministic clock)
    ```

### INFERRED #imports_from-6
- **Source:** `atom-federation-os/chaos/__init__.py:LL18 :: chaos_init`
- **Target:** `atom-federation-os/chaos/scenarios.py:L1 :: chaos_scenarios`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/failure_replay/event_store.py:11:  - SQLite (default, for single node or replay scenarios)
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:338:    """Runs a suite of federation scenarios and produces a report."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:357:        scenarios = [
    ```

### INFERRED #imports_from-7
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/durable_queue.py:LL35 :: agent_runtime_durable_queue`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:L1 :: agent_runtime_task_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:136:        store = StateWindowStore(db_path=str(db_path))
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:142:        store.close()
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:152:        store = StateWindowStore(db_path=str(db_path), gateway=gateway)
    ```

### INFERRED #imports_from-8
- **Source:** `atom-federation-os/orchestration/mutation_executor.py:LL38 :: orchestration_mutation_executor`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:51:    We verify the gateway code CONSISTENCY with the DFA spec:
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:87:    # P6 federated gateway — has its own DFA but delegates through ExecutionGateway
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:103:    # apply_mutation in mutation_executor is PERMITTED (internal gateway wrapper)
    ```

### INFERRED #imports_from-9
- **Source:** `atom-federation-os/meta_control/integration/persistence_bridge.py:LL24 :: integration_persistence_bridge`
- **Target:** `atom-federation-os/meta_control/temporal_gain_scheduler.py:L1 :: meta_control_temporal_gain_scheduler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:32:from .scheduler import AdaptiveScheduler
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:306:    Replaces Redis Stream consumer group pattern with sorted-set scheduler.
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:309:    scheduler = await get_scheduler()
    ```

### INFERRED #imports_from-10
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_store.py:LL14 :: agent_runtime_event_store`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:L1 :: agent_runtime_event_sourcing`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/adapters.py:30:    event log compatible with DESC event-sourcing layer.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/adapters.py:241:        Map DESC event-sourcing state → SBS canonical state.
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/state_store.py:2:ROMA State Store — Current state management with event sourcing.
    ```

### INFERRED #imports_from-11
- **Source:** `atom-federation-os/actuator/__init__.py:LL22 :: actuator_init`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L1 :: actuator_stability_feedback_controller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/kubernetes/atom_operator/main.py:4:Loads kubeconfig, starts controller, handles signals.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/kubernetes/atom_operator/main.py:17:from .controller import ATOMController
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/kubernetes/atom_operator/main.py:50:    controller = ATOMController(k8s, poll_interval=poll_interval)
    ```

### INFERRED #imports_from-12
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL35 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/federation/consensus.py:L1 :: federation_consensus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:115:    """Phase 2: proof-weighted consensus ranking."""
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:296:    """Full v9.3 pipeline: gossip → policy_sync → consensus."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:5:  Phase 2: consensus weighted by proof_valid + stability + drift
    ```

### INFERRED #imports_from-13
- **Source:** `atom-federation-os/chaos/__init__.py:LL21 :: chaos_init`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/k8s/roma_controller.py:45:    spec = romatask.get("spec", {})
    ```
    ```
    /home/workspace/roma-execution-bridge/k8s/roma_controller.py:46:    task = spec.get("task", "")
    ```
    ```
    /home/workspace/roma-execution-bridge/k8s/roma_controller.py:47:    gpu_required = spec.get("gpuRequired", False)
    ```

### INFERRED #imports_from-14
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:LL16 :: agent_runtime_event_sourcing`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-15
- **Source:** `atom-federation-os/federation/bootstrap/node_runtime.py:LL30 :: bootstrap_node_runtime`
- **Target:** `atom-federation-os/federation/gossip_protocol.py:L1 :: federation_gossip_protocol`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/main.py:91:                "protocol": "rom",
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:25:from federation.delta_gossip.protocol import DeltaGossipMessage
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:25:  - DeltaGossipMessage (protocol.py) — proof_hash, proof_origin, proof_valid
    ```

### INFERRED #imports_from-16
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL11 :: resilience_meta_coherence_controller`
- **Target:** `atom-federation-os/coherence/objective_stabilizer.py:L1 :: coherence_objective_stabilizer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:358:    stabilizer = TrustDynamicsStabilizer(
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:368:    report = stabilizer.stabilize(
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:414:    report3 = stabilizer.stabilize(
    ```

### INFERRED #imports_from-17
- **Source:** `atom-federation-os/chaos/test_replay_validator.py:LL7 :: chaos_test_replay_validator`
- **Target:** `atom-federation-os/chaos/replay_validator.py:L1 :: chaos_replay_validator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/models.py:9:from pydantic import BaseModel, Field, validator
    ```
    ```
    /home/workspace/orchestration/models.py:42:    @validator("user_query")
    ```
    ```
    /home/workspace/orchestration/models.py:49:    @validator("symbol")
    ```

### INFERRED #imports_from-18
- **Source:** `atom-federation-os/federation/policy_sync.py:LL22 :: federation_policy_sync`
- **Target:** `atom-federation-os/federation/consensus_resolver.py:L1 :: federation_consensus_resolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:118:        resolver = ProofAwareConsensusResolver(node_id="node_A")
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:129:        winner = resolver.rank_candidates([c1, c2])
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:134:        resolver = ProofAwareConsensusResolver(node_id="node_A")
    ```

### INFERRED #imports_from-19
- **Source:** `atom-federation-os/alignment/gcst.py:LL11 :: alignment_gcst`
- **Target:** `atom-federation-os/alignment/bcil.py:L1 :: alignment_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/gcst.py:11:from alignment.bcil import BCIL
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gcst.py:37:        self.bcil = BCIL()
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_bcil.py:5:from alignment.bcil import BCIL, ByzantineConvergenceFunction, ByzantineFailureType, QuorumSpec
    ```

### INFERRED #imports_from-20
- **Source:** `_sbs_old/global_invariant_engine.py:LL22 :: sbs_old_global_invariant_engine`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/observability/core/atom_metrics.py:85:        spec = METRICS_SCHEMA.get(name)
    ```
    ```
    /home/workspace/atom-federation-os/observability/core/atom_metrics.py:86:        return spec.get("type") if spec else None
    ```
    ```
    /home/workspace/atom-federation-os/observability/core/atom_metrics.py:118:            spec = METRICS_SCHEMA.get(name, {})
    ```

### INFERRED #imports_from-21
- **Source:** `atom-federation-os/core/federation/quorum_certificate.py:LL16 :: federation_quorum_certificate`
- **Target:** `atom-federation-os/core/federation/consensus.py:L1 :: federation_consensus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:5:  Phase 2: consensus weighted by proof_valid + stability + drift
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_consensus_resolver.py:35:        """2/3 consensus → quorum source."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_policy_sync.py:81:        consensus = make_consensus("h_remote")
    ```

### INFERRED #imports_from-22
- **Source:** `atom-federation-os/orchestration/__init__.py:LL10 :: atom_federation_os_orchestration_init_py_orchestration_init`
- **Target:** `atom-federation-os/orchestration/system_wide_gain_scheduler.py:L1 :: orchestration_system_wide_gain_scheduler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/gossip_protocol.py:70:    # manual sync (called by external scheduler)                         #
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/consistency_v3/explainable_divergence_engine.py:139:            "delta-rate divergence": "Investigate transition rate limits; check scheduler fairness.",
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/integration/persistence_bridge.py:49:        scheduler: TemporalGainScheduler,
    ```

### INFERRED #imports_from-23
- **Source:** `atom-federation-os/alignment/rollback_engine_v2.py:LL26 :: alignment_rollback_engine_v2`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/otl.py:7:from core.deterministic import DeterministicClock
    ```
    ```
    /home/workspace/atom-federation-os/alignment/otl.py:47:        self._tick = 0  # track tick for deterministic RNG
    ```
    ```
    /home/workspace/atom-federation-os/alignment/otl.py:50:        # Advance tick for deterministic noise (ATOM-META-RL-021)
    ```

### INFERRED #imports_from-24
- **Source:** `atom-federation-os/orchestration/__init__.py:LL7 :: atom_federation_os_orchestration_init_py_orchestration_init`
- **Target:** `atom-federation-os/orchestration/conflict_resolution_matrix.py:L1 :: orchestration_conflict_resolution_matrix`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_consensus.py:35:    - ProofOrigin priority matrix
    ```
    ```
    /home/workspace/atom-federation-os/alignment/merge_engine.py:16:Conflict resolution matrix:
    ```
    ```
    /home/workspace/atom-federation-os/alignment/merge_engine.py:202:            - If event exists in both branches → conflict → resolve via matrix
    ```

### INFERRED #imports_from-25
- **Source:** `atom-federation-os/federation/bootstrap/cluster_simulator.py:LL20 :: bootstrap_cluster_simulator`
- **Target:** `atom-federation-os/federation/gossip_protocol.py:L1 :: federation_gossip_protocol`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:25:from federation.delta_gossip.protocol import DeltaGossipMessage
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:25:  - DeltaGossipMessage (protocol.py) — proof_hash, proof_origin, proof_valid
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_enriched_gossip.py:314:    Documentation of schema change needed in DeltaGossipMessage (protocol.py).
    ```

### INFERRED #imports_from-26
- **Source:** `atom-federation-os/tests/test_operator_reconciler.py:LL10 :: tests_test_operator_reconciler`
- **Target:** `atom-federation-os/kubernetes/atom_operator/state.py:L1 :: atom_operator_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:81:async def run_technical_flow(state: dict, selected_agents: list | None = None) -> dict:
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:85:        tasks.append(run_market_analyst(state))
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:88:        tasks.append(run_bull_researcher(state))
    ```

### INFERRED #imports_from-27
- **Source:** `atom-federation-os/federation/gossip_protocol.py:LL15 :: federation_gossip_protocol`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:6:# CRD state = projection from event log. Replay = deterministic rebuild.
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:69:    tick: int              # global monotonic tick (deterministic clock)
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:200:        """Replay events from tick N (deterministic iteration)."""
    ```

### INFERRED #imports_from-28
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL30 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/equivalence.py:L1 :: alignment_equivalence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_policy_sync.py:207:            reason = f"Cross-origin equivalence violated: {divergence}"
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_consensus.py:234:        # Verify the candidate's proof by re-running equivalence
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_v9_3_federation_binding.py:11:  2. PolicySync evaluates cross-origin equivalence
    ```

### INFERRED #imports_from-29
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL32 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:6:# CRD state = projection from event log. Replay = deterministic rebuild.
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:69:    tick: int              # global monotonic tick (deterministic clock)
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:200:        """Replay events from tick N (deterministic iteration)."""
    ```

### INFERRED #imports_from-30
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL18 :: chaos_test_chaos`
- **Target:** `atom-federation-os/chaos/harness.py:L1 :: chaos_harness`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/observability/bootstrap.py:9:Minimal one-shot startup for a cluster node or test harness.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/__init__.py:10:harness : Jepsen-style test harness
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/__init__.py:15:from chaos.harness import ChaosHarness, ChaosResult
    ```

### INFERRED #imports_from-31
- **Source:** `atom-federation-os/federation/state_vector.py:LL9 :: federation_state_vector`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:5:Builds a deterministic DAG of all execution entry points and their call-sites,
    ```
    ```
    /home/workspace/atom-federation-os/scripts/ast_snapshot.py:7:serialized to produce a deterministic SHA256 hash.
    ```
    ```
    /home/workspace/atom-federation-os/scripts/environment_hash.py:42:    """Get deterministic pip freeze output."""
    ```

### INFERRED #imports_from-32
- **Source:** `atom-federation-os/federation/gossip_protocol.py:LL16 :: federation_gossip_protocol`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/tests/test_gossip_protocol.py:28:        assert pr.vector is None
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_gossip_protocol.py:90:        assert g._peers["n2"].vector == remote
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_consensus_resolver.py:109:        # Only my fresh vector counts → no quorum → highest_stability
    ```

### INFERRED #imports_from-33
- **Source:** `_sbs_old/runtime.py:LL20 :: sbs_old_runtime`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:7:    DFA(runtime) == DFA(spec)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:85:        spec = load_spec()
    ```
    ```
    /home/workspace/atom-federation-os/scripts/comprehensive_audit.py:87:        delta = compute_delta(spec, runtime)
    ```

### INFERRED #imports_from-34
- **Source:** `atom-federation-os/swarm/causal_merge_protocol.py:LL10 :: swarm_causal_merge_protocol`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:51:    We verify the gateway code CONSISTENCY with the DFA spec:
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:87:    # P6 federated gateway — has its own DFA but delegates through ExecutionGateway
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:103:    # apply_mutation in mutation_executor is PERMITTED (internal gateway wrapper)
    ```

### INFERRED #imports_from-35
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL13 :: alignment_test_alignment`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L1 :: alignment_rollback_engine_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:78:        v2 = rng2.random()
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:79:        assert v1 == v2, f"Same seed produced different values: {v1} != {v2}"
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:89:        v2 = rng2.random()
    ```

### INFERRED #imports_from-36
- **Source:** `atom-federation-os/federation/tests/test_gossip_protocol.py:LL8 :: tests_test_gossip_protocol`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/tests/test_gossip_protocol.py:28:        assert pr.vector is None
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_gossip_protocol.py:90:        assert g._peers["n2"].vector == remote
    ```
    ```
    /home/workspace/atom-federation-os/federation/gossip_protocol.py:33:    vector: StateVector | None = None
    ```

### INFERRED #imports_from-37
- **Source:** `_sbs_old/tests/test_invariants.py:LL20 :: sbs_old_tests_test_invariants_py_tests_test_invariants`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/mcpc.py:137:        for metric_name, spec in CANONICAL_METRICS.items():
    ```
    ```
    /home/workspace/atom-federation-os/alignment/mcpc.py:138:            canonical_formula = spec["formula"]
    ```
    ```
    /home/workspace/atom-federation-os/alignment/mcpc.py:157:        for metric_name, spec in CANONICAL_METRICS.items():
    ```

### INFERRED #imports_from-38
- **Source:** `atom-federation-os/failure_replay/__init__.py:LL26 :: failure_replay_init`
- **Target:** `atom-federation-os/failure_replay/replay_engine.py:L1 :: failure_replay_replay_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/orchestration/consistency/test_cross_origin_proof.py:25:        engine = SemanticProofEngine()
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/consistency/test_cross_origin_proof.py:26:        proof = engine.prove_from_digests(d, d)
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/consistency/test_cross_origin_proof.py:34:        engine = SemanticProofEngine()
    ```

### INFERRED #imports_from-39
- **Source:** `atom-federation-os/core/runtime/determinism_guard.py:LL11 :: runtime_determinism_guard`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/orchestration/chaos/test_observability_integration.py:6:  - ImpactScorer deterministic scoring
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/chaos/test_observability_integration.py:26:    """ImpactScorer: deterministic weighted scoring."""
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/chaos/observability_integration.py:11:  ImpactScorer           — deterministic weighted impact scoring
    ```

### INFERRED #imports_from-40
- **Source:** `atom-federation-os/federation/byzantine/pbft_consensus.py:LL17 :: byzantine_pbft_consensus`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L1 :: byzantine_message_signatures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/security/inbound_security_gate.py:7:  - Verify signatures via FederationMessageSigning (HMAC-SHA256)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_resilience_v65.py:2:Tests for v6.5 resilience modules — matched to actual API signatures.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/observability/core/replay_subscriber.py:32:    Supports three calling signatures (backward compatible):
    ```

### INFERRED #imports_from-41
- **Source:** `atom-federation-os/alignment/branch.py:LL22 :: alignment_branch`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:6:# CRD state = projection from event log. Replay = deterministic rebuild.
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:69:    tick: int              # global monotonic tick (deterministic clock)
    ```
    ```
    /home/workspace/roma-execution-bridge/durability/event_sourcing.py:200:        """Replay events from tick N (deterministic iteration)."""
    ```

### INFERRED #imports_from-42
- **Source:** `atom-federation-os/cluster/node/node.py:LL21 :: node_node`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/plugins/plugin_runtime.py:34:    spec: PluginSpec
    ```
    ```
    /home/workspace/roma-execution-bridge/plugins/plugin_runtime.py:56:        spec = PluginSpec(
    ```
    ```
    /home/workspace/roma-execution-bridge/plugins/plugin_runtime.py:66:        plugin_inst = PluginInstance(spec=spec, plugin_class=plugin_class, instance=instance_obj)
    ```

### INFERRED #imports_from-43
- **Source:** `atom-federation-os/chaos/harness.py:LL19 :: chaos_harness`
- **Target:** `atom-federation-os/chaos/validator.py:L1 :: chaos_validator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/models.py:9:from pydantic import BaseModel, Field, validator
    ```
    ```
    /home/workspace/orchestration/models.py:42:    @validator("user_query")
    ```
    ```
    /home/workspace/orchestration/models.py:49:    @validator("symbol")
    ```

### INFERRED #imports_from-44
- **Source:** `atom-federation-os/meta_control/__init__.py:LL14 :: meta_control_init`
- **Target:** `atom-federation-os/meta_control/temporal_gain_scheduler.py:L1 :: meta_control_temporal_gain_scheduler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/connector.py:2:"""ROMA GPU Connector — Connects ROMA scheduler to GPU workers
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/connector.py:195:# Convenience function for scheduler
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/production_worker.py:204:COPY scheduler/ /app/scheduler/
    ```

### INFERRED #imports_from-45
- **Source:** `atom-federation-os/dag/test_fingerprint.py:LL6 :: dag_test_fingerprint`
- **Target:** `atom-federation-os/dag/fingerprint.py:L1 :: dag_fingerprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/consensus.py:64:    Now quorum is reached on root_hash (DAG fingerprint) alone,
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/consensus.py:125:        # Count by root_hash (quorum on fingerprint, not full state)
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/__init__.py:2:DeltaGossip — O(Δnodes) federation gossip with DAG fingerprint deltas.
    ```

### INFERRED #imports_from-46
- **Source:** `atom-federation-os/failure_replay/__init__.py:LL25 :: failure_replay_init`
- **Target:** `atom-federation-os/failure_replay/event_store.py:L1 :: failure_replay_event_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/anti_entropy.py:74:        # Layer 0: leaves — store mode in each node
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/node_runtime.py:259:        # In simulation, we store theta per node in ClusterSimulator
    ```
    ```
    /home/workspace/atom-federation-os/federation/semantic/v910.py:158:        snapshot start can appear in it, even if store is mutated concurrently.
    ```

### INFERRED #imports_from-47
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL37 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/federation/quorum_certificate.py:L1 :: federation_quorum_certificate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:189:        - certificate = hash(sorted([all_prepare_digests])) → ensures all voters committed to same digest
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:205:            # Prepare certificate: hash of sorted prepare digests for commit binding
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/core/federation/distributed_ledger.py:29:    qc: QuorumCertificate    # quorum certificate for this entry
    ```

### INFERRED #imports_from-48
- **Source:** `atom-federation-os/meta_control/integration/persistence_bridge.py:LL25 :: integration_persistence_bridge`
- **Target:** `atom-federation-os/proof/temporal_verifier.py:L1 :: proof_temporal_verifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/dfa_regression_verifier.py:105:        return True, "P2-internal gateway wrapper (verifier: must assert delegation)"
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:327:        verifier = TemporalVerifier(stability_threshold=0.75, drift_threshold=0.6)
    ```

### INFERRED #imports_from-49
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL36 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/federation/distributed_ledger.py:L1 :: federation_distributed_ledger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas_api/auth.py:7:from billing.ledger import BillingLedger
    ```
    ```
    /home/workspace/atom-federation-os/meta_control/persistence/state_window_store.py:25:    # Append-only ledger with hard durability guarantees
    ```
    ```
    /home/workspace/atom-federation-os/meta_control/persistence/stability_ledger.py:88:        """Get or create a ledger, assigning source name on first creation."""
    ```

### INFERRED #imports_from-50
- **Source:** `atom-federation-os/cluster/node/entrypoint.py:LL17 :: node_entrypoint`
- **Target:** `atom-federation-os/cluster/shared/runtime_bootstrap.py:L1 :: shared_runtime_bootstrap`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_operator_reconciler.py:214:    """Step 5 — Phase 3: Pending → bootstrap creates StatefulSet."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:18:from federation.bootstrap.node_runtime import NodeRuntime
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/observability/bootstrap.py:12:    from observability.bootstrap import start_observability
    ```

---

## Bucket: relation = `rationale_for` (50 edges)

### INFERRED #rationale_for-1
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL203 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_203`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L202 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_test_propagate_unknown_body_raises`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-2
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL226 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_226`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L225 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration_test_position_risk_adjusted_flag_set`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-3
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL148 :: monitoring_health_endpoints_rationale_148`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L147 :: monitoring_health_endpoints_ab_compare`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #rationale_for-4
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL92 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_rationale_92`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L91 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation_test_eccentric_anomaly_convergence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #rationale_for-5
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL343 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_343`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L342 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow_test_confidence_capped_at_bounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-6
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL1 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L1 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #rationale_for-7
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL265 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_265`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L264 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow_test_lag_metrics_in_synth_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-8
- **Source:** `AsurDev/acos/events/event.py:LL58 :: events_event_rationale_58`
- **Target:** `AsurDev/acos/events/event.py:L57 :: asurdev_acos_events_event_py_events_event_event_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:53:def _compute_oap_adjustments(oap_state, agents: list) -> dict:
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:62:        return dict.fromkeys(agents, adjustment)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:81:async def run_technical_flow(state: dict, selected_agents: list | None = None) -> dict:
    ```

### INFERRED #rationale_for-9
- **Source:** `AstroFinSentinelV5/tests/test_observability_belief_cache.py:LL5 :: tests_test_observability_belief_cache_rationale_5`
- **Target:** `AstroFinSentinelV5/tests/test_observability_belief_cache.py:L4 :: astrofinsentinelv5_tests_test_observability_belief_cache_py_tests_test_observability_belief_cache_test_belief_get_cache_increments_counters`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_observability_belief_cache.py
    ```

### INFERRED #rationale_for-10
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL189 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_rationale_189`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L188 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testsafetydisabled_test_disabled_returns_approved`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #rationale_for-11
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL135 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_135`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L134 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_immature_window_flag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-12
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL116 :: tests_test_dual_mode_rationale_116`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L115 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_backward_compatibility_signatures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #rationale_for-13
- **Source:** `AstroFinSentinelV5/web/components/__init__.py:LL1 :: astrofinsentinelv5_web_components_init_py_components_init_rationale_1`
- **Target:** `AstroFinSentinelV5/web/components/__init__.py:L1 :: astrofinsentinelv5_web_components_init_py_components_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/components/__init__.py
    ```

### INFERRED #rationale_for-14
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL163 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_rationale_163`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L162 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testheliocentriclongitude_test_longitude_changes_with_time`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #rationale_for-15
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL62 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_rationale_62`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L61 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/__main__.py:24:    query = " ".join(clean_args) if clean_args else "Analyze BTC"
    ```
    ```
    /home/workspace/orchestration/__main__.py:36:                    user_query=query,
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:492:    parser.add_argument("--query", default="", help="User query")
    ```

### INFERRED #rationale_for-16
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL96 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_rationale_96`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L95 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_macro_agent_called_in_real_mode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #rationale_for-17
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL188 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_188`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L187 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity_test_jupiter_slow_motion`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-18
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL132 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_132`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L131 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_test_mean_anomaly_in_circle`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-19
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL41 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_41`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L40 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_j2000_mean_accuracy_outer_planets`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-20
- **Source:** `AsurDev/acos/events/event.py:LL66 :: events_event_rationale_66`
- **Target:** `AsurDev/acos/events/event.py:L65 :: asurdev_acos_events_event_py_events_event_event_from_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:53:def _compute_oap_adjustments(oap_state, agents: list) -> dict:
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:62:        return dict.fromkeys(agents, adjustment)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:81:async def run_technical_flow(state: dict, selected_agents: list | None = None) -> dict:
    ```

### INFERRED #rationale_for-21
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL86 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_86`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L85 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_no_catastrophic_divergence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-22
- **Source:** `AstroFinSentinelV5/tests/test_phase1_cleanup.py:LL1 :: astrofinsentinelv5_tests_test_phase1_cleanup_py_tests_test_phase1_cleanup_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_phase1_cleanup.py:L1 :: astrofinsentinelv5_tests_test_phase1_cleanup_py_tests_test_phase1_cleanup`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_phase1_cleanup.py
    ```

### INFERRED #rationale_for-23
- **Source:** `AstroFinSentinelV5/tests/test_observability_rag_quality.py:LL12 :: tests_test_observability_rag_quality_rationale_12`
- **Target:** `AstroFinSentinelV5/tests/test_observability_rag_quality.py:L11 :: astrofinsentinelv5_tests_test_observability_rag_quality_py_tests_test_observability_rag_quality_test_rag_query_cache_hits_increment`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_observability_rag_quality.py
    ```

### INFERRED #rationale_for-24
- **Source:** `AsurDev/acos/contracts/scheduler_contract.py:LL5 :: contracts_scheduler_contract_rationale_5`
- **Target:** `AsurDev/acos/contracts/scheduler_contract.py:L4 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_schedulercontract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:57:        entropy = getattr(oap_state, "entropy_avg", 0.5) or 0.5
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:59:        oap_score = 0.5 * entropy + 0.5 * max(0.0, sharpe)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:60:        adjustment = (oap_score - 0.5) * 0.4
    ```

### INFERRED #rationale_for-25
- **Source:** `AstroFinSentinelV5/tests/test_observability_ollama.py:LL8 :: tests_test_observability_ollama_rationale_8`
- **Target:** `AstroFinSentinelV5/tests/test_observability_ollama.py:L7 :: astrofinsentinelv5_tests_test_observability_ollama_py_tests_test_observability_ollama_test_ollama_available_sets_status_to_one`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_observability_ollama.py
    ```

### INFERRED #rationale_for-26
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL78 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_rationale_78`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L77 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskengineintegration_test_reduced_on_high_exposure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #rationale_for-27
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL1 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L1 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-28
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL197 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_197`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L196 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity_test_saturn_retrograde_flag_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-29
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL161 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_161`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L160 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_radius_perihelion_lt_aphelion`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-30
- **Source:** `AstroFinSentinelV5/web/components/live.py:LL1 :: astrofinsentinelv5_web_components_live_py_components_live_rationale_1`
- **Target:** `AstroFinSentinelV5/web/components/live.py:L1 :: astrofinsentinelv5_web_components_live_py_components_live`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/components/live.py
    ```

### INFERRED #rationale_for-31
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL175 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_175`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L174 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-32
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL8 :: tests_test_rag_agent_integration_rationale_8`
- **Target:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:L7 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rag_agent_integration.py
    ```

### INFERRED #rationale_for-33
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL1 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L1 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #rationale_for-34
- **Source:** `AstroFinSentinelV5/web/sessions_callbacks.py:LL1 :: astrofinsentinelv5_web_sessions_callbacks_py_web_sessions_callbacks_rationale_1`
- **Target:** `AstroFinSentinelV5/web/sessions_callbacks.py:L1 :: astrofinsentinelv5_web_sessions_callbacks_py_web_sessions_callbacks`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/sessions_callbacks.py
    ```

### INFERRED #rationale_for-35
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL190 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_190`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L189 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration_test_risk_adjustment_called_when_mature`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-36
- **Source:** `AsurDev/acos/contracts/scheduler_contract.py:LL16 :: contracts_scheduler_contract_rationale_16`
- **Target:** `AsurDev/acos/contracts/scheduler_contract.py:L15 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_validate_scheduler_contract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/orchestration/chaos/test_integration_full_loop.py:285:    Top-level contract: under feedback control, drift decreases across iterations.
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/chaos/test_integration_full_loop.py:370:            f"Closed-loop contract violated: drift must decrease. "
    ```
    ```
    /home/workspace/atom-federation-os/sbs/system_contract.py:64:        Verify a single invariant value against the contract.
    ```

### INFERRED #rationale_for-37
- **Source:** `AstroFinSentinelV5/tests/test_type_consolidation.py:LL7 :: tests_test_type_consolidation_rationale_7`
- **Target:** `AstroFinSentinelV5/tests/test_type_consolidation.py:L6 :: astrofinsentinelv5_tests_test_type_consolidation_py_tests_test_type_consolidation_test_no_duplicate_agent_response_imports`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_type_consolidation.py
    ```

### INFERRED #rationale_for-38
- **Source:** `AstroFinSentinelV5/tests/test_agent_http_migration.py:LL2 :: tests_test_agent_http_migration_rationale_2`
- **Target:** `AstroFinSentinelV5/tests/test_agent_http_migration.py:L1 :: astrofinsentinelv5_tests_test_agent_http_migration_py_tests_test_agent_http_migration_test_quant_agent_no_sync_requests`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_agent_http_migration.py
    ```

### INFERRED #rationale_for-39
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL66 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_66`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L65 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_mean_anomaly_360`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-40
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL58 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_58`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L57 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_earth_frame_difference_acknowledged`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-41
- **Source:** `AstroFinSentinelV5/tests/test_switch_nodes.py:LL1 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_switch_nodes.py:L1 :: astrofinsentinelv5_tests_test_switch_nodes_py_tests_test_switch_nodes`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_switch_nodes.py
    ```

### INFERRED #rationale_for-42
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL78 :: tests_test_dual_mode_rationale_78`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L77 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_return_type_unchanged`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #rationale_for-43
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL34 :: tests_test_dual_mode_rationale_34`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L33 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_masfactory_fallback_on_error`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #rationale_for-44
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL43 :: contracts_trace_contract_rationale_43`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L42 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract_list_traces`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/tracing.py:14:    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/dag_hash_modes.py:13:  - Used by: replay validation, execution traces, plan_graph
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/dag_hash_modes.py:44:                 Suitable for deterministic replay, causal traces,
    ```

### INFERRED #rationale_for-45
- **Source:** `AstroFinSentinelV5/tests/conftest.py:LL9 :: tests_conftest_rationale_9`
- **Target:** `AstroFinSentinelV5/tests/conftest.py:L8 :: tests_conftest_flask_app`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/conftest.py
    ```

### INFERRED #rationale_for-46
- **Source:** `AstroFinSentinelV5/tests/test_auth_middleware.py:LL21 :: tests_test_auth_middleware_rationale_21`
- **Target:** `AstroFinSentinelV5/tests/test_auth_middleware.py:L20 :: tests_test_auth_middleware_test_protected_endpoint_rejects_wrong_key`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth_middleware.py
    ```

### INFERRED #rationale_for-47
- **Source:** `AstroFinSentinelV5/web/components/strategy_explorer.py:LL12 :: astrofinsentinelv5_web_components_strategy_explorer_py_components_strategy_explorer_rationale_12`
- **Target:** `AstroFinSentinelV5/web/components/strategy_explorer.py:L11 :: astrofinsentinelv5_web_components_strategy_explorer_py_components_strategy_explorer_alpha_badge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/components/strategy_explorer.py
    ```

### INFERRED #rationale_for-48
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL256 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_256`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L255 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_test_known_body_result_complete`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-49
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL301 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_301`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L300 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_test_validate_skips_gracefully`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-50
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL116 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_rationale_116`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L115 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_astro_agent_called_in_real_mode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

---

## Bucket: relation = `calls` (50 edges)

### INFERRED #calls-1
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL118 :: resilience_meta_coherence_controller_metacoherencecontroller_init`
- **Target:** `atom-federation-os/coherence/objective_stabilizer.py:L102 :: coherence_objective_stabilizer_globalobjectivestabilizer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #calls-2
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL152 :: consistency_test_cross_layer_invariant_engine_testcausaldag_test_is_identical_false_different_parents`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L79 :: consistency_cross_layer_invariant_engine_causaldag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/karl_cli.py:106:    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:194:    output_path.parent.mkdir(parents=True, exist_ok=True)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/ast_snapshot.py:195:    output_path.parent.mkdir(parents=True, exist_ok=True)
    ```

### INFERRED #calls-3
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL172 :: tests_test_stability_feedback_controller_testadaptivegainrestoration_test_gain_restores_when_normal`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:37:    STABLE          = auto()   # normal operation
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/federation/trust_weighted/trust_feedback_dampener.py:37:    STABLE          = auto()   # normal operation
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/core/runtime/execution_context.py:280:        Used for gateway-internal operations that bypass normal checks.
    ```

### INFERRED #calls-4
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL9 :: alignment_test_adlr_test_oscillation_streak`
- **Target:** `atom-federation-os/alignment/adlr.py:L112 :: alignment_adlr_oscillationmonitor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:6:  - TERMINAL: streak >= K only
    ```
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:244:    K: streak threshold → ESCALATE; >K → TERMINAL
    ```
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:249:    K = 3    # streak threshold
    ```

### INFERRED #calls-5
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL165 :: consistency_test_cross_layer_invariant_engine_testcausaldag_test_is_identical_false_different_nodes`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L79 :: consistency_cross_layer_invariant_engine_causaldag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/audit_v3.py:31:    leaders = [nid for nid, n in state.get('nodes', {}).items()
    ```
    ```
    /home/workspace/atom-federation-os/audit_v3.py:32:               if getattr(dcp.nodes.get(nid), 'role', None) == 'leader']
    ```
    ```
    /home/workspace/atom-federation-os/audit_v3.py:36:    print(f"  Node roles: {[(nid, getattr(dcp.nodes.get(nid), 'role', None)) for nid in state.get('nodes', {})]}")
    ```

### INFERRED #calls-6
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL253 :: chaos_test_chaos_testnetworkpartitioner_test_partitioner_block_ip_dry_run`
- **Target:** `atom-federation-os/chaos/partitioner.py:L28 :: chaos_partitioner_networkpartitioner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/__main__.py:34:            result = asyncio.run(
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:284:        synthesis_result = await synthesis_agent.run(state)
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:440:        karl_result = await karl_agent.run(state)
    ```

### INFERRED #calls-7
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL35 :: tests_test_v68_coherence_test_drift_above_threshold_triggers_correction`
- **Target:** `atom-federation-os/coherence/drift_controller.py:L85 :: coherence_drift_controller_driftcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/observability/tests/test_integration_v2_5.py:171:      - drift + correction cycle
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/drift_detector.py:487:        correction = self._correction_type(score, severity, l3.is_diverged)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/drift_detector.py:499:            correction_type=correction,
    ```

### INFERRED #calls-8
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL36 :: alignment_test_bcil_test_bc_f3_trust_inflation`
- **Target:** `atom-federation-os/alignment/bcil.py:L20 :: alignment_bcil_quorumspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'quorumspec' not found in atom-federation-os/alignment/bcil.py
    ```

### INFERRED #calls-9
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL75 :: chaos_test_chaos_validator`
- **Target:** `atom-federation-os/chaos/validator.py:L69 :: chaos_validator_chaosvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/models.py:9:from pydantic import BaseModel, Field, validator
    ```
    ```
    /home/workspace/orchestration/models.py:42:    @validator("user_query")
    ```
    ```
    /home/workspace/orchestration/models.py:49:    @validator("symbol")
    ```

### INFERRED #calls-10
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL249 :: tests_test_v68_coherence_test_sci_drift_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:82:        with pytest.raises(SafetyViolationError) as exc_info:
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:122:            with pytest.raises(SafetyViolationError):
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:196:        with pytest.raises(SafetyViolationError):
    ```

### INFERRED #calls-11
- **Source:** `atom-federation-os/federation/bootstrap/node_runtime.py:LL82 :: bootstrap_node_runtime_noderuntime_init`
- **Target:** `atom-federation-os/chaos/replay_validator.py:L207 :: chaos_replay_validator_replayvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #calls-12
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL435 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/scripts/environment_hash.py:48:        env={**os.environ, "PIP_VERBOSITY": "quiet"},
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/cli.py:238:    parser.add_argument("--quiet", action="store_true", help="Suppress progress output, show only result")
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli.py:3:Rich output, auto-completion, --json, -v/-vv/--quiet.
    ```

### INFERRED #calls-13
- **Source:** `atom-federation-os/alignment/test_convergence.py:LL85 :: alignment_test_convergence_test_convergence_layer_integration`
- **Target:** `atom-federation-os/alignment/convergence.py:L362 :: alignment_convergence_convergencelayer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/_dashboard_cli.py:1:"""orchestration/_dashboard.py — CLI dashboard integration (ATOM-DASHBOARD-CLI"""
    ```
    ```
    /home/workspace/atom-federation-os/alignment/adlr.py:11:  - FailureReplay: save/load/replay with ADLRecoveryOrchestrator integration
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_convergence.py:111:    print("  [ConvergenceLayer] integration: ✅")
    ```

### INFERRED #calls-14
- **Source:** `atom-federation-os/chaos/validator.py:LL100 :: chaos_validator_chaosvalidator_init`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L81 :: sbs_failure_classifier_failureclassifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #calls-15
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL38 :: alignment_test_rcf_test_rcf_gcpl_stable_otl_unstable`
- **Target:** `atom-federation-os/alignment/rcf.py:L43 :: alignment_rcf_rcf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:2:from alignment.rcf import RCF, StabilityLevel
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:7:    rcf = RCF()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:13:    report = rcf.evaluate(model, observed, sensors, branches)
    ```

### INFERRED #calls-16
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL140 :: tests_test_v68_coherence_test_smoother_summary`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L71 :: coherence_temporal_smoother_temporalcoherencesmoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/proof_aware_policy_sync.py:314:    def summary(self) -> dict:
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/test_delta_gossip.py:174:        assert r.summary()["tracked_nodes"] == 0
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/routing.py:148:    def summary(self) -> dict:
    ```

### INFERRED #calls-17
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL130 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_blueprint_falls_back_to_secondary_on_error`
- **Target:** `data_room/blueprint.py:L36 :: data_room_blueprint_blueprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/architecture_linter.py:179:            "use data_room.blueprint.get_price(...)",
    ```
    ```
    /home/workspace/agents/_impl/_template_agent.py:21:    5. Consume all data through data_room.blueprint (R3, R4).
    ```
    ```
    /home/workspace/agents/_impl/_template_agent.py:123:        #     tick = data_room.blueprint.get_price(symbol, asof=state.get("asof"))
    ```

### INFERRED #calls-18
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL126 :: resilience_meta_coherence_controller_metacoherencecontroller_init`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #calls-19
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL278 :: tests_test_v68_coherence_test_sci_lattice_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:82:        with pytest.raises(SafetyViolationError) as exc_info:
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:122:            with pytest.raises(SafetyViolationError):
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:196:        with pytest.raises(SafetyViolationError):
    ```

### INFERRED #calls-20
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL202 :: tests_test_v68_coherence_test_stabilizer_j_compat_via_adapter`
- **Target:** `atom-federation-os/coherence/objective_stabilizer.py:L102 :: coherence_objective_stabilizer_globalobjectivestabilizer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/drl/__init__.py:55:        """Convert to protobuf message (used by RPC adapter)."""
    ```
    ```
    /home/workspace/atom-federation-os/drl/__init__.py:96:    adapter layers on top of.
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:42:    This adapter translates DRL's decisions to real network I/O.
    ```

### INFERRED #calls-21
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL118 :: tests_test_stability_feedback_controller_testcomputegainadjustment_test_normal_mode_no_adjustment`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:60:        adjustment = (oap_score - 0.5) * 0.4
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:61:        logger.debug(f"[OAP] no per-agent stats — uniform adj={adjustment:+.3f}")
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:62:        return dict.fromkeys(agents, adjustment)
    ```

### INFERRED #calls-22
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL290 :: chaos_test_chaos_testintegration_test_byzantine_injection_detected`
- **Target:** `atom-federation-os/chaos/scenarios.py:L287 :: chaos_scenarios_byzantine_sender_injection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/load_test/workload/generator.py:29:    """Generated job stream for one injection cycle."""
    ```
    ```
    /home/workspace/AsurDev/load_test/workload/generator.py:94:            # Failure injection
    ```
    ```
    /home/workspace/AsurDev/load_test/workload/types.py:102:    """Frequent failure injection to test rollback and recovery."""
    ```

### INFERRED #calls-23
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL139 :: consistency_test_cross_layer_invariant_engine_testcausaldag_test_is_identical_true`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L79 :: consistency_cross_layer_invariant_engine_causaldag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:50:KARL_ENABLED = os.getenv("KARL_ENABLED", "true").lower() == "true"
    ```
    ```
    /home/workspace/roma-execution-bridge/k8s/roma_controller.py:74:                    "nodeSelector": {"gpu": "true"} if gpu_required else {},
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:13:    GPU_NODE_SELECTOR = {"gpu": "true"}
    ```

### INFERRED #calls-24
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL29 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_starts_closed`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:103:    AFTER fix (TOCTOU closed):
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gsct.py:32:    """A closed subset of the state space containing trajectories."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/formal/model_checker.py:103:    AFTER fix (TOCTOU closed):
    ```

### INFERRED #calls-25
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL337 :: tests_test_v68_coherence_test_sci_convergence_window`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:349:        print("║  T_AFTER:  TOCTOU window eliminated                       ║")
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/auth.py:35:    window = {"free": 60, "pro": 10, "enterprise": 1}[tier]
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/auth.py:38:    if now - last < window:
    ```

### INFERRED #calls-26
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL113 :: alignment_test_gcpl_test_checker_irreconcilable_ratio`
- **Target:** `atom-federation-os/alignment/gcpl.py:L192 :: alignment_gcpl_globalconsistencychecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_stability_feedback_controller.py:66:        """Gain ratio near 1.0 → stable."""
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_stability_feedback_controller.py:71:                actual_gain=0.1 + (i % 2) * 0.01,  # near 1.0 ratio
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_stability_feedback_controller.py:84:            ratio = 1.4 if i % 2 == 0 else 0.2
    ```

### INFERRED #calls-27
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL219 :: chaos_test_chaos_testchaosharness_test_harness_runs_all_scenarios`
- **Target:** `atom-federation-os/chaos/harness.py:L126 :: chaos_harness_chaosharness`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:338:    """Runs a suite of federation scenarios and produces a report."""
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:357:        scenarios = [
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:386:        for s in scenarios:
    ```

### INFERRED #calls-28
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL46 :: tests_test_v68_coherence_test_drift_hysteresis_no_jitter`
- **Target:** `atom-federation-os/coherence/drift_controller.py:L85 :: coherence_drift_controller_driftcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/__init__.py:9:  - Exponential backoff with jitter on push failures
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/shared/drl_bridge.py:13:    - latency jitter (non-deterministic delay)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/cluster/shared/drl_bridge.py:18:    "noisy but functional" LAN (≈ 5% loss, 30 ms ± 15 ms jitter).
    ```

### INFERRED #calls-29
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL138 :: alignment_test_rcf_test_rcf_boundary_45_stable`
- **Target:** `atom-federation-os/alignment/rcf.py:L43 :: alignment_rcf_rcf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:2:from alignment.rcf import RCF, StabilityLevel
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:7:    rcf = RCF()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:13:    report = rcf.evaluate(model, observed, sensors, branches)
    ```

### INFERRED #calls-30
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL274 :: chaos_test_chaos_testintegration_test_node_isolation_complete`
- **Target:** `atom-federation-os/chaos/scenarios.py:L296 :: chaos_scenarios_node_isolation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:6:# 3. SQLite WAL + deferred isolation — no deadlock
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:1:# tests/conftest.py — SBS isolation for atom-federation-os tests
    ```
    ```
    /home/workspace/atom-federation-os/federation/security/replay_protection.py:259:    # ── per-sender isolation ─────────────────────────────────────────
    ```

### INFERRED #calls-31
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL316 :: tests_test_stability_feedback_controller_testdampingbounds_test_damping_never_below_min`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:74:            adjustment = max(-0.25, min(0.25, (agent_score - 0.5) * 0.5))
    ```
    ```
    /home/workspace/atom-federation-os/federation.consensus_resolver.py:91:            best = min(tied, key=self._drift)
    ```
    ```
    /home/workspace/atom-federation-os/federation/gossip_protocol.py:78:        k = min(self.config.fanout, len(available))
    ```

### INFERRED #calls-32
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL23 :: alignment_test_rcf_test_rcf_byzantine_critical`
- **Target:** `atom-federation-os/alignment/rcf.py:L43 :: alignment_rcf_rcf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/test_rcf.py:2:from alignment.rcf import RCF, StabilityLevel
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_rcf.py:7:    rcf = RCF()
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_rcf.py:14:    report = rcf.evaluate(model, observed, sensors, branches)
    ```

### INFERRED #calls-33
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL96 :: alignment_test_bcil_test_bc_split_brain`
- **Target:** `atom-federation-os/alignment/bcil.py:L20 :: alignment_bcil_quorumspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/tests/test_consensus_resolver.py:201:        """2 vs 2 split-brain → highest stability wins."""
    ```
    ```
    /home/workspace/atom-federation-os/alignment/bcil.py:287:                explanation="Split-brain: multiple branches have quorum"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/scenarios.py:223:    A+B form majority. C thinks it's still leader (split-brain).
    ```

### INFERRED #calls-34
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL89 :: alignment_test_adlr_test_ri3_deterministic`
- **Target:** `atom-federation-os/alignment/adlr.py:L241 :: alignment_adlr_adlrecoveryorchestrator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/cluster/shared/drl_bridge.py:13:    - latency jitter (non-deterministic delay)
    ```
    ```
    /home/workspace/atom-federation-os/scripts/execution_graph_hash.py:5:Builds a deterministic DAG of all execution entry points and their call-sites,
    ```
    ```
    /home/workspace/atom-federation-os/scripts/ast_snapshot.py:7:serialized to produce a deterministic SHA256 hash.
    ```

### INFERRED #calls-35
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL264 :: tests_test_v68_coherence_test_sci_coherence_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/security/origin_policy.py:14:    policy.check(sender_id="node_C", trust_score=0.8)  # → raises OriginViolation
    ```
    ```
    /home/workspace/atom-federation-os/federation/security/origin_policy.py:18:    trust_policy.check(sender_id="node_B", trust_score=0.1)  # → raises OriginViolation
    ```
    ```
    /home/workspace/atom-federation-os/federation/semantic/test_v910.py:41:        with pytest.raises(ValueError):
    ```

### INFERRED #calls-36
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL33 :: alignment_test_adlr_test_policy_escalate`
- **Target:** `atom-federation-os/alignment/adlr.py:L147 :: alignment_adlr_recoverypolicy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:103:            HIGH / CRITICAL        → REWEIGHT  (NO reset — escalate only via human)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/v8_2a_safety_foundations/stability_governor.py:19:    ESCALATE = "ESCALATE"     # health critically low → escalate to human review
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/v8_2a_safety_foundations/stability_governor.py:122:            reasons.append(f"PSI={signal.plan_stability_index:.3f}+health={signal.health_score:.3f} → escalate")
    ```

### INFERRED #calls-37
- **Source:** `astrofin-sentinel-v5/meta_rl/git_agent_exporter.py:LL30 :: astrofin_sentinel_v5_meta_rl_git_agent_exporter_py_meta_rl_git_agent_exporter_validate_agent_yaml`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/operator_sdk/converter.py:14:        yaml = generate_crd_yaml(crd)
    ```
    ```
    /home/workspace/roma-execution-bridge/operator_sdk/converter.py:16:        self._converted[name] = {"crd_yaml": yaml, "controller_code": code, "schema": crd.schema}
    ```
    ```
    /home/workspace/integrations/gitagent/validators/agent_validator.py:8:import yaml
    ```

### INFERRED #calls-38
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL278 :: tests_test_v68_coherence_test_sci_lattice_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/security/origin_policy.py:14:    policy.check(sender_id="node_C", trust_score=0.8)  # → raises OriginViolation
    ```
    ```
    /home/workspace/atom-federation-os/federation/security/origin_policy.py:18:    trust_policy.check(sender_id="node_B", trust_score=0.1)  # → raises OriginViolation
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:82:        with pytest.raises(SafetyViolationError) as exc_info:
    ```

### INFERRED #calls-39
- **Source:** `atom-federation-os/cluster/shared/sbs_client.py:LL36 :: shared_sbs_client_sbsdistributedclient_init`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L62 :: sbs_global_invariant_engine_globalinvariantengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #calls-40
- **Source:** `atom-federation-os/chaos/harness.py:LL137 :: chaos_harness_chaosharness_init`
- **Target:** `atom-federation-os/chaos/validator.py:L69 :: chaos_validator_chaosvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:108:                 "  init [shape=point];", "  init -> S0;"]
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:156:    def build(self, init: State) -> None:
    ```
    ```
    /home/workspace/atom-federation-os/formal/model_checker.py:157:        Q = deque([init])
    ```

### INFERRED #calls-41
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL160 :: alignment_test_alignment_test_rollback_decider`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L82 :: alignment_rollback_engine_v2_rollbackdecider`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_alignment.py:160:    decider = RollbackDecider()
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_alignment.py:168:    scope_ok = decider.decide(bind_ok, rep_ok)
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_alignment.py:170:    print(f"  decider OK→noop: type={scope_ok.rollback_type.name} ✅")
    ```

### INFERRED #calls-42
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL66 :: alignment_test_rcf_test_rcf_high_branch_entropy_critical`
- **Target:** `atom-federation-os/alignment/rcf.py:L43 :: alignment_rcf_rcf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:2:from alignment.rcf import RCF, StabilityLevel
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:7:    rcf = RCF()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_rcf.py:13:    report = rcf.evaluate(model, observed, sensors, branches)
    ```

### INFERRED #calls-43
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL41 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_opens_after_threshold`
- **Target:** `data_room/circuit_breaker.py:L79 :: data_room_circuit_breaker_call_with_breaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:326:            '# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:352:# ── circuit breaker registry (singleton) ───────────────────────────────────────
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:375:    """Manually reset a circuit breaker to CLOSED state."""
    ```

### INFERRED #calls-44
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL292 :: consistency_test_cross_layer_invariant_engine_testcrosslayerinvariantengine_test_all_passed_false_when_any_fails`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L131 :: consistency_cross_layer_invariant_engine_crosslayerinvariantengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/orchestration/models.py:25:    If Pydantic validation fails, the orchestrator never runs —
    ```
    ```
    /home/workspace/roma-execution-bridge/input_contract/__init__.py:11:    """Raised when input fails validation."""
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_enforcement_layer.py:390:        '''Direct mutation call fails without context.'''
    ```

### INFERRED #calls-45
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL149 :: tests_test_stability_feedback_controller_testcomputegainadjustment_test_saturated_mode_reduces_gain_significantly`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/orchestration/planning_observability/drift_profiler.py:9:  - structural DAG drift (graph structure changing significantly)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/continuous_stability.py:168:            # 3. Convergence detection: if score improved significantly → partition healed
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/predictive_controller.py:78:        """True if predicted score is significantly worse than current."""
    ```

### INFERRED #calls-46
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL344 :: tests_test_stability_feedback_controller_testhistorymanagement_test_gain_history_max_length`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/failure_replay/event_store.py:450:                mismatches.append({"event": e, "reason": f"bad length {len(e.event_id)}"})
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:33:        assert chain.length == 1
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_meta_control_v78.py:68:        chain_length=chain.length,
    ```

### INFERRED #calls-47
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL216 :: tests_test_stability_feedback_controller_testapplygaintocommands_test_noop_when_apply_false`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gsct.py:308:        # F4: Undefined attractor (false closure illusion)
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gsct.py:308:        # F4: Undefined attractor (false closure illusion)
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli_config.py:10:    "allow_split_brain": "false",
    ```

### INFERRED #calls-48
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL68 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_half_open_recovery`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/bootstrap/cluster_simulator.py:144:        """Remove fault from a node (recovery scenario)."""
    ```
    ```
    /home/workspace/atom-federation-os/rpc/test_rpc.py:11:6. node_crash_and_reconnect   kill one node, reconnect, verify recovery
    ```
    ```
    /home/workspace/atom-federation-os/rpc/test_rpc.py:382:    messages buffered/dropped during downtime, then recovery.
    ```

### INFERRED #calls-49
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL47 :: alignment_test_bcil_test_bc_f4_equivocation`
- **Target:** `atom-federation-os/alignment/bcil.py:L20 :: alignment_bcil_quorumspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:185:        - digest matches leader's PRE_PREPARE (equivocation detection)
    ```
    ```
    /home/workspace/atom-federation-os/federation/byzantine/pbft_consensus.py:196:            return False, None  # ← equivocation: voter sent different digest → reject
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/bcil.py:177:        # Only flag equivocation if the SAME voter set saw different digests
    ```

### INFERRED #calls-50
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL80 :: chaos_test_chaos_classifier`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L81 :: sbs_failure_classifier_failureclassifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/test_chaos.py:79:def classifier():
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/test_chaos.py:121:    def test_classifies_partition(self, classifier):
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/test_chaos.py:123:        result = classifier.classify(event)
    ```

---

## Bucket: relation = `inherits` (50 edges)

### INFERRED #inherits-1
- **Source:** `roma-execution-bridge/saas/gateway/models.py:LL33 :: gateway_models_authconfig`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-2
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL162 :: agent_runtime_app_taskcreate`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-3
- **Source:** `push/tests/test_rag_agent_integration.py:LL8 :: push_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `(empty): :: baseagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-4
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL13 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_eventtype`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-5
- **Source:** `atom-federation-os/alignment/adlr.py:LL25 :: alignment_adlr_oscillationstage`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-6
- **Source:** `atom-federation-os/alignment/gsct.py:LL22 :: alignment_gsct_regime`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-7
- **Source:** `audit_repo/orchestration/models.py:LL20 :: audit_repo_orchestration_models_py_orchestration_models_sentinelv5request`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-8
- **Source:** `atom-federation-os/core/economics/slashing_engine.py:LL43 :: economics_slashing_engine_economicsecurityviolation`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/production_worker.py:149:            print(f"[{self.worker_id}] Job {job.job_id} exception: {e}")
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```

### INFERRED #inherits-9
- **Source:** `atom-federation-os/sbs/runtime.py:LL42 :: sbs_runtime_invariantviolation`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/production_worker.py:149:            print(f"[{self.worker_id}] Job {job.job_id} exception: {e}")
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```

### INFERRED #inherits-10
- **Source:** `atom-federation-os/alignment/convergence.py:LL190 :: alignment_convergence_entropyregime`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-11
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL31 :: monitoring_health_endpoints_healthresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-12
- **Source:** `atom-federation-os/federation/security/inbound_security_gate.py:LL42 :: security_inbound_security_gate_securityviolation`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:78:        """AUDIT mode → returns False, no exception."""
    ```

### INFERRED #inherits-13
- **Source:** `astrofin-sentinel-v5/agents/_impl/amre/oap_optimizer.py:LL12 :: astrofin_sentinel_v5_agents_impl_amre_oap_optimizer_py_amre_oap_optimizer_optimizationstatus`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-14
- **Source:** `astrofin-sentinel-v5/trading/execution/sanity.py:LL11 :: astrofin_sentinel_v5_trading_execution_sanity_py_execution_sanity_validationstatus`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-15
- **Source:** `atom-federation-os/actuator/divergence_response_policy.py:LL31 :: actuator_divergence_response_policy_responseaction`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-16
- **Source:** `AsurDev/ml_engine/inference/schemas.py:LL94 :: inference_schemas_explainresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-17
- **Source:** `atom-federation-os/alignment/gcst.py:LL15 :: alignment_gcst_regime`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-18
- **Source:** `push/orchestration/models.py:LL20 :: push_orchestration_models_py_orchestration_models_sentinelv5request`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-19
- **Source:** `atom-federation-os/core/proof/proof_verifier.py:LL26 :: proof_proof_verifier_proofverificationerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:78:        """AUDIT mode → returns False, no exception."""
    ```

### INFERRED #inherits-20
- **Source:** `astrofin-sentinel-v5/tests/test_rag_agent_integration.py:LL8 :: astrofin_sentinel_v5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `(empty): :: baseagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-21
- **Source:** `astrofin-sentinel-v5/trading/broker/base.py:LL23 :: astrofin_sentinel_v5_trading_broker_base_py_broker_base_orderstatus`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-22
- **Source:** `roma-execution-bridge/gpu_worker/server.py:LL33 :: gpu_worker_server_jobrequest`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-23
- **Source:** `astrofin-sentinel-v5/knowledge/daily_brief/idea_tracker_refactored.py:LL35 :: astrofin_sentinel_v5_knowledge_daily_brief_idea_tracker_refactored_py_daily_brief_idea_tracker_refactored_ideastatus`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-24
- **Source:** `roma-execution-bridge/models/roma_schema.py:LL7 :: models_roma_schema_resourcespec`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-25
- **Source:** `push/agents/_impl/ephemeris_decorator.py:LL46 :: push_agents_impl_ephemeris_decorator_py_impl_ephemeris_decorator_ephemerisunavailableerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:78:        """AUDIT mode → returns False, no exception."""
    ```

### INFERRED #inherits-26
- **Source:** `roma-execution-bridge/input_contract/__init__.py:LL10 :: input_contract_init_romavalidationerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:78:        """AUDIT mode → returns False, no exception."""
    ```

### INFERRED #inherits-27
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL7 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `(empty): :: baseagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-28
- **Source:** `AsurDev/ete/compiler/dag.py:LL14 :: asurdev_ete_compiler_dag_py_compiler_dag_nodetype`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-29
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL13 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_tunnelstate`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-30
- **Source:** `atom-federation-os/core/runtime/runtime_guard.py:LL29 :: runtime_runtime_guard_systemintegrityviolation`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/production_worker.py:149:            print(f"[{self.worker_id}] Job {job.job_id} exception: {e}")
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```

### INFERRED #inherits-31
- **Source:** `audit_repo/orchestration/router.py:LL24 :: audit_repo_orchestration_router_py_orchestration_router_routeroutput`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-32
- **Source:** `roma-execution-bridge/saas/tenants/models.py:LL35 :: tenants_models_tenantbase`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-33
- **Source:** `atom-federation-os/alignment/mcpc.py:LL17 :: alignment_mcpc_driftkind`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-34
- **Source:** `astrofin-sentinel-v5/mas_factory/topology.py:LL20 :: astrofin_sentinel_v5_mas_factory_topology_py_mas_factory_topology_switchstrategy`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-35
- **Source:** `audit_repo/tests/test_rag_agent_integration.py:LL8 :: audit_repo_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Target:** `(empty): :: baseagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-36
- **Source:** `atom-federation-os/core/federation/distributed_ledger.py:LL71 :: federation_distributed_ledger_ledgerintegrityerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:78:        """AUDIT mode → returns False, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```

### INFERRED #inherits-37
- **Source:** `roma-execution-bridge/main.py:LL20 :: roma_execution_bridge_main_romataskinput`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-38
- **Source:** `astrofin-sentinel-v5/orchestration/router.py:LL24 :: astrofin_sentinel_v5_orchestration_router_py_orchestration_router_routeroutput`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-39
- **Source:** `AsurDev/v6/solver/optimizer_api.py:LL28 :: asurdev_v6_solver_optimizer_api_py_solver_optimizer_api_optimizationresult`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-40
- **Source:** `atom-federation-os/alignment/rcf.py:LL19 :: alignment_rcf_stabilitylevel`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-41
- **Source:** `astrofin-sentinel-v5/core/aspects.py:LL20 :: astrofin_sentinel_v5_core_aspects_py_core_aspects_aspecttype`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-42
- **Source:** `AsurDev/scheduler_v3/api.py:LL73 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_schedulerequest`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-43
- **Source:** `roma-execution-bridge/saas_api/auth.py:LL12 :: saas_api_auth_ratelimitexceeded`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/production_worker.py:149:            print(f"[{self.worker_id}] Job {job.job_id} exception: {e}")
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```

### INFERRED #inherits-44
- **Source:** `roma-execution-bridge/models/roma_schema.py:LL31 :: models_roma_schema_romainput`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-45
- **Source:** `audit_repo/agents/_impl/ephemeris_decorator.py:LL46 :: audit_repo_agents_impl_ephemeris_decorator_py_impl_ephemeris_decorator_ephemerisunavailableerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/chaos/harness.py:248:            error = f"harness exception: {e}"
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:40:        """Healthy state → enforce returns True, no exception."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/sbs/tests/test_sbs_runtime.py:78:        """AUDIT mode → returns False, no exception."""
    ```

### INFERRED #inherits-46
- **Source:** `AsurDev/ai_scheduler/scheduler_v2.py:LL20 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_schedulerequest`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-47
- **Source:** `AsurDev/ml_engine/inference/schemas.py:LL123 :: inference_schemas_metricsresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-48
- **Source:** `astrofin-sentinel-v5/knowledge/daily_digest/daily_digest_log.py:LL20 :: astrofin_sentinel_v5_knowledge_daily_digest_daily_digest_log_py_daily_digest_daily_digest_log_digeststatus`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-49
- **Source:** `atom-federation-os/actuator/stability_feedback_controller.py:LL25 :: actuator_stability_feedback_controller_oscillationmode`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-50
- **Source:** `astrofin-sentinel-v5/agents/_impl/amre/oap_optimizer.py:LL18 :: astrofin_sentinel_v5_agents_impl_amre_oap_optimizer_py_amre_oap_optimizer_controlaction`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

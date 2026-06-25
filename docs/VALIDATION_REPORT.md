# VALIDATION_REPORT.md

Stratified validation of N=452 INFERRED edges from `graphify-out/graph.json` (snapshot 2026-06-17).

**Verdict legend:**
- `valid` — link is real and current
- `false` — link does not exist in code

**Verdict summary (N=452):** `valid`=272 (60%), `ambiguous`=179 (40%), `false`=1 (0%)

- `moved` — entity exists, but in a different file (new path noted)
- `outdated` — was true at some point, now dead (e.g. `_archived/`, removed submodules)
- `ambiguous` — needs human review

---

## Bucket: relation = `imports` (80 edges)

### INFERRED #imports-1
- **Source:** `atom-federation-os/rpc/__init__.py:LL37 :: rpc_init`
- **Target:** `atom-federation-os/rpc/server.py:L81 :: rpc_server_create_server`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:12:from web.wsgi import server as flask_app
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:4:from web.app import server
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:9:    server.config["TESTING"] = True
    ```

### INFERRED #imports-2
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL18 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-3
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL12 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/explainable_divergence_engine.py:L117 :: consistency_v3_explainable_divergence_engine_explainabledivergenceengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-4
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL23 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/system_observer.py:L25 :: testing_system_observer_stabilitylevel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/integrations/gitagent/tests/test_mcp_adapter.py:15:    """Test suite for MCPAdapter."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```

### INFERRED #imports-5
- **Source:** `audit_repo/tests/test_validator.py:LL10 :: audit_repo_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-6
- **Source:** `audit_repo/tests/data_room/test_data_room.py:LL115 :: audit_repo_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L12 :: data_room_blueprint_pricetick`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/audit_repo/tests/test_data_room_api.py:17:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```

### INFERRED #imports-7
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL3 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/feedback_injection.py:L161 :: v8_2b_controlled_autocorrection_feedback_injection_feedbackinjectionloop`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-8
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL23 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/system_observer.py:L70 :: testing_system_observer_systemobserver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/integrations/gitagent/tests/test_mcp_adapter.py:15:    """Test suite for MCPAdapter."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```

### INFERRED #imports-9
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL21 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/mutation_ledger.py:L34 :: v8_2a_safety_foundations_mutation_ledger_ledgerentry`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-10
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL18 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L19 :: v8_2b_controlled_autocorrection_severity_mapper_mutationclass`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-11
- **Source:** `audit_repo/tests/test_validator.py:LL10 :: audit_repo_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-12
- **Source:** `audit_repo/tests/data_room/test_data_room.py:LL18 :: audit_repo_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L34 :: data_room_circuit_breaker_breakerstate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-13
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL29 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/branch.py:L34 :: alignment_branch_branchpoint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports-14
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:LL12 :: v8_2b_controlled_autocorrection_mutation_executor`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:L50 :: v8_2b_controlled_autocorrection_policy_selector_mutationpolicy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:89:    logger.info("executor.running_topology")
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:90:    executor = TopologyExecutor(topology, state)
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:91:    results = await executor.run()
    ```

### INFERRED #imports-15
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/__init__.py:LL13 :: v8_2b_controlled_autocorrection_init`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:L85 :: v8_2b_controlled_autocorrection_policy_selector_policyselector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-16
- **Source:** `atom-federation-os/cluster/node/node.py:LL15 :: node_node`
- **Target:** `atom-federation-os/proto/atom_os_pb2_grpc.py:L1 :: proto_atom_os_pb2_grpc`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/core/tracing.py:10:from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/observability/tracing.py:10:from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    ```
    ```
    /home/workspace/core/tracing.py:11:from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
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
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-18
- **Source:** `push/tests/data_room/test_data_room.py:LL18 :: push_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L79 :: data_room_circuit_breaker_call_with_breaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/AsurDev/ml_engine/inference/ml_client.py:5:Includes circuit-breaker behaviour: on API error → falls back to 0.0.
    ```

### INFERRED #imports-19
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL14 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/invariant_checker.py:L83 :: v8_2a_safety_foundations_invariant_checker_positivesemidefiniteinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-20
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L84 :: alignment_drift_detector_executiontrace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-21
- **Source:** `atom-federation-os/alignment/__init__.py:LL33 :: alignment_init`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L59 :: alignment_rollback_engine_v2_rollbackplan`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-22
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL15 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/load_simulator.py:L374 :: testing_load_simulator_make_cascade_failure_scenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/ad_hoc_ov_check.py:3:Builds a synthetic enriched-edge list that mirrors the production tie scenario
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:5:Performs Root Cause Analysis for each failure scenario,
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:30:    scenario: str
    ```

### INFERRED #imports-23
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL14 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/invariant_checker.py:L16 :: v8_2a_safety_foundations_invariant_checker_invariantviolation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-24
- **Source:** `audit_repo/meta_rl/strategy_evaluator.py:LL111 :: audit_repo_meta_rl_strategy_evaluator_py_meta_rl_strategy_evaluator`
- **Target:** `meta_rl/types.py:L149 :: meta_rl_types_symbolmetrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:244:        # Use a plain object — evaluator should not even reach backtest_adapter.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:251:        """With ≥10 OHLCV bars the evaluator must run the backtest pipeline
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:349:            evaluator = StrategyEvaluator()
    ```

### INFERRED #imports-25
- **Source:** `atom-federation-os/kubernetes/atom_operator/controller.py:LL12 :: atom_operator_controller`
- **Target:** `atom-federation-os/kubernetes/atom_operator/client.py:L11 :: atom_operator_client_k8sclient`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/admission_controller/__init__.py:1:from .controller import AdmissionController, AdmitDecision, AdmitResult
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:129:    controller = ProbabilisticAdmissionController(windows)
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:137:        controller.update("rtx-node", val)
    ```

### INFERRED #imports-26
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL23 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/stability_governor.py:L43 :: v8_2a_safety_foundations_stability_governor_stabilitygovernor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-27
- **Source:** `atom-federation-os/kubernetes/atom_operator/main.py:LL17 :: atom_operator_main`
- **Target:** `atom-federation-os/kubernetes/atom_operator/controller.py:L18 :: atom_operator_controller_atomcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:91:    """Import infer_edges.py with REPO_ROOT monkey-patched, run main()."""
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:110:        mod.main()
    ```

### INFERRED #imports-28
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL28 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L19 :: byzantine_message_signatures_messagesignatureerror`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-29
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL23 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_store.py:L73 :: agent_runtime_event_store_eventstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:24:# ── ПРОСТОЙ EVENT STORE (вместо внешнего pkg.eventstore) ──
    ```
    ```
    /home/workspace/atom-federation-os/chaos/__init__.py:20:from pkg.eventstore.store import EventStore
    ```

### INFERRED #imports-30
- **Source:** `tests/data_room/test_data_room.py:LL18 :: tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L100 :: data_room_circuit_breaker_circuitbreakeropen`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-31
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL23 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/system_observer.py:L36 :: testing_system_observer_stabilitysnapshot`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/integrations/gitagent/tests/test_mcp_adapter.py:15:    """Test suite for MCPAdapter."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```

### INFERRED #imports-32
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:LL280 :: v8_2b_controlled_autocorrection_mutation_executor`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:L20 :: v8_2b_controlled_autocorrection_policy_selector_policycontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:89:    logger.info("executor.running_topology")
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:90:    executor = TopologyExecutor(topology, state)
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:91:    results = await executor.run()
    ```

### INFERRED #imports-33
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL30 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/quorum.py:L17 :: byzantine_quorum_quorumtype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-34
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL2 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/drl_bridge.py:L7 :: shared_drl_bridge_drlbridge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-35
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL33 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:L127 :: agent_runtime_task_store_taskstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports-36
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL22 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:L33 :: agent_runtime_event_sourcing_taskevent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports-37
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL31 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/view_change.py:L21 :: byzantine_view_change_viewchangeevent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-38
- **Source:** `atom-federation-os/federation/byzantine/pbft_consensus.py:LL17 :: byzantine_pbft_consensus`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L23 :: byzantine_message_signatures_federationmessagesigning`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:95:    print("T2 OK | consensus LONG → abstains, reports dominant=BradleyAgent LONG@80")
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:112:    # T4 — strong consensus, no compromise
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:119:    print("T4 OK | consensus LONG → abstains, reports dominant=AstroCouncil LONG@85")
    ```

### INFERRED #imports-39
- **Source:** `audit_repo/tests/data_room/test_data_room.py:LL18 :: audit_repo_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L79 :: data_room_circuit_breaker_call_with_breaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/AsurDev/ml_engine/inference/ml_client.py:5:Includes circuit-breaker behaviour: on API error → falls back to 0.0.
    ```

### INFERRED #imports-40
- **Source:** `audit_repo/tests/test_validator.py:LL10 :: audit_repo_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-41
- **Source:** `audit_repo/tests/test_validator.py:LL10 :: audit_repo_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L35 :: validators_agent_validator_validationreport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-42
- **Source:** `atom-federation-os/alignment/__init__.py:LL27 :: alignment_init`
- **Target:** `atom-federation-os/alignment/plan_reality_comparator.py:L31 :: alignment_plan_reality_comparator_nodemapping`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-43
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/policy_selector.py:LL8 :: v8_2b_controlled_autocorrection_policy_selector`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L19 :: v8_2b_controlled_autocorrection_severity_mapper_mutationclass`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:199:        Output("strategy-selector", "options"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:200:        Output("strategy-selector", "value"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:201:        Input("session-selector", "value"),
    ```

### INFERRED #imports-44
- **Source:** `push/tests/data_room/test_data_room.py:LL115 :: push_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L12 :: data_room_blueprint_pricetick`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-45
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL29 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/pbft_consensus.py:L70 :: byzantine_pbft_consensus_consensusoutcome`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-46
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL21 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/mutation_ledger.py:L87 :: v8_2a_safety_foundations_mutation_ledger_mutationledger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-47
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL30 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/equivalence.py:L55 :: alignment_equivalence_mergedecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports-48
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L178 :: alignment_drift_detector_layer3result`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-49
- **Source:** `atom-federation-os/rpc/__init__.py:LL37 :: rpc_init`
- **Target:** `atom-federation-os/rpc/server.py:L109 :: rpc_server_serve_forever`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/adlr.py:82:    """Enforces liveness: cannot stall forever, every oscillation resolves."""
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/v106_liveness_proof.py:99:Without BCIL veto: alternation cannot avoid TERMINAL forever.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/federation/bootstrap/cluster_simulator.py:59:    fault_step_end: int | None = None  # None = stays degraded forever
    ```

### INFERRED #imports-50
- **Source:** `tests/data_room/test_data_room.py:LL18 :: tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L34 :: data_room_circuit_breaker_breakerstate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-51
- **Source:** `atom-federation-os/cluster/shared/rpc_server.py:LL23 :: shared_rpc_server`
- **Target:** `atom-federation-os/proto/atom_os_pb2_grpc.py:L1 :: proto_atom_os_pb2_grpc`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/core/tracing.py:10:from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/observability/tracing.py:10:from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    ```
    ```
    /home/workspace/core/tracing.py:11:from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    ```

### INFERRED #imports-52
- **Source:** `astrofin-sentinel-v5/tests/test_validator.py:LL10 :: astrofin_sentinel_v5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-53
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL29 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/pbft_consensus.py:L79 :: byzantine_pbft_consensus_pbftliteconsensusengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-54
- **Source:** `atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:LL36 :: trust_weighted_trust_dynamics_stabilizer`
- **Target:** `atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:L59 :: trust_weighted_trust_feedback_dampener_trustupdateresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/v7/policy_governor/governor.py:47:    EMA-based policy stabilizer.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/meta_coherence_controller.py:118:        self.stabilizer = GlobalObjectiveStabilizer(
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/meta_coherence_controller.py:244:        stabilizer_snap = self.stabilizer.compute_J(
    ```

### INFERRED #imports-55
- **Source:** `push/tests/data_room/test_data_room.py:LL18 :: push_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L100 :: data_room_circuit_breaker_circuitbreakeropen`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-56
- **Source:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:LL13 :: v8_2b_controlled_autocorrection_mutation_executor`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/severity_mapper.py:L19 :: v8_2b_controlled_autocorrection_severity_mapper_mutationclass`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:89:    logger.info("executor.running_topology")
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:90:    executor = TopologyExecutor(topology, state)
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5_mas.py:91:    results = await executor.run()
    ```

### INFERRED #imports-57
- **Source:** `atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:LL36 :: trust_weighted_trust_dynamics_stabilizer`
- **Target:** `atom-federation-os/federation/trust_weighted/trust_feedback_dampener.py:L46 :: trust_weighted_trust_feedback_dampener_dampenerconfig`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/v7/policy_governor/governor.py:47:    EMA-based policy stabilizer.
    ```
    ```
    /home/workspace/atom-federation-os/resilience/meta_coherence_controller.py:118:        self.stabilizer = GlobalObjectiveStabilizer(
    ```
    ```
    /home/workspace/atom-federation-os/resilience/meta_coherence_controller.py:244:        stabilizer_snap = self.stabilizer.compute_J(
    ```

### INFERRED #imports-58
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/chaos_test_suite.py:LL15 :: testing_chaos_test_suite`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/testing/load_simulator.py:L37 :: testing_load_simulator_chaosconfig`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/integrations/gitagent/tests/test_mcp_adapter.py:15:    """Test suite for MCPAdapter."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```

### INFERRED #imports-59
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL22 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/rollback_engine.py:L54 :: v8_2a_safety_foundations_rollback_engine_rollbackengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-60
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL30 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/equivalence.py:L94 :: alignment_equivalence_equivalencechecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports-61
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/async_engine.py:LL156 :: agent_runtime_async_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:L233 :: agent_runtime_engine_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:44:    result = subprocess.run(
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:54:    pytest_result = subprocess.run(
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:33:    return asyncio.run(run_test())
    ```

### INFERRED #imports-62
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL37 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/federation/quorum_certificate.py:L20 :: federation_quorum_certificate_quorumcertificate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:131:        "network_latency": network_latency(node, "gateway"),
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:5:Every trade/agent/job MUST pass through this gateway.
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:107:    gateway = ACOSSubmissionGateway()
    ```

### INFERRED #imports-63
- **Source:** `audit_repo/tests/data_room/test_data_room.py:LL115 :: audit_repo_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L36 :: data_room_blueprint_blueprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_data_room_api.py:1:"""Smoke test for Data Room API blueprint."""
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:115:    from data_room.blueprint import Blueprint, PriceTick
    ```

### INFERRED #imports-64
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL22 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/rollback_engine.py:L23 :: v8_2a_safety_foundations_rollback_engine_checkpoint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/core/belief.py:26:from core.checkpoint import get_project_root
    ```
    ```
    /home/workspace/audit_repo/core/checkpoint.py:21:    # This file lives at: <project_root>/core/checkpoint.py
    ```
    ```
    /home/workspace/audit_repo/core/history_db.py:12:from core.checkpoint import get_project_root
    ```

### INFERRED #imports-65
- **Source:** `audit_repo/tests/test_validator.py:LL10 :: audit_repo_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L11 :: validators_agent_validator_severity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_validator.py:442:            severity=Severity.ERROR,
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:68:    severity: str        # "FAIL" | "WARN"
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:88:        return any(f.severity == "FAIL" for f in self.findings)
    ```

### INFERRED #imports-66
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/async_engine.py:LL255 :: agent_runtime_async_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_store.py:L73 :: agent_runtime_event_store_eventstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:24:# ── ПРОСТОЙ EVENT STORE (вместо внешнего pkg.eventstore) ──
    ```
    ```
    /home/workspace/atom-federation-os/chaos/__init__.py:20:from pkg.eventstore.store import EventStore
    ```

### INFERRED #imports-67
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL28 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L12 :: byzantine_message_signatures_signedmessage`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-68
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL18 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L100 :: data_room_circuit_breaker_circuitbreakeropen`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-69
- **Source:** `astrofin-sentinel-v5/tests/test_validator.py:LL10 :: astrofin_sentinel_v5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-70
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL14 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/invariant_checker.py:L59 :: v8_2a_safety_foundations_invariant_checker_spectralinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-71
- **Source:** `audit_repo/tests/data_room/test_data_room.py:LL18 :: audit_repo_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L100 :: data_room_circuit_breaker_circuitbreakeropen`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-72
- **Source:** `tests/data_room/test_data_room.py:LL18 :: tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:18:    """При запросе /data-room/conflicts должен возвращаться JSON."""
    ```
    ```
    /home/workspace/tests/test_data_room_api.py:22:        resp = c.get("/data-room/conflicts")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:171:        return  # the data room itself is the only allowed caller
    ```

### INFERRED #imports-73
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L41 :: alignment_drift_detector_driftseverity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-74
- **Source:** `tests/data_room/test_data_room.py:LL115 :: tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/blueprint.py:L36 :: data_room_blueprint_blueprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_data_room_api.py:1:"""Smoke test for Data Room API blueprint."""
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:115:    from data_room.blueprint import Blueprint, PriceTick
    ```

### INFERRED #imports-75
- **Source:** `atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:LL35 :: trust_weighted_trust_dynamics_stabilizer`
- **Target:** `atom-federation-os/federation/trust_weighted/node_weights.py:L44 :: trust_weighted_node_weights_nodeweightssnapshot`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/v7/policy_governor/governor.py:47:    EMA-based policy stabilizer.
    ```
    ```
    /home/workspace/atom-federation-os/resilience/meta_coherence_controller.py:118:        self.stabilizer = GlobalObjectiveStabilizer(
    ```
    ```
    /home/workspace/atom-federation-os/resilience/meta_coherence_controller.py:244:        stabilizer_snap = self.stabilizer.compute_J(
    ```

### INFERRED #imports-76
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL23 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/stability_governor.py:L14 :: v8_2a_safety_foundations_stability_governor_governordecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-77
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL37 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/federation/quorum_certificate.py:L75 :: federation_quorum_certificate_quorumcertificatebuilder`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:131:        "network_latency": network_latency(node, "gateway"),
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:5:Every trade/agent/job MUST pass through this gateway.
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:107:    gateway = ACOSSubmissionGateway()
    ```

### INFERRED #imports-78
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL3 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/rpc_server.py:L115 :: shared_rpc_server_rpcserver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-79
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L33 :: alignment_drift_detector_drifttype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #imports-80
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL29 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/branch.py:L25 :: alignment_branch_branchstatus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

---

## Bucket: relation = `imports_from` (81 edges)

### INFERRED #imports_from-1
- **Source:** `atom-federation-os/federation/tests/test_consensus_resolver.py:LL6 :: tests_test_consensus_resolver`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:162:        """With threshold=0.7, an identical feature vector must be filtered out.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:201:        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:217:        clone of the seed; orthogonal/zero-vector candidates survive because
    ```

### INFERRED #imports_from-2
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL27 :: alignment_merge_engine`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-3
- **Source:** `atom-federation-os/federation/policy_sync.py:LL23 :: federation_policy_sync`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:162:        """With threshold=0.7, an identical feature vector must be filtered out.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:201:        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:217:        clone of the seed; orthogonal/zero-vector candidates survive because
    ```

### INFERRED #imports_from-4
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL20 :: chaos_test_chaos`
- **Target:** `atom-federation-os/chaos/scenarios.py:L1 :: chaos_scenarios`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:48:    SCENARIO_MODULE_PREFIX = "load_test.scenarios"
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:57:            self.repo_root, "load_test", "scenarios",
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:276:    scenarios = [
    ```

### INFERRED #imports_from-5
- **Source:** `atom-federation-os/failure_replay/__init__.py:LL19 :: failure_replay_init`
- **Target:** `atom-federation-os/failure_replay/determinism_checker.py:L1 :: failure_replay_determinism_checker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:128:        checker = ExecutionSanityChecker(SanityConfig(max_slippage_bps=50.0))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:131:        result = checker.validate(order, market)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:136:        checker = ExecutionSanityChecker(SanityConfig(max_slippage_bps=50.0))
    ```

### INFERRED #imports_from-6
- **Source:** `atom-federation-os/observability/trace_ledger.py:LL9 :: observability_trace_ledger`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-7
- **Source:** `_sbs_old/tests/test_invariants.py:LL21 :: sbs_old_tests_test_invariants_py_tests_test_invariants`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L1 :: sbs_global_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports_from-8
- **Source:** `atom-federation-os/alignment/rollback_engine_v2.py:LL26 :: alignment_rollback_engine_v2`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-9
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL22 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:L1 :: agent_runtime_event_sourcing`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/adapters.py:30:    event log compatible with DESC event-sourcing layer.
    ```
    ```
    /home/workspace/_sbs_old/adapters.py:241:        Map DESC event-sourcing state → SBS canonical state.
    ```
    ```
    /home/workspace/_sbs_old/__init__.py:9:    [DESC] → event sourcing / audit trail
    ```

### INFERRED #imports_from-10
- **Source:** `atom-federation-os/failure_replay/__init__.py:LL25 :: failure_replay_init`
- **Target:** `atom-federation-os/failure_replay/event_store.py:L1 :: failure_replay_event_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/web/callbacks.py:676:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:719:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:737:        State("selected-strategy-store", "data"),
    ```

### INFERRED #imports_from-11
- **Source:** `atom-federation-os/core/federation/federated_gateway.py:LL32 :: federation_federated_gateway`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-12
- **Source:** `atom-federation-os/core/federation/quorum_certificate.py:LL16 :: federation_quorum_certificate`
- **Target:** `atom-federation-os/core/federation/consensus.py:L1 :: federation_consensus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_compromise_agent.py:95:    print("T2 OK | consensus LONG → abstains, reports dominant=BradleyAgent LONG@80")
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:112:    # T4 — strong consensus, no compromise
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:119:    print("T4 OK | consensus LONG → abstains, reports dominant=AstroCouncil LONG@85")
    ```

### INFERRED #imports_from-13
- **Source:** `atom-federation-os/core/proof/execution_request.py:LL10 :: proof_execution_request`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-14
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL5 :: alignment_test_adlr`
- **Target:** `atom-federation-os/alignment/adlr.py:L1 :: alignment_adlr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:82:            from alignment.adlr import ADLRecoveryOrchestrator, FailureReplay
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/adlr.py:1:"""adlr.py — v10.5 Anti-Deadlock Liveness Recovery Layer.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_adlr.py:5:from alignment.adlr import ADLRecoveryOrchestrator, OscillationMonitor, OscillationStage, RecoveryAction, RecoveryPolicy
    ```

### INFERRED #imports_from-15
- **Source:** `atom-federation-os/chaos/test_replay_validator.py:LL7 :: chaos_test_replay_validator`
- **Target:** `atom-federation-os/chaos/replay_validator.py:L1 :: chaos_replay_validator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports_from-16
- **Source:** `atom-federation-os/core/proof/proof_verifier.py:LL20 :: proof_proof_verifier`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-17
- **Source:** `atom-federation-os/chaos/harness.py:LL20 :: chaos_harness`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:93:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:94:    mod = importlib.util.module_from_spec(spec)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:179:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```

### INFERRED #imports_from-18
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL26 :: agent_runtime_app`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:L1 :: agent_runtime_task_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/web/callbacks.py:676:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:719:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:737:        State("selected-strategy-store", "data"),
    ```

### INFERRED #imports_from-19
- **Source:** `atom-federation-os/consistency_v2/test_rolling_state_diff.py:LL6 :: consistency_v2_test_rolling_state_diff`
- **Target:** `atom-federation-os/consistency_v2/rolling_state_diff.py:L1 :: consistency_v2_rolling_state_diff`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_ralph_safety.py:39:    # Симулируем вывод git diff --name-only с защищённым файлом
    ```
    ```
    /home/workspace/tests/test_kepler_property.py:291:    diff = abs(E - M) % 360.0
    ```
    ```
    /home/workspace/tests/test_kepler_property.py:292:    diff = min(diff, 360.0 - diff)
    ```

### INFERRED #imports_from-20
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL19 :: chaos_test_chaos`
- **Target:** `atom-federation-os/chaos/partitioner.py:L1 :: chaos_partitioner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/chaos/partitioner.py:10:    from chaos.partitioner import NetworkPartitioner
    ```
    ```
    /home/workspace/atom-federation-os/chaos/partitioner.py:220:        self.partitioner = NetworkPartitioner()
    ```
    ```
    /home/workspace/atom-federation-os/chaos/partitioner.py:249:                        ok = self.server.partitioner.block_ip(src, dst)
    ```

### INFERRED #imports_from-21
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL3 :: alignment_test_alignment`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L1 :: alignment_drift_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:165:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:249:        detector = ProofDriftDetector(severity_threshold=0.6)
    ```

### INFERRED #imports_from-22
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL18 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/circuit_breaker.py:L1 :: data_room_circuit_breaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/AsurDev/ml_engine/inference/ml_client.py:5:Includes circuit-breaker behaviour: on API error → falls back to 0.0.
    ```

### INFERRED #imports_from-23
- **Source:** `atom-federation-os/meta_control/persistence/state_window_store.py:LL10 :: persistence_state_window_store`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:131:        "network_latency": network_latency(node, "gateway"),
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:5:Every trade/agent/job MUST pass through this gateway.
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:107:    gateway = ACOSSubmissionGateway()
    ```

### INFERRED #imports_from-24
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL30 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/equivalence.py:L1 :: alignment_equivalence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/acos/scl_v6.py:221:        ("INV6: Cross-log equivalence", test_inv6),
    ```
    ```
    /home/workspace/AsurDev/acos/scl_v5.py:72:    """INV6: Replay equivalence — cross-Reducer determinism."""
    ```
    ```
    /home/workspace/AsurDev/acos/scl.py:36:    """INV3: Replay equivalence."""
    ```

### INFERRED #imports_from-25
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL11 :: consistency_test_cross_layer_invariant_engine`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L1 :: consistency_cross_layer_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports_from-26
- **Source:** `atom-federation-os/core/federation/consensus.py:LL14 :: federation_consensus`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-27
- **Source:** `atom-federation-os/federation/trust_weighted/trust_dynamics_stabilizer.py:LL35 :: trust_weighted_trust_dynamics_stabilizer`
- **Target:** `atom-federation-os/federation/trust_weighted/node_weights.py:L1 :: trust_weighted_node_weights`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:173:        before={"weights": {r.name: r.weight for r in roles}},
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:183:    # All weights should be halved
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:188:    print("  ✅ PASSED: OOSFailSwitch tightens policy (weights halved)")
    ```

### INFERRED #imports_from-28
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL11 :: tests_test_v68_coherence`
- **Target:** `atom-federation-os/coherence/invariant.py:L1 :: coherence_invariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/system_contract.py:38:    Each key is an invariant name; value must always be True in production.
    ```
    ```
    /home/workspace/_sbs_old/system_contract.py:64:        Verify a single invariant value against the contract.
    ```
    ```
    /home/workspace/_sbs_old/system_contract.py:115:        """Return all defined invariant names."""
    ```

### INFERRED #imports_from-29
- **Source:** `_sbs_old/__init__.py:LL21 :: sbs_old_init`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:93:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:94:    mod = importlib.util.module_from_spec(spec)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:179:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```

### INFERRED #imports_from-30
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL24 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room`
- **Target:** `data_room/observability.py:L1 :: data_room_observability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/observability/test_metrics.py:1:"""Smoke tests for observability/metrics.py."""
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:7:from observability.metrics import (
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:5:observability counter.
    ```

### INFERRED #imports_from-31
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL29 :: chaos_test_chaos`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L1 :: sbs_failure_classifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:226:        classifier = FailureClassifier()
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:233:        classifier = FailureClassifier()
    ```

### INFERRED #imports_from-32
- **Source:** `atom-federation-os/alignment/gcst.py:LL11 :: alignment_gcst`
- **Target:** `atom-federation-os/alignment/bcil.py:L1 :: alignment_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gcst.py:11:from alignment.bcil import BCIL
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gcst.py:37:        self.bcil = BCIL()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/bcil.py:1:"""bcil.py — v10.4 Byzantine-Convergence Integration Layer."""
    ```

### INFERRED #imports_from-33
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL24 :: agent_runtime_app`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/durable_queue.py:L1 :: agent_runtime_durable_queue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/monitoring/exporters/slurm/slurm_exporter.py:4:Exports: queue depth, node state, GPU allocation, job states
    ```
    ```
    /home/workspace/AsurDev/monitoring/exporters/slurm/slurm_exporter.py:71:    queue = get_slurm_queue()
    ```
    ```
    /home/workspace/AsurDev/monitoring/exporters/slurm/slurm_exporter.py:75:        "# HELP slurm_queue_total Total jobs in Slurm queue",
    ```

### INFERRED #imports_from-34
- **Source:** `_sbs_old/__init__.py:LL24 :: sbs_old_init`
- **Target:** `atom-federation-os/sbs/system_contract.py:L1 :: sbs_system_contract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:10:  - override contract (all 7 pairs survive end-to-end)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:84:         "reason": "core contract"},
    ```
    ```
    /home/workspace/tests/agent_test_base.py:18:    - When the contract changes, ONE place to update.
    ```

### INFERRED #imports_from-35
- **Source:** `atom-federation-os/alignment/mcpc.py:LL8 :: alignment_mcpc`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-36
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL21 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/dag_recorder.py:L1 :: agent_runtime_dag_recorder`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ete/replay/replay_engine.py:25:    def replay(self, trace_id: str, recorder) -> dict:
    ```
    ```
    /home/workspace/AsurDev/ete/replay/replay_engine.py:26:        trace = recorder.get(trace_id)
    ```
    ```
    /home/workspace/AsurDev/ete/replay/replay_engine.py:50:    def audit(self, trace_id: str, recorder) -> dict:
    ```

### INFERRED #imports_from-37
- **Source:** `atom-federation-os/chaos/__init__.py:LL19 :: chaos_init`
- **Target:** `atom-federation-os/chaos/validator.py:L1 :: chaos_validator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports_from-38
- **Source:** `atom-federation-os/persistence/stateful_recovery.py:LL11 :: persistence_stateful_recovery`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-39
- **Source:** `atom-federation-os/chaos/validator.py:LL32 :: chaos_validator`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L1 :: sbs_global_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports_from-40
- **Source:** `atom-federation-os/chaos/__init__.py:LL21 :: chaos_init`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:93:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:94:    mod = importlib.util.module_from_spec(spec)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:179:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```

### INFERRED #imports_from-41
- **Source:** `atom-federation-os/dag/test_fingerprint.py:LL6 :: dag_test_fingerprint`
- **Target:** `atom-federation-os/dag/fingerprint.py:L1 :: dag_fingerprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/plugins/plugin_api.py:85:    def fingerprint(self) -> str: return self._hash
    ```
    ```
    /home/workspace/roma-execution-bridge/plugins/plugin_runtime.py:107:        payload = {"batch_size": 8, "epochs": 10}; metadata = {}; fingerprint = "abc123"
    ```
    ```
    /home/workspace/roma-execution-bridge/plugins/plugin_runtime.py:119:                               'payload': {'model': 'llama3-8b'}, 'metadata': {}, 'fingerprint': 'x'})()
    ```

### INFERRED #imports_from-42
- **Source:** `atom-federation-os/meta_control/proof_feedback_controller.py:LL9 :: meta_control_proof_feedback_controller`
- **Target:** `atom-federation-os/proof/temporal_verifier.py:L1 :: proof_temporal_verifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/l11_verifier/verifier.py:156:    verifier = L11Verifier()
    ```
    ```
    /home/workspace/AsurDev/l11_verifier/verifier.py:158:    pre = verifier.pre_execution(dag, {"seed": 42})
    ```
    ```
    /home/workspace/AsurDev/l11_verifier/verifier.py:160:    print(f"Invariants: {verifier.verify_invariants()}")
    ```

### INFERRED #imports_from-43
- **Source:** `atom-federation-os/alignment/plan_reality_comparator.py:LL27 :: alignment_plan_reality_comparator`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-44
- **Source:** `atom-federation-os/alignment/convergence.py:LL9 :: alignment_convergence`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-45
- **Source:** `atom-federation-os/federation/bootstrap/node_runtime.py:LL32 :: bootstrap_node_runtime`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:162:        """With threshold=0.7, an identical feature vector must be filtered out.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:201:        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:217:        clone of the seed; orthogonal/zero-vector candidates survive because
    ```

### INFERRED #imports_from-46
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL2 :: alignment_test_rcf`
- **Target:** `atom-federation-os/alignment/rcf.py:L1 :: alignment_rcf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
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

### INFERRED #imports_from-47
- **Source:** `atom-federation-os/federation/gossip_protocol.py:LL16 :: federation_gossip_protocol`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:162:        """With threshold=0.7, an identical feature vector must be filtered out.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:201:        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:217:        clone of the seed; orthogonal/zero-vector candidates survive because
    ```

### INFERRED #imports_from-48
- **Source:** `atom-federation-os/coherence/__init__.py:LL15 :: coherence_init`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L1 :: coherence_temporal_smoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/agents/_impl/amre/lag_windowing.py:67:    EMA-based signal smoother with adaptive window size.
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/meta_rl/amre/lag_windowing.py:67:    EMA-based signal smoother with adaptive window size.
    ```
    ```
    /home/workspace/agents/_impl/amre/lag_windowing.py:69:    EMA-based signal smoother with adaptive window size.
    ```

### INFERRED #imports_from-49
- **Source:** `atom-federation-os/federation/tests/test_consensus_resolver.py:LL5 :: tests_test_consensus_resolver`
- **Target:** `atom-federation-os/federation/consensus_resolver.py:L1 :: federation_consensus_resolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/audit_repo/observability/metrics.py:74:        "Data Room resolver calls",
    ```

### INFERRED #imports_from-50
- **Source:** `atom-federation-os/meta_control/integration/test_integration.py:LL22 :: integration_test_integration`
- **Target:** `atom-federation-os/proof/stability_prover.py:L1 :: proof_stability_prover`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_proof_v76.py:126:        prover = DecisionProver()
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_proof_v76.py:136:        result = prover.prove(record)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_proof_v76.py:142:        prover = DecisionProver()
    ```

### INFERRED #imports_from-51
- **Source:** `_sbs_old/__init__.py:LL23 :: sbs_old_init`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L1 :: sbs_failure_classifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:226:        classifier = FailureClassifier()
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:233:        classifier = FailureClassifier()
    ```

### INFERRED #imports_from-52
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL13 :: alignment_test_alignment`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L1 :: alignment_rollback_engine_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/daily_digest/atom_proposer.py:231:            title="CrewAI v2.3 Integration для Agent Council",
    ```
    ```
    /home/workspace/knowledge/daily_digest/atom_proposer.py:233:            summary="CrewAI v2.3 представил hierarchical agent teams и flow visualization. "
    ```
    ```
    /home/workspace/data/market_adapter.py:226:        In production this hits POLYGON_API_BASE/v2/aggs/ticker/{symbol}/range/...
    ```

### INFERRED #imports_from-53
- **Source:** `atom-federation-os/swarm/worker_projection_engine.py:LL12 :: swarm_worker_projection_engine`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:131:        "network_latency": network_latency(node, "gateway"),
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:5:Every trade/agent/job MUST pass through this gateway.
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:107:    gateway = ACOSSubmissionGateway()
    ```

### INFERRED #imports_from-54
- **Source:** `atom-federation-os/orchestration/__init__.py:LL8 :: atom_federation_os_orchestration_init_py_orchestration_init`
- **Target:** `atom-federation-os/orchestration/control_arbitrator.py:L1 :: orchestration_control_arbitrator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/meta_control/__init__.py:7:    stability_weighted_arbitrator — arbitrator with stability-adjusted weights
    ```
    ```
    /home/workspace/atom-federation-os/meta_control/__init__.py:7:    stability_weighted_arbitrator — arbitrator with stability-adjusted weights
    ```

### INFERRED #imports_from-55
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL33 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:L1 :: agent_runtime_task_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/web/callbacks.py:676:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:719:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:737:        State("selected-strategy-store", "data"),
    ```

### INFERRED #imports_from-56
- **Source:** `atom-federation-os/federation/state_vector.py:LL9 :: federation_state_vector`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-57
- **Source:** `atom-federation-os/tests/test_v9_3_federation_binding.py:LL26 :: tests_test_v9_3_federation_binding`
- **Target:** `atom-federation-os/federation/proof_aware_consensus.py:L1 :: federation_proof_aware_consensus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_compromise_agent.py:95:    print("T2 OK | consensus LONG → abstains, reports dominant=BradleyAgent LONG@80")
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:112:    # T4 — strong consensus, no compromise
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:119:    print("T4 OK | consensus LONG → abstains, reports dominant=AstroCouncil LONG@85")
    ```

### INFERRED #imports_from-58
- **Source:** `atom-federation-os/cluster/node/node.py:LL24 :: node_node`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L1 :: sbs_global_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports_from-59
- **Source:** `atom-federation-os/federation/delta_gossip/consensus.py:LL25 :: delta_gossip_consensus`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:162:        """With threshold=0.7, an identical feature vector must be filtered out.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:201:        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:217:        clone of the seed; orthogonal/zero-vector candidates survive because
    ```

### INFERRED #imports_from-60
- **Source:** `atom-federation-os/orchestration/mutation_executor.py:LL38 :: orchestration_mutation_executor`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/auth/api_gateway.py:72:        """Decorator: apply gateway to handler."""
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/middleware.py:4:from saas.gateway.tenant_middleware import TenantMiddleware
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/middleware.py:5:from saas.gateway.auth_middleware import AuthMiddleware
    ```

### INFERRED #imports_from-61
- **Source:** `atom-federation-os/consistency_v2/test_streaming_invariant_engine.py:LL6 :: consistency_v2_test_streaming_invariant_engine`
- **Target:** `atom-federation-os/consistency_v2/streaming_invariant_engine.py:L1 :: consistency_v2_streaming_invariant_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #imports_from-62
- **Source:** `atom-federation-os/core/runtime/execution_context.py:LL20 :: runtime_execution_context`
- **Target:** `atom-federation-os/core/deterministic.py:L1 :: core_deterministic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:164:        We monkeypatch ``StrategyPool._chrom_to_vec`` to a deterministic mapper
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:17:  to keep the test fast and deterministic.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:43:    """200 deterministic OHLCV bars — enough for walk-forward + backtest."""
    ```

### INFERRED #imports_from-63
- **Source:** `_sbs_old/tests/test_invariants.py:LL23 :: sbs_old_tests_test_invariants_py_tests_test_invariants`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L1 :: sbs_failure_classifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:226:        classifier = FailureClassifier()
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:233:        classifier = FailureClassifier()
    ```

### INFERRED #imports_from-64
- **Source:** `atom-federation-os/consistency_v2/test_realtime_divergence_detector.py:LL6 :: consistency_v2_test_realtime_divergence_detector`
- **Target:** `atom-federation-os/consistency_v2/realtime_divergence_detector.py:L1 :: consistency_v2_realtime_divergence_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:165:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:249:        detector = ProofDriftDetector(severity_threshold=0.6)
    ```

### INFERRED #imports_from-65
- **Source:** `atom-federation-os/meta_control/integration/persistence_bridge.py:LL23 :: integration_persistence_bridge`
- **Target:** `atom-federation-os/meta_control/proof_feedback_controller.py:L1 :: meta_control_proof_feedback_controller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/admission_controller/__init__.py:1:from .controller import AdmissionController, AdmitDecision, AdmitResult
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:129:    controller = ProbabilisticAdmissionController(windows)
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:137:        controller.update("rtx-node", val)
    ```

### INFERRED #imports_from-66
- **Source:** `atom-federation-os/coherence/__init__.py:LL12 :: coherence_init`
- **Target:** `atom-federation-os/coherence/drift_controller.py:L1 :: coherence_drift_controller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:14:    """Check if Slurm controller is responsive."""
    ```
    ```
    /home/workspace/AsurDev/admission_controller/__init__.py:1:from .controller import AdmissionController, AdmitDecision, AdmitResult
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:129:    controller = ProbabilisticAdmissionController(windows)
    ```

### INFERRED #imports_from-67
- **Source:** `atom-federation-os/chaos/harness.py:LL329 :: chaos_harness`
- **Target:** `atom-federation-os/chaos/scenarios.py:L1 :: chaos_scenarios`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:48:    SCENARIO_MODULE_PREFIX = "load_test.scenarios"
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:57:            self.repo_root, "load_test", "scenarios",
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:276:    scenarios = [
    ```

### INFERRED #imports_from-68
- **Source:** `atom-federation-os/swarm/causal_merge_protocol.py:LL10 :: swarm_causal_merge_protocol`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:131:        "network_latency": network_latency(node, "gateway"),
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:5:Every trade/agent/job MUST pass through this gateway.
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:107:    gateway = ACOSSubmissionGateway()
    ```

### INFERRED #imports_from-69
- **Source:** `atom-federation-os/actuator/__init__.py:LL27 :: actuator_init`
- **Target:** `atom-federation-os/actuator/swarm_control_surface.py:L1 :: actuator_swarm_control_surface`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/acos/storage/schema.py:15:__all__ = ["TraceRecord"]  # preserve old public surface verbatim
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/meta_rl/reward/__init__.py:18:try:  # pragma: no cover - optional legacy surface
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/core_determinism/__init__.py:6:deterministic surface, and makes it possible to swap the underlying
    ```

### INFERRED #imports_from-70
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL19 :: tests_test_v68_coherence`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L1 :: coherence_temporal_smoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/agents/_impl/amre/lag_windowing.py:67:    EMA-based signal smoother with adaptive window size.
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/meta_rl/amre/lag_windowing.py:67:    EMA-based signal smoother with adaptive window size.
    ```
    ```
    /home/workspace/agents/_impl/amre/lag_windowing.py:69:    EMA-based signal smoother with adaptive window size.
    ```

### INFERRED #imports_from-71
- **Source:** `atom-federation-os/federation/consensus_resolver.py:LL10 :: federation_consensus_resolver`
- **Target:** `atom-federation-os/orchestration/execution_gateway.py:L1 :: orchestration_execution_gateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:131:        "network_latency": network_latency(node, "gateway"),
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:5:Every trade/agent/job MUST pass through this gateway.
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:107:    gateway = ACOSSubmissionGateway()
    ```

### INFERRED #imports_from-72
- **Source:** `atom-federation-os/federation/tests/test_policy_sync.py:LL9 :: tests_test_policy_sync`
- **Target:** `atom-federation-os/federation/state_vector.py:L1 :: federation_state_vector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:162:        """With threshold=0.7, an identical feature vector must be filtered out.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:201:        # Orthogonal candidate: zero-vector chromosome so cosine is 0.0.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:217:        clone of the seed; orthogonal/zero-vector candidates survive because
    ```

### INFERRED #imports_from-73
- **Source:** `_sbs_old/global_invariant_engine.py:LL22 :: sbs_old_global_invariant_engine`
- **Target:** `atom-federation-os/sbs/boundary_spec.py:L1 :: sbs_boundary_spec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:93:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:94:    mod = importlib.util.module_from_spec(spec)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:179:    spec = importlib.util.spec_from_file_location("infer_edges", INFER_EDGES)
    ```

### INFERRED #imports_from-74
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/engine.py:LL23 :: agent_runtime_engine`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_store.py:L1 :: agent_runtime_event_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/web/callbacks.py:676:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:719:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:737:        State("selected-strategy-store", "data"),
    ```

### INFERRED #imports_from-75
- **Source:** `atom-federation-os/federation/bootstrap/cluster_simulator.py:LL19 :: bootstrap_cluster_simulator`
- **Target:** `atom-federation-os/federation/consensus_resolver.py:L1 :: federation_consensus_resolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:2:Compromise Agent — explicit trade-off resolver for conflicting agent signals.
    ```

### INFERRED #imports_from-76
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL18 :: chaos_test_chaos`
- **Target:** `atom-federation-os/chaos/harness.py:L1 :: chaos_harness`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_compromise_agent.py:6:This is a runtime harness, not a normal pytest test: we need to stub
    ```
    ```
    /home/workspace/audit_repo/tests/test_compromise_agent.py:6:This is a runtime harness, not a normal pytest test: we need to stub
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/tests/test_compromise_agent.py:6:This is a runtime harness, not a normal pytest test: we need to stub
    ```

### INFERRED #imports_from-77
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL29 :: alignment_merge_engine`
- **Target:** `atom-federation-os/alignment/branch.py:L1 :: alignment_branch`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:9:  thresholds and the no-chromosome branch), ``top_k`` ranking after
    ```
    ```
    /home/workspace/AsurDev/v6/solver/ilp/or_ilp.py:3:ILP Solver — exact optimization via scipy minimize + branch-and-bound.
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/dag_retry.py:40:    PARTIAL_RECOMPUTE = "partial_recompute"  # reuse cached ancestors, recompute only failed branch
    ```

### INFERRED #imports_from-78
- **Source:** `atom-federation-os/federation/policy_sync.py:LL22 :: federation_policy_sync`
- **Target:** `atom-federation-os/federation/consensus_resolver.py:L1 :: federation_consensus_resolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:114:    """If primary resolver raises, blueprint tries the secondary."""
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:2:Compromise Agent — explicit trade-off resolver for conflicting agent signals.
    ```

### INFERRED #imports_from-79
- **Source:** `atom-federation-os/meta_control/integration/test_integration.py:LL23 :: integration_test_integration`
- **Target:** `atom-federation-os/proof/temporal_verifier.py:L1 :: proof_temporal_verifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/l11_verifier/verifier.py:156:    verifier = L11Verifier()
    ```
    ```
    /home/workspace/AsurDev/l11_verifier/verifier.py:158:    pre = verifier.pre_execution(dag, {"seed": 42})
    ```
    ```
    /home/workspace/AsurDev/l11_verifier/verifier.py:160:    print(f"Invariants: {verifier.verify_invariants()}")
    ```

### INFERRED #imports_from-80
- **Source:** `atom-federation-os/federation/byzantine/pbft_consensus.py:LL17 :: byzantine_pbft_consensus`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L1 :: byzantine_message_signatures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:123:    """Test that function signatures haven't changed."""
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:124:    print("\n[TEST 5] Function signatures unchanged...")
    ```
    ```
    /home/workspace/audit_repo/tests/test_dual_mode.py:122:    """Test that function signatures haven't changed."""
    ```

### INFERRED #imports_from-81
- **Source:** `atom-federation-os/chaos/validator.py:LL31 :: chaos_validator`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L1 :: sbs_failure_classifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:226:        classifier = FailureClassifier()
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:233:        classifier = FailureClassifier()
    ```

---

## Bucket: relation = `defines` (85 edges)

### INFERRED #defines-1
- **Source:** `atom-federation-os/pop-os-setup.sh:LL26 :: atom_federation_os_pop_os_setup`
- **Target:** `atom-federation-os/pop-os-setup.sh:L26 :: atom_federation_os_pop_os_setup_err`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_kepler_property.py:159:        err = abs(computed_period - elements.orbital_period) / elements.orbital_period
    ```
    ```
    /home/workspace/tests/test_kepler_property.py:160:        assert err < 0.001, (
    ```
    ```
    /home/workspace/tests/test_kepler_property.py:161:            f"{body}: P={computed_period:.2f} differs from stored P={elements.orbital_period} by {err * 100:.2f}%"
    ```

### INFERRED #defines-2
- **Source:** `home-cluster-iac/deploy_and_verify.sh:LL60 :: home_cluster_iac_deploy_and_verify`
- **Target:** `home-cluster-iac/deploy_and_verify.sh:L60 :: home_cluster_iac_deploy_and_verify_is_done`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/migrations/migrate.py:265:        help="Show what would be done without doing it",
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/migrations/migrate.py:265:        help="Show what would be done without doing it",
    ```
    ```
    /home/workspace/roma-execution-bridge/compiler/json_to_k8s.py:132:                "Entrypoint": dag[0]["command"] if dag else "echo done",
    ```

### INFERRED #defines-3
- **Source:** `AsurDev/scripts/test_suite.sh:LL346 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L346 :: asurdev_scripts_test_suite_sh_scripts_test_suite_run_all`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:97:        # Verify all expected keys exist
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:10:  - override contract (all 7 pairs survive end-to-end)
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:21:    """The template is hand-written to pass all 9 checks."""
    ```

### INFERRED #defines-4
- **Source:** `AsurDev/scripts/test_suite.sh:LL519 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L519 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l9`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/integrations/gitagent/tests/test_mcp_adapter.py:15:    """Test suite for MCPAdapter."""
    ```
    ```
    /home/workspace/atom-federation-os/chaos/test_chaos.py:2:pytest chaos test suite — v6.3 adversarial validation.
    ```
    ```
    /home/workspace/atom-federation-os/coherence/invariant.py:18:  - Offline: verified by test suite (S-CI verifier)
    ```

### INFERRED #defines-5
- **Source:** `AsurDev/scripts/test_suite.sh:LL33 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L33 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l1_network`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/adapters.py:181:        Map DRL network layer state → SBS canonical state.
    ```
    ```
    /home/workspace/_sbs_old/global_invariant_engine.py:95:            DRL layer state (network partitions, clock skew, causality markers)
    ```
    ```
    /home/workspace/_sbs_old/boundary_spec.py:36:        Maximum allowed network partitions before system halts.
    ```

### INFERRED #defines-6
- **Source:** `AsurDev/self_healing/health_check.sh:LL39 :: asurdev_self_healing_health_check_sh_self_healing_health_check`
- **Target:** `AsurDev/self_healing/health_check.sh:L39 :: asurdev_self_healing_health_check_sh_self_healing_health_check_check_ray`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/recovery.py:90:    _run(["ray", "stop"])
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/recovery.py:92:    ok, msg = _run(["ray", "start", "--head", "--port=6379", "--dashboard-host=0.0.0.0", "-f"])
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/recovery.py:94:        return True, "ray head started"
    ```

### INFERRED #defines-7
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL48 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L48 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_gen_keys`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:97:        # Verify all expected keys exist
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:114:        print(f"   All {len(expected_keys)} keys present ✓")
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:132:    params1 = list(sig1.parameters.keys())
    ```

### INFERRED #defines-8
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_command_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:22:        if os.path.exists(f):
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:26:        if os.path.exists(f):
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:53:    assert os.path.exists(TARGET_FILE), f"Агент не создал {TARGET_FILE}"
    ```

### INFERRED #defines-9
- **Source:** `AsurDev/self_healing/watchdog.sh:LL70 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L70 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_should_alert`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:3:Validate that all alert rules reference existing metrics.
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:56:            alert_name = rule.get("alert")
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:88:        print("OK: All alert metrics are known.")
    ```

### INFERRED #defines-10
- **Source:** `home-cluster-iac/deploy.sh:LL58 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L58 :: home_cluster_iac_deploy_log_step`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/optimize_lag_blend.py:16:        --blend-min 0.10 --blend-max 0.20 --blend-step 0.01 \
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:444:        "--blend-step",
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:447:        help=f"Blend step size. Default: {BLEND_STEP}.",
    ```

### INFERRED #defines-11
- **Source:** `engine_sandbox_runtime.sh:LL59 :: engine_sandbox_runtime`
- **Target:** `engine_sandbox_runtime.sh:L59 :: engine_sandbox_runtime_sandbox_network`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/adapters.py:181:        Map DRL network layer state → SBS canonical state.
    ```
    ```
    /home/workspace/_sbs_old/boundary_spec.py:36:        Maximum allowed network partitions before system halts.
    ```
    ```
    /home/workspace/_sbs_old/boundary_spec.py:68:            - partitions (int): number of detected network partitions
    ```

### INFERRED #defines-12
- **Source:** `AsurDev/scripts/day7-integration.sh:LL17 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L17 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agents_md.py:31:    assert "_archived" in content, "Should warn about archived modules"
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:21:Soft rules (warn, do not fail):
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:83:    def warn(self, file: str, line: int, rule: str, message: str) -> None:
    ```

### INFERRED #defines-13
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL37 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L37 :: atom_federation_os_pop_os_ai_dev_setup_stage1_preflight`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/middleware.py:27:    4. CORS                 — outermost, handles preflight
    ```

### INFERRED #defines-14
- **Source:** `AsurDev/scripts/test_suite.sh:LL20 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L20 :: asurdev_scripts_test_suite_sh_scripts_test_suite_pass`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:35:        f"linter should pass on template, got:\n{rc.stdout}\n{rc.stderr}"
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:68:    pass
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:84:    pass
    ```

### INFERRED #defines-15
- **Source:** `home-cluster-iac/deploy.sh:LL178 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L178 :: home_cluster_iac_deploy_troubleshoot`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_auth.py:11:from deploy.monitoring.health_endpoints import app as fastapi_app
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:11:from deploy.monitoring.health_endpoints import app
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:45:    alerts_path = Path(__file__).parent.parent / "deploy" / "monitoring" / "alerts.yml"
    ```

### INFERRED #defines-16
- **Source:** `AsurDev/self_healing/watchdog.sh:LL61 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L61 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_inc_failure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:38:    """Test that MASFactory failure triggers graceful fallback."""
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:42:        # Simulate MASFactory failure
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:124:            raise RuntimeError("simulated upstream failure")
    ```

### INFERRED #defines-17
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL28 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L28 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:356:    """Show detailed idea info."""
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker.py:302:    """Show detailed idea info."""
    ```

### INFERRED #defines-18
- **Source:** `home-cluster-iac/deploy_and_verify.sh:LL27 :: home_cluster_iac_deploy_and_verify`
- **Target:** `home-cluster-iac/deploy_and_verify.sh:L27 :: home_cluster_iac_deploy_and_verify_cleanup`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:19:def cleanup():
    ```
    ```
    /home/workspace/tests/test_phase1_cleanup.py:1:"""Phase 1 cleanup validation tests."""
    ```
    ```
    /home/workspace/audit_repo/tests/test_phase1_cleanup.py:1:"""Phase 1 cleanup validation tests."""
    ```

### INFERRED #defines-19
- **Source:** `AsurDev/self_healing/health_check.sh:LL20 :: asurdev_self_healing_health_check_sh_self_healing_health_check`
- **Target:** `AsurDev/self_healing/health_check.sh:L20 :: asurdev_self_healing_health_check_sh_self_healing_health_check_log`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:22:    assert captured.out, "No log output"
    ```
    ```
    /home/workspace/tests/test_logging.py:37:    assert captured.out, "No log output from orchestrator"
    ```
    ```
    /home/workspace/knowledge/daily_digest/cli.py:8:    log       — Show digest processing history
    ```

### INFERRED #defines-20
- **Source:** `home-cluster-iac/deploy.sh:LL163 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L163 :: home_cluster_iac_deploy_integration_test`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:170:    for test in tests:
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:172:            success = test()
    ```

### INFERRED #defines-21
- **Source:** `home-cluster-iac/deploy.sh:LL107 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L107 :: home_cluster_iac_deploy_day4`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_auth.py:11:from deploy.monitoring.health_endpoints import app as fastapi_app
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:11:from deploy.monitoring.health_endpoints import app
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:45:    alerts_path = Path(__file__).parent.parent / "deploy" / "monitoring" / "alerts.yml"
    ```

### INFERRED #defines-22
- **Source:** `home-cluster-iac/deploy.sh:LL62 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L62 :: home_cluster_iac_deploy_wait_ssh`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:63:    cmd = ["ssh", "-o", f"ConnectTimeout={timeout}", "-o", "StrictHostKeyChecking=no"]
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:116:    """Check if a node is reachable via TCP (ssh port check)."""
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/recovery.py:40:    ok, _ = _run(["ssh", node, "systemctl", "restart", "slurmd"])
    ```

### INFERRED #defines-23
- **Source:** `home-cluster-iac/deploy_and_verify.sh:LL22 :: home_cluster_iac_deploy_and_verify`
- **Target:** `home-cluster-iac/deploy_and_verify.sh:L22 :: home_cluster_iac_deploy_and_verify_error`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:39:    print("\n[TEST 2] MASFactory fallback on error...")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:195:    print("\n[TEST 4] Rollback on SwitchNode error")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```

### INFERRED #defines-24
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL144 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L144 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_cgroup_conf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:140:    # conf=0.7 — at boundary; per ADR-0004 T1 needs conf>=0.7, so uses=T1
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:96:        conf, pos, meta = agent._apply_lag_smoothing(90, 0.05)
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:98:        assert conf == 90
    ```

### INFERRED #defines-25
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL189 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L189 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_test_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/governance.py:130:                for kw in ['slurm','kubectl','ceph','docker','systemctl']:
    ```
    ```
    /home/workspace/AsurDev/tests/integration/test_ml_pipeline.py:49:      - 18 feature columns  (cpu, mem, gpu, disk, net, slurm, proc)
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/scheduler_v2.py:88:    """Submit job to selected partition via slurm wrapper."""
    ```

### INFERRED #defines-26
- **Source:** `AsurDev/scripts/test_suite.sh:LL23 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L23 :: asurdev_scripts_test_suite_sh_scripts_test_suite_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/observability/test_metrics.py:17:    record_data_room_resolve("price_resolver", "ok", 0.05)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:36:        ok, dd, msg = engine.check_kill_switch()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:37:        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
    ```

### INFERRED #defines-27
- **Source:** `atom-federation-os/build_push.sh:LL13 :: atom_federation_os_build_push`
- **Target:** `atom-federation-os/build_push.sh:L13 :: atom_federation_os_build_push_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:103:    logger.info(f"[Demo] Generated {n} rows, reversals in raw: {sum(np.abs(np.diff(np.sign(raw - 50))) > 0)}")
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:125:    logger.info(f"[Data] Loaded {len(df)} rows from {path}")
    ```

### INFERRED #defines-28
- **Source:** `AsurDev/self_healing/watchdog.sh:LL218 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L218 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_check_service`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/health_endpoints.py:135:        "service": "AstroFin Sentinel V5",
    ```
    ```
    /home/workspace/tools/metrics_server.py:17:OLLAMA_STATUS = Gauge("astrofin_ollama_status", "Ollama service status (1=healthy)")
    ```
    ```
    /home/workspace/audit_repo/tools/metrics_server.py:16:OLLAMA_STATUS = Gauge("astrofin_ollama_status", "Ollama service status (1=healthy)")
    ```

### INFERRED #defines-29
- **Source:** `home-cluster-iac/deploy_and_verify.sh:LL52 :: home_cluster_iac_deploy_and_verify`
- **Target:** `home-cluster-iac/deploy_and_verify.sh:L52 :: home_cluster_iac_deploy_and_verify_get_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:72:    # Speed-ups: skip Hyperopt warm-up and KARL state updates during the test.
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:37:    async def fake_run(state):
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:51:    def run(self, state):
    ```

### INFERRED #defines-30
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL216 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L216 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/daily_brief/daily_brief.py:187:def main():
    ```
    ```
    /home/workspace/knowledge/daily_brief/daily_brief.py:257:    main()
    ```
    ```
    /home/workspace/knowledge/daily_digest/cli.py:209:def main():
    ```

### INFERRED #defines-31
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agents_md.py:31:    assert "_archived" in content, "Should warn about archived modules"
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:21:Soft rules (warn, do not fail):
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:83:    def warn(self, file: str, line: int, rule: str, message: str) -> None:
    ```

### INFERRED #defines-32
- **Source:** `engine_sandbox_runtime.sh:LL109 :: engine_sandbox_runtime`
- **Target:** `engine_sandbox_runtime.sh:L109 :: engine_sandbox_runtime_sandbox_exec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:106:    exec(compile(src, str(INFER_EDGES), "exec"), mod.__dict__)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:183:    exec(compile(src, str(INFER_EDGES), "exec"), {"__name__": "infer_edges"})
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:308:    exec(compile(src, str(INFER_EDGES), "exec"), mod.__dict__)
    ```

### INFERRED #defines-33
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL152 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L152 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_mount_cephfs`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:7:  1.3 heartbeat_age replaced with explicit ceph health detail parsing
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:60:    Run ceph command via SSH. Reuses connection via explicit host param.
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:66:    cmd += ["ceph"] + args + ["--format=json"]
    ```

### INFERRED #defines-34
- **Source:** `atom-federation-os/scripts/bootstrap_env.sh:LL21 :: scripts_bootstrap_env`
- **Target:** `atom-federation-os/scripts/bootstrap_env.sh:L21 :: scripts_bootstrap_env_pythonpath`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/core/runtime/runtime_guard.py:568:        "pythonpath": os.environ.get("PYTHONPATH", ""),
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/core/runtime/runtime_guard.py:568:        "pythonpath": os.environ.get("PYTHONPATH", ""),
    ```
    ```
    /home/workspace/atom-federation-os/scripts/environment_hash.py:85:        "pythonpath": os.environ.get("PYTHONPATH", ""),
    ```

### INFERRED #defines-35
- **Source:** `AsurDev/self_healing/watchdog.sh:LL31 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L31 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_log_fail`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:42:    """If a module imports ephemeris but no method has @require_ephemeris, fail."""
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:105:    """When hard rules fail, the script returns non-zero."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:143:    """Test 3: OOS fail > 0.4 → tighten policy."""
    ```

### INFERRED #defines-36
- **Source:** `AsurDev/scripts/test_suite.sh:LL22 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L22 :: asurdev_scripts_test_suite_sh_scripts_test_suite_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/nightly_export.py:37:        logger.info(f"Top {len(top)} strategies in pool:")
    ```
    ```
    /home/workspace/tools/nightly_export.py:39:            logger.info(f"  {s.id}: reward={s.reward:.4f}")
    ```
    ```
    /home/workspace/tools/nightly_export.py:48:    logger.info(f"Starting nightly export daemon (poll={poll_seconds}s)")
    ```

### INFERRED #defines-37
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL662 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L662 :: atom_federation_os_pop_os_ai_dev_setup_stage17_minio`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

### INFERRED #defines-38
- **Source:** `AsurDev/self_healing/watchdog.sh:LL283 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L283 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_check_scheduler_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:21:    response = fastapi_client.get("/api/ab/compare")  # защищённый эндпоинт
    ```
    ```
    /home/workspace/tests/test_auth.py:27:    response = flask_client.get("/api/ab/compare")
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:20:    responses = [client.get("/api/ab/compare", headers=headers) for _ in range(11)]
    ```

### INFERRED #defines-39
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:356:    """Show detailed idea info."""
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker.py:302:    """Show detailed idea info."""
    ```

### INFERRED #defines-40
- **Source:** `engine_sandbox_runtime.sh:LL159 :: engine_sandbox_runtime`
- **Target:** `engine_sandbox_runtime.sh:L159 :: engine_sandbox_runtime_sandbox_validate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:131:        result = checker.validate(order, market)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:139:        result = checker.validate(order, market)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:148:        result = checker.validate(order, market)
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
    /home/workspace/tests/test_auth.py:11:from deploy.monitoring.health_endpoints import app as fastapi_app
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:11:from deploy.monitoring.health_endpoints import app
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:45:    alerts_path = Path(__file__).parent.parent / "deploy" / "monitoring" / "alerts.yml"
    ```

### INFERRED #defines-42
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL265 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L265 :: atom_federation_os_pop_os_ai_dev_setup_stage12_kde`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

### INFERRED #defines-43
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL429 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L429 :: atom_federation_os_pop_os_ai_dev_setup_stage15_longhorn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

### INFERRED #defines-44
- **Source:** `AsurDev/scripts/test_suite.sh:LL84 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L84 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l2_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/tests/integration/test_ml_pipeline.py:49:      - 18 feature columns  (cpu, mem, gpu, disk, net, slurm, proc)
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/scheduler_v2.py:88:    """Submit job to selected partition via slurm wrapper."""
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/scheduler.py:152:    "rtx-node":   {"ip": "10.20.20.10", "capabilities": ["gpu", "slurm", "ceph_osd", "ray_head"]},
    ```

### INFERRED #defines-45
- **Source:** `AsurDev/scripts/day7-integration.sh:LL59 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L59 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_setup_ceph_slurm_integration`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:1:"""tests/test_karl_synthesis_lag.py — ATOM-KARL-015 Phase 5: Tests for LagWindow integration in KARLSynthesisAgent
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:6:``tests/integration/test_evolution_pipeline.py``:
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:106:@pytest.mark.integration
    ```

### INFERRED #defines-46
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/tests/test_security_fixes.py:74:        self.assertIn("wg-quick", mgr._available_binaries())
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:103:        out = subprocess.check_output(["wg", "show", peer], timeout=5).decode()
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/recovery.py:115:    ok, msg = _run(["wg-quick", "down", interface])
    ```

### INFERRED #defines-47
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL854 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L854 :: atom_federation_os_pop_os_ai_dev_setup_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:91:    """Import infer_edges.py with REPO_ROOT monkey-patched, run main()."""
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:110:        mod.main()
    ```

### INFERRED #defines-48
- **Source:** `AsurDev/scripts/day3-compute.sh:LL54 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L54 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/connector.py:219:            "command": "echo 'ROM A GPU working!' && nvidia-smi --query-gpu=name --format=csv,noheader",
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/observability_fast.py:24:    return {"gpus": []}  # In production: nvidia-smi query
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/server.py:67:                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
    ```

### INFERRED #defines-49
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL60 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L60 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_deploy_ceph`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:7:  1.3 heartbeat_age replaced with explicit ceph health detail parsing
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:60:    Run ceph command via SSH. Reuses connection via explicit host param.
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:66:    cmd += ["ceph"] + args + ["--format=json"]
    ```

### INFERRED #defines-50
- **Source:** `AsurDev/self_healing/watchdog.sh:LL300 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L300 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:91:    """Import infer_edges.py with REPO_ROOT monkey-patched, run main()."""
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:110:        mod.main()
    ```

### INFERRED #defines-51
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL147 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L147 :: atom_federation_os_pop_os_ai_dev_setup_stage6_k3s`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/saas/arch.py:21:print("│ prod: k3s cluster on Hetzner / AWS GPU instances            │")
    ```

### INFERRED #defines-52
- **Source:** `AsurDev/self_healing/watchdog.sh:LL251 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L251 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_check_ceph_health`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:33:    response = fastapi_client.get("/health")
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:108:    health = m.health_check()
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:109:    assert health["good"]["status"] == "healthy"
    ```

### INFERRED #defines-53
- **Source:** `AsurDev/scripts/day7-integration.sh:LL124 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L124 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_setup_monitoring`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:11:from deploy.monitoring.health_endpoints import app as fastapi_app
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:11:from deploy.monitoring.health_endpoints import app
    ```
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:75:        "monitoring",
    ```

### INFERRED #defines-54
- **Source:** `AsurDev/self_healing/watchdog.sh:LL48 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog`
- **Target:** `AsurDev/self_healing/watchdog.sh:L48 :: asurdev_self_healing_watchdog_sh_self_healing_watchdog_save_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:117:        state = engine.get_state()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:118:        assert not math.isnan(state.total_equity)
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:37:    async def fake_run(state):
    ```

### INFERRED #defines-55
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL48 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L48 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_install_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/lccp_v12.py:120:        Node("rtx-node",0.85,0.75,0.60,["slurm","ceph"]),
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/scheduler_v2.py:88:    """Submit job to selected partition via slurm wrapper."""
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/scheduler.py:152:    "rtx-node":   {"ip": "10.20.20.10", "capabilities": ["gpu", "slurm", "ceph_osd", "ray_head"]},
    ```

### INFERRED #defines-56
- **Source:** `AsurDev/scripts/day6-ceph.sh:LL93 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph`
- **Target:** `AsurDev/scripts/day6-ceph.sh:L93 :: asurdev_scripts_day6_ceph_sh_scripts_day6_ceph_deploy_manual`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:17:    python knowledge/daily_brief/idea_tracker.py --add "text" --source manual --category GENERAL
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:389:    parser.add_argument("--source", type=str, default="manual", help="Source for --add")
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker.py:335:    parser.add_argument("--source", type=str, default="manual", help="Source for --add")
    ```

### INFERRED #defines-57
- **Source:** `AsurDev/scripts/day3-compute.sh:LL18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:103:    logger.info(f"[Demo] Generated {n} rows, reversals in raw: {sum(np.abs(np.diff(np.sign(raw - 50))) > 0)}")
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:125:    logger.info(f"[Data] Loaded {len(df)} rows from {path}")
    ```

### INFERRED #defines-58
- **Source:** `AsurDev/scripts/day7-integration.sh:LL352 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L352 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:91:    """Import infer_edges.py with REPO_ROOT monkey-patched, run main()."""
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:110:        mod.main()
    ```

### INFERRED #defines-59
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL532 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L532 :: atom_federation_os_pop_os_ai_dev_setup_stage16_rookceph`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

### INFERRED #defines-60
- **Source:** `atom-federation-os/pop-os-setup.sh:LL28 :: atom_federation_os_pop_os_setup`
- **Target:** `atom-federation-os/pop-os-setup.sh:L28 :: atom_federation_os_pop_os_setup_step`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/optimize_lag_blend.py:16:        --blend-min 0.10 --blend-max 0.20 --blend-step 0.01 \
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:444:        "--blend-step",
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:447:        help=f"Blend step size. Default: {BLEND_STEP}.",
    ```

### INFERRED #defines-61
- **Source:** `atom-federation-os/pop-os-setup.sh:LL25 :: atom_federation_os_pop_os_setup`
- **Target:** `atom-federation-os/pop-os-setup.sh:L25 :: atom_federation_os_pop_os_setup_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agents_md.py:31:    assert "_archived" in content, "Should warn about archived modules"
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:21:Soft rules (warn, do not fail):
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:83:    def warn(self, file: str, line: int, rule: str, message: str) -> None:
    ```

### INFERRED #defines-62
- **Source:** `AsurDev/scripts/day7-integration.sh:LL22 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L22 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_create_slurm_ray_bridge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:129:    "roma-execution-bridge/",
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:150:    "roma-execution-bridge":"roma-execution-bridge",
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/idea_buffer_integration.py:192:    ATOM-R-041 + ATOM-016 bridge:
    ```

### INFERRED #defines-63
- **Source:** `AsurDev/scripts/day3-compute.sh:LL25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_detect_os`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:8:import os
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:13:BENCHMARK_DIR = os.path.dirname(__file__)
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:14:TARGET_FILE = os.path.join(BENCHMARK_DIR, "_temp_add.py")
    ```

### INFERRED #defines-64
- **Source:** `engine_sandbox_runtime.sh:LL194 :: engine_sandbox_runtime`
- **Target:** `engine_sandbox_runtime.sh:L194 :: engine_sandbox_runtime_sandbox_cleanup`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:19:def cleanup():
    ```
    ```
    /home/workspace/tests/test_phase1_cleanup.py:1:"""Phase 1 cleanup validation tests."""
    ```
    ```
    /home/workspace/audit_repo/tests/test_phase1_cleanup.py:1:"""Phase 1 cleanup validation tests."""
    ```

### INFERRED #defines-65
- **Source:** `AsurDev/scripts/test_suite.sh:LL25 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L20 :: asurdev_scripts_test_suite_sh_scripts_test_suite_skip`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:5:pytestmark = pytest.mark.skip(reason="Requires external Ralph agent")
    ```
    ```
    /home/workspace/tests/test_auth.py:20:    pytest.skip("FastAPI metrics endpoint not yet implemented")
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:72:    # Speed-ups: skip Hyperopt warm-up and KARL state updates during the test.
    ```

### INFERRED #defines-66
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL255 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L255 :: atom_federation_os_pop_os_ai_dev_setup_stage11_monitoring`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:11:from deploy.monitoring.health_endpoints import app as fastapi_app
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:11:from deploy.monitoring.health_endpoints import app
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:45:    alerts_path = Path(__file__).parent.parent / "deploy" / "monitoring" / "alerts.yml"
    ```

### INFERRED #defines-67
- **Source:** `home-cluster-iac/deploy.sh:LL140 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L140 :: home_cluster_iac_deploy_monitor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/db_monitor.py:55:        print(f"  [monitor] {SNAPSHOT_TBL} not found — skipping snapshot")
    ```
    ```
    /home/workspace/tools/db_monitor.py:78:        print(f"  [monitor] snapshot failed: {e}")
    ```
    ```
    /home/workspace/tools/db_monitor.py:116:            print(f"  [monitor] trend query failed: {e}")
    ```

### INFERRED #defines-68
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL245 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L245 :: atom_federation_os_pop_os_ai_dev_setup_stage10_ai`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:130:    "local-ai-stack/",
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:151:    "local-ai-stack":       "local-ai-stack",
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/email/service.py:31:    from_email: str = "noreply@roma.ai"
    ```

### INFERRED #defines-69
- **Source:** `home-cluster-iac/deploy.sh:LL40 :: home_cluster_iac_deploy`
- **Target:** `home-cluster-iac/deploy.sh:L40 :: home_cluster_iac_deploy_is_skipped`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:212:        # Same instance added again — should be skipped
    ```
    ```
    /home/workspace/scripts/validate_agent.py:218:                     "skipped (template/archived file)")
    ```
    ```
    /home/workspace/knowledge/daily_brief/daily_brief.py:127:        skipped = 0
    ```

### INFERRED #defines-70
- **Source:** `AsurDev/scripts/day1-network.sh:LL33 :: asurdev_scripts_day1_network_sh_scripts_day1_network`
- **Target:** `AsurDev/scripts/day1-network.sh:L33 :: asurdev_scripts_day1_network_sh_scripts_day1_network_ros_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:21:    response = fastapi_client.get("/api/ab/compare")  # защищённый эндпоинт
    ```
    ```
    /home/workspace/tests/test_auth.py:27:    response = flask_client.get("/api/ab/compare")
    ```
    ```
    /home/workspace/tests/test_rate_limit.py:20:    responses = [client.get("/api/ab/compare", headers=headers) for _ in range(11)]
    ```

### INFERRED #defines-71
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/observability/test_metrics.py:17:    record_data_room_resolve("price_resolver", "ok", 0.05)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:36:        ok, dd, msg = engine.check_kill_switch()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:37:        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
    ```

### INFERRED #defines-72
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL181 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L181 :: atom_federation_os_pop_os_ai_dev_setup_stage8_zsh`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

### INFERRED #defines-73
- **Source:** `AsurDev/scripts/day3-compute.sh:LL40 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L40 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_common`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/orchestration/router.py:80:    # Symbol extraction (common crypto/ stock patterns)
    ```
    ```
    /home/workspace/common/interfaces.py:5:them for callers that still import from ``common.interfaces`` during
    ```
    ```
    /home/workspace/common/__init__.py:1:"""astrofin.common — DEPRECATED compatibility shim.
    ```

### INFERRED #defines-74
- **Source:** `AsurDev/scripts/day3-compute.sh:LL152 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L152 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_munge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:140:        reward = calc.compute(sample_evaluation_result)
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:147:        reward = calc.compute(r)
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:153:        reward = calc.compute(r)
    ```

### INFERRED #defines-75
- **Source:** `AsurDev/scripts/day3-compute.sh:LL113 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L113 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_python_ml`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrology/residual_model.py:92:    ml = ResidualModel(mode="ml")
    ```
    ```
    /home/workspace/astrology/residual_model.py:93:    print(f"\nML Model trained: {ml.is_trained()}")
    ```
    ```
    /home/workspace/audit_repo/core/residual_model.py:91:    ml = ResidualModel(mode="ml")
    ```

### INFERRED #defines-76
- **Source:** `AsurDev/scripts/day7-integration.sh:LL166 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration`
- **Target:** `AsurDev/scripts/day7-integration.sh:L166 :: asurdev_scripts_day7_integration_sh_scripts_day7_integration_create_ai_scheduler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/recall_test.py:24:  python3 graphify-out/recall_test.py --keyword scheduler
    ```
    ```
    /home/workspace/AsurDev/ete/gate/governance_gate.py:22:    Every DAG passes through here before hitting the scheduler.
    ```
    ```
    /home/workspace/AsurDev/ete/scheduler/adapter.py:12:        """Determine scheduler for job."""
    ```

### INFERRED #defines-77
- **Source:** `AsurDev/scripts/test_suite.sh:LL231 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L231 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l5_integration`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:1:"""tests/test_karl_synthesis_lag.py — ATOM-KARL-015 Phase 5: Tests for LagWindow integration in KARLSynthesisAgent
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:6:``tests/integration/test_evolution_pipeline.py``:
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:106:@pytest.mark.integration
    ```

### INFERRED #defines-78
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL50 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L50 :: atom_federation_os_pop_os_ai_dev_setup_stage2_update`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:18:    - When the contract changes, ONE place to update.
    ```
    ```
    /home/workspace/tests/agent_test_base.py:92:        state.update(self.happy_state_overrides)
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:20:    # With .env update
    ```

### INFERRED #defines-79
- **Source:** `home-cluster-iac/ansible/roles/self_healing/files/systemd_watchdog.sh:LL9 :: files_systemd_watchdog`
- **Target:** `home-cluster-iac/ansible/roles/self_healing/files/systemd_watchdog.sh:L9 :: files_systemd_watchdog_log`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:22:    assert captured.out, "No log output"
    ```
    ```
    /home/workspace/tests/test_logging.py:37:    assert captured.out, "No log output from orchestrator"
    ```
    ```
    /home/workspace/knowledge/daily_digest/cli.py:8:    log       — Show digest processing history
    ```

### INFERRED #defines-80
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL274 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L274 :: atom_federation_os_pop_os_ai_dev_setup_stage13_tailscale`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

### INFERRED #defines-81
- **Source:** `AsurDev/cluster_status.sh:LL15 :: asurdev_cluster_status`
- **Target:** `AsurDev/cluster_status.sh:L15 :: asurdev_cluster_status_check_port`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_metrics_cli.py:22:    assert "--port" in result.stdout, "Should have --port option"
    ```
    ```
    /home/workspace/scripts/validate_docker_security.py:56:                    errors.append(f"{svc_name}: port {port_str} is not bound to 127.0.0.1")
    ```
    ```
    /home/workspace/tools/healthcheck.py:58:        "port": 5432,
    ```

### INFERRED #defines-82
- **Source:** `engine_sandbox_runtime.sh:LL72 :: engine_sandbox_runtime`
- **Target:** `engine_sandbox_runtime.sh:L72 :: engine_sandbox_runtime_sandbox_pid`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:40:        pid = self.tracker.record_prediction(
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:45:        self.assertGreater(pid, 0)
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:46:        oid = self.tracker.record_outcome(pid, actual_label=1, pnl=1.5)
    ```

### INFERRED #defines-83
- **Source:** `AsurDev/scripts/day5-ray.sh:LL21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray`
- **Target:** `AsurDev/scripts/day5-ray.sh:L21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/observability/test_metrics.py:17:    record_data_room_resolve("price_resolver", "ok", 0.05)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:36:        ok, dd, msg = engine.check_kill_switch()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:37:        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
    ```

### INFERRED #defines-84
- **Source:** `AsurDev/scripts/test_suite.sh:LL188 :: asurdev_scripts_test_suite_sh_scripts_test_suite`
- **Target:** `AsurDev/scripts/test_suite.sh:L188 :: asurdev_scripts_test_suite_sh_scripts_test_suite_test_l4_ceph`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:7:  1.3 heartbeat_age replaced with explicit ceph health detail parsing
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:60:    Run ceph command via SSH. Reuses connection via explicit host param.
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:66:    cmd += ["ceph"] + args + ["--format=json"]
    ```

### INFERRED #defines-85
- **Source:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:LL23 :: atom_federation_os_pop_os_ai_dev_setup`
- **Target:** `atom-federation-os/Pop_OS_AI_Dev_Setup.sh:L23 :: atom_federation_os_pop_os_ai_dev_setup_logwarn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/app.py:43:# ── App setup ──────────────────────────────────────────────────────────────────
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/time_window_agent.py:160:            summary = "4H no clear setup"
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:139:    "pop-os-setup/",
    ```

---

## Bucket: relation = `rationale_for` (12 edges)

### INFERRED #rationale_for-1
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL54 :: contracts_trace_contract_rationale_54`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L53 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract_write`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:34:        f.write("""
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:58:    reward-shaped metrics so persistence has something meaningful to write.
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:147:        f.write(json.dumps(idea.to_dict(), ensure_ascii=False) + "\n")
    ```

### INFERRED #rationale_for-2
- **Source:** `AsurDev/acos/__init__.py:LL1 :: asurdev_acos_init_py_acos_init_rationale_1`
- **Target:** `AsurDev/acos/__init__.py:L1 :: asurdev_acos_init_py_acos_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #rationale_for-3
- **Source:** `AsurDev/acos/events/event.py:LL16 :: events_event_rationale_16`
- **Target:** `AsurDev/acos/events/event.py:L15 :: asurdev_acos_events_event_py_events_event_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/_sbs_old/failure_classifier.py:90:        Classify a single failure event.
    ```
    ```
    /home/workspace/_sbs_old/failure_classifier.py:95:            Raw failure event with at minimum:
    ```

### INFERRED #rationale_for-4
- **Source:** `AsurDev/acos/contracts/engine_contract.py:LL5 :: contracts_engine_contract_rationale_5`
- **Target:** `AsurDev/acos/contracts/engine_contract.py:L4 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:38:    assert add(2, 3) == 5
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:124:    print("\n[TEST 5] Function signatures unchanged...")
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:25:    assert elapsed["elapsed"] < 0.5
    ```

### INFERRED #rationale_for-5
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL62 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_rationale_62`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L61 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/knowledge/build_index.py:187:    query_vec = get_embedding(args.query)
    ```

### INFERRED #rationale_for-6
- **Source:** `AsurDev/acos/events/types.py:LL1 :: asurdev_acos_events_types_py_events_types_rationale_1`
- **Target:** `AsurDev/acos/events/types.py:L1 :: asurdev_acos_events_types_py_events_types`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_type_consolidation.py:11:    """Везде должен использоваться AgentResponse из core.base_agent, а не agents._impl.types."""
    ```
    ```
    /home/workspace/tests/test_type_consolidation.py:17:        if "from agents._impl.types import" in content or "import agents._impl.types" in content:
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:106:    """Wrong types in known fields must not raise."""
    ```

### INFERRED #rationale_for-7
- **Source:** `AsurDev/acos/contracts/scheduler_contract.py:LL12 :: contracts_scheduler_contract_rationale_12`
- **Target:** `AsurDev/acos/contracts/scheduler_contract.py:L11 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_schedulercontract_route`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:17:    @app.route("/protected")
    ```
    ```
    /home/workspace/tests/test_auth_empty_key.py:12:    @app.route("/test")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:11:    R4.  Any HTTP route handler under web/ must use @require_auth (or be
    ```

### INFERRED #rationale_for-8
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL43 :: contracts_trace_contract_rationale_43`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L42 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract_list_traces`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:13:    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    ```
    ```
    /home/workspace/AsurDev/tests/test_amneziawg_integration.py:222:    print(f"  [OK{'=' if ok else '!'}] INV6 — O(1) lookup: {elapsed:.4f}s for 1000 lookups (100 traces)")
    ```
    ```
    /home/workspace/AsurDev/ete/engine/execution_engine.py:22:        self.traces = {}
    ```

### INFERRED #rationale_for-9
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL51 :: contracts_trace_contract_rationale_51`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L50 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_deterministic_kernel.py:438:        for tick in range(1, 51):
    ```
    ```
    /home/workspace/atom-federation-os/resilience/tests/test_v67_meta_coherence.py:62:    aligner.observe({"cpu": 0.5}, {"cpu": 0.51})
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/resilience/tests/test_v67_meta_coherence.py:62:    aligner.observe({"cpu": 0.5}, {"cpu": 0.51})
    ```

### INFERRED #rationale_for-10
- **Source:** `AsurDev/acos.py:LL134 :: asurdev_acos_rationale_134`
- **Target:** `AsurDev/acos.py:L133 :: asurdev_acos_acosorchestrator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/astrology/vedic.py:215:    l = 134.9633964 + 477198.8675055 * T  # Mean anomaly
    ```
    ```
    /home/workspace/audit_repo/astrology/vedic.py:213:    l = 134.9633964 + 477198.8675055 * T  # Mean anomaly
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/astrology/vedic.py:213:    l = 134.9633964 + 477198.8675055 * T  # Mean anomaly
    ```

### INFERRED #rationale_for-11
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL66 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_rationale_66`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L65 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_validate_trace_recorder_contract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:10:  - override contract (all 7 pairs survive end-to-end)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:84:         "reason": "core contract"},
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:97:    # the contract is "do not raise".
    ```

### INFERRED #rationale_for-12
- **Source:** `AsurDev/acos/contracts/engine_contract.py:LL16 :: contracts_engine_contract_rationale_16`
- **Target:** `AsurDev/acos/contracts/engine_contract.py:L15 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_validate_engine_contract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:10:  - override contract (all 7 pairs survive end-to-end)
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:84:         "reason": "core contract"},
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:97:    # the contract is "do not raise".
    ```

---

## Bucket: relation = `inherits` (14 edges)

### INFERRED #inherits-1
- **Source:** `atom-federation-os/federation/byzantine/message_signatures.py:LL19 :: byzantine_message_signatures_messagesignatureerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-2
- **Source:** `atom-federation-os/core/runtime/dfa_execution_guard.py:LL92 :: runtime_dfa_execution_guard_invalidtransitionerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-3
- **Source:** `atom-federation-os/core/proof/proof_verifier.py:LL26 :: proof_proof_verifier_proofverificationerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-4
- **Source:** `push/agents/_impl/ephemeris_decorator.py:LL46 :: push_agents_impl_ephemeris_decorator_py_impl_ephemeris_decorator_ephemerisunavailableerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-5
- **Source:** `atom-federation-os/federation/security/inbound_security_gate.py:LL46 :: security_inbound_security_gate_securitygateerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-6
- **Source:** `roma-execution-bridge/saas_api/auth.py:LL12 :: saas_api_auth_ratelimitexceeded`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-7
- **Source:** `home-cluster-iac/l9_ebl/capabilities/registry.py:LL101 :: home_cluster_iac_l9_ebl_capabilities_registry_py_capabilities_registry_capabilitydenied`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-8
- **Source:** `atom-federation-os/core/economics/slashing_engine.py:LL43 :: economics_slashing_engine_economicsecurityviolation`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-9
- **Source:** `roma-execution-bridge/input_contract/__init__.py:LL10 :: input_contract_init_romavalidationerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-10
- **Source:** `data_room/circuit_breaker.py:LL100 :: data_room_circuit_breaker_circuitbreakeropen`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-11
- **Source:** `atom-federation-os/sbs/schema_validator.py:LL9 :: sbs_schema_validator_schemavalidationerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-12
- **Source:** `atom-federation-os/core/runtime/guard_policy.py:LL58 :: runtime_guard_policy_systemshutdown`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-13
- **Source:** `audit_repo/agents/_impl/ephemeris_decorator.py:LL46 :: audit_repo_agents_impl_ephemeris_decorator_py_impl_ephemeris_decorator_ephemerisunavailableerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

### INFERRED #inherits-14
- **Source:** `agents/_impl/ephemeris_decorator.py:LL46 :: agents_impl_ephemeris_decorator_py_impl_ephemeris_decorator_ephemerisunavailableerror`
- **Target:** `atom-federation-os/orchestration/v8_2b_controlled_autocorrection/mutation_executor.py:L212 :: atom_federation_os_orchestration_v8_2b_controlled_autocorrection_mutation_executor_py_exception`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:129:    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")
    ```

---

## Bucket: relation = `references` (70 edges)

### INFERRED #references-1
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL249 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_decide`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L15 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_fixtype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_030_stress_test.py:82:    # Test decide() - returns selected candidates
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_030_stress_test.py:83:    candidates = unc.decide(ctx_high)
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_030_stress_test.py:85:    print(f"  ✅ decide() returned: {candidates}")
    ```

### INFERRED #references-2
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL106 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator_validate_trace`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L29 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_contractviolation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:3:from opentelemetry import trace
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:6:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:7:from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    ```

### INFERRED #references-3
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL52 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L52 :: asurdev_execution_sandbox_sandbox_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-4
- **Source:** `AsurDev/l11_verifier/verifier.py:LL138 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_full_pipeline`
- **Target:** `AsurDev/l11_verifier/verifier.py:L69 :: asurdev_l11_verifier_verifier_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-5
- **Source:** `AsurDev/job_engine/engine.py:LL67 :: asurdev_job_engine_engine_py_job_engine_engine_jobeventhooks_on_failure`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ete/scheduler/adapter.py:11:    def route(self, job: dict) -> dict:
    ```
    ```
    /home/workspace/AsurDev/ete/scheduler/adapter.py:12:        """Determine scheduler for job."""
    ```
    ```
    /home/workspace/AsurDev/ete/scheduler/adapter.py:13:        jtype = job.get("type", "agent")
    ```

### INFERRED #references-6
- **Source:** `AsurDev/determinism_controller/controller.py:LL47 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_get_determinism_report`
- **Target:** `AsurDev/determinism_controller/controller.py:L47 :: asurdev_determinism_controller_controller_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-7
- **Source:** `AsurDev/job_engine/engine.py:LL164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:22:    """Map job/outcome string to label integer."""
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:49:        2. For each job outcome at time T, look ahead horizon_minutes
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:67:        """Load job events from state_store. Falls back to synthetic data."""
    ```

### INFERRED #references-8
- **Source:** `AsurDev/acos.py:LL308 :: asurdev_acos_acosgovernancekernel_analyze`
- **Target:** `AsurDev/acos.py:L285 :: asurdev_acos_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-9
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL46 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_check`
- **Target:** `AsurDev/l10_self_healing/watchdog/watchdog.py:L23 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdogresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:47:            # Import and check that fallback works
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:32:        capture_output=True, text=True, check=False,
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:79:    """Archived files are exempt from the inherit check."""
    ```

### INFERRED #references-10
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL90 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyblock_evaluate`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L28 :: asurdev_constraint_compiler_parser_parser_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-11
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL40 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_register_trigger`
- **Target:** `AsurDev/l10_self_healing/watchdog/watchdog.py:L40 :: asurdev_l10_self_healing_watchdog_watchdog_py_failuretrigger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:220:    # Try to apply invalid change (should trigger rollback)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:37:        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:45:        assert ok, f"Kill should NOT trigger at 6% DD, got dd={dd:.2%}"
    ```

### INFERRED #references-12
- **Source:** `AsurDev/acos/network/amnezia_patch.py:LL104 :: asurdev_acos_network_amnezia_patch_py_network_amnezia_patch_get_tunnel_metrics`
- **Target:** `AsurDev/acos/network/amnezia_patch.py:L104 :: asurdev_acos_network_amnezia_patch_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-13
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL95 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_can`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L11 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:79:        2. Select roles by capability matching
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:122:        # Step 3: Select roles by capability matching
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:273:        # Router → First tier (capability-matched agents)
    ```

### INFERRED #references-14
- **Source:** `AsurDev/astrofin/agents/registry.py:LL189 :: asurdev_astrofin_agents_registry_py_agents_registry_get_agent`
- **Target:** `AsurDev/astrofin/agents/registry.py:L11 :: asurdev_astrofin_agents_registry_py_agents_registry_agentspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:5:pytestmark = pytest.mark.skip(reason="Requires external Ralph agent")
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:104:            {"agent": "A", "signal": "LONG"},
    ```

### INFERRED #references-15
- **Source:** `AsurDev/ete/replay/replayer.py:LL83 :: asurdev_ete_replay_replayer_py_replay_replayer_correlationengine_init`
- **Target:** `AsurDev/ete/replay/replayer.py:L21 :: asurdev_ete_replay_replayer_py_tracestore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #references-16
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL109 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capabilitydenied_init`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L11 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:79:        2. Select roles by capability matching
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:122:        # Step 3: Select roles by capability matching
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:273:        # Router → First tier (capability-matched agents)
    ```

### INFERRED #references-17
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL180 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_summary`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L28 :: asurdev_constraint_compiler_parser_parser_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-18
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL115 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_create_from_state_store`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L49 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/backtest/metrics_agent.py:133:    """SQLite-backed metrics store for all backtest runs."""
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:676:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:719:        State("selected-strategy-store", "data"),
    ```

### INFERRED #references-19
- **Source:** `AsurDev/feature_pipeline/features.py:LL13 :: asurdev_feature_pipeline_features_py_feature_pipeline_features_feature_init`
- **Target:** `AsurDev/feature_pipeline/features.py:L13 :: asurdev_feature_pipeline_features_py_featurefunc`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #references-20
- **Source:** `AsurDev/feature_pipeline/embedding.py:LL57 :: asurdev_feature_pipeline_embedding_py_feature_pipeline_embedding_nodeembeddingbuilder_build_from_features`
- **Target:** `AsurDev/feature_pipeline/embedding.py:L24 :: asurdev_feature_pipeline_embedding_py_ndarray`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/rag_retriever.py:31:def _embed(text: str) -> np.ndarray:
    ```
    ```
    /home/workspace/audit_repo/training/train_residual_model.py:39:) -> tuple[np.ndarray, np.ndarray]:
    ```
    ```
    /home/workspace/audit_repo/meta_rl/strategy_pool.py:225:    def _chrom_to_vec(self, strategy: any) -> np.ndarray:
    ```

### INFERRED #references-21
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL108 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_node_metrics_prometheus`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L33 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_nodemetrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:39:    # Simple regex: match words that follow prometheus metric naming conventions
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_alerts_metrics.py:38:    # Simple regex: match words that follow prometheus metric naming conventions
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/builder.py:10:    builder = FeatureBuilder(backend='prometheus')    # DEV
    ```

### INFERRED #references-22
- **Source:** `AsurDev/ete/store/trace_store.py:LL35 :: asurdev_ete_store_trace_store_py_store_trace_store_tracenode_to_dict`
- **Target:** `AsurDev/ete/store/trace_store.py:L35 :: asurdev_ete_store_trace_store_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-23
- **Source:** `AsurDev/determinism_controller/controller.py:LL62 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_checkpoint_state`
- **Target:** `AsurDev/determinism_controller/controller.py:L47 :: asurdev_determinism_controller_controller_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-24
- **Source:** `AsurDev/acos/events/event_log.py:LL13 :: asurdev_acos_events_event_log_py_events_event_log_eventlog_append`
- **Target:** `AsurDev/acos/events/event_log.py:L13 :: asurdev_acos_events_event_log_py_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/audit_repo/tests/test_logging.py:18:    logger.info("Test event")
    ```
    ```
    /home/workspace/audit_repo/db/session.py:35:    from sqlalchemy import create_engine, event
    ```

### INFERRED #references-25
- **Source:** `AsurDev/astrofin/trace_schema/trace.py:LL73 :: asurdev_astrofin_trace_schema_trace_py_trace_schema_trace_trace_to_dict`
- **Target:** `AsurDev/astrofin/trace_schema/trace.py:L33 :: asurdev_astrofin_trace_schema_trace_py_trace_schema_trace_astrofintrace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:31:def _write_fake_report(edges: list[dict], target: Path) -> None:
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:90:def _run_infer_edges(workspace: Path, out: Path) -> dict:
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:116:def _read_enriched(path: Path) -> list[dict]:
    ```

### INFERRED #references-26
- **Source:** `AsurDev/ete/replay/replayer.py:LL102 :: asurdev_ete_replay_replayer_py_replay_replayer_correlationengine_find_divergence`
- **Target:** `AsurDev/ete/replay/replayer.py:L93 :: asurdev_ete_replay_replayer_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-27
- **Source:** `AsurDev/hash_chain/chain.py:LL38 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain_to_dict`
- **Target:** `AsurDev/hash_chain/chain.py:L19 :: asurdev_hash_chain_chain_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-28
- **Source:** `AsurDev/astrofin/agents/registry.py:LL193 :: asurdev_astrofin_agents_registry_py_agents_registry_list_agents`
- **Target:** `AsurDev/astrofin/agents/registry.py:L11 :: asurdev_astrofin_agents_registry_py_agents_registry_agentspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_type_consolidation.py:11:    """Везде должен использоваться AgentResponse из core.base_agent, а не agents._impl.types."""
    ```
    ```
    /home/workspace/tests/test_type_consolidation.py:17:        if "from agents._impl.types import" in content or "import agents._impl.types" in content:
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:31:        [sys.executable, str(LINTER), "agents/_impl/_template_agent.py"],
    ```

### INFERRED #references-29
- **Source:** `AsurDev/ete/replay/replayer.py:LL93 :: asurdev_ete_replay_replayer_py_replay_replayer_correlationengine_query_by_layer`
- **Target:** `AsurDev/ete/replay/replayer.py:L93 :: asurdev_ete_replay_replayer_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-30
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL168 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowengine_init`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L103 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowconfig`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #references-31
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL115 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_create_from_state_store`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L115 :: asurdev_admission_controller_probabilistic_py_statestore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:676:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:719:        State("selected-strategy-store", "data"),
    ```
    ```
    /home/workspace/audit_repo/web/callbacks.py:737:        State("selected-strategy-store", "data"),
    ```

### INFERRED #references-32
- **Source:** `AsurDev/l11_verifier/verifier.py:LL99 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_mid_execution`
- **Target:** `AsurDev/l11_verifier/verifier.py:L51 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_verificationreport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:20:from trading.execution.sanity import (
    ```
    ```
    /home/workspace/knowledge/daily_digest/atom_proposer.py:238:            project_context="Текущий Astro Council использует parallel agent execution. "
    ```
    ```
    /home/workspace/tools/metrics_server.py:25:    "astrofin_agent_duration_seconds", "Agent execution duration", buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
    ```

### INFERRED #references-33
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL98 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_check`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L11 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:79:        2. Select roles by capability matching
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:122:        # Step 3: Select roles by capability matching
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:273:        # Router → First tier (capability-matched agents)
    ```

### INFERRED #references-34
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL96 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L60 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctioncycleresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/registry.py:176:        name="cycle",
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_exporter.py:126:        "description": "Market cycle analysis: 20/40/80 day cycles, phase detection, turn points",
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/bradley_agent.py:187:        # Check Jupiter-Saturn aspect (major cycle)
    ```

### INFERRED #references-35
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL46 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator_validate_dag`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L29 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_contractviolation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/tests/test_security_fixes.py:25:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```
    ```
    /home/workspace/AsurDev/tests/test_security_fixes.py:45:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```
    ```
    /home/workspace/AsurDev/tests/test_security_fixes.py:50:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```

### INFERRED #references-36
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL128 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_slidingwindow_push`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L67 :: asurdev_feature_pipeline_window_engine_py_datetime`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_orchestrator.py:176:        from datetime import datetime
    ```
    ```
    /home/workspace/tests/test_orchestrator.py:178:        dt = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:3:from datetime import datetime, timezone
    ```

### INFERRED #references-37
- **Source:** `AsurDev/job_engine/engine.py:LL200 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_on_retry`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/observability.py:155:            # Check job failures
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/observability.py:202:    # Simulate job results
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/observability.py:203:    obs.record_job_result("job-001", "gpu-node-1", success=True, duration_ms=1200)
    ```

### INFERRED #references-38
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL162 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_route_job`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L78 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_scheduleresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:22:    """Map job/outcome string to label integer."""
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:49:        2. For each job outcome at time T, look ahead horizon_minutes
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:67:        """Load job events from state_store. Falls back to synthetic data."""
    ```

### INFERRED #references-39
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL319 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_act`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L47 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctiondecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/self_question.py:51:        "Is the regime stable enough to act on this signal?",
    ```
    ```
    /home/workspace/AsurDev/lccp_v12.py:96:        act = ctrl(issue)
    ```
    ```
    /home/workspace/AsurDev/lccp_v12.py:99:            results.append({"node":n.id,"issue":issue,"action":act,"gate":"REJECT_SCOPE","status":"BLOCKED"})
    ```

### INFERRED #references-40
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL249 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_decide`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L36 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionsignal`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_030_stress_test.py:82:    # Test decide() - returns selected candidates
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_030_stress_test.py:83:    candidates = unc.decide(ctx_high)
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_030_stress_test.py:85:    print(f"  ✅ decide() returned: {candidates}")
    ```

### INFERRED #references-41
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL76 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_default_fitness`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L16 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:12:  scored-strategy round-trip (``save_scored_strategy`` ↔
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:60:    strategy = _make_strategy(chromosome, generation=generation)
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:73:        strategy=strategy,
    ```

### INFERRED #references-42
- **Source:** `AsurDev/acos/events/event_log.py:LL28 :: asurdev_acos_events_event_log_py_events_event_log_eventlog_get_trace`
- **Target:** `AsurDev/acos/events/event_log.py:L13 :: asurdev_acos_events_event_log_py_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/audit_repo/tests/test_logging.py:18:    logger.info("Test event")
    ```
    ```
    /home/workspace/audit_repo/db/session.py:35:    from sqlalchemy import create_engine, event
    ```

### INFERRED #references-43
- **Source:** `AsurDev/hash_chain/chain.py:LL48 :: asurdev_hash_chain_chain_py_hash_chain_chain_compute_deterministic_hash`
- **Target:** `AsurDev/hash_chain/chain.py:L19 :: asurdev_hash_chain_chain_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-44
- **Source:** `AsurDev/acos/contracts/scheduler_contract.py:LL15 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_validate_scheduler_contract`
- **Target:** `AsurDev/acos/contracts/scheduler_contract.py:L15 :: asurdev_acos_contracts_scheduler_contract_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-45
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL224 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_run_full_correction_cycle`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L29 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/registry.py:176:        name="cycle",
    ```
    ```
    /home/workspace/audit_repo/meta_rl/basket.py:10:# F821 fix: keep StrategyEvaluator import out of cycle
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_exporter.py:126:        "description": "Market cycle analysis: 20/40/80 day cycles, phase detection, turn points",
    ```

### INFERRED #references-46
- **Source:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:LL88 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failureisolator_classify_incident`
- **Target:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:L41 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_incident`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/v8/safety_kernel/engine.py:88:            incident = self.incident_manager.create(
    ```
    ```
    /home/workspace/AsurDev/v8/safety_kernel/engine.py:117:            incident = self.incident_manager.create(
    ```
    ```
    /home/workspace/AsurDev/v8/rollback/engine.py:59:        - On incident: before recovery action
    ```

### INFERRED #references-47
- **Source:** `AsurDev/acos/storage/schema.py:LL9 :: asurdev_acos_storage_schema_py_storage_schema_utcnow`
- **Target:** `AsurDev/acos/storage/schema.py:L9 :: asurdev_acos_storage_schema_py_datetime`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_orchestrator.py:176:        from datetime import datetime
    ```
    ```
    /home/workspace/tests/test_orchestrator.py:178:        dt = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:3:from datetime import datetime, timezone
    ```

### INFERRED #references-48
- **Source:** `AsurDev/dag_validator/validator.py:LL114 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_check_deterministic_order`
- **Target:** `AsurDev/dag_validator/validator.py:L20 :: asurdev_dag_validator_validator_py_dag_validator_validator_violation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/architecture_linter.py:30:        1 — hard-rule violation
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:31:        2 — soft-rule violation only (still allowed in dev)
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:430:        print(RED(f"❌ {len(fails)} hard-rule violation(s). Build blocked."))
    ```

### INFERRED #references-49
- **Source:** `AsurDev/acos/storage/schema.py:LL36 :: asurdev_acos_storage_schema_py_storage_schema_tracerecord_from_dict`
- **Target:** `AsurDev/acos/storage/schema.py:L13 :: asurdev_acos_storage_schema_py_storage_schema_tracerecord`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:31:def _write_fake_report(edges: list[dict], target: Path) -> None:
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:90:def _run_infer_edges(workspace: Path, out: Path) -> dict:
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:116:def _read_enriched(path: Path) -> list[dict]:
    ```

### INFERRED #references-50
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL106 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_status`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L28 :: asurdev_acos_network_amnezia_wg_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-51
- **Source:** `AsurDev/ete/gate/governance_gate.py:LL28 :: asurdev_ete_gate_governance_gate_py_gate_governance_gate_governancegate_pre_check`
- **Target:** `AsurDev/ete/gate/governance_gate.py:L14 :: asurdev_ete_gate_governance_gate_py_gate_governance_gate_decision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:82:        "decision",
    ```
    ```
    /home/workspace/audit_repo/db/models.py:114:    """Vedic planetary positions at decision time."""
    ```
    ```
    /home/workspace/audit_repo/db/migrate_from_sqlite.py:67:                # Convert session to decision record format
    ```

### INFERRED #references-52
- **Source:** `AsurDev/job_engine/engine.py:LL142 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get_job`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/scheduler_v3/scorer.py:4:Reads job + node state from DB. Considers history + failure counts.
    ```
    ```
    /home/workspace/AsurDev/scheduler_v3/scorer.py:25:def score_and_select(job, state_store) -> Tuple[Optional[Any], List[Dict]]:
    ```
    ```
    /home/workspace/AsurDev/scheduler_v3/scorer.py:38:    job_type   = job.job_type if hasattr(job, "job_type") else job.get("job_type", "gpu")
    ```

### INFERRED #references-53
- **Source:** `AsurDev/dag_validator/validator.py:LL131 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_check_side_effects`
- **Target:** `AsurDev/dag_validator/validator.py:L20 :: asurdev_dag_validator_validator_py_dag_validator_validator_violation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/architecture_linter.py:30:        1 — hard-rule violation
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:31:        2 — soft-rule violation only (still allowed in dev)
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:430:        print(RED(f"❌ {len(fails)} hard-rule violation(s). Build blocked."))
    ```

### INFERRED #references-54
- **Source:** `AsurDev/job_engine/engine.py:LL151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Target:** `AsurDev/job_engine/engine.py:L46 :: asurdev_job_engine_engine_py_job_engine_engine_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:22:    """Map job/outcome string to label integer."""
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:49:        2. For each job outcome at time T, look ahead horizon_minutes
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:67:        """Load job events from state_store. Falls back to synthetic data."""
    ```

### INFERRED #references-55
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL79 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute_batch`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L26 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_sandboxresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/meta_rl/persistence.py:165:        """Save elite chromosomes (batch of save_scored_strategy)."""
    ```
    ```
    /home/workspace/audit_repo/core/reward_engine.py:96:        """Compute rewards for a batch of trades."""
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/exporter.py:190:        batch = self.build_dataset()
    ```

### INFERRED #references-56
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL97 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator_validate_event`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L46 :: asurdev_acos_validator_contract_validator_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-57
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL226 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_classify`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L15 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_fixtype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_orchestrator.py:18:    """Router must correctly classify queries."""
    ```
    ```
    /home/workspace/audit_repo/tests/test_orchestrator.py:16:    """Router must correctly classify queries."""
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```

### INFERRED #references-58
- **Source:** `AsurDev/acos.py:LL285 :: asurdev_acos_acosorchestrator_architecture_summary`
- **Target:** `AsurDev/acos.py:L285 :: asurdev_acos_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-59
- **Source:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:LL105 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failureisolator_plan_rollback`
- **Target:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:L25 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failuretrigger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:194:    """Test 4: Correct rollback when SwitchNode fails."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:220:    # Try to apply invalid change (should trigger rollback)
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```

### INFERRED #references-60
- **Source:** `AsurDev/acos.py:LL172 :: asurdev_acos_acosorchestrator_decision`
- **Target:** `AsurDev/acos.py:L124 :: asurdev_acos_acosdecisionresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:82:        "decision",
    ```
    ```
    /home/workspace/audit_repo/core/online_trainer.py:301:            decision = self.decide_position(ss, unc, astro, regime)
    ```
    ```
    /home/workspace/audit_repo/core/online_trainer.py:302:            pos = decision["position_pct"]
    ```

### INFERRED #references-61
- **Source:** `AsurDev/ete/store/trace_store.py:LL106 :: asurdev_ete_store_trace_store_py_store_trace_store_tracestore_add_node`
- **Target:** `AsurDev/ete/store/trace_store.py:L25 :: asurdev_ete_store_trace_store_py_store_trace_store_tracenode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:146:    """If a node is T3, decay must be forced to 0.05."""
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:12:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:14:        f"{node.module}.{alias.name}"
    ```

### INFERRED #references-62
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL97 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_get_label`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L97 :: asurdev_feature_pipeline_exporter_py_datetime`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/daily_digest/cli.py:21:from datetime import datetime
    ```
    ```
    /home/workspace/knowledge/daily_digest/cli.py:33:        date = args.date or datetime.now().strftime("%Y-%m-%d")
    ```
    ```
    /home/workspace/knowledge/daily_digest/cli.py:137:    print(f"  🔄 DAILY DIGEST PIPELINE — {args.date or datetime.now().strftime('%Y-%m-%d')}")
    ```

### INFERRED #references-63
- **Source:** `AsurDev/dag_validator/validator.py:LL106 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_check_dependency_closure`
- **Target:** `AsurDev/dag_validator/validator.py:L20 :: asurdev_dag_validator_validator_py_dag_validator_validator_violation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/architecture_linter.py:30:        1 — hard-rule violation
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:31:        2 — soft-rule violation only (still allowed in dev)
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:430:        print(RED(f"❌ {len(fails)} hard-rule violation(s). Build blocked."))
    ```

### INFERRED #references-64
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL119 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_any`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L75 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'executioncontext' not found in AsurDev/l9_ebl/capabilities/registry.py
    ```

### INFERRED #references-65
- **Source:** `AsurDev/acos.py:LL172 :: asurdev_acos_acosorchestrator_decision`
- **Target:** `AsurDev/acos.py:L115 :: asurdev_acos_acosdecisionrequest`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:82:        "decision",
    ```
    ```
    /home/workspace/audit_repo/trading/safety_gate.py:21:  decision = gate.check(signal, state)
    ```
    ```
    /home/workspace/audit_repo/db/models.py:114:    """Vedic planetary positions at decision time."""
    ```

### INFERRED #references-66
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL133 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_all`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L75 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:97:        # Verify all expected keys exist
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:10:  - override contract (all 7 pairs survive end-to-end)
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:21:    """The template is hand-written to pass all 9 checks."""
    ```

### INFERRED #references-67
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL103 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_add_constraint`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L31 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:24:    CONSTRAINT_VIOLATION = "constraint violation"
    ```

### INFERRED #references-68
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL58 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_constraint_to_dict`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L28 :: asurdev_constraint_compiler_parser_parser_py_any`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:37:    # We accept exit 0 in any case.
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:18:    - any agent-specific assertions
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:165:    # We allow any signal, but reasoning must remain under a sane size.
    ```

### INFERRED #references-69
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL234 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_build_astrofin_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L92 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:143:    """Test 3: OOS fail > 0.4 → tighten policy."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:144:    print("\n[TEST 3] OOSFailSwitch → tighten policy")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:169:    # Apply tighten policy
    ```

### INFERRED #references-70
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL226 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_classify`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L36 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionsignal`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_orchestrator.py:18:    """Router must correctly classify queries."""
    ```
    ```
    /home/workspace/audit_repo/tests/test_orchestrator.py:16:    """Router must correctly classify queries."""
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```

---

## Bucket: relation = `re_exports` (19 edges)

### INFERRED #re_exports-1
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL3 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/rpc_server.py:L1 :: shared_rpc_server`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:12:from web.wsgi import server as flask_app
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:4:from web.app import server
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:9:    server.config["TESTING"] = True
    ```

### INFERRED #re_exports-2
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL28 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/message_signatures.py:L1 :: byzantine_message_signatures`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:123:    """Test that function signatures haven't changed."""
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:124:    print("\n[TEST 5] Function signatures unchanged...")
    ```
    ```
    /home/workspace/audit_repo/tests/test_dual_mode.py:122:    """Test that function signatures haven't changed."""
    ```

### INFERRED #re_exports-3
- **Source:** `astrofin-sentinel-v5/db/__init__.py:LL12 :: astrofin_sentinel_v5_db_init_py_db_init`
- **Target:** `astrofin-sentinel-v5/db/init.py:L1 :: astrofin_sentinel_v5_db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #re_exports-4
- **Source:** `data_room/resolvers/__init__.py:LL13 :: resolvers_init`
- **Target:** `data_room/resolvers/base.py:L1 :: resolvers_base`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:4:Shared test base class for all AstroFin Sentinel V5 agents.
    ```
    ```
    /home/workspace/tests/agent_test_base.py:15:Why a base class and not a free function:
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:429:        help=f"LagWindow base window size. Default: {DEFAULT_WINDOW_SIZE}.",
    ```

### INFERRED #re_exports-5
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL4 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/models.py:L1 :: branding_models`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrology/residual_model.py:34:    MODEL_PATH = Path(__file__).parent.parent / "models" / "residual_model.joblib"
    ```
    ```
    /home/workspace/tools/healthcheck.py:70:            models = [m["name"] for m in data.get("models", [])]
    ```
    ```
    /home/workspace/tools/healthcheck.py:71:        return {"available": True, "models": models}
    ```

### INFERRED #re_exports-6
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL22 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/rollback_engine.py:L1 :: v8_2a_safety_foundations_rollback_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:33:        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:34:        engine.update_equity(100_000)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:35:        engine.update_equity(88_000)
    ```

### INFERRED #re_exports-7
- **Source:** `db/__init__.py:LL12 :: db_init_py_db_init`
- **Target:** `db/init.py:L1 :: db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #re_exports-8
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L1 :: alignment_drift_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:165:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_temporal_proof_v77.py:249:        detector = ProofDriftDetector(severity_threshold=0.6)
    ```

### INFERRED #re_exports-9
- **Source:** `atom-federation-os/rpc/__init__.py:LL33 :: rpc_init`
- **Target:** `atom-federation-os/rpc/adapter.py:L1 :: rpc_adapter`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:253:        GeneratedStrategy because the backtest adapter dispatches on
    ```
    ```
    /home/workspace/data/market_adapter.py:48:    """Multi-source market data adapter with fallback chain and caching."""
    ```
    ```
    /home/workspace/audit_repo/data/market_adapter.py:45:    """Multi-source market data adapter with fallback chain and caching."""
    ```

### INFERRED #re_exports-10
- **Source:** `atom-federation-os/rpc/__init__.py:LL37 :: rpc_init`
- **Target:** `atom-federation-os/rpc/server.py:L1 :: rpc_server`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:12:from web.wsgi import server as flask_app
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:4:from web.app import server
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:9:    server.config["TESTING"] = True
    ```

### INFERRED #re_exports-11
- **Source:** `atom-federation-os/alignment/__init__.py:LL33 :: alignment_init`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L1 :: alignment_rollback_engine_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/knowledge/daily_digest/atom_proposer.py:231:            title="CrewAI v2.3 Integration для Agent Council",
    ```
    ```
    /home/workspace/knowledge/daily_digest/atom_proposer.py:233:            summary="CrewAI v2.3 представил hierarchical agent teams и flow visualization. "
    ```
    ```
    /home/workspace/data/market_adapter.py:226:        In production this hits POLYGON_API_BASE/v2/aggs/ticker/{symbol}/range/...
    ```

### INFERRED #re_exports-12
- **Source:** `atom-federation-os/rpc/__init__.py:LL35 :: rpc_init`
- **Target:** `atom-federation-os/rpc/mesh.py:L1 :: rpc_mesh`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/v6/constraint_engine/engine.py:158:        """Check if node has lost connectivity to mesh."""
    ```
    ```
    /home/workspace/AsurDev/acos.py:40:  ├── WireGuard mesh (L0 network)
    ```
    ```
    /home/workspace/atom-federation-os/rpc/adapter.py:28:from .mesh import NodeMesh
    ```

### INFERRED #re_exports-13
- **Source:** `push/db/__init__.py:LL12 :: push_db_init_py_db_init`
- **Target:** `push/db/init.py:L1 :: push_db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    cross_submodule: push/db/__init__.py -> push/db/init.py
    ```

### INFERRED #re_exports-14
- **Source:** `roma-execution-bridge/saas/webhooks/__init__.py:LL1 :: webhooks_init`
- **Target:** `roma-execution-bridge/saas/webhooks/revenue_share.py:L1 :: webhooks_revenue_share`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/scheduler/gpu_policy_engine_v2.py:11:#   - Fair share scheduling (weighted by priority)
    ```
    ```
    /home/workspace/roma-execution-bridge/billing/ledger.py:102:# Revenue-share extension (dev helper only)
    ```
    ```
    /home/workspace/roma-execution-bridge/tests/test_revenue_share.py:60:    print("\n✅ All revenue-share tests passed")
    ```

### INFERRED #re_exports-15
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL5 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/service.py:L1 :: branding_service`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/metrics_server.py:17:OLLAMA_STATUS = Gauge("astrofin_ollama_status", "Ollama service status (1=healthy)")
    ```
    ```
    /home/workspace/health_endpoints.py:135:        "service": "AstroFin Sentinel V5",
    ```
    ```
    /home/workspace/audit_repo/tools/metrics_server.py:16:OLLAMA_STATUS = Gauge("astrofin_ollama_status", "Ollama service status (1=healthy)")
    ```

### INFERRED #re_exports-16
- **Source:** `atom-federation-os/orchestration/v8_2a_safety_foundations/__init__.py:LL23 :: v8_2a_safety_foundations_init`
- **Target:** `atom-federation-os/orchestration/v8_2a_safety_foundations/stability_governor.py:L1 :: v8_2a_safety_foundations_stability_governor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:175:                "file": "v7/policy_governor/governor.py",
    ```
    ```
    /home/workspace/AsurDev/acos.py:64:  ├── Policy governor
    ```
    ```
    /home/workspace/atom-federation-os/resilience/meta_coherence_controller.py:104:        self.governor = ObjectiveStabilityGovernor(mode=governor_mode)
    ```

### INFERRED #re_exports-17
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL31 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/view_change.py:L1 :: byzantine_view_change`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:53:    # Apply change
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:54:    change = TopologyChange.create(
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:68:    new_topo = updater.apply_change(change)
    ```

### INFERRED #re_exports-18
- **Source:** `atom-federation-os/rpc/__init__.py:LL34 :: rpc_init`
- **Target:** `atom-federation-os/rpc/client.py:L1 :: rpc_client`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:37:    client = app.test_client()
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:38:    resp = client.get("/protected", headers={"X-API-Key": "correct-key"})
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:54:    client = app.test_client()
    ```

### INFERRED #re_exports-19
- **Source:** `roma-execution-bridge/saas/branding/__init__.py:LL8 :: branding_init`
- **Target:** `roma-execution-bridge/saas/branding/cache.py:L1 :: branding_cache`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:43:            res1 = retriever.retrieve("cache test", domain="astrology", top_k=1)
    ```
    ```
    /home/workspace/tests/test_observability_rag_quality.py:44:            res2 = retriever.retrieve("cache test", domain="astrology", top_k=1)
    ```
    ```
    /home/workspace/tests/test_observability_faiss_cache.py:35:        # Первый вызов – cache miss
    ```

---

## Bucket: relation = `method` (7 edges)

### INFERRED #method-1
- **Source:** `AsurDev/acos/contracts/scheduler_contract.py:LL11 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_schedulercontract`
- **Target:** `AsurDev/acos/contracts/scheduler_contract.py:L11 :: asurdev_acos_contracts_scheduler_contract_py_contracts_scheduler_contract_schedulercontract_route`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:17:    @app.route("/protected")
    ```
    ```
    /home/workspace/tests/test_auth_empty_key.py:12:    @app.route("/test")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:11:    R4.  Any HTTP route handler under web/ must use @require_auth (or be
    ```

### INFERRED #method-2
- **Source:** `AsurDev/acos/contracts/engine_contract.py:LL7 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract`
- **Target:** `AsurDev/acos/contracts/engine_contract.py:L7 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract_execute`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/tools/db_monitor.py:30:                cur.execute("SELECT COUNT(*) FROM sessions")
    ```
    ```
    /home/workspace/tools/db_monitor.py:32:                cur.execute("SELECT COUNT(*) FROM backtest_runs")
    ```

### INFERRED #method-3
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL34 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L34 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract_record_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:3:from opentelemetry import trace
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:6:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:7:from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    ```

### INFERRED #method-4
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL38 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L38 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract_get_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:3:from opentelemetry import trace
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:6:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:7:from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    ```

### INFERRED #method-5
- **Source:** `AsurDev/acos/events/event.py:LL57 :: asurdev_acos_events_event_py_events_event_event`
- **Target:** `AsurDev/acos/events/event.py:L57 :: asurdev_acos_events_event_py_events_event_event_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:31:def _write_fake_report(edges: list[dict], target: Path) -> None:
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:90:def _run_infer_edges(workspace: Path, out: Path) -> dict:
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:116:def _read_enriched(path: Path) -> list[dict]:
    ```

### INFERRED #method-6
- **Source:** `AsurDev/acos.py:LL308 :: asurdev_acos_acosgovernancekernel`
- **Target:** `AsurDev/acos.py:L308 :: asurdev_acos_acosgovernancekernel_analyze`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:123:        async def analyze(self, state):
    ```
    ```
    /home/workspace/tests/test_macro_agent.py:88:        # Вызываем analyze синхронно, так как без моков RAG не вызовется
    ```

### INFERRED #method-7
- **Source:** `AsurDev/acos/contracts/engine_contract.py:LL11 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract`
- **Target:** `AsurDev/acos/contracts/engine_contract.py:L11 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract_get_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:51:    def run(self, state):
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:112:    def run(self, state):
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:52:    async def run(self, state):
    ```

---

## Bucket: relation = `calls` (84 edges)

### INFERRED #calls-1
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL139 :: consistency_test_cross_layer_invariant_engine_testcausaldag_test_is_identical_true`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L79 :: consistency_cross_layer_invariant_engine_causaldag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:28:    monkeypatch.setenv("REQUIRE_AUTH", "true")
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:46:    monkeypatch.setenv("REQUIRE_AUTH", "true")
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:63:    monkeypatch.setenv("REQUIRE_AUTH", "true")
    ```

### INFERRED #calls-2
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL258 :: chaos_test_chaos_testnetworkpartitioner_test_partitioner_partition_nodes`
- **Target:** `atom-federation-os/chaos/partitioner.py:L28 :: chaos_partitioner_networkpartitioner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:48:        "nodes": [
    ```
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:34:        # Add roles as nodes
    ```
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:41:        # Add switch nodes
    ```

### INFERRED #calls-3
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL152 :: alignment_test_rcf_test_rcf_boundary_44_unstable`
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

### INFERRED #calls-4
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL278 :: tests_test_v68_coherence_test_sci_lattice_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:29:    with pytest.raises(RuntimeError):
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:190:    with pytest.raises(ValueError):
    ```

### INFERRED #calls-5
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL118 :: resilience_meta_coherence_controller_metacoherencecontroller_init`
- **Target:** `atom-federation-os/coherence/objective_stabilizer.py:L102 :: coherence_objective_stabilizer_globalobjectivestabilizer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-6
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL337 :: tests_test_v68_coherence_test_sci_convergence_window`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:63:        "count": 25,  # mature window
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:15:        --window 50 \
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:219:        window = LagWindow(
    ```

### INFERRED #calls-7
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL145 :: alignment_test_gcpl_test_termination_terminal_leaves`
- **Target:** `atom-federation-os/alignment/gcpl.py:L303 :: alignment_gcpl_terminationprover`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gcpl.py:347:                details=f"|B|={recent_b[0]} stable, oscillation_free: terminal leaves",
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/equivalence.py:25:    SPLIT = auto()       # irreconcilable → both become terminal leaves
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/federation/delta_gossip/anti_entropy.py:74:        # Layer 0: leaves — store mode in each node
    ```

### INFERRED #calls-8
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL68 :: alignment_test_adlr_test_orch_terminal`
- **Target:** `atom-federation-os/alignment/adlr.py:L241 :: alignment_adlr_adlrecoveryorchestrator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos/cli/monitor.py:18:    "grafatui": {"port": None, "url": "terminal", "label": "Grafatui Terminal"},
    ```
    ```
    /home/workspace/AsurDev/acos/cli/monitor.py:69:            icon, status = "⚠️ ", "terminal"
    ```
    ```
    /home/workspace/atom-federation-os/formal/dfa_gateway.py:129:        "dfa": "Only terminal states: S11 (accept) or SR (reject)",
    ```

### INFERRED #calls-9
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL89 :: alignment_test_alignment_test_l3_semantic`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L321 :: alignment_drift_detector_semanticfidelitydetector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_validator.py:267:                    "description": "Agent with invalid version format for semantic versioning",
    ```
    ```
    /home/workspace/knowledge/rag_retriever.py:4:FAISS-backed semantic search with Ollama embeddings.
    ```
    ```
    /home/workspace/knowledge/rag_retriever.py:191:    Agent tool: semantic search over the knowledge base.
    ```

### INFERRED #calls-10
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL224 :: tests_test_v68_coherence_test_stabilizer_summary`
- **Target:** `atom-federation-os/coherence/objective_stabilizer.py:L102 :: coherence_objective_stabilizer_globalobjectivestabilizer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:33:    lines = ["# VALIDATION_REPORT.md", "", "**Verdict summary**", "", "---", ""]
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:295:    """--fmt json writes a JSON summary with tier_counts."""
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:309:    out_json = tmp_path / "summary.json"
    ```

### INFERRED #calls-11
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL216 :: tests_test_stability_feedback_controller_testapplygaintocommands_test_noop_when_apply_false`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:106:    """When REQUIRE_AUTH=false, all requests should succeed."""
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:107:    monkeypatch.setenv("REQUIRE_AUTH", "false")
    ```
    ```
    /home/workspace/tests/test_risk_integration.py:190:        """SAFETY_STACK_ENABLED=false → APPROVED regardless."""
    ```

### INFERRED #calls-12
- **Source:** `AsurDev/lccp_v12.py:LL138 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L51 :: asurdev_lccp_v12_staterebuilder_verify`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:21:        # Just verify the function signature and it doesn't crash
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:3:These tests verify authentication behavior including edge cases.
    ```

### INFERRED #calls-13
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL264 :: tests_test_v68_coherence_test_sci_coherence_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:29:    with pytest.raises(RuntimeError):
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:190:    with pytest.raises(ValueError):
    ```

### INFERRED #calls-14
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL157 :: alignment_test_gcpl_test_termination_deadlock`
- **Target:** `atom-federation-os/alignment/gcpl.py:L303 :: alignment_gcpl_terminationprover`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_execution_gateway.py:6:# 3. SQLite WAL + deferred isolation — no deadlock
    ```

### INFERRED #calls-15
- **Source:** `atom-federation-os/chaos/validator.py:LL100 :: chaos_validator_chaosvalidator_init`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L81 :: sbs_failure_classifier_failureclassifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-16
- **Source:** `atom-federation-os/chaos/harness.py:LL138 :: chaos_harness_chaosharness_init`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L62 :: sbs_global_invariant_engine_globalinvariantengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-17
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL254 :: tests_test_stability_feedback_controller_testapplygaintocommands_test_multiple_commands`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L49 :: actuator_stability_feedback_controller_gainadjustment`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker.py:434:    print("\nUse --help for commands.")
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:488:    print("\nUse --help for commands.")
    ```
    ```
    /home/workspace/audit_repo/orchestration/karl_cli.py:154:    """Prometheus /metrics server commands."""
    ```

### INFERRED #calls-18
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL133 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L101 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ray_active_workers`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:102:    """Ray active workers"""
    ```
    ```
    /home/workspace/roma-execution-bridge/scheduler/roma_scheduler.py:3:Routes jobs to GPU workers based on cost/performance policy."""
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/run.py:37:    workers = _worker_reg.list_all()
    ```

### INFERRED #calls-19
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL328 :: tests_test_stability_feedback_controller_testdampingbounds_test_damping_never_above_max`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:342:        assert injected >= 3  # max(5, 12 // 4) = 5
    ```
    ```
    /home/workspace/tests/test_market_adapter.py:9:  - Каждая свеча валидна: high >= max(open, close), low <= min(open, close)
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:16:        --blend-min 0.10 --blend-max 0.20 --blend-step 0.01 \
    ```

### INFERRED #calls-20
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL291 :: chaos_test_chaos_testintegration_test_byzantine_injection_detected`
- **Target:** `atom-federation-os/chaos/harness.py:L126 :: chaos_harness_chaosharness`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:87:    """Test 2: bias detected → adds Critic role."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:100:    # Bias detected context
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:122:        reason=f"Switch {switch.id}: bias detected",
    ```

### INFERRED #calls-21
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL103 :: tests_test_stability_feedback_controller_testoscillationdetection_test_undershoot_counting`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_exporter.py:196:        "description": "Elliott Wave analysis for wave counting and trend prediction",
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/elliot_agent.py:127:        Simplified wave counting.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/elliot_agent.py:157:        # Simplified wave counting
    ```

### INFERRED #calls-22
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL70 :: tests_test_v68_coherence_test_drift_force_correction`
- **Target:** `atom-federation-os/coherence/drift_controller.py:L85 :: coherence_drift_controller_driftcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/astrology/vedic.py:221:    # Sidereal correction (ayanamsa ~ 24° in 2026)
    ```
    ```
    /home/workspace/audit_repo/astrology/vedic.py:219:    # Sidereal correction (ayanamsa ~ 24° in 2026)
    ```
    ```
    /home/workspace/audit_repo/core/kepler_hybrid.py:4:Kepler orbital model backed by ML residual correction.
    ```

### INFERRED #calls-23
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL161 :: alignment_test_alignment_test_rollback_decider`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L134 :: alignment_rollback_engine_v2_rollbackplanner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:160:    decider = RollbackDecider()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:168:    scope_ok = decider.decide(bind_ok, rep_ok)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:170:    print(f"  decider OK→noop: type={scope_ok.rollback_type.name} ✅")
    ```

### INFERRED #calls-24
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL113 :: alignment_test_gcpl_test_checker_irreconcilable_ratio`
- **Target:** `atom-federation-os/alignment/gcpl.py:L192 :: alignment_gcpl_globalconsistencychecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:164:    Compute Sharpe ratio if PnL column is available.
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:47:        """Quorum ratio below threshold must fail."""
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:55:        """Quorum ratio at exact threshold should pass."""
    ```

### INFERRED #calls-25
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL235 :: tests_test_v68_coherence_test_sci_stable_passes`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:306:        """Empty pool ⇒ no comparison baseline ⇒ every candidate passes."""
    ```
    ```
    /home/workspace/graphify-out/select_top_inferred.py:101:                    help="Absolute ceiling per relation across ALL passes (default: 200). "
    ```
    ```
    /home/workspace/graphify-out/select_top_inferred.py:169:            # Hard cap is absolute across ALL passes; soft cap is per-pass.
    ```

### INFERRED #calls-26
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL253 :: chaos_test_chaos_testnetworkpartitioner_test_partitioner_block_ip_dry_run`
- **Target:** `atom-federation-os/chaos/partitioner.py:L28 :: chaos_partitioner_networkpartitioner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:33:    return asyncio.run(run_test())
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:52:    return asyncio.run(run_test())
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:118:    return asyncio.run(run_test())
    ```

### INFERRED #calls-27
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL264 :: chaos_test_chaos_testnetworkpartitioner_test_partitioner_restore_all_dry_run`
- **Target:** `atom-federation-os/chaos/partitioner.py:L28 :: chaos_partitioner_networkpartitioner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:33:    return asyncio.run(run_test())
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:52:    return asyncio.run(run_test())
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:118:    return asyncio.run(run_test())
    ```

### INFERRED #calls-28
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL189 :: tests_test_stability_feedback_controller_testadaptivegainrestoration_test_gain_reduces_when_oscillating`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/core/reward/test_reward.py:36:        """Oscillating values should NOT produce oscillating EMA."""
    ```
    ```
    /home/workspace/audit_repo/core/reward/test_reward.py:41:        assert abs(smoothed[-1]) < 1.0, f"EMA oscillating! last={smoothed[-1]}"
    ```
    ```
    /home/workspace/AsurDev/load_test/scenarios/policy_oscillation/test.py:125:        """Simulate a policy decision with oscillating behavior."""
    ```

### INFERRED #calls-29
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL36 :: alignment_test_gcpl_test_edit_distance_disjoint`
- **Target:** `atom-federation-os/alignment/gcpl.py:L89 :: alignment_gcpl_causal_edit_distance`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/meta_rl/live_data.py:295:        # ATR-based stop distance
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:126:        # stop_distance_pct (≈ loss) and a 2R target distance (≈ gain).
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/fundamental_agent.py:185:        # ATH distance bonus
    ```

### INFERRED #calls-30
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL75 :: chaos_test_chaos_validator`
- **Target:** `atom-federation-os/chaos/validator.py:L69 :: chaos_validator_chaosvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #calls-31
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL46 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_short_circuits_when_open`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:33:    with open(TEST_FILE, "w") as f:
    ```
    ```
    /home/workspace/tests/test_bull_researcher_async.py:34:        # Проверяем структуру: [open, high, low, close, volume]
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:53:    # Now open. Next call should NOT invoke the function.
    ```

### INFERRED #calls-32
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL120 :: consistency_test_cross_layer_invariant_engine_testcausaldag_test_add_and_retrieve_parents`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L79 :: consistency_cross_layer_invariant_engine_causaldag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:21:REPO_ROOT = Path(__file__).resolve().parents[2]
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:27:REPO_ROOT = Path(__file__).resolve().parents[2]
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:14:REPO_ROOT = Path(__file__).resolve().parents[2]
    ```

### INFERRED #calls-33
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL122 :: tests_test_v68_coherence_test_smoother_adaptive_window_calm`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L71 :: coherence_temporal_smoother_temporalcoherencesmoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/core/volatility.py:38:    LOW = "LOW"  # σ < 1.5%  — calm market
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/astrology/volatility.py:38:    LOW = "LOW"  # σ < 1.5%  — calm market
    ```
    ```
    /home/workspace/core/volatility.py:39:    LOW = "LOW"  # σ < 1.5%  — calm market
    ```

### INFERRED #calls-34
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL17 :: alignment_test_adlr_test_oscillation_change`
- **Target:** `atom-federation-os/alignment/adlr.py:L112 :: alignment_adlr_oscillationmonitor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:53:    # Apply change
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:54:    change = TopologyChange.create(
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:68:    new_topo = updater.apply_change(change)
    ```

### INFERRED #calls-35
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL181 :: tests_test_stability_feedback_controller_testadaptivegainrestoration_test_gain_caps_at_1_0`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/backtest/test_metrics_agent.py:45:        win_rate=60.0,
    ```
    ```
    /home/workspace/backtest/test_metrics_agent.py:50:        avg_win_pct=3.0,
    ```
    ```
    /home/workspace/backtest/test_metrics_agent.py:51:        avg_loss_pct=-2.0,
    ```

### INFERRED #calls-36
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL80 :: chaos_test_chaos_classifier`
- **Target:** `atom-federation-os/sbs/failure_classifier.py:L81 :: sbs_failure_classifier_failureclassifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:226:        classifier = FailureClassifier()
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:227:        result = classifier.classify({"type": "partition", "layer": "DRL", "description": "net split"})
    ```
    ```
    /home/workspace/_sbs_old/tests/test_invariants.py:233:        classifier = FailureClassifier()
    ```

### INFERRED #calls-37
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL7 :: alignment_test_rcf_test_rcf_stable_system`
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

### INFERRED #calls-38
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL160 :: alignment_test_alignment_test_rollback_decider`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L82 :: alignment_rollback_engine_v2_rollbackdecider`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:160:    decider = RollbackDecider()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:168:    scope_ok = decider.decide(bind_ok, rep_ok)
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/test_alignment.py:170:    print(f"  decider OK→noop: type={scope_ok.rollback_type.name} ✅")
    ```

### INFERRED #calls-39
- **Source:** `AsurDev/job_engine/engine.py:LL159 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Target:** `AsurDev/job_engine/engine.py:L169 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_write_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/audit_repo/tests/test_logging.py:18:    logger.info("Test event")
    ```
    ```
    /home/workspace/audit_repo/db/session.py:35:    from sqlalchemy import create_engine, event
    ```

### INFERRED #calls-40
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL108 :: alignment_test_rcf_test_rcf_drift_vector_explainable`
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

### INFERRED #calls-41
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL292 :: tests_test_v68_coherence_test_sci_oscillation_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:29:    with pytest.raises(RuntimeError):
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:190:    with pytest.raises(ValueError):
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
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL42 :: tests_test_stability_feedback_controller_teststabilityfeedbackcontrollerbasics_test_initial_state`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:51:    def run(self, state):
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:112:    def run(self, state):
    ```
    ```
    /home/workspace/tests/architecture/test_validate_agent.py:52:    async def run(self, state):
    ```

### INFERRED #calls-44
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL83 :: alignment_test_rcf_test_rcf_all_consistent_stable_merge_allowed`
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

### INFERRED #calls-45
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL242 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_build_astrofin_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L169 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_latency_sla`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/v6/constraint_graph/graph.py:18:    SLA           = "sla"            # P(latency > threshold) < 0.05
    ```
    ```
    /home/workspace/home-cluster-iac/v6/constraint_graph/graph.py:18:    SLA = "sla"  # P(latency > threshold) < 0.05
    ```

### INFERRED #calls-46
- **Source:** `atom-federation-os/cluster/node/node.py:LL52 :: node_node_clusternode_init`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L62 :: sbs_global_invariant_engine_globalinvariantengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-47
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL67 :: tests_test_stability_feedback_controller_testoscillationdetection_test_stable_observations`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/resilience/model_reality_aligner.py:48:    Monitors the gap between self_model predictions and real cluster observations.
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/actuator/stability_feedback_controller.py:78:      - Oscillation detection uses a rolling window of gain observations
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/actuator/stability_feedback_controller.py:84:        oscillation_window: int = 8,        # number of observations for oscillation detection
    ```

### INFERRED #calls-48
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL166 :: alignment_test_rcf_test_rcf_consensus_score_clamped`
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

### INFERRED #calls-49
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL282 :: chaos_test_chaos_testintegration_test_partition_half_cluster_verdict_not_fail`
- **Target:** `atom-federation-os/chaos/scenarios.py:L278 :: chaos_scenarios_partition_half_cluster`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/agents/_impl/gann_agent.py:200:            summary = f"Gann time cluster: bar {bar_num} aligns with {hits}"
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/gann_agent.py:206:            summary = f"no Gann time cluster at bar {bar_num}"
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/gann_agent.py:245:            summary = f"Astro time cluster: {', '.join(hits)}"
    ```

### INFERRED #calls-50
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL116 :: resilience_meta_coherence_controller_metacoherencecontroller_init`
- **Target:** `atom-federation-os/coherence/drift_controller.py:L85 :: coherence_drift_controller_driftcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-51
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL20 :: tests_test_stability_feedback_controller_teststabilityfeedbackcontrollerbasics_test_default_init`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-52
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL96 :: tests_test_stability_feedback_controller_testoscillationdetection_test_overshoot_counting`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_exporter.py:196:        "description": "Elliott Wave analysis for wave counting and trend prediction",
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/elliot_agent.py:127:        Simplified wave counting.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/elliot_agent.py:157:        # Simplified wave counting
    ```

### INFERRED #calls-53
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL290 :: chaos_test_chaos_testintegration_test_byzantine_injection_detected`
- **Target:** `atom-federation-os/chaos/scenarios.py:L287 :: chaos_scenarios_byzantine_sender_injection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:338:        # Seed the pool with one strategy to verify injection respects caps.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/idea_buffer_integration.py:116:    Full injection workflow:
    ```
    ```
    /home/workspace/AsurDev/load_test/injectors/synthetic_scheduler.py:43:    """Full injection cycle result."""
    ```

### INFERRED #calls-54
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL114 :: tests_test_v68_coherence_test_smoother_adaptive_window_high_volatility`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L71 :: coherence_temporal_smoother_temporalcoherencesmoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:230:            result = window.add(confidence=raw, volatility=None)
    ```
    ```
    /home/workspace/data/market_adapter.py:259:        higher volatility and inflated volume to mimic flow-driven markets.
    ```
    ```
    /home/workspace/audit_repo/trading/risk_v2.py:199:        Adjust raw PnL by volatility regime and drawdown.
    ```

### INFERRED #calls-55
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL133 :: alignment_test_gcpl_test_termination_converged`
- **Target:** `atom-federation-os/alignment/gcpl.py:L303 :: alignment_gcpl_terminationprover`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/Projects/Loopcraft/loopcraft_demo.py:250:    converged = False
    ```
    ```
    /home/workspace/Projects/Loopcraft/loopcraft_demo.py:305:                converged = True
    ```
    ```
    /home/workspace/Projects/Loopcraft/loopcraft_demo.py:311:    if verbose and not converged:
    ```

### INFERRED #calls-56
- **Source:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:LL165 :: consistency_test_cross_layer_invariant_engine_testcausaldag_test_is_identical_false_different_nodes`
- **Target:** `atom-federation-os/consistency/cross_layer_invariant_engine.py:L79 :: consistency_cross_layer_invariant_engine_causaldag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_infer_edges.py:48:        "nodes": [
    ```
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:34:        # Add roles as nodes
    ```
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:41:        # Add switch nodes
    ```

### INFERRED #calls-57
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL128 :: tests_test_stability_feedback_controller_testcomputegainadjustment_test_oscillating_mode_reduces_gain`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/meta_rl/quant/metrics.py:47:    """Omega: gain above threshold / loss below threshold."""
    ```
    ```
    /home/workspace/audit_repo/meta_rl/quant/metrics.py:48:    gain = sum(threshold - r for r in returns if r >= threshold)
    ```
    ```
    /home/workspace/audit_repo/meta_rl/quant/metrics.py:50:    return gain / loss if loss != 0 else 0.0
    ```

### INFERRED #calls-58
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL248 :: chaos_test_chaos_testnetworkpartitioner_test_partitioner_init`
- **Target:** `atom-federation-os/chaos/partitioner.py:L28 :: chaos_partitioner_networkpartitioner`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-59
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

### INFERRED #calls-60
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL118 :: tests_test_stability_feedback_controller_testcomputegainadjustment_test_normal_mode_no_adjustment`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5.py:60:        adjustment = (oap_score - 0.5) * 0.4
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5.py:61:        logger.debug(f"[OAP] no per-agent stats — uniform adj={adjustment:+.3f}")
    ```
    ```
    /home/workspace/audit_repo/orchestration/sentinel_v5.py:62:        return dict.fromkeys(agents, adjustment)
    ```

### INFERRED #calls-61
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL306 :: tests_test_v68_coherence_test_sci_fail_fast_false_does_not_raise`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:31:            raise RuntimeError("boom")
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:93:    """An empty state is not allowed to raise — must degrade gracefully."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:97:    # the contract is "do not raise".
    ```

### INFERRED #calls-62
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL27 :: alignment_test_gcpl_test_edit_distance_identical`
- **Target:** `atom-federation-os/alignment/gcpl.py:L89 :: alignment_gcpl_causal_edit_distance`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:126:        # stop_distance_pct (≈ loss) and a 2R target distance (≈ gain).
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/fundamental_agent.py:185:        # ATH distance bonus
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/risk_agent.py:195:        # ATR-based stop distance
    ```

### INFERRED #calls-63
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL34 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_opens_after_threshold`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:208:                "position_lag": 0.15,  # < 0.3 threshold → no risk change
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:242:                "position_lag": 0.5,  # > 0.3 threshold → increase
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:251:        # Проверяем что position_lag > threshold приведёт к увеличению
    ```

### INFERRED #calls-64
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL292 :: tests_test_v68_coherence_test_sci_oscillation_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:29:    with pytest.raises(RuntimeError):
    ```
    ```
    /home/workspace/tests/agent_test_base.py:137:        """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```

### INFERRED #calls-65
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL148 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_health_check_loop`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L127 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_reconnect_with_backoff`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/meta_rl/live_provider.py:134:        """Fetch with retry + exponential backoff."""
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:143:                backoff = engine.BACKOFF_BASE ** attempt
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:145:                log.warning(f"Failure detected [{name}]: {reason} → attempt {attempt}/{engine.MAX_RETRIES} (backoff={backoff}s)")
    ```

### INFERRED #calls-66
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL100 :: tests_test_v68_coherence_test_smoother_damps_oscillation`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L71 :: coherence_temporal_smoother_temporalcoherencesmoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:143:                "ML retraining triggers rapid policy weight oscillation without damping"
    ```
    ```
    /home/workspace/AsurDev/load_test/scenarios/policy_oscillation/test.py:6:HYPOTHESIS: ML (v5) retraining faster than policy (v7) stabilizes → oscillation
    ```
    ```
    /home/workspace/AsurDev/load_test/scenarios/policy_oscillation/test.py:63:        """Run oscillation scenario for duration_sec."""
    ```

### INFERRED #calls-67
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL249 :: tests_test_stability_feedback_controller_testapplygaintocommands_test_multiple_commands`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:488:    print("\nUse --help for commands.")
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker.py:434:    print("\nUse --help for commands.")
    ```
    ```
    /home/workspace/audit_repo/orchestration/karl_cli.py:154:    """Prometheus /metrics server commands."""
    ```

### INFERRED #calls-68
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL344 :: tests_test_stability_feedback_controller_testhistorymanagement_test_gain_history_max_length`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:172:    # the same length and identical generation numbers.
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/branding_injector.py:49:                response.headers["content-length"] = str(len(response.body))
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/tests/test_gateway.py:101:        """ACME tenant accepts a valid-length API key (>= 16 chars)."""
    ```

### INFERRED #calls-69
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL63 :: alignment_test_alignment_test_l2_causal`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L245 :: alignment_drift_detector_causalorderdriftdetector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos.py:89:  └── Correlation engine (causal linking)
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/dag_hash_modes.py:44:                 Suitable for deterministic replay, causal traces,
    ```
    ```
    /home/workspace/atom-federation-os/federation/delta_gossip/dag_hash_modes.py:89:                     For replay, execution traces, causal lineage.
    ```

### INFERRED #calls-70
- **Source:** `astrofin-sentinel-v5/meta_rl/git_agent_exporter.py:LL30 :: astrofin_sentinel_v5_meta_rl_git_agent_exporter_py_meta_rl_git_agent_exporter_validate_agent_yaml`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_validator.py:9:import yaml
    ```
    ```
    /home/workspace/tests/test_validator.py:34:# ─── Test: Valid agent.yaml ───────────────────────────────────────────────────
    ```
    ```
    /home/workspace/tests/test_validator.py:41:        (agent_dir / "agent.yaml").write_text(
    ```

### INFERRED #calls-71
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL124 :: alignment_test_rcf_test_rcf_trust_variance_tracked`
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

### INFERRED #calls-72
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL79 :: alignment_test_gcpl_test_checker_nominal`
- **Target:** `atom-federation-os/alignment/gcpl.py:L192 :: alignment_gcpl_globalconsistencychecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/core/kepler_calibrator.py:233:        # Start with nominal elements
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/astrology/kepler_calibrator.py:233:        # Start with nominal elements
    ```
    ```
    /home/workspace/core/kepler_calibrator.py:233:        # Start with nominal elements
    ```

### INFERRED #calls-73
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL249 :: tests_test_v68_coherence_test_sci_drift_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L62 :: coherence_invariant_systemcoherenceinvariant`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:29:    with pytest.raises(RuntimeError):
    ```
    ```
    /home/workspace/tests/agent_test_base.py:137:        """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```

### INFERRED #calls-74
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL276 :: tests_test_stability_feedback_controller_teststabilitystatefields_test_stability_state_explicit`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L34 :: actuator_stability_feedback_controller_stabilitystate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:83:    """The convenience function must work without explicit instantiation."""
    ```
    ```
    /home/workspace/tools/thompson_cli.py:84:    # k resolved: explicit --k > pool.k > default_k(=4)
    ```
    ```
    /home/workspace/audit_repo/tests/_template_agent_test.py:83:    """The convenience function must work without explicit instantiation."""
    ```

### INFERRED #calls-75
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL159 :: tests_test_stability_feedback_controller_testcomputegainadjustment_test_collapsed_mode_zero_gain`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:12:      - Compute expected utility E[U] = p·gain − (1−p)·loss for each,
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:13:        using VolatilityEngine.analyze() for gain/loss.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:125:        # E[U] = p·gain − (1−p)·loss. VolatilityEngine gives us the
    ```

### INFERRED #calls-76
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL91 :: tests_test_v68_coherence_test_smoother_stable_actions`
- **Target:** `atom-federation-os/coherence/temporal_smoother.py:L71 :: coherence_temporal_smoother_temporalcoherencesmoother`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/oap_optimizer.py:181:        Вычисляет actions для KPI control loop.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/oap_optimizer.py:188:        actions: list[ControlAction] = []
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/oap_optimizer.py:203:            actions.append(ControlAction.INCREASE_TTC_DEPTH)
    ```

### INFERRED #calls-77
- **Source:** `atom-federation-os/coherence/tests/test_v68_coherence.py:LL249 :: tests_test_v68_coherence_test_sci_drift_violation_raises`
- **Target:** `atom-federation-os/coherence/invariant.py:L39 :: coherence_invariant_coherencebounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:190:    with pytest.raises(ValueError):
    ```
    ```
    /home/workspace/tests/agent_test_base.py:137:        """If a data source raises, the response is degraded with a machine reason."""
    ```

### INFERRED #calls-78
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL149 :: tests_test_stability_feedback_controller_testcomputegainadjustment_test_saturated_mode_reduces_gain_significantly`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/scripts/compare_backtest_modes.py:101:        print("❌ Modes differ significantly.")
    ```
    ```
    /home/workspace/audit_repo/scripts/compare_backtest_modes.py:100:        print("❌ Modes differ significantly.")
    ```
    ```
    /home/workspace/AsurDev/ml_engine/training/evaluate.py:44:    Detect if model performance has drifted significantly.
    ```

### INFERRED #calls-79
- **Source:** `atom-federation-os/alignment/merge_engine.py:LL145 :: alignment_merge_engine_mergeengine_do_merge`
- **Target:** `atom-federation-os/alignment/branch.py:L34 :: alignment_branch_branchpoint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:50:        "merge node",
    ```
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:174:            "merge node",
    ```
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:17:        "merge": "#9C27B0",  # Purple for merges
    ```

### INFERRED #calls-80
- **Source:** `atom-federation-os/chaos/validator.py:LL102 :: chaos_validator_chaosvalidator_init`
- **Target:** `atom-federation-os/sbs/global_invariant_engine.py:L62 :: sbs_global_invariant_engine_globalinvariantengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```

### INFERRED #calls-81
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL283 :: chaos_test_chaos_testintegration_test_partition_half_cluster_verdict_not_fail`
- **Target:** `atom-federation-os/chaos/harness.py:L126 :: chaos_harness_chaosharness`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:42:    """If a module imports ephemeris but no method has @require_ephemeris, fail."""
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:105:    """When hard rules fail, the script returns non-zero."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:143:    """Test 3: OOS fail > 0.4 → tighten policy."""
    ```

### INFERRED #calls-82
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL219 :: chaos_test_chaos_testchaosharness_test_harness_runs_all_scenarios`
- **Target:** `atom-federation-os/chaos/harness.py:L126 :: chaos_harness_chaosharness`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:48:    SCENARIO_MODULE_PREFIX = "load_test.scenarios"
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:57:            self.repo_root, "load_test", "scenarios",
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:276:    scenarios = [
    ```

### INFERRED #calls-83
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL58 :: alignment_test_adlr_test_orch_oscillation_loop`
- **Target:** `atom-federation-os/alignment/adlr.py:L241 :: alignment_adlr_adlrecoveryorchestrator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/daily_digest/daily_digest_analytics.py:359:                apps.append("Интегрировать в KARL reward calibration loop")
    ```
    ```
    /home/workspace/audit_repo/knowledge/daily_digest/daily_digest_analytics.py:358:                apps.append("Интегрировать в KARL reward calibration loop")
    ```
    ```
    /home/workspace/audit_repo/mas_factory/engine.py:220:            loop = asyncio.get_event_loop()
    ```

### INFERRED #calls-84
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL10 :: alignment_test_bcil_test_bc_f1_byzantine_branch_dominated`
- **Target:** `atom-federation-os/alignment/bcil.py:L325 :: alignment_bcil_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gcst.py:11:from alignment.bcil import BCIL
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/gcst.py:37:        self.bcil = BCIL()
    ```
    ```
    /home/workspace/atom-federation-os/build/lib/alignment/bcil.py:1:"""bcil.py — v10.4 Byzantine-Convergence Integration Layer."""
    ```

---

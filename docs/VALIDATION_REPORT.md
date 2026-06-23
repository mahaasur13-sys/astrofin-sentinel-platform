# VALIDATION_REPORT.md

Stratified validation of N=317 INFERRED edges from `graphify-out/graph.json` (snapshot 2026-06-17).

**Verdict legend:**
- `valid` — link is real and current
- `false` — link does not exist in code

**Verdict summary (N=317):** `valid`=122 (38%), `false`=99 (31%), `ambiguous`=87 (27%), `outdated`=9 (3%)

- `moved` — entity exists, but in a different file (new path noted)
- `outdated` — was true at some point, now dead (e.g. `_archived/`, removed submodules)
- `ambiguous` — needs human review

---

## Bucket: relation = `calls` (57 edges)

### INFERRED #calls-1
- **Source:** `atom-federation-os/tests/test_resilience_v65.py:LL48 :: tests_test_resilience_v65_testinvariantresult_test_to_dict_method_exists`
- **Target:** `atom-federation-os/resilience/invariants.py:L140 :: resilience_invariants_invariantsengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/db_monitor.py:22:        if not db_path.exists():
    ```
    ```
    /home/workspace/tools/db_monitor.py:54:    if not SNAPSHOT_TBL.exists():
    ```
    ```
    /home/workspace/tools/db_monitor.py:96:    if SNAPSHOT_TBL.exists():
    ```

### INFERRED #calls-2
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL148 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_evolve`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L127 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_reproduce`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/astrofin/meta_rl/engine.py:127:    def reproduce(self, selected: list["Strategy"]) -> list["Strategy"]:
    ```
    ```
    /home/workspace/AsurDev/astrofin/meta_rl/engine.py:141:        3. reproduce (crossover + mutation)
    ```
    ```
    /home/workspace/AsurDev/astrofin/meta_rl/engine.py:148:            self.population = self.reproduce(selected)
    ```

### INFERRED #calls-3
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL81 :: tests_test_stability_feedback_controller_testoscillationdetection_test_oscillating_observations`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/chaos/stress_envelope.py:324:        Returns avg violation_score across last `window` observations.
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gsl.py:267:        """Branch-observation entropy: how many branches share observations."""
    ```
    ```
    /home/workspace/atom-federation-os/actuator/stability_feedback_controller.py:78:      - Oscillation detection uses a rolling window of gain observations
    ```

### INFERRED #calls-4
- **Source:** `atom-federation-os/federation/tests/test_consensus_resolver.py:LL140 :: tests_test_consensus_resolver_testdetectdivergence_test_no_divergence_with_agreeing_peers`
- **Target:** `atom-federation-os/federation/consensus_resolver.py:L40 :: federation_consensus_resolver_consensusresolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_patch.py:118:        "awg_peers_connected": len(status.get("peers", [])),
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_wg.py:107:        result = {"up": False, "interface": self._iface, "peers": [],
    ```
    ```
    /home/workspace/AsurDev/monitoring/exporters/wireguard/wg_exporter.py:19:        return {"peers": [], "interface": {}}
    ```

### INFERRED #calls-5
- **Source:** `atom-federation-os/consistency_v3/test_unified_state_metric_tensor.py:LL151 :: consistency_v3_test_unified_state_metric_tensor_testunifiedstatemetrictensor_test_custom_weights`
- **Target:** `atom-federation-os/consistency_v3/unified_state_metric_tensor.py:L52 :: consistency_v3_unified_state_metric_tensor_axisvector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/topology.py:67:    weights: dict[str, float] | None = None
    ```
    ```
    /home/workspace/push/mas_factory/topology.py:80:            scores = {a: random.random() * (self.weights or {}).get(a, 1.0) for a in self.candidates}
    ```
    ```
    /home/workspace/push/mas_factory/architect.py:321:                weights={r.name: r.weight for r in roles if r.name != "synthesis"},
    ```

### INFERRED #calls-6
- **Source:** `AsurDev/lccp_v12.py:LL138 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L51 :: asurdev_lccp_v12_staterebuilder_verify`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/test_auth_flask_decorator.py:4:These tests verify authentication behavior including edge cases.
    ```
    ```
    /home/workspace/push/tests/test_dual_mode.py:20:        # Just verify the function signature and it doesn't crash
    ```
    ```
    /home/workspace/push/tests/test_dual_mode.py:47:            # We can't easily test main(), so just verify the architecture
    ```

### INFERRED #calls-7
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL109 :: tests_test_stability_feedback_controller_testoscillationdetection_test_saturation_mode`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/scripts/compare_backtest_modes.py:88:    parser.add_argument("--ci", action="store_true", help="Run in CI mode with identical mock results")
    ```
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:133:    return {"mode": "base", "decisions": results}
    ```
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:203:        "mode": "karl",
    ```

### INFERRED #calls-8
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL89 :: alignment_test_adlr_test_ri3_deterministic`
- **Target:** `atom-federation-os/alignment/adlr.py:L241 :: alignment_adlr_adlrecoveryorchestrator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/agents/_impl/_template_agent.py:28:    - Be deterministic for a given state (no `random` without seeded RNG).
    ```
    ```
    /home/workspace/push/agents/gitagent_registry.py:383:            # Add seed to state for deterministic variation
    ```
    ```
    /home/workspace/push/meta_rl/backtest_adapter.py:29:    Seed-controlled: Backtester is deterministic per strategy evaluation.
    ```

### INFERRED #calls-9
- **Source:** `atom-federation-os/resilience/tests/test_v67_meta_coherence.py:LL153 :: tests_test_v67_meta_coherence_test_governor_summary`
- **Target:** `atom-federation-os/resilience/objective_stability_governor.py:L65 :: resilience_objective_stability_governor_objectivestabilitygovernor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/visualizer.py:171:            "summary": {
    ```
    ```
    /home/workspace/push/mas_factory/atom_033_production_test.py:120:    summary = engine.get_metrics_summary()
    ```
    ```
    /home/workspace/push/mas_factory/atom_033_production_test.py:121:    cprint(f"  Total runs: {summary['total_runs']}", "93")
    ```

### INFERRED #calls-10
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL116 :: resilience_meta_coherence_controller_metacoherencecontroller_init`
- **Target:** `atom-federation-os/coherence/drift_controller.py:L85 :: coherence_drift_controller_driftcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:268:        "--init-single",
    ```
    ```
    /home/workspace/audit_repo/meta_rl/calibration.py:143:            logger.warning(f"[CALIBRATION] schema init failed: {exc}")
    ```

### INFERRED #calls-11
- **Source:** `atom-federation-os/tests/test_temporal_proof_v77.py:LL39 :: tests_test_temporal_proof_v77_testproofchain_test_append_links_are_sequential`
- **Target:** `atom-federation-os/proof/proof_trace.py:L64 :: proof_proof_trace_decisionrecord`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/langgraph_schema.py:11:Flow (conditional, не sequential):
    ```
    ```
    /home/workspace/push/knowledge/daily_digest/daily_digest_analytics.py:50:        "sequential node",
    ```
    ```
    /home/workspace/push/knowledge/daily_digest/daily_digest_analytics.py:174:            "sequential",
    ```

### INFERRED #calls-12
- **Source:** `roma-execution-bridge/control_plane/leases.py:LL17 :: control_plane_leases_gpuleasemanager_acquire`
- **Target:** `roma-execution-bridge/control_plane/core_models.py:L26 :: control_plane_core_models_gpulease`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/control_plane/leases.py:14:    def acquire(self, gpu_id: str, job_id: str, worker_id: str, ttl: float = 30.0) -> bool:
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/gpu_lock_manager_fast.py:18:@app.post("/lock/acquire")
    ```
    ```
    /home/workspace/roma-execution-bridge/gpu_worker/gpu_lock_manager_fast.py:19:def acquire(req: LockReq):
    ```

### INFERRED #calls-13
- **Source:** `atom-federation-os/tests/test_proof_v76.py:LL56 :: tests_test_proof_v76_testprooftracebasics_test_add_conflict_stage`
- **Target:** `atom-federation-os/proof/proof_trace.py:L112 :: proof_proof_trace_prooftrace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/trading/safety_gate.py:407:    def _log_event(self, stage: str, status: str, reason: str):
    ```
    ```
    /home/workspace/push/trading/safety_gate.py:411:            print(f"[SAFETY-STACK] {ts} {stage:8s} {icon} {status:8s} — {reason}")
    ```
    ```
    /home/workspace/push/core/idea_model.py:92:    def stage(self) -> IdeaStage:
    ```

### INFERRED #calls-14
- **Source:** `atom-federation-os/meta_control/integration/test_integration.py:LL137 :: integration_test_integration_testweightmodulator_test_weight_modulator_no_history_defaults_neutral`
- **Target:** `atom-federation-os/meta_control/proof_feedback_controller.py:L19 :: meta_control_proof_feedback_controller_prooffeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/astrology/vedic.py:20:    {"name": "Krittika", "quality": "neutral", "deity": "Agni", "ruling_planet": "Sun"},
    ```
    ```
    /home/workspace/push/astrology/vedic.py:47:    {"name": "Magha", "quality": "neutral", "deity": "Pitris", "ruling_planet": "Ketu"},
    ```
    ```
    /home/workspace/push/astrology/vedic.py:68:        "quality": "neutral",
    ```

### INFERRED #calls-15
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL148 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_health_check_loop`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L127 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_reconnect_with_backoff`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/meta_rl/live_provider.py:134:        """Fetch with retry + exponential backoff."""
    ```
    ```
    /home/workspace/audit_repo/meta_rl/live_provider.py:134:        """Fetch with retry + exponential backoff."""
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:143:                backoff = engine.BACKOFF_BASE ** attempt
    ```

### INFERRED #calls-16
- **Source:** `atom-federation-os/consistency_v2/test_realtime_divergence_detector.py:LL64 :: consistency_v2_test_realtime_divergence_detector_test_realtime_divergence_detector_rate_divergence`
- **Target:** `atom-federation-os/consistency_v2/realtime_divergence_detector.py:L140 :: consistency_v2_realtime_divergence_detector_realtimedivergencedetector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/tests/test_kepler_differential.py:73:    # ─── Test 3: No catastrophic divergence — outer planets only ───────
    ```
    ```
    /home/workspace/push/core/idea_model.py:4:# Idea must import from here. No dict/dataclass divergence.
    ```
    ```
    /home/workspace/push/knowledge/daily_brief/idea_tracker_refactored.py:30:# All Idea data flows through this dataclass. No dict divergence.
    ```

### INFERRED #calls-17
- **Source:** `atom-federation-os/resilience/tests/test_v67_meta_coherence.py:LL277 :: tests_test_v67_meta_coherence_test_meta_coherence_force_rebuild`
- **Target:** `atom-federation-os/resilience/meta_coherence_controller.py:L73 :: resilience_meta_coherence_controller_metacoherencecontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/knowledge/build_index.py:7:    python build_index.py --domain all --rebuild
    ```
    ```
    /home/workspace/audit_repo/knowledge/build_index.py:126:        if index_path.exists() and not args.rebuild:
    ```
    ```
    /home/workspace/audit_repo/knowledge/build_index.py:127:            print(f"  {d}: index exists (use --rebuild to overwrite)")
    ```

### INFERRED #calls-18
- **Source:** `atom-federation-os/tests/test_temporal_proof_v77.py:LL194 :: tests_test_temporal_proof_v77_teststabilityprover_test_stability_all_same_source`
- **Target:** `atom-federation-os/proof/proof_trace.py:L64 :: proof_proof_trace_decisionrecord`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/db_monitor.py:63:                source TEXT NOT NULL,
    ```
    ```
    /home/workspace/tools/db_monitor.py:72:                "INSERT INTO _row_count_snapshots (source, count, distribution) VALUES (?, ?, ?)",
    ```
    ```
    /home/workspace/tools/db_monitor.py:101:                SELECT source,
    ```

### INFERRED #calls-19
- **Source:** `atom-federation-os/federation/tests/test_policy_sync.py:LL55 :: tests_test_policy_sync_testpolicysyncbasics_test_init`
- **Target:** `atom-federation-os/federation/policy_sync.py:L53 :: federation_policy_sync_policysync`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:22:    spread: float = field(init=False)
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:23:    mid_price: float = field(init=False)
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:24:    depth_bid_10: float = field(init=False)  # total bid qty in top 10 levels
    ```

### INFERRED #calls-20
- **Source:** `atom-federation-os/federation/tests/test_gossip_protocol.py:LL98 :: tests_test_gossip_protocol_testgossippushpull_test_receive_push_records_history`
- **Target:** `atom-federation-os/federation/gossip_protocol.py:L37 :: federation_gossip_protocol_gossipprotocol`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/db_monitor.py:12:    "sessions (history)": BASE / "core" / "history.db",
    ```
    ```
    /home/workspace/push/strategies/generator.py:270:    history = [best_ever[1]]
    ```
    ```
    /home/workspace/push/strategies/generator.py:294:        history.append(best_ever[1])
    ```

### INFERRED #calls-21
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL344 :: tests_test_stability_feedback_controller_testhistorymanagement_test_gain_history_max_length`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/branding_injector.py:49:                response.headers["content-length"] = str(len(response.body))
    ```
    ```
    /home/workspace/roma-execution-bridge/saas/gateway/tests/test_gateway.py:101:        """ACME tenant accepts a valid-length API key (>= 16 chars)."""
    ```
    ```
    /home/workspace/FINAL_INTEGRATION_TEST.py:334:        print_test("Mermaid generated", has_mermaid, f"length={len(mermaid)}")
    ```

### INFERRED #calls-22
- **Source:** `atom-federation-os/meta_control/integration/test_integration.py:LL99 :: integration_test_integration_testgainmodulator_test_gain_modulator_applies_aware_adjustments`
- **Target:** `atom-federation-os/meta_control/temporal_gain_scheduler.py:L20 :: meta_control_temporal_gain_scheduler_temporalgainscheduler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/karl_diagnostics.py:93:        adjustments = [q.get("confidence_adjustment", 0) for q in meta_questions]
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/karl_diagnostics.py:94:        m.meta_adjustment_avg = sum(adjustments) / len(adjustments)
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/karl_diagnostics.py:95:        m.meta_prevented_wrong = sum(1 for a in adjustments if a < 0)
    ```

### INFERRED #calls-23
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

### INFERRED #calls-24
- **Source:** `AsurDev/job_engine/engine.py:LL159 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Target:** `AsurDev/job_engine/engine.py:L169 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_write_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/session.py:35:    from sqlalchemy import create_engine, event
    ```
    ```
    /home/workspace/push/db/session.py:48:    @event.listens_for(engine, "connect")
    ```
    ```
    /home/workspace/push/tests/test_logging.py:18:    logger.info("Test event")
    ```

### INFERRED #calls-25
- **Source:** `atom-federation-os/federation/tests/test_state_vector.py:LL123 :: tests_test_state_vector_teststatevectorstr_test_str_contains_node_id`
- **Target:** `atom-federation-os/federation/state_vector.py:L14 :: federation_state_vector_statevector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/nightly_export.py:39:            logger.info(f"  {s.id}: reward={s.reward:.4f}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:226:            print(f"  {idea.id:<14} {idea.status:<12} {idea.score:>6.2f} {idea.impact_score:>8.4f} {idea.category:<20}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:238:            print(f"  {idea.id:<14} {idea.score:>6.2f} {idea.category:<20} {idea.text[:28]:<30}")
    ```

### INFERRED #calls-26
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL138 :: alignment_test_rcf_test_rcf_boundary_45_stable`
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

### INFERRED #calls-27
- **Source:** `atom-federation-os/sbs/cli_schema.py:LL28 :: sbs_cli_schema_run_schema_check`
- **Target:** `atom-federation-os/sbs/schema_validator.py:L14 :: sbs_schema_validator_validate_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/health_endpoints.py:27:app.state.limiter = limiter
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:190:    state = {
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:200:    result = await executor.run(state)
    ```

### INFERRED #calls-28
- **Source:** `atom-federation-os/alignment/test_rcf.py:LL83 :: alignment_test_rcf_test_rcf_all_consistent_stable_merge_allowed`
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

### INFERRED #calls-29
- **Source:** `atom-federation-os/resilience/meta_coherence_controller.py:LL112 :: resilience_meta_coherence_controller_metacoherencecontroller_init`
- **Target:** `atom-federation-os/resilience/optimizer.py:L85 :: resilience_optimizer_systemoptimizer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:268:        "--init-single",
    ```
    ```
    /home/workspace/audit_repo/meta_rl/calibration.py:143:            logger.warning(f"[CALIBRATION] schema init failed: {exc}")
    ```

### INFERRED #calls-30
- **Source:** `atom-federation-os/swarm/test_swarm.py:LL172 :: swarm_test_swarm_testintegrationswarmlayer_test_full_swarm_pipeline`
- **Target:** `atom-federation-os/swarm/causal_merge_protocol.py:L38 :: swarm_causal_merge_protocol_causalmergeprotocol`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/strategies/generator.py:410:    """Run the full Meta-RL pipeline."""
    ```
    ```
    /home/workspace/push/tests/test_orchestrator.py:97:    """Full pipeline — all agents run, final output is complete."""
    ```
    ```
    /home/workspace/push/agents/_impl/amre/karl_optimizer.py:35:    """Async pipeline for parallel KARL operations."""
    ```

### INFERRED #calls-31
- **Source:** `atom-federation-os/persistence/stateful_recovery.py:LL131 :: persistence_stateful_recovery_eventstore_flush`
- **Target:** `atom-federation-os/persistence/atomic_fs.py:L38 :: persistence_atomic_fs_atomicfilewrite`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/core/atomic_ledger.py:151:            f.flush()
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2a_safety_foundations/mutation_ledger.py:110:        ledger.flush(path="mutation_ledger.jsonl")
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/v8_2a_safety_foundations/mutation_ledger.py:183:    def flush(self, path: str | Path) -> None:
    ```

### INFERRED #calls-32
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL97 :: alignment_test_bcil_test_bc_split_brain`
- **Target:** `atom-federation-os/alignment/bcil.py:L325 :: alignment_bcil_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/alignment/test_bcil.py:5:from alignment.bcil import BCIL, ByzantineConvergenceFunction, ByzantineFailureType, QuorumSpec
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_bcil.py:10:    bcil = BCIL(quorum)
    ```
    ```
    /home/workspace/atom-federation-os/alignment/test_bcil.py:18:    report = bcil.analyze(branches, trust_scores, node_trust, voter_assignments, gcpl_convergence=0.3)
    ```

### INFERRED #calls-33
- **Source:** `atom-federation-os/consistency_v3/test_causal_semantic_space.py:LL70 :: consistency_v3_test_causal_semantic_space_testdictdiff_test_novel_key`
- **Target:** `atom-federation-os/consistency_v3/causal_semantic_space.py:L217 :: consistency_v3_causal_semantic_space_dict_diff`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:325:        diff, sign = k - b, "+" if k - b > 0 else ""
    ```
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:327:            diff, sign = b - k, "+" if b - k > 0 else ""
    ```
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:328:        print(f"{key.replace('_', ' ').title():<30} {b:>12.4f} {k:>12.4f} {sign}{abs(diff):>9.4f}")
    ```

### INFERRED #calls-34
- **Source:** `atom-federation-os/dag/test_fingerprint.py:LL62 :: dag_test_fingerprint_testincrementalfingerprint_test_full_diamond`
- **Target:** `atom-federation-os/dag/fingerprint.py:L148 :: dag_fingerprint_incrementalfingerprint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/visualizer.py:84:                f'    {sw.id} [label="{sw.id}\\n{cond}", shape=diamond, fillcolor="{sw_color}40", color="{sw_color}"];'
    ```
    ```
    /home/workspace/push/mas_factory/visualizer.py:106:                '        leg2 [shape=diamond, label="Switch", fillcolor="#FF980040"];',
    ```
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:84:                f'    {sw.id} [label="{sw.id}\\n{cond}", shape=diamond, fillcolor="{sw_color}40", color="{sw_color}"];'
    ```

### INFERRED #calls-35
- **Source:** `atom-federation-os/tests/test_v9_3_federation_binding.py:LL151 :: tests_test_v9_3_federation_binding_testphase2proofawareconsensus_test_origin_priority_remote_over_replay`
- **Target:** `atom-federation-os/federation/proof_aware_consensus.py:L54 :: federation_proof_aware_consensus_proofawareconsensuscandidate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/db/models.py:283:    """Complete trajectory for KARL replay buffer."""
    ```
    ```
    /home/workspace/push/agents/_impl/amre/idea_buffer_integration.py:2:Встраивает Idea в KARL replay buffer lifecycle.
    ```
    ```
    /home/workspace/push/agents/_impl/amre/idea_buffer_integration.py:51:    Inject a scored Idea into the KARL replay buffer.
    ```

### INFERRED #calls-36
- **Source:** `roma-execution-bridge/saas/branding/loader.py:LL31 :: branding_loader_load_by_tenant_id`
- **Target:** `roma-execution-bridge/saas/branding/models.py:L9 :: branding_models_tenantbranding`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/nightly_export.py:39:            logger.info(f"  {s.id}: reward={s.reward:.4f}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:226:            print(f"  {idea.id:<14} {idea.status:<12} {idea.score:>6.2f} {idea.impact_score:>8.4f} {idea.category:<20}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:238:            print(f"  {idea.id:<14} {idea.score:>6.2f} {idea.category:<20} {idea.text[:28]:<30}")
    ```

### INFERRED #calls-37
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL133 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L101 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ray_active_workers`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ai_scheduler/modules/metrics.py:102:    """Ray active workers"""
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/run.py:37:    workers = _worker_reg.list_all()
    ```
    ```
    /home/workspace/roma-execution-bridge/saas_api/routes/run.py:38:    if not workers:
    ```

### INFERRED #calls-38
- **Source:** `data_room/resolvers/price_resolver.py:LL37 :: resolvers_price_resolver_binancepriceresolver_resolve`
- **Target:** `data_room/resolvers/base.py:L14 :: resolvers_base_resolvererror`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/scripts/translate_comments.py:19:PROJECT_ROOT = Path(__file__).resolve().parent.parent
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_registry.py:17:REPO_ROOT = Path(__file__).resolve().parent.parent
    ```
    ```
    /home/workspace/push/scripts/validate_agent.py:56:REPO_ROOT = Path(__file__).resolve().parent.parent
    ```

### INFERRED #calls-39
- **Source:** `atom-federation-os/tests/test_proof_v76.py:LL262 :: tests_test_proof_v76_testverificationengine_test_verify_single_candidate_pass`
- **Target:** `atom-federation-os/proof/proof_trace.py:L64 :: proof_proof_trace_decisionrecord`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_registry.py:310:            # TTC fallback: single-pass execution
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_registry.py:311:            logger.debug(f"[Registry] {agent_name} doesn't support TTC, using single-pass")
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_registry.py:323:        """Single-pass agent execution."""
    ```

### INFERRED #calls-40
- **Source:** `atom-federation-os/federation/tests/test_consensus_resolver.py:LL62 :: tests_test_consensus_resolver_testresolvequorum_test_no_quorum_1_of_3`
- **Target:** `atom-federation-os/federation/consensus_resolver.py:L40 :: federation_consensus_resolver_consensusresolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/trading/mode.py:98:    print("  Test 3 (LIVE_LIMITED cap): PASSED")
    ```
    ```
    /home/workspace/trading/risk_v2.py:204:        3. Volatility regime multiplier
    ```
    ```
    /home/workspace/trading/risk_v2.py:232:        # ── 3. Combine ─────────────────────────────────────────────────
    ```

### INFERRED #calls-41
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL138 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_reboot_node`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:311:        help="Agents to select per run (default: pool.k or 4)",
    ```
    ```
    /home/workspace/tools/healthcheck.py:26:        result = subprocess.run(
    ```
    ```
    /home/workspace/tools/healthcheck.py:36:            subprocess.run(
    ```

### INFERRED #calls-42
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/async_engine.py:LL245 :: agent_runtime_async_engine_get_task_store`
- **Target:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:L127 :: agent_runtime_task_store_taskstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/audit_repo/backtest/metrics_agent.py:133:    """SQLite-backed metrics store for all backtest runs."""
    ```
    ```
    /home/workspace/audit_repo/web/components/evolution.py:336:                id="evolution-store",
    ```

### INFERRED #calls-43
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL41 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_opens_after_threshold`
- **Target:** `data_room/circuit_breaker.py:L79 :: data_room_circuit_breaker_call_with_breaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:4:Tests for the Data Room: circuit breaker, graceful degradation,
    ```
    ```
    /home/workspace/data_room/circuit_breaker.py:4:Per-resolver circuit breaker (half-open state machine).
    ```

### INFERRED #calls-44
- **Source:** `atom-federation-os/orchestration/consistency/invariant_contract/test_invariant_contract.py:LL344 :: invariant_contract_test_invariant_contract_testsysteminvariants_make_evaluator`
- **Target:** `atom-federation-os/orchestration/consistency/invariant_contract/invariant_contract.py:L317 :: invariant_contract_invariant_contract_invariantevaluator`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/web/callbacks.py:349:            evaluator = StrategyEvaluator()
    ```
    ```
    /home/workspace/push/web/callbacks.py:350:            agent = MetaAgent(evaluator=evaluator, config=cfg)
    ```
    ```
    /home/workspace/push/meta_rl/meta_agent.py:110:    def __init__(self, evaluator=None, reward_config=None, config=None, karl_state=None):
    ```

### INFERRED #calls-45
- **Source:** `atom-federation-os/meta_control/integration/test_integration.py:LL86 :: integration_test_integration_testgainmodulator_test_gain_modulator_enriches_global_with_ledger_trend`
- **Target:** `atom-federation-os/meta_control/integration/persistence_bridge.py:L39 :: integration_persistence_bridge_gainmodulator`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/db_monitor.py:53:    """Append a snapshot row to the backtest DB for trend tracking."""
    ```
    ```
    /home/workspace/tools/db_monitor.py:116:            print(f"  [monitor] trend query failed: {e}")
    ```
    ```
    /home/workspace/audit_repo/meta_rl/evolution.py:302:        # Check: is reward in a continuous downward trend?
    ```

### INFERRED #calls-46
- **Source:** `astrofin-sentinel-v5/tests/test_validator.py:LL432 :: astrofin_sentinel_v5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L35 :: validators_agent_validator_validationreport`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli.py:3:Rich output, auto-completion, --json, -v/-vv/--quiet.
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli.py:46:quiet_opt = typer.Option(False, "--quiet", "-q", help="Suppress all output")
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli.py:55:    quiet: bool = quiet_opt,
    ```

### INFERRED #calls-47
- **Source:** `atom-federation-os/meta_control/integration/test_integration.py:LL247 :: integration_test_integration_testpersistencebridge_test_to_dict_serializes_all_fields`
- **Target:** `atom-federation-os/meta_control/integration/persistence_bridge.py:L317 :: integration_persistence_bridge_persistencebridge`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/adapters.py:31:    """Extract only signal fields from agent output"""
    ```
    ```
    /home/workspace/push/backtest/test_metrics_agent.py:4:  C1: MetricsDB.list() returns list[BacktestRun] with correct fields
    ```
    ```
    /home/workspace/push/backtest/test_metrics_agent.py:6:  C3: record() round-trip save → load preserves all fields
    ```

### INFERRED #calls-48
- **Source:** `atom-federation-os/orchestration/chaos/test_observability_integration.py:LL148 :: chaos_test_observability_integration_testchaosobservabilitybridge_test_correlations_list_grows`
- **Target:** `atom-federation-os/orchestration/chaos/observability_integration.py:L185 :: chaos_observability_integration_chaosobservabilitybridge`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/core/federation/distributed_ledger.py:81:    Ledger grows ONLY via quorum consensus — no single node can append.
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gcpl.py:72:    1. Branch count grows without bound AND C(t) does not → 0
    ```
    ```
    /home/workspace/atom-federation-os/alignment/v106_liveness_proof.py:77:Between repeats: streak grows.
    ```

### INFERRED #calls-49
- **Source:** `atom-federation-os/tools/test_p7_bft.py:LL285 :: tools_test_p7_bft_test_federated_gateway_rejects_insufficient_quorum`
- **Target:** `atom-federation-os/core/federation/federated_gateway.py:L79 :: federation_federated_gateway_federatedexecutiongateway`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:3:Ceph Diagnostics — FIX-004 L4 CRITICAL: proper Ceph quorum + split-brain handling
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:5:  1.1 mon_count correct (total Mons vs quorum Mons)
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:8:  1.4 split-brain detection with single-MON quorum risk
    ```

### INFERRED #calls-50
- **Source:** `atom-federation-os/federation/delta_gossip/test_delta_gossip.py:LL317 :: delta_gossip_test_delta_gossip_testdeltagossipintegration_test_end_to_end_delta_flow`
- **Target:** `atom-federation-os/federation/delta_gossip/protocol.py:L139 :: delta_gossip_protocol_deltagossipprotocol`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:80:        3. Build connections based on data flow
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:125:        # Step 4: Build connections based on data flow
    ```
    ```
    /home/workspace/audit_repo/mas_factory/architect.py:261:        """Build data flow connections between roles"""
    ```

### INFERRED #calls-51
- **Source:** `atom-federation-os/formal_model/execution_equivalence/test_equivalence.py:LL99 :: execution_equivalence_test_equivalence_test_complex_federation_trace`
- **Target:** `atom-federation-os/formal_model/execution_equivalence/trace_normalizer.py:L68 :: execution_equivalence_trace_normalizer_compare_execution_traces`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/orchestration/tracing.py:13:    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:13:    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    ```
    ```
    /home/workspace/AsurDev/acos/recorder/recorder.py:79:        Query traces by filter. Returns list[dict].
    ```

### INFERRED #calls-52
- **Source:** `atom-federation-os/orchestration/chaos/test_observability_integration.py:LL179 :: chaos_test_observability_integration_testchaosobservabilitybridge_test_governor_block_rate_empty_returns_zero`
- **Target:** `atom-federation-os/orchestration/chaos/observability_integration.py:L185 :: chaos_observability_integration_chaosobservabilitybridge`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/tests/architecture/test_architecture_linter.py:36:    # Either exit 0 (no violations) or non-zero with only warnings.
    ```
    ```
    /home/workspace/push/tests/architecture/test_architecture_linter.py:105:    """When hard rules fail, the script returns non-zero."""
    ```
    ```
    /home/workspace/push/agents/metrics.py:79:    metrics requires zero changes at the call site.
    ```

### INFERRED #calls-53
- **Source:** `atom-federation-os/alignment/test_convergence.py:LL72 :: alignment_test_convergence_test_merge_auditor`
- **Target:** `atom-federation-os/consistency/test_cross_layer_invariant_engine.py:L21 :: consistency_test_cross_layer_invariant_engine_mockevent`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/alignment/convergence.py:305:    Invariant: auditor NEVER deletes merged events. Rollback = new event.
    ```
    ```
    /home/workspace/atom-federation-os/alignment/convergence.py:373:        self.auditor = MergeAuditor()
    ```
    ```
    /home/workspace/atom-federation-os/alignment/convergence.py:410:        result = self.auditor.audit_merge(
    ```

### INFERRED #calls-54
- **Source:** `atom-federation-os/tools/test_p7_bft.py:LL88 :: tools_test_p7_bft_test_bftqc_valid`
- **Target:** `atom-federation-os/core/federation/bft_quorum_certificate.py:L28 :: federation_bft_quorum_certificate_bftqc`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/scripts/optimize_lag_blend.py:283:        valid = [r for r in results if r.sharpe is not None]
    ```
    ```
    /home/workspace/push/scripts/optimize_lag_blend.py:284:        if not valid:
    ```
    ```
    /home/workspace/push/scripts/optimize_lag_blend.py:286:        best = max(valid, key=lambda r: r.sharpe)
    ```

### INFERRED #calls-55
- **Source:** `astrofin-sentinel-v5/meta_rl/basket.py:LL265 :: astrofin_sentinel_v5_meta_rl_basket_py_meta_rl_basket_basketevaluator_single_symbol_fallback`
- **Target:** `meta_rl/types.py:L149 :: meta_rl_types_symbolmetrics`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/data_provider.py:2:Primary: Yahoo Finance v8 (free, no key) + yfinance fallback
    ```
    ```
    /home/workspace/audit_repo/data_provider.py:229:    """yfinance library fallback (works for most standard symbols)."""
    ```
    ```
    /home/workspace/audit_repo/data_provider.py:367:    # 2. yfinance library fallback
    ```

### INFERRED #calls-56
- **Source:** `atom-federation-os/tests/test_orchestration_v75.py:LL127 :: tests_test_orchestration_v75_testconflictresolutionmatrix_test_resolve_empty_raises`
- **Target:** `atom-federation-os/orchestration/conflict_resolution_matrix.py:L3 :: orchestration_conflict_resolution_matrix_conflictresolutionmatrix`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/meta_rl/basket.py:125:            BasketMetrics (never raises — always returns safe result)
    ```
    ```
    /home/workspace/audit_repo/agents/metrics.py:66:# same object — prometheus_client raises on duplicate metric registration.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/synthesis_agent.py:33:    Performs runtime validation: raises ValueError if weights don't sum to 1.0.
    ```

### INFERRED #calls-57
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL48 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_masfactory_fallback_on_error`
- **Target:** `atom-federation-os/tools/test_p0_4_import_sandbox.py:L12 :: tools_test_p0_4_import_sandbox_run_test`
- **Confidence:** 0.800  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:3:Thompson Sampling CLI — test and inspect agent selection.
    ```
    ```
    /home/workspace/push/mas_factory/atom_032_e2e_test.py:116:            "session_id": "test-e2e",
    ```
    ```
    /home/workspace/push/mas_factory/architect.py:174:        elif any(w in lower for w in ["backtest", "test", "historical"]):
    ```

---

## Bucket: relation = `contains` (50 edges)

### INFERRED #contains-1
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL173 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L173 :: monitoring_health_endpoints_karl_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-2
- **Source:** `agents/_impl/amre/idea_buffer_integration.py:LL142 :: agents_impl_amre_idea_buffer_integration_py_amre_idea_buffer_integration`
- **Target:** `agents/_impl/amre/idea_buffer_integration.py:L142 :: agents_impl_amre_idea_buffer_integration_py_amre_idea_buffer_integration_karl_evaluate_idea`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:186:        for idea in ideas:
    ```
    ```
    /home/workspace/tools/thompson_cli.py:187:            print(f"  [{idea['category']}]")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:188:            print(f"    → {idea['prompt']}\n")
    ```

### INFERRED #contains-3
- **Source:** `AsurDev/ml_engine/__init__.py:LL38 :: asurdev_ml_engine_init_py_ml_engine_init`
- **Target:** `AsurDev/ml_engine/__init__.py:L38 :: ml_engine_init_retrainer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ml_engine/__init__.py:6:labels.py   load_model.py     evaluate.py  predictor.py   retrainer.py
    ```
    ```
    /home/workspace/AsurDev/ml_engine/feedback/__init__.py:2:from .retrainer import Retrainer
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/__init__.py:2:from .retrainer import Retrainer
    ```

### INFERRED #contains-4
- **Source:** `AsurDev/v6/constraint_engine/engine.py:LL44 :: asurdev_v6_constraint_engine_engine_py_constraint_engine_engine`
- **Target:** `AsurDev/v6/constraint_engine/engine.py:L44 :: asurdev_v6_constraint_engine_engine_py_constraint_engine_engine_constraintengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/__init__.py:4:from mas_factory.engine import (
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:13:from mas_factory.engine import TopologyExecutor
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:166:    engine = MetaQuestioningEngine()
    ```

### INFERRED #contains-5
- **Source:** `AsurDev/l9_ebl/policy_compiler/compiler.py:LL11 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler`
- **Target:** `AsurDev/l9_ebl/policy_compiler/compiler.py:L11 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_constraintnode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos.py:18:from l9_ebl.policy_compiler.compiler import PolicyCompiler, GuardRule
    ```
    ```
    /home/workspace/AsurDev/acos.py:78:  └── Policy compiler (policy → executable constraint graph)
    ```
    ```
    /home/workspace/AsurDev/acos_cli.py:22:    from ete.compiler.dag import DAGCompiler
    ```

### INFERRED #contains-6
- **Source:** `agents/_impl/amre/astro_reward.py:LL160 :: agents_impl_amre_astro_reward_py_amre_astro_reward`
- **Target:** `agents/_impl/amre/astro_reward.py:L160 :: agents_impl_amre_astro_reward_py_amre_astro_reward_get_astro_market_phase`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/scripts/optimize_lag_blend.py:389:    ax.set_xlabel("Blend (mature phase)")
    ```
    ```
    /home/workspace/push/agents/gitagent_exporter.py:126:        "description": "Market cycle analysis: 20/40/80 day cycles, phase detection, turn points",
    ```
    ```
    /home/workspace/push/agents/_impl/bull_researcher.py:261:        summary = f"Jupiter: {jupiter.longitude:.1f}°, Moon phase: {moon_phase:.0f}%"
    ```

### INFERRED #contains-7
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL74 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L74 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_policyblock`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos_cli.py:22:    from ete.compiler.dag import DAGCompiler
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/feature_registry.py:4:Transforms pipeline into deterministic function compiler.
    ```
    ```
    /home/workspace/AsurDev/astrofin/constraint_compiler.py:240:    compiler = AstroFinConstraintCompiler()
    ```

### INFERRED #contains-8
- **Source:** `agents/_impl/amre/meta_questioning.py:LL30 :: agents_impl_amre_meta_questioning_py_amre_meta_questioning`
- **Target:** `agents/_impl/amre/meta_questioning.py:L30 :: agents_impl_amre_meta_questioning_py_amre_meta_questioning_metaquestionbank`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/atom_033_production_test.py:107:        cprint("  ✅ PASSED (meta-questioning active)", "92")
    ```
    ```
    /home/workspace/push/mas_factory/engine.py:8:- Meta-questioning as topology change driver
    ```
    ```
    /home/workspace/push/mas_factory/engine.py:191:            logger.debug(f"Meta-questioning skipped: {e}")
    ```

### INFERRED #contains-9
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL33 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L33 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_nodemetrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/tests/unit/test_determinism.py:3:Determinism Tests (L10) — verify scheduler produces same decision for same input.
    ```
    ```
    /home/workspace/AsurDev/tests/unit/test_determinism.py:82:    """Test 3: Deduplication — scheduler must not double-submit."""
    ```
    ```
    /home/workspace/AsurDev/acos_cli.py:24:    from ete.scheduler.adapter import SchedulerAdapter
    ```

### INFERRED #contains-10
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL50 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L50 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_storagebackendcontract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:18:    - When the contract changes, ONE place to update.
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:54:    Canonical test contract for an AstroFin Sentinel V5 agent.
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:140:        # The contract: never raise. Either succeed or degrade cleanly.
    ```

### INFERRED #contains-11
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL83 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L83 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ceph_storage_total`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/strategies/generator.py:315:    wins, losses, total = 0, 0, 0
    ```
    ```
    /home/workspace/push/strategies/generator.py:339:            total += 1
    ```
    ```
    /home/workspace/push/strategies/generator.py:354:        total += 1
    ```

### INFERRED #contains-12
- **Source:** `AsurDev/acos/events/event.py:LL15 :: asurdev_acos_events_event_py_events_event`
- **Target:** `AsurDev/acos/events/event.py:L15 :: asurdev_acos_events_event_py_events_event_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/session.py:35:    from sqlalchemy import create_engine, event
    ```
    ```
    /home/workspace/push/db/session.py:48:    @event.listens_for(engine, "connect")
    ```
    ```
    /home/workspace/push/tests/test_logging.py:18:    logger.info("Test event")
    ```

### INFERRED #contains-13
- **Source:** `agents/_impl/amre/reward.py:LL286 :: agents_impl_amre_reward_py_amre_reward`
- **Target:** `agents/_impl/amre/reward.py:L286 :: agents_impl_amre_reward_py_amre_reward_get_correlation_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:165:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```

### INFERRED #contains-14
- **Source:** `AsurDev/acos/scl_v5.py:LL71 :: asurdev_acos_scl_v5_py_acos_scl_v5`
- **Target:** `AsurDev/acos/scl_v5.py:L71 :: asurdev_acos_scl_v5_py_acos_scl_v5_test_invariant_6`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:66:    print(f"{'Agent':<22} {'Sample':>8}  {'Alpha':>6}  {'Beta':>6}  {'Mean':>7}  Sessions")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:73:                f"{belief.alpha:>6.2f}  {belief.beta:>6.2f}  "
    ```
    ```
    /home/workspace/tools/thompson_cli.py:223:        print(f"{'ID':<16} {'Status':<12} {'Score':>6} {'Impact':>8} {'Category':<20}")
    ```

### INFERRED #contains-15
- **Source:** `AsurDev/tests/unit/test_determinism.py:LL49 :: asurdev_tests_unit_test_determinism_py_unit_test_determinism`
- **Target:** `AsurDev/tests/unit/test_determinism.py:L49 :: asurdev_tests_unit_test_determinism_py_unit_test_determinism_test_same_seed_same_node`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/tests/test_agent_http_migration.py:10:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```
    ```
    /home/workspace/audit_repo/tests/test_agent_http_migration.py:12:        f"{node.module}.{alias.name}"
    ```
    ```
    /home/workspace/audit_repo/tests/test_agent_http_migration.py:13:        for node in ast.walk(tree)
    ```

### INFERRED #contains-16
- **Source:** `AsurDev/tests/integration/test_ml_pipeline.py:LL40 :: integration_test_ml_pipeline`
- **Target:** `AsurDev/tests/integration/test_ml_pipeline.py:L40 :: integration_test_ml_pipeline_generate_synthetic_dataset`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/agents/_impl/quant_agent.py:156:        # Simple momentum: % change over dataset
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/quant_agent.py:156:        # Simple momentum: % change over dataset
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:80:    Every transition writes to the event log for ML dataset generation.
    ```

### INFERRED #contains-17
- **Source:** `AsurDev/acos/scl_v5.py:LL127 :: asurdev_acos_scl_v5_py_acos_scl_v5`
- **Target:** `AsurDev/acos/scl_v5.py:L127 :: asurdev_acos_scl_v5_py_acos_scl_v5_test_trace_record`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:145:        print(f"Reset {deleted} record(s) for '{args.agent}'")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:148:        print(f"Reset all {deleted} belief record(s)")
    ```
    ```
    /home/workspace/audit_repo/meta_rl/persistence.py:56:        """Append a ScoredStrategy record to the session's strategies file."""
    ```

### INFERRED #contains-18
- **Source:** `AsurDev/ete/store/trace_store.py:LL25 :: asurdev_ete_store_trace_store_py_store_trace_store`
- **Target:** `AsurDev/ete/store/trace_store.py:L25 :: asurdev_ete_store_trace_store_py_store_trace_store_tracenode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/backtest/metrics_agent.py:133:    """SQLite-backed metrics store for all backtest runs."""
    ```
    ```
    /home/workspace/push/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/push/web/utils/notifications.py:69:# Singleton store for active toasts
    ```

### INFERRED #contains-19
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL51 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L51 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_mock_lag_window`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #contains-20
- **Source:** `AsurDev/acos/cli/monitor.py:LL37 :: asurdev_acos_cli_monitor_py_cli_monitor`
- **Target:** `AsurDev/acos/cli/monitor.py:L37 :: asurdev_acos_cli_monitor_py_cli_monitor_get_tunnel_status`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:226:            print(f"  {idea.id:<14} {idea.status:<12} {idea.score:>6.2f} {idea.impact_score:>8.4f} {idea.category:<20}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:261:    elif args.status:
    ```
    ```
    /home/workspace/tools/thompson_cli.py:264:        status = args.status
    ```

### INFERRED #contains-21
- **Source:** `AsurDev/v6/digital_twin/simulator.py:LL58 :: asurdev_v6_digital_twin_simulator_py_digital_twin_simulator`
- **Target:** `AsurDev/v6/digital_twin/simulator.py:L58 :: asurdev_v6_digital_twin_simulator_py_digital_twin_simulator_predictedevent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos.py:61:  └── Digital twin simulator
    ```
    ```
    /home/workspace/AsurDev/v6/digital_twin/simulator.py:78:    Deterministic forward simulator.
    ```
    ```
    /home/workspace/AsurDev/v6/solver/optimizer_api.py:58:    from v6.digital_twin.simulator import DigitalTwin, SimState, NodeState
    ```

### INFERRED #contains-22
- **Source:** `AsurDev/tests/unit/test_determinism.py:LL99 :: asurdev_tests_unit_test_determinism_py_unit_test_determinism`
- **Target:** `AsurDev/tests/unit/test_determinism.py:L99 :: asurdev_tests_unit_test_determinism_py_unit_test_determinism_test_low_priority_throttled`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/admission_controller/controller.py:93:                    f"Low priority throttled: load {avg_load:.1f}% >= {LOAD_THRESHOLD_LOW_PRI*100:.0f}%",
    ```
    ```
    /home/workspace/AsurDev/admission_controller/controller.py:100:                    f"Low priority throttled (load={avg_load:.1f}%)",
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/controller.py:90:                    f"Low priority throttled: load {avg_load:.1f}% >= {LOAD_THRESHOLD_LOW_PRI*100:.0f}%",
    ```

### INFERRED #contains-23
- **Source:** `AsurDev/feature_pipeline/schemas.py:LL30 :: asurdev_feature_pipeline_schemas_py_feature_pipeline_schemas`
- **Target:** `AsurDev/feature_pipeline/schemas.py:L30 :: asurdev_feature_pipeline_schemas_py_feature_pipeline_schemas_labeltype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/tests/test_ml_api.py:177:        from ml_engine.inference.schemas import MetricsInput
    ```
    ```
    /home/workspace/AsurDev/tests/test_ml_api.py:184:        from ml_engine.inference.schemas import MetricsInput
    ```
    ```
    /home/workspace/AsurDev/tests/test_ml_api.py:191:        from ml_engine.inference.schemas import PredictionResponse
    ```

### INFERRED #contains-24
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL12 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L12 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_driftsample`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/thompson_cli.py:3:Thompson Sampling CLI — test and inspect agent selection.
    ```
    ```
    /home/workspace/push/mas_factory/atom_032_e2e_test.py:116:            "session_id": "test-e2e",
    ```
    ```
    /home/workspace/push/mas_factory/architect.py:174:        elif any(w in lower for w in ["backtest", "test", "historical"]):
    ```

### INFERRED #contains-25
- **Source:** `AsurDev/astrofin/gateway/submission.py:LL20 :: asurdev_astrofin_gateway_submission_py_gateway_submission`
- **Target:** `AsurDev/astrofin/gateway/submission.py:L20 :: asurdev_astrofin_gateway_submission_py_gateway_submission_acossubmissiongateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/astrofin/gateway/submission.py:111:    # Test 1: Normal submission
    ```
    ```
    /home/workspace/AsurDev/astrofin/meta_rl/engine.py:110:            # Placeholder: call ACOS submission gateway
    ```
    ```
    /home/workspace/AsurDev/astrofin/meta_rl/engine.py:158:    Bridge: MetaRL → ACOS submission gateway.
    ```

### INFERRED #contains-26
- **Source:** `AstroFinSentinelV5/tests/test_ai_editorconfig.py:LL6 :: astrofinsentinelv5_tests_test_ai_editorconfig_py_tests_test_ai_editorconfig`
- **Target:** `AstroFinSentinelV5/tests/test_ai_editorconfig.py:L6 :: astrofinsentinelv5_tests_test_ai_editorconfig_py_tests_test_ai_editorconfig_test_cursorrules_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_ai_editorconfig.py
    ```

### INFERRED #contains-27
- **Source:** `AsurDev/acos/cli/monitor.py:LL115 :: asurdev_acos_cli_monitor_py_cli_monitor`
- **Target:** `AsurDev/acos/cli/monitor.py:L115 :: asurdev_acos_cli_monitor_py_cli_monitor_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:278:def main():
    ```
    ```
    /home/workspace/tools/thompson_cli.py:357:    main()
    ```
    ```
    /home/workspace/tools/db_monitor.py:81:def main():
    ```

### INFERRED #contains-28
- **Source:** `agents/_impl/amre/backtest_loop.py:LL44 :: agents_impl_amre_backtest_loop_py_amre_backtest_loop`
- **Target:** `agents/_impl/amre/backtest_loop.py:L44 :: agents_impl_amre_backtest_loop_py_amre_backtest_loop_backtestresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/FINAL_INTEGRATION_TEST.py:153:    """Test KARL self-improvement loop"""
    ```
    ```
    /home/workspace/FINAL_INTEGRATION_TEST.py:189:        print_test("KARL loop", False, str(e)[:80])
    ```
    ```
    /home/workspace/push/mas_factory/engine.py:220:            loop = asyncio.get_event_loop()
    ```

### INFERRED #contains-29
- **Source:** `agents/_impl/amre/oap_optimizer.py:LL18 :: agents_impl_amre_oap_optimizer_py_amre_oap_optimizer`
- **Target:** `agents/_impl/amre/oap_optimizer.py:L18 :: agents_impl_amre_oap_optimizer_py_amre_oap_optimizer_controlaction`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/agents/karl_synthesis.py:341:        # ── Step 8: Update OAP optimizer ─────────────────────────────────────────
    ```
    ```
    /home/workspace/push/agents/_impl/amre/karl_optimizer.py:97:# Global optimizer instance
    ```
    ```
    /home/workspace/push/agents/_impl/amre/karl_optimizer.py:102:    """Main optimizer for KARL loop performance."""
    ```

### INFERRED #contains-30
- **Source:** `AsurDev/astrofin/trace_schema/trace.py:LL73 :: asurdev_astrofin_trace_schema_trace_py_trace_schema_trace`
- **Target:** `AsurDev/astrofin/trace_schema/trace.py:L73 :: asurdev_astrofin_trace_schema_trace_py_trace_schema_trace_trace_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/db_monitor.py:41:                dist = dict(cur.fetchall())
    ```
    ```
    /home/workspace/tools/db_monitor.py:44:                dist = dict(cur.fetchall())
    ```
    ```
    /home/workspace/tools/thompson_cli.py:117:    counts = dict.fromkeys(pool.agents, 0)
    ```

### INFERRED #contains-31
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL104 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L104 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #contains-32
- **Source:** `AstroFinSentinelV5/web/app.py:LL134 :: astrofinsentinelv5_web_app_py_web_app`
- **Target:** `AstroFinSentinelV5/web/app.py:L134 :: astrofinsentinelv5_web_app_py_web_app_update_clock`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/app.py
    ```

### INFERRED #contains-33
- **Source:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:LL48 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter`
- **Target:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:L48 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_build_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/metrics_server.py:2:"""Prometheus metrics server for AstroFin Sentinel V5.
    ```
    ```
    /home/workspace/tools/metrics_server.py:27:from meta_rl.metrics import *  # re-export
    ```
    ```
    /home/workspace/tools/metrics_server.py:48:    app.router.add_get("/metrics", metrics_handler)
    ```

### INFERRED #contains-34
- **Source:** `agents/_impl/amre/reward.py:LL230 :: agents_impl_amre_reward_py_amre_reward`
- **Target:** `agents/_impl/amre/reward.py:L230 :: agents_impl_amre_reward_py_amre_reward_drawdownstate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/nightly_export.py:39:            logger.info(f"  {s.id}: reward={s.reward:.4f}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:252:        reward = args.reward
    ```
    ```
    /home/workspace/tools/thompson_cli.py:253:        if reward is None:
    ```

### INFERRED #contains-35
- **Source:** `AsurDev/l9_ebl/policy_compiler/compiler.py:LL48 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler`
- **Target:** `AsurDev/l9_ebl/policy_compiler/compiler.py:L48 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_policycompiler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/ete/compiler/dag.py:126:    compiler = DAGCompiler()
    ```
    ```
    /home/workspace/AsurDev/ete/compiler/dag.py:128:    dag = compiler.compile(job)
    ```
    ```
    /home/workspace/AsurDev/ete/compiler/dag.py:130:    ok, errs = compiler.validate_dag(dag)
    ```

### INFERRED #contains-36
- **Source:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:LL90 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter`
- **Target:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:L90 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter_handler`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/scripts/architecture_linter.py:11:    R4.  Any HTTP route handler under web/ must use @require_auth (or be
    ```
    ```
    /home/workspace/push/scripts/architecture_linter.py:218:                    f"route handler '{node.name}' is missing @require_auth",
    ```
    ```
    /home/workspace/push/tools/metrics_server.py:63:async def metrics_middleware(request, handler):
    ```

### INFERRED #contains-37
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL35 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L35 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_blackrock_tests.py:39:    parser = argparse.ArgumentParser(description="BlackRock six-test validator")
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_blackrock_tests.py:62:    print("BlackRock six-test validator:")
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_agent.py:5:Per-agent validator for AstroFin Sentinel V5.
    ```

### INFERRED #contains-38
- **Source:** `AsurDev/tests/test_amneziawg_integration.py:LL123 :: asurdev_tests_test_amneziawg_integration_py_tests_test_amneziawg_integration`
- **Target:** `AsurDev/tests/test_amneziawg_integration.py:L123 :: asurdev_tests_test_amneziawg_integration_py_tests_test_amneziawg_integration_test_awg_trace_id_required`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:254:            print("Reward is required for evaluation.")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:280:    sub = parser.add_subparsers(dest="cmd", required=True)
    ```
    ```
    /home/workspace/tools/metrics_server.py:14:# Metrics required by rag_retriever and other modules
    ```

### INFERRED #contains-39
- **Source:** `AsurDev/v6/solver/optimizer_api.py:LL53 :: asurdev_v6_solver_optimizer_api_py_solver_optimizer_api`
- **Target:** `AsurDev/v6/solver/optimizer_api.py:L53 :: asurdev_v6_solver_optimizer_api_py_solver_optimizer_api_get_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/trading/risk_v2.py:263:    engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
    ```
    ```
    /home/workspace/trading/risk_v2.py:264:    engine.update_equity(100_000)
    ```
    ```
    /home/workspace/trading/risk_v2.py:265:    engine.update_equity(88_000)
    ```

### INFERRED #contains-40
- **Source:** `AsurDev/acos/scl_v5.py:LL40 :: asurdev_acos_scl_v5_py_acos_scl_v5`
- **Target:** `AsurDev/acos/scl_v5.py:L40 :: asurdev_acos_scl_v5_py_acos_scl_v5_test_invariant_3`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/nightly_export.py:32:        top = strategy_pool.get_top(n=3)
    ```
    ```
    /home/workspace/tools/thompson_cli.py:108:            f"  {rank:<3} {row['agent_name']:<22} {row['mean_accuracy']:>7.4f}  "
    ```
    ```
    /home/workspace/tools/metrics_server.py:22:    "astrofin_rag_relevance_score", "Relevance score of RAG chunks", buckets=(0.1, 0.3, 0.5, 0.7, 0.9, 1.0)
    ```

### INFERRED #contains-41
- **Source:** `AsurDev/load_test/evolution/evolver.py:LL28 :: asurdev_load_test_evolution_evolver_py_evolution_evolver`
- **Target:** `AsurDev/load_test/evolution/evolver.py:L28 :: asurdev_load_test_evolution_evolver_py_evolution_evolver_generationsummary`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/load_test/orchestrator/__main__.py:11:from load_test.evolution.evolver import SystemEvolver
    ```
    ```
    /home/workspace/AsurDev/load_test/orchestrator/__main__.py:81:    evolver = SystemEvolver()
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/orchestrator/__main__.py:14:from load_test.evolution.evolver import SystemEvolver
    ```

### INFERRED #contains-42
- **Source:** `agents/_impl/amre/ensemble_selection.py:LL30 :: agents_impl_amre_ensemble_selection_py_amre_ensemble_selection`
- **Target:** `agents/_impl/amre/ensemble_selection.py:L30 :: agents_impl_amre_ensemble_selection_py_amre_ensemble_selection_select_ensemble_by_confidence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/strategies/generator.py:159:            confidence=int(conf),
    ```
    ```
    /home/workspace/push/strategies/generator.py:324:        if result.signal == Signal.LONG and result.confidence >= conf and pos == 0:
    ```
    ```
    /home/workspace/push/strategies/generator.py:328:        elif result.signal == Signal.SHORT and result.confidence >= conf and pos == 0:
    ```

### INFERRED #contains-43
- **Source:** `AsurDev/v6/solver/optimizer.py:LL27 :: asurdev_v6_solver_optimizer_py_solver_optimizer`
- **Target:** `AsurDev/v6/solver/optimizer.py:L27 :: asurdev_v6_solver_optimizer_py_solver_optimizer_solverresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/agents/karl_synthesis.py:341:        # ── Step 8: Update OAP optimizer ─────────────────────────────────────────
    ```
    ```
    /home/workspace/push/agents/_impl/amre/karl_optimizer.py:97:# Global optimizer instance
    ```
    ```
    /home/workspace/push/agents/_impl/amre/karl_optimizer.py:102:    """Main optimizer for KARL loop performance."""
    ```

### INFERRED #contains-44
- **Source:** `AsurDev/v8/constraint_compiler/compiler.py:LL96 :: asurdev_v8_constraint_compiler_compiler_py_constraint_compiler_compiler`
- **Target:** `AsurDev/v8/constraint_compiler/compiler.py:L96 :: asurdev_v8_constraint_compiler_compiler_py_constraint_compiler_compiler_constraintregistry`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos_cli.py:22:    from ete.compiler.dag import DAGCompiler
    ```
    ```
    /home/workspace/AsurDev/feature_pipeline/feature_registry.py:4:Transforms pipeline into deterministic function compiler.
    ```
    ```
    /home/workspace/AsurDev/astrofin/constraint_compiler.py:240:    compiler = AstroFinConstraintCompiler()
    ```

### INFERRED #contains-45
- **Source:** `AsurDev/v6/solver/ilp/or_ilp.py:LL24 :: asurdev_v6_solver_ilp_or_ilp_py_ilp_or_ilp`
- **Target:** `AsurDev/v6/solver/ilp/or_ilp.py:L24 :: asurdev_v6_solver_ilp_or_ilp_py_ilp_or_ilp_ilpsolver`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/v6/solver/optimizer.py:30:    solver_layer: str             # "ilp" | "heuristic" | "exploration"
    ```
    ```
    /home/workspace/AsurDev/v6/solver/optimizer.py:198:        self.ilp = ILPOptimizer(timeout_ms=self.config.ilp_timeout_ms)
    ```
    ```
    /home/workspace/AsurDev/v6/solver/optimizer.py:241:            assignment = self.ilp.solve([job_id], {job_id: [n for n, _ in valid]}, utilities)
    ```

### INFERRED #contains-46
- **Source:** `AsurDev/ml_engine/__init__.py:LL14 :: asurdev_ml_engine_init_py_ml_engine_init`
- **Target:** `AsurDev/ml_engine/__init__.py:L14 :: ml_engine_init_timeseriessplitter`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:268:        "--init-single",
    ```
    ```
    /home/workspace/audit_repo/meta_rl/calibration.py:143:            logger.warning(f"[CALIBRATION] schema init failed: {exc}")
    ```

### INFERRED #contains-47
- **Source:** `AsurDev/v7/policy_governor/governor.py:LL45 :: asurdev_v7_policy_governor_governor_py_policy_governor_governor`
- **Target:** `AsurDev/v7/policy_governor/governor.py:L45 :: asurdev_v7_policy_governor_governor_py_policy_governor_governor_policygovernor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos_correction/rca_engine.py:175:                "file": "v7/policy_governor/governor.py",
    ```
    ```
    /home/workspace/AsurDev/acos.py:64:  ├── Policy governor
    ```
    ```
    /home/workspace/atom-federation-os/resilience/tests/test_v67_meta_coherence.py:273:    assert mc.governor.mode == GovernorMode.STRICT
    ```

### INFERRED #contains-48
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL47 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L47 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctiondecision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/engine.py:220:            loop = asyncio.get_event_loop()
    ```
    ```
    /home/workspace/audit_repo/mas_factory/engine.py:222:            loop = asyncio.new_event_loop()
    ```
    ```
    /home/workspace/audit_repo/mas_factory/engine.py:223:            asyncio.set_event_loop(loop)
    ```

### INFERRED #contains-49
- **Source:** `AsurDev/slsa4/scripts/slsa4_policy_engine.py:LL99 :: scripts_slsa4_policy_engine`
- **Target:** `AsurDev/slsa4/scripts/slsa4_policy_engine.py:L99 :: scripts_slsa4_policy_engine_h`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/healthcheck.py:27:            ["pg_isready", "-h", "localhost", "-p", "5432"],
    ```
    ```
    /home/workspace/tools/healthcheck.py:44:                ["pg_isready", "-h", "localhost", "-p", "5432"],
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/meta_questioning.py:197:        passed = sum(1 for h in self.history if h.get("passed", False))
    ```

### INFERRED #contains-50
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL31 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L31 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:18:    - When the contract changes, ONE place to update.
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:54:    Canonical test contract for an AstroFin Sentinel V5 agent.
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:140:        # The contract: never raise. Either succeed or degrade cleanly.
    ```

---

## Bucket: relation = `rationale_for` (50 edges)

### INFERRED #rationale_for-1
- **Source:** `_sbs_old/adapters.py:LL1 :: sbs_old_adapters_rationale_1`
- **Target:** `_sbs_old/adapters.py:L1 :: sbs_old_adapters`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/mas_factory/visualizer.py:19:        "adapter": "#607D8B",  # Gray for adapters
    ```
    ```
    /home/workspace/audit_repo/mas_factory/adapters.py:1:"""mas_factory/adapters.py - Context adapters between agents"""
    ```
    ```
    /home/workspace/audit_repo/mas_factory/adapters.py:117:    adapters = {
    ```

### INFERRED #rationale_for-2
- **Source:** `_sbs_old/tests/test_sbs_runtime.py:LL252 :: tests_test_sbs_runtime_rationale_252`
- **Target:** `_sbs_old/tests/test_sbs_runtime.py:L251 :: sbs_old_tests_test_sbs_runtime_py_tests_test_sbs_runtime_testexecutionloopsbs_test_execute_with_sbs_fallback_without_layers`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/l10_self_healing/orchestrator/failure_isolation.py:138:                        f"CASCADE_RISK: incident={incident.incident_id} shares layers {shared_layers} "
    ```
    ```
    /home/workspace/AsurDev/l10_self_healing/watchdog/watchdog.py:4:Monitors health across all layers, triggers isolation on failure.
    ```
    ```
    /home/workspace/AsurDev/acos.py:279:            reason="All layers passed",
    ```

### INFERRED #rationale_for-3
- **Source:** `_sbs_old/system_contract.py:LL120 :: sbs_old_system_contract_rationale_120`
- **Target:** `_sbs_old/system_contract.py:L119 :: sbs_old_system_contract_system_contract_is_loaded`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/test_compromise_agent.py:8:project code is loaded. Once a proper conftest at tests/conftest.py
    ```
    ```
    /home/workspace/push/meta_rl/evolution.py:445:            loaded = get_persistence().load_evolution_session(self.session_id)
    ```
    ```
    /home/workspace/push/meta_rl/evolution.py:446:            if not loaded:
    ```

### INFERRED #rationale_for-4
- **Source:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:LL15 :: wireguard_wg_exporter_rationale_15`
- **Target:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:L14 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter_parse_wg_show`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:6:    python tools/thompson_cli.py scores --pool astro        # show all agents + sampled scores
    ```
    ```
    /home/workspace/tools/thompson_cli.py:11:    python tools/thompson_cli.py daily-brief                # show latest brief
    ```
    ```
    /home/workspace/tools/thompson_cli.py:115:    """Simulate N Thompson sampling runs and show selection frequency."""
    ```

### INFERRED #rationale_for-5
- **Source:** `agents/_impl/amre/audit.py:LL1 :: agents_impl_amre_audit_py_amre_audit_rationale_1`
- **Target:** `agents/_impl/amre/audit.py:L1 :: agents_impl_amre_audit_py_amre_audit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:280:    print("[4/4] Analyzing audit drift...")
    ```
    ```
    /home/workspace/push/db/models.py:130:    """Immutable audit log record."""
    ```
    ```
    /home/workspace/push/agents/karl_synthesis.py:6:  DecisionRecord → OAP update → Backtest sample → Sync audit
    ```

### INFERRED #rationale_for-6
- **Source:** `_sbs_old/runtime.py:LL68 :: sbs_old_runtime_rationale_68`
- **Target:** `_sbs_old/runtime.py:L67 :: sbs_old_runtime_violationpolicy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/tests/test_karl_synthesis_lag.py:56:        "ema": 68.4,
    ```
    ```
    /home/workspace/push/tests/test_karl_synthesis_lag.py:117:        assert meta["ema_confidence"] == 68.4
    ```
    ```
    /home/workspace/push/tests/test_karl_synthesis_lag.py:205:                "ema": 68.4,
    ```

### INFERRED #rationale_for-7
- **Source:** `_sbs_old/tests/test_invariants.py:LL222 :: tests_test_invariants_rationale_222`
- **Target:** `_sbs_old/tests/test_invariants.py:L221 :: sbs_old_tests_test_invariants_py_tests_test_invariants_testfailureclassifier`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'testfailureclassifier' not found in _sbs_old/tests/test_invariants.py
    ```

### INFERRED #rationale_for-8
- **Source:** `AsurDev/load_test/evolution/evolver.py:LL42 :: evolution_evolver_rationale_42`
- **Target:** `AsurDev/load_test/evolution/evolver.py:L41 :: asurdev_load_test_evolution_evolver_py_evolution_evolver_evolutionengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/thompson_cli.py:314:    p_sim.add_argument("--seed", type=int, default=42)
    ```
    ```
    /home/workspace/push/backtest/metrics_agent.py:13:  agent.record("BTCUSDT", 2025, win_rate=63.5, sharpe=1.42, trades=142)
    ```
    ```
    /home/workspace/push/training/train_residual_model.py:46:    np.random.seed(42)
    ```

### INFERRED #rationale_for-9
- **Source:** `_sbs_old/failure_classifier.py:LL40 :: sbs_old_failure_classifier_rationale_40`
- **Target:** `_sbs_old/failure_classifier.py:L39 :: sbs_old_failure_classifier_failureseverity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/topology.py:438:            condition="confidence < 40",
    ```
    ```
    /home/workspace/push/mas_factory/topology.py:443:                "threshold": 40,
    ```
    ```
    /home/workspace/push/mas_factory/topology.py:444:                "description": "Adds validation when confidence < 40",
    ```

### INFERRED #rationale_for-10
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL1 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L1 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #rationale_for-11
- **Source:** `AsurDev/v6/digital_twin/simulator.py:LL216 :: digital_twin_simulator_rationale_216`
- **Target:** `AsurDev/v6/digital_twin/simulator.py:L209 :: asurdev_v6_digital_twin_simulator_py_digital_twin_simulator_digitaltwin_evaluate_action`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/nightly_export.py:61:    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:275:        print("No action specified for idea tracker. Use --kpi, --list, --pending, --inject, --eval, or --status.")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:326:    p_daily_brief.add_argument("--list", action="store_true", help="List all briefs")
    ```

### INFERRED #rationale_for-12
- **Source:** `Projects/Loopcraft/loopcraft_demo.py:LL92 :: loopcraft_loopcraft_demo_rationale_92`
- **Target:** `Projects/Loopcraft/loopcraft_demo.py:L91 :: loopcraft_loopcraft_demo_cyclestate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_033_production_test.py:13:def cprint(msg, color="92"):
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_033_production_test.py:43:        cprint("  ✅ PASSED", "92")
    ```
    ```
    /home/workspace/audit_repo/mas_factory/atom_033_production_test.py:68:        cprint("  ✅ PASSED (< 100ms)", "92")
    ```

### INFERRED #rationale_for-13
- **Source:** `agents/_impl/amre/test_lag_windowing.py:LL163 :: agents_impl_amre_test_lag_windowing_py_amre_test_lag_windowing_rationale_163`
- **Target:** `agents/_impl/amre/test_lag_windowing.py:L162 :: agents_impl_amre_test_lag_windowing_py_amre_test_lag_windowing_testwarmupblend_test_mature_blend_after_20`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:72:                f"  {name:<20} {score:>8.4f}  "
    ```
    ```
    /home/workspace/tools/thompson_cli.py:78:            print(f"  {name:<20} {score:>8.4f}  (unseen, Beta(1{bonus_note},1))")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:137:        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    ```

### INFERRED #rationale_for-14
- **Source:** `AsurDev/ete/gate/governance_gate.py:LL20 :: gate_governance_gate_rationale_20`
- **Target:** `AsurDev/ete/gate/governance_gate.py:L19 :: asurdev_ete_gate_governance_gate_py_gate_governance_gate_governancegate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/knowledge/build_index.py:58:            if not body or len(body) < 20:
    ```
    ```
    /home/workspace/knowledge/daily_brief/daily_brief.py:59:        if len(text) > 20:  # Filter short noise
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker.py:292:    print(f"{'ID':<16} {'Status':<10} {'Score':>6} {'Impact':>8} {'Category':<20}")
    ```

### INFERRED #rationale_for-15
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL64 :: meta_rl_engine_rationale_64`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L63 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/core/coordination/test_pressure_field.py:68:        → B net: +0.70 - 0.85 = -0.15 → 65 + 0.15×(-0.15) = 64.98 (теряет)
    ```
    ```
    /home/workspace/audit_repo/core/coordination/test_pressure_field.py:68:        → B net: +0.70 - 0.85 = -0.15 → 65 + 0.15×(-0.15) = 64.98 (теряет)
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_wg.py:20:    prev_hash: str = field(default="0" * 64, repr=False)
    ```

### INFERRED #rationale_for-16
- **Source:** `FINAL_INTEGRATION_TEST.py:LL344 :: final_integration_test_rationale_344`
- **Target:** `FINAL_INTEGRATION_TEST.py:L343 :: final_integration_test_test_10_thompson_sampling`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:115:    """Simulate N Thompson sampling runs and show selection frequency."""
    ```
    ```
    /home/workspace/push/backtest/db_analysis.py:248:        print("  → Thompson sampling decisions not being logged")
    ```
    ```
    /home/workspace/push/tools/thompson_cli.py:114:    """Simulate N Thompson sampling runs and show selection frequency."""
    ```

### INFERRED #rationale_for-17
- **Source:** `agents/_impl/amre/self_question.py:LL110 :: agents_impl_amre_self_question_py_amre_self_question_rationale_110`
- **Target:** `agents/_impl/amre/self_question.py:L109 :: agents_impl_amre_self_question_py_amre_self_question_selfquestioningengine_answer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/ralph_agent.py:136:            answer = response.choices[0].message.content
    ```
    ```
    /home/workspace/audit_repo/scripts/ralph_agent.py:142:        print(f"🤖 Ответ модели:\n{answer}")
    ```
    ```
    /home/workspace/audit_repo/scripts/ralph_agent.py:143:        log_audit(AUDIT_LOG, task, answer, "LLM_DONE")
    ```

### INFERRED #rationale_for-18
- **Source:** `AsurDev/feature_pipeline/embedding.py:LL16 :: feature_pipeline_embedding_rationale_16`
- **Target:** `AsurDev/feature_pipeline/embedding.py:L15 :: asurdev_feature_pipeline_embedding_py_feature_pipeline_embedding_nodeembeddingbuilder`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tools/thompson_cli.py:223:        print(f"{'ID':<16} {'Status':<12} {'Score':>6} {'Impact':>8} {'Category':<20}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:235:        print(f"{'ID':<16} {'Score':>6} {'Category':<20} {'Text':<30}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:270:        print(f"{'ID':<16} {'Status':<12} {'Score':>6} {'Impact':>8} {'Category':<20}")
    ```

### INFERRED #rationale_for-19
- **Source:** `AsurDev/v6/solver/optimizer.py:LL205 :: solver_optimizer_rationale_205`
- **Target:** `AsurDev/v6/solver/optimizer.py:L201 :: asurdev_v6_solver_optimizer_py_solver_optimizer_hybridsolver_solve`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/knowledge/daily_digest/atom_proposer.py:213:            why_now="Показано 48.5% solve rate vs 12.6% conversation-based — "
    ```
    ```
    /home/workspace/push/knowledge/daily_digest/atom_proposer.py:213:            why_now="Показано 48.5% solve rate vs 12.6% conversation-based — "
    ```
    ```
    /home/workspace/AsurDev/v6/solver/optimizer.py:6:Layer 3: ILP (exact solve on small subset)
    ```

### INFERRED #rationale_for-20
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL102 :: correction_loop_loop_rationale_102`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L96 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/mas_factory/registry.py:176:        name="cycle",
    ```
    ```
    /home/workspace/push/agents/gitagent_exporter.py:126:        "description": "Market cycle analysis: 20/40/80 day cycles, phase detection, turn points",
    ```
    ```
    /home/workspace/push/agents/metrics.py:60:# the same agent in multiple collection cycles (each cycle re-imports
    ```

### INFERRED #rationale_for-21
- **Source:** `_sbs_old/tests/test_invariants.py:LL47 :: tests_test_invariants_rationale_47`
- **Target:** `_sbs_old/tests/test_invariants.py:L46 :: sbs_old_tests_test_invariants_py_tests_test_invariants_testsystemboundaryspec_test_quorum_violation_fail`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/bench/bench_diversity.py:16:        ev = EvaluationResult.fail()
    ```
    ```
    /home/workspace/bench/bench_diversity.py:41:    ev = EvaluationResult.fail()
    ```
    ```
    /home/workspace/bench/perf_debug.py:13:    pool.add(ScoredStrategy(strategy=st, reward=0.5+i*0.0001, evaluation=EvaluationResult.fail()))
    ```

### INFERRED #rationale_for-22
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL43 :: contracts_trace_contract_rationale_43`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L42 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract_list_traces`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/orchestration/tracing.py:13:    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    ```
    ```
    /home/workspace/audit_repo/orchestration/tracing.py:13:    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    ```
    ```
    /home/workspace/AsurDev/tests/test_amneziawg_integration.py:222:    print(f"  [OK{'=' if ok else '!'}] INV6 — O(1) lookup: {elapsed:.4f}s for 1000 lookups (100 traces)")
    ```

### INFERRED #rationale_for-23
- **Source:** `AsurDev/load_test/injectors/synthetic_scheduler.py:LL17 :: injectors_synthetic_scheduler_rationale_17`
- **Target:** `AsurDev/load_test/injectors/synthetic_scheduler.py:L16 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_nodestate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/backtest/test_metrics_agent.py:152:        losing_trades=17,
    ```
    ```
    /home/workspace/audit_repo/core/panchanga.py:136:    ("Krishna Dvitiya", 17),
    ```
    ```
    /home/workspace/push/backtest/test_metrics_agent.py:152:        losing_trades=17,
    ```

### INFERRED #rationale_for-24
- **Source:** `AsurDev/acos/recorder/recorder.py:LL108 :: recorder_recorder_rationale_108`
- **Target:** `AsurDev/acos/recorder/recorder.py:L107 :: asurdev_acos_recorder_recorder_py_recorder_recorder_deterministictracerecorder_clear`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/backtest/metrics_agent.py:247:    def clear(self, older_than_days: int = None) -> int:
    ```
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:149:    audit_log.records.clear()
    ```
    ```
    /home/workspace/push/backtest/atom_014_stress_test.py:151:    # calibrator.calibration_history.clear()
    ```

### INFERRED #rationale_for-25
- **Source:** `agents/_impl/amre/audit.py:LL89 :: agents_impl_amre_audit_py_amre_audit_rationale_89`
- **Target:** `agents/_impl/amre/audit.py:L88 :: agents_impl_amre_audit_py_amre_audit_decisionrecord`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/coherence/tests/test_v68_coherence.py:168:    snap2 = stab.compute_J(0.79, 0.89, 0.11)
    ```

### INFERRED #rationale_for-26
- **Source:** `AsurDev/acos/scl.py:LL86 :: asurdev_acos_scl_py_acos_scl_rationale_86`
- **Target:** `AsurDev/acos/scl.py:L85 :: asurdev_acos_scl_py_acos_scl_test_full_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/core/tracing.py:9:from opentelemetry import trace
    ```
    ```
    /home/workspace/push/core/tracing.py:12:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/push/core/tracing.py:13:from opentelemetry.sdk.trace.export import BatchSpanProcessor
    ```

### INFERRED #rationale_for-27
- **Source:** `agents/_impl/amre/reward.py:LL1 :: agents_impl_amre_reward_py_amre_reward_rationale_1`
- **Target:** `agents/_impl/amre/reward.py:L1 :: agents_impl_amre_reward_py_amre_reward`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/nightly_export.py:39:            logger.info(f"  {s.id}: reward={s.reward:.4f}")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:252:        reward = args.reward
    ```
    ```
    /home/workspace/tools/thompson_cli.py:253:        if reward is None:
    ```

### INFERRED #rationale_for-28
- **Source:** `AsurDev/load_test/orchestrator/__main__.py:LL39 :: orchestrator_main_rationale_39`
- **Target:** `AsurDev/load_test/orchestrator/__main__.py:L38 :: asurdev_load_test_orchestrator_main_py_orchestrator_main_compute_tag_stats`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/backtest/db_analysis.py:63:    # ── 1. Basic stats ──────────────────────────────────────────────────
    ```
    ```
    /home/workspace/push/db/repositories.py:423:    stats = {"backend": _BACKEND, "postgres_available": False}
    ```
    ```
    /home/workspace/push/db/repositories.py:425:        stats["postgres_available"] = is_postgres_available()
    ```

### INFERRED #rationale_for-29
- **Source:** `AsurDev/load_test/workload/types.py:LL102 :: workload_types_rationale_102`
- **Target:** `AsurDev/load_test/workload/types.py:L101 :: asurdev_load_test_workload_types_py_workload_types_cascading_failure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tools/metrics_server.py:73:    except Exception:  # noqa: BLE001 - we just want to observe the failure
    ```
    ```
    /home/workspace/push/tests/test_compromise_agent.py:122:            raise RuntimeError("simulated upstream failure")
    ```
    ```
    /home/workspace/push/tests/data_room/test_data_room.py:107:    # `bad` is >50% failure → degraded
    ```

### INFERRED #rationale_for-30
- **Source:** `AsurDev/v7/meta_learner/meta_learner.py:LL96 :: meta_learner_meta_learner_rationale_96`
- **Target:** `AsurDev/v7/meta_learner/meta_learner.py:L95 :: asurdev_v7_meta_learner_meta_learner_py_meta_learner_meta_learner_metalearner_all_time_best`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/strategies/generator.py:238:    def best(self) -> tuple[BaseStrategy, float]:
    ```
    ```
    /home/workspace/push/strategies/generator.py:250:    best = max(selected, key=lambda x: x[1])
    ```
    ```
    /home/workspace/push/strategies/generator.py:251:    return best[0]
    ```

### INFERRED #rationale_for-31
- **Source:** `agents/_impl/amre/idea_buffer_integration.py:LL1 :: agents_impl_amre_idea_buffer_integration_py_amre_idea_buffer_integration_rationale_1`
- **Target:** `agents/_impl/amre/idea_buffer_integration.py:L1 :: agents_impl_amre_idea_buffer_integration_py_amre_idea_buffer_integration`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/parse_known_issues.py:4:Phase 6 - KNOWN_ISSUES.md parser for CI integration.
    ```
    ```
    /home/workspace/audit_repo/meta_rl/config.py:1:"""meta_rl/config.py — Feature flags & integration config (ATOM-META-RL-006: Production)
    ```
    ```
    /home/workspace/audit_repo/meta_rl/strategy_evaluator.py:146:        """ATOM-META-RL-007: Full WalkForwardValidator integration."""
    ```

### INFERRED #rationale_for-32
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL125 :: policy_oscillation_test_rationale_125`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L124 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_make_decision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/trading/safety_gate.py:21:  decision = gate.check(signal, state)
    ```
    ```
    /home/workspace/push/db/models.py:114:    """Vedic planetary positions at decision time."""
    ```
    ```
    /home/workspace/push/db/migrate_from_sqlite.py:67:                # Convert session to decision record format
    ```

### INFERRED #rationale_for-33
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL24 :: correction_loop_loop_rationale_24`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L23 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionaction`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/astrology/vedic.py:219:    # Sidereal correction (ayanamsa ~ 24° in 2026)
    ```
    ```
    /home/workspace/push/astrology/vedic.py:220:    ayanamsa = 24.0  # Approximate for 2026
    ```
    ```
    /home/workspace/push/astrology/vedic.py:358:    jd = jdn + (utc.hour + utc.minute / 60.0 + utc.second / 3600.0 - 12) / 24.0
    ```

### INFERRED #rationale_for-34
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL413 :: archived_synthesis_agent_rationale_413`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L412 :: archived_synthesis_agent_synthesisagent_format_breakdown`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #rationale_for-35
- **Source:** `AstroFinSentinelV5/web/components/sessions.py:LL1 :: astrofinsentinelv5_web_components_sessions_py_components_sessions_rationale_1`
- **Target:** `AstroFinSentinelV5/web/components/sessions.py:L1 :: astrofinsentinelv5_web_components_sessions_py_components_sessions`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/components/sessions.py
    ```

### INFERRED #rationale_for-36
- **Source:** `AsurDev/v6/constraint_graph/graph.py:LL99 :: asurdev_v6_constraint_graph_graph_py_constraint_graph_graph_rationale_99`
- **Target:** `AsurDev/v6/constraint_graph/graph.py:L98 :: asurdev_v6_constraint_graph_graph_py_constraint_graph_graph_constraintgraph_add_sla_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/AsurDev/v6/constraint_graph/graph.py:4:Cluster represented as directed constraint graph:
    ```

### INFERRED #rationale_for-37
- **Source:** `AsurDev/ete/scheduler/adapter.py:LL35 :: scheduler_adapter_rationale_35`
- **Target:** `AsurDev/ete/scheduler/adapter.py:L34 :: asurdev_ete_scheduler_adapter_py_scheduler_adapter_scheduleradapter_schedule`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/integrations/gitagent/adapters/mcp_adapter.py:205:                "calendar": ["calendar", "schedule", "google-calendar"],
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:112:    def schedule(self, job_id: str, node_id: str) -> bool:
    ```
    ```
    /home/workspace/AsurDev/scheduler_v3/api.py:4:POST /schedule     — admission check → stateful scoring → Slurm submit
    ```

### INFERRED #rationale_for-38
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL79 :: modules_metrics_rationale_79`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L78 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ceph_storage_used`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tools/metrics_server.py:27:# ── HTTP request metrics (used by middleware below) ──────────────────────────
    ```
    ```
    /home/workspace/push/scripts/architecture_linter.py:346:# ─── Library API (used by tests and embedding) ────────────────
    ```
    ```
    /home/workspace/push/scripts/architecture_linter.py:467:# ─── Library API (used by tests and embedding) ────────────────
    ```

### INFERRED #rationale_for-39
- **Source:** `agents/_impl/amre/audit.py:LL54 :: agents_impl_amre_audit_py_amre_audit_rationale_54`
- **Target:** `agents/_impl/amre/audit.py:L53 :: agents_impl_amre_audit_py_amre_audit_marketsnapshot`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/agents/gitagent_exporter.py:369:Weak                 35-54
    ```
    ```
    /home/workspace/audit_repo/agents/gitagent_exporter.py:369:Weak                 35-54
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/agents/gitagent_exporter.py:369:Weak                 35-54
    ```

### INFERRED #rationale_for-40
- **Source:** `AsurDev/v6/objective/utility.py:LL91 :: objective_utility_rationale_91`
- **Target:** `AsurDev/v6/objective/utility.py:L90 :: asurdev_v6_objective_utility_py_objective_utility_utilityfunction_sla_violation_component`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/meta_rl/ranking.py:78:                # Per-component scores (0-1, higher = better)
    ```
    ```
    /home/workspace/push/meta_rl/reward.py:19:    Weights for multi-component risk-adjusted reward function.
    ```
    ```
    /home/workspace/push/meta_rl/reward.py:86:            # ── 1. Sharpe component ─────────────────────────────────────────
    ```

### INFERRED #rationale_for-41
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL134 :: feature_pipeline_window_engine_rationale_134`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L133 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_slidingwindow_get_window`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/optimize_lag_blend.py:15:        --window 50 \
    ```
    ```
    /home/workspace/audit_repo/scripts/optimize_lag_blend.py:218:        window = LagWindow(
    ```
    ```
    /home/workspace/audit_repo/scripts/optimize_lag_blend.py:229:            result = window.add(confidence=raw, volatility=None)
    ```

### INFERRED #rationale_for-42
- **Source:** `AsurDev/v6/constraint_graph/graph.py:LL49 :: constraint_graph_graph_rationale_49`
- **Target:** `AsurDev/v6/constraint_graph/graph.py:L48 :: asurdev_v6_constraint_graph_graph_py_constraint_graph_graph_constraintgraph`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/core/kepler.py:83:            mean_longitude=49.94432,
    ```
    ```
    /home/workspace/audit_repo/core/kepler.py:83:            mean_longitude=49.94432,
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/astrology/kepler.py:83:            mean_longitude=49.94432,
    ```

### INFERRED #rationale_for-43
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL116 :: failure_orchestrator_detectors_rationale_116`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L115 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_node_unreachable`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/scheduler_v3/scorer.py:110:    # Latency: lower is better (assume LAN = 0.1ms, penalize if unreachable)
    ```
    ```
    /home/workspace/AsurDev/ml_engine/inference/ml_client.py:94:        logger.warning("ML API unreachable at %s — returning 0.0", url)
    ```
    ```
    /home/workspace/AsurDev/ai_scheduler/scheduler.py:134:    """Fallback when Prometheus is unreachable — use static info + rough estimates."""
    ```

### INFERRED #rationale_for-44
- **Source:** `AstroFinSentinelV5/tests/ralph_benchmark/test_agent_basic.py:LL23 :: ralph_benchmark_test_agent_basic_rationale_23`
- **Target:** `AstroFinSentinelV5/tests/ralph_benchmark/test_agent_basic.py:L22 :: astrofinsentinelv5_tests_ralph_benchmark_test_agent_basic_py_ralph_benchmark_test_agent_basic_test_agent_can_create_add_function`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/ralph_benchmark/test_agent_basic.py
    ```

### INFERRED #rationale_for-45
- **Source:** `_sbs_old/tests/test_invariants.py:LL192 :: tests_test_invariants_rationale_192`
- **Target:** `_sbs_old/tests/test_invariants.py:L191 :: sbs_old_tests_test_invariants_py_tests_test_invariants_testsystemcontract_test_verify_unknown_raises`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/agent_test_base.py:137:        """If a data source raises, the response is degraded with a machine reason."""
    ```
    ```
    /home/workspace/push/tests/test_compromise_agent.py:119:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/push/tests/_template_agent_test.py:123:    """If a data source raises, the response is degraded with a machine reason."""
    ```

### INFERRED #rationale_for-46
- **Source:** `AsurDev/acos/contracts/trace_contract.py:LL32 :: contracts_trace_contract_rationale_32`
- **Target:** `AsurDev/acos/contracts/trace_contract.py:L31 :: asurdev_acos_contracts_trace_contract_py_contracts_trace_contract_tracerecordercontract`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/mas_factory/engine.py:64:    @lru_cache(maxsize=32)
    ```
    ```
    /home/workspace/push/db/models.py:191:    state_hash = Column(String(32))
    ```
    ```
    /home/workspace/push/scripts/architecture_linter.py:54:GREEN = lambda s: _c("32", s)
    ```

### INFERRED #rationale_for-47
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL134 :: ai_scheduler_scheduler_rationale_134`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L133 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_node_metrics_fallback`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/parse_known_issues.py:33:# body itself is the fallback.
    ```
    ```
    /home/workspace/audit_repo/data_provider.py:2:Primary: Yahoo Finance v8 (free, no key) + yfinance fallback
    ```
    ```
    /home/workspace/audit_repo/data_provider.py:229:    """yfinance library fallback (works for most standard symbols)."""
    ```

### INFERRED #rationale_for-48
- **Source:** `AstroFinSentinelV5/tests/test_risk_integration.py:LL78 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_rationale_78`
- **Target:** `AstroFinSentinelV5/tests/test_risk_integration.py:L77 :: astrofinsentinelv5_tests_test_risk_integration_py_tests_test_risk_integration_testriskengineintegration_test_reduced_on_high_exposure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_integration.py
    ```

### INFERRED #rationale_for-49
- **Source:** `Projects/Loopcraft/loopcraft_demo.py:LL197 :: loopcraft_loopcraft_demo_rationale_197`
- **Target:** `Projects/Loopcraft/loopcraft_demo.py:L196 :: loopcraft_loopcraft_demo_save_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:190:    state = {
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:200:    result = await executor.run(state)
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:217:        state = {
    ```

### INFERRED #rationale_for-50
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL312 :: tests_test_kepler_property_rationale_312`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L311 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_test_longitude_periodic_real_bodies`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

---

## Bucket: relation = `inherits` (10 edges)

### INFERRED #inherits-1
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL68 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_jobrequest`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-2
- **Source:** `astrofin-sentinel-v5/orchestration/router.py:LL24 :: astrofin_sentinel_v5_orchestration_router_py_orchestration_router_routeroutput`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-3
- **Source:** `astrofin-sentinel-v5/orchestration/models.py:LL20 :: astrofin_sentinel_v5_orchestration_models_py_orchestration_models_sentinelv5request`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-4
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL162 :: agent_runtime_app_taskcreate`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-5
- **Source:** `roma-execution-bridge/deploy/stripe-webhook/app/main.py:LL76 :: app_main_webhookresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-6
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL186 :: agent_runtime_app_queuestatsresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-7
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL169 :: agent_runtime_app_tasksubmitresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-8
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL175 :: agent_runtime_app_taskstatusresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-9
- **Source:** `astrofin-sentinel-v5/health_endpoints.py:LL31 :: astrofin_sentinel_v5_health_endpoints_healthresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-10
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL31 :: monitoring_health_endpoints_healthresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

## Bucket: relation = `defines` (10 edges)

### INFERRED #defines-1
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/tests/test_security_fixes.py:74:        self.assertIn("wg-quick", mgr._available_binaries())
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_wg.py:47:        binaries = ["awg-quick", "wg-quick"]
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_wg.py:48:        for b in ["wg", "awg"]:
    ```

### INFERRED #defines-2
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_command_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/db_monitor.py:22:        if not db_path.exists():
    ```
    ```
    /home/workspace/tools/db_monitor.py:54:    if not SNAPSHOT_TBL.exists():
    ```
    ```
    /home/workspace/tools/db_monitor.py:96:    if SNAPSHOT_TBL.exists():
    ```

### INFERRED #defines-3
- **Source:** `AsurDev/scripts/day3-compute.sh:LL25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_detect_os`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/nightly_export.py:14:import os
    ```
    ```
    /home/workspace/tools/nightly_export.py:18:sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ```
    ```
    /home/workspace/tools/metrics_server.py:9:import os
    ```

### INFERRED #defines-4
- **Source:** `AsurDev/cluster_status.sh:LL15 :: asurdev_cluster_status`
- **Target:** `AsurDev/cluster_status.sh:L15 :: asurdev_cluster_status_check_port`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/metrics_server.py:46:def run_server(port: int = 9091, host: str = "0.0.0.0"):
    ```
    ```
    /home/workspace/tools/metrics_server.py:50:    web.run_app(app, port=port, host=host, print=lambda *_: None)
    ```
    ```
    /home/workspace/tools/metrics_server.py:55:    parser.add_argument("--port", type=int, default=9091)
    ```

### INFERRED #defines-5
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/validate_blackrock_tests.py:65:    print("  incomplete: " + str(len(incomplete_files)) + " test files (warn)")
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_registry.py:52:    return 0  # warn, not fail
    ```
    ```
    /home/workspace/audit_repo/scripts/architecture_linter.py:21:Soft rules (warn, do not fail):
    ```

### INFERRED #defines-6
- **Source:** `AsurDev/scripts/day1-network.sh:LL33 :: asurdev_scripts_day1_network_sh_scripts_day1_network`
- **Target:** `AsurDev/scripts/day1-network.sh:L33 :: asurdev_scripts_day1_network_sh_scripts_day1_network_ros_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/healthcheck.py:67:        req = urllib.request.Request("http://localhost:11434/api/tags")
    ```
    ```
    /home/workspace/audit_repo/health_endpoints.py:54:# Auth middleware – только для /api/*
    ```
    ```
    /home/workspace/audit_repo/health_endpoints.py:58:    if request.url.path.startswith("/api/"):
    ```

### INFERRED #defines-7
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL48 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L48 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_gen_keys`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/migrations/migrate.py:202:        print(f"Unknown DB: {db_key}. Options: {list(DBs.keys())}", file=sys.stderr)
    ```
    ```
    /home/workspace/audit_repo/trading/risk_v2.py:122:        symbols = list(self._positions.keys())
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_agent.py:97:            for k, v in zip(assign_value.keys, assign_value.values):
    ```

### INFERRED #defines-8
- **Source:** `AsurDev/scripts/day1-network.sh:LL78 :: asurdev_scripts_day1_network_sh_scripts_day1_network`
- **Target:** `AsurDev/scripts/day1-network.sh:L78 :: asurdev_scripts_day1_network_sh_scripts_day1_network_create_vlan`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/integrations/gitagent/adapters/mcp_adapter.py:55:        """Get fallback server list for common queries when network is unavailable."""
    ```
    ```
    /home/workspace/data_provider.py:479:    "MATIC": "matic-network",
    ```
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:255:        reasons.append(f"Single MON quorum [{status.quorum_names[0]}] → split-brain risk if any network glitch")
    ```

### INFERRED #defines-9
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_info`
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

### INFERRED #defines-10
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL32 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L32 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/healthcheck.py:78:        "status": "ok",
    ```
    ```
    /home/workspace/push/mas_factory/atom_032_e2e_test.py:140:    passed = sum(1 for _, ok in results if ok)
    ```
    ```
    /home/workspace/push/mas_factory/atom_032_e2e_test.py:145:        for name, ok in results:
    ```

---

## Bucket: relation = `uses` (50 edges)

### INFERRED #uses-1
- **Source:** `AsurDev/acos.py:LL21 :: asurdev_acos_acosdecisionresponse`
- **Target:** `home-cluster-iac/ete/store/trace_store.py:L28 :: home_cluster_iac_ete_store_trace_store_py_store_trace_store_tracenode`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'tracenode' not found in home-cluster-iac/ete/store/trace_store.py
    ```

### INFERRED #uses-2
- **Source:** `AsurDev/acos.py:LL21 :: asurdev_acos_acosorchestrator`
- **Target:** `home-cluster-iac/ete/store/trace_store.py:L28 :: home_cluster_iac_ete_store_trace_store_py_store_trace_store_tracenode`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'tracenode' not found in home-cluster-iac/ete/store/trace_store.py
    ```

### INFERRED #uses-3
- **Source:** `atom-federation-os/chaos/validator.py:LL31 :: atom_federation_os_chaos_validator_py_chaosresult`
- **Target:** `_sbs_old/failure_classifier.py:L81 :: sbs_old_failure_classifier_failureclassifier`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'failureclassifier' not found in _sbs_old/failure_classifier.py
    ```

### INFERRED #uses-4
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL11 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testevaluationresult`
- **Target:** `push/meta_rl/strategy_evaluator.py:L69 :: push_meta_rl_strategy_evaluator_py_evaluationresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'evaluationresult' not found in push/meta_rl/strategy_evaluator.py
    ```

### INFERRED #uses-5
- **Source:** `AsurDev/acos.py:LL25 :: asurdev_acos_acosdecisionresult`
- **Target:** `home-cluster-iac/constraint_compiler/parser/parser.py:L102 :: home_cluster_iac_constraint_compiler_parser_parser_py_parser_parser_policyparser`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'policyparser' not found in home-cluster-iac/constraint_compiler/parser/parser.py
    ```

### INFERRED #uses-6
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL11 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator`
- **Target:** `push/meta_rl/strategy_evaluator.py:L38 :: push_meta_rl_strategy_evaluator_py_meta_rl_strategy_evaluator_strategyevaluator`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'strategyevaluator' not found in push/meta_rl/strategy_evaluator.py
    ```

### INFERRED #uses-7
- **Source:** `AsurDev/acos.py:LL17 :: asurdev_acos_acoscontext`
- **Target:** `home-cluster-iac/l9_ebl/gate/gate.py:L23 :: home_cluster_iac_l9_ebl_gate_gate_py_gate_gate_gatedecision`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'gatedecision' not found in home-cluster-iac/l9_ebl/gate/gate.py
    ```

### INFERRED #uses-8
- **Source:** `_pr_logs/PR1/synthesis_agent.py:LL17 :: pr_logs_pr1_synthesis_agent_py_agentresponse`
- **Target:** `push/core/volatility.py:L107 :: push_core_volatility_py_core_volatility_volatilityengine`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'volatilityengine' not found in push/core/volatility.py
    ```

### INFERRED #uses-9
- **Source:** `_pr_logs/PR1/compromise_agent.py:LL32 :: pr_logs_pr1_compromise_agent_py_signaldirection`
- **Target:** `push/core/base_agent.py:L83 :: push_core_base_agent_py_core_base_agent_baseagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'baseagent' not found in push/core/base_agent.py
    ```

### INFERRED #uses-10
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL315 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `push/core/base_agent.py:L49 :: push_core_base_agent_py_core_base_agent_agentresponse`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'agentresponse' not found in push/core/base_agent.py
    ```

### INFERRED #uses-11
- **Source:** `atom-federation-os/cluster/shared/sbs_client.py:LL16 :: shared_sbs_client_sbsdistributedclient`
- **Target:** `_sbs_old/boundary_spec.py:L15 :: sbs_old_boundary_spec_systemboundaryspec`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'systemboundaryspec' not found in _sbs_old/boundary_spec.py
    ```

### INFERRED #uses-12
- **Source:** `AsurDev/scheduler_v3/api.py:LL20 :: asurdev_scheduler_v3_api_py_admissioncontroller`
- **Target:** `roma-execution-bridge/durability/state_store.py:L12 :: durability_state_store_statestore`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'statestore' not found in roma-execution-bridge/durability/state_store.py
    ```

### INFERRED #uses-13
- **Source:** `agents/_impl/amre/replay_buffer.py:LL7 :: agents_impl_amre_replay_buffer_py_amre_replay_buffer_bufferentry`
- **Target:** `push/agents/_impl/amre/trajectory.py:L18 :: push_agents_impl_amre_trajectory_py_amre_trajectory_trajectory`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/models.py:283:    """Complete trajectory for KARL replay buffer."""
    ```
    ```
    /home/workspace/push/db/models.py:301:    steps = relationship("KARLTrajectoryStep", back_populates="trajectory")
    ```
    ```
    /home/workspace/push/db/models.py:305:    """Individual step within a KARL trajectory."""
    ```

### INFERRED #uses-14
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL11 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategyevaluator`
- **Target:** `push/meta_rl/strategy_evaluator.py:L69 :: push_meta_rl_strategy_evaluator_py_evaluationresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'evaluationresult' not found in push/meta_rl/strategy_evaluator.py
    ```

### INFERRED #uses-15
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testdrawdownkillswitch`
- **Target:** `trading/execution/sanity.py:L11 :: trading_execution_sanity_py_execution_sanity_validationstatus`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'validationstatus' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-16
- **Source:** `AsurDev/acos.py:LL25 :: asurdev_acos_acosorchestrator`
- **Target:** `home-cluster-iac/constraint_compiler/parser/parser.py:L102 :: home_cluster_iac_constraint_compiler_parser_parser_py_parser_parser_policyparser`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'policyparser' not found in home-cluster-iac/constraint_compiler/parser/parser.py
    ```

### INFERRED #uses-17
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-18
- **Source:** `atom-federation-os/sbs/runtime.py:LL20 :: sbs_runtime_violationpolicy`
- **Target:** `_sbs_old/global_invariant_engine.py:L62 :: sbs_old_global_invariant_engine_globalinvariantengine`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'globalinvariantengine' not found in _sbs_old/global_invariant_engine.py
    ```

### INFERRED #uses-19
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testspreadfilter`
- **Target:** `trading/execution/sanity.py:L30 :: trading_execution_sanity_py_execution_sanity_orderrequest`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'orderrequest' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-20
- **Source:** `atom-federation-os/sbs/runtime.py:LL20 :: sbs_runtime_sbsruntimeenforcer`
- **Target:** `_sbs_old/global_invariant_engine.py:L62 :: sbs_old_global_invariant_engine_globalinvariantengine`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'globalinvariantengine' not found in _sbs_old/global_invariant_engine.py
    ```

### INFERRED #uses-21
- **Source:** `audit_repo/langgraph_schema.py:LL309 :: audit_repo_langgraph_schema_py_agentpool`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-22
- **Source:** `atom-federation-os/sbs/runtime.py:LL19 :: sbs_runtime_sbsruntimeenforcer`
- **Target:** `_sbs_old/boundary_spec.py:L15 :: sbs_old_boundary_spec_systemboundaryspec`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'systemboundaryspec' not found in _sbs_old/boundary_spec.py
    ```

### INFERRED #uses-23
- **Source:** `atom-federation-os/sbs/schema_validator.py:LL28 :: sbs_schema_validator_schemavalidationerror`
- **Target:** `_sbs_old/boundary_spec.py:L15 :: sbs_old_boundary_spec_systemboundaryspec`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'systemboundaryspec' not found in _sbs_old/boundary_spec.py
    ```

### INFERRED #uses-24
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL19 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolregime`
- **Target:** `trading/execution/sanity.py:L55 :: trading_execution_sanity_py_execution_sanity_executionsanitychecker`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'executionsanitychecker' not found in trading/execution/sanity.py
    ```

### INFERRED #uses-25
- **Source:** `AsurDev/acos.py:LL21 :: asurdev_acos_acosdecisionrequest`
- **Target:** `home-cluster-iac/ete/store/trace_store.py:L28 :: home_cluster_iac_ete_store_trace_store_py_store_trace_store_tracenode`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'tracenode' not found in home-cluster-iac/ete/store/trace_store.py
    ```

### INFERRED #uses-26
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL78 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_tunnelevent`
- **Target:** `home-cluster-iac/acos/events/types.py:L8 :: home_cluster_iac_acos_events_types_py_events_types_eventtype`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'eventtype' not found in home-cluster-iac/acos/events/types.py
    ```

### INFERRED #uses-27
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL10 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog`
- **Target:** `home-cluster-iac/l10_self_healing/orchestrator/failure_isolation.py:L13 :: home_cluster_iac_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_incidentseverity`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/AsurDev/acos.py:31:from l10_self_healing.watchdog.watchdog import Watchdog, HealthMetric
    ```
    ```
    /home/workspace/AsurDev/acos.py:158:        self.watchdog = Watchdog(self.failure_isolator)
    ```
    ```
    /home/workspace/home-cluster-iac/acos.py:29:from l10_self_healing.watchdog.watchdog import Watchdog
    ```

### INFERRED #uses-28
- **Source:** `_sbs_old/tests/test_invariants.py:LL21 :: sbs_old_tests_test_invariants_py_tests_test_invariants_testfailureclassifier`
- **Target:** `_sbs_old/global_invariant_engine.py:L26 :: sbs_old_global_invariant_engine_layerstate`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'layerstate' not found in _sbs_old/global_invariant_engine.py
    ```

### INFERRED #uses-29
- **Source:** `atom-federation-os/sbs/tests/test_invariants.py:LL23 :: atom_federation_os_sbs_tests_test_invariants_py_tests_test_invariants_testlayerstate`
- **Target:** `_sbs_old/system_contract.py:L34 :: sbs_old_system_contract_system_contract`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/agent_test_base.py:18:    - When the contract changes, ONE place to update.
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:54:    Canonical test contract for an AstroFin Sentinel V5 agent.
    ```
    ```
    /home/workspace/push/tests/agent_test_base.py:140:        # The contract: never raise. Either succeed or degrade cleanly.
    ```

### INFERRED #uses-30
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testsanitynansafety`
- **Target:** `trading/risk_v2.py:L38 :: trading_risk_v2_py_trading_risk_v2_assetposition`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'assetposition' not found in trading/risk_v2.py
    ```

### INFERRED #uses-31
- **Source:** `agents/_impl/amre/replay_buffer.py:LL7 :: agents_impl_amre_replay_buffer_py_amre_replay_buffer_bufferentry`
- **Target:** `push/agents/_impl/amre/trajectory.py:L24 :: push_agents_impl_amre_trajectory_py_amre_trajectory_trajectorymetrics`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'trajectorymetrics' not found in push/agents/_impl/amre/trajectory.py
    ```

### INFERRED #uses-32
- **Source:** `AsurDev/v6/solver/optimizer.py:LL15 :: asurdev_v6_solver_optimizer_py_solver_optimizer_hardconstraintpruner`
- **Target:** `home-cluster-iac/v6/constraint_graph/graph.py:L49 :: home_cluster_iac_v6_constraint_graph_graph_py_constraint_graph_graph_constraintgraph`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'constraintgraph' not found in home-cluster-iac/v6/constraint_graph/graph.py
    ```

### INFERRED #uses-33
- **Source:** `AsurDev/l11_verifier/verifier.py:LL25 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_failurereport`
- **Target:** `home-cluster-iac/execution_sandbox/sandbox.py:L40 :: home_cluster_iac_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'executionsandbox' not found in home-cluster-iac/execution_sandbox/sandbox.py
    ```

### INFERRED #uses-34
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL9 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testevolutionengine`
- **Target:** `push/meta_rl/meta_agent.py:L81 :: push_meta_rl_meta_agent_py_meta_rl_meta_agent_evolutionconfig`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'evolutionconfig' not found in push/meta_rl/meta_agent.py
    ```

### INFERRED #uses-35
- **Source:** `AsurDev/acos.py:LL18 :: asurdev_acos_acosdecisionrequest`
- **Target:** `home-cluster-iac/l9_ebl/policy_compiler/compiler.py:L53 :: home_cluster_iac_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_policycompiler`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'policycompiler' not found in home-cluster-iac/l9_ebl/policy_compiler/compiler.py
    ```

### INFERRED #uses-36
- **Source:** `_sbs_old/global_invariant_engine.py:LL22 :: sbs_old_global_invariant_engine_py_systemboundaryspec`
- **Target:** `_sbs_old/boundary_spec.py:L15 :: sbs_old_boundary_spec_systemboundaryspec`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'systemboundaryspec' not found in _sbs_old/boundary_spec.py
    ```

### INFERRED #uses-37
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL29 :: chaos_test_chaos_testfailureclassifier`
- **Target:** `_sbs_old/failure_classifier.py:L23 :: sbs_old_failure_classifier_failurecategory`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'failurecategory' not found in _sbs_old/failure_classifier.py
    ```

### INFERRED #uses-38
- **Source:** `_sbs_old/tests/test_invariants.py:LL21 :: sbs_old_tests_test_invariants_py_tests_test_invariants_testsystemcontract`
- **Target:** `_sbs_old/global_invariant_engine.py:L26 :: sbs_old_global_invariant_engine_layerstate`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'layerstate' not found in _sbs_old/global_invariant_engine.py
    ```

### INFERRED #uses-39
- **Source:** `AsurDev/tests/test_security_fixes.py:LL5 :: asurdev_tests_test_security_fixes_py_tests_test_security_fixes_testamneziawg`
- **Target:** `home-cluster-iac/acos/events/event_log.py:L9 :: home_cluster_iac_acos_events_event_log_py_events_event_log_eventlog`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/tests/test_amneziawg_integration.py:104:    mgr = AmneziaWGManager(log, trace_id="eventlog-test")
    ```
    ```
    /home/workspace/AsurDev/tests/test_amneziawg_integration.py:107:    log.emit("eventlog-test", "TUNNEL_UP", {"interface": "wg0", "peer": "10.8.0.1"})
    ```
    ```
    /home/workspace/AsurDev/tests/test_amneziawg_integration.py:109:    events = log.get_trace("eventlog-test")
    ```

### INFERRED #uses-40
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testnonan`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-41
- **Source:** `agents/_impl/amre/backtest_loop.py:LL13 :: agents_impl_amre_backtest_loop_py_amre_backtest_loop_backteststep`
- **Target:** `push/agents/_impl/amre/replay_buffer.py:L21 :: push_agents_impl_amre_replay_buffer_py_amre_replay_buffer_replaybuffer`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'replaybuffer' not found in push/agents/_impl/amre/replay_buffer.py
    ```

### INFERRED #uses-42
- **Source:** `astrofin-sentinel-v5/agents/karl_synthesis.py:LL44 :: astrofin_sentinel_v5_agents_karl_synthesis_py_any`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-43
- **Source:** `AsurDev/tests/test_security_fixes.py:LL8 :: asurdev_tests_test_security_fixes_py_tests_test_security_fixes_testeventlog`
- **Target:** `home-cluster-iac/acos/state/reducer.py:L29 :: home_cluster_iac_acos_state_reducer_py_state_reducer_statereducer`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'statereducer' not found in home-cluster-iac/acos/state/reducer.py
    ```

### INFERRED #uses-44
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL10 :: asurdev_l10_self_healing_watchdog_watchdog_py_any`
- **Target:** `home-cluster-iac/l10_self_healing/orchestrator/failure_isolation.py:L23 :: home_cluster_iac_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failmode`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'failmode' not found in home-cluster-iac/l10_self_healing/orchestrator/failure_isolation.py
    ```

### INFERRED #uses-45
- **Source:** `atom-federation-os/chaos/test_chaos.py:LL29 :: chaos_test_chaos_testchaosharness`
- **Target:** `_sbs_old/failure_classifier.py:L39 :: sbs_old_failure_classifier_failureseverity`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'failureseverity' not found in _sbs_old/failure_classifier.py
    ```

### INFERRED #uses-46
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL27 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testnansafety`
- **Target:** `trading/risk_v2.py:L21 :: trading_risk_v2_py_trading_risk_v2_riskconfigv2`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'riskconfigv2' not found in trading/risk_v2.py
    ```

### INFERRED #uses-47
- **Source:** `_pr_logs/PR1/synthesis_agent.py:LL213 :: pr_logs_pr1_synthesis_agent_py_agentresponse`
- **Target:** `_pr_logs/PR1/compromise_agent.py:L63 :: pr1_compromise_agent_compromiseagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'compromiseagent' not found in _pr_logs/PR1/compromise_agent.py
    ```

### INFERRED #uses-48
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'validationresult' not found in integrations/gitagent/validators/agent_validator.py
    ```

### INFERRED #uses-49
- **Source:** `AsurDev/ete/replay/replayer.py:LL10 :: asurdev_ete_replay_replayer_py_replay_replayer_deterministicreplayer`
- **Target:** `home-cluster-iac/ete/store/trace_store.py:L98 :: home_cluster_iac_ete_store_trace_store_py_store_trace_store_tracestore`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'tracestore' not found in home-cluster-iac/ete/store/trace_store.py
    ```

### INFERRED #uses-50
- **Source:** `atom-federation-os/chaos/__init__.py:LL21 :: atom_federation_os_chaos_init_py_verdict`
- **Target:** `_sbs_old/boundary_spec.py:L15 :: sbs_old_boundary_spec_systemboundaryspec`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/core/panchanga.py:379:        "verdict": "Excellent" if score >= 85 else "Good" if score >= 70 else "Average" if score >= 50 else "Poor",
    ```
    ```
    /home/workspace/audit_repo/core/panchanga.py:379:        "verdict": "Excellent" if score >= 85 else "Good" if score >= 70 else "Average" if score >= 50 else "Poor",
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:19:Each verdict is recorded with grep evidence (line of proof).
    ```

---

## Bucket: relation = `imports` (10 edges)

### INFERRED #imports-1
- **Source:** `push/db/models.py:LL7 :: push_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-2
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/dag_retry.py:LL13 :: agent_runtime_dag_retry`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-3
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L11 :: validators_agent_validator_severity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/scripts/architecture_linter.py:68:    severity: str        # "FAIL" | "WARN"
    ```
    ```
    /home/workspace/push/scripts/architecture_linter.py:88:        return any(f.severity == "FAIL" for f in self.findings)
    ```
    ```
    /home/workspace/push/scripts/architecture_linter.py:92:        return any(f.severity == "WARN" for f in self.findings)
    ```

### INFERRED #imports-4
- **Source:** `db/models.py:LL7 :: db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-5
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_blackrock_tests.py:39:    parser = argparse.ArgumentParser(description="BlackRock six-test validator")
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_blackrock_tests.py:62:    print("BlackRock six-test validator:")
    ```
    ```
    /home/workspace/audit_repo/scripts/validate_agent.py:5:Per-agent validator for AstroFin Sentinel V5.
    ```

### INFERRED #imports-6
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/scripts/validate_agent.py:5:Per-agent validator for AstroFin Sentinel V5.
    ```
    ```
    /home/workspace/push/scripts/validate_blackrock_tests.py:39:    parser = argparse.ArgumentParser(description="BlackRock six-test validator")
    ```
    ```
    /home/workspace/push/scripts/validate_blackrock_tests.py:62:    print("BlackRock six-test validator:")
    ```

### INFERRED #imports-7
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/scripts/validate_agent.py:5:Per-agent validator for AstroFin Sentinel V5.
    ```
    ```
    /home/workspace/push/tests/architecture/test_validate_agent.py:4:Tests for the per-agent validator.
    ```
    ```
    /home/workspace/push/tests/test_validator.py:22:def validator():
    ```

### INFERRED #imports-8
- **Source:** `audit_repo/db/models.py:LL7 :: audit_repo_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-9
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L35 :: validators_agent_validator_validationreport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/push/scripts/validate_agent.py:5:Per-agent validator for AstroFin Sentinel V5.
    ```
    ```
    /home/workspace/push/scripts/validate_blackrock_tests.py:39:    parser = argparse.ArgumentParser(description="BlackRock six-test validator")
    ```
    ```
    /home/workspace/push/scripts/validate_blackrock_tests.py:62:    print("BlackRock six-test validator:")
    ```

### INFERRED #imports-10
- **Source:** `astrofin-sentinel-v5/db/models.py:LL7 :: astrofin_sentinel_v5_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

## Bucket: relation = `method` (50 edges)

### INFERRED #method-1
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL166 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L166 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testrewardcalculator_test_summary_breakdown`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-2
- **Source:** `AsurDev/hash_chain/chain.py:LL29 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain`
- **Target:** `AsurDev/hash_chain/chain.py:L29 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain_verify_chain`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/test_compromise_agent.py:4:broken `meta_rl` import chain (caused by missing `integrations.gitagent`).
    ```
    ```
    /home/workspace/push/tests/test_compromise_agent.py:9:stubs the chain, this file can be reduced to a normal test module.
    ```
    ```
    /home/workspace/push/tests/test_compromise_agent.py:19:# ── 1. Stub the broken chain BEFORE any user code imports it ─────────────
    ```

### INFERRED #method-3
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL70 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L70 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller_p_overload`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/self_healing/diagnostics/ceph.py:319:            "reason": f"{len(status.pgs_deep)} PGs deep-scrubbing (recovery overload)",
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:3:Probabilistic Admission Controller — predicts overload before it happens.
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:4:Replaces static threshold (GPU>85%) with P(overload in next M minutes).
    ```

### INFERRED #method-4
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL64 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_recoveryengine`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L64 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_recoveryengine_record_attempt`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/orchestration/sentinel_v5.py:180:        for attempt in range(max_retries):
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:193:                logger.warning(f"[Price] Attempt {attempt + 1}/{max_retries} error: {e}")
    ```
    ```
    /home/workspace/orchestration/sentinel_v5.py:194:            if attempt < max_retries - 1:
    ```

### INFERRED #method-5
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL45 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L45 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_register`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/mas_factory/registry.py:255:    def register(self, agent_type: str, role: Role):
    ```
    ```
    /home/workspace/audit_repo/strategies/generator.py:99:        PluginRegistry().register(self)
    ```
    ```
    /home/workspace/audit_repo/tests/data_room/test_data_room.py:131:    bp.register("price", AlwaysFails(), chain=["always_succeeds"])
    ```

### INFERRED #method-6
- **Source:** `AsurDev/dag_validator/validator.py:LL34 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator`
- **Target:** `AsurDev/dag_validator/validator.py:L34 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/trading/execution/order_book.py:22:    spread: float = field(init=False)
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:23:    mid_price: float = field(init=False)
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:24:    depth_bid_10: float = field(init=False)  # total bid qty in top 10 levels
    ```

### INFERRED #method-7
- **Source:** `AsurDev/ete/recorder/trace_recorder.py:LL41 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder`
- **Target:** `AsurDev/ete/recorder/trace_recorder.py:L41 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record_postgres`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/healthcheck.py:37:                ["docker-compose", "up", "-d", "postgres"],
    ```
    ```
    /home/workspace/audit_repo/health_endpoints.py:121:                "postgres": "ok" if pg_ok else "fail",
    ```
    ```
    /home/workspace/push/db/migrate_from_sqlite.py:125:        logger.error("PostgreSQL not available. Start it with: docker-compose up -d postgres")
    ```

### INFERRED #method-8
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL110 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L110 :: archived_synthesis_agent_synthesisagent_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-9
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL194 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testsanitynansafety`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L194 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testsanitynansafety_test_zero_price_rejected`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-10
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL261 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategypool`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L261 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategypool_test_statistics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-11
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL40 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog`
- **Target:** `AsurDev/l10_self_healing/watchdog/watchdog.py:L40 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_register_trigger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/agents/karl_synthesis.py:527:        Manual trigger: sync_with_audit().
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/compromise_agent.py:46:# trigger, SynthesisAgent should re-evaluate.
    ```
    ```
    /home/workspace/audit_repo/tests/test_risk_v2.py:36:        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
    ```

### INFERRED #method-12
- **Source:** `AsurDev/ete/store/trace_store.py:LL99 :: asurdev_ete_store_trace_store_py_store_trace_store_tracestore`
- **Target:** `AsurDev/ete/store/trace_store.py:L99 :: asurdev_ete_store_trace_store_py_store_trace_store_tracestore_create_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/core/tracing.py:9:from opentelemetry import trace
    ```
    ```
    /home/workspace/push/core/tracing.py:12:from opentelemetry.sdk.trace import TracerProvider
    ```
    ```
    /home/workspace/push/core/tracing.py:13:from opentelemetry.sdk.trace.export import BatchSpanProcessor
    ```

### INFERRED #method-13
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL97 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L97 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:268:        "--init-single",
    ```
    ```
    /home/workspace/push/db/__init__.py:4:    init.py         - ATOM-020: Auto-create tables on first run
    ```

### INFERRED #method-14
- **Source:** `AsurDev/acos.py:LL305 :: asurdev_acos_acosgovernancekernel`
- **Target:** `AsurDev/acos.py:L305 :: asurdev_acos_acosgovernancekernel_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:268:        "--init-single",
    ```
    ```
    /home/workspace/push/db/__init__.py:4:    init.py         - ATOM-020: Auto-create tables on first run
    ```

### INFERRED #method-15
- **Source:** `AsurDev/state_store/client.py:LL118 :: asurdev_state_store_client_py_state_store_client_statestore`
- **Target:** `AsurDev/state_store/client.py:L118 :: asurdev_state_store_client_py_state_store_client_statestore_create_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/job_engine/engine.py:64:    def on_state_change(self, job: Job, old: JobState, new: JobState) -> None:
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:65:        logger.info(f"[{job.id}] {old.value} → {new.value} (node={job.node_id})")
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:67:    def on_failure(self, job: Job, reason: str) -> None:
    ```

### INFERRED #method-16
- **Source:** `AsurDev/acos/contracts/engine_contract.py:LL7 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract`
- **Target:** `AsurDev/acos/contracts/engine_contract.py:L7 :: asurdev_acos_contracts_engine_contract_py_contracts_engine_contract_executionenginecontract_execute`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/db_monitor.py:30:                cur.execute("SELECT COUNT(*) FROM sessions")
    ```
    ```
    /home/workspace/tools/db_monitor.py:32:                cur.execute("SELECT COUNT(*) FROM backtest_runs")
    ```
    ```
    /home/workspace/tools/db_monitor.py:36:                cur.execute("""
    ```

### INFERRED #method-17
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL21 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L21 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/__init__.py:4:    init.py         - ATOM-020: Auto-create tables on first run
    ```
    ```
    /home/workspace/push/db/__init__.py:12:from db.init import get_db_status, init_db_if_needed, init_schema_if_needed
    ```
    ```
    /home/workspace/push/db/__main__.py:1:"""db/__main__.py — Entry point for: python -m db.init
    ```

### INFERRED #method-18
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL178 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolregime`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L178 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testvolregime_test_allows_high_regime`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-19
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL244 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategypool`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L244 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_teststrategypool_test_scored_strategy_hashable`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-20
- **Source:** `AsurDev/v6/solver/prune/beam.py:LL46 :: asurdev_v6_solver_prune_beam_py_prune_beam_beampruner`
- **Target:** `AsurDev/v6/solver/prune/beam.py:L46 :: asurdev_v6_solver_prune_beam_py_prune_beam_beampruner_prune_by_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/job_engine/engine.py:64:    def on_state_change(self, job: Job, old: JobState, new: JobState) -> None:
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:65:        logger.info(f"[{job.id}] {old.value} → {new.value} (node={job.node_id})")
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:67:    def on_failure(self, job: Job, reason: str) -> None:
    ```

### INFERRED #method-21
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL193 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerresult`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L193 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerresult_test_propagate_kepler_unknown_body_raises`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-22
- **Source:** `AsurDev/tests/unit/test_determinism.py:LL30 :: asurdev_tests_unit_test_determinism_py_unit_test_determinism_mockjob`
- **Target:** `AsurDev/tests/unit/test_determinism.py:L30 :: asurdev_tests_unit_test_determinism_py_unit_test_determinism_mockjob_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```
    ```
    /home/workspace/audit_repo/migrations/migrate.py:268:        "--init-single",
    ```
    ```
    /home/workspace/push/db/__init__.py:4:    init.py         - ATOM-020: Auto-create tables on first run
    ```

### INFERRED #method-23
- **Source:** `AsurDev/acos_cli.py:LL162 :: asurdev_acos_cli_acoscli`
- **Target:** `AsurDev/acos_cli.py:L162 :: asurdev_acos_cli_acoscli_invariants`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/tests/_template_agent_test.py:189:    """The dataclass itself must guard its invariants."""
    ```
    ```
    /home/workspace/push/tests/test_kepler_property.py:5:Covers: orbital mechanics invariants, convergence, periodicity, no NaN across
    ```
    ```
    /home/workspace/audit_repo/tests/_template_agent_test.py:189:    """The dataclass itself must guard its invariants."""
    ```

### INFERRED #method-24
- **Source:** `AstroFinSentinelV5/tests/test_risk_v2.py:LL203 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testmodegating`
- **Target:** `AstroFinSentinelV5/tests/test_risk_v2.py:L203 :: astrofinsentinelv5_tests_test_risk_v2_py_tests_test_risk_v2_testmodegating_test_backtest_allows_all`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_risk_v2.py
    ```

### INFERRED #method-25
- **Source:** `_sbs_old/runtime.py:LL85 :: sbs_old_runtime_violationpolicy`
- **Target:** `_sbs_old/runtime.py:L85 :: sbs_old_runtime_violationpolicy_apply`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/mas_factory/topology.py:92:    def apply(self, data: Any) -> Any:
    ```
    ```
    /home/workspace/push/db/init.py:49:        logger.error(f"[DB-INIT] Failed to apply raw SQL schema: {e}")
    ```
    ```
    /home/workspace/push/tests/test_switch_nodes.py:217:    # Try to apply invalid change (should trigger rollback)
    ```

### INFERRED #method-26
- **Source:** `AsurDev/job_engine/engine.py:LL145 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine`
- **Target:** `AsurDev/job_engine/engine.py:L145 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get_jobs_by_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:190:    state = {
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:200:    result = await executor.run(state)
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:217:        state = {
    ```

### INFERRED #method-27
- **Source:** `AsurDev/v6/solver/optimizer.py:LL100 :: asurdev_v6_solver_optimizer_py_solver_optimizer_ilpoptimizer`
- **Target:** `AsurDev/v6/solver/optimizer.py:L100 :: asurdev_v6_solver_optimizer_py_solver_optimizer_ilpoptimizer_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrofin-sentinel-v5/agents/_impl/macro_agent.py:49:        """Lazy init RAG retriever."""
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/agents/_impl/macro_agent.py:54:                logger.warning("Failed to init RAG for MacroAgent: %s", e)
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/migrations/migrate.py:14:    python migrations/migrate.py --init-single core/history.db
    ```

### INFERRED #method-28
- **Source:** `AsurDev/l11_verifier/verifier.py:LL138 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier`
- **Target:** `AsurDev/l11_verifier/verifier.py:L138 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_full_pipeline`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ml_engine/training/trainer.py:97:        Full training pipeline: build → split → train → evaluate → register.
    ```
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:148:                "Feature pipeline builds from Prometheus, ML trains from TimescaleDB — "
    ```
    ```
    /home/workspace/home-cluster-iac/astrofin/gateway/submission.py:38:        Submit AstroFin job through ACOS governance pipeline.
    ```

### INFERRED #method-29
- **Source:** `AsurDev/v6/policy_eval/evaluator.py:LL97 :: asurdev_v6_policy_eval_evaluator_py_policy_eval_evaluator_policyevaluator`
- **Target:** `AsurDev/v6/policy_eval/evaluator.py:L97 :: asurdev_v6_policy_eval_evaluator_py_policy_eval_evaluator_policyevaluator_policy_score`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:69:    for name, score, belief in results:
    ```
    ```
    /home/workspace/tools/thompson_cli.py:72:                f"  {name:<20} {score:>8.4f}  "
    ```
    ```
    /home/workspace/tools/thompson_cli.py:78:            print(f"  {name:<20} {score:>8.4f}  (unseen, Beta(1{bonus_note},1))")
    ```

### INFERRED #method-30
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL445 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L445 :: archived_synthesis_agent_synthesisagent_calculate_levels`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-31
- **Source:** `AsurDev/load_test/observability/metrics.py:LL75 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector`
- **Target:** `AsurDev/load_test/observability/metrics.py:L75 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_collect`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/knowledge/daily_brief/daily_brief.py:192:    parser.add_argument("--gc", action="store_true", help="Garbage collect old briefs")
    ```
    ```
    /home/workspace/push/knowledge/daily_brief/daily_brief.py:198:    # Garbage collect old briefs
    ```
    ```
    /home/workspace/audit_repo/knowledge/daily_brief/daily_brief.py:192:    parser.add_argument("--gc", action="store_true", help="Garbage collect old briefs")
    ```

### INFERRED #method-32
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL135 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L135 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_no_nan`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #method-33
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL37 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L37 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testvalidagentyaml_test_valid_minimal_agent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

### INFERRED #method-34
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL138 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L138 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testradius_test_jupiter_radius_near_5au`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-35
- **Source:** `AsurDev/feature_pipeline/schemas.py:LL151 :: asurdev_feature_pipeline_schemas_py_feature_pipeline_schemas_mlbatch`
- **Target:** `AsurDev/feature_pipeline/schemas.py:L151 :: asurdev_feature_pipeline_schemas_py_feature_pipeline_schemas_mlbatch_val_size`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/karl_replay.py:68:    def size(self) -> int:
    ```
    ```
    /home/workspace/push/db/session.py:126:            "size": pool.size(),
    ```
    ```
    /home/workspace/push/trading/backtester.py:27:    size: float
    ```

### INFERRED #method-36
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL47 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L47 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:9:    python tools/thompson_cli.py simulate --pool astro --k 4 --n 100  # simulate N runs
    ```
    ```
    /home/workspace/tools/thompson_cli.py:305:    p_sim = sub.add_parser("simulate", help="Simulate N runs")
    ```
    ```
    /home/workspace/tools/thompson_cli.py:346:    elif args.cmd == "simulate":
    ```

### INFERRED #method-37
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL122 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L122 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_deterministic_delay`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/tests/test_amneziawg_integration.py:48:    """INV-AWG2: reconnect delay is deterministic (seed = trace_id hash)."""
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_wg.py:121:    # CRITICAL-8: deterministic delay - same on every replay
    ```
    ```
    /home/workspace/AsurDev/acos/network/amnezia_wg.py:128:        delay = self._deterministic_delay(attempt)
    ```

### INFERRED #method-38
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL164 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L164 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_detect_signals`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/run_backtest.py:27:    signals = []
    ```
    ```
    /home/workspace/audit_repo/scripts/run_backtest.py:47:        signals.append(
    ```
    ```
    /home/workspace/audit_repo/scripts/run_backtest.py:56:    return signals
    ```

### INFERRED #method-39
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL344 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L344 :: archived_synthesis_agent_synthesisagent_vote`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-40
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL85 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L85 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_no_catastrophic_divergence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #method-41
- **Source:** `AstroFinSentinelV5/tests/test_meta_rl.py:LL312 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent`
- **Target:** `AstroFinSentinelV5/tests/test_meta_rl.py:L312 :: astrofinsentinelv5_tests_test_meta_rl_py_tests_test_meta_rl_testmetaagent_test_generation_counter_increments`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_meta_rl.py
    ```

### INFERRED #method-42
- **Source:** `AsurDev/acos/storage/memory_backend.py:LL30 :: asurdev_acos_storage_memory_backend_py_storage_memory_backend_memorytracestorage`
- **Target:** `AsurDev/acos/storage/memory_backend.py:L30 :: asurdev_acos_storage_memory_backend_py_storage_memory_backend_memorytracestorage_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/db_monitor.py:116:            print(f"  [monitor] trend query failed: {e}")
    ```
    ```
    /home/workspace/tools/metrics_server.py:19:RAG_QUERY_CACHE_HITS = Counter("astrofin_rag_query_cache_hits", "RAG query cache hits")
    ```
    ```
    /home/workspace/tools/metrics_server.py:20:RAG_QUERY_CACHE_MISSES = Counter("astrofin_rag_query_cache_misses", "RAG query cache misses")
    ```

### INFERRED #method-43
- **Source:** `AsurDev/job_engine/engine.py:LL73 :: asurdev_job_engine_engine_py_job_engine_engine_jobeventhooks`
- **Target:** `AsurDev/job_engine/engine.py:L73 :: asurdev_job_engine_engine_py_job_engine_engine_jobeventhooks_on_submit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/tests/unit/test_determinism.py:82:    """Test 3: Deduplication — scheduler must not double-submit."""
    ```
    ```
    /home/workspace/AsurDev/scheduler_v3/api.py:4:POST /schedule     — admission check → stateful scoring → Slurm submit
    ```
    ```
    /home/workspace/AsurDev/scheduler_v3/api.py:132:        # Step 4: Advance job to SCHEDULED (Slurm submit)
    ```

### INFERRED #method-44
- **Source:** `AsurDev/load_test/observability/metrics.py:LL187 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector`
- **Target:** `AsurDev/load_test/observability/metrics.py:L187 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_check_slo_breaches`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/load_test/observability/metrics.py:188:        """Return list of active SLO breaches."""
    ```
    ```
    /home/workspace/AsurDev/load_test/observability/metrics.py:189:        breaches = []
    ```
    ```
    /home/workspace/AsurDev/load_test/observability/metrics.py:191:            breaches.append(f"p99_latency={metrics.p99_latency_ms:.0f}ms > {self._thresholds.p99_latency_ms}ms")
    ```

### INFERRED #method-45
- **Source:** `AsurDev/acos/events/event.py:LL36 :: asurdev_acos_events_event_py_events_event_event`
- **Target:** `AsurDev/acos/events/event.py:L36 :: asurdev_acos_events_event_py_events_event_event_post_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/__init__.py:4:    init.py         - ATOM-020: Auto-create tables on first run
    ```
    ```
    /home/workspace/push/db/__init__.py:12:from db.init import get_db_status, init_db_if_needed, init_schema_if_needed
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:22:    spread: float = field(init=False)
    ```

### INFERRED #method-46
- **Source:** `AsurDev/v6/solver/candidates/generator.py:LL37 :: asurdev_v6_solver_candidates_generator_py_candidates_generator_candidategenerator`
- **Target:** `AsurDev/v6/solver/candidates/generator.py:L37 :: asurdev_v6_solver_candidates_generator_py_candidates_generator_candidategenerator_generate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/thompson_cli.py:13:    python tools/thompson_cli.py daily-brief --ideas         # generate ATOM ideas
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:143:    # Test that visualizer can generate outputs
    ```
    ```
    /home/workspace/push/scripts/optimize_lag_blend.py:466:    # Load or generate data
    ```

### INFERRED #method-47
- **Source:** `AsurDev/hash_chain/chain.py:LL24 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain`
- **Target:** `AsurDev/hash_chain/chain.py:L24 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain_add_execution_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/mas_factory/topology.py:202:    def hash(self) -> str:
    ```
    ```
    /home/workspace/push/mas_factory/architect.py:328:        """Retrieve cached topology by hash"""
    ```
    ```
    /home/workspace/push/mas_factory/visualizer.py:120:            f"  Version: {self.topo.version} | Hash: {self.topo.hash}",
    ```

### INFERRED #method-48
- **Source:** `AsurDev/v8/incident/model.py:LL100 :: asurdev_v8_incident_model_py_incident_model_incidentmanager`
- **Target:** `AsurDev/v8/incident/model.py:L100 :: asurdev_v8_incident_model_py_incident_model_incidentmanager_route`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/scripts/architecture_linter.py:11:    R4.  Any HTTP route handler under web/ must use @require_auth (or be
    ```
    ```
    /home/workspace/audit_repo/scripts/architecture_linter.py:195:    if "@app.route" not in source_text and "@bp.route" not in source_text and ".route(" not in source_text:
    ```
    ```
    /home/workspace/audit_repo/scripts/architecture_linter.py:197:    # Find functions that are directly decorated with a route, then look for @require_auth.
    ```

### INFERRED #method-49
- **Source:** `AsurDev/v8/rollback/engine.py:LL154 :: asurdev_v8_rollback_engine_py_rollback_engine_rollbackengine`
- **Target:** `AsurDev/v8/rollback/engine.py:L154 :: asurdev_v8_rollback_engine_py_rollback_engine_rollbackengine_get_events`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/agents/_impl/macro_agent.py:174:        Searches for recent geopolitical events and scores their impact.
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/macro_agent.py:174:        Searches for recent geopolitical events and scores their impact.
    ```
    ```
    /home/workspace/AsurDev/tests/test_security_fixes.py:5:from acos.events.event_log import EventLog
    ```

### INFERRED #method-50
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL343 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testinvalidagentyaml`
- **Target:** `AstroFinSentinelV5/tests/test_validator.py:L343 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_testinvalidagentyaml_test_description_too_short_warning`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_validator.py
    ```

---

## Bucket: relation = `imports_from` (10 edges)

### INFERRED #imports_from-1
- **Source:** `atom-federation-os/actuator/stability_feedback_controller.py:LL22 :: actuator_stability_feedback_controller`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-2
- **Source:** `atom-federation-os/actuator/divergence_response_policy.py:LL19 :: actuator_divergence_response_policy`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-3
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/governance.py:LL18 :: agent_runtime_governance`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-4
- **Source:** `atom-federation-os/actuator/swarm_control_surface.py:LL18 :: actuator_swarm_control_surface`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-5
- **Source:** `AsurDev/acos.py:LL13 :: asurdev_acos`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-6
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:LL16 :: agent_runtime_event_sourcing`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-7
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/dag_recorder.py:LL15 :: agent_runtime_dag_recorder`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-8
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/task_store.py:LL20 :: agent_runtime_task_store`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-9
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/durable_queue.py:LL31 :: agent_runtime_durable_queue`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-10
- **Source:** `atom-federation-os/actuator/causal_actuation_engine.py:LL19 :: actuator_causal_actuation_engine`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

## Bucket: relation = `references` (10 edges)

### INFERRED #references-1
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL57 :: monitoring_health_endpoints_auth_middleware`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-2
- **Source:** `AstroFinSentinelV5/web/callbacks.py:LL1069 :: astrofinsentinelv5_web_callbacks_py_web_callbacks_render_live_status`
- **Target:** `AstroFinSentinelV5/web/callbacks.py:L1069 :: astrofinsentinelv5_web_callbacks_py_div`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/callbacks.py
    ```

### INFERRED #references-3
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL10 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent_run`
- **Target:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:L10 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_agentresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rag_agent_integration.py
    ```

### INFERRED #references-4
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL158 :: monitoring_health_endpoints_karl_status`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-5
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL118 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L118 :: astrofinsentinelv5_agents_archived_synthesis_agent_py_agentresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #references-6
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL445 :: archived_synthesis_agent_synthesisagent_calculate_levels`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L398 :: astrofinsentinelv5_agents_archived_synthesis_agent_py_signaldirection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #references-7
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL147 :: monitoring_health_endpoints_ab_compare`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-8
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL229 :: monitoring_health_endpoints_system_metrics`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-9
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL173 :: monitoring_health_endpoints_karl_metrics`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-10
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL398 :: archived_synthesis_agent_synthesisagent_apply_guards`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L398 :: astrofinsentinelv5_agents_archived_synthesis_agent_py_signaldirection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

---

## Bucket: relation = `re_exports` (10 edges)

### INFERRED #re_exports-1
- **Source:** `atom-federation-os/alignment/__init__.py:LL11 :: alignment_init`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L1 :: alignment_drift_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:165:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```

### INFERRED #re_exports-2
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL11 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/causal_semantic_space.py:L1 :: consistency_v3_causal_semantic_space`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/meta_rl/strategy_pool.py:163:            # Remove worst performer to make space
    ```
    ```
    /home/workspace/push/core/houses.py:49:    type: str  # time, space, ecliptic, quadrant
    ```
    ```
    /home/workspace/push/core/houses.py:56:    "C": HouseSystem("Campanus", "C", "space"),
    ```

### INFERRED #re_exports-3
- **Source:** `atom-federation-os/alignment/__init__.py:LL33 :: alignment_init`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L1 :: alignment_rollback_engine_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/agents/_impl/amre/audit.py:138:        d["_version"] = "KARL-009-v1"  # bump to v2 for risk_adjusted_pnl
    ```
    ```
    /home/workspace/push/knowledge/daily_digest/atom_proposer.py:230:            title="CrewAI v2.3 Integration для Agent Council",
    ```
    ```
    /home/workspace/push/knowledge/daily_digest/atom_proposer.py:232:            summary="CrewAI v2.3 представил hierarchical agent teams и flow visualization. "
    ```

### INFERRED #re_exports-4
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL27 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/byzantine_detector.py:L1 :: byzantine_byzantine_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/AsurDev/failure_orchestrator/orchestrator.py:165:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```

### INFERRED #re_exports-5
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL13 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/unified_state_metric_tensor.py:L1 :: consistency_v3_unified_state_metric_tensor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/swarm/swarm_divergence_field.py:69:      v7.3: per-axis field divergence with global coherence tensor
    ```
    ```
    /home/workspace/atom-federation-os/swarm/swarm_divergence_field.py:73:      distributed_tensor_alignment.py into ONE global coherence tensor.
    ```
    ```
    /home/workspace/atom-federation-os/swarm/distributed_tensor_alignment.py:3:Aligns S_full (unified_state_metric_tensor) across workers into ONE global coherence tensor.
    ```

### INFERRED #re_exports-6
- **Source:** `atom-federation-os/alignment/__init__.py:LL27 :: alignment_init`
- **Target:** `atom-federation-os/alignment/plan_reality_comparator.py:L1 :: alignment_plan_reality_comparator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/audit_repo/trading/execution/order_book.py:22:    spread: float = field(init=False)
    ```
    ```
    /home/workspace/audit_repo/trading/execution/order_book.py:23:    mid_price: float = field(init=False)
    ```
    ```
    /home/workspace/audit_repo/trading/execution/order_book.py:24:    depth_bid_10: float = field(init=False)  # total bid qty in top 10 levels
    ```

### INFERRED #re_exports-7
- **Source:** `astrofin-sentinel-v5/db/__init__.py:LL12 :: astrofin_sentinel_v5_db_init_py_db_init`
- **Target:** `astrofin-sentinel-v5/db/init.py:L1 :: astrofin_sentinel_v5_db_init_py_db_init`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/trading/execution/order_book.py:22:    spread: float = field(init=False)
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:23:    mid_price: float = field(init=False)
    ```
    ```
    /home/workspace/push/trading/execution/order_book.py:24:    depth_bid_10: float = field(init=False)  # total bid qty in top 10 levels
    ```

### INFERRED #re_exports-8
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL2 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/drl_bridge.py:L1 :: shared_drl_bridge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/agents/_impl/amre/idea_buffer_integration.py:192:    ATOM-R-041 + ATOM-016 bridge:
    ```
    ```
    /home/workspace/audit_repo/agents/_impl/amre/idea_buffer_integration.py:192:    ATOM-R-041 + ATOM-016 bridge:
    ```
    ```
    /home/workspace/AsurDev/admission_controller/probabilistic.py:6:v4.1 → v5 bridge component.
    ```

### INFERRED #re_exports-9
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL12 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/explainable_divergence_engine.py:L1 :: consistency_v3_explainable_divergence_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/scripts/compare_backtest_modes.py:11:from backtest.engine import BacktestEngine
    ```
    ```
    /home/workspace/push/scripts/compare_backtest_modes.py:15:    engine = BacktestEngine(symbol="BTCUSDT")
    ```
    ```
    /home/workspace/push/scripts/compare_backtest_modes.py:16:    return await engine.run("2025-01-01", "2025-01-10", use_real_agents=False)
    ```

### INFERRED #re_exports-10
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL3 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/rpc_server.py:L1 :: shared_rpc_server`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tools/metrics_server.py:2:"""Prometheus metrics server for AstroFin Sentinel V5.
    ```
    ```
    /home/workspace/tools/metrics_server.py:54:    parser = argparse.ArgumentParser(description="AstroFin Prometheus metrics server")
    ```
    ```
    /home/workspace/push/tools/metrics_server.py:2:"""Prometheus metrics server for AstroFin Sentinel V5.
    ```

---

# VALIDATION_REPORT.md

Stratified validation of N=167 INFERRED edges from `graphify-out/graph.json` (snapshot 2026-06-17).

**Verdict legend:**
- `valid` — link is real and current
- `false` — link does not exist in code

**Verdict summary (N=167):** `false`=91 (54%), `valid`=29 (17%), `outdated`=27 (16%), `ambiguous`=20 (12%)

- `moved` — entity exists, but in a different file (new path noted)
- `outdated` — was true at some point, now dead (e.g. `_archived/`, removed submodules)
- `ambiguous` — needs human review

---

## Bucket: relation = `calls` (27 edges)

### INFERRED #calls-1
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL148 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_evolve`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L127 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_reproduce`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/astrofin/meta_rl/engine.py:128:    def reproduce(self, selected: list["Strategy"]) -> list["Strategy"]:
    ```
    ```
    /home/workspace/home-cluster-iac/astrofin/meta_rl/engine.py:142:        3. reproduce (crossover + mutation)
    ```
    ```
    /home/workspace/home-cluster-iac/astrofin/meta_rl/engine.py:149:            self.population = self.reproduce(selected)
    ```

### INFERRED #calls-2
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL133 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L101 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ray_active_workers`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/modules/metrics.py:103:    """Ray active workers"""
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:93:        workers = num_workers or self.max_workers
    ```
    ```
    /home/workspace/atom-federation-os/tests/conftest.py:97:            'workers': workers,
    ```

### INFERRED #calls-3
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL25 :: alignment_test_bcil_test_bc_f2_quorum_bypass`
- **Target:** `atom-federation-os/alignment/bcil.py:L325 :: alignment_bcil_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-4
- **Source:** `atom-federation-os/alignment/test_convergence.py:LL105 :: alignment_test_convergence_test_convergence_layer_integration`
- **Target:** `atom-federation-os/alignment/convergence.py:L29 :: alignment_convergence_oscillationdetector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:106:@pytest.mark.integration
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:1:"""tests/test_karl_synthesis_lag.py — ATOM-KARL-015 Phase 5: Tests for LagWindow integration in KARLSynthesisAgent
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:48:# ATOM-019: PostgreSQL integration
    ```

### INFERRED #calls-5
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL430 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-6
- **Source:** `atom-federation-os/alignment/test_alignment.py:LL19 :: alignment_test_alignment_enode`
- **Target:** `atom-federation-os/alignment/drift_detector.py:L53 :: alignment_drift_detector_executednode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/alignment/plan_reality_comparator.py:287:        for exec_id, enode in by_id.items():
    ```
    ```
    /home/workspace/atom-federation-os/alignment/plan_reality_comparator.py:288:            if hasattr(enode, 'step_name') and enode.step_name == pnode.step_name:
    ```
    ```
    /home/workspace/atom-federation-os/alignment/plan_reality_comparator.py:290:            if hasattr(enode, 'tool') and enode.tool == pnode.tool:
    ```

### INFERRED #calls-7
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL146 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L247 :: archived_synthesis_agent_synthesisagent_get_signal_attr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-8
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL242 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_build_astrofin_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L169 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_latency_sla`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/constraint_graph/graph.py:18:    SLA = "sla"  # P(latency > threshold) < 0.05
    ```
    ```
    /home/workspace/AsurDev/v6/constraint_graph/graph.py:18:    SLA           = "sla"            # P(latency > threshold) < 0.05
    ```

### INFERRED #calls-9
- **Source:** `atom-federation-os/tests/test_stability_feedback_controller.py:LL109 :: tests_test_stability_feedback_controller_testoscillationdetection_test_saturation_mode`
- **Target:** `atom-federation-os/actuator/stability_feedback_controller.py:L61 :: actuator_stability_feedback_controller_stabilityfeedbackcontroller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:27:from trading.mode import ModeEnforcer, TradingMode
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:247:        assert enforcer.mode == TradingMode.LIVE_FULL
    ```
    ```
    /home/workspace/tests/test_validator.py:146:                        "Use KARL drift detection in production mode",
    ```

### INFERRED #calls-10
- **Source:** `AsurDev/job_engine/engine.py:LL159 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Target:** `AsurDev/job_engine/engine.py:L169 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_write_event`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/meta_rl/evolution.py:335:        4. Log the reset event
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:4:backends** (PostgreSQL thread-pool vs. event-sourcing KV) and **identical
    ```

### INFERRED #calls-11
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL60 :: alignment_test_bcil_test_bc_f5_convergence_to_malicious`
- **Target:** `atom-federation-os/alignment/bcil.py:L20 :: alignment_bcil_quorumspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/tools/test_p7_bft.py:316:        node_id='malicious', request_hash_a='A', request_hash_b='B',
    ```
    ```
    /home/workspace/atom-federation-os/tools/test_p7_bft.py:319:    assert engine.is_slashed('malicious')
    ```
    ```
    /home/workspace/atom-federation-os/tools/test_p7_bft.py:349:    assert engine.is_slashed('malicious')
    ```

### INFERRED #calls-12
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL192 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L330 :: archived_synthesis_agent_synthesisagent_synthesize`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-13
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL234 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L436 :: archived_synthesis_agent_synthesisagent_collect_sources`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-14
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL95 :: alignment_test_gcpl_test_checker_entropy_violation`
- **Target:** `atom-federation-os/alignment/gcpl.py:L192 :: alignment_gcpl_globalconsistencychecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:30:        1 — hard-rule violation
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:31:        2 — soft-rule violation only (still allowed in dev)
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:430:        print(RED(f"❌ {len(fails)} hard-rule violation(s). Build blocked."))
    ```

### INFERRED #calls-15
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL148 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_health_check_loop`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L127 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_reconnect_with_backoff`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/live_provider.py:134:        """Fetch with retry + exponential backoff."""
    ```
    ```
    /home/workspace/home-cluster-iac/ete/compiler/dag.py:49:    retry_policy: dict[str, Any] = field(default=lambda: {"max_retries": 3, "backoff": 2.0})
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/orchestrator.py:145:                backoff = engine.BACKOFF_BASE**attempt
    ```

### INFERRED #calls-16
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL138 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_reboot_node`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/select_top_inferred.py:121:    # end-to-end testable on every run.
    ```
    ```
    /home/workspace/graphify-out/recall_test.py:47:            f"missing {INGEST} — run `python3 graphify-out/infer_edges.py` first"
    ```
    ```
    /home/workspace/graphify-out/recall_test.py:61:        subprocess.run(
    ```

### INFERRED #calls-17
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL24 :: alignment_test_bcil_test_bc_f2_quorum_bypass`
- **Target:** `atom-federation-os/alignment/bcil.py:L20 :: alignment_bcil_quorumspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/meta_rl/reward.py:229:        Returns ``base_reward`` for inputs that should bypass the
    ```
    ```
    /home/workspace/_sbs_old/boundary_spec.py:5:All validation is strict: no soft defaults, no silent bypass.
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_enforcement_layer.py:6:#   - No bypass paths exist
    ```

### INFERRED #calls-18
- **Source:** `atom-federation-os/alignment/test_adlr.py:LL27 :: alignment_test_adlr_test_policy_attempt`
- **Target:** `atom-federation-os/alignment/adlr.py:L147 :: alignment_adlr_recoverypolicy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/meta_rl/live_provider.py:135:        for attempt in range(_CCXT_RECONNECT_ATTEMPTS):
    ```
    ```
    /home/workspace/meta_rl/live_provider.py:142:                logger.warning(f"[CCXT] {method} attempt {attempt + 1} failed: {e}")
    ```
    ```
    /home/workspace/meta_rl/live_provider.py:143:                if attempt < _CCXT_RECONNECT_ATTEMPTS - 1:
    ```

### INFERRED #calls-19
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
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_meta_control_v78.py:68:        chain_length=chain.length,
    ```

### INFERRED #calls-20
- **Source:** `atom-federation-os/alignment/test_gcpl.py:LL113 :: alignment_test_gcpl_test_checker_irreconcilable_ratio`
- **Target:** `atom-federation-os/alignment/gcpl.py:L192 :: alignment_gcpl_globalconsistencychecker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/_impl/risk_agent.py:25:    4. Validate risk/reward ratio
    ```
    ```
    /home/workspace/agents/_impl/synthesis_agent.py:560:        rr_ratio = 2.5  # risk-reward ratio
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:164:    Compute Sharpe ratio if PnL column is available.
    ```

### INFERRED #calls-21
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL84 :: alignment_test_bcil_test_bc_safe_merge`
- **Target:** `atom-federation-os/alignment/bcil.py:L325 :: alignment_bcil_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-22
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL61 :: alignment_test_bcil_test_bc_f5_convergence_to_malicious`
- **Target:** `atom-federation-os/alignment/bcil.py:L325 :: alignment_bcil_bcil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-23
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL431 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L35 :: validators_agent_validator_validationreport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-24
- **Source:** `atom-federation-os/alignment/test_bcil.py:LL96 :: alignment_test_bcil_test_bc_split_brain`
- **Target:** `atom-federation-os/alignment/bcil.py:L20 :: alignment_bcil_quorumspec`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:3:Ceph Diagnostics — FIX-004 L4 CRITICAL: proper Ceph quorum + split-brain handling
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:8:  1.4 split-brain detection with single-MON quorum risk
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:245:    FIX 1.4: Proper split-brain detection.
    ```

### INFERRED #calls-25
- **Source:** `astrofin-sentinel-v5/tests/data_room/test_data_room.py:LL68 :: astrofin_sentinel_v5_tests_data_room_test_data_room_py_data_room_test_data_room_test_circuit_breaker_half_open_recovery`
- **Target:** `data_room/circuit_breaker.py:L41 :: data_room_circuit_breaker_circuitbreaker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:279:    FIX 3.2: Structured recovery actions.
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:325:                "reason": f"{len(status.pgs_deep)} PGs deep-scrubbing (recovery overload)",
    ```
    ```
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:61:        - On incident: before recovery action
    ```

### INFERRED #calls-26
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL451 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_all_pass`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:299:                    pass
    ```
    ```
    /home/workspace/agents/metrics.py:153:            pass
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:359:                pass  # Non-fatal
    ```

### INFERRED #calls-27
- **Source:** `AsurDev/lccp_v12.py:LL138 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L51 :: asurdev_lccp_v12_staterebuilder_verify`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:3:These tests verify authentication behavior including edge cases.
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:21:        # Just verify the function signature and it doesn't crash
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:48:            # We can't easily test main(), so just verify the architecture
    ```

---

## Bucket: relation = `contains` (20 edges)

### INFERRED #contains-1
- **Source:** `AstroFinSentinelV5/tests/test_dual_mode.py:LL51 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode`
- **Target:** `AstroFinSentinelV5/tests/test_dual_mode.py:L51 :: astrofinsentinelv5_tests_test_dual_mode_py_tests_test_dual_mode_test_dual_mode_detection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_dual_mode.py
    ```

### INFERRED #contains-2
- **Source:** `AstroFinSentinelV5/tests/test_ai_editorconfig.py:LL6 :: astrofinsentinelv5_tests_test_ai_editorconfig_py_tests_test_ai_editorconfig`
- **Target:** `AstroFinSentinelV5/tests/test_ai_editorconfig.py:L6 :: astrofinsentinelv5_tests_test_ai_editorconfig_py_tests_test_ai_editorconfig_test_cursorrules_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_ai_editorconfig.py
    ```

### INFERRED #contains-3
- **Source:** `AstroFinSentinelV5/tests/test_auth.py:LL20 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth`
- **Target:** `AstroFinSentinelV5/tests/test_auth.py:L20 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth_test_flask_unauthenticated_returns_401`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth.py
    ```

### INFERRED #contains-4
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL147 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L147 :: monitoring_health_endpoints_ab_compare`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-5
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL66 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L66 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_ollama_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #contains-6
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #contains-7
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL60 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L60 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_both_modes_return_same_structure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #contains-8
- **Source:** `AstroFinSentinelV5/tests/e2e/test_api_endpoints.py:LL19 :: astrofinsentinelv5_tests_e2e_test_api_endpoints_py_e2e_test_api_endpoints`
- **Target:** `AstroFinSentinelV5/tests/e2e/test_api_endpoints.py:L19 :: e2e_test_api_endpoints_test_rate_limiting`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/e2e/test_api_endpoints.py
    ```

### INFERRED #contains-9
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL101 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L101 :: monitoring_health_endpoints_health_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-10
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #contains-11
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL133 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_monitoring_health_endpoints`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L133 :: monitoring_health_endpoints_root`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #contains-12
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL154 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L154 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testheliocentriclongitude`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #contains-13
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL159 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L159 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_synthesis_agent_called_in_real_mode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #contains-14
- **Source:** `AstroFinSentinelV5/tests/test_auth_middleware.py:LL8 :: tests_test_auth_middleware`
- **Target:** `AstroFinSentinelV5/tests/test_auth_middleware.py:L8 :: tests_test_auth_middleware_client`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth_middleware.py
    ```

### INFERRED #contains-15
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL57 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L57 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_db_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #contains-16
- **Source:** `AstroFinSentinelV5/tests/test_auth.py:LL30 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth`
- **Target:** `AstroFinSentinelV5/tests/test_auth.py:L30 :: astrofinsentinelv5_tests_test_auth_py_tests_test_auth_test_public_metrics_returns_200`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_auth.py
    ```

### INFERRED #contains-17
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL12 :: astrofinsentinelv5_tests_test_council_py_tests_test_council`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L12 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #contains-18
- **Source:** `AstroFinSentinelV5/tests/ralph_benchmark/test_agent_basic.py:LL22 :: astrofinsentinelv5_tests_ralph_benchmark_test_agent_basic_py_ralph_benchmark_test_agent_basic`
- **Target:** `AstroFinSentinelV5/tests/ralph_benchmark/test_agent_basic.py:L22 :: astrofinsentinelv5_tests_ralph_benchmark_test_agent_basic_py_ralph_benchmark_test_agent_basic_test_agent_can_create_add_function`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/ralph_benchmark/test_agent_basic.py
    ```

### INFERRED #contains-19
- **Source:** `AstroFinSentinelV5/tests/test_ai_editorconfig.py:LL14 :: astrofinsentinelv5_tests_test_ai_editorconfig_py_tests_test_ai_editorconfig`
- **Target:** `AstroFinSentinelV5/tests/test_ai_editorconfig.py:L14 :: astrofinsentinelv5_tests_test_ai_editorconfig_py_tests_test_ai_editorconfig_test_cursorrules_references_agents_md`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_ai_editorconfig.py
    ```

### INFERRED #contains-20
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL52 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L52 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_positive_eccentricity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `contains`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
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
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/orchestrator.py:169:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/atom-federation-os/consistency_v2/test_realtime_divergence_detector.py:31:    detector = RealtimeDivergenceDetector(
    ```

### INFERRED #re_exports-2
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL13 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/unified_state_metric_tensor.py:L1 :: consistency_v3_unified_state_metric_tensor`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/actuator/swarm_control_surface.py:106:        Map the global S_full tensor (canonical + deltas) into control vectors.
    ```
    ```
    /home/workspace/atom-federation-os/swarm/distributed_tensor_alignment.py:3:Aligns S_full (unified_state_metric_tensor) across workers into ONE global coherence tensor.
    ```
    ```
    /home/workspace/atom-federation-os/swarm/distributed_tensor_alignment.py:7:  we compute S_full per partition, then reconcile into ONE global tensor.
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
- **Source:** `atom-federation-os/federation/byzantine/__init__.py:LL27 :: byzantine_init`
- **Target:** `atom-federation-os/federation/byzantine/byzantine_detector.py:L1 :: byzantine_byzantine_detector`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:5:Each detector returns (is_down: bool, reason: str, severity: str)
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/orchestrator.py:169:                log.info(f"Previously failed detector now OK: {name}")
    ```
    ```
    /home/workspace/atom-federation-os/federation/semantic/v910.py:315:        detector = DriftDetector(store=snap)
    ```

### INFERRED #re_exports-5
- **Source:** `atom-federation-os/alignment/__init__.py:LL27 :: alignment_init`
- **Target:** `atom-federation-os/alignment/plan_reality_comparator.py:L1 :: alignment_plan_reality_comparator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```
    ```
    /home/workspace/tests/test_db_init.py:10:        importlib.import_module("db.init")
    ```
    ```
    /home/workspace/tests/test_db_init.py:12:        pytest.fail(f"db.init should be importable: {e}")
    ```

### INFERRED #re_exports-6
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL12 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/explainable_divergence_engine.py:L1 :: consistency_v3_explainable_divergence_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:9:from backtest.engine import BacktestEngine
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:15:    engine = BacktestEngine(symbol="BTCUSDT", initial_capital=10000)
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:30:        result = await engine.run(start_date="2025-01-01", end_date="2025-01-10", use_real_agents=True)
    ```

### INFERRED #re_exports-7
- **Source:** `atom-federation-os/consistency_v3/__init__.py:LL11 :: consistency_v3_init`
- **Target:** `atom-federation-os/consistency_v3/causal_semantic_space.py:L1 :: consistency_v3_causal_semantic_space`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:238:            # Remove worst performer to make space
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/prune/beam.py:24:    Prunes candidate space using beam search with variance estimation.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/policy_eval/evaluator.py:4:Policy space: (priority_weights, risk_threshold, admission_policy)
    ```

### INFERRED #re_exports-8
- **Source:** `atom-federation-os/cluster/shared/__init__.py:LL2 :: shared_init`
- **Target:** `atom-federation-os/cluster/shared/drl_bridge.py:L1 :: shared_drl_bridge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:81:    "push/", "atom-federation-os/", "roma-execution-bridge/",
    ```
    ```
    /home/workspace/agents/_impl/amre/idea_buffer_integration.py:194:    ATOM-R-041 + ATOM-016 bridge:
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/errors.py:4:AsurDev, home-cluster-iac, roma-execution-bridge) raise and catch the *same*
    ```

### INFERRED #re_exports-9
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

### INFERRED #re_exports-10
- **Source:** `atom-federation-os/alignment/__init__.py:LL33 :: alignment_init`
- **Target:** `atom-federation-os/alignment/rollback_engine_v2.py:L1 :: alignment_rollback_engine_v2`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `re_exports`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/audit.py:140:        d["_version"] = "KARL-009-v1"  # bump to v2 for risk_adjusted_pnl
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler_v2.py:3:AI Scheduler v2 — FastAPI Service
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler_v2.py:18:app = FastAPI(title="AI Scheduler v2", version="2.0.0")
    ```

---

## Bucket: relation = `defines` (10 edges)

### INFERRED #defines-1
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
    /home/workspace/home-cluster-iac/scheduler_v3/api.py:191:    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    ```

### INFERRED #defines-2
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:243:TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}
    ```

### INFERRED #defines-3
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

### INFERRED #defines-4
- **Source:** `AsurDev/scripts/day1-network.sh:LL78 :: asurdev_scripts_day1_network_sh_scripts_day1_network`
- **Target:** `AsurDev/scripts/day1-network.sh:L78 :: asurdev_scripts_day1_network_sh_scripts_day1_network_create_vlan`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_wg.py:64:        self._trace_id = trace_id or "network-bootstrap"
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_patch.py:18:    from acos.network.amnezia_wg import AmneziaWGManager
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_patch.py:24:    PATCH 1a: DAGValidator network check.
    ```

### INFERRED #defines-5
- **Source:** `AsurDev/scripts/day3-compute.sh:LL25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute`
- **Target:** `AsurDev/scripts/day3-compute.sh:L25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_detect_os`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:23:import os
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:34:import os
    ```

### INFERRED #defines-6
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL32 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L32 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:151:                    "reasoning": "ok",
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:181:                {"signal": "NEUTRAL", "confidence": 50, "reasoning": "ok"},
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:36:        ok, dd, msg = engine.check_kill_switch()
    ```

### INFERRED #defines-7
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_command_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agents_md.py:13:    assert agents_md.exists(), "AGENTS.md not found"
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:88:    """Delete each path if it exists. Path may be a file or a directory."""
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:92:        if p.exists():
    ```

### INFERRED #defines-8
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

### INFERRED #defines-9
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `defines`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agents_md.py:31:    assert "_archived" in content, "Should warn about archived modules"
    ```
    ```
    /home/workspace/meta_rl/test_reward.py:59:        Without this, ``__post_init__`` would warn every time the default
    ```
    ```
    /home/workspace/meta_rl/test_reward.py:68:        """Constructing RewardConfig() must not warn."""
    ```

### INFERRED #defines-10
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
    /home/workspace/agents/_impl/sentiment_agent.py:91:            url = "https://api.alternative.me/fng/?limit=1"
    ```

---

## Bucket: relation = `uses` (20 edges)

### INFERRED #uses-1
- **Source:** `audit_repo/langgraph_schema.py:LL309 :: audit_repo_langgraph_schema_py_stategraph`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-2
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testswissephemerisvalidation`
- **Target:** `push/core/kepler.py:L90 :: push_core_kepler_py_core_kepler_keplerorbit`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerorbit' not found in push/core/kepler.py
    ```

### INFERRED #uses-3
- **Source:** `audit_repo/agents/karl_synthesis.py:LL44 :: audit_repo_agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-4
- **Source:** `audit_repo/backtest/engine.py:LL20 :: audit_repo_backtest_engine_py_backtest_engine_backtestresult`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-5
- **Source:** `backtest/engine.py:LL20 :: backtest_engine_py_backtest_engine_ohlcv`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-6
- **Source:** `push/agents/karl_synthesis.py:LL44 :: push_agents_karl_synthesis_py_any`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-7
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testorbitalelements`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-8
- **Source:** `astrofin-sentinel-v5/backtest/engine.py:LL20 :: astrofin_sentinel_v5_backtest_engine_py_datetime`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-9
- **Source:** `audit_repo/langgraph_schema.py:LL309 :: audit_repo_langgraph_schema_py_agentpool`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-10
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL15 :: astrofinsentinelv5_agents_archived_synthesis_agent_py_signaldirection`
- **Target:** `push/core/volatility.py:L107 :: push_core_volatility_py_core_volatility_volatilityengine`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'volatilityengine' not found in push/core/volatility.py
    ```

### INFERRED #uses-11
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testswissephemerisvalidation`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-12
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL345 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `push/agents/karl_synthesis.py:L70 :: push_agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'karlsynthesisagent' not found in push/agents/karl_synthesis.py
    ```

### INFERRED #uses-13
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL14 :: archived_synthesis_agent_synthesisagent`
- **Target:** `push/core/base_agent.py:L41 :: push_core_base_agent_py_core_base_agent_signaldirection`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'signaldirection' not found in push/core/base_agent.py
    ```

### INFERRED #uses-14
- **Source:** `astrofin-sentinel-v5/langgraph_schema.py:LL309 :: astrofin_sentinel_v5_langgraph_schema_py_thompsonsampler`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-15
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testmeananomaly`
- **Target:** `push/core/kepler.py:L26 :: push_core_kepler_py_core_kepler_orbitalelements`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'orbitalelements' not found in push/core/kepler.py
    ```

### INFERRED #uses-16
- **Source:** `push/langgraph_schema.py:LL309 :: push_langgraph_schema_py_stategraph`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-17
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL14 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerresult`
- **Target:** `push/core/kepler.py:L209 :: push_core_kepler_py_core_kepler_keplerresult`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'keplerresult' not found in push/core/kepler.py
    ```

### INFERRED #uses-18
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL15 :: astrofinsentinelv5_agents_archived_synthesis_agent_py_agentresponse`
- **Target:** `push/core/volatility.py:L107 :: push_core_volatility_py_core_volatility_volatilityengine`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'volatilityengine' not found in push/core/volatility.py
    ```

### INFERRED #uses-19
- **Source:** `backtest/engine.py:LL20 :: backtest_engine_py_datetime`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #uses-20
- **Source:** `push/agents/karl_synthesis.py:LL44 :: push_agents_karl_synthesis_py_agents_karl_synthesis_karlsynthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 0.500  **Weight:** 0.80  **Relation:** `uses`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

---

## Bucket: relation = `rationale_for` (20 edges)

### INFERRED #rationale_for-1
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL160 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_160`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L159 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_all_metrics_keys_present`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-2
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL1 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L1 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-3
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL102 :: archived_synthesis_agent_rationale_102`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #rationale_for-4
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL215 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_215`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L214 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_test_validate_returns_all_keys`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-5
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL68 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_68`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L67 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_agent_with_mocks`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-6
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL122 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_rationale_122`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L121 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_mature_window_flag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #rationale_for-7
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL25 :: archived_synthesis_agent_rationale_25`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L24 :: archived_synthesis_agent_load_weights`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #rationale_for-8
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL1 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_1`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L1 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-9
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL66 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_66`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L65 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_mean_anomaly_360`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-10
- **Source:** `AstroFinSentinelV5/tests/test_agent_http_migration.py:LL2 :: tests_test_agent_http_migration_rationale_2`
- **Target:** `AstroFinSentinelV5/tests/test_agent_http_migration.py:L1 :: astrofinsentinelv5_tests_test_agent_http_migration_py_tests_test_agent_http_migration_test_quant_agent_no_sync_requests`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_agent_http_migration.py
    ```

### INFERRED #rationale_for-11
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL35 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_35`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L34 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-12
- **Source:** `AstroFinSentinelV5/tests/test_agents_md.py:LL6 :: tests_test_agents_md_rationale_6`
- **Target:** `AstroFinSentinelV5/tests/test_agents_md.py:L5 :: astrofinsentinelv5_tests_test_agents_md_py_tests_test_agents_md_test_agents_md_has_ai_rules_section`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_agents_md.py
    ```

### INFERRED #rationale_for-13
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL227 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_rationale_227`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L226 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_elliot_agent_called_in_real_mode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #rationale_for-14
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL490 :: archived_synthesis_agent_rationale_490`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L489 :: archived_synthesis_agent_run_synthesis_agent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #rationale_for-15
- **Source:** `AstroFinSentinelV5/tests/test_kepler_property.py:LL40 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_rationale_40`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_property.py:L35 :: astrofinsentinelv5_tests_test_kepler_property_py_tests_test_kepler_property_jd_range`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_property.py
    ```

### INFERRED #rationale_for-16
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL41 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_41`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L40 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_j2000_mean_accuracy_outer_planets`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-17
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL12 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_rationale_12`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L11 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_use_real_agents_does_not_generate_synthetic_signals`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #rationale_for-18
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL204 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_rationale_204`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L203 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity_test_saturn_no_teleportation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #rationale_for-19
- **Source:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:LL96 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_rationale_96`
- **Target:** `AstroFinSentinelV5/tests/test_backtest_real_agents.py:L95 :: astrofinsentinelv5_tests_test_backtest_real_agents_py_tests_test_backtest_real_agents_test_macro_agent_called_in_real_mode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_backtest_real_agents.py
    ```

### INFERRED #rationale_for-20
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL92 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_rationale_92`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L91 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation_test_eccentric_anomaly_convergence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `rationale_for`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
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
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL147 :: monitoring_health_endpoints_ab_compare`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
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
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL173 :: monitoring_health_endpoints_karl_metrics`
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
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL229 :: monitoring_health_endpoints_system_metrics`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-8
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL398 :: archived_synthesis_agent_synthesisagent_apply_guards`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L398 :: astrofinsentinelv5_agents_archived_synthesis_agent_py_signaldirection`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #references-9
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL158 :: monitoring_health_endpoints_karl_status`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L57 :: astrofinsentinelv5_deploy_monitoring_health_endpoints_py_request`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #references-10
- **Source:** `AstroFinSentinelV5/web/callbacks.py:LL1069 :: astrofinsentinelv5_web_callbacks_py_web_callbacks_render_live_status`
- **Target:** `AstroFinSentinelV5/web/callbacks.py:L1069 :: astrofinsentinelv5_web_callbacks_py_div`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `references`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/callbacks.py
    ```

---

## Bucket: relation = `method` (20 edges)

### INFERRED #method-1
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL225 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L225 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration_test_position_risk_adjusted_flag_set`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-2
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL140 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L140 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_all_agents`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-3
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL134 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L134 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_immature_window_flag`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-4
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL91 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L91 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testkeplerequation_test_eccentric_anomaly_convergence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-5
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL100 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L100 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_weighted_signal`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-6
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL189 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L189 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testriskcontrolintegration_test_risk_adjustment_called_when_mature`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-7
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL255 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L255 :: archived_synthesis_agent_synthesisagent_group_by_category`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-8
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL412 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L412 :: archived_synthesis_agent_synthesisagent_format_breakdown`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-9
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL330 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L330 :: archived_synthesis_agent_synthesisagent_synthesize`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-10
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL13 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L13 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_majority_long`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-11
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL86 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L86 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_disabled_returns_unchanged`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-12
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL344 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L344 :: archived_synthesis_agent_synthesisagent_vote`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-13
- **Source:** `AstroFinSentinelV5/tests/test_kepler.py:LL39 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testorbitalelements`
- **Target:** `AstroFinSentinelV5/tests/test_kepler.py:L39 :: astrofinsentinelv5_tests_test_kepler_py_tests_test_kepler_testorbitalelements_test_saturn_elements_exist`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler.py
    ```

### INFERRED #method-14
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL299 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L299 :: archived_synthesis_agent_synthesisagent_detect_conflicts`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-15
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL436 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L436 :: archived_synthesis_agent_synthesisagent_collect_sources`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #method-16
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL342 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L342 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testrunwithlagwindow_test_confidence_capped_at_bounds`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-17
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL103 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L103 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_enabled_smooths_confidence`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-18
- **Source:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:LL159 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing`
- **Target:** `AstroFinSentinelV5/tests/test_karl_synthesis_lag.py:L159 :: astrofinsentinelv5_tests_test_karl_synthesis_lag_py_tests_test_karl_synthesis_lag_testapplylagsmoothing_test_all_metrics_keys_present`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_karl_synthesis_lag.py
    ```

### INFERRED #method-19
- **Source:** `AstroFinSentinelV5/tests/test_council.py:LL72 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil`
- **Target:** `AstroFinSentinelV5/tests/test_council.py:L72 :: astrofinsentinelv5_tests_test_council_py_tests_test_council_testastrocouncil_test_neutral_tie`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_council.py
    ```

### INFERRED #method-20
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL398 :: archived_synthesis_agent_synthesisagent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L398 :: archived_synthesis_agent_synthesisagent_apply_guards`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `method`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

---

## Bucket: relation = `imports` (10 edges)

### INFERRED #imports-1
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
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

### INFERRED #imports-2
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/select_top_inferred.py:9:graph.json → validator).
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-3
- **Source:** `astrofin-sentinel-v5/db/models.py:LL7 :: astrofin_sentinel_v5_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-4
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/select_top_inferred.py:9:graph.json → validator).
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:192:    The validator's CLI default is a stale /tmp/inferred_sample_500.json.
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:207:        raise SystemExit(f"validator failed: {proc.stderr}")
    ```

### INFERRED #imports-5
- **Source:** `push/db/models.py:LL7 :: push_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-6
- **Source:** `audit_repo/db/models.py:LL7 :: audit_repo_db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-7
- **Source:** `db/models.py:LL7 :: db_models_py_db_models`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports-8
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L35 :: validators_agent_validator_validationreport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/select_top_inferred.py:9:graph.json → validator).
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```

### INFERRED #imports-9
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL10 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_validator.py:23:def validator():
    ```
    ```
    /home/workspace/tests/test_validator.py:38:    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
    ```
    ```
    /home/workspace/tests/test_validator.py:59:        result = validator.validate_file(agent_dir / "agent.yaml")
    ```

### INFERRED #imports-10
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/dag_retry.py:LL13 :: agent_runtime_dag_retry`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

## Bucket: relation = `inherits` (10 edges)

### INFERRED #inherits-1
- **Source:** `roma-execution-bridge/deploy/stripe-webhook/app/main.py:LL76 :: app_main_webhookresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-2
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL175 :: agent_runtime_app_taskstatusresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-3
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL31 :: monitoring_health_endpoints_healthresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-4
- **Source:** `astrofin-sentinel-v5/orchestration/router.py:LL24 :: astrofin_sentinel_v5_orchestration_router_py_orchestration_router_routeroutput`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-5
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL186 :: agent_runtime_app_queuestatsresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-6
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL162 :: agent_runtime_app_taskcreate`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-7
- **Source:** `astrofin-sentinel-v5/health_endpoints.py:LL31 :: astrofin_sentinel_v5_health_endpoints_healthresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-8
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL68 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_jobrequest`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-9
- **Source:** `astrofin-sentinel-v5/orchestration/models.py:LL20 :: astrofin_sentinel_v5_orchestration_models_py_orchestration_models_sentinelv5request`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #inherits-10
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/app.py:LL169 :: agent_runtime_app_tasksubmitresponse`
- **Target:** `(empty): :: basemodel`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `inherits`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

## Bucket: relation = `imports_from` (10 edges)

### INFERRED #imports_from-1
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/event_sourcing.py:LL16 :: agent_runtime_event_sourcing`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-2
- **Source:** `atom-federation-os/actuator/causal_actuation_engine.py:LL19 :: actuator_causal_actuation_engine`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-3
- **Source:** `atom-federation-os/actuator/divergence_response_policy.py:LL19 :: actuator_divergence_response_policy`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-4
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/durable_queue.py:LL31 :: agent_runtime_durable_queue`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-5
- **Source:** `atom-federation-os/actuator/stability_feedback_controller.py:LL22 :: actuator_stability_feedback_controller`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-6
- **Source:** `atom-federation-os/actuator/swarm_control_surface.py:LL18 :: actuator_swarm_control_surface`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-7
- **Source:** `AsurDev/acos.py:LL13 :: asurdev_acos`
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
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/dag_recorder.py:LL15 :: agent_runtime_dag_recorder`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

### INFERRED #imports_from-10
- **Source:** `atom-federation-os/local-ai-stack/agent-runtime/agent_runtime/governance.py:LL18 :: agent_runtime_governance`
- **Target:** `(empty): :: enum`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `imports_from`
- **Verdict:** **false**
- **Evidence:**
    ```
    empty_target_source_file
    ```

---

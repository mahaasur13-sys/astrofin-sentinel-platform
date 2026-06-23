# VALIDATION_REPORT.md

Stratified validation of the top-100 INFERRED edges from `graphify-out/graph.json` (snapshot 2026-06-17).

**Verdict legend:**
- `valid` — link is real and current
- `false` — link does not exist in code

**Verdict summary (N=500):** `valid`=409 (82%), `ambiguous`=55 (11%), `false`=21 (4%), `outdated`=15 (3%)

- `moved` — entity exists, but in a different file (new path noted)
- `outdated` — was true at some point, now dead (e.g. `_archived/`, removed submodules)
- `ambiguous` — needs human review

---

## Bucket: relation = `calls` (500 edges)

### INFERRED #calls-1
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL491 :: archived_synthesis_agent_run_synthesis_agent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L101 :: archived_synthesis_agent_synthesisagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-2
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL492 :: archived_synthesis_agent_run_synthesis_agent`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L118 :: archived_synthesis_agent_synthesisagent_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-3
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL214 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L445 :: archived_synthesis_agent_synthesisagent_calculate_levels`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-4
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL234 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L436 :: archived_synthesis_agent_synthesisagent_collect_sources`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-5
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL189 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L299 :: archived_synthesis_agent_synthesisagent_detect_conflicts`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-6
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL211 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L412 :: archived_synthesis_agent_synthesisagent_format_breakdown`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
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
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL186 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L255 :: archived_synthesis_agent_synthesisagent_group_by_category`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-9
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL192 :: archived_synthesis_agent_synthesisagent_run`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L330 :: archived_synthesis_agent_synthesisagent_synthesize`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-10
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL440 :: archived_synthesis_agent_synthesisagent_collect_sources`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L247 :: archived_synthesis_agent_synthesisagent_get_signal_attr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-11
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL422 :: archived_synthesis_agent_synthesisagent_format_breakdown`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L247 :: archived_synthesis_agent_synthesisagent_get_signal_attr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-12
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL292 :: archived_synthesis_agent_synthesisagent_group_by_category`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L247 :: archived_synthesis_agent_synthesisagent_get_signal_attr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-13
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL359 :: archived_synthesis_agent_synthesisagent_vote`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L247 :: archived_synthesis_agent_synthesisagent_get_signal_attr`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-14
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL341 :: archived_synthesis_agent_synthesisagent_synthesize`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L344 :: archived_synthesis_agent_synthesisagent_vote`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-15
- **Source:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:LL390 :: archived_synthesis_agent_synthesisagent_vote`
- **Target:** `AstroFinSentinelV5/agents/_archived/synthesis_agent.py:L398 :: archived_synthesis_agent_synthesisagent_apply_guards`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **outdated**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/agents/_archived/synthesis_agent.py
    ```

### INFERRED #calls-16
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL102 :: monitoring_health_endpoints_health_check`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L31 :: monitoring_health_endpoints_healthresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #calls-17
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL113 :: monitoring_health_endpoints_readiness_check`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L70 :: monitoring_health_endpoints_check_postgres`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #calls-18
- **Source:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:LL114 :: monitoring_health_endpoints_readiness_check`
- **Target:** `AstroFinSentinelV5/deploy/monitoring/health_endpoints.py:L86 :: monitoring_health_endpoints_check_redis`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/deploy/monitoring/health_endpoints.py
    ```

### INFERRED #calls-19
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL60 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_db_check`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #calls-20
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL41 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_exit_code_ok_when_all_good`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #calls-21
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL69 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_ollama_check`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #calls-22
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL32 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_outputs_json`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #calls-23
- **Source:** `AstroFinSentinelV5/tests/test_healthcheck.py:LL50 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_test_healthcheck_venv_check`
- **Target:** `AstroFinSentinelV5/tests/test_healthcheck.py:L14 :: astrofinsentinelv5_tests_test_healthcheck_py_tests_test_healthcheck_run_healthcheck`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_healthcheck.py
    ```

### INFERRED #calls-24
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL70 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_earth_frame_difference_acknowledged`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-25
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL49 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_j2000_mean_accuracy_outer_planets`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-26
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL115 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_kepler_periodicity`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-27
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL89 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testdifferentialswissephemeris_test_no_catastrophic_divergence`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-28
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL183 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity_test_earth_one_year_return`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-29
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL192 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity_test_jupiter_slow_motion`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-30
- **Source:** `AstroFinSentinelV5/tests/test_kepler_differential.py:LL208 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_testswissephemerissanity_test_saturn_no_teleportation`
- **Target:** `AstroFinSentinelV5/tests/test_kepler_differential.py:L26 :: astrofinsentinelv5_tests_test_kepler_differential_py_tests_test_kepler_differential_angular_sep`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_kepler_differential.py
    ```

### INFERRED #calls-31
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL45 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_test_build_prompt_handles_ollama_unavailable`
- **Target:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:L7 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rag_agent_integration.py
    ```

### INFERRED #calls-32
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL20 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_test_build_prompt_includes_rag_results`
- **Target:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:L7 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rag_agent_integration.py
    ```

### INFERRED #calls-33
- **Source:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:LL38 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_test_build_prompt_no_rag_when_disabled`
- **Target:** `AstroFinSentinelV5/tests/test_rag_agent_integration.py:L7 :: astrofinsentinelv5_tests_test_rag_agent_integration_py_tests_test_rag_agent_integration_mockagent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_rag_agent_integration.py
    ```

### INFERRED #calls-34
- **Source:** `AstroFinSentinelV5/tests/test_update_progress.py:LL47 :: astrofinsentinelv5_tests_test_update_progress_py_tests_test_update_progress_test_generates_progress_file`
- **Target:** `AstroFinSentinelV5/tests/test_update_progress.py:L12 :: astrofinsentinelv5_tests_test_update_progress_py_tests_test_update_progress_run_script`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/tests/test_update_progress.py
    ```

### INFERRED #calls-35
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL430 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
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
    /home/workspace/atom-federation-os/sbs/cli.py:3:Rich output, auto-completion, --json, -v/-vv/--quiet.
    ```
    ```
    /home/workspace/atom-federation-os/sbs/cli.py:46:quiet_opt = typer.Option(False, "--quiet", "-q", help="Suppress all output")
    ```

### INFERRED #calls-36
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL435 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L17 :: validators_agent_validator_validationissue`
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

### INFERRED #calls-37
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

### INFERRED #calls-38
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL432 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_quiet`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
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

### INFERRED #calls-39
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL448 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_all_pass`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L43 :: validators_agent_validator_agentyamlvalidator`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:35:        f"linter should pass on template, got:\n{rc.stdout}\n{rc.stderr}"
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:68:    pass
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:84:    pass
    ```

### INFERRED #calls-40
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL449 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_all_pass`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L35 :: validators_agent_validator_validationreport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:265:                    pass
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:257:                        pass  # skip if instantiation fails
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:259:            pass
    ```

### INFERRED #calls-41
- **Source:** `AstroFinSentinelV5/tests/test_validator.py:LL451 :: astrofinsentinelv5_tests_test_validator_py_tests_test_validator_test_print_report_all_pass`
- **Target:** `integrations/gitagent/validators/agent_validator.py:L26 :: validators_agent_validator_validationresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:265:                    pass
    ```
    ```
    /home/workspace/tests/test_logging.py:35:        pass
    ```
    ```
    /home/workspace/tests/test_healthcheck.py:89:        pass
    ```

### INFERRED #calls-42
- **Source:** `AstroFinSentinelV5/web/utils/notifications.py:LL32 :: astrofinsentinelv5_web_utils_notifications_py_utils_notifications_make_toast`
- **Target:** `AstroFinSentinelV5/web/utils/notifications.py:L60 :: astrofinsentinelv5_web_utils_notifications_py_div`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    file_not_found: AstroFinSentinelV5/web/utils/notifications.py
    ```

### INFERRED #calls-43
- **Source:** `AsurDev/acos.py:LL142 :: asurdev_acos_acosorchestrator_init`
- **Target:** `AsurDev/acos.py:L144 :: asurdev_acos_acosorchestrator_init_components`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/reward.py:59:    ATOM-META-RL-004: All pnl components MUST use ``risk_adjusted_pnl``,
    ```
    ```
    /home/workspace/meta_rl/reward.py:201:        Return a detailed breakdown of reward components.
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/observability/metrics.py:3:Observability Layer — collects metrics from all system components.
    ```

### INFERRED #calls-44
- **Source:** `AsurDev/acos/cli/monitor.py:LL47 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_status`
- **Target:** `AsurDev/acos/cli/monitor.py:L22 :: asurdev_acos_cli_monitor_py_cli_monitor_load_config`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:14:  - manual overrides from config/memory_overrides.json
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:20:  - /home/workspace/config/memory_overrides.json
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:41:OVERRIDES_JSON = REPO_ROOT / "config" / "memory_overrides.json"
    ```

### INFERRED #calls-45
- **Source:** `AsurDev/acos/cli/monitor.py:LL82 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_switch`
- **Target:** `AsurDev/acos/cli/monitor.py:L22 :: asurdev_acos_cli_monitor_py_cli_monitor_load_config`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:14:  - manual overrides from config/memory_overrides.json
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:20:  - /home/workspace/config/memory_overrides.json
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:41:OVERRIDES_JSON = REPO_ROOT / "config" / "memory_overrides.json"
    ```

### INFERRED #calls-46
- **Source:** `AsurDev/acos/cli/monitor.py:LL124 :: asurdev_acos_cli_monitor_py_cli_monitor_main`
- **Target:** `AsurDev/acos/cli/monitor.py:L22 :: asurdev_acos_cli_monitor_py_cli_monitor_load_config`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_integration.py:35:    config = RiskConfigV2(max_exposure_per_asset=0.10, correlation_limit=0.8, target_volatility=0.15)
    ```
    ```
    /home/workspace/tests/test_risk_integration.py:36:    engine = RiskEngineV2(config)
    ```
    ```
    /home/workspace/tests/conftest.py:6:def pytest_configure(config):
    ```

### INFERRED #calls-47
- **Source:** `AsurDev/acos/cli/monitor.py:LL85 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_switch`
- **Target:** `AsurDev/acos/cli/monitor.py:L27 :: asurdev_acos_cli_monitor_py_cli_monitor_save_config`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:14:  - manual overrides from config/memory_overrides.json
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:20:  - /home/workspace/config/memory_overrides.json
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:41:OVERRIDES_JSON = REPO_ROOT / "config" / "memory_overrides.json"
    ```

### INFERRED #calls-48
- **Source:** `AsurDev/acos/cli/monitor.py:LL71 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_status`
- **Target:** `AsurDev/acos/cli/monitor.py:L30 :: asurdev_acos_cli_monitor_py_cli_monitor_check_port`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_metrics_cli.py:22:    assert "--port" in result.stdout, "Should have --port option"
    ```
    ```
    /home/workspace/scripts/validate_docker_security.py:56:                    errors.append(f"{svc_name}: port {port_str} is not bound to 127.0.0.1")
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:109:def node_unreachable(host: str, port: int = 22, timeout: int = 3) -> tuple[bool, str, str]:
    ```

### INFERRED #calls-49
- **Source:** `AsurDev/acos/cli/monitor.py:LL53 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_status`
- **Target:** `AsurDev/acos/cli/monitor.py:L37 :: asurdev_acos_cli_monitor_py_cli_monitor_get_tunnel_status`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:58:        status, size, msg = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:59:        assert status == "REJECTED"
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:84:        status, size, msg = engine.pre_trade_check("ETH", 30_000, 0.15, "NORMAL")
    ```

### INFERRED #calls-50
- **Source:** `AsurDev/acos/cli/monitor.py:LL119 :: asurdev_acos_cli_monitor_py_cli_monitor_main`
- **Target:** `AsurDev/acos/cli/monitor.py:L46 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_status`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_kepler.py:234:        assert "status" in v
    ```
    ```
    /home/workspace/tests/test_kepler.py:238:        for key in ["kepler_lon", "swiss_lon", "delta_lon", "status", "message"]:
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:58:        status, size, msg = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    ```

### INFERRED #calls-51
- **Source:** `AsurDev/acos/cli/monitor.py:LL122 :: asurdev_acos_cli_monitor_py_cli_monitor_main`
- **Target:** `AsurDev/acos/cli/monitor.py:L78 :: asurdev_acos_cli_monitor_py_cli_monitor_cmd_switch`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:4:  1. Drawdown kill switch triggers at threshold
    ```
    ```
    /home/workspace/tests/test_risk_integration.py:64:        """Kill switch active → ModeEnforcer/RiskEngine still check (REJECTED or APPROVED)."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:46:    switch = topo.switch_nodes[0]
    ```

### INFERRED #calls-52
- **Source:** `AsurDev/acos/events/event.py:LL42 :: asurdev_acos_events_event_py_events_event_event_post_init`
- **Target:** `AsurDev/acos/events/event.py:L44 :: asurdev_acos_events_event_py_events_event_event_compute_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:223:        # ── Step 6: Build state hash for record ──────────────────────────────
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:452:        """Compute reproducible state hash."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```

### INFERRED #calls-53
- **Source:** `AsurDev/acos/events/event_log.py:LL26 :: asurdev_acos_events_event_log_py_events_event_log_eventlog_emit`
- **Target:** `AsurDev/acos/events/event_log.py:L13 :: asurdev_acos_events_event_log_py_events_event_log_eventlog_append`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:43:        history.append(
    ```
    ```
    /home/workspace/tests/test_validator.py:436:    r2.errors.append(
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:173:            results.append((test.__name__, success))
    ```

### INFERRED #calls-54
- **Source:** `AsurDev/acos/events/event_log.py:LL41 :: asurdev_acos_events_event_log_py_events_event_log_eventlog_verify_chain`
- **Target:** `AsurDev/acos/events/event_log.py:L28 :: asurdev_acos_events_event_log_py_events_event_log_eventlog_get_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:57:    mgr1 = AmneziaWGManager(log1, trace_id="deterministic-trace")
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:58:    mgr2 = AmneziaWGManager(log2, trace_id="deterministic-trace")
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:136:    mgr1 = AmneziaWGManager(log, trace_id="explicit-trace")
    ```

### INFERRED #calls-55
- **Source:** `AsurDev/acos/network/amnezia_patch.py:LL89 :: asurdev_acos_network_amnezia_patch_py_network_amnezia_patch_patch_engine_pre_execute`
- **Target:** `AsurDev/acos/network/amnezia_patch.py:L19 :: asurdev_acos_network_amnezia_patch_py_network_amnezia_patch_validate_network_requirements`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_docker_security.py:2:"""Validate docker-compose.yml for P0 security requirements."""
    ```
    ```
    /home/workspace/meta_rl/security.py:3:Security requirements:
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/scripts/validate_docker_security.py:2:"""Validate docker-compose.yml for P0 security requirements."""
    ```

### INFERRED #calls-56
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL80 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_emit`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L17 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_tunnelevent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:32:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:54:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:55:        log.emit("t", EventType.DAG_INVALID, {})
    ```

### INFERRED #calls-57
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL88 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_start`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L46 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_available_binaries`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_wg.py:70:        binaries = ["awg-quick", "wg-quick"]
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_wg.py:74:                binaries.append(b)
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_wg.py:77:        return binaries
    ```

### INFERRED #calls-58
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL89 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_start`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L56 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_run_wg_quick`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-59
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL89 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_start`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L64 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_run_wg_setconf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:222:    agents = dict(AGENTS)  # start with static definitions
    ```
    ```
    /home/workspace/agents/_impl/time_window_agent.py:140:        # Check if we're at start of 4H candle (higher volume expected)
    ```
    ```
    /home/workspace/agents/_impl/time_window_agent.py:148:            summary = "4H candle start + uptrend"
    ```

### INFERRED #calls-60
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL131 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_reconnect_with_backoff`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L77 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_emit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:113:    log.emit("eventlog-test", "TUNNEL_UP", {"interface": "wg0", "peer": "10.8.0.1"})
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:196:            if isinstance(func, ast.Attribute) and func.attr in ("emit", "append"):
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:207:    log.emit("inv4", EventType.DAG_CREATED, {})
    ```

### INFERRED #calls-61
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL90 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_start`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L77 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_emit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:113:    log.emit("eventlog-test", "TUNNEL_UP", {"interface": "wg0", "peer": "10.8.0.1"})
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:196:            if isinstance(func, ast.Attribute) and func.attr in ("emit", "append"):
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:207:    log.emit("inv4", EventType.DAG_CREATED, {})
    ```

### INFERRED #calls-62
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL101 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_stop`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L77 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_emit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:32:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:54:        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:55:        log.emit("t", EventType.DAG_INVALID, {})
    ```

### INFERRED #calls-63
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL133 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_reconnect_with_backoff`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L85 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_start`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/time_window_agent.py:140:        # Check if we're at start of 4H candle (higher volume expected)
    ```
    ```
    /home/workspace/agents/_impl/time_window_agent.py:148:            summary = "4H candle start + uptrend"
    ```
    ```
    /home/workspace/agents/_impl/time_window_agent.py:152:            summary = "4H candle start + downtrend"
    ```

### INFERRED #calls-64
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL138 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_ensure_up`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L106 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_status`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:58:        status, size, msg = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:59:        assert status == "REJECTED"
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:84:        status, size, msg = engine.pre_trade_check("ETH", 30_000, 0.15, "NORMAL")
    ```

### INFERRED #calls-65
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL145 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_health_check_loop`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L106 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_status`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:58:        status, size, msg = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:59:        assert status == "REJECTED"
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:84:        status, size, msg = engine.pre_trade_check("ETH", 30_000, 0.15, "NORMAL")
    ```

### INFERRED #calls-66
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL128 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_reconnect_with_backoff`
- **Target:** `AsurDev/acos/network/amnezia_wg.py:L122 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_deterministic_delay`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:54:    """INV-AWG2: reconnect delay is deterministic (seed = trace_id hash)."""
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_wg.py:151:    # CRITICAL-8: deterministic delay - same on every replay
    ```
    ```
    /home/workspace/home-cluster-iac/acos/network/amnezia_wg.py:158:        delay = self._deterministic_delay(attempt)
    ```

### INFERRED #calls-67
- **Source:** `AsurDev/acos/network/amnezia_wg.py:LL140 :: asurdev_acos_network_amnezia_wg_py_network_amnezia_wg_amneziawgmanager_ensure_up`
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

### INFERRED #calls-68
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

### INFERRED #calls-69
- **Source:** `AsurDev/acos/projection/state.py:LL44 :: asurdev_acos_projection_state_py_projection_state_stateprojection_get_enriched_trace`
- **Target:** `AsurDev/acos/projection/state.py:L22 :: asurdev_acos_projection_state_py_projection_state_stateprojection_get_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:4:Guarantees deterministic replay of any decision trace.
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:31:        trace = self.store.get_trace(trace_id)
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:32:        if not trace:
    ```

### INFERRED #calls-70
- **Source:** `AsurDev/acos/state/reducer.py:LL47 :: asurdev_acos_state_reducer_py_state_reducer_statereducer_apply`
- **Target:** `AsurDev/acos/state/reducer.py:L18 :: asurdev_acos_state_reducer_py_state_reducer_payload_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:71:def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:160:    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")
    ```

### INFERRED #calls-71
- **Source:** `AsurDev/acos/state/reducer.py:LL35 :: asurdev_acos_state_reducer_py_state_reducer_statereducer_rebuild`
- **Target:** `AsurDev/acos/state/reducer.py:L27 :: asurdev_acos_state_reducer_py_state_reducer_statereducer_reduce`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/risk_control.py:49:      if position_lag < -RISK_POSITION_LAG_THRESHOLD  →  reduce (перегрев)
    ```
    ```
    /home/workspace/agents/_impl/amre/meta_questioning.py:175:                    "text": "EXTREME - reduce exposure",
    ```
    ```
    /home/workspace/meta_rl/walkforward.py:332:            recommendations.append("Strategy fails on OOS — increase regularization or reduce population complexity")
    ```

### INFERRED #calls-72
- **Source:** `AsurDev/acos/state/reducer.py:LL31 :: asurdev_acos_state_reducer_py_state_reducer_statereducer_reduce`
- **Target:** `AsurDev/acos/state/reducer.py:L45 :: asurdev_acos_state_reducer_py_state_reducer_statereducer_apply`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:220:    # Try to apply invalid change (should trigger rollback)
    ```
    ```
    /home/workspace/agents/_impl/amre/reward.py:182:        """Assess whether reward is spurious and apply penalty."""
    ```
    ```
    /home/workspace/agents/_impl/amre/self_question.py:178:                "WARNING: Questions have poor track record recently — apply extra skepticism",
    ```

### INFERRED #calls-73
- **Source:** `AsurDev/acos/storage/postgres_backend.py:LL46 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_fetch`
- **Target:** `AsurDev/acos/storage/postgres_backend.py:L24 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_get_conn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:29:        with sqlite3.connect(self.db) as conn:
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/mas_factory/visualizer.py:53:        for conn in self.topo.connections:
    ```

### INFERRED #calls-74
- **Source:** `AsurDev/acos/storage/postgres_backend.py:LL54 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_query`
- **Target:** `AsurDev/acos/storage/postgres_backend.py:L24 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_get_conn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:29:        with sqlite3.connect(self.db) as conn:
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/mas_factory/visualizer.py:53:        for conn in self.topo.connections:
    ```

### INFERRED #calls-75
- **Source:** `AsurDev/acos/storage/postgres_backend.py:LL69 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_update`
- **Target:** `AsurDev/acos/storage/postgres_backend.py:L24 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_get_conn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:29:        with sqlite3.connect(self.db) as conn:
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/mas_factory/visualizer.py:53:        for conn in self.topo.connections:
    ```

### INFERRED #calls-76
- **Source:** `AsurDev/acos/storage/postgres_backend.py:LL31 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_write`
- **Target:** `AsurDev/acos/storage/postgres_backend.py:L24 :: asurdev_acos_storage_postgres_backend_py_storage_postgres_backend_postgrestracestorage_get_conn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:29:        with sqlite3.connect(self.db) as conn:
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/mas_factory/visualizer.py:53:        for conn in self.topo.connections:
    ```

### INFERRED #calls-77
- **Source:** `AsurDev/acos/storage/schema.py:LL26 :: asurdev_acos_storage_schema_py_storage_schema_tracerecord_post_init`
- **Target:** `AsurDev/acos/storage/schema.py:L9 :: asurdev_acos_storage_schema_py_storage_schema_utcnow`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/data/market_adapter.py:216:        now = datetime.utcnow()
    ```
    ```
    /home/workspace/agents/_impl/bull_researcher.py:243:        now = datetime.utcnow()
    ```
    ```
    /home/workspace/agents/_impl/time_window_agent.py:137:        now = datetime.utcnow()
    ```

### INFERRED #calls-78
- **Source:** `AsurDev/acos/validator/contract_validator.py:LL90 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_dagvalidator_validate_dag`
- **Target:** `AsurDev/acos/validator/contract_validator.py:L13 :: asurdev_acos_validator_contract_validator_py_validator_contract_validator_eventtype`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:154:    dag = {"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": []}
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:155:    returned = engine.execute(dag, {}, "inv1")
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:217:    log.emit("inv5", EventType.DAG_CREATED, {"dag": {"nodes": [{"id": "n"}]}})
    ```

### INFERRED #calls-79
- **Source:** `AsurDev/acos_cli.py:LL192 :: asurdev_acos_cli_main`
- **Target:** `AsurDev/acos_cli.py:L39 :: asurdev_acos_cli_validate_all_contracts`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:64:    "acos-contracts/", "acos-core/", "sbs/",
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:16:from acos.contracts import (
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:76:    print("[OK] All contracts validated. System ready.")
    ```

### INFERRED #calls-80
- **Source:** `AsurDev/acos_cli.py:LL45 :: asurdev_acos_cli_validate_all_contracts`
- **Target:** `AsurDev/acos_cli.py:L155 :: asurdev_acos_cli_acoscli_get_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/acos.py:176:        trace = self.trace_store.create_trace(request.context.run_id if request.context else "default")
    ```
    ```
    /home/workspace/home-cluster-iac/acos.py:177:        trace_id = trace.trace_id
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:57:    mgr1 = AmneziaWGManager(log1, trace_id="deterministic-trace")
    ```

### INFERRED #calls-81
- **Source:** `AsurDev/acos_cli.py:LL193 :: asurdev_acos_cli_main`
- **Target:** `AsurDev/acos_cli.py:L71 :: asurdev_acos_cli_acoscli`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-82
- **Source:** `AsurDev/acos_cli.py:LL97 :: asurdev_acos_cli_acoscli_submit`
- **Target:** `AsurDev/acos_cli.py:L144 :: asurdev_acos_cli_acoscli_record`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/data_room/test_data_room.py:88:    m.record("resolver_a", latency=0.1, success=True, quality=0.95)
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:89:    m.record("resolver_a", latency=0.2, success=False, quality=0.0)
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:90:    m.record("resolver_b", latency=0.3, success=True, quality=0.8)
    ```

### INFERRED #calls-83
- **Source:** `AsurDev/acos_cli.py:LL210 :: asurdev_acos_cli_main`
- **Target:** `AsurDev/acos_cli.py:L80 :: asurdev_acos_cli_acoscli_submit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/scheduler_v3/api.py:4:POST /schedule     — admission check → stateful scoring → Slurm submit
    ```
    ```
    /home/workspace/home-cluster-iac/scheduler_v3/api.py:120:        # Step 4: Advance job to SCHEDULED (Slurm submit)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:134:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.timeout_ms)
    ```

### INFERRED #calls-84
- **Source:** `AsurDev/acos_cli.py:LL214 :: asurdev_acos_cli_main`
- **Target:** `AsurDev/acos_cli.py:L155 :: asurdev_acos_cli_acoscli_get_trace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:4:Guarantees deterministic replay of any decision trace.
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:31:        trace = self.store.get_trace(trace_id)
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:32:        if not trace:
    ```

### INFERRED #calls-85
- **Source:** `AsurDev/acos_cli.py:LL217 :: asurdev_acos_cli_main`
- **Target:** `AsurDev/acos_cli.py:L159 :: asurdev_acos_cli_acoscli_list_traces`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:98:        traces = self.store.get_traces_by_run(run_id)
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:100:        for trace in traces:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/engine/execution_engine.py:29:        self.traces = {}
    ```

### INFERRED #calls-86
- **Source:** `AsurDev/acos_cli.py:LL199 :: asurdev_acos_cli_main`
- **Target:** `AsurDev/acos_cli.py:L162 :: asurdev_acos_cli_acoscli_invariants`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/_sbs_old/adapters.py:96:            True if all invariants passed.
    ```
    ```
    /home/workspace/_sbs_old/adapters.py:98:            List of violated invariants (empty if ok=True).
    ```
    ```
    /home/workspace/_sbs_old/system_contract.py:4:These invariants CANNOT be bypassed by any runtime layer.
    ```

### INFERRED #calls-87
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL274 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_main`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L45 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-88
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL227 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_run_full_correction_cycle`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L54 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_run_scenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:82:        1. REQUEST   — load scenario + system state
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/workload/generator.py:135:            raise ValueError(f"Unknown scenario: {scenario_name}")
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/workload/generator.py:136:        scenario = SCENARIOS[scenario_name]
    ```

### INFERRED #calls-89
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL97 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_analyze`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L172 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_build_fix`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/mas_factory/engine.py:3:from mas_factory.registry import get_agent_runner  # F821 fix
    ```
    ```
    /home/workspace/mas_factory/engine.py:145:        errors = 0  # F821 fix
    ```
    ```
    /home/workspace/meta_rl/trading_bridge.py:2:META_RL_TRADING_ENABLED = False  # F821 fix (TODO: move to config)
    ```

### INFERRED #calls-90
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL100 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_analyze`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L212 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_impact`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/idea_buffer_integration.py:154:    3. Return impact result
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:174:        Searches for recent geopolitical events and scores their impact.
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-91
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL94 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_analyze`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L139 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_root_cause`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:91:        # Determine root cause
    ```
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:168:        return causes.get(scenario, f"Unknown cause: {cause_type.value}")
    ```
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:253:        print(f"[RCA] Root cause: {rca.root_cause}")
    ```

### INFERRED #calls-92
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL233 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_run_full_correction_cycle`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L69 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_analyze`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_metrics_cli.py:42:            "analyze",
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:123:        async def analyze(self, state):
    ```

### INFERRED #calls-93
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL290 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_main`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L224 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_run_full_correction_cycle`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_exporter.py:127:        "description": "Market cycle analysis: 20/40/80 day cycles, phase detection, turn points",
    ```
    ```
    /home/workspace/agents/_impl/bull_researcher.py:255:        # Moon waxing (first half of cycle)
    ```
    ```
    /home/workspace/agents/_impl/bradley_agent.py:187:        # Check Jupiter-Saturn aspect (major cycle)
    ```

### INFERRED #calls-94
- **Source:** `AsurDev/acos_correction/rca_engine.py:LL292 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_main`
- **Target:** `AsurDev/acos_correction/rca_engine.py:L242 :: asurdev_acos_correction_rca_engine_py_acos_correction_rca_engine_rcaengine_generate_report`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:339:        report = engine.convergence_report()
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:340:        assert "status" in report
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:341:        assert "total_generations" in report
    ```

### INFERRED #calls-95
- **Source:** `AsurDev/admission_controller/controller.py:LL105 :: asurdev_admission_controller_controller_py_admission_controller_controller_admissioncontroller_admit`
- **Target:** `AsurDev/admission_controller/controller.py:L115 :: asurdev_admission_controller_controller_py_admission_controller_controller_admissioncontroller_check_memory`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:5:Implements the policy from docs/adr/ADR-0004-hybrid-memory-policy.md:
    ```
    ```
    /home/workspace/tests/test_cache.py:12:    """Создаём экземпляр кэша (in‑memory, Redis не нужен)."""
    ```
    ```
    /home/workspace/agents/_impl/amre/idea_buffer_integration.py:106:    """Clear the in-memory buffer (for testing/reset)."""
    ```

### INFERRED #calls-96
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL111 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller_update`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L17 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_rollingwindow`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/agent_test_base.py:18:    - When the contract changes, ONE place to update.
    ```
    ```
    /home/workspace/tests/agent_test_base.py:92:        state.update(self.happy_state_overrides)
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:7:  DecisionRecord → OAP update → Backtest sample → Sync audit
    ```

### INFERRED #calls-97
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL90 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller_p_overload`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L92 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller_normal_cdf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/ab_testing.py:46:        p_value = 2.0 * (1.0 - t_dist.cdf(abs(t_stat), df))
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/meta_rl/ab_testing.py:45:        p_value = 2.0 * (1.0 - t_dist.cdf(abs(t_stat), df))
    ```
    ```
    /home/workspace/audit_repo/meta_rl/ab_testing.py:45:        p_value = 2.0 * (1.0 - t_dist.cdf(abs(t_stat), df))
    ```

### INFERRED #calls-98
- **Source:** `AsurDev/admission_controller/probabilistic.py:LL104 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller_should_reject`
- **Target:** `AsurDev/admission_controller/probabilistic.py:L70 :: asurdev_admission_controller_probabilistic_py_admission_controller_probabilistic_probabilisticadmissioncontroller_p_overload`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/constraint_graph/graph.py:145:            violations.append("memory:overload")
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:3:Probabilistic Admission Controller — predicts overload before it happens.
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:4:Replaces static threshold (GPU>85%) with P(overload in next M minutes).
    ```

### INFERRED #calls-99
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL70 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ceph_osd_latency`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-100
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL75 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ceph_osd_replication_latency`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-101
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL85 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ceph_storage_total`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-102
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL80 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ceph_storage_used`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:180:            query = " ".join(headlines[:3]) + " " + query
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:187:            results = await rag.search(query, top_k=3)
    ```

### INFERRED #calls-103
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL44 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_cpu_util`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-104
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL59 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_disk_io_time`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-105
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL34 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_gpu_mem_util`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-106
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL39 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_gpu_temp`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-107
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL29 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_gpu_util`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-108
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL50 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_mem_util`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-109
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL64 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_network_latency`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-110
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL103 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_ray_active_workers`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-111
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL96 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_slurm_node_state`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-112
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL90 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_slurm_queue_depth`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-113
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL109 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_wg_peer_handshake_age`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/tests/test_observability_ollama.py:21:        vec = _embed("test query")
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```

### INFERRED #calls-114
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL114 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_wg_peer_rx_bytes`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:180:            query = " ".join(headlines[:3]) + " " + query
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:187:            results = await rag.search(query, top_k=3)
    ```

### INFERRED #calls-115
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL119 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_wg_peer_tx_bytes`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L14 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_query`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_rag_quality.py:78:            results = retriever.retrieve("test query", domain="astrology", top_k=2)
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:178:        query = "geopolitical risk financial markets impact"
    ```
    ```
    /home/workspace/agents/_impl/macro_agent.py:180:            query = " ".join(headlines[:3]) + " " + query
    ```

### INFERRED #calls-116
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL125 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L27 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_gpu_util`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:158:            # Resource decay: GPU util reverts toward baseline (0.3) at rate 0.05/step
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:65:        # windows["rtx-node"]: RollingWindow for GPU util
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:66:        # windows["rk3576"]: RollingWindow for CPU util
    ```

### INFERRED #calls-117
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL126 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L32 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_gpu_mem_util`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:158:            # Resource decay: GPU util reverts toward baseline (0.3) at rate 0.05/step
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:65:        # windows["rtx-node"]: RollingWindow for GPU util
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:66:        # windows["rk3576"]: RollingWindow for CPU util
    ```

### INFERRED #calls-118
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL127 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L37 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_gpu_temp`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_cache.py:31:    await cache.set("temp", 123)
    ```
    ```
    /home/workspace/tests/test_cache.py:32:    await cache.delete("temp")
    ```
    ```
    /home/workspace/tests/test_cache.py:33:    assert await cache.get("temp") is None
    ```

### INFERRED #calls-119
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL128 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L42 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_cpu_util`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:158:            # Resource decay: GPU util reverts toward baseline (0.3) at rate 0.05/step
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:65:        # windows["rtx-node"]: RollingWindow for GPU util
    ```
    ```
    /home/workspace/home-cluster-iac/admission_controller/probabilistic.py:66:        # windows["rk3576"]: RollingWindow for CPU util
    ```

### INFERRED #calls-120
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL129 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L48 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_mem_util`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:9:import importlib.util
    ```
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:63:        spec = importlib.util.spec_from_file_location("test_module", module_path)
    ```
    ```
    /home/workspace/home-cluster-iac/acos_correction/rca_engine.py:64:        module = importlib.util.module_from_spec(spec)
    ```

### INFERRED #calls-121
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL130 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L57 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_disk_io_time`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:58:# stable across decay, while decay varies with time.
    ```
    ```
    /home/workspace/agents/metrics.py:41:        with LATENCY.time():
    ```
    ```
    /home/workspace/agents/metrics.py:143:        with latency.labels(agent=agent_label).time():
    ```

### INFERRED #calls-122
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL131 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L62 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_network_latency`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:176:    # ─── 7. hot latency budget ────────────────────────────────────
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:88:    m.record("resolver_a", latency=0.1, success=True, quality=0.95)
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:89:    m.record("resolver_a", latency=0.2, success=False, quality=0.0)
    ```

### INFERRED #calls-123
- **Source:** `AsurDev/ai_scheduler/modules/metrics.py:LL132 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics`
- **Target:** `AsurDev/ai_scheduler/modules/metrics.py:L88 :: asurdev_ai_scheduler_modules_metrics_py_modules_metrics_slurm_queue_depth`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:251:                "depth": 0,
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_optimizer.py:5:"""Optimizations for KARL loop: parallel processing, TTC depth, reduced overhead."""
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_optimizer.py:113:        """Dynamically adjust TTC (Time To Commit) depth based on conditions."""
    ```

### INFERRED #calls-124
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

### INFERRED #calls-125
- **Source:** `AsurDev/ai_scheduler/modules/policy.py:LL41 :: asurdev_ai_scheduler_modules_policy_py_modules_policy_select_node`
- **Target:** `AsurDev/ai_scheduler/modules/policy.py:L69 :: asurdev_ai_scheduler_modules_policy_py_modules_policy_build_reason`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:288:                f"author={ov.get('author')} reason={ov.get('reason', '')[:60]}",
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:133:        assert "SLIPPAGE" in result.reason
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:167:        assert "SPREAD" in result.reason
    ```

### INFERRED #calls-126
- **Source:** `AsurDev/ai_scheduler/modules/policy.py:LL40 :: asurdev_ai_scheduler_modules_policy_py_modules_policy_select_node`
- **Target:** `AsurDev/ai_scheduler/modules/policy.py:L57 :: asurdev_ai_scheduler_modules_policy_py_modules_policy_node_to_partition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:224:        path_line, _, node_id = s.partition("::")
    ```
    ```
    /home/workspace/home-cluster-iac/v6/constraint_engine/engine.py:38:    partition: str
    ```
    ```
    /home/workspace/home-cluster-iac/v6/constraint_engine/engine.py:101:        if placement.partition not in self._node_partitions.get(nid, []):
    ```

### INFERRED #calls-127
- **Source:** `AsurDev/ai_scheduler/modules/scoring.py:LL64 :: asurdev_ai_scheduler_modules_scoring_py_modules_scoring_rank_nodes`
- **Target:** `AsurDev/ai_scheduler/modules/scoring.py:L19 :: asurdev_ai_scheduler_modules_scoring_py_modules_scoring_score_node`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:75:    src_label = edge["source"].rsplit("_", 1)[-1]   # last segment of node id
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:90:    # 3. target node has no source_file at all (parser bug — same family as KI-014)
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:12:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```

### INFERRED #calls-128
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL188 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_route_job`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L45 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_nodemetrics_compute_score`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_sentiment_agent_async.py:26:        assert result["score"] == 0.25
    ```
    ```
    /home/workspace/agents/_impl/sentiment_agent.py:45:        sentiment_score = fear_greed["score"] * 0.40 + funding_rate["score"] * 0.30 + price_momentum["score"] * 0.30
    ```
    ```
    /home/workspace/agents/_impl/sentiment_agent.py:61:            f"Sentiment score: {sentiment_score:.2f}"
    ```

### INFERRED #calls-129
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL274 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_cli_route`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L68 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_jobrequest`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:17:    @app.route("/protected")
    ```
    ```
    /home/workspace/tests/test_auth_empty_key.py:12:    @app.route("/test")
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:11:    R4.  Any HTTP route handler under web/ must use @require_auth (or be
    ```

### INFERRED #calls-130
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL112 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_node_metrics_prometheus`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L90 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_prometheus_metric`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/metrics.py:46:Both patterns produce the same metric names, so dashboards see one
    ```
    ```
    /home/workspace/agents/metrics.py:47:metric per agent regardless of which pattern the author picked.
    ```
    ```
    /home/workspace/agents/metrics.py:66:# same object — prometheus_client raises on duplicate metric registration.
    ```

### INFERRED #calls-131
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL242 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_list_nodes`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L108 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_node_metrics_prometheus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:39:    # Simple regex: match words that follow prometheus metric naming conventions
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py:268:    return {"status": "ok", "prometheus": prom_status}
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/modules/metrics.py:64:    """Network latency estimate via prometheus blackbox or node_network_*"""
    ```

### INFERRED #calls-132
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL172 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_route_job`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L108 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_node_metrics_prometheus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:39:    # Simple regex: match words that follow prometheus metric naming conventions
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py:268:    return {"status": "ok", "prometheus": prom_status}
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/modules/metrics.py:64:    """Network latency estimate via prometheus blackbox or node_network_*"""
    ```

### INFERRED #calls-133
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL174 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_route_job`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L133 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_get_node_metrics_fallback`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_cache.py:13:    c = RedisCache(use_redis=False)  # fallback‑режим для тестов
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:38:    """Test that MASFactory failure triggers graceful fallback."""
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:39:    print("\n[TEST 2] MASFactory fallback on error...")
    ```

### INFERRED #calls-134
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL279 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_cli_route`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L162 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_route_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ml_engine/dataset/labels.py:47:    Label from job outcome stored in job_events table.
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/retrainer.py:56:        """Call after each job completes — tracks toward retrain threshold."""
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/collector.py:3:Feedback Collector — ingests job outcomes from state_store into TimescaleDB.
    ```

### INFERRED #calls-135
- **Source:** `AsurDev/ai_scheduler/scheduler.py:LL233 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_schedule_job`
- **Target:** `AsurDev/ai_scheduler/scheduler.py:L162 :: asurdev_ai_scheduler_scheduler_py_ai_scheduler_scheduler_route_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:1:"""State-store and job-state protocols.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:27:    """Common job lifecycle shared across schedulers.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:45:    """Common job-state DTO.
    ```

### INFERRED #calls-136
- **Source:** `AsurDev/ai_scheduler/scheduler_v2.py:LL91 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_submit`
- **Target:** `AsurDev/ai_scheduler/scheduler_v2.py:L20 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_schedulerequest`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:134:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.timeout_ms)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:170:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.horizon_minutes)
    ```
    ```
    /home/workspace/home-cluster-iac/tests/unit/test_determinism.py:82:    """Test 3: Deduplication — scheduler must not double-submit."""
    ```

### INFERRED #calls-137
- **Source:** `AsurDev/ai_scheduler/scheduler_v2.py:LL60 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_schedule`
- **Target:** `AsurDev/ai_scheduler/scheduler_v2.py:L31 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_scheduleresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:125:                scheduled = self.scheduler.schedule(dag, {})
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:178:            s1 = self.scheduler.schedule(dag, {})
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:179:            s2 = self.scheduler.schedule(dag, {})
    ```

### INFERRED #calls-138
- **Source:** `AsurDev/ai_scheduler/scheduler_v2.py:LL91 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_submit`
- **Target:** `AsurDev/ai_scheduler/scheduler_v2.py:L45 :: asurdev_ai_scheduler_scheduler_v2_py_ai_scheduler_scheduler_v2_schedule`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:36:    def schedule(self, dag: dict, context: dict) -> dict:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:37:        """Compile DAG into executable schedule. Contract-required method."""
    ```
    ```
    /home/workspace/home-cluster-iac/scheduler_v3/api.py:4:POST /schedule     — admission check → stateful scoring → Slurm submit
    ```

### INFERRED #calls-139
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL158 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_agent_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L31 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/acos.py:76:  └── Policy compiler (policy → executable constraint graph)
    ```
    ```
    /home/workspace/home-cluster-iac/acos.py:90:  ├── Policy parser (text → constraint DAG)
    ```

### INFERRED #calls-140
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL172 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_latency_sla`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L31 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:52:            raise ValueError(f"Invalid constraint expr: {expr}")
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:108:    def register(self, constraint: CompiledConstraint) -> None:
    ```

### INFERRED #calls-141
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL123 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_risk_profile`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L31 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/v8/safety_kernel/engine.py:86:        # STEP 1: constraint validation
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:52:            raise ValueError(f"Invalid constraint expr: {expr}")
    ```

### INFERRED #calls-142
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL159 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_agent_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L41 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint_make_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/job_engine/engine.py:47:    id: str
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:65:        logger.info(f"[{job.id}] {old.value} → {new.value} (node={job.node_id})")
    ```
    ```
    /home/workspace/AsurDev/job_engine/engine.py:68:        logger.error(f"[{job.id}] FAILURE: {reason}")
    ```

### INFERRED #calls-143
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL173 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_latency_sla`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L41 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint_make_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/db/migrate_from_sqlite.py:69:                    "decision_id": session.get("session_id", session.get("id")),
    ```
    ```
    /home/workspace/push/db/migrate_from_sqlite.py:70:                    "session_id": session.get("session_id", session.get("id")),
    ```
    ```
    /home/workspace/push/db/models.py:117:    id = Column(Integer, primary_key=True, autoincrement=True)
    ```

### INFERRED #calls-144
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL124 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_risk_profile`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L41 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint_make_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:42:    nodes = {n["id"]: n for n in g["nodes"]}
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:75:    src_label = edge["source"].rsplit("_", 1)[-1]   # last segment of node id
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:263:                    node_age_days[n["id"]] = (as_of - dt).days
    ```

### INFERRED #calls-145
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL225 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_validate_trace`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L44 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint_evaluate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/compromise_agent.py:46:# trigger, SynthesisAgent should re-evaluate.
    ```
    ```
    /home/workspace/agents/_impl/amre/meta_questioning.py:182:    def evaluate(self, answers: list[dict]) -> bool:
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:108:        result = dummy_evaluator.evaluate(strategy, sample_market_data)
    ```

### INFERRED #calls-146
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL88 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_policyblock_to_executable`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L61 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_constraint_to_guard`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/_template_agent_test.py:189:    """The dataclass itself must guard its invariants."""
    ```
    ```
    /home/workspace/agents/_impl/risk_agent.py:124:        except Exception as e:  # noqa: BLE001 — last-resort guard
    ```
    ```
    /home/workspace/agents/_impl/compromise_agent.py:179:        # (mirrors SynthesisAgent's V-07 guard).
    ```

### INFERRED #calls-147
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL105 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_add_constraint`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L74 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_policyblock`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/constraint_compiler/parser/parser.py:4:Transforms policy text into executable constraint DAG.
    ```
    ```
    /home/workspace/home-cluster-iac/constraint_compiler/parser/parser.py:150:                    constraint = Constraint(
    ```

### INFERRED #calls-148
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL194 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_compile`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L87 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_policyblock_to_executable`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:171:    proc = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True)
    ```
    ```
    /home/workspace/tests/test_healthcheck.py:19:        [sys.executable, str(HEALTHCHECK)] + list(args),
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:31:        [sys.executable, str(LINTER), "agents/_impl/_template_agent.py"],
    ```

### INFERRED #calls-149
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL166 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_agent_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L103 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_add_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:52:            raise ValueError(f"Invalid constraint expr: {expr}")
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:108:    def register(self, constraint: CompiledConstraint) -> None:
    ```

### INFERRED #calls-150
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL180 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_latency_sla`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L103 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_add_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/v6/constraint_graph/graph.py:4:Cluster represented as directed constraint graph:
    ```
    ```
    /home/workspace/home-cluster-iac/v6/constraint_graph/graph.py:39:    """Vertex in constraint graph."""
    ```

### INFERRED #calls-151
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL150 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_risk_profile`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L103 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_add_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:52:            raise ValueError(f"Invalid constraint expr: {expr}")
    ```
    ```
    /home/workspace/home-cluster-iac/v8/constraint_compiler/compiler.py:108:    def register(self, constraint: CompiledConstraint) -> None:
    ```

### INFERRED #calls-152
- **Source:** `AsurDev/astrofin/constraint_compiler.py:LL241 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_build_astrofin_policy`
- **Target:** `AsurDev/astrofin/constraint_compiler.py:L112 :: asurdev_astrofin_constraint_compiler_py_astrofin_constraint_compiler_astrofinconstraintcompiler_build_risk_profile`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/technical_agent.py:196:        # Volume profile
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_optimizer.py:17:    """Performance profile for KARL operations."""
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_optimizer.py:146:    def record_perf(self, profile: KARLPerfProfile):
    ```

### INFERRED #calls-153
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

### INFERRED #calls-154
- **Source:** `AsurDev/astrofin/gateway/submission.py:LL107 :: asurdev_astrofin_gateway_submission_py_gateway_submission_main`
- **Target:** `AsurDev/astrofin/gateway/submission.py:L20 :: asurdev_astrofin_gateway_submission_py_gateway_submission_acossubmissiongateway`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-155
- **Source:** `AsurDev/astrofin/gateway/submission.py:LL112 :: asurdev_astrofin_gateway_submission_py_gateway_submission_main`
- **Target:** `AsurDev/astrofin/gateway/submission.py:L30 :: asurdev_astrofin_gateway_submission_py_gateway_submission_acossubmissiongateway_submit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:134:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.timeout_ms)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:170:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.horizon_minutes)
    ```
    ```
    /home/workspace/home-cluster-iac/tests/unit/test_determinism.py:82:    """Test 3: Deduplication — scheduler must not double-submit."""
    ```

### INFERRED #calls-156
- **Source:** `AsurDev/astrofin/gateway/submission.py:LL135 :: asurdev_astrofin_gateway_submission_py_gateway_submission_main`
- **Target:** `AsurDev/astrofin/gateway/submission.py:L102 :: asurdev_astrofin_gateway_submission_py_gateway_submission_acossubmissiongateway_get_traces`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:98:        traces = self.store.get_traces_by_run(run_id)
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:100:        for trace in traces:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/engine/execution_engine.py:29:        self.traces = {}
    ```

### INFERRED #calls-157
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL96 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_init_population`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L16 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:107:        strategy = GeneratedStrategy(random_chromosome())
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:108:        result = dummy_evaluator.evaluate(strategy, sample_market_data)
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:113:        strategy = GeneratedStrategy(random_chromosome())
    ```

### INFERRED #calls-158
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL55 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_crossover`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L16 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:107:        strategy = GeneratedStrategy(random_chromosome())
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:108:        result = dummy_evaluator.evaluate(strategy, sample_market_data)
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:113:        strategy = GeneratedStrategy(random_chromosome())
    ```

### INFERRED #calls-159
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL38 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_mutate`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L16 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:107:        strategy = GeneratedStrategy(random_chromosome())
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:108:        result = dummy_evaluator.evaluate(strategy, sample_market_data)
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:113:        strategy = GeneratedStrategy(random_chromosome())
    ```

### INFERRED #calls-160
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL97 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_init_population`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L26 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_make_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:42:    nodes = {n["id"]: n for n in g["nodes"]}
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:75:    src_label = edge["source"].rsplit("_", 1)[-1]   # last segment of node id
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:263:                    node_age_days[n["id"]] = (as_of - dt).days
    ```

### INFERRED #calls-161
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL56 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_crossover`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L26 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_make_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:42:    nodes = {n["id"]: n for n in g["nodes"]}
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:75:    src_label = edge["source"].rsplit("_", 1)[-1]   # last segment of node id
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:263:                    node_age_days[n["id"]] = (as_of - dt).days
    ```

### INFERRED #calls-162
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL39 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_mutate`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L26 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_make_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:259:        assert "id" in exported[0]
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:118:        id = "always_fails"
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:124:        id = "always_succeeds"
    ```

### INFERRED #calls-163
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL132 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_reproduce`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L30 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_mutate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/meta_agent.py:203:        from strategies.generator import GeneratedStrategy, crossover, mutate
    ```
    ```
    /home/workspace/meta_rl/meta_agent.py:216:                chrom = mutate(chrom, rate=self.config.mutation_rate)
    ```
    ```
    /home/workspace/meta_rl/meta_agent.py:233:                chrom = mutate(dict(p.strategy.chromosome), rate=self.config.mutation_rate * 2)
    ```

### INFERRED #calls-164
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL132 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_reproduce`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L45 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_strategy_crossover`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:49:                "reasoning": "RSI oversold, MACD bullish crossover",
    ```
    ```
    /home/workspace/agents/_impl/ml_predictor_agent.py:128:        Simple ML-like prediction using momentum and moving average crossover.
    ```
    ```
    /home/workspace/agents/_impl/ml_predictor_agent.py:141:        # Signals from MA crossover
    ```

### INFERRED #calls-165
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL146 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_evolve`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L103 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_evaluate_population`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:7:1. Create a MetaAgent with a small population.
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:71:    """MetaAgent wired with a tiny population and slow features disabled."""
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:128:    # The pool should never shrink below the configured population.
    ```

### INFERRED #calls-166
- **Source:** `AsurDev/astrofin/meta_rl/engine.py:LL147 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_evolve`
- **Target:** `AsurDev/astrofin/meta_rl/engine.py:L114 :: asurdev_astrofin_meta_rl_engine_py_meta_rl_engine_metarlengine_select`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:140:    """При use_real_agents=True и use_thompson=True вызывается ThompsonSampler.select."""
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:142:    with patch("core.thompson.ThompsonSampler.select") as mock_select:
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:157:            assert mock_select.called, "ThompsonSampler.select was not called"
    ```

### INFERRED #calls-167
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

### INFERRED #calls-168
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL144 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_parse_text`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L20 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_constraint`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_registry.py:38:        return 0  # nothing under _impl/ changed; no constraint applies
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer.py:96:        sum(job for node in nodes) <= cap [capacity constraint]
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/ilp/or_ilp.py:27:    Uses scipy minimize with penalty method for constraint handling.
    ```

### INFERRED #calls-169
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL124 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_parse_text`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L69 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_constraintgroup`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:131:            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=5,
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:155:            stderr=subprocess.DEVNULL, text=True
    ```

### INFERRED #calls-170
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL78 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_constraintgroup_evaluate_all`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L90 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyblock_evaluate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/compromise_agent.py:46:# trigger, SynthesisAgent should re-evaluate.
    ```
    ```
    /home/workspace/agents/_impl/amre/meta_questioning.py:182:    def evaluate(self, answers: list[dict]) -> bool:
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:108:        result = dummy_evaluator.evaluate(strategy, sample_market_data)
    ```

### INFERRED #calls-171
- **Source:** `AsurDev/constraint_compiler/parser/parser.py:LL149 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_parse_text`
- **Target:** `AsurDev/constraint_compiler/parser/parser.py:L162 :: asurdev_constraint_compiler_parser_parser_py_parser_parser_policyparser_parse_value`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_integration.py:76:        assert result.status.value in ("REJECTED", "APPROVED"), f"Expected kill_switch check, got {result.status}"
    ```
    ```
    /home/workspace/tests/test_risk_integration.py:100:        assert result.status.value == "APPROVED", f"Expected APPROVED, got {result.status}: {result.reason}"
    ```
    ```
    /home/workspace/tests/test_risk_integration.py:145:        assert result.status.value == "APPROVED", f"Expected APPROVED, got {result.status}: {result.reason}"
    ```

### INFERRED #calls-172
- **Source:** `AsurDev/dag_validator/validator.py:LL60 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L20 :: asurdev_dag_validator_validator_py_dag_validator_validator_violation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-173
- **Source:** `AsurDev/dag_validator/validator.py:LL53 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L37 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_get_node_id`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:42:    nodes = {n["id"]: n for n in g["nodes"]}
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:75:    src_label = edge["source"].rsplit("_", 1)[-1]   # last segment of node id
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:263:                    node_age_days[n["id"]] = (as_of - dt).days
    ```

### INFERRED #calls-174
- **Source:** `AsurDev/dag_validator/validator.py:LL81 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_compute_dag_hash`
- **Target:** `AsurDev/dag_validator/validator.py:L40 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_serialize`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrofin-sentinel-v5/knowledge/daily_brief/idea_tracker_refactored.py:32:# Decision record: serialize Idea via asdict() only
    ```
    ```
    /home/workspace/knowledge/daily_brief/idea_tracker_refactored.py:33:# Decision record: serialize Idea via asdict() only
    ```
    ```
    /home/workspace/atom-federation-os/alignment/failure_replay.py:161:    def serialize(self) -> dict:
    ```

### INFERRED #calls-175
- **Source:** `AsurDev/dag_validator/validator.py:LL61 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L106 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_check_dependency_closure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/dag_validator/validator.py:4:I1: acyclicity, I2: dependency closure, I3: deterministic ordering, I4: side-effect isolation
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gsct.py:44:    """Evidence for a single step in the closure proof."""
    ```
    ```
    /home/workspace/atom-federation-os/alignment/gsct.py:308:        # F4: Undefined attractor (false closure illusion)
    ```

### INFERRED #calls-176
- **Source:** `AsurDev/dag_validator/validator.py:LL62 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L114 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_check_deterministic_order`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:130:        order = OrderRequest("BTC", "BUY", 0.5, 50_000, "MARKET", slippage_bp_estimate=75.0)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:131:        result = checker.validate(order, market)
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:138:        order = OrderRequest("BTC", "BUY", 0.5, 50_000, "MARKET", slippage_bp_estimate=5.0)
    ```

### INFERRED #calls-177
- **Source:** `AsurDev/dag_validator/validator.py:LL63 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L131 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_check_side_effects`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:138:        # Apply action effects
    ```
    ```
    /home/workspace/home-cluster-iac/governance.py:144:        findings.append(f"{len(lt_se)} lt side effects")
    ```
    ```
    /home/workspace/atom-federation-os/core/deterministic.py:547:    No time, no randomness, no side effects.
    ```

### INFERRED #calls-178
- **Source:** `AsurDev/dag_validator/validator.py:LL55 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L80 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_compute_dag_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:244:    print(f"  Current topology hash: {updater.current_topology.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:245:    print(f"  Expected (after valid change): {new_topo.hash}")
    ```

### INFERRED #calls-179
- **Source:** `AsurDev/dag_validator/validator.py:LL58 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_validate`
- **Target:** `AsurDev/dag_validator/validator.py:L84 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_find_cycle`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/bull_researcher.py:255:        # Moon waxing (first half of cycle)
    ```
    ```
    /home/workspace/agents/_impl/bradley_agent.py:187:        # Check Jupiter-Saturn aspect (major cycle)
    ```
    ```
    /home/workspace/agents/_impl/cycle_agent.py:23:    1. Detect dominant cycle periods (20, 40, 80 days)
    ```

### INFERRED #calls-180
- **Source:** `AsurDev/dag_validator/validator.py:LL139 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_verify_hash`
- **Target:** `AsurDev/dag_validator/validator.py:L80 :: asurdev_dag_validator_validator_py_dag_validator_validator_dagvalidator_compute_dag_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:244:    print(f"  Current topology hash: {updater.current_topology.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:245:    print(f"  Expected (after valid change): {new_topo.hash}")
    ```

### INFERRED #calls-181
- **Source:** `AsurDev/determinism_controller/controller.py:LL48 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_get_determinism_report`
- **Target:** `AsurDev/determinism_controller/controller.py:L38 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_verify_replay`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/idea_buffer_integration.py:2:Встраивает Idea в KARL replay buffer lifecycle.
    ```
    ```
    /home/workspace/agents/_impl/amre/idea_buffer_integration.py:53:    Inject a scored Idea into the KARL replay buffer.
    ```
    ```
    /home/workspace/agents/_impl/amre/backtest_loop.py:115:    - Accumulating replay buffer
    ```

### INFERRED #calls-182
- **Source:** `AsurDev/determinism_controller/controller.py:LL63 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_checkpoint_state`
- **Target:** `AsurDev/determinism_controller/controller.py:L58 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_compute_state_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:223:        # ── Step 6: Build state hash for record ──────────────────────────────
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:452:        """Compute reproducible state hash."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```

### INFERRED #calls-183
- **Source:** `AsurDev/determinism_controller/controller.py:LL68 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_verify_checkpoint`
- **Target:** `AsurDev/determinism_controller/controller.py:L58 :: asurdev_determinism_controller_controller_py_determinism_controller_controller_determinismcontroller_compute_state_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:244:    print(f"  Current topology hash: {updater.current_topology.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:245:    print(f"  Expected (after valid change): {new_topo.hash}")
    ```

### INFERRED #calls-184
- **Source:** `AsurDev/ete/compiler/constraint_compiler.py:LL32 :: asurdev_ete_compiler_constraint_compiler_py_compiler_constraint_compiler_constraintcompiler_inject`
- **Target:** `AsurDev/ete/compiler/constraint_compiler.py:L57 :: asurdev_ete_compiler_constraint_compiler_py_compiler_constraint_compiler_constraintcompiler_make_post_guard`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/fundamental_agent.py:110:        except Exception as e:  # noqa: BLE001 — last-resort guard
    ```
    ```
    /home/workspace/agents/_impl/risk_agent.py:124:        except Exception as e:  # noqa: BLE001 — last-resort guard
    ```
    ```
    /home/workspace/agents/_impl/bull_researcher.py:120:        except Exception as e:  # noqa: BLE001 — last-resort guard
    ```

### INFERRED #calls-185
- **Source:** `AsurDev/ete/compiler/constraint_compiler.py:LL29 :: asurdev_ete_compiler_constraint_compiler_py_compiler_constraint_compiler_constraintcompiler_inject`
- **Target:** `AsurDev/ete/compiler/constraint_compiler.py:L41 :: asurdev_ete_compiler_constraint_compiler_py_compiler_constraint_compiler_constraintcompiler_make_pre_guard`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/_template_agent_test.py:189:    """The dataclass itself must guard its invariants."""
    ```
    ```
    /home/workspace/agents/_impl/risk_agent.py:124:        except Exception as e:  # noqa: BLE001 — last-resort guard
    ```
    ```
    /home/workspace/agents/_impl/compromise_agent.py:179:        # (mirrors SynthesisAgent's V-07 guard).
    ```

### INFERRED #calls-186
- **Source:** `AsurDev/ete/compiler/dag.py:LL80 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_agent_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L29 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/retrainer.py:56:        """Call after each job completes — tracks toward retrain threshold."""
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/collector.py:3:Feedback Collector — ingests job outcomes from state_store into TimescaleDB.
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/collector.py:56:        logger.info(f"Collected {len(rows)} job outcomes")
    ```

### INFERRED #calls-187
- **Source:** `AsurDev/ete/compiler/dag.py:LL94 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_batch_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L29 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:1:"""State-store and job-state protocols.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:27:    """Common job lifecycle shared across schedulers.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:45:    """Common job-state DTO.
    ```

### INFERRED #calls-188
- **Source:** `AsurDev/ete/compiler/dag.py:LL108 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_governance_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L29 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:1:"""State-store and job-state protocols.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:27:    """Common job lifecycle shared across schedulers.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:45:    """Common job-state DTO.
    ```

### INFERRED #calls-189
- **Source:** `AsurDev/ete/compiler/dag.py:LL103 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_risk_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L29 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:140:            job = JobState(
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:149:            state.jobs[job.job_id] = job
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:176:            for job in state.jobs.values():
    ```

### INFERRED #calls-190
- **Source:** `AsurDev/ete/compiler/dag.py:LL86 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_agent_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L42 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:71:def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:160:    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")
    ```

### INFERRED #calls-191
- **Source:** `AsurDev/ete/compiler/dag.py:LL95 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_batch_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L42 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:71:def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:160:    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")
    ```

### INFERRED #calls-192
- **Source:** `AsurDev/ete/compiler/dag.py:LL109 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_governance_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L42 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:71:def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:160:    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")
    ```

### INFERRED #calls-193
- **Source:** `AsurDev/ete/compiler/dag.py:LL104 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_risk_job`
- **Target:** `AsurDev/ete/compiler/dag.py:L42 :: asurdev_ete_compiler_dag_py_compiler_dag_dagnode_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:71:def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:160:    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")
    ```

### INFERRED #calls-194
- **Source:** `AsurDev/ete/compiler/dag.py:LL65 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile`
- **Target:** `AsurDev/ete/compiler/dag.py:L75 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_agent_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v8/safety_kernel/engine.py:160:        # Downgrade GPU job → CPU-only
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:140:            job = JobState(
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:149:            state.jobs[job.job_id] = job
    ```

### INFERRED #calls-195
- **Source:** `AsurDev/ete/compiler/dag.py:LL67 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile`
- **Target:** `AsurDev/ete/compiler/dag.py:L88 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_batch_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:88:    def submit(self, job: dict) -> dict:
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:93:            # 1. DAG compilation (MUST happen first — gate expects dag, not job)
    ```
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:95:                dag = self.dag_compiler.compile(job)
    ```

### INFERRED #calls-196
- **Source:** `AsurDev/ete/compiler/dag.py:LL71 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile`
- **Target:** `AsurDev/ete/compiler/dag.py:L106 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_governance_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v8/safety_kernel/engine.py:160:        # Downgrade GPU job → CPU-only
    ```
    ```
    /home/workspace/home-cluster-iac/state_store/client.py:4:Thread-safe connection pool + all queries for scheduler + job engine.
    ```
    ```
    /home/workspace/home-cluster-iac/state_store/client.py:197:        """Prevent duplicate Slurm submissions for same job."""
    ```

### INFERRED #calls-197
- **Source:** `AsurDev/ete/compiler/dag.py:LL69 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile`
- **Target:** `AsurDev/ete/compiler/dag.py:L101 :: asurdev_ete_compiler_dag_py_compiler_dag_dagcompiler_compile_risk_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:140:            job = JobState(
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:149:            state.jobs[job.job_id] = job
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:176:            for job in state.jobs.values():
    ```

### INFERRED #calls-198
- **Source:** `AsurDev/ete/engine/execution_engine.py:LL76 :: asurdev_ete_engine_execution_engine_py_engine_execution_engine_executionengine_execute`
- **Target:** `AsurDev/ete/engine/execution_engine.py:L98 :: asurdev_ete_engine_execution_engine_py_engine_execution_engine_executionengine_execute_node`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agent_http_migration.py:12:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:14:        f"{node.module}.{alias.name}"
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:15:        for node in ast.walk(tree)
    ```

### INFERRED #calls-199
- **Source:** `AsurDev/ete/recorder/trace_recorder.py:LL36 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record`
- **Target:** `AsurDev/ete/recorder/trace_recorder.py:L44 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record_ceph`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:7:  1.3 heartbeat_age replaced with explicit ceph health detail parsing
    ```
    ```
    /home/workspace/home-cluster-iac/self_healing/diagnostics/ceph.py:57:    Run ceph command via SSH. Reuses connection via explicit host param.
    ```

### INFERRED #calls-200
- **Source:** `AsurDev/ete/recorder/trace_recorder.py:LL34 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record`
- **Target:** `AsurDev/ete/recorder/trace_recorder.py:L41 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record_postgres`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/collector.py:79:                user="postgres",
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/feedback/collector.py:80:                password="postgres",
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/dataset/builder.py:22:        tsdb_user: str = "postgres",
    ```

### INFERRED #calls-201
- **Source:** `AsurDev/ete/recorder/trace_recorder.py:LL38 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record`
- **Target:** `AsurDev/ete/recorder/trace_recorder.py:L47 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_record_tsdb`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:85:        self.tsdb = tsdb_client  # TimescaleDB client for historical drift
    ```
    ```
    /home/workspace/home-cluster-iac/ete/recorder/trace_recorder.py:27:        self.tsdb = tsdb_client
    ```
    ```
    /home/workspace/home-cluster-iac/ete/recorder/trace_recorder.py:38:        if self.tsdb:
    ```

### INFERRED #calls-202
- **Source:** `AsurDev/ete/recorder/trace_recorder.py:LL57 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_export`
- **Target:** `AsurDev/ete/recorder/trace_recorder.py:L50 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:21:    response = fastapi_client.get("/api/ab/compare")  # защищённый эндпоинт
    ```
    ```
    /home/workspace/tests/test_auth.py:27:    response = flask_client.get("/api/ab/compare")
    ```
    ```
    /home/workspace/tests/test_auth.py:33:    response = fastapi_client.get("/health")
    ```

### INFERRED #calls-203
- **Source:** `AsurDev/ete/recorder/trace_recorder.py:LL54 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_list`
- **Target:** `AsurDev/ete/recorder/trace_recorder.py:L50 :: asurdev_ete_recorder_trace_recorder_py_recorder_trace_recorder_tracerecorder_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-204
- **Source:** `AsurDev/ete/replay/replay_engine.py:LL39 :: asurdev_ete_replay_replay_engine_py_replay_replay_engine_replayengine_replay`
- **Target:** `AsurDev/ete/replay/replay_engine.py:L43 :: asurdev_ete_replay_replay_engine_py_replay_replay_engine_replayengine_compare_traces`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:240:    print(f"  [OK{'=' if ok else '!'}] INV6 — O(1) lookup: {elapsed:.4f}s for 1000 lookups (100 traces)")
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:98:        traces = self.store.get_traces_by_run(run_id)
    ```
    ```
    /home/workspace/home-cluster-iac/ete/replay/replayer.py:100:        for trace in traces:
    ```

### INFERRED #calls-205
- **Source:** `AsurDev/ete/replay/replayer.py:LL29 :: asurdev_ete_replay_replayer_py_replay_replayer_deterministicreplayer_register_trace`
- **Target:** `AsurDev/ete/replay/replayer.py:L33 :: asurdev_ete_replay_replayer_py_replay_replayer_deterministicreplayer_hash_trace_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:117:        state = engine.get_state()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:118:        assert not math.isnan(state.total_equity)
    ```
    ```
    /home/workspace/tests/agent_test_base.py:62:    ``self.agent_class()`` so per-test state never leaks.
    ```

### INFERRED #calls-206
- **Source:** `AsurDev/ete/replay/replayer.py:LL71 :: asurdev_ete_replay_replayer_py_replay_replayer_deterministicreplayer_replay`
- **Target:** `AsurDev/ete/replay/replayer.py:L33 :: asurdev_ete_replay_replayer_py_replay_replayer_deterministicreplayer_hash_trace_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:117:        state = engine.get_state()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:118:        assert not math.isnan(state.total_equity)
    ```
    ```
    /home/workspace/tests/agent_test_base.py:62:    ``self.agent_class()`` so per-test state never leaks.
    ```

### INFERRED #calls-207
- **Source:** `AsurDev/ete/replay/replayer.py:LL104 :: asurdev_ete_replay_replayer_py_replay_replayer_correlationengine_find_divergence`
- **Target:** `AsurDev/ete/replay/replayer.py:L93 :: asurdev_ete_replay_replayer_py_replay_replayer_correlationengine_query_by_layer`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/persistence.py:40:    Full persistence layer for meta_rl.
    ```
    ```
    /home/workspace/meta_rl/reward.py:4:the meta-RL layer to rank and select strategies.
    ```
    ```
    /home/workspace/meta_rl/reward.py:14:* :func:`RewardCalculator.compute` is a thin orchestration layer: all
    ```

### INFERRED #calls-208
- **Source:** `AsurDev/ete/store/trace_store.py:LL135 :: asurdev_ete_store_trace_store_py_store_trace_store_tracestore_load`
- **Target:** `AsurDev/ete/store/trace_store.py:L48 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/Projects/Loopcraft/loopcraft_demo.py:214:            data = json.load(f)
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:41:    g = json.load(open(GRAPH))
    ```

### INFERRED #calls-209
- **Source:** `AsurDev/ete/store/trace_store.py:LL64 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace_add_node`
- **Target:** `AsurDev/ete/store/trace_store.py:L76 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:40:def load() -> tuple[dict, list, list]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:71:def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:160:    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")
    ```

### INFERRED #calls-210
- **Source:** `AsurDev/ete/store/trace_store.py:LL127 :: asurdev_ete_store_trace_store_py_store_trace_store_tracestore_store`
- **Target:** `AsurDev/ete/store/trace_store.py:L76 :: asurdev_ete_store_trace_store_py_store_trace_store_executiontrace_to_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:227:        chrom_a = dict.fromkeys(CHROMOSOME_KEYS, 0.5)
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:228:        chrom_b = dict.fromkeys(CHROMOSOME_KEYS, 0.8)
    ```
    ```
    /home/workspace/tests/agent_test_base.py:72:    happy_state_overrides: dict = {}
    ```

### INFERRED #calls-211
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL58 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L20 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_sandboxviolation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/meta_rl/trading_bridge.py:33:    def execute(self, strategy, market_data: dict, mode: str = "PAPER") -> TradingExecutionResult:
    ```
    ```
    /home/workspace/meta_rl/calibration.py:132:        conn.execute("PRAGMA journal_mode=WAL")
    ```

### INFERRED #calls-212
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL62 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L46 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_validate_fs_write`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/_template_agent.py:140:        # This is the part you actually write.
    ```
    ```
    /home/workspace/tests/ralph_benchmark/test_agent_basic.py:34:        f.write("""
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:58:    reward-shaped metrics so persistence has something meaningful to write.
    ```

### INFERRED #calls-213
- **Source:** `AsurDev/execution_sandbox/sandbox.py:LL80 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute_batch`
- **Target:** `AsurDev/execution_sandbox/sandbox.py:L52 :: asurdev_execution_sandbox_sandbox_py_execution_sandbox_sandbox_executionsandbox_execute`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:32:                for row in conn.execute(
    ```
    ```
    /home/workspace/meta_rl/trading_bridge.py:33:    def execute(self, strategy, market_data: dict, mode: str = "PAPER") -> TradingExecutionResult:
    ```
    ```
    /home/workspace/meta_rl/calibration.py:132:        conn.execute("PRAGMA journal_mode=WAL")
    ```

### INFERRED #calls-214
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL151 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_all_detectors`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L13 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_slurm_controller_down`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:138:        with patch.object(agent, self.data_method, side_effect=ConnectionError("data_room down")):
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:121:            raise RuntimeError("down")
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:126:    with patch.object(agent, "retrieve", side_effect=ConnectionError("data_room down")):
    ```

### INFERRED #calls-215
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL152 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_all_detectors`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L32 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_slurm_worker_down`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:138:        with patch.object(agent, self.data_method, side_effect=ConnectionError("data_room down")):
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:121:            raise RuntimeError("down")
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:126:    with patch.object(agent, "retrieve", side_effect=ConnectionError("data_room down")):
    ```

### INFERRED #calls-216
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL153 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_all_detectors`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L49 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_ceph_health_degraded`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:191:            degraded = max(30, round(confidence * grounding_factor))
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:192:            confidence = degraded
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:193:            print(f"[Grounding] factor={grounding_factor:.3f} → conf {confidence} (degraded)")
    ```

### INFERRED #calls-217
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL154 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_all_detectors`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L83 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_ray_head_down`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/self_question.py:43:    Each question tracks its historical accuracy — bad questions get weighted down.
    ```
    ```
    /home/workspace/agents/_impl/amre/test_lag_windowing.py:293:        r_spike = lw.add(confidence=30)  # spike down
    ```
    ```
    /home/workspace/agents/_impl/ml_predictor_agent.py:67:        elif direction_pred["direction"] == "down":
    ```

### INFERRED #calls-218
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL155 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_all_detectors`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L100 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_wireguard_peer_down`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:138:        with patch.object(agent, self.data_method, side_effect=ConnectionError("data_room down")):
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:121:            raise RuntimeError("down")
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:126:    with patch.object(agent, "retrieve", side_effect=ConnectionError("data_room down")):
    ```

### INFERRED #calls-219
- **Source:** `AsurDev/failure_orchestrator/detectors.py:LL156 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_all_detectors`
- **Target:** `AsurDev/failure_orchestrator/detectors.py:L129 :: asurdev_failure_orchestrator_detectors_py_failure_orchestrator_detectors_gpu_available`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_kepler_differential.py:178:    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    ```
    ```
    /home/workspace/tests/test_kepler_differential.py:187:    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    ```
    ```
    /home/workspace/tests/test_kepler_differential.py:196:    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    ```

### INFERRED #calls-220
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL125 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L24 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_load_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_rag_agent_integration.py:13:    async def run(self, state: dict) -> AgentResponse:
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:117:        state = engine.get_state()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:118:        assert not math.isnan(state.total_equity)
    ```

### INFERRED #calls-221
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL169 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L33 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_save_state`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:117:        state = engine.get_state()
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:118:        assert not math.isnan(state.total_equity)
    ```
    ```
    /home/workspace/tests/agent_test_base.py:62:    ``self.agent_class()`` so per-test state never leaks.
    ```

### INFERRED #calls-222
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL87 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_escalate`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L38 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_load_escalation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_docker_security.py:58:    # 5. Services must drop all capabilities and disable privilege escalation
    ```
    ```
    /home/workspace/home-cluster-iac/l10_self_healing/orchestrator/failure_isolation.py:25:    HARD = auto()  # mandatory rollback + escalation
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/orchestrator.py:111:            log.error(f"Telegram escalation failed: {e}")
    ```

### INFERRED #calls-223
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL95 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_escalate`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L47 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_save_escalation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_docker_security.py:58:    # 5. Services must drop all capabilities and disable privilege escalation
    ```
    ```
    /home/workspace/home-cluster-iac/l10_self_healing/orchestrator/failure_isolation.py:25:    HARD = auto()  # mandatory rollback + escalation
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/orchestrator.py:111:            log.error(f"Telegram escalation failed: {e}")
    ```

### INFERRED #calls-224
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL140 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L60 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_recoveryengine_should_retry`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_http_client.py:52:        # Передаём retry вручную (будет реализовано в методе)
    ```
    ```
    /home/workspace/tests/test_http_client.py:53:        # Пока проверяем только сам retry-механизм — его нужно будет добавить в клиент
    ```
    ```
    /home/workspace/tests/test_http_client.py:54:        pass  # этот тест написан для будущей реализации retry
    ```

### INFERRED #calls-225
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL141 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L64 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_recoveryengine_record_attempt`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/live_provider.py:135:        for attempt in range(_CCXT_RECONNECT_ATTEMPTS):
    ```
    ```
    /home/workspace/meta_rl/live_provider.py:142:                logger.warning(f"[CCXT] {method} attempt {attempt + 1} failed: {e}")
    ```
    ```
    /home/workspace/meta_rl/live_provider.py:143:                if attempt < _CCXT_RECONNECT_ATTEMPTS - 1:
    ```

### INFERRED #calls-226
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL152 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L68 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_recoveryengine_reset`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/idea_buffer_integration.py:106:    """Clear the in-memory buffer (for testing/reset)."""
    ```
    ```
    /home/workspace/agents/_impl/amre/lag_windowing.py:276:    def reset(self):
    ```
    ```
    /home/workspace/agents/_impl/amre/lag_windowing.py:283:        logger.debug("[LagWindow] reset")
    ```

### INFERRED #calls-227
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL158 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L86 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_escalate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:22:    ESCALATE = "escalate"  # Human review required
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:86:        5. ACT       — apply correction (or escalate)
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:262:        # High severity → escalate
    ```

### INFERRED #calls-228
- **Source:** `AsurDev/failure_orchestrator/orchestrator.py:LL176 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_main`
- **Target:** `AsurDev/failure_orchestrator/orchestrator.py:L121 :: asurdev_failure_orchestrator_orchestrator_py_failure_orchestrator_orchestrator_run_cycle`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/bull_researcher.py:255:        # Moon waxing (first half of cycle)
    ```
    ```
    /home/workspace/agents/_impl/bradley_agent.py:187:        # Check Jupiter-Saturn aspect (major cycle)
    ```
    ```
    /home/workspace/agents/_impl/cycle_agent.py:23:    1. Detect dominant cycle periods (20, 40, 80 days)
    ```

### INFERRED #calls-229
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL138 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_reboot_node`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-230
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL79 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_ceph`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:171:    proc = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True)
    ```

### INFERRED #calls-231
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL70 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_ceph_manager`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:17:    with patch("agents._impl.technical_agent.TechnicalAgent.run") as mock_run:
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:30:        result = await engine.run(start_date="2025-01-01", end_date="2025-01-10", use_real_agents=True)
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:42:    with patch("agents._impl.technical_agent.TechnicalAgent.run") as mock_run:
    ```

### INFERRED #calls-232
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL61 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_ceph_mon`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-233
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL52 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_ceph_osd`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_rag_agent_integration.py:13:    async def run(self, state: dict) -> AgentResponse:
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:17:    with patch("agents._impl.technical_agent.TechnicalAgent.run") as mock_run:
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:30:        result = await engine.run(start_date="2025-01-01", end_date="2025-01-10", use_real_agents=True)
    ```

### INFERRED #calls-234
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL127 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_nvidia_driver`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-235
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL90 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_ray_head`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:171:    proc = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True)
    ```

### INFERRED #calls-236
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL101 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_ray_worker`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-237
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL29 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_slurm_controller`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-238
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL40 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_slurm_worker`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-239
- **Source:** `AsurDev/failure_orchestrator/recovery.py:LL115 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_restart_wireguard`
- **Target:** `AsurDev/failure_orchestrator/recovery.py:L15 :: asurdev_failure_orchestrator_recovery_py_failure_orchestrator_recovery_run`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-240
- **Source:** `AsurDev/feature_pipeline/builder.py:LL55 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_query_tsdb`
- **Target:** `AsurDev/feature_pipeline/builder.py:L47 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_tsdb_connect`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:29:        with sqlite3.connect(self.db) as conn:
    ```
    ```
    /home/workspace/meta_rl/calibration.py:131:        conn = sqlite3.connect(self.db_path, timeout=10.0, isolation_level=None)
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/builder.py:51:            self._conn = psycopg2.connect(self.tsdb_dsn)
    ```

### INFERRED #calls-241
- **Source:** `AsurDev/feature_pipeline/builder.py:LL109 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_build`
- **Target:** `AsurDev/feature_pipeline/builder.py:L53 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_query_tsdb`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:85:        self.tsdb = tsdb_client  # TimescaleDB client for historical drift
    ```
    ```
    /home/workspace/home-cluster-iac/ete/recorder/trace_recorder.py:27:        self.tsdb = tsdb_client
    ```
    ```
    /home/workspace/home-cluster-iac/ete/recorder/trace_recorder.py:38:        if self.tsdb:
    ```

### INFERRED #calls-242
- **Source:** `AsurDev/feature_pipeline/builder.py:LL111 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_build`
- **Target:** `AsurDev/feature_pipeline/builder.py:L76 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_query_prometheus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:39:    # Simple regex: match words that follow prometheus metric naming conventions
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py:268:    return {"status": "ok", "prometheus": prom_status}
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/modules/metrics.py:64:    """Network latency estimate via prometheus blackbox or node_network_*"""
    ```

### INFERRED #calls-243
- **Source:** `AsurDev/feature_pipeline/builder.py:LL116 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_build`
- **Target:** `AsurDev/feature_pipeline/builder.py:L122 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_build_features`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:71:    """MetaAgent wired with a tiny population and slow features disabled."""
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:101:        "description": "ML-based price prediction using historical patterns and features",
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:103:        "inputs": ["price_history", "features", "regime"],
    ```

### INFERRED #calls-244
- **Source:** `AsurDev/feature_pipeline/builder.py:LL119 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_build_batch`
- **Target:** `AsurDev/feature_pipeline/builder.py:L103 :: asurdev_feature_pipeline_builder_py_feature_pipeline_builder_featurebuilder_build`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/mas_factory/atom_032_e2e_test.py:32:        topo = arch.build(intention="swING trade", symbol="BTCUSDT", timeframe="SWING")
    ```
    ```
    /home/workspace/mas_factory/atom_033_production_test.py:139:    topology = architect.build(intention="ANALYZE", symbol="BTCUSDT", timeframe="SWING")
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```

### INFERRED #calls-245
- **Source:** `AsurDev/feature_pipeline/embedding.py:LL103 :: asurdev_feature_pipeline_embedding_py_feature_pipeline_embedding_nodeembeddingbuilder_find_similar_nodes`
- **Target:** `AsurDev/feature_pipeline/embedding.py:L83 :: asurdev_feature_pipeline_embedding_py_feature_pipeline_embedding_nodeembeddingbuilder_cosine_similarity`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:290:        # in the cosine similarity (the dot-product formula clamps negatives to
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:314:        similarity check and is always kept."""
    ```
    ```
    /home/workspace/agents/_impl/amre/replay_buffer.py:8:from .similarity import is_similar_trajectory
    ```

### INFERRED #calls-246
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL123 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_build_dataset`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L66 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_load_events`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/macro_agent.py:174:        Searches for recent geopolitical events and scores their impact.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/events.py:4:  * `home-cluster-iac/acos/events/types.py` already has an `EventType(str, Enum)`
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/events.py:24:    Mirrors `home-cluster-iac/acos/events/types.py:EventType` so existing
    ```

### INFERRED #calls-247
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL71 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_load_events`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L73 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_generate_synthetic_events`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/macro_agent.py:174:        Searches for recent geopolitical events and scores their impact.
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:8:from acos.events.event import Event
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:9:from acos.events.event_log import EventLog
    ```

### INFERRED #calls-248
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL165 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_build_dataset`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L97 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_get_label`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:51:        # Brier for (conf=0.7, label=1): (0.7 - 1)^2 = 0.09
    ```
    ```
    /home/workspace/agents/_impl/technical_agent.py:273:            label = "oversold" if rsi < 40 else "overbought" if rsi > 60 else "neutral"
    ```
    ```
    /home/workspace/agents/_impl/technical_agent.py:274:            parts.append(f"RSI(14)={rsi:.1f} ({label})")
    ```

### INFERRED #calls-249
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL190 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_export_csv`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L118 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_build_dataset`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/quant_agent.py:156:        # Simple momentum: % change over dataset
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/exporter.py:198:        """Export full dataset to JSON. Returns path."""
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/exporter.py:200:        path = Path(output_dir) / "dataset.json"
    ```

### INFERRED #calls-250
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL197 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_export_json`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L118 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_build_dataset`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/quant_agent.py:156:        # Simple momentum: % change over dataset
    ```
    ```
    /home/workspace/home-cluster-iac/job_engine/engine.py:81:    Every transition writes to the event log for ML dataset generation.
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/exporter.py:198:        """Export full dataset to JSON. Returns path."""
    ```

### INFERRED #calls-251
- **Source:** `AsurDev/feature_pipeline/exporter.py:LL219 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_export_parquet`
- **Target:** `AsurDev/feature_pipeline/exporter.py:L118 :: asurdev_feature_pipeline_exporter_py_feature_pipeline_exporter_datasetexporter_build_dataset`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/quant_agent.py:156:        # Simple momentum: % change over dataset
    ```
    ```
    /home/workspace/home-cluster-iac/job_engine/engine.py:81:    Every transition writes to the event log for ML dataset generation.
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/exporter.py:198:        """Export full dataset to JSON. Returns path."""
    ```

### INFERRED #calls-252
- **Source:** `AsurDev/feature_pipeline/pipeline.py:LL155 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_main`
- **Target:** `AsurDev/feature_pipeline/pipeline.py:L38 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_parse_args`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:239:    args = ap.parse_args()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:247:    as_of = (datetime.fromisoformat(args.as_of) if args.as_of
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:343:    if args.fmt == "json":
    ```

### INFERRED #calls-253
- **Source:** `AsurDev/feature_pipeline/pipeline.py:LL167 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_main`
- **Target:** `AsurDev/feature_pipeline/pipeline.py:L57 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_run_continuous`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:548:        Run continuous backtest on historical bars.
    ```
    ```
    /home/workspace/agents/_impl/amre/backtest_loop.py:24:    CONTINUOUS = "continuous"  # Rolling window continuous
    ```
    ```
    /home/workspace/meta_rl/evolution.py:291:        continuous decline > ALPHA_DECAY_REWARD_DROP_PCT.
    ```

### INFERRED #calls-254
- **Source:** `AsurDev/feature_pipeline/pipeline.py:LL172 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_main`
- **Target:** `AsurDev/feature_pipeline/pipeline.py:L89 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_run_export`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:110:    """Generate → evolve → export → persist → reload → verify metrics."""
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:178:    # Verify pool export is also reproducible (StrategyPool.export_elites is pure).
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:3:infer_edges.py — validated INFERRED-edge export for Hybrid Memory.
    ```

### INFERRED #calls-255
- **Source:** `AsurDev/feature_pipeline/pipeline.py:LL177 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_main`
- **Target:** `AsurDev/feature_pipeline/pipeline.py:L115 :: asurdev_feature_pipeline_pipeline_py_feature_pipeline_pipeline_run_embedding`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_observability_ollama.py:18:    mock_response.read.return_value = json.dumps({"embedding": fake_embedding}).encode()
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:346:# ─── Library API (used by tests and embedding) ────────────────
    ```
    ```
    /home/workspace/scripts/architecture_linter.py:467:# ─── Library API (used by tests and embedding) ────────────────
    ```

### INFERRED #calls-256
- **Source:** `AsurDev/feature_pipeline/schemas.py:LL140 :: asurdev_feature_pipeline_schemas_py_feature_pipeline_schemas_mlbatch_to_csv`
- **Target:** `AsurDev/feature_pipeline/schemas.py:L77 :: asurdev_feature_pipeline_schemas_py_feature_pipeline_schemas_labeledexample_to_ml_dict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrofin-sentinel-v5/mas_factory/visualizer.py:164:    def to_json(self) -> dict:
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/mas_factory/visualizer.py:179:    def save_all(self, output_dir: str = "data/topology", session_id: str = None) -> dict[str, str]:
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/mas_factory/visualizer.py:215:def visualize_topology(topology: Topology, output_dir: str = "data/topology", session_id: str = None) -> dict[str, str]:
    ```

### INFERRED #calls-257
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL22 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_std`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L16 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_mean`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_kepler_differential.py:38:    # ─── Test 1: J2000 mean accuracy for outer planets ─────────────────
    ```
    ```
    /home/workspace/tests/test_kepler_differential.py:42:        """J2000: mean error < 1 arcmin for Jupiter and Saturn.
    ```
    ```
    /home/workspace/tests/test_kepler_property.py:283:    """For e=0, eccentric anomaly E should equal mean anomaly M exactly."""
    ```

### INFERRED #calls-258
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL196 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowengine_get_window_data`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L142 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_slidingwindow_get_values`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_kepler.py:118:        # Result is mod 360, so compare normalized values
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:484:        - Returns unchanged values when ``self.lag_enabled`` is False.
    ```
    ```
    /home/workspace/agents/_impl/technical_agent.py:209:    def _ema(self, values: list, period: int) -> float:
    ```

### INFERRED #calls-259
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL202 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowengine_get_aggregated`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L148 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_slidingwindow_aggregate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/walkforward.py:185:            WalkForwardReport with per-split metrics and aggregate assessment
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:24:        resp = await council.aggregate({})
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:32:        resp = await council.aggregate({})
    ```

### INFERRED #calls-260
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL211 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowengine_get_all_windows_for_node`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L148 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_slidingwindow_aggregate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_astro_council_integration.py:24:        resp = await council.aggregate({})
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:32:        resp = await council.aggregate({})
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:40:        resp = await council.aggregate({})
    ```

### INFERRED #calls-261
- **Source:** `AsurDev/feature_pipeline/window_engine.py:LL189 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowengine_push`
- **Target:** `AsurDev/feature_pipeline/window_engine.py:L180 :: asurdev_feature_pipeline_window_engine_py_feature_pipeline_window_engine_windowengine_get_or_create_window`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:63:        "count": 25,  # mature window
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:200:        # Risk control via position_lag (only when window is mature)
    ```
    ```
    /home/workspace/agents/_impl/time_window_agent.py:80:            f"4H window: {window_4h['summary']}. "
    ```

### INFERRED #calls-262
- **Source:** `AsurDev/feature_pipeline/windows.py:LL61 :: asurdev_feature_pipeline_windows_py_feature_pipeline_windows_build_windows`
- **Target:** `AsurDev/feature_pipeline/windows.py:L24 :: asurdev_feature_pipeline_windows_py_feature_pipeline_windows_get_window_data`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:103:    data = json.loads(OVERRIDES_JSON.read_text(encoding="utf-8"))
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:105:    for entry in data.get("overrides", []):
    ```
    ```
    /home/workspace/tests/test_auth_flask_decorator.py:20:        return jsonify({"data": "secret"})
    ```

### INFERRED #calls-263
- **Source:** `AsurDev/governance.py:LL123 :: asurdev_governance_run`
- **Target:** `AsurDev/governance.py:L38 :: asurdev_governance_classify`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_orchestrator.py:18:    """Router must correctly classify queries."""
    ```
    ```
    /home/workspace/home-cluster-iac/v8/incident/model.py:67:        """Factory: create + classify + route incident."""
    ```
    ```
    /home/workspace/home-cluster-iac/v8/incident/model.py:70:        # Auto-classify severity
    ```

### INFERRED #calls-264
- **Source:** `AsurDev/governance.py:LL125 :: asurdev_governance_run`
- **Target:** `AsurDev/governance.py:L44 :: asurdev_governance_get_imports`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrology/residual_model.py:12:# ── package imports (work when run as module) ──
    ```
    ```
    /home/workspace/tests/agent_test_base.py:16:    - Per-agent tests stay tiny (one file ~ 30 lines + imports).
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:12:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```

### INFERRED #calls-265
- **Source:** `AsurDev/governance.py:LL137 :: asurdev_governance_run`
- **Target:** `AsurDev/governance.py:L56 :: asurdev_governance_detect_dynamic`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/synthesis_agent.py:185:        # Compute dynamic risk_pct before synthesis so levels are volatility-aware
    ```
    ```
    /home/workspace/agents/_impl/synthesis_agent.py:303:        # ─── 5. Entry zones, targets, stop (dynamic risk_pct) ──────────
    ```
    ```
    /home/workspace/agents/_impl/synthesis_agent.py:555:        Uses dynamic risk_pct from VolatilityEngine (R-07):
    ```

### INFERRED #calls-266
- **Source:** `AsurDev/governance.py:LL141 :: asurdev_governance_run`
- **Target:** `AsurDev/governance.py:L64 :: asurdev_governance_compute_violations`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:36:    # Either exit 0 (no violations) or non-zero with only warnings.
    ```
    ```
    /home/workspace/tests/test_type_consolidation.py:12:    violations = []
    ```
    ```
    /home/workspace/tests/test_type_consolidation.py:20:                violations.append(str(py_file))
    ```

### INFERRED #calls-267
- **Source:** `AsurDev/governance.py:LL142 :: asurdev_governance_run`
- **Target:** `AsurDev/governance.py:L90 :: asurdev_governance_adversarial_analysis`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_exporter.py:13:        "type": "analysis",
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:26:        "type": "analysis",
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:39:        "type": "analysis",
    ```

### INFERRED #calls-268
- **Source:** `AsurDev/hash_chain/chain.py:LL45 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain_to_dict`
- **Target:** `AsurDev/hash_chain/chain.py:L29 :: asurdev_hash_chain_chain_py_hash_chain_chain_hashchain_verify_chain`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/fundamental_agent.py:137:        """Fetch on-chain metrics (simplified)."""
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:21:        "sources": ["News API", "Social Media", "On-chain data"],
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:34:        "sources": ["News API", "Social Media", "On-chain data"],
    ```

### INFERRED #calls-269
- **Source:** `AsurDev/job_engine/engine.py:LL99 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_create_job`
- **Target:** `AsurDev/job_engine/engine.py:L73 :: asurdev_job_engine_engine_py_job_engine_engine_jobeventhooks_on_submit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:134:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.timeout_ms)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:170:            pool.submit(_sim_wrapper, twin, req.cluster_state, a, req.ml_predictions, req.horizon_minutes)
    ```
    ```
    /home/workspace/home-cluster-iac/tests/unit/test_determinism.py:82:    """Test 3: Deduplication — scheduler must not double-submit."""
    ```

### INFERRED #calls-270
- **Source:** `AsurDev/job_engine/engine.py:LL100 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_create_job`
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
    /home/workspace/home-cluster-iac/load_test/evolution/evolver.py:17:    """Single evolution event."""
    ```

### INFERRED #calls-271
- **Source:** `AsurDev/job_engine/engine.py:LL104 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_admit`
- **Target:** `AsurDev/job_engine/engine.py:L164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-272
- **Source:** `AsurDev/job_engine/engine.py:LL105 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_admit`
- **Target:** `AsurDev/job_engine/engine.py:L151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:24:    2. Identify cycle phase (up/down/transition)
    ```
    ```
    /home/workspace/mas_factory/architect.py:78:    This is the CORE of the transition from SkillMD to MAS Factory.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:107:        State transition per step:
    ```

### INFERRED #calls-273
- **Source:** `AsurDev/job_engine/engine.py:LL108 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_reject`
- **Target:** `AsurDev/job_engine/engine.py:L164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-274
- **Source:** `AsurDev/job_engine/engine.py:LL110 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_reject`
- **Target:** `AsurDev/job_engine/engine.py:L151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:24:    2. Identify cycle phase (up/down/transition)
    ```
    ```
    /home/workspace/mas_factory/architect.py:78:    This is the CORE of the transition from SkillMD to MAS Factory.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:107:        State transition per step:
    ```

### INFERRED #calls-275
- **Source:** `AsurDev/job_engine/engine.py:LL113 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_schedule`
- **Target:** `AsurDev/job_engine/engine.py:L164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-276
- **Source:** `AsurDev/job_engine/engine.py:LL116 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_schedule`
- **Target:** `AsurDev/job_engine/engine.py:L151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:24:    2. Identify cycle phase (up/down/transition)
    ```
    ```
    /home/workspace/mas_factory/architect.py:78:    This is the CORE of the transition from SkillMD to MAS Factory.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:107:        State transition per step:
    ```

### INFERRED #calls-277
- **Source:** `AsurDev/job_engine/engine.py:LL119 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_start`
- **Target:** `AsurDev/job_engine/engine.py:L164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-278
- **Source:** `AsurDev/job_engine/engine.py:LL121 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_start`
- **Target:** `AsurDev/job_engine/engine.py:L151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:24:    2. Identify cycle phase (up/down/transition)
    ```
    ```
    /home/workspace/mas_factory/architect.py:78:    This is the CORE of the transition from SkillMD to MAS Factory.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:107:        State transition per step:
    ```

### INFERRED #calls-279
- **Source:** `AsurDev/job_engine/engine.py:LL124 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_succeed`
- **Target:** `AsurDev/job_engine/engine.py:L164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-280
- **Source:** `AsurDev/job_engine/engine.py:LL126 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_succeed`
- **Target:** `AsurDev/job_engine/engine.py:L151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:24:    2. Identify cycle phase (up/down/transition)
    ```
    ```
    /home/workspace/mas_factory/architect.py:78:    This is the CORE of the transition from SkillMD to MAS Factory.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:107:        State transition per step:
    ```

### INFERRED #calls-281
- **Source:** `AsurDev/job_engine/engine.py:LL129 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_fail`
- **Target:** `AsurDev/job_engine/engine.py:L164 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-282
- **Source:** `AsurDev/job_engine/engine.py:LL139 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_fail`
- **Target:** `AsurDev/job_engine/engine.py:L197 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_on_failure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:38:    """Test that MASFactory failure triggers graceful fallback."""
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:42:        # Simulate MASFactory failure
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:107:    # `bad` is >50% failure → degraded
    ```

### INFERRED #calls-283
- **Source:** `AsurDev/job_engine/engine.py:LL133 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_fail`
- **Target:** `AsurDev/job_engine/engine.py:L200 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_on_retry`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_http_client.py:52:        # Передаём retry вручную (будет реализовано в методе)
    ```
    ```
    /home/workspace/tests/test_http_client.py:53:        # Пока проверяем только сам retry-механизм — его нужно будет добавить в клиент
    ```
    ```
    /home/workspace/tests/test_http_client.py:54:        pass  # этот тест написан для будущей реализации retry
    ```

### INFERRED #calls-284
- **Source:** `AsurDev/job_engine/engine.py:LL134 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_fail`
- **Target:** `AsurDev/job_engine/engine.py:L151 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:24:    2. Identify cycle phase (up/down/transition)
    ```
    ```
    /home/workspace/mas_factory/architect.py:78:    This is the CORE of the transition from SkillMD to MAS Factory.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:107:        State transition per step:
    ```

### INFERRED #calls-285
- **Source:** `AsurDev/job_engine/engine.py:LL136 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_fail`
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
    /home/workspace/home-cluster-iac/load_test/evolution/evolver.py:17:    """Single evolution event."""
    ```

### INFERRED #calls-286
- **Source:** `AsurDev/job_engine/engine.py:LL158 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_transition`
- **Target:** `AsurDev/job_engine/engine.py:L194 :: asurdev_job_engine_engine_py_job_engine_engine_telemetryjobengine_on_state_change`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_integration.py:129:        """Zero notional → allowed (edge case: no position change)."""
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:15:copy it, change:
    ```
    ```
    /home/workspace/tests/_template_agent_test.py:129:    # If your agent DOES depend on a source, change the assertion to:
    ```

### INFERRED #calls-287
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
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:112:        # STEP 2: build event
    ```

### INFERRED #calls-288
- **Source:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:LL100 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failureisolator_classify_incident`
- **Target:** `AsurDev/l10_self_healing/orchestrator/failure_isolation.py:L105 :: asurdev_l10_self_healing_orchestrator_failure_isolation_py_orchestrator_failure_isolation_failureisolator_plan_rollback`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:194:    """Test 4: Correct rollback when SwitchNode fails."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:220:    # Try to apply invalid change (should trigger rollback)
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:238:        # If we get here without exception, check rollback
    ```

### INFERRED #calls-289
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL53 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_check`
- **Target:** `AsurDev/l10_self_healing/watchdog/watchdog.py:L15 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_healthmetric`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:43:    subprocess.run(["git", "config", "user.email", "test@test.com"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:44:    subprocess.run(["git", "config", "user.name", "Test"], check=False)
    ```

### INFERRED #calls-290
- **Source:** `AsurDev/l10_self_healing/watchdog/watchdog.py:LL58 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_check`
- **Target:** `AsurDev/l10_self_healing/watchdog/watchdog.py:L87 :: asurdev_l10_self_healing_watchdog_watchdog_py_watchdog_watchdog_watchdog_evaluate_trigger`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_v2.py:37:        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:45:        assert ok, f"Kill should NOT trigger at 6% DD, got dd={dd:.2%}"
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:220:    # Try to apply invalid change (should trigger rollback)
    ```

### INFERRED #calls-291
- **Source:** `AsurDev/l11_verifier/verifier.py:LL104 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_mid_execution`
- **Target:** `AsurDev/l11_verifier/verifier.py:L43 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_failurereport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:311:            # TTC fallback: single-pass execution
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:315:            # Full TTC execution
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:324:        """Single-pass agent execution."""
    ```

### INFERRED #calls-292
- **Source:** `AsurDev/l11_verifier/verifier.py:LL124 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_post_execution`
- **Target:** `AsurDev/l11_verifier/verifier.py:L43 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_failurereport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:62:    "push/", "atom-federation-os/", "roma-execution-bridge/",
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:20:from trading.execution.sanity import (
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:311:            # TTC fallback: single-pass execution
    ```

### INFERRED #calls-293
- **Source:** `AsurDev/l11_verifier/verifier.py:LL87 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_pre_execution`
- **Target:** `AsurDev/l11_verifier/verifier.py:L43 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_failurereport`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:62:    "push/", "atom-federation-os/", "roma-execution-bridge/",
    ```
    ```
    /home/workspace/agents/_impl/ephemeris_decorator.py:26:    Decorator that blocks agent execution if Swiss Ephemeris is unavailable.
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:311:            # TTC fallback: single-pass execution
    ```

### INFERRED #calls-294
- **Source:** `AsurDev/l11_verifier/verifier.py:LL139 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_full_pipeline`
- **Target:** `AsurDev/l11_verifier/verifier.py:L79 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_pre_execution`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:62:    "push/", "atom-federation-os/", "roma-execution-bridge/",
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:20:from trading.execution.sanity import (
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:311:            # TTC fallback: single-pass execution
    ```

### INFERRED #calls-295
- **Source:** `AsurDev/l11_verifier/verifier.py:LL140 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_full_pipeline`
- **Target:** `AsurDev/l11_verifier/verifier.py:L99 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_mid_execution`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:62:    "push/", "atom-federation-os/", "roma-execution-bridge/",
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:20:from trading.execution.sanity import (
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:311:            # TTC fallback: single-pass execution
    ```

### INFERRED #calls-296
- **Source:** `AsurDev/l11_verifier/verifier.py:LL141 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_full_pipeline`
- **Target:** `AsurDev/l11_verifier/verifier.py:L115 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_post_execution`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:62:    "push/", "atom-federation-os/", "roma-execution-bridge/",
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:311:            # TTC fallback: single-pass execution
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:315:            # Full TTC execution
    ```

### INFERRED #calls-297
- **Source:** `AsurDev/l11_verifier/verifier.py:LL152 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_full_pipeline`
- **Target:** `AsurDev/l11_verifier/verifier.py:L135 :: asurdev_l11_verifier_verifier_py_l11_verifier_verifier_l11verifier_verify_invariants`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/_template_agent_test.py:189:    """The dataclass itself must guard its invariants."""
    ```
    ```
    /home/workspace/tests/test_kepler_property.py:5:Covers: orbital mechanics invariants, convergence, periodicity, no NaN across
    ```
    ```
    /home/workspace/meta_rl/test_reward.py:54:    """RewardConfig invariants and warning behaviour."""
    ```

### INFERRED #calls-298
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL41 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_register_role`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L11 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capability`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/mas_factory/registry.py:239:    def get_by_capability(self, capability: str) -> list[Role]:
    ```
    ```
    /home/workspace/mas_factory/registry.py:240:        return [r for r in self._roles.values() if capability in r.capabilities]
    ```
    ```
    /home/workspace/mas_factory/architect.py:81:        2. Select roles by capability matching
    ```

### INFERRED #calls-299
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL88 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_create`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L75 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/agent_test_base.py:153:                with patch.object(agent.__class__, "HAS_SWISS_EPHEMERIS", False, create=True):
    ```
    ```
    /home/workspace/agents/_impl/_template_agent.py:87:            instructions_path="agents/TemplateAgent_instructions.md",  # TODO: create this file
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_optimizer.py:174:    """Get or create global KARLOptimizer instance."""
    ```

### INFERRED #calls-300
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL117 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L98 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_dual_mode.py:47:            # Import and check that fallback works
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:43:    subprocess.run(["git", "config", "user.email", "test@test.com"], check=False)
    ```

### INFERRED #calls-301
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL135 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_all`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L98 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:32:        capture_output=True, text=True, check=False,
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:79:    """Archived files are exempt from the inherit check."""
    ```
    ```
    /home/workspace/tests/architecture/test_architecture_linter.py:98:        capture_output=True, text=True, check=False,
    ```

### INFERRED #calls-302
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL122 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_any`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L98 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_check`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:43:    subprocess.run(["git", "config", "user.email", "test@test.com"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:44:    subprocess.run(["git", "config", "user.name", "Test"], check=False)
    ```

### INFERRED #calls-303
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL100 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_executioncontext_check`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L108 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capabilitydenied`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_update_progress.py:42:    subprocess.run(["git", "init"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:43:    subprocess.run(["git", "config", "user.email", "test@test.com"], check=False)
    ```
    ```
    /home/workspace/tests/test_update_progress.py:44:    subprocess.run(["git", "config", "user.name", "Test"], check=False)
    ```

### INFERRED #calls-304
- **Source:** `AsurDev/l9_ebl/capabilities/registry.py:LL126 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_enforce_any`
- **Target:** `AsurDev/l9_ebl/capabilities/registry.py:L108 :: asurdev_l9_ebl_capabilities_registry_py_capabilities_registry_capabilitydenied`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **false**
- **Evidence:**
    ```
    target_symbol 'capabilitydenied' not found in AsurDev/l9_ebl/capabilities/registry.py
    ```

### INFERRED #calls-305
- **Source:** `AsurDev/l9_ebl/gate/gate.py:LL59 :: asurdev_l9_ebl_gate_gate_py_gate_gate_executiongate_check`
- **Target:** `AsurDev/l9_ebl/gate/gate.py:L90 :: asurdev_l9_ebl_gate_gate_py_gate_gate_executiongate_log_decision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_registry.py:307:        # TTC decision
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:247:        # Trajectories (simplified — just current decision)
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:354:                    decision=record,
    ```

### INFERRED #calls-306
- **Source:** `AsurDev/l9_ebl/policy_compiler/compiler.py:LL60 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_policycompiler_load_policy`
- **Target:** `AsurDev/l9_ebl/policy_compiler/compiler.py:L11 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_constraintnode`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:5:Implements the policy from docs/adr/ADR-0004-hybrid-memory-policy.md:
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:336:        "policy": "ADR-0004",
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:257:                "policy": "karl_synthesis",
    ```

### INFERRED #calls-307
- **Source:** `AsurDev/l9_ebl/policy_compiler/compiler.py:LL57 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_policycompiler_load_policy`
- **Target:** `AsurDev/l9_ebl/policy_compiler/compiler.py:L36 :: asurdev_l9_ebl_policy_compiler_compiler_py_policy_compiler_compiler_guardrule`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:5:Implements the policy from docs/adr/ADR-0004-hybrid-memory-policy.md:
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:336:        "policy": "ADR-0004",
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:257:                "policy": "karl_synthesis",
    ```

### INFERRED #calls-308
- **Source:** `AsurDev/lccp_v12.py:LL95 :: asurdev_lccp_v12_orch`
- **Target:** `AsurDev/lccp_v12.py:L15 :: asurdev_lccp_v12_controlevent`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:93:            orch = ADLRecoveryOrchestrator(byzantine_risk=False, k=3, t=len(actions))
    ```
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:96:                stage = orch.step(action)
    ```
    ```
    /home/workspace/atom-federation-os/alignment/failure_replay.py:437:        orch = ADLRecoveryOrchestrator(
    ```

### INFERRED #calls-309
- **Source:** `AsurDev/lccp_v12.py:LL118 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L22 :: asurdev_lccp_v12_eventstore`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:24:# ── ПРОСТОЙ EVENT STORE (вместо внешнего pkg.eventstore) ──
    ```
    ```
    /home/workspace/atom-federation-os/chaos/__init__.py:20:from pkg.eventstore.store import EventStore
    ```

### INFERRED #calls-310
- **Source:** `AsurDev/lccp_v12.py:LL95 :: asurdev_lccp_v12_orch`
- **Target:** `AsurDev/lccp_v12.py:L24 :: asurdev_lccp_v12_eventstore_append`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:43:        history.append(
    ```
    ```
    /home/workspace/tests/test_validator.py:436:    r2.errors.append(
    ```
    ```
    /home/workspace/tests/test_dual_mode.py:173:            results.append((test.__name__, success))
    ```

### INFERRED #calls-311
- **Source:** `AsurDev/lccp_v12.py:LL42 :: asurdev_lccp_v12_staterebuilder_rebuild`
- **Target:** `AsurDev/lccp_v12.py:L24 :: asurdev_lccp_v12_eventstore_append`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:115:    lines.append("# VALIDATION_REPORT.md")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:116:    lines.append("")
    ```

### INFERRED #calls-312
- **Source:** `AsurDev/lccp_v12.py:LL132 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L34 :: asurdev_lccp_v12_staterebuilder_rebuild`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:166:    # Verify: no self.get_trace / self.get_all / self.rebuild in engine source
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:176:            if isinstance(func, ast.Attribute) and func.attr in ("get_trace", "get_all", "rebuild"):
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:221:    r1 = StateReducer(log).rebuild("inv5")
    ```

### INFERRED #calls-313
- **Source:** `AsurDev/lccp_v12.py:LL52 :: asurdev_lccp_v12_staterebuilder_verify`
- **Target:** `AsurDev/lccp_v12.py:L34 :: asurdev_lccp_v12_staterebuilder_rebuild`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:166:    # Verify: no self.get_trace / self.get_all / self.rebuild in engine source
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:176:            if isinstance(func, ast.Attribute) and func.attr in ("get_trace", "get_all", "rebuild"):
    ```
    ```
    /home/workspace/home-cluster-iac/tests/test_amneziawg_integration.py:221:    r1 = StateReducer(log).rebuild("inv5")
    ```

### INFERRED #calls-314
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

### INFERRED #calls-315
- **Source:** `AsurDev/lccp_v12.py:LL120 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L62 :: asurdev_lccp_v12_node`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:75:    src_label = edge["source"].rsplit("_", 1)[-1]   # last segment of node id
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:90:    # 3. target node has no source_file at all (parser bug — same family as KI-014)
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:12:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```

### INFERRED #calls-316
- **Source:** `AsurDev/lccp_v12.py:LL73 :: asurdev_lccp_v12_health`
- **Target:** `AsurDev/lccp_v12.py:L70 :: asurdev_lccp_v12_node_within`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/agent_test_base.py:179:        """First call must return within HOT_LATENCY_BUDGET_S."""
    ```
    ```
    /home/workspace/tests/test_risk_integration.py:124:        """New 5% position within 10% limit → accepted."""
    ```
    ```
    /home/workspace/tests/test_kepler_differential.py:44:        Pure Keplerian (2-body) vs N-body DE405 should agree within ~1 arcminute
    ```

### INFERRED #calls-317
- **Source:** `AsurDev/lccp_v12.py:LL94 :: asurdev_lccp_v12_orch`
- **Target:** `AsurDev/lccp_v12.py:L72 :: asurdev_lccp_v12_health`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:33:    response = fastapi_client.get("/health")
    ```
    ```
    /home/workspace/tests/e2e/test_api_endpoints.py:15:    rv = client.get("/health")
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:108:    health = m.health_check()
    ```

### INFERRED #calls-318
- **Source:** `AsurDev/lccp_v12.py:LL96 :: asurdev_lccp_v12_orch`
- **Target:** `AsurDev/lccp_v12.py:L80 :: asurdev_lccp_v12_ctrl`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/tests/test_meta_control_v78.py:85:        ctrl = ProofFeedbackController()
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_meta_control_v78.py:87:        deltas = ctrl.compute(report)
    ```
    ```
    /home/workspace/atom-federation-os/tests/test_meta_control_v78.py:91:        ctrl = ProofFeedbackController(drift_penalty=0.15)
    ```

### INFERRED #calls-319
- **Source:** `AsurDev/lccp_v12.py:LL106 :: asurdev_lccp_v12_orch`
- **Target:** `AsurDev/lccp_v12.py:L85 :: asurdev_lccp_v12_run_act`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/self_question.py:53:        "Is the regime stable enough to act on this signal?",
    ```
    ```
    /home/workspace/home-cluster-iac/v7/drift_alignment/tracker.py:148:        for sim, act in zip(simulated_states[-50:], actual_states[-50:]):
    ```
    ```
    /home/workspace/home-cluster-iac/v7/drift_alignment/tracker.py:151:                if key in sim and key in act:
    ```

### INFERRED #calls-320
- **Source:** `AsurDev/lccp_v12.py:LL126 :: asurdev_lccp_v12_main`
- **Target:** `AsurDev/lccp_v12.py:L90 :: asurdev_lccp_v12_orch`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:93:            orch = ADLRecoveryOrchestrator(byzantine_risk=False, k=3, t=len(actions))
    ```
    ```
    /home/workspace/atom-federation-os/chaos/harness.py:96:                stage = orch.step(action)
    ```
    ```
    /home/workspace/atom-federation-os/alignment/failure_replay.py:437:        orch = ADLRecoveryOrchestrator(
    ```

### INFERRED #calls-321
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL144 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L319 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_act`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/self_question.py:53:        "Is the regime stable enough to act on this signal?",
    ```
    ```
    /home/workspace/home-cluster-iac/v7/drift_alignment/tracker.py:148:        for sim, act in zip(simulated_states[-50:], actual_states[-50:]):
    ```
    ```
    /home/workspace/home-cluster-iac/v7/drift_alignment/tracker.py:151:                if key in sim and key in act:
    ```

### INFERRED #calls-322
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL132 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L226 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_classify`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_orchestrator.py:18:    """Router must correctly classify queries."""
    ```
    ```
    /home/workspace/home-cluster-iac/governance.py:69:def classify(fp):
    ```
    ```
    /home/workspace/home-cluster-iac/governance.py:166:            src_layer = classify(fp)
    ```

### INFERRED #calls-323
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL135 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L249 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_decide`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/push/mas_factory/topology.py:76:    def decide(self, context: dict[str, Any]) -> list[str]:
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:82:    # Test decide() - returns selected candidates
    ```
    ```
    /home/workspace/push/mas_factory/atom_030_stress_test.py:83:    candidates = unc.decide(ctx_high)
    ```

### INFERRED #calls-324
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL129 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L164 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_detect_signals`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:33:            "Real agents should not produce synthetic momentum signals"
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:171:                "reasoning": "Synthesis: mixed signals",
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:103:        "signals": [
    ```

### INFERRED #calls-325
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL139 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L292 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_governance_approval`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/gate/governance_gate.py:25:    L8 + L9 mandatory gate. NO execution without approval.
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:306:            approved=False,  # Needs governance approval
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:312:        """STEP 4: Route through v8 safety kernel for approval."""
    ```

### INFERRED #calls-326
- **Source:** `AsurDev/load_test/correction_loop/loop.py:LL149 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_cycle`
- **Target:** `AsurDev/load_test/correction_loop/loop.py:L331 :: asurdev_load_test_correction_loop_loop_py_correction_loop_loop_correctionloop_validate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-327
- **Source:** `AsurDev/load_test/evolution/evolver.py:LL61 :: asurdev_load_test_evolution_evolver_py_evolution_evolver_evolutionengine_record`
- **Target:** `AsurDev/load_test/evolution/evolver.py:L14 :: asurdev_load_test_evolution_evolver_py_evolution_evolver_evolutionrecord`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:88:    m.record("resolver_a", latency=0.1, success=True, quality=0.95)
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:89:    m.record("resolver_a", latency=0.2, success=False, quality=0.0)
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:90:    m.record("resolver_b", latency=0.3, success=True, quality=0.8)
    ```

### INFERRED #calls-328
- **Source:** `AsurDev/load_test/evolution/evolver.py:LL133 :: asurdev_load_test_evolution_evolver_py_evolution_evolver_evolutionengine_get_evolution_report`
- **Target:** `AsurDev/load_test/evolution/evolver.py:L111 :: asurdev_load_test_evolution_evolver_py_evolution_evolver_evolutionengine_should_trigger_meta_learning`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/replay_buffer.py:1:"""amre/replay_buffer.py — Replay Buffer for trajectory learning"""
    ```
    ```
    /home/workspace/meta_rl/meta_agent.py:107:    updates internal state for cross-session learning.
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/evolution/evolver.py:48:    Detects convergence, identifies stuck patterns, triggers meta-learning.
    ```

### INFERRED #calls-329
- **Source:** `AsurDev/load_test/injectors/synthetic_scheduler.py:LL105 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_syntheticscheduler_run_simulation`
- **Target:** `AsurDev/load_test/injectors/synthetic_scheduler.py:L29 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_jobresult`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:3:Digital Twin — deterministic forward simulation engine.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:104:        Deterministic forward simulation over horizon_minutes.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:127:        """Vectorized batch simulation — runs all actions in parallel."""
    ```

### INFERRED #calls-330
- **Source:** `AsurDev/load_test/injectors/synthetic_scheduler.py:LL75 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_syntheticscheduler_submit`
- **Target:** `AsurDev/load_test/injectors/synthetic_scheduler.py:L77 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_syntheticscheduler_run_simulation`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:3:Digital Twin — deterministic forward simulation engine.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:104:        Deterministic forward simulation over horizon_minutes.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:127:        """Vectorized batch simulation — runs all actions in parallel."""
    ```

### INFERRED #calls-331
- **Source:** `AsurDev/load_test/injectors/synthetic_scheduler.py:LL90 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_syntheticscheduler_run_simulation`
- **Target:** `AsurDev/load_test/injectors/synthetic_scheduler.py:L133 :: asurdev_load_test_injectors_synthetic_scheduler_py_injectors_synthetic_scheduler_syntheticscheduler_try_schedule`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:36:    def schedule(self, dag: dict, context: dict) -> dict:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:37:        """Compile DAG into executable schedule. Contract-required method."""
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/events.py:83:    consumers must tolerate missing `schedule` / `final_state` etc.
    ```

### INFERRED #calls-332
- **Source:** `AsurDev/load_test/observability/metrics.py:LL73 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_init`
- **Target:** `AsurDev/load_test/observability/metrics.py:L45 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricthresholds`
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

### INFERRED #calls-333
- **Source:** `AsurDev/load_test/observability/metrics.py:LL81 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_collect`
- **Target:** `AsurDev/load_test/observability/metrics.py:L104 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_collect_from_prometheus`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/validate_alerts_metrics.py:39:    # Simple regex: match words that follow prometheus metric naming conventions
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py:268:    return {"status": "ok", "prometheus": prom_status}
    ```
    ```
    /home/workspace/home-cluster-iac/ai_scheduler/modules/metrics.py:64:    """Network latency estimate via prometheus blackbox or node_network_*"""
    ```

### INFERRED #calls-334
- **Source:** `AsurDev/load_test/observability/metrics.py:LL93 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_collect`
- **Target:** `AsurDev/load_test/observability/metrics.py:L145 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_enrich_from_scheduler_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-335
- **Source:** `AsurDev/load_test/observability/metrics.py:LL87 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_collect`
- **Target:** `AsurDev/load_test/observability/metrics.py:L140 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_enrich_from_state_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:64:        1. load snapshot from state store
    ```

### INFERRED #calls-336
- **Source:** `AsurDev/load_test/observability/metrics.py:LL99 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_collect`
- **Target:** `AsurDev/load_test/observability/metrics.py:L159 :: asurdev_load_test_observability_metrics_py_observability_metrics_metricscollector_synthetic_baseline`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:306:        """Empty pool ⇒ no comparison baseline ⇒ every candidate passes."""
    ```
    ```
    /home/workspace/meta_rl/evolution.py:300:        baseline = self._history[-window - 1].max_reward if len(self._history) > window else recent[0]
    ```
    ```
    /home/workspace/meta_rl/evolution.py:306:        drop_pct = (baseline - recent[-1]) / abs(baseline) if baseline != 0 else 0
    ```

### INFERRED #calls-337
- **Source:** `AsurDev/load_test/orchestrator/__main__.py:LL62 :: asurdev_load_test_orchestrator_main_py_orchestrator_main_main`
- **Target:** `AsurDev/load_test/orchestrator/__main__.py:L24 :: asurdev_load_test_orchestrator_main_py_orchestrator_main_run_scenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:82:        1. REQUEST   — load scenario + system state
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/workload/generator.py:135:            raise ValueError(f"Unknown scenario: {scenario_name}")
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/workload/generator.py:136:        scenario = SCENARIOS[scenario_name]
    ```

### INFERRED #calls-338
- **Source:** `AsurDev/load_test/orchestrator/__main__.py:LL97 :: asurdev_load_test_orchestrator_main_py_orchestrator_main_main`
- **Target:** `AsurDev/load_test/orchestrator/__main__.py:L38 :: asurdev_load_test_orchestrator_main_py_orchestrator_main_compute_tag_stats`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:129:    stats = defaultdict(int)
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:136:            stats[verdict] += 1
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:151:    total = sum(stats.values())
    ```

### INFERRED #calls-339
- **Source:** `AsurDev/load_test/reporters/markdown.py:LL66 :: asurdev_load_test_reporters_markdown_py_reporters_markdown_generate_report`
- **Target:** `AsurDev/load_test/reporters/markdown.py:L11 :: asurdev_load_test_reporters_markdown_py_reporters_markdown_format_result`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:30:        result = await engine.run(start_date="2025-01-01", end_date="2025-01-10", use_real_agents=True)
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:32:        assert all("momentum=" not in t.signal_reasoning for t in result.trades), (
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:54:        result = await engine.run("2025-01-01", "2025-01-10", use_real_agents=True)
    ```

### INFERRED #calls-340
- **Source:** `AsurDev/load_test/scenarios/false_positive/test.py:LL20 :: asurdev_load_test_scenarios_false_positive_test_py_false_positive_test_falsepositivescenario_init`
- **Target:** `AsurDev/load_test/scenarios/false_positive/test.py:L12 :: asurdev_load_test_scenarios_false_positive_test_py_false_positive_test_osdstate`
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

### INFERRED #calls-341
- **Source:** `AsurDev/load_test/scenarios/false_positive/test.py:LL62 :: asurdev_load_test_scenarios_false_positive_test_py_false_positive_test_run`
- **Target:** `AsurDev/load_test/scenarios/false_positive/test.py:L15 :: asurdev_load_test_scenarios_false_positive_test_py_false_positive_test_falsepositivescenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-342
- **Source:** `AsurDev/load_test/scenarios/false_positive/test.py:LL63 :: asurdev_load_test_scenarios_false_positive_test_py_false_positive_test_run`
- **Target:** `AsurDev/load_test/scenarios/false_positive/test.py:L23 :: asurdev_load_test_scenarios_false_positive_test_py_false_positive_test_falsepositivescenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v8/policy_verifier/pipeline.py:101:            return self.digital_twin.simulate(
    ```

### INFERRED #calls-343
- **Source:** `AsurDev/load_test/scenarios/governance_failure/test.py:LL46 :: asurdev_load_test_scenarios_governance_failure_test_py_governance_failure_test_run`
- **Target:** `AsurDev/load_test/scenarios/governance_failure/test.py:L15 :: asurdev_load_test_scenarios_governance_failure_test_py_governance_failure_test_governancefailurescenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-344
- **Source:** `AsurDev/load_test/scenarios/governance_failure/test.py:LL47 :: asurdev_load_test_scenarios_governance_failure_test_py_governance_failure_test_run`
- **Target:** `AsurDev/load_test/scenarios/governance_failure/test.py:L20 :: asurdev_load_test_scenarios_governance_failure_test_py_governance_failure_test_governancefailurescenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:95:    def simulate(
    ```

### INFERRED #calls-345
- **Source:** `AsurDev/load_test/scenarios/idempotency/test.py:LL31 :: asurdev_load_test_scenarios_idempotency_test_py_idempotency_test_idempotencyscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/idempotency/test.py:L12 :: asurdev_load_test_scenarios_idempotency_test_py_idempotency_test_executedaction`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v8/policy_verifier/pipeline.py:101:            return self.digital_twin.simulate(
    ```

### INFERRED #calls-346
- **Source:** `AsurDev/load_test/scenarios/idempotency/test.py:LL52 :: asurdev_load_test_scenarios_idempotency_test_py_idempotency_test_run`
- **Target:** `AsurDev/load_test/scenarios/idempotency/test.py:L15 :: asurdev_load_test_scenarios_idempotency_test_py_idempotency_test_idempotencyscenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:23:            agent.run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 80))
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:31:            agent.run = AsyncMock(return_value=mock_response(SignalDirection.SHORT, 80))
    ```
    ```
    /home/workspace/tests/test_astro_council_integration.py:39:            agent.run = AsyncMock(return_value=mock_response(SignalDirection.NEUTRAL, 50))
    ```

### INFERRED #calls-347
- **Source:** `AsurDev/load_test/scenarios/idempotency/test.py:LL53 :: asurdev_load_test_scenarios_idempotency_test_py_idempotency_test_run`
- **Target:** `AsurDev/load_test/scenarios/idempotency/test.py:L19 :: asurdev_load_test_scenarios_idempotency_test_py_idempotency_test_idempotencyscenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v8/policy_verifier/pipeline.py:101:            return self.digital_twin.simulate(
    ```

### INFERRED #calls-348
- **Source:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:LL46 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario_generate_nodes`
- **Target:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:L12 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_node`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_agent_http_migration.py:12:    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:14:        f"{node.module}.{alias.name}"
    ```
    ```
    /home/workspace/tests/test_agent_http_migration.py:15:        for node in ast.walk(tree)
    ```

### INFERRED #calls-349
- **Source:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:LL59 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_run`
- **Target:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:L15 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:188:    """Тест интеграции position_lag risk control в run()."""
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:222:            # Risk control вызывается только в run(), не в _apply_lag_smoothing
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:250:        # В run() position_pct корректируется через apply_position_lag_risk
    ```

### INFERRED #calls-350
- **Source:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:LL23 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:L44 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario_generate_nodes`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:42:    nodes = {n["id"]: n for n in g["nodes"]}
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:45:    return nodes, links, sample
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:109:    nodes, _links, sample = load()
    ```

### INFERRED #calls-351
- **Source:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:LL25 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:L52 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario_pick_without_penalty`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/reward.py:4:- Regime-aware reward with drawdown penalty
    ```
    ```
    /home/workspace/agents/_impl/amre/reward.py:162:    penalty: float
    ```
    ```
    /home/workspace/agents/_impl/amre/reward.py:182:        """Assess whether reward is spurious and apply penalty."""
    ```

### INFERRED #calls-352
- **Source:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:LL60 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_run`
- **Target:** `AsurDev/load_test/scenarios/ml_risk_ignored/test.py:L20 :: asurdev_load_test_scenarios_ml_risk_ignored_test_py_ml_risk_ignored_test_mlriskignoredscenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v8/policy_verifier/pipeline.py:101:            return self.digital_twin.simulate(
    ```

### INFERRED #calls-353
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL220 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_run_all`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L31 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:32:        assert all("momentum=" not in t.signal_reasoning for t in result.trades), (
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:131:    assert all(isinstance(s, ScoredStrategy) for s in elites)
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:132:    assert all(s.reward_history for s in elites), "every elite must have reward history"
    ```

### INFERRED #calls-354
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL118 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L187 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_apply_correction`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrology/vedic.py:221:    # Sidereal correction (ayanamsa ~ 24° in 2026)
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/orchestrator/__main__.py:75:                        "correction": r["correction_applied"],
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/orchestrator/__main__.py:87:    for correction in corrections:
    ```

### INFERRED #calls-355
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL115 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L182 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_check_failure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/karl_diagnostics.py:136:        issues.append("High OOS failure rate")
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_diagnostics.py:174:    if "High OOS failure rate" in issues:
    ```
    ```
    /home/workspace/agents/_impl/amre/grounding.py:90:    # Count failed checks (issues with "but" + "signal" = internal consistency failure)
    ```

### INFERRED #calls-356
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL114 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L158 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_compute_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_metrics_cli.py:14:    """Проверяем, что команда 'karl metrics serve' доступна."""
    ```
    ```
    /home/workspace/tests/test_metrics_cli.py:16:        [sys.executable, "-m", "orchestration.karl_cli", "metrics", "serve", "--help"],
    ```
    ```
    /home/workspace/tests/test_metrics_cli.py:21:    assert result.returncode == 0, f"metrics serve --help failed: {result.stderr}"
    ```

### INFERRED #calls-357
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL98 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L124 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_make_decision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:247:        # Trajectories (simplified — just current decision)
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:354:                    decision=record,
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:307:        # TTC decision
    ```

### INFERRED #calls-358
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL120 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L198 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate_after_fix`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/mas_factory/engine.py:3:from mas_factory.registry import get_agent_runner  # F821 fix
    ```
    ```
    /home/workspace/mas_factory/engine.py:145:        errors = 0  # F821 fix
    ```
    ```
    /home/workspace/meta_rl/trading_bridge.py:2:META_RL_TRADING_ENABLED = False  # F821 fix (TODO: move to config)
    ```

### INFERRED #calls-359
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL229 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_run_all`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L62 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v8/policy_verifier/pipeline.py:101:            return self.digital_twin.simulate(
    ```

### INFERRED #calls-360
- **Source:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:LL207 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_simulate_after_fix`
- **Target:** `AsurDev/load_test/scenarios/policy_oscillation/test.py:L124 :: asurdev_load_test_scenarios_policy_oscillation_test_py_policy_oscillation_test_policyoscillationscenario_make_decision`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:247:        # Trajectories (simplified — just current decision)
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:354:                    decision=record,
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:307:        # TTC decision
    ```

### INFERRED #calls-361
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL161 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_run_all`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L29 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:90:    # 3. target node has no source_file at all (parser bug — same family as KI-014)
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:32:        assert all("momentum=" not in t.signal_reasoning for t in result.trades), (
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:294:        assert all(isinstance(r, float) for r in rewards)
    ```

### INFERRED #calls-362
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL168 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_run_all`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L47 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer_api.py:5:POST /simulate    — async batch digital twin evaluation (parallel, non-blocking)
    ```

### INFERRED #calls-363
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL99 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L137 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_apply_correction`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/astrology/vedic.py:221:    # Sidereal correction (ayanamsa ~ 24° in 2026)
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:4:Every cycle: observes state, detects deviation, classifies fix, applies correction.
    ```
    ```
    /home/workspace/home-cluster-iac/load_test/correction_loop/loop.py:26:    """Concrete actions available to the correction loop."""
    ```

### INFERRED #calls-364
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL101 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L146 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate_after_fix`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/mas_factory/engine.py:3:from mas_factory.registry import get_agent_runner  # F821 fix
    ```
    ```
    /home/workspace/mas_factory/engine.py:145:        errors = 0  # F821 fix
    ```
    ```
    /home/workspace/meta_rl/trading_bridge.py:2:META_RL_TRADING_ENABLED = False  # F821 fix (TODO: move to config)
    ```

### INFERRED #calls-365
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL71 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L105 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer.py:19:    k_candidates: int = 5  # Top-k candidates per job
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer.py:35:    Layer 1: Generate k-best candidate placements per job.
    ```
    ```
    /home/workspace/home-cluster-iac/v6/solver/optimizer.py:93:      maximize sum(x[job,node] * utility[job,node])
    ```

### INFERRED #calls-366
- **Source:** `AsurDev/load_test/scenarios/solver_latency/test.py:LL150 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate_after_fix`
- **Target:** `AsurDev/load_test/scenarios/solver_latency/test.py:L105 :: asurdev_load_test_scenarios_solver_latency_test_py_solver_latency_test_solverlatencyscenario_simulate_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:140:            job = JobState(
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:149:            state.jobs[job.job_id] = job
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:176:            for job in state.jobs.values():
    ```

### INFERRED #calls-367
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL30 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L12 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_driftsample`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v8/policy_verifier/pipeline.py:101:            return self.digital_twin.simulate(
    ```

### INFERRED #calls-368
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL81 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_run`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L15 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:59:        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:19:  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:129:        out = subprocess.run(
    ```

### INFERRED #calls-369
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL82 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_run`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L23 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_simulate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:236:        # Manually call _apply_change_internal with bad change to simulate error
    ```
    ```
    /home/workspace/bench/perf_debug.py:15:# Pre-build candidate vectors (simulate hot path)
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:95:    def simulate(
    ```

### INFERRED #calls-370
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL32 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L57 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_analyze`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_metrics_cli.py:42:            "analyze",
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:121:    # T5 — degraded: analyze raises non-ephemeris exception
    ```
    ```
    /home/workspace/tests/test_compromise_agent.py:123:        async def analyze(self, state):
    ```

### INFERRED #calls-371
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL27 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L34 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_feature_value`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:248:        d = {scored: "value"}
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:249:        assert d[scored] == "value"
    ```
    ```
    /home/workspace/tests/test_cache.py:38:    await cache.set("short", "value", ttl=1)  # 1 секунда
    ```

### INFERRED #calls-372
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL28 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L39 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_model_output`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_metrics_endpoint.py:25:    output = generate_latest(REGISTRY).decode()
    ```
    ```
    /home/workspace/tests/test_metrics_endpoint.py:26:    assert "astrofin_requests_total" in output
    ```
    ```
    /home/workspace/tests/test_metrics_endpoint.py:27:    assert "astrofin_broker_errors_total" in output
    ```

### INFERRED #calls-373
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL29 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_simulate`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L44 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_system_metric`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/metrics.py:46:Both patterns produce the same metric names, so dashboards see one
    ```
    ```
    /home/workspace/agents/metrics.py:47:metric per agent regardless of which pattern the author picked.
    ```
    ```
    /home/workspace/agents/metrics.py:66:# same object — prometheus_client raises on duplicate metric registration.
    ```

### INFERRED #calls-374
- **Source:** `AsurDev/load_test/scenarios/state_drift/test.py:LL61 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_analyze`
- **Target:** `AsurDev/load_test/scenarios/state_drift/test.py:L49 :: asurdev_load_test_scenarios_state_drift_test_py_state_drift_test_statedriftscenario_pearson`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/metrics.py:26:            return await self.analyze(state)
    ```
    ```
    /home/workspace/agents/metrics.py:42:            response = await self.analyze(state)
    ```
    ```
    /home/workspace/agents/metrics.py:130:                return await self.analyze(state)
    ```

### INFERRED #calls-375
- **Source:** `AsurDev/load_test/workload/generator.py:LL112 :: asurdev_load_test_workload_generator_py_workload_generator_workloadgenerator_generate`
- **Target:** `AsurDev/load_test/workload/generator.py:L15 :: asurdev_load_test_workload_generator_py_workload_generator_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:140:            job = JobState(
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:149:            state.jobs[job.job_id] = job
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:176:            for job in state.jobs.values():
    ```

### INFERRED #calls-376
- **Source:** `AsurDev/load_test/workload/generator.py:LL133 :: asurdev_load_test_workload_generator_py_workload_generator_workloadgenerator_generate_scenario`
- **Target:** `AsurDev/load_test/workload/generator.py:L47 :: asurdev_load_test_workload_generator_py_workload_generator_workloadgenerator_generate`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:56:        assert result.total_trades > 0, "Should generate at least one trade"
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:467:    # Load or generate data
    ```
    ```
    /home/workspace/mas_factory/atom_030_stress_test.py:145:    # Test that visualizer can generate outputs
    ```

### INFERRED #calls-377
- **Source:** `AsurDev/ml_engine/dataset/builder.py:LL75 :: asurdev_ml_engine_dataset_builder_py_dataset_builder_datasetbuilder_build`
- **Target:** `AsurDev/ml_engine/dataset/builder.py:L122 :: asurdev_ml_engine_dataset_builder_py_dataset_builder_datasetbuilder_label_from_timescale`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/builder.py:21:Backend = Literal["timescale", "prometheus"]
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/builder.py:32:        backend: Backend = "timescale",
    ```
    ```
    /home/workspace/home-cluster-iac/feature_pipeline/builder.py:114:        Uses TimescaleDB if backend='timescale', Prometheus otherwise.
    ```

### INFERRED #calls-378
- **Source:** `AsurDev/ml_engine/feedback/retrainer.py:LL50 :: asurdev_ml_engine_feedback_retrainer_py_feedback_retrainer_retrainer_retrain`
- **Target:** `AsurDev/ml_engine/feedback/retrainer.py:L61 :: asurdev_ml_engine_feedback_retrainer_py_feedback_retrainer_retrainer_load_latest_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:20:    pytest.skip("FastAPI metrics endpoint not yet implemented")
    ```
    ```
    /home/workspace/tests/test_auth.py:39:    response = fastapi_client.get("/metrics")
    ```
    ```
    /home/workspace/agents/metrics.py:2:agents/metrics.py
    ```

### INFERRED #calls-379
- **Source:** `AsurDev/ml_engine/inference/api.py:LL93 :: inference_api_init_shap`
- **Target:** `AsurDev/ml_engine/inference/api.py:L100 :: inference_api_x_train_sample`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:7:  - /tmp/inferred_sample.json   (top-N sample, stratified)
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:44:    sample = json.load(open(SAMPLE))
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:45:    return nodes, links, sample
    ```

### INFERRED #calls-380
- **Source:** `AsurDev/ml_engine/inference/api.py:LL162 :: inference_api_on_startup`
- **Target:** `AsurDev/ml_engine/inference/api.py:L83 :: inference_api_init_shap`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/AsurDev/ml_engine/inference/api.py:87:        import shap
    ```
    ```
    /home/workspace/AsurDev/ml_engine/inference/api.py:93:        _shap_explainer = shap.Explainer(_model, X_train_sample())
    ```
    ```
    /home/workspace/AsurDev/ml_engine/inference/api.py:403:        import shap
    ```

### INFERRED #calls-381
- **Source:** `AsurDev/ml_engine/inference/api.py:LL335 :: asurdev_ml_engine_inference_api_py_inference_api_predict`
- **Target:** `AsurDev/ml_engine/inference/api.py:L100 :: asurdev_ml_engine_inference_api_py_dataframe`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/_impl/cycle_agent.py:42:        Analyze cycle position and predict next turning point.
    ```
    ```
    /home/workspace/mas_factory/architect.py:51:    intent_type: str  # "analyze" | "compare" | "predict" | "backtest"
    ```
    ```
    /home/workspace/mas_factory/architect.py:174:        elif any(w in lower for w in ["predict", "forecast", "will"]):
    ```

### INFERRED #calls-382
- **Source:** `AsurDev/ml_engine/inference/api.py:LL172 :: inference_api_validate_features`
- **Target:** `AsurDev/ml_engine/inference/api.py:L100 :: asurdev_ml_engine_inference_api_py_dataframe`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:101:        "description": "ML-based price prediction using historical patterns and features",
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:103:        "inputs": ["price_history", "features", "regime"],
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:71:    """MetaAgent wired with a tiny population and slow features disabled."""
    ```

### INFERRED #calls-383
- **Source:** `AsurDev/ml_engine/inference/api.py:LL155 :: inference_api_on_startup`
- **Target:** `AsurDev/ml_engine/inference/api.py:L120 :: inference_api_load_model`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_validator.py:47:                    "model": {"provider": "openai", "name": "gpt-4o-mini"},
    ```
    ```
    /home/workspace/tests/test_validator.py:72:                    "model": {
    ```
    ```
    /home/workspace/tests/test_validator.py:100:                    "model": {"provider": "groq", "name": "llama-4"},
    ```

### INFERRED #calls-384
- **Source:** `AsurDev/ml_engine/inference/api.py:LL160 :: inference_api_on_startup`
- **Target:** `AsurDev/ml_engine/inference/api.py:L166 :: inference_api_validate_features`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_exporter.py:101:        "description": "ML-based price prediction using historical patterns and features",
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:103:        "inputs": ["price_history", "features", "regime"],
    ```
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:71:    """MetaAgent wired with a tiny population and slow features disabled."""
    ```

### INFERRED #calls-385
- **Source:** `AsurDev/ml_engine/inference/api.py:LL231 :: inference_api_startup_event`
- **Target:** `AsurDev/ml_engine/inference/api.py:L150 :: inference_api_on_startup`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/acos_cli.py:4:Contract-compliant: all components validated at startup.
    ```
    ```
    /home/workspace/home-cluster-iac/systemd/tunnel_monitor.py:44:        logger.info("Tunnel down on startup, bringing up...")
    ```
    ```
    /home/workspace/astrofin-sentinel-v5/observability/health_endpoints.py:46:@app.on_event("startup")
    ```

### INFERRED #calls-386
- **Source:** `AsurDev/ml_engine/inference/api.py:LL275 :: inference_api_cache_get`
- **Target:** `AsurDev/ml_engine/inference/api.py:L260 :: inference_api_get_cache_ttl`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_cache.py:38:    await cache.set("short", "value", ttl=1)  # 1 секунда
    ```
    ```
    /home/workspace/data/market_adapter.py:99:                        ttl = CACHE_TTL_MAP.get(interval, 3600)
    ```
    ```
    /home/workspace/data/market_adapter.py:102:                            ttl,
    ```

### INFERRED #calls-387
- **Source:** `AsurDev/ml_engine/inference/api.py:LL287 :: inference_api_cache_put`
- **Target:** `AsurDev/ml_engine/inference/api.py:L260 :: inference_api_get_cache_ttl`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_cache.py:38:    await cache.set("short", "value", ttl=1)  # 1 секунда
    ```
    ```
    /home/workspace/data/market_adapter.py:99:                        ttl = CACHE_TTL_MAP.get(interval, 3600)
    ```
    ```
    /home/workspace/data/market_adapter.py:102:                            ttl,
    ```

### INFERRED #calls-388
- **Source:** `AsurDev/ml_engine/inference/api.py:LL272 :: inference_api_cache_get`
- **Target:** `AsurDev/ml_engine/inference/api.py:L264 :: inference_api_input_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:244:    print(f"  Current topology hash: {updater.current_topology.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:245:    print(f"  Expected (after valid change): {new_topo.hash}")
    ```

### INFERRED #calls-389
- **Source:** `AsurDev/ml_engine/inference/api.py:LL282 :: inference_api_cache_put`
- **Target:** `AsurDev/ml_engine/inference/api.py:L264 :: inference_api_input_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:223:        # ── Step 6: Build state hash for record ──────────────────────────────
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:452:        """Compute reproducible state hash."""
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```

### INFERRED #calls-390
- **Source:** `AsurDev/ml_engine/inference/api.py:LL319 :: asurdev_ml_engine_inference_api_py_inference_api_predict`
- **Target:** `AsurDev/ml_engine/inference/api.py:L271 :: inference_api_cache_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-391
- **Source:** `AsurDev/ml_engine/inference/api.py:LL351 :: asurdev_ml_engine_inference_api_py_inference_api_predict`
- **Target:** `AsurDev/ml_engine/inference/api.py:L281 :: inference_api_cache_put`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/rpc/server.py:49:        self._inbound.put(request)
    ```
    ```
    /home/workspace/atom-federation-os/rpc/server.py:69:            self._inbound.put(request)
    ```
    ```
    /home/workspace/atom-federation-os/local-ai-stack/agent_runtime/task_store.py:5:    def put(self, task_id: str, value):
    ```

### INFERRED #calls-392
- **Source:** `AsurDev/ml_engine/inference/ml_client.py:LL65 :: inference_ml_client_get_risk_score`
- **Target:** `AsurDev/ml_engine/inference/ml_client.py:L35 :: inference_ml_client_is_circuit_open`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_meta_rl.py:46:                "open": price * 0.99,
    ```
    ```
    /home/workspace/tests/test_bull_researcher_async.py:34:        # Проверяем структуру: [open, high, low, close, volume]
    ```
    ```
    /home/workspace/tests/data_room/test_data_room.py:53:    # Now open. Next call should NOT invoke the function.
    ```

### INFERRED #calls-393
- **Source:** `AsurDev/ml_engine/inference/ml_client.py:LL83 :: inference_ml_client_get_risk_score`
- **Target:** `AsurDev/ml_engine/inference/ml_client.py:L103 :: inference_ml_client_record_failure`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/karl_diagnostics.py:136:        issues.append("High OOS failure rate")
    ```
    ```
    /home/workspace/agents/_impl/amre/karl_diagnostics.py:174:    if "High OOS failure rate" in issues:
    ```
    ```
    /home/workspace/agents/_impl/amre/grounding.py:90:    # Count failed checks (issues with "but" + "signal" = internal consistency failure)
    ```

### INFERRED #calls-394
- **Source:** `AsurDev/ml_engine/inference/predictor.py:LL94 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_predict`
- **Target:** `AsurDev/ml_engine/inference/predictor.py:L125 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_compute_risk`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_risk_integration.py:85:        # Test the risk engine directly (not via SafetyGate, which doesn't detect pre-existing)
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:116:        assert pos == 0.05  # not yet risk-adjusted
    ```
    ```
    /home/workspace/tests/test_karl_synthesis_lag.py:188:    """Тест интеграции position_lag risk control в run()."""
    ```

### INFERRED #calls-395
- **Source:** `AsurDev/ml_engine/inference/predictor.py:LL73 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_predict`
- **Target:** `AsurDev/ml_engine/inference/predictor.py:L144 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_default_prediction`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/reward.py:127:        """Apply Platt scaling to raw reward prediction."""
    ```
    ```
    /home/workspace/agents/_impl/amre/backtest_loop.py:333:        # В реальной реализации — из trajectory prediction
    ```
    ```
    /home/workspace/agents/_impl/ml_predictor_agent.py:2:ML Predictor Agent — ML-based price prediction and volatility forecasting.
    ```

### INFERRED #calls-396
- **Source:** `AsurDev/ml_engine/inference/predictor.py:LL70 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_predict`
- **Target:** `AsurDev/ml_engine/inference/predictor.py:L110 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_fetch_features`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:71:    """MetaAgent wired with a tiny population and slow features disabled."""
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:101:        "description": "ML-based price prediction using historical patterns and features",
    ```
    ```
    /home/workspace/agents/gitagent_exporter.py:103:        "inputs": ["price_history", "features", "regime"],
    ```

### INFERRED #calls-397
- **Source:** `AsurDev/ml_engine/inference/predictor.py:LL95 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_predict`
- **Target:** `AsurDev/ml_engine/inference/predictor.py:L136 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_recommend`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v7/meta_learner/meta_learner.py:51:    def recommend(
    ```
    ```
    /home/workspace/home-cluster-iac/v7/meta_learner/meta_learner.py:107:        recs = self.recommend(workload_type, cluster_state_class)
    ```
    ```
    /home/workspace/AsurDev/v7/meta_learner/meta_learner.py:50:    def recommend(
    ```

### INFERRED #calls-398
- **Source:** `AsurDev/ml_engine/inference/predictor.py:LL108 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_predict_batch`
- **Target:** `AsurDev/ml_engine/inference/predictor.py:L47 :: asurdev_ml_engine_inference_predictor_py_inference_predictor_predictor_predict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/audit_repo/training/train_residual_model.py:4:Trains a RandomForest to predict Keplerian-vs-SwissEph residuals in arcmin.
    ```
    ```
    /home/workspace/audit_repo/training/train_residual_model.py:10:  5. Train RandomForestRegressor to predict residual from (jd, body)
    ```
    ```
    /home/workspace/audit_repo/core/kepler_hybrid.py:7:  2. ResidualModel.predict(jd, body) → Δ correction in arcmin
    ```

### INFERRED #calls-399
- **Source:** `AsurDev/ml_engine/models/failure_xgboost.py:LL69 :: asurdev_ml_engine_models_failure_xgboost_py_models_failure_xgboost_failurexgboost_predict`
- **Target:** `AsurDev/ml_engine/models/failure_xgboost.py:L61 :: asurdev_ml_engine_models_failure_xgboost_py_models_failure_xgboost_failurexgboost_predict_proba`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/ml_engine/models/failure_xgboost.py:71:        proba = self.predict_proba(X)
    ```
    ```
    /home/workspace/home-cluster-iac/ml_engine/models/failure_xgboost.py:72:        return (proba >= threshold).astype(int)
    ```
    ```
    /home/workspace/AsurDev/ml_engine/models/failure_xgboost.py:69:        proba = self.predict_proba(X)
    ```

### INFERRED #calls-400
- **Source:** `AsurDev/ml_engine/models/load_model.py:LL89 :: asurdev_ml_engine_models_load_model_py_models_load_model_loadxgboost_predict_gpu`
- **Target:** `AsurDev/ml_engine/models/load_model.py:L79 :: asurdev_ml_engine_models_load_model_py_models_load_model_loadxgboost_predict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:42:        Analyze cycle position and predict next turning point.
    ```
    ```
    /home/workspace/mas_factory/architect.py:51:    intent_type: str  # "analyze" | "compare" | "predict" | "backtest"
    ```
    ```
    /home/workspace/mas_factory/architect.py:174:        elif any(w in lower for w in ["predict", "forecast", "will"]):
    ```

### INFERRED #calls-401
- **Source:** `AsurDev/ml_engine/models/load_model.py:LL92 :: asurdev_ml_engine_models_load_model_py_models_load_model_loadxgboost_predict_memory`
- **Target:** `AsurDev/ml_engine/models/load_model.py:L79 :: asurdev_ml_engine_models_load_model_py_models_load_model_loadxgboost_predict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:42:        Analyze cycle position and predict next turning point.
    ```
    ```
    /home/workspace/mas_factory/architect.py:51:    intent_type: str  # "analyze" | "compare" | "predict" | "backtest"
    ```
    ```
    /home/workspace/mas_factory/architect.py:174:        elif any(w in lower for w in ["predict", "forecast", "will"]):
    ```

### INFERRED #calls-402
- **Source:** `AsurDev/ml_engine/models/load_model.py:LL86 :: asurdev_ml_engine_models_load_model_py_models_load_model_loadxgboost_predict_queue`
- **Target:** `AsurDev/ml_engine/models/load_model.py:L79 :: asurdev_ml_engine_models_load_model_py_models_load_model_loadxgboost_predict`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/cycle_agent.py:42:        Analyze cycle position and predict next turning point.
    ```
    ```
    /home/workspace/mas_factory/architect.py:51:    intent_type: str  # "analyze" | "compare" | "predict" | "backtest"
    ```
    ```
    /home/workspace/mas_factory/architect.py:174:        elif any(w in lower for w in ["predict", "forecast", "will"]):
    ```

### INFERRED #calls-403
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL25 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_init`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L27 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_load_index`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/amre/karl_integration.py:63:                fallback_symbol="QQQ",  # Tech index as proxy
    ```
    ```
    /home/workspace/agents/_impl/bradley_agent.py:22:    1. Calculate Bradley seasonality index
    ```
    ```
    /home/workspace/agents/_impl/bradley_agent.py:121:        Calculate Bradley-like seasonality index.
    ```

### INFERRED #calls-404
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL85 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_register`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L34 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_save_index`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/integration/test_evolution_pipeline.py:136:    # Generation index on stats should be monotonic.
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:428:            # Both versions are listed in the index.
    ```
    ```
    /home/workspace/agents/_impl/bradley_agent.py:22:    1. Calculate Bradley seasonality index
    ```

### INFERRED #calls-405
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL62 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_register`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L38 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_compute_hash`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_switch_nodes.py:218:    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:244:    print(f"  Current topology hash: {updater.current_topology.hash}")
    ```
    ```
    /home/workspace/tests/test_switch_nodes.py:245:    print(f"  Expected (after valid change): {new_topo.hash}")
    ```

### INFERRED #calls-406
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL87 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_register`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L90 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-407
- **Source:** `AsurDev/ml_engine/registry/model_registry.py:LL112 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_load_model`
- **Target:** `AsurDev/ml_engine/registry/model_registry.py:L90 :: asurdev_ml_engine_registry_model_registry_py_registry_model_registry_modelregistry_get`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:32:SAMPLE = Path(os.environ.get("INFERRED_SAMPLE") or
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:74:    tgt_file = (tnode or {}).get("source_file", "")
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:112:        buckets[e.get("relation", "uses")].append(e)
    ```

### INFERRED #calls-408
- **Source:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:LL49 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:L15 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_get_ceph_status`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_kepler.py:234:        assert "status" in v
    ```
    ```
    /home/workspace/tests/test_kepler.py:238:        for key in ["kepler_lon", "swiss_lon", "delta_lon", "status", "message"]:
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:58:        status, size, msg = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
    ```

### INFERRED #calls-409
- **Source:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:LL50 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:L23 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_get_ceph_osd_dump`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_validator.py:42:            yaml.dump(
    ```
    ```
    /home/workspace/tests/test_validator.py:67:            yaml.dump(
    ```
    ```
    /home/workspace/tests/test_validator.py:95:            yaml.dump(
    ```

### INFERRED #calls-410
- **Source:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:LL51 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:L32 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_get_ceph_pg_dump`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_validator.py:42:            yaml.dump(
    ```
    ```
    /home/workspace/tests/test_validator.py:67:            yaml.dump(
    ```
    ```
    /home/workspace/tests/test_validator.py:95:            yaml.dump(
    ```

### INFERRED #calls-411
- **Source:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:LL52 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:L40 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_get_ceph_df`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/scripts/optimize_lag_blend.py:94:    df = pd.DataFrame(
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:105:    return df
    ```
    ```
    /home/workspace/scripts/optimize_lag_blend.py:113:    df = pd.read_csv(path)
    ```

### INFERRED #calls-412
- **Source:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:LL114 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_handler_do_get`
- **Target:** `AsurDev/monitoring/exporters/ceph/ceph_exporter.py:L48 :: asurdev_monitoring_exporters_ceph_ceph_exporter_py_ceph_ceph_exporter_build_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:20:    pytest.skip("FastAPI metrics endpoint not yet implemented")
    ```
    ```
    /home/workspace/tests/test_auth.py:39:    response = fastapi_client.get("/metrics")
    ```
    ```
    /home/workspace/tests/test_metrics_cli.py:14:    """Проверяем, что команда 'karl metrics serve' доступна."""
    ```

### INFERRED #calls-413
- **Source:** `AsurDev/monitoring/exporters/slurm/slurm_exporter.py:LL71 :: asurdev_monitoring_exporters_slurm_slurm_exporter_py_slurm_slurm_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/slurm/slurm_exporter.py:L18 :: asurdev_monitoring_exporters_slurm_slurm_exporter_py_slurm_slurm_exporter_get_slurm_queue`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/objective/utility.py:129:            return -0.05  # Small queue penalty
    ```
    ```
    /home/workspace/home-cluster-iac/v6/digital_twin/simulator.py:110:          queue_next     = queue + arrival_rate * dt - completion_rate * dt
    ```
    ```
    /home/workspace/home-cluster-iac/v6/constraint_graph/graph.py:42:    vtype: str  # "compute_node" | "job" | "queue" | "resource_pool"
    ```

### INFERRED #calls-414
- **Source:** `AsurDev/monitoring/exporters/slurm/slurm_exporter.py:LL72 :: asurdev_monitoring_exporters_slurm_slurm_exporter_py_slurm_slurm_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/slurm/slurm_exporter.py:L45 :: asurdev_monitoring_exporters_slurm_slurm_exporter_py_slurm_slurm_exporter_get_slurm_nodes`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:42:    nodes = {n["id"]: n for n in g["nodes"]}
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:45:    return nodes, links, sample
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:109:    nodes, _links, sample = load()
    ```

### INFERRED #calls-415
- **Source:** `AsurDev/monitoring/exporters/slurm/slurm_exporter.py:LL98 :: asurdev_monitoring_exporters_slurm_slurm_exporter_py_slurm_slurm_exporter_handler_do_get`
- **Target:** `AsurDev/monitoring/exporters/slurm/slurm_exporter.py:L69 :: asurdev_monitoring_exporters_slurm_slurm_exporter_py_slurm_slurm_exporter_build_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:20:    pytest.skip("FastAPI metrics endpoint not yet implemented")
    ```
    ```
    /home/workspace/tests/test_auth.py:39:    response = fastapi_client.get("/metrics")
    ```
    ```
    /home/workspace/tests/observability/test_metrics.py:1:"""Smoke tests for observability/metrics.py."""
    ```

### INFERRED #calls-416
- **Source:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:LL56 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter_build_metrics`
- **Target:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:L14 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter_parse_wg_show`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:24:                "reasoning": "Technical indicators show no clear trend",
    ```
    ```
    /home/workspace/agents/_impl/amre/reward.py:56:    this will show it.
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:97:        out = subprocess.check_output(["wg", "show", peer], timeout=5).decode()
    ```

### INFERRED #calls-417
- **Source:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:LL96 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter_handler_do_get`
- **Target:** `AsurDev/monitoring/exporters/wireguard/wg_exporter.py:L55 :: asurdev_monitoring_exporters_wireguard_wg_exporter_py_wireguard_wg_exporter_build_metrics`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth.py:20:    pytest.skip("FastAPI metrics endpoint not yet implemented")
    ```
    ```
    /home/workspace/tests/test_auth.py:39:    response = fastapi_client.get("/metrics")
    ```
    ```
    /home/workspace/tests/test_metrics_cli.py:14:    """Проверяем, что команда 'karl metrics serve' доступна."""
    ```

### INFERRED #calls-418
- **Source:** `AsurDev/scheduler_v3/api.py:LL53 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_admission`
- **Target:** `AsurDev/scheduler_v3/api.py:L43 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:64:        1. load snapshot from state store
    ```

### INFERRED #calls-419
- **Source:** `AsurDev/scheduler_v3/api.py:LL60 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_engine`
- **Target:** `AsurDev/scheduler_v3/api.py:L43 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:1:"""State-store and job-state protocols.
    ```

### INFERRED #calls-420
- **Source:** `AsurDev/scheduler_v3/api.py:LL175 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_job`
- **Target:** `AsurDev/scheduler_v3/api.py:L43 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:1:"""State-store and job-state protocols.
    ```

### INFERRED #calls-421
- **Source:** `AsurDev/scheduler_v3/api.py:LL151 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_scores`
- **Target:** `AsurDev/scheduler_v3/api.py:L43 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:64:        1. load snapshot from state store
    ```

### INFERRED #calls-422
- **Source:** `AsurDev/scheduler_v3/api.py:LL186 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_state`
- **Target:** `AsurDev/scheduler_v3/api.py:L43 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:64:        1. load snapshot from state store
    ```

### INFERRED #calls-423
- **Source:** `AsurDev/scheduler_v3/api.py:LL117 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_schedule`
- **Target:** `AsurDev/scheduler_v3/api.py:L43 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_store`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/meta_rl/strategy_pool.py:315:        # version via a length check because we don't store the version
    ```
    ```
    /home/workspace/meta_rl/evolution.py:182:        self._final_elites = final_elites  # store for get_best_strategy()
    ```
    ```
    /home/workspace/home-cluster-iac/v8/rollback/engine.py:64:        1. load snapshot from state store
    ```

### INFERRED #calls-424
- **Source:** `AsurDev/scheduler_v3/api.py:LL60 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_engine`
- **Target:** `AsurDev/scheduler_v3/api.py:L50 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_admission`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v8/safety_kernel/engine.py:3:Safety Kernel — final admission gate for all decisions.
    ```
    ```
    /home/workspace/home-cluster-iac/v8/safety_kernel/engine.py:57:    Final admission gate — runs BEFORE every decision executes.
    ```
    ```
    /home/workspace/home-cluster-iac/v8/safety_kernel/engine.py:83:        Primary admission function.
    ```

### INFERRED #calls-425
- **Source:** `AsurDev/scheduler_v3/api.py:LL101 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_schedule`
- **Target:** `AsurDev/scheduler_v3/api.py:L57 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_engine`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-426
- **Source:** `AsurDev/scheduler_v3/api.py:LL114 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_schedule`
- **Target:** `AsurDev/scheduler_v3/api.py:L81 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_scheduleresponse`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:36:    def schedule(self, dag: dict, context: dict) -> dict:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:37:        """Compile DAG into executable schedule. Contract-required method."""
    ```
    ```
    /home/workspace/home-cluster-iac/acos/contracts/scheduler_contract.py:9:    def schedule(self, dag: dict, context: dict) -> dict:
    ```

### INFERRED #calls-427
- **Source:** `AsurDev/scheduler_v3/api.py:LL117 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_schedule`
- **Target:** `AsurDev/scheduler_v3/api.py:L173 :: asurdev_scheduler_v3_api_py_scheduler_v3_api_get_job`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:1:"""State-store and job-state protocols.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:27:    """Common job lifecycle shared across schedulers.
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/state.py:45:    """Common job-state DTO.
    ```

### INFERRED #calls-428
- **Source:** `AsurDev/scheduler_v3/scorer.py:LL57 :: asurdev_scheduler_v3_scorer_py_scheduler_v3_scorer_score_and_select`
- **Target:** `AsurDev/scheduler_v3/scorer.py:L97 :: asurdev_scheduler_v3_scorer_py_scheduler_v3_scorer_compute_score`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_sentiment_agent_async.py:26:        assert result["score"] == 0.25
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:66:        score=reward,
    ```
    ```
    /home/workspace/tests/unit/test_strategy_pool_and_persistence.py:121:            score=reward,
    ```

### INFERRED #calls-429
- **Source:** `AsurDev/scheduler_v3/scorer.py:LL42 :: asurdev_scheduler_v3_scorer_py_scheduler_v3_scorer_score_and_select`
- **Target:** `AsurDev/scheduler_v3/scorer.py:L79 :: asurdev_scheduler_v3_scorer_py_scheduler_v3_scorer_filter_eligible`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/admission_controller/controller.py:109:        """Check if any eligible node has enough free memory."""
    ```
    ```
    /home/workspace/home-cluster-iac/scheduler_v3/scorer.py:42:    # Filter eligible nodes by job type
    ```
    ```
    /home/workspace/home-cluster-iac/scheduler_v3/scorer.py:43:    eligible = _filter_eligible(nodes, job_type, memory_gb)
    ```

### INFERRED #calls-430
- **Source:** `AsurDev/scripts/day1-network.sh:LL92 :: home_workspace_asurdev_scripts_day1_network_sh__entry`
- **Target:** `AsurDev/scripts/day1-network.sh:L78 :: asurdev_scripts_day1_network_sh_scripts_day1_network_create_vlan`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:105:    for entry in data.get("overrides", []):
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:106:        key = (entry["source_node_id"], entry["target_node_id"])
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:107:        out[key] = entry
    ```

### INFERRED #calls-431
- **Source:** `AsurDev/scripts/day1-network.sh:LL66 :: home_workspace_asurdev_scripts_day1_network_sh__entry`
- **Target:** `AsurDev/scripts/day1-network.sh:L33 :: asurdev_scripts_day1_network_sh_scripts_day1_network_ros_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-432
- **Source:** `AsurDev/scripts/day1-network.sh:LL83 :: asurdev_scripts_day1_network_sh_scripts_day1_network_create_vlan`
- **Target:** `AsurDev/scripts/day1-network.sh:L33 :: asurdev_scripts_day1_network_sh_scripts_day1_network_ros_api`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/_impl/sentiment_agent.py:91:            url = "https://api.alternative.me/fng/?limit=1"
    ```
    ```
    /home/workspace/agents/_impl/sentiment_agent.py:122:        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
    ```
    ```
    /home/workspace/agents/_impl/risk_agent.py:133:            url = f"https://www.okx.com/api/v5/market/candles?symbol={symbol}-USDT&interval={interval}&limit={limit}"
    ```

### INFERRED #calls-433
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL56 :: home_workspace_asurdev_scripts_day2_vpn_sh__entry`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_command_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_update_progress.py:33:    assert SCRIPT.exists(), "tools/update_progress.sh not found"
    ```
    ```
    /home/workspace/tests/test_update_progress.py:38:    if not SCRIPT.exists():
    ```
    ```
    /home/workspace/tests/test_update_progress.py:54:    assert progress_file.exists(), "progress.md was not created"
    ```

### INFERRED #calls-434
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL60 :: home_workspace_asurdev_scripts_day2_vpn_sh__entry`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/_impl/amre/audit.py:396:        logger.info(
    ```
    ```
    /home/workspace/agents/_impl/amre/lag_windowing.py:167:            logger.info(
    ```

### INFERRED #calls-435
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL57 :: home_workspace_asurdev_scripts_day2_vpn_sh__entry`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L38 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/tests/test_security_fixes.py:88:        self.assertIn("wg-quick", mgr._available_binaries())
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:97:        out = subprocess.check_output(["wg", "show", peer], timeout=5).decode()
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:113:    ok, msg = _run(["wg-quick", "down", interface])
    ```

### INFERRED #calls-436
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL77 :: home_workspace_asurdev_scripts_day2_vpn_sh__entry`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L32 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-437
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL39 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L30 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-438
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL43 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L31 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-439
- **Source:** `AsurDev/scripts/day2-vpn.sh:LL40 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_install_wg`
- **Target:** `AsurDev/scripts/day2-vpn.sh:L34 :: asurdev_scripts_day2_vpn_sh_scripts_day2_vpn_command_exists`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:15:  moved     — entity exists but in a different file (give the new path)
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:122:    lines.append("- `moved` — entity exists, but in a different file (new path noted)")
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:101:    if not OVERRIDES_JSON.exists():
    ```

### INFERRED #calls-440
- **Source:** `AsurDev/scripts/day3-compute.sh:LL201 :: home_workspace_asurdev_scripts_day3_compute_sh__entry`
- **Target:** `AsurDev/scripts/day3-compute.sh:L163 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-441
- **Source:** `AsurDev/scripts/day3-compute.sh:LL41 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_common`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/_impl/amre/audit.py:396:        logger.info(
    ```

### INFERRED #calls-442
- **Source:** `AsurDev/scripts/day3-compute.sh:LL84 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_docker`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-443
- **Source:** `AsurDev/scripts/day3-compute.sh:LL153 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_munge`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-444
- **Source:** `AsurDev/scripts/day3-compute.sh:LL56 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:243:TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:246:KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl", False)}
    ```

### INFERRED #calls-445
- **Source:** `AsurDev/scripts/day3-compute.sh:LL100 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia_container_toolkit`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/data/market_adapter.py:60:            logger.info("Redis connected for market data cache")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```

### INFERRED #calls-446
- **Source:** `AsurDev/scripts/day3-compute.sh:LL114 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_python_ml`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/data/market_adapter.py:60:            logger.info("Redis connected for market data cache")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```

### INFERRED #calls-447
- **Source:** `AsurDev/scripts/day3-compute.sh:LL136 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_update_hosts`
- **Target:** `AsurDev/scripts/day3-compute.sh:L18 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/_impl/amre/audit.py:396:        logger.info(
    ```

### INFERRED #calls-448
- **Source:** `AsurDev/scripts/day3-compute.sh:LL48 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_common`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-449
- **Source:** `AsurDev/scripts/day3-compute.sh:LL80 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_docker`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-450
- **Source:** `AsurDev/scripts/day3-compute.sh:LL157 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_munge`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-451
- **Source:** `AsurDev/scripts/day3-compute.sh:LL62 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-452
- **Source:** `AsurDev/scripts/day3-compute.sh:LL96 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia_container_toolkit`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_registry.py:513:        ok, msg = validate_agent(args.name)
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:514:        print(f"{'✅' if ok else '❌'} {args.name}: {msg}")
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:151:                    "reasoning": "ok",
    ```

### INFERRED #calls-453
- **Source:** `AsurDev/scripts/day3-compute.sh:LL129 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_python_ml`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_registry.py:513:        ok, msg = validate_agent(args.name)
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:514:        print(f"{'✅' if ok else '❌'} {args.name}: {msg}")
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:151:                    "reasoning": "ok",
    ```

### INFERRED #calls-454
- **Source:** `AsurDev/scripts/day3-compute.sh:LL146 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_update_hosts`
- **Target:** `AsurDev/scripts/day3-compute.sh:L19 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-455
- **Source:** `AsurDev/scripts/day3-compute.sh:LL72 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia`
- **Target:** `AsurDev/scripts/day3-compute.sh:L20 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-456
- **Source:** `AsurDev/scripts/day3-compute.sh:LL127 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_python_ml`
- **Target:** `AsurDev/scripts/day3-compute.sh:L20 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-457
- **Source:** `AsurDev/scripts/day3-compute.sh:LL168 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L25 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_detect_os`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_calibration_tracker.py:5:import os
    ```
    ```
    /home/workspace/tests/test_auth.py:3:import os
    ```
    ```
    /home/workspace/tests/test_auth.py:8:os.environ["API_KEY"] = "test-key-123"
    ```

### INFERRED #calls-458
- **Source:** `AsurDev/scripts/day3-compute.sh:LL169 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L40 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_common`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/common/interfaces.py:5:them for callers that still import from ``common.interfaces`` during
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/deterministic.py:3:This is a **verbatim copy** of `common/deterministic.py` from
    ```
    ```
    /home/workspace/acos-contracts/acos_contracts/deterministic.py:6:`common/` on their path.
    ```

### INFERRED #calls-459
- **Source:** `AsurDev/scripts/day3-compute.sh:LL175 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L54 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/detectors.py:127:            ["nvidia-smi", "--query-gpu=gpu_name,temperature.gpu,utilization.gpu", "--format=csv,noheader"], timeout=5
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:125:    ok, msg = _run(["nvidia-smi"])
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:127:        return False, "nvidia-smi not responding"
    ```

### INFERRED #calls-460
- **Source:** `AsurDev/scripts/day3-compute.sh:LL176 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L78 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_docker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_healthcheck.py:86:    # Мокаем отсутствие docker-compose
    ```
    ```
    /home/workspace/tests/test_ralph_safety.py:17:    assert is_protected_file("docker-compose.yml")
    ```
    ```
    /home/workspace/tests/test_ralph_safety.py:42:        lambda *a, **kw: type("res", (), {"stdout": "docker-compose.yml\nother_file.py", "returncode": 0}),
    ```

### INFERRED #calls-461
- **Source:** `AsurDev/scripts/day3-compute.sh:LL177 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L94 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_nvidia_container_toolkit`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-462
- **Source:** `AsurDev/scripts/day3-compute.sh:LL187 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L113 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_python_ml`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v6/solver/candidates/generator.py:31:        self.ml = ml_predictor
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:16:        if jtype in ("ml", "ray"):
    ```
    ```
    /home/workspace/home-cluster-iac/l10_self_healing/orchestrator/failure_isolation.py:134:        elif "ml" in metric:
    ```

### INFERRED #calls-463
- **Source:** `AsurDev/scripts/day3-compute.sh:LL188 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L135 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_update_hosts`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/roma-execution-bridge/config/crd/controller/operator.py:117:                "hosts": [f"{subdomain}.{domain}", domain],
    ```

### INFERRED #calls-464
- **Source:** `AsurDev/scripts/day3-compute.sh:LL170 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_main`
- **Target:** `AsurDev/scripts/day3-compute.sh:L152 :: asurdev_scripts_day3_compute_sh_scripts_day3_compute_install_munge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-465
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL238 :: home_workspace_asurdev_scripts_day4_slurm_sh__entry`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L204 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-466
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL33 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_check_munge`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:243:TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:246:KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl", False)}
    ```

### INFERRED #calls-467
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL170 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_configure_worker`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/data/market_adapter.py:60:            logger.info("Redis connected for market data cache")
    ```
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```

### INFERRED #calls-468
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL129 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_gres_conf`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:243:TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:246:KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl", False)}
    ```

### INFERRED #calls-469
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL70 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_slurm_conf`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:243:TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:246:KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl", False)}
    ```

### INFERRED #calls-470
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL49 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_install_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:243:TTC_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("ttc", False)}
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:246:KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl", False)}
    ```

### INFERRED #calls-471
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL158 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_start_controller`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-472
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL190 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_test_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L24 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-473
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL42 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_check_munge`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-474
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL183 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_configure_worker`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-475
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL151 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_cgroup_conf`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-476
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL138 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_gres_conf`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-477
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL122 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_slurm_conf`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/atom-federation-os/orchestration/consistency/test_cross_origin_proof.py:44:        assert p.equivalence_result.is_equivalent  # empty = trivially ok
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/consistency/invariant_contract/cross_mode_validator.py:138:        ok = (ch == csh == csw)
    ```
    ```
    /home/workspace/atom-federation-os/orchestration/consistency/invariant_contract/cross_mode_validator.py:140:            is_equivalent=ok,
    ```

### INFERRED #calls-478
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL59 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_install_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/gitagent_registry.py:513:        ok, msg = validate_agent(args.name)
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:514:        print(f"{'✅' if ok else '❌'} {args.name}: {msg}")
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:151:                    "reasoning": "ok",
    ```

### INFERRED #calls-479
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL163 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_start_controller`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L25 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_auth_empty_key.py:15:        return jsonify({"status": "ok"})
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:151:                    "reasoning": "ok",
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:181:                {"signal": "NEUTRAL", "confidence": 50, "reasoning": "ok"},
    ```

### INFERRED #calls-480
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL174 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_configure_worker`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L26 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-481
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL61 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_install_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L26 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-482
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL198 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_test_slurm`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L26 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_warn`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-483
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL209 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L32 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_check_munge`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **ambiguous**
- **Evidence:**
    ```
    source_symbol_present_but_target_not
    ```
    ```
    /home/workspace/tests/test_risk_v2.py:277:    pytest.main([__file__, "-v", "--tb=short"])
    ```
    ```
    /home/workspace/tests/test_meta_rl.py:415:    pytest.main([__file__, "-v"])
    ```
    ```
    /home/workspace/tests/test_validator.py:461:    pytest.main([__file__, "-v", "--tb=short"])
    ```

### INFERRED #calls-484
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL210 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L48 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_install_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:18:        elif jtype in ("batch", "slurm"):
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:19:            target = "slurm"
    ```

### INFERRED #calls-485
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL211 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L69 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_slurm_conf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:193:            print(f"[Grounding] factor={grounding_factor:.3f} → conf {confidence} (degraded)")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:516:                f"[LagWindow] conf {confidence} → {adjusted_conf} "
    ```
    ```
    /home/workspace/agents/_impl/compromise_agent.py:94:            conf = self._get_signal_attr(s, "confidence", 0) or 0
    ```

### INFERRED #calls-486
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL212 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L128 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_gres_conf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/infer_edges.py:7:      valid & conf >= 0.7  -> T1
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:8:      valid & conf <  0.7  -> T2
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:270:            conf = float(row["confidence"])
    ```

### INFERRED #calls-487
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL213 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L144 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_create_cgroup_conf`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_orchestrator.py:133:        conf = rec.get("confidence")
    ```
    ```
    /home/workspace/tests/test_orchestrator.py:134:        assert isinstance(conf, (int, float)), f"confidence is {type(conf)}: {conf}"  # noqa: UP038
    ```
    ```
    /home/workspace/tests/test_orchestrator.py:135:        assert 0 <= conf <= 100, f"confidence={conf} out of range"
    ```

### INFERRED #calls-488
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL214 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L157 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_start_controller`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/v8/admission/controller.py:19:    K8s-style admission controller.
    ```
    ```
    /home/workspace/home-cluster-iac/tests/unit/test_determinism.py:110:    controller = AdmissionController(store)
    ```
    ```
    /home/workspace/home-cluster-iac/tests/unit/test_determinism.py:111:    result = controller.admit(
    ```

### INFERRED #calls-489
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL220 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L169 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_configure_worker`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:99:    log.warning(f"Recovery: restarting Ray worker on {node}")
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:107:        return True, f"ray worker started on {node}"
    ```
    ```
    /home/workspace/home-cluster-iac/failure_orchestrator/recovery.py:108:    return False, f"ray worker start failed on {node}: {msg}"
    ```

### INFERRED #calls-490
- **Source:** `AsurDev/scripts/day4-slurm.sh:LL223 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_main`
- **Target:** `AsurDev/scripts/day4-slurm.sh:L189 :: asurdev_scripts_day4_slurm_sh_scripts_day4_slurm_test_slurm`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/home-cluster-iac/governance.py:173:                for kw in ["slurm", "kubectl", "ceph", "docker", "systemctl"]:
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:18:        elif jtype in ("batch", "slurm"):
    ```
    ```
    /home/workspace/home-cluster-iac/ete/scheduler/adapter.py:19:            target = "slurm"
    ```

### INFERRED #calls-491
- **Source:** `AsurDev/scripts/day5-ray.sh:LL248 :: home_workspace_asurdev_scripts_day5_ray_sh__entry`
- **Target:** `AsurDev/scripts/day5-ray.sh:L210 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_main`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/graphify-out/validate_inferred.py:108:def main() -> None:
    ```
    ```
    /home/workspace/graphify-out/validate_inferred.py:164:    main()
    ```
    ```
    /home/workspace/graphify-out/infer_edges.py:234:def main():
    ```

### INFERRED #calls-492
- **Source:** `AsurDev/scripts/day5-ray.sh:LL135 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_create_ray_scripts`
- **Target:** `AsurDev/scripts/day5-ray.sh:L20 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/data/market_adapter.py:60:            logger.info("Redis connected for market data cache")
    ```

### INFERRED #calls-493
- **Source:** `AsurDev/scripts/day5-ray.sh:LL28 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_install_ray`
- **Target:** `AsurDev/scripts/day5-ray.sh:L20 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/agents/_impl/amre/audit.py:396:        logger.info(
    ```

### INFERRED #calls-494
- **Source:** `AsurDev/scripts/day5-ray.sh:LL42 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_start_head`
- **Target:** `AsurDev/scripts/day5-ray.sh:L20 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/agents/_impl/amre/audit.py:396:        logger.info(
    ```

### INFERRED #calls-495
- **Source:** `AsurDev/scripts/day5-ray.sh:LL73 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_start_workers`
- **Target:** `AsurDev/scripts/day5-ray.sh:L20 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_logging.py:20:    logger.info("Test event")
    ```
    ```
    /home/workspace/data/market_adapter.py:60:            logger.info("Redis connected for market data cache")
    ```
    ```
    /home/workspace/agents/karl_synthesis.py:235:        # Collect ensemble info from signals
    ```

### INFERRED #calls-496
- **Source:** `AsurDev/scripts/day5-ray.sh:LL93 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_test_ray`
- **Target:** `AsurDev/scripts/day5-ray.sh:L20 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_info`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-497
- **Source:** `AsurDev/scripts/day5-ray.sh:LL204 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_create_ray_scripts`
- **Target:** `AsurDev/scripts/day5-ray.sh:L21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
- **Verdict:** **valid**
- **Evidence:**
    ```
    /home/workspace/tests/test_backtest_real_agents.py:151:                    "reasoning": "ok",
    ```
    ```
    /home/workspace/tests/test_backtest_real_agents.py:181:                {"signal": "NEUTRAL", "confidence": 50, "reasoning": "ok"},
    ```
    ```
    /home/workspace/agents/gitagent_registry.py:513:        ok, msg = validate_agent(args.name)
    ```

### INFERRED #calls-498
- **Source:** `AsurDev/scripts/day5-ray.sh:LL30 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_install_ray`
- **Target:** `AsurDev/scripts/day5-ray.sh:L21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-499
- **Source:** `AsurDev/scripts/day5-ray.sh:LL62 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_start_head`
- **Target:** `AsurDev/scripts/day5-ray.sh:L21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

### INFERRED #calls-500
- **Source:** `AsurDev/scripts/day5-ray.sh:LL85 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_start_workers`
- **Target:** `AsurDev/scripts/day5-ray.sh:L21 :: asurdev_scripts_day5_ray_sh_scripts_day5_ray_ok`
- **Confidence:** 1.000  **Weight:** 1.00  **Relation:** `calls`
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

---

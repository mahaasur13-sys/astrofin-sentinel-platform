# SKIP_REGISTER.md

**Source of truth:** [`tests/conftest.py`](../tests/conftest.py) — set `SKIP_LIST_KI_125A`
**Last refreshed:** 2026-07-09
**Total entries:** 46

> Generated automatically from `SKIP_LIST_KI_125A`. When you fix one of these
> tests, remove the entry from the conftest set and re-run `pytest --collect-only`
> to verify the test now collects and passes.

## Skip List (KI-125a — tracked in issue #149)

| # | Test ID | Owner | Linked Issue | Target Fix Version |
|---|---------|-------|--------------|--------------------|
| 1 | `tests/architecture/test_architecture_linter.py::test_linter_cli_exit_code_with_violations` | unassigned | #149 | v1.2.0 |
| 2 | `tests/architecture/test_architecture_linter.py::test_linter_flags_ephemeris_without_decorator` | unassigned | #149 | v1.2.0 |
| 3 | `tests/architecture/test_architecture_linter.py::test_linter_flags_orphan_agent` | unassigned | #149 | v1.2.0 |
| 4 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_confidence_clipped_to_unit_interval` | unassigned | #149 | v1.2.0 |
| 5 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_confidence_under_1_treated_as_fraction` | unassigned | #149 | v1.2.0 |
| 6 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_ece_perfect_calibration` | unassigned | #149 | v1.2.0 |
| 7 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_empty_report` | unassigned | #149 | v1.2.0 |
| 8 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_record_and_resolve_round_trip` | unassigned | #149 | v1.2.0 |
| 9 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_reliability_bins_shape` | unassigned | #149 | v1.2.0 |
| 10 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_to_dict_serializable` | unassigned | #149 | v1.2.0 |
| 11 | `tests/test_calibration_tracker.py::CalibrationTrackerTest::test_window_filter` | unassigned | #149 | v1.2.0 |
| 12 | `tests/test_dual_mode.py::test_return_type_unchanged` | unassigned | #149 | v1.2.0 |
| 13 | `tests/test_ephemeris_decorator.py::test_happy_path` | unassigned | #149 | v1.2.0 |
| 14 | `tests/test_logging.py::test_orchestrator_sets_correlation_id` | unassigned | #149 | v1.2.0 |
| 15 | `tests/test_meta_rl.py::TestEvolutionEngine::test_reward_improves_after_evolution` | unassigned | #149 | v1.2.0 |
| 16 | `tests/test_http_client.py::test_get_http_client_returns_async_client` | unassigned | #149 | v1.2.0 |
| 17 | `tests/test_http_client.py::test_get_http_client_is_singleton` | unassigned | #149 | v1.2.0 |
| 18 | `tests/test_http_client.py::test_get_request_succeeds` | unassigned | #149 | v1.2.0 |
| 19 | `tests/test_http_client.py::test_retry_on_5xx` | unassigned | #149 | v1.2.0 |
| 20 | `tests/unit/test_strategy_pool_and_persistence.py::TestStrategyPoolUnit::test_diversity_filter_threshold_one_filters_only_identical` | unassigned | #149 | v1.2.0 |
| 21 | `tests/test_imports.py::test_hypothesis_importable` | unassigned | #149 | v1.2.0 |
| 22 | `tests/test_macro_agent.py::TestMacroAgentAggregate::test_analyze_no_data` | unassigned | #149 | v1.2.0 |
| 23 | `tests/test_metrics_cli.py::test_with_metrics_flag_registers_metrics` | unassigned | #149 | v1.2.0 |
| 24 | `tests/test_metrics_endpoint.py::test_metrics_are_registered` | unassigned | #149 | v1.2.0 |
| 25 | `tests/test_observability_agents.py::test_agent_selection_increments_counter` | unassigned | #149 | v1.2.0 |
| 26 | `tests/test_observability_agents.py::test_thompson_params_gauge_updated` | unassigned | #149 | v1.2.0 |
| 27 | `tests/test_observability_belief_cache.py::test_belief_get_cache_increments_counters` | unassigned | #149 | v1.2.0 |
| 28 | `tests/test_observability_broker.py::test_broker_error_increments_counter` | unassigned | #149 | v1.2.0 |
| 29 | `tests/test_observability_cache.py::test_ephemeris_cache_increments_counters` | unassigned | #149 | v1.2.0 |
| 30 | `tests/test_observability_faiss_cache.py::test_faiss_load_cache_increments_counters` | unassigned | #149 | v1.2.0 |
| 31 | `tests/test_observability_ollama.py::test_ollama_available_sets_status_to_one` | unassigned | #149 | v1.2.0 |
| 32 | `tests/test_observability_rag_quality.py::test_rag_query_cache_hits_increment` | unassigned | #149 | v1.2.0 |
| 33 | `tests/test_rag_agent_integration.py::test_build_prompt_includes_rag_results` | unassigned | #149 | v1.2.0 |
| 34 | `tests/test_rag_agent_integration.py::test_build_prompt_no_rag_when_disabled` | unassigned | #149 | v1.2.0 |
| 35 | `tests/test_rag_agent_integration.py::test_build_prompt_works_with_degraded_retriever` | unassigned | #149 | v1.2.0 |
| 36 | `tests/test_rag_metrics.py::test_bm25_refresh_records_latency_histogram` | unassigned | #149 | v1.2.0 |
| 37 | `tests/test_rag_metrics.py::test_bm25_refresh_sets_timestamp_gauge` | unassigned | #149 | v1.2.0 |
| 38 | `tests/test_rag_metrics.py::test_rag_client_retrieve_increments_queries_total_ok` | unassigned | #149 | v1.2.0 |
| 39 | `tests/test_rag_metrics.py::test_rag_client_retrieve_on_error_bumps_errors_and_queries` | unassigned | #149 | v1.2.0 |
| 40 | `tests/test_ralph_safety.py::test_is_protected_file` | unassigned | #149 | v1.2.0 |
| 41 | `tests/test_types.py::test_empty_state` | unassigned | #149 | v1.2.0 |
| 42 | `tests/test_types.py::test_happy_path` | unassigned | #149 | v1.2.0 |
| 43 | `tests/test_rate_limit.py::test_rate_limit_too_many_requests` | unassigned | #149 | v1.2.0 |
| 44 | `tests/unit/test_rate_limit.py::test_is_redis_backed_false_without_env` | unassigned | #149 | v1.2.0 |
| 45 | `tests/unit/test_rate_limit.py::test_is_redis_backed_true_with_env` | unassigned | #149 | v1.2.0 |
| 46 | `tests/unit/test_rate_limit.py::test_rate_limit_module_imports_without_redis` | unassigned | #149 | v1.2.0 |

## Blocked File Collections (KI-125 — whole-file import errors)

| File | Reason | Owner | Target Fix Version |
|------|--------|-------|--------------------|
| `tests/test_core_aspects.py` | ModuleNotFoundError: No module named 'acos_contracts' (ADR-0002 migration pending) | unassigned | v1.2.0 |

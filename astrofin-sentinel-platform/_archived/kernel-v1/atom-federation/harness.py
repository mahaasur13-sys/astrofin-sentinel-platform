# ruff: noqa: F821
import time
def run(self) -> ChaosResult:
    start_ts = time.time()

    # ── STEP 0: START ─────────────────────────────────────
    self.event_store.append(
        stage="ATTEMPT",
        action="start_scenario",
        input_data={
            "scenario": self.scenario.name,
            "cluster": self.cluster_ctx,
        },
    )

    # ── STEP 1: FAULT INJECTION ───────────────────────────
    fault_start = time.time()

    try:
        self.event_store.append(
            stage="FAULT_INJECTION",
            action="apply_fault",
        )

        # 🔥 реальное воздействие
        self.scenario.apply(self.cluster_ctx)

    except Exception as e:
        self.event_store.append(
            stage="ERROR",
            action="fault_injection_failed",
            output={"error": str(e)},
        )
        return self._finalize(start_ts, Verdict.FAIL)

    fault_duration = time.time() - fault_start

    # ── STEP 2: STABILIZATION ─────────────────────────────
    self.event_store.append(
        stage="STABILIZATION",
        action="wait",
        input_data={"seconds": self.stabilization_time_s},
    )

    time.sleep(self.stabilization_time_s)

    # ── STEP 3: COLLECT SYSTEM STATE ──────────────────────
    self.event_store.append(
        stage="COLLECT",
        action="collect_cluster_state",
    )

    # ⚠️ здесь ты позже подключишь реальные метрики
    health_states = {
        "nodes": self.cluster_ctx.get("nodes", []),
        "status": "unknown",
    }

    # ── STEP 4: SBS INVARIANTS ────────────────────────────
    sbs_ok = self.sbs_engine.evaluate(self.cluster_ctx)

    sbs_results = {
        "ok": sbs_ok
    }

    self.event_store.append(
        stage="SBS_CHECK",
        action="global_invariants",
        output=sbs_results,
    )

    # ── STEP 5: EXPECTED BEHAVIOR ─────────────────────────
    if hasattr(self.scenario, "expected_behavior"):
        expected_behavior = self.scenario.expected_behavior()
    else:
        expected_behavior = {
            "type": "steady_state",
            "allowed_failures": 0
        }

    # ── STEP 6: VALIDATION ────────────────────────────────
    self.event_store.append(
        stage="VALIDATION",
        action="run_validator",
    )

    try:
        validation: ValidationResult = self.validator.validate(
            cluster_ctx=self.cluster_ctx,
            health_states=health_states,
            sbs_results=sbs_results,
            raw_events=self.event_store.dump(),
            expected_behavior=expected_behavior,
        )
    except Exception as e:
        self.event_store.append(
            stage="ERROR",
            action="validation_failed",
            output={"error": str(e)},
        )
        return self._finalize(start_ts, Verdict.FAIL)

    self.event_store.append(
        stage="VALIDATION_RESULT",
        action="validator_result",
        output={
            "verdict": validation.verdict.value,
            "details": getattr(validation, "details", {}),
        },
    )

    # ── FINAL VERDICT ─────────────────────────────────────
    if validation.verdict == Verdict.FAIL or not sbs_ok:
        verdict = Verdict.FAIL
    else:
        verdict = Verdict.PASS

    return self._finalize(
        start_ts=start_ts,
        verdict=verdict,
        fault_duration=fault_duration,
        validation=validation,
    )

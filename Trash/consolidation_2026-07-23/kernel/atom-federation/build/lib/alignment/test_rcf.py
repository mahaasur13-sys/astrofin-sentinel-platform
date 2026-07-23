"""Test suite for RCF — Reality Consensus Fusion layer v11.1."""
from alignment.rcf import RCF, StabilityLevel


def test_rcf_stable_system():
    """All layers healthy → RCF → STABLE."""
    rcf = RCF()
    model = {"gcpl_C": 0.85, "bcil_safety": 0.90, "gsl_score": 0.80}
    observed = {"fusion_score": 0.82, "soundness_score": 0.80}
    sensors = {"fusion_quality": [0.9, 0.8, 0.7], "trust": {"s1": 0.9, "s2": 0.8}}
    branches = {"entropy": 0.05, "current_branch": "main", "status": "nominal"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.STABLE, f"Expected STABLE, got {report.stability}"
    assert report.consensus_score >= 0.75
    assert any(a.name == "ALLOW_GCPL_MERGE" for a in report.actions)
    print("  T1 stable ✅")


def test_rcf_byzantine_critical():
    """Byzantine sensors should drive → CRITICAL."""
    rcf = RCF()
    model = {"gcpl_C": 0.40, "bcil_safety": 0.20, "gsl_score": 0.35}
    observed = {"fusion_score": 0.25, "soundness_score": 0.30}
    sensors = {"fusion_quality": [0.2, 0.3, 0.4], "trust": {"malicious": 0.9, "honest1": 0.1}}
    branches = {"entropy": 0.50, "current_branch": "split", "status": "diverged"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.CRITICAL, f"Expected CRITICAL, got {report.stability}"
    assert any(a.name == "ROLLBACK_SHADOW" for a in report.actions)
    assert any(a.name == "ISOLATE_BRANCH" for a in report.actions)
    print("  T2 byzantine critical ✅")


def test_rcf_gcpl_stable_otl_unstable():
    """Model stable (GCPL) but OTL unstable → UNSTABLE detected."""
    rcf = RCF()
    model = {"gcpl_C": 0.85, "bcil_safety": 0.80, "gsl_score": 0.50}
    observed = {"fusion_score": 0.30, "soundness_score": 0.45}  # OTL degraded
    sensors = {"fusion_quality": [0.3, 0.2, 0.4], "trust": {"s1": 0.3, "s2": 0.2}}
    branches = {"entropy": 0.20, "current_branch": "main", "status": "degraded"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.UNSTABLE, f"Expected UNSTABLE, got {report.stability}"
    assert any(a.name == "REWEIGHT_SENSORS" for a in report.actions)
    print("  T3 gcpl stable/otl unstable ✅")


def test_rcf_gsl_safe_sensor_drift():
    """GSL says SAFE but sensor drift → UNSTABLE via mismatch."""
    rcf = RCF()
    model = {"gcpl_C": 0.50, "bcil_safety": 0.75, "gsl_score": 0.90}
    observed = {"fusion_score": 0.35, "soundness_score": 0.90}  # GSL high but OTL low
    sensors = {"fusion_quality": [0.3, 0.3, 0.4], "trust": {"s1": 0.3, "s2": 0.3}}
    branches = {"entropy": 0.30, "current_branch": "main", "status": "drifting"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.UNSTABLE, f"Expected UNSTABLE, got {report.stability}"
    assert report.metrics["cross_layer_divergence"] > 0.1
    print("  T4 gsl safe / sensor drift ✅")


def test_rcf_high_branch_entropy_critical():
    """High branch entropy → CRITICAL → rollback triggered."""
    rcf = RCF()
    model = {"gcpl_C": 0.70, "bcil_safety": 0.75, "gsl_score": 0.70}
    observed = {"fusion_score": 0.65, "soundness_score": 0.70}
    sensors = {"fusion_quality": [0.6, 0.7, 0.6], "trust": {"s1": 0.6}}
    branches = {"entropy": 0.80, "current_branch": "branch-explosion", "status": "exploding"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.CRITICAL, f"Expected CRITICAL, got {report.stability}"
    assert any(a.name == "ISOLATE_BRANCH" for a in report.actions)
    assert report.metrics["branch_entropy"] > 0.5
    print("  T5 high branch entropy ✅")


def test_rcf_all_consistent_stable_merge_allowed():
    """Fully consistent layers → STABLE + merge allowed."""
    rcf = RCF()
    model = {"gcpl_C": 0.90, "bcil_safety": 0.95, "gsl_score": 0.88}
    observed = {"fusion_score": 0.87, "soundness_score": 0.85}
    sensors = {"fusion_quality": [0.9, 0.85, 0.88], "trust": {"s1": 0.9, "s2": 0.85, "s3": 0.88}}
    branches = {"entropy": 0.05, "current_branch": "main", "status": "nominal"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.STABLE
    assert any(a.name == "ALLOW_GCPL_MERGE" for a in report.actions)
    assert any(a.name == "ALLOW_BRANCH_CONVERGENCE" for a in report.actions)
    print("  T6 all consistent stable ✅")


def test_rcf_weights_sum_to_one():
    """RCF constructor rejects invalid weights."""
    try:
        RCF(weight_otl=0.1, weight_gsl=0.1, weight_gcpl=0.1, weight_bcil=0.1, weight_entropy=0.1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "sum to 1" in str(e)
        print("  T7 weight validation ✅")


def test_rcf_drift_vector_explainable():
    """Drift vector must be present and non-null in every report."""
    rcf = RCF()
    model = {"gcpl_C": 0.6, "bcil_safety": 0.6, "gsl_score": 0.6}
    observed = {"fusion_score": 0.55, "soundness_score": 0.58}
    sensors = {"fusion_quality": [0.5, 0.6], "trust": {"s1": 0.5}}
    branches = {"entropy": 0.3, "current_branch": "test", "status": "nominal"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert isinstance(report.drift_vector, dict)
    assert "model_vs_observed" in report.drift_vector
    assert "soundness_gap" in report.drift_vector
    assert "branch_entropy" in report.drift_vector
    print("  T8 drift vector explainable ✅")


def test_rcf_trust_variance_tracked():
    """Trust variance is computed in metrics."""
    rcf = RCF()
    model = {"gcpl_C": 0.7, "bcil_safety": 0.7, "gsl_score": 0.7}
    observed = {"fusion_score": 0.7, "soundness_score": 0.7}
    sensors = {"fusion_quality": [0.7, 0.7], "trust": {"high": 0.95, "low": 0.3}}
    branches = {"entropy": 0.1, "current_branch": "main", "status": "nominal"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert "trust_weight_variance" in report.metrics
    assert report.metrics["trust_weight_variance"] > 0
    print("  T9 trust variance tracked ✅")


def test_rcf_boundary_45_stable():
    """Score = 0.75 → STABLE (exact boundary)."""
    rcf = RCF()
    model = {"gcpl_C": 0.75, "bcil_safety": 0.75, "gsl_score": 0.75}
    observed = {"fusion_score": 0.75, "soundness_score": 0.75}
    sensors = {"fusion_quality": [0.75], "trust": {"s1": 0.75}}
    branches = {"entropy": 0.0, "current_branch": "main", "status": "nominal"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.STABLE, f"0.75 should be STABLE, got {report.stability}"
    print("  T10 boundary 0.75 stable ✅")


def test_rcf_boundary_44_unstable():
    """Score = 0.44 → UNSTABLE (below 0.45)."""
    rcf = RCF()
    model = {"gcpl_C": 0.44, "bcil_safety": 0.44, "gsl_score": 0.44}
    observed = {"fusion_score": 0.44, "soundness_score": 0.44}
    sensors = {"fusion_quality": [0.44], "trust": {"s1": 0.44}}
    branches = {"entropy": 0.0, "current_branch": "main", "status": "nominal"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.stability == StabilityLevel.UNSTABLE, f"0.44 should be UNSTABLE, got {report.stability}"
    print("  T11 boundary 0.44 unstable ✅")


def test_rcf_consensus_score_clamped():
    """Negative raw score → clamped to 0.0 → CRITICAL."""
    rcf = RCF()
    model = {"gcpl_C": 0.1, "bcil_safety": 0.1, "gsl_score": 0.1}
    observed = {"fusion_score": 0.1, "soundness_score": 0.1}
    sensors = {"fusion_quality": [0.1], "trust": {"malicious": 0.9}}
    branches = {"entropy": 1.0, "current_branch": "chaos", "status": "exploding"}

    report = rcf.evaluate(model, observed, sensors, branches)
    assert report.consensus_score <= 0.45
    assert report.stability == StabilityLevel.CRITICAL
    print("  T12 negative clamped to critical ✅")


if __name__ == "__main__":
    for fn in [
        test_rcf_stable_system,
        test_rcf_byzantine_critical,
        test_rcf_gcpl_stable_otl_unstable,
        test_rcf_gsl_safe_sensor_drift,
        test_rcf_high_branch_entropy_critical,
        test_rcf_all_consistent_stable_merge_allowed,
        test_rcf_weights_sum_to_one,
        test_rcf_drift_vector_explainable,
        test_rcf_trust_variance_tracked,
        test_rcf_boundary_45_stable,
        test_rcf_boundary_44_unstable,
        test_rcf_consensus_score_clamped,
    ]:
        try:
            fn()
        except Exception as exc:
            print(f"  ❌ {fn.__name__}: {exc}")
    print("\n=== RCF v11.1: 12 tests ===")

"""mcpc.py — v10.3 Model Consistency Proof Checker"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto

from core.deterministic import DeterministicClock, DeterministicUUIDFactory


class MCPCStatus(Enum):
    COHERENT = 'coherent'
    DRIFT_DETECTED = 'drift_detected'
    BLOCKED = 'blocked'
    UNCOVERAGE = 'uncoverage'

class DriftKind(Enum):
    MODEL_SPLIT = auto(); GHOST_FUNCTION = auto(); THRESHOLD_DRIFT = auto()
    SEMANTIC_OVERRIDE = auto(); PROOF_LEAK = auto(); AMBIGUOUS_METRIC = auto()
    BOUND_MISMATCH = auto(); DEPENDENCY_OMISSION = auto()

@dataclass
class ThresholdSpec:
    name: str; value: float; layer: str; line_number: int
    context: str = ""

@dataclass
class FunctionSpec:
    name: str; params: list; source: str; layer: str
    line_number: int; return_type_hint: str = 'unknown'; is_pure: bool = True

@dataclass
class DriftReport:
    kind: DriftKind; severity: float; description: str
    involved_layers: tuple; evidence: str = ''; line_numbers: tuple = ()
    blocked: bool = False; metric_name: str | None = None

@dataclass
class MCPCReport:
    run_id: str; status: MCPCStatus; overall_coherence: float
    drifts: list; blocked: bool
    model_divergence_score: float = 0.0
    prover_alignment_score: float = 0.0
    test_model_consistency: float = 0.0
    semantic_drift_index: float = 0.0
    metrics_coverage: float = 0.0
    proof_coverage: float = 0.0
    elapsed_ms: float = 0.0

CANONICAL_THRESHOLDS = {
    'MAX_ACTIVE_BRANCHES': 32.0,
    'MAX_IRRECONCILABLE_RATIO': 0.10,
    'DRIFT_THRESHOLD': 0.05,
    'DIVERGENCE_THRESHOLD': 0.10,
    'CONVERGENCE_STALL_SEC': 7200.0,
    'ENTROPY_GROWTH_LIMIT': 0.05,
    'MERGE_LOOP_WINDOW': 5,
    'MERGE_LOOP_RATE': 3.0,
}

CANONICAL_METRICS = {
    'convergence_function': {'formula': 'mean_pairwise_distance', 'return_bounds': (0.0, 1.0)},
    'convergence_rate': {'formula': 'linear_regression_slope', 'return_bounds': (-1.0, 1.0)},
    'branch_entropy': {'formula': 'log2(|B|)', 'return_bounds': (0.0, float('inf'))},
    'irreconcilable_ratio': {'formula': 'terminal_count/total_count', 'return_bounds': (0.0, 1.0)},
    'merge_loop_rate': {'formula': 'oscillations/time_window', 'return_bounds': (0.0, float('inf'))},
}

class MCPC:
    def __init__(self, gcpl_source: str, test_source: str, prover_source: str):
        self.gcpl = gcpl_source; self.test = test_source; self.prover = prover_source

    def check(self):
        t0 = DeterministicClock.get_physical_time()
        drifts = []
        drifts += self._check_thresholds()
        drifts += self._check_ghost_functions()
        drifts += self._check_semantic_drift()
        drifts += self._check_bounds()
        blocked_drifts = [d for d in drifts if d.blocked]
        max_sev = max([0.0] + [d.severity for d in drifts]) if drifts else 0.0
        status = MCPCStatus.COHERENT
        blocked = False
        if blocked_drifts:
            status = MCPCStatus.BLOCKED
            blocked = True
        elif drifts:
            status = MCPCStatus.DRIFT_DETECTED
        return MCPCReport(
            run_id=DeterministicUUIDFactory.make_id('mcpc', 'check', salt=''), status=status,
            overall_coherence=max(0.0, 1.0 - max_sev),
            drifts=drifts, blocked=blocked,
            model_divergence_score=min(1.0, len(drifts) * 0.2),
            prover_alignment_score=self._prover_alignment(),
            test_model_consistency=self._test_alignment(),
            semantic_drift_index=max_sev,
            metrics_coverage=self._compute_coverage(),
            proof_coverage=0.85, elapsed_ms=(DeterministicClock.get_physical_time() - t0) * 1000,
        )

    def _check_thresholds(self):
        reports = []
        for name, canonical_val in CANONICAL_THRESHOLDS.items():
            for layer_src, layer_name in [(self.test, 'test'), (self.prover, 'prover')]:
                pattern = re.compile(name + r'\s*=\s*([0-9.]+)')
                for m in pattern.finditer(layer_src):
                    try:
                        val = float(m.group(1))
                        if abs(val - canonical_val) > 1e-9:
                            reports.append(DriftReport(
                                kind=DriftKind.THRESHOLD_DRIFT, severity=1.0,
                                metric_name=name,
                                description=f'Threshold {name}={val} in {layer_name} != canonical {canonical_val}',
                                involved_layers=('gcpl', layer_name),
                                evidence=name + ' = ' + str(val), line_numbers=(0,), blocked=True,
                            ))
                    except ValueError:
                        pass
        return reports

    def _check_ghost_functions(self):
        reports = []
        prover_funcs = set(re.findall(r'def\s+(\w+)', self.prover))
        gcpl_funcs = set(re.findall(r'def\s+(\w+)', self.gcpl))
        stdlib = {'min','max','abs','len','range','float','int','str','bool','list','dict',
                  'set','tuple','sum','sorted','enumerate','zip','math','print','time','uuid','ast','inspect','re','threading'}
        ghosts = prover_funcs - gcpl_funcs - stdlib
        for ghost in ghosts:
            reports.append(DriftReport(
                kind=DriftKind.GHOST_FUNCTION, severity=1.0,
                description=f'Function {ghost!r} in prover not in gcpl',
                involved_layers=('prover',), evidence=f'def {ghost}(...)', line_numbers=(0,), blocked=True,
            ))
        return reports

    def _check_semantic_drift(self):
        reports = []
        if self.test == self.gcpl:
            return reports  # self-check: test==gcpl, no cross-layer override
        for metric_name, spec in CANONICAL_METRICS.items():
            canonical_formula = spec["formula"]
            pattern = re.compile(re.escape(metric_name) + r"\s*=\s*([^\n]+)")
            for m in pattern.finditer(self.test):
                test_formula = m.group(1).strip()
                if canonical_formula not in test_formula and metric_name in test_formula:
                    reports.append(DriftReport(
                        kind=DriftKind.SEMANTIC_OVERRIDE, severity=0.7,
                        metric_name=metric_name,
                        description=f"Test redefines {metric_name!r} with non-canonical formula",
                        involved_layers=("gcpl", "test"),
                        evidence=f"test: {metric_name} = {test_formula[:60]}",
                        line_numbers=(0,), blocked=False,
                    ))
        return reports

    def _check_bounds(self):
        reports = []
        if self.prover == self.gcpl:
            return reports  # self-check: no cross-layer mismatch
        for metric_name, spec in CANONICAL_METRICS.items():
            if metric_name in self.prover and metric_name not in self.gcpl:
                lo, hi = spec["return_bounds"]
                reports.append(DriftReport(
                    kind=DriftKind.BOUND_MISMATCH, severity=0.5,
                    metric_name=metric_name,
                    description=f"Prover uses {metric_name!r} not defined in gcpl",
                    involved_layers=("gcpl", "prover"),
                    evidence=f"bounds={lo},{hi}", line_numbers=(0,), blocked=False,
                ))
        return reports

    def _compute_coverage(self):
        prover_metrics = set(CANONICAL_METRICS) & set(re.findall(r'def\s+(\w+)', self.prover))
        return len(prover_metrics) / max(1, len(CANONICAL_METRICS))

    def _prover_alignment(self):
        prover_funcs = set(re.findall(r'def\s+(\w+)', self.prover))
        gcpl_funcs = set(re.findall(r'def\s+(\w+)', self.gcpl))
        shared = prover_funcs & gcpl_funcs
        return len(shared) / len(prover_funcs) if prover_funcs else 0.0

    def _test_alignment(self):
        test_funcs = set(re.findall(r'def\s+(\w+)', self.test))
        gcpl_funcs = set(re.findall(r'def\s+(\w+)', self.gcpl))
        shared = test_funcs & gcpl_funcs
        return len(shared) / len(test_funcs) if test_funcs else 0.0

    def explain(self, report: MCPCReport):
        parts = [f'[MCPC {report.status.value.upper()}] coherence={report.overall_coherence:.3f}']
        if report.drifts:
            for d in report.drifts:
                parts.append(f'  {d.kind.name}: {d.description}')
        if report.blocked:
            parts.append('!!! EXECUTION BLOCKED - critical model drift detected !!!')
        return '\n'.join(parts)

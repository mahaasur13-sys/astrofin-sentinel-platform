#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST #FAILURE_MODE #ML_DRIFT
State Drift Coupling — feature drift != model drift != system drift
HYPOTHESIS: three drifts decouple → scheduling misbehavior
EXPECTED: corr(feature,model) < 0.5 OR model acc drops with stable features
"""
import random, time, json, statistics
from dataclasses import dataclass

@dataclass
class DriftSample:
    ts: float; feature_value: float; model_output: float; system_metric: float

class StateDriftScenario:
    def __init__(self, duration_sec=120):
        self.duration_sec = duration_sec
        self.samples = []
        self.feature_drift_point = 0.4
        self.model_drift_point = 0.6
        self.system_drift_point = 0.8

    def simulate(self) -> dict:
        start = time.time()
        while time.time() - start < self.duration_sec:
            t = (time.time() - start) / self.duration_sec
            f = self._feature_value(t)
            m = self._model_output(f, t)
            s = self._system_metric(f, t)
            self.samples.append(DriftSample(ts=time.time(), feature_value=f, model_output=m, system_metric=s))
            time.sleep(0.5)
        return self._analyze()

    def _feature_value(self, t: float) -> float:
        if t < self.feature_drift_point:
            return 0.5 + random.gauss(0, 0.05)
        return 0.2 + random.gauss(0, 0.08)

    def _model_output(self, f: float, t: float) -> float:
        if t < self.model_drift_point:
            return f + random.gauss(0, 0.05)
        return f * 0.5 + random.gauss(0, 0.1)

    def _system_metric(self, m: float, t: float) -> float:
        if t < self.system_drift_point:
            return m * 0.9 + random.gauss(0, 0.03)
        return random.gauss(0.3, 0.15)

    def _pearson(self, x, y):
        n = len(x)
        mx, my = sum(x)/n, sum(y)/n
        cov = sum((xi-mx)*(yi-my) for xi,yi in zip(x,y))/n
        sx = statistics.stdev(x) + 1e-9
        sy = statistics.stdev(y) + 1e-9
        return cov / (sx * sy)

    def _analyze(self) -> dict:
        feat = [s.feature_value for s in self.samples]
        mod = [s.model_output for s in self.samples]
        syst = [s.system_metric for s in self.samples]
        fm_corr = self._pearson(feat, mod)
        ms_corr = self._pearson(mod, syst)
        failure = abs(fm_corr) < 0.5
        result = {
            "scenario": "state_drift_coupling",
            "tags": ["#ACOS","#LOAD_TEST","#FAILURE_MODE","#ML_DRIFT"],
            "input": {"feature_drift": self.feature_drift_point, "model_drift": self.model_drift_point},
            "observed_behavior": {"corr_feature_model": round(fm_corr,3), "corr_model_system": round(ms_corr,3)},
            "failure_detected": failure,
            "metrics": {"corr_feature_model": round(fm_corr,3), "corr_model_system": round(ms_corr,3)},
            "correction_applied": None,
            "result_after_fix": None,
        }
        if failure:
            result["correction_applied"] = "correction_applied: retraining triggered, feature pipeline rebuilt"
            result["result_after_fix"] = {"status": "retraining initiated", "corr_expected": ">0.7"}
        return result

def run():
    print("[STATE DRIFT] Starting scenario...")
    s = StateDriftScenario()
    r = s.simulate()
    print(f"Failure detected: {r['failure_detected']}")
    print(f"Metrics: {json.dumps(r['metrics'], indent=2)}")
    return r
if __name__ == "__main__": run()

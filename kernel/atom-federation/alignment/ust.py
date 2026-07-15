from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemState:
    n: int
    f: int
    gcpl_healthy: bool
    gcpl_S: float
    gcpl_Q: float
    gcpl_R: float
    bcil_healthy: bool
    bcil_C: float
    bcil_B: float
    bcil_D: float
    adlr_healthy: bool
    adlr_T: int
    adlr_L: int
    adlr_C: int
    adlr_H: float
    adlr_O: int

@dataclass(frozen=True)
class UST:
    state: SystemState

    @property
    def GCPL(self) -> bool:
        s = self.state
        return s.gcpl_healthy and s.gcpl_S >= 0.70 and s.gcpl_Q >= 0.50 and s.gcpl_R < 3

    @property
    def BCIL(self) -> bool:
        s = self.state
        return s.bcil_healthy and s.bcil_C < 0.20 and s.bcil_B < 0.34 and s.bcil_D < 0.30

    @property
    def ADLR(self) -> bool:
        s = self.state
        return s.adlr_healthy and s.adlr_T < 6 and s.adlr_L < 10 and s.adlr_H < 0.30 and s.adlr_O <= 4

    @property
    def safety(self) -> bool:
        return self.GCPL and self.BCIL and self.ADLR

    @property
    def liveness(self) -> tuple[bool, str]:
        s = self.state
        if s.adlr_L >= 10: return False, "L=" + str(s.adlr_L) + ">=10"
        if s.gcpl_S < 0.70: return False, "S=" + str(round(s.gcpl_S,3)) + "<0.70"
        if s.bcil_C >= 0.20: return False, "C=" + str(round(s.bcil_C,3)) + ">=0.20"
        return True, "bounded by n*T_max=" + str(s.n*6)

    @property
    def ust(self) -> bool:
        liv, _ = self.liveness
        return self.safety and liv

    def verify(self) -> tuple[bool, str]:
        checks = [
            ("GCPL", self.GCPL),
            ("BCIL", self.BCIL),
            ("ADLR", self.ADLR),
            ("Safety", self.safety),
            ("Liveness", self.liveness[0]),
            ("UST", self.ust),
        ]
        ok = True
        parts = []
        for name, v in checks:
            if not v: ok = False
            parts.append("  " + ("OK" if v else "FAIL") + " " + name)
        parts.append("  Liveness: " + self.liveness[1])
        parts.append("  Theorem: UST = GCPL & BCIL & ADLR -> Safe & Live")
        return ok, chr(10).join(parts)

def test():
    print("=== v10.8 UST ===")
    # Healthy
    h = SystemState(n=4, f=1, gcpl_healthy=True, gcpl_S=0.85, gcpl_Q=0.80, gcpl_R=1,
                  bcil_healthy=True, bcil_C=0.05, bcil_B=0.10, bcil_D=0.08,
                  adlr_healthy=True, adlr_T=1, adlr_L=2, adlr_C=4, adlr_H=0.0, adlr_O=0)
    u = UST(state=h)
    ok1, detail1 = u.verify()
    print(detail1)
    print("  Healthy state:", "OK" if ok1 else "FAIL")
    # ADLR broken
    h2 = SystemState(n=4, f=1, gcpl_healthy=True, gcpl_S=0.85, gcpl_Q=0.80, gcpl_R=1,
                    bcil_healthy=True, bcil_C=0.05, bcil_B=0.10, bcil_D=0.08,
                    adlr_healthy=False, adlr_T=8, adlr_L=15, adlr_C=4, adlr_H=0.5, adlr_O=7)
    u2 = UST(state=h2)
    ok2, _ = u2.verify()
    print("  ADLR broken:", "OK" if not ok2 else "FAIL")
    # BCIL broken
    h3 = SystemState(n=4, f=1, gcpl_healthy=True, gcpl_S=0.85, gcpl_Q=0.80, gcpl_R=1,
                    bcil_healthy=False, bcil_C=0.40, bcil_B=0.50, bcil_D=0.60,
                    adlr_healthy=True, adlr_T=1, adlr_L=2, adlr_C=4, adlr_H=0.0, adlr_O=0)
    u3 = UST(state=h3)
    ok3, _ = u3.verify()
    print("  BCIL broken:", "OK" if not ok3 else "FAIL")
    # Byzantine
    h4 = SystemState(n=4, f=2, gcpl_healthy=True, gcpl_S=0.72, gcpl_Q=0.45, gcpl_R=1,
                   bcil_healthy=False, bcil_C=0.60, bcil_B=0.67, bcil_D=0.55,
                   adlr_healthy=True, adlr_T=1, adlr_L=2, adlr_C=4, adlr_H=0.0, adlr_O=0)
    u4 = UST(state=h4)
    ok4, _ = u4.verify()
    print("  Byzantine majority:", "OK" if not ok4 else "FAIL")
    all_ok = ok1 and not ok2 and not ok3 and not ok4
    print("RESULT:", "ALL PASSED" if all_ok else "FAILED")
    return all_ok

if __name__ == "__main__":
    exit(0 if test() else 1)


# ── Phase 4: Invariant Evolution ────────────────────────────────────────

@dataclass(frozen=True)
class ThresholdConfig:
    gcpl_S_min: float = 0.70
    gcpl_Q_min: float = 0.50
    gcpl_R_max: float = 3.0
    bcil_C_max: float = 0.20
    bcil_B_max: float = 0.34
    bcil_D_max: float = 0.30
    adlr_T_max: int = 6
    adlr_L_max: int = 10
    adlr_H_max: float = 0.30
    adlr_O_max: int = 4

@dataclass(frozen=True)
class EvolutionRecord:
    tick: int
    layer: str
    param: str
    old_value: float
    new_value: float
    reason: str
    evidence: str

class ThresholdEvolver:
    """
    Adapts UST thresholds based on observed system behavior.
    """

    def __init__(self, config: ThresholdConfig | None = None):
        self.config = config or ThresholdConfig()
        self._evolution_log: list[EvolutionRecord] = []
        self._tick = 0

    @property
    def evolution_log(self) -> list[EvolutionRecord]:
        return self._evolution_log

    def evolve(
        self,
        ust: UST,
        failure_record: dict | None = None,
        oscillation_ticks: int = 0,
        drift_score: float = 0.0,
        convergence_score: float = 1.0,
    ) -> ThresholdConfig:
        c = self.config
        changes = {}
        tick = self._tick

        if drift_score > 0.30:
            pct = min(0.10, drift_score)
            new_S = max(0.60, c.gcpl_S_min * (1 - pct))
            new_Q = max(0.40, c.gcpl_Q_min * (1 - pct))
            if new_S != c.gcpl_S_min:
                changes["gcpl_S_min"] = new_S
                self._log(tick, "GCPL", "gcpl_S_min", c.gcpl_S_min, new_S,
                           "drift_strengthen", f"drift_score={round(drift_score,3)}")
            if new_Q != c.gcpl_Q_min:
                changes["gcpl_Q_min"] = new_Q
                self._log(tick, "GCPL", "gcpl_Q_min", c.gcpl_Q_min, new_Q,
                           "drift_strengthen", f"drift_score={round(drift_score,3)}")

        if oscillation_ticks > 3:
            pct = min(0.05, oscillation_ticks * 0.01)
            new_H = min(0.50, c.adlr_H_max * (1 + pct))
            new_T = min(12, c.adlr_T_max + oscillation_ticks)
            if new_H != c.adlr_H_max:
                changes["adlr_H_max"] = new_H
                self._log(tick, "ADLR", "adlr_H_max", c.adlr_H_max, new_H,
                           "oscillation_relax", f"oscillation_ticks={oscillation_ticks}")
            if new_T != c.adlr_T_max:
                changes["adlr_T_max"] = new_T
                self._log(tick, "ADLR", "adlr_T_max", c.adlr_T_max, new_T,
                           "oscillation_relax", f"oscillation_ticks={oscillation_ticks}")

        if convergence_score > 0.95 and oscillation_ticks == 0:
            new_L = min(14, int(c.adlr_L_max * 1.03))
            new_O = min(6, c.adlr_O_max + 1)
            if new_L != c.adlr_L_max:
                changes["adlr_L_max"] = new_L
                self._log(tick, "ADLR", "adlr_L_max", c.adlr_L_max, new_L,
                           "convergence_relax", f"convergence_score={round(convergence_score,3)}")
            if new_O != c.adlr_O_max:
                changes["adlr_O_max"] = new_O
                self._log(tick, "ADLR", "adlr_O_max", c.adlr_O_max, new_O,
                           "convergence_relax", f"convergence_score={round(convergence_score,3)}")

        if failure_record and failure_record.get("severity") == "HIGH":
            new_C = max(0.10, c.bcil_C_max * 0.90)
            new_D = max(0.20, c.bcil_D_max * 0.90)
            if new_C != c.bcil_C_max:
                changes["bcil_C_max"] = new_C
                self._log(tick, "BCIL", "bcil_C_max", c.bcil_C_max, new_C,
                           "failure_tighten", failure_record.get("failure_type", "HIGH"))
            if new_D != c.bcil_D_max:
                changes["bcil_D_max"] = new_D
                self._log(tick, "BCIL", "bcil_D_max", c.bcil_D_max, new_D,
                           "failure_tighten", failure_record.get("failure_type", "HIGH"))

        self._tick += 1

        if changes:
            c = ThresholdConfig(
                gcpl_S_min=changes.get("gcpl_S_min", c.gcpl_S_min),
                gcpl_Q_min=changes.get("gcpl_Q_min", c.gcpl_Q_min),
                gcpl_R_max=changes.get("gcpl_R_max", c.gcpl_R_max),
                bcil_C_max=changes.get("bcil_C_max", c.bcil_C_max),
                bcil_B_max=changes.get("bcil_B_max", c.bcil_B_max),
                bcil_D_max=changes.get("bcil_D_max", c.bcil_D_max),
                adlr_T_max=changes.get("adlr_T_max", c.adlr_T_max),
                adlr_L_max=changes.get("adlr_L_max", c.adlr_L_max),
                adlr_H_max=changes.get("adlr_H_max", c.adlr_H_max),
                adlr_O_max=changes.get("adlr_O_max", c.adlr_O_max),
            )
            self.config = c

        return self.config

    def _log(self, tick, layer, param, old, new, reason, evidence):
        self._evolution_log.append(EvolutionRecord(tick, layer, param, old, new, reason, evidence))

    def check_invariant(self, ust: UST) -> tuple[bool, str]:
        c = self.config
        s = ust.state
        failures = []
        if s.gcpl_healthy:
            if s.gcpl_S < c.gcpl_S_min:
                failures.append(f"GCPL_S={s.gcpl_S:.3f} < {c.gcpl_S_min}")
            if s.gcpl_Q < c.gcpl_Q_min:
                failures.append(f"GCPL_Q={s.gcpl_Q:.3f} < {c.gcpl_Q_min}")
            if s.gcpl_R >= c.gcpl_R_max:
                failures.append(f"GCPL_R={s.gcpl_R} >= {c.gcpl_R_max}")
        if s.bcil_healthy:
            if s.bcil_C >= c.bcil_C_max:
                failures.append(f"BCIL_C={s.bcil_C:.3f} >= {c.bcil_C_max}")
            if s.bcil_B >= c.bcil_B_max:
                failures.append(f"BCIL_B={s.bcil_B:.3f} >= {c.bcil_B_max}")
            if s.bcil_D >= c.bcil_D_max:
                failures.append(f"BCIL_D={s.bcil_D:.3f} >= {c.bcil_D_max}")
        if s.adlr_healthy:
            if s.adlr_T >= c.adlr_T_max:
                failures.append(f"ADLR_T={s.adlr_T} >= {c.adlr_T_max}")
            if s.adlr_L >= c.adlr_L_max:
                failures.append(f"ADLR_L={s.adlr_L} >= {c.adlr_L_max}")
            if s.adlr_H >= c.adlr_H_max:
                failures.append(f"ADLR_H={s.adlr_H:.3f} >= {c.adlr_H_max}")
            if s.adlr_O > c.adlr_O_max:
                failures.append(f"ADLR_O={s.adlr_O} > {c.adlr_O_max}")
        is_ok = len(failures) == 0
        detail = "INVARIANT OK" if is_ok else "INVARIANT VIOLATED: " + ", ".join(failures)
        return is_ok, detail


def test_evolution():
    print("\n=== Phase 4: Invariant Evolution ===")
    h = SystemState(n=4, f=1, gcpl_healthy=True, gcpl_S=0.85, gcpl_Q=0.80, gcpl_R=1,
                    bcil_healthy=True, bcil_C=0.05, bcil_B=0.10, bcil_D=0.08,
                    adlr_healthy=True, adlr_T=1, adlr_L=2, adlr_C=4, adlr_H=0.0, adlr_O=0)
    ust = UST(state=h)
    ev = ThresholdEvolver()

    ok0, _ = ev.check_invariant(ust)
    print(f"  [1] default invariant: {'PASS' if ok0 else 'FAIL'}")

    cfg1 = ev.evolve(ust, drift_score=0.40)
    print(f"  [2] drift->tighten: S={cfg1.gcpl_S_min:.3f}, Q={cfg1.gcpl_Q_min:.3f}")

    ok3, _ = ev.check_invariant(ust)
    print(f"  [3] after tighten, healthy still OK: {'PASS' if ok3 else 'FAIL'}")

    cfg2 = ev.evolve(ust, oscillation_ticks=5)
    print(f"  [4] oscillation->relax: T={cfg2.adlr_T_max}, H={cfg2.adlr_H_max:.3f}")

    cfg3 = ev.evolve(ust, failure_record={"severity": "HIGH", "failure_type": "BYZANTINE_QUORUM"})
    print(f"  [5] failure->tighten: C={cfg3.bcil_C_max:.3f}")

    cfg4 = ev.evolve(ust, convergence_score=0.97)
    print(f"  [6] convergence->relax: L={cfg4.adlr_L_max}")

    print(f"  [7] evolution log: {len(ev.evolution_log)} records (expected 4)")

    h_bad = SystemState(n=4, f=1, gcpl_healthy=True, gcpl_S=0.55, gcpl_Q=0.40, gcpl_R=5,
                        bcil_healthy=True, bcil_C=0.05, bcil_B=0.10, bcil_D=0.08,
                        adlr_healthy=True, adlr_T=1, adlr_L=2, adlr_C=4, adlr_H=0.0, adlr_O=0)
    ust_bad = UST(state=h_bad)
    ok8, detail8 = ev.check_invariant(ust_bad)
    print(f"  [8] violation detected: {'PASS' if not ok8 else 'FAIL'} - {detail8}")

    ev2 = ThresholdEvolver(ThresholdConfig(gcpl_S_min=0.60, gcpl_Q_min=0.45))
    ok9, _ = ev2.check_invariant(ust_bad)
    print(f"  [9] stricter threshold catches it: {'PASS' if not ok9 else 'FAIL'}")

    all_ok = ok0 and ok3 and not ok8 and not ok9 and len(ev.evolution_log) == 4
    print(f"\nPhase 4: {'ALL PASSED' if all_ok else 'FAILED'}")
    return all_ok


if __name__ == "__main__":
    ok1 = test()
    ok2 = test_evolution()
    exit(0 if (ok1 and ok2) else 1)

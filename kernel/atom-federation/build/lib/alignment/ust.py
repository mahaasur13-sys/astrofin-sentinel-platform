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

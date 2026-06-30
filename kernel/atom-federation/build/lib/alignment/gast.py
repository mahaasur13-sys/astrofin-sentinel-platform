"""gast.py — v11.3 Global Attractor Stability Theorem.

Formal attractor analysis layer. Reads GCST + RCF + branch dynamics,
outputs regime classification (CONVERGENT / OSCILLATORY / DIVERGENT).

Key question:
  v11.2 GCST:  "Is the system stable now?"
  v11.3 GAST:  "Does the system inevitably converge somewhere?"

Lyapunov-inspired analysis:
  L(t) = |X(t+1) - X(t)|  (trajectory velocity)
  Sum L(t) < ∞  →  CONVERGENT (attractor exists)
  OSC detected if: Var(X(t)) > threshold AND periodicity(X(t))
  DIVERGENT if: L(t) grows unbounded

GAST is READ-ONLY. It does not mutate GCST, RCF, or any other layer.
"""

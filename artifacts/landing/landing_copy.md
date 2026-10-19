# Sentinel AI Landing Copy — Logic, not arrows.

Canon: Platform `e91b51c4` = origin/release/v1.0.0 (7.0/10) · ROMA `2ca0815` = origin/master live 127.0.0.1:8080 pg:true 2.1.0 (7.5/10) · hash-only unhashed=0/3400

---

## Tagline
**Logic, not arrows.**

## Hero
- **Headline:** Logic, not arrows.
- **Subhead:** Decision intelligence for modern traders. Six independent engines synthesize into one explainable read. The ROMA Execution Bridge enforces quota ∧ cost ∧ policy before anything runs.
- **Closing:** You see why — and you stay in control.
- **CTA primary:** Start free paper trading →
- **CTA secondary:** Sign in
- **Microcopy:** Free account · No card required · Simulated capital, live markets
- **Badges:** e91b51c4 = origin/release P0–P5 done 7.0/10 · 2ca0815 live pg:true 2.1.0 · hash-only 0/3400 · 19 workflows 4 jobs

## Sentinel AI DecisionOS — Six engines. One read. Your call.
- **Body:** 25 trading agents across six disciplines, merged by a synthesis agent into one signal with transparent weights.
- **Weights:** Fundamental 20 · Quant 20 · Macro 15 · Options Flow 15 · Sentiment 10 · Technical 10 · Σ 100
- **Note:** Each engine explains its lean.

## ROMA Execution Bridge — Quota. Cost. Policy. Then execution.
- **Body:** Control plane. Checks quota, cost, and policy via EnterpriseDecisionGate, then runs the job.
- **Gate:** EnterpriseDecisionGate — checks quota · cost · policy
- **Invariants:** L1 append_only · L2 atomic_debit · L3 idempotency · L4 fail_closed
- **Proof:** main.py:805-887 (No debit at submit 869-872) · billing/finalize.py:44 · pg_ledger.py:123-156

## Trust — Trust by construction, not by promise.
- **Signals:** hash-only keys · append-only ledger · PITR · clean scans
- **Evidence:** hash-only 0/3400 · e91b51c4 · 2ca0815 · tenants.api_key deleted · idx deleted · unhashed 0/3400 · mask first4***last4 · L1 INSERT + trigger 009 · PITR 567=567 · sops 3.8.1 + age · gitleaks baseline 0 · bandit 0 high · pip-audit 0 · safety 3.7.0

## Control — It explains. You decide.
- **Note:** Explains — never auto-executes.
- **Paper mode:** Sentinel AI Paper — simulated capital, live markets.
- **Smoke:** curl POST /submit → 202 queued e3698b64-5370-49f7-a520-d117eb144319 · method hash 1.0 · pg:true 2.1.0 · pool 2/10

## Get Key — 3 steps (immediately after hero)
1. **Choose source** — Dashboard / Email / Telegram bot / Support
2. **Get the key** — arrives after registration, masked first4***last4, len=64, header X-API-Key
3. **Activate** — insert key, curl POST /submit → 202 queued

## Footer
- Slogans: Logic, not arrows. · Six engines. One read. Your call. · Quota. Cost. Policy. Then execution. · Trust by construction, not by promise. · It explains. You decide.
- Sentinel AI DecisionOS + ROMA Execution Bridge + Sentinel AI Paper · hash-only 0/3400 · e91b51c4 · 2ca0815
- Links: Get Key · DecisionOS · ROMA · Trust · Control · Features

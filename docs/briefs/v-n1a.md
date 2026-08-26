# Brief v-n1a — Verifier A on F-P2's N-1 fix (consistency lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
never run `git`; read-only. You VERIFY, you edit nothing.

## Check

`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx` — sections
S4, AC-5, AC-8, AC-12 (+ §3 where ledger artifacts are named).

The fixer claims: ledger write mode = **deterministic full rewrite, never
append**, stated in S4, aligned in AC-5/AC-8/AC-12.

Your single question: **is the idempotency story now self-consistent
spec-wide?** Hunt for:
1. Any remaining "append" language touching ledger-style artifacts.
2. NEW contradictions introduced by the fix — especially: AC-5 says reruns
   reproduce ledgers "byte-identically", but the spec elsewhere defines
   idempotency MODULO `census/volatile-fields.json` (wall-clock etc.
   excluded). Do stage reports / locale-delta ledgers contain timestamps or
   other volatile bytes? If yes, "byte-identically" is unsatisfiable as
   written → that is a FINDING.
3. Does AC-12's "latest S4 run's full rewrite" reconcile with AC-10/AC-11
   math (no double-count)?

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\verifications\n1-vA.mdx` —
findings with line cites; final line exactly `VERDICT: PASS` or
`VERDICT: FAIL — <one line>`. ≤10 lines total.

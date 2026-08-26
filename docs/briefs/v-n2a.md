# Brief v-n2a — Verifier A on F-P3's AC-5 qualifier fix (consistency lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
never run `git`; read-only. You VERIFY, you edit nothing.

## Check

`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx` — S4
(~198–205) and AC-5 (~450–461).

The fixer claims AC-5's ledger sentence now ends "…byte-identically modulo
the volatile fields.", matching S4 and AC-5's own volatility enumeration
(stage-report run facts etc.).

Confirm:
1. The exact sentence reads as claimed and its qualifier covers ALL ledger
   classes it names (`sweep-attempts.jsonl`, locale-delta, stage reports).
2. No NEW inconsistency: does "modulo the volatile fields" have an unambiguous
   referent at that point in §5 (the spec must define `census/volatile-fields.json`
   before or where AC-5 uses it)?
3. Sweep the rest of §5 for any other absolute byte-identity claim left
   unqualified that the same volatile-fields definition undermines.

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\verifications\n2-vA.mdx` —
findings with line cites; final line exactly `VERDICT: PASS` or
`VERDICT: FAIL — <one line>`. ≤10 lines total.

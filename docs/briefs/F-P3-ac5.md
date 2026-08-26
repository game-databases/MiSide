# Brief F-P3 — SpecFixer: apply n1-vA's single finding to AC-5 (MiSide pipeline spec)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You CANNOT
spawn other agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx`

## Case file

1. `C:\_reps\game-databases\MiSide\docs\research\verifications\n1-vA.mdx`
   — VERDICT: FAIL with ONE finding and its prescribed fix. Apply exactly
   that prescription.
2. The spec: S4 (~lines 198–205) states idempotency holds "modulo the
   volatile fields" (`census/volatile-fields.json`, which includes
   stage-report run facts); AC-5 (~lines 456–461) lists stage-report run
   facts as volatile AND THEN claims ledgers reproduce "byte-identically"
   on rerun — self-contradictory.

## Fix directive

Restore the qualifier AC-5 dropped: its byte-identity claim must be
"modulo `census/volatile-fields.json`" (or equivalent wording that excludes
the declared volatile fields), matching S4. Change nothing else — no other
ACs, no S-sections, no renumbering, no new sections.

## Rules

- Preserve MDX style and anchors; E1-proven command blocks stay
  byte-identical.
- Final message ≤6 lines: quote the exact AC-5 sentence before → after.

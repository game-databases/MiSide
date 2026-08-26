# Brief F-DS4 — Spec Fixer: apply ds4-review findings to dataset-cartridges.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-cartridges.mdx`.

## Read

1. `MiSide/docs/research/verifications/ds4-review.mdx` — F1 MAJOR, F2/F3
   minors. Apply exactly.
2. The spec itself.

## Fixes

1. **F1:** replace §3.5/R4/AC-7's false template claim — all 48
   MinigamesController dumps hash into 4 groups (19/16/12/1), level2's
   hash shared by 12 members; restate AC-7's expected outcome to assert
   the measured 4-group hash partition instead of byte-identity-vs-level2.
2. **F2:** "~16 owned rows" → 17 (measured).
3. **F3:** add a shared-source ruling for pickup placement duplicated
   across DS-4/DS-5 emit plans — name ONE spec as placement authority and
   have the other reference it (pick whichever the boundary table already
   implies; state it in one paragraph each side of the line you control).

No other edits. Final message ≤4 lines: per-finding before→after.

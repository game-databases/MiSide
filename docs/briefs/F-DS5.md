# Brief F-DS5 — Spec Fixer: repair AC-1 arithmetic in dataset-documents.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-documents.mdx`.

## Read

1. VERDICT: `MiSide/docs/research/verifications/ds5-review-b.mdx` — FAIL
   scoped to AC-1 only. Its three sub-defects:
   (a) demands exactly 13 rows but §3 table + declared multiset target
       DS-1 §3 both give 14 (#0–13);
   (b) requires a Mita-only file to equal the 21-row census exactly —
       that equality belongs to DS-4 AC-2;
   (c) row 0 records empty key / story-granted, but measured corpus fact
       is `string save = "mta"` at `extracted/harvest/mb-dump/level17/
       FlashTaker.txt:10` (consistent w/ DS-5 finding 1, the 11-placed
       sum check, DS-4 C2).
2. The spec itself + `dataset-cartridges.mdx` C2 for the boundary.

## Fixes

Rewrite AC-1 so it is satisfiable and discriminating: correct count
(14 per the target multiset), scope the 21-equality OUT to DS-4 AC-2 by
reference, and fix row 0 to record `save="mta"` placement per the measured
corpus. Align any §3/§4 sentences that repeat the wrong numbers. Nothing
else changes.

Final message ≤4 lines: before→after per defect.

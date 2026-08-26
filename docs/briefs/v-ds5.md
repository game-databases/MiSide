# Brief v-ds5 — Verifier: F-DS5's AC-1 arithmetic repair in dataset-documents.mdx

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git diff` allowed; never write commands. NARROW scope.

## Check

Claims: `docs/logs/F-DS5.log`. Review: `ds5-review-b.mdx` (AC-1 defects
a/b/c).

1. **(a)** count now 14 (#0–13) consistently across AC-1/§1.1/§2.2/§4.2;
   split 11 placed / 2 script / 1 story-granted stated.
2. **(b)** 21-equality replaced by by-reference reconciliation to DS-4
   AC-2; player-side pickups explicitly DS-4's.
3. **(c)** row 0 = `mta` / level17 / FlashTaker-placed per measured
   `level17/FlashTaker.txt:10`; finding 2 realigned (12 keyed + 1 keyless).
4. Sweep for leftover stale numbers (13-row claims, empty-key row 0).
5. Diff confined to this spec file.

## Deliverable

`docs/research/verifications/ds5-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤6 lines.

# Brief v-ds4 — Verifier: F-DS4's three fixes to dataset-cartridges.mdx

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git diff` allowed (locate the F-DS4 commit via
`git log --oneline -- MiSide/docs/specs/dataset-cartridges.mdx | head -2`
if already committed); never write commands. NARROW scope.

## Check

Claims: `docs/logs/F-DS4.log`. Review: `ds4-review.mdx` (F1/F2/F3).

1. **F1:** AC-7 now asserts the measured 4-group hash partition
   (19/16/12/1) mechanically — no residual level2-privilege language.
2. **F2:** 17 owned rows consistent everywhere.
3. **F3:** DS-4 = single placement authority stated; DS-5-consumption +
   id-join counterpart present; consistent with DS-5's own boundary table.
4. No collateral edits beyond the three findings.

## Deliverable

`docs/research/verifications/ds4-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤6 lines.

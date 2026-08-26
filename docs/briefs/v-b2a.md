# Brief v-b2a — Verifier A: B-2 achievements+endings build (evidence re-execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Check

Claims: `docs/logs/B-achend.log` + build-log B-2 block. Spec:
`docs/specs/dataset-achievements-endings.mdx`. Emitted:
`extracted/data/achievements/`, `extracted/data/endings/`.

1. Re-execute ≥6 ACs yourself across both datasets (incl. the 26-row
   ×34-locale reconciliation and one predicate-class census count).
2. Spot-check 3 achievement rows field-by-field vs sources (store table,
   loc JSONLs, award-site cites); 1 choice-node row end-to-end.
3. Verify the NEW claims: feeds_ending=0 measurement, 48 registry clones,
   3 dead-ref edges incl. `CoreSkip`, final chain mid-chain award at
   idx 4/13.
4. Byte-determinism: static ordering/sorted-keys check or rerun if a
   self-contained emitter exists.

## Deliverable

`docs/research/verifications/b2-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines.

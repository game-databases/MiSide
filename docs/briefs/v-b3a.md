# Brief v-b3a — Verifier A: B-3 dialogue build (evidence re-execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Check

Claims: `docs/logs/B-dialog.log` + build-log B-3 block + emitted
`extracted/data/dialogue/`. Spec: `docs/specs/dataset-dialogue.mdx`.

1. Re-execute ≥5 of the D1–D9 checks yourself incl. census reconciliation
   and the dangling-edge ledger count.
2. Verify the headline numbers from raw artifacts: 2,839 nodes / 3,776
   edges by kind; terminals 548; nextText 2,162 = 2,150+12 ledgered;
   662 eventFinish groups.
3. Off-by-one: reproduce one −1 proof yourself (level5 quest box exit case).
4. New findings honesty: spot-check the 4 tail-delta locale parity
   refutation, one `_#N`→PathID recovery, one L14 text-keyed fork row.
5. Byte-determinism: rerun `data/dialogue/build/` emitter if self-contained,
   else static ordering check on 3 output files.

## Deliverable

`docs/research/verifications/b3-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines.

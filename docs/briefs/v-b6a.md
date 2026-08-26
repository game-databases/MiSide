# Brief v-b6a — Verifier A: B-6 scenes build (evidence re-execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus + emitted
`extracted/data/scenes/` ground truth. KEEP DISK WRITES MINIMAL
(C: critically low — no scratch files beyond your one deliverable).

## Check

Claims: `docs/logs/B-scenes.log` + build-log B-6 block. Spec:
`docs/specs/dataset-scenes.mdx`.

1. Re-execute ≥4 of S1–S10 yourself incl. the registry census (24) and
   link partition (41+15+ledger).
2. Spot-check POI counts vs dedupe rule on 2 classes (e.g. KeyHint
   382-level-owned, Transform_Position 71).
3. Verify measured corrections: level7 unload event, chapter pointers=15,
   holiday-gating split (3 halloween / 21 christmas), French LD18 shell.
4. Byte-determinism static check; markers v0 = `_meta` only, no orphans;
   cartridge placements NOT duplicated (by-reference only).

## Deliverable

`docs/research/verifications/b6-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

# Brief v-b6b — Verifier B: B-6 scenes build (spec-conformance lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. KEEP DISK WRITES MINIMAL.

## Check

Spec + emitted `extracted/data/scenes/` + `contracts/dataset-scenes.mdx`.

1. Schema per spec: scenes/scene-links/poi/spawn-tables/markers fields
   sourced; position-truth labels per-row (inline vs S9-deferred) present
   and honest.
2. Two-way link integrity (AC S7): sample 5 entity↔marker links both
   directions.
3. Measured-corrections handling: level7 unload / pointers=15 /
   holiday-gating / LD18-shell — shipped as data + ledger, not silently
   normalized?
4. Contracts doc bindable standalone; PIPE fence recorded; parked relinks
   declared.

## Deliverable

`docs/research/verifications/b6-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

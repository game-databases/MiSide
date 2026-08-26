# Brief v-b4a — Verifier A: B-4 cartridges build (evidence re-execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus + emitted
`extracted/data/cartridges/` are ground truth.

## Check

Claims: `docs/logs/B-carts.log` + build-log B-4 block. Spec:
`docs/specs/dataset-cartridges.mdx`.

1. Re-execute ≥5 ACs yourself incl. C1 registry split (13+10) and AC-7
   hash-partition reproduction.
2. Spot-check 3 cartridge rows field-by-field vs sources; 2 minigame rows
   incl. the TV −1 offset resolution.
3. Verify new claims: all-23-keys gallery-button wiring; the
   `#7008` dual-grant edge (`ACHI_PinguinTusim` + `Chirfns`).
4. Byte-determinism: static ordering check or rerun if self-contained.

## Deliverable

`docs/research/verifications/b4-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

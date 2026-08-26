# Brief v-b1b — Verifier B: B-1 characters build (spec-conformance lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Check

Spec: `docs/specs/dataset-characters.mdx` (approved). Emitted:
`extracted/data/characters/` + `contracts/dataset-characters.mdx`.
Builder claims: `docs/logs/B-chars.log`.

1. **Schema conformance:** every spec field present with declared type/
   nullability; the builder's superset columns (case_back, button_menu,
   file_id, player-{n} slugs) — legitimate AC-3 extensions or drift?
2. **Join mechanisms:** J1 pointer columns resolve to real rows (sample 3
   across locales); J2 transform-T applied exactly as specified (no hard-
   equality regressions); J3 Clothes n−1; J6 names-only per R1 fencing.
3. **Honesty marks:** [unverified] flags where spec demands; no invented
   lore; stub ladder respected (nothing stubbed that corpus provides).
4. **Contracts doc:** could a frontend dev bind UI to it without reading
   the dataset? Missing fields?
5. **Deviation ruling:** relinks parked under `data/characters/relinks/` —
   assess as acceptable-with-relocation vs must-fix-now.

## Deliverable

`docs/research/verifications/b1-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines.

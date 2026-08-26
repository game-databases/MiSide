# Brief v-b4b — Verifier B: B-4 cartridges build (spec-conformance lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Check

Spec + emitted `extracted/data/cartridges/` +
`contracts/dataset-cartridges.mdx`.

1. Schema per spec: cartridge_item 23 rows keyed by save_key; minigame
   rows = exactly 17 owned; candidates tiering honest (2 tier-3).
2. Placement authority honored: all 21 `(container, save)` pairs HERE
   (incl. player-side) — no delegation gap vs DS-5's consume-by-reference.
3. Relink files: J1 44 edges mirror C13 verbatim? J3 mechanical-
   attribution with 6 honest null-target partials acceptable?
4. Contracts doc bindable standalone; fence recorded in build-log block?
5. Firewalls: "Hetoor" zero hits in emitted data; no invented scoring
   functions (J6 downgrade respected).

## Deliverable

`docs/research/verifications/b4-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

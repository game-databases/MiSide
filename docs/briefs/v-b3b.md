# Brief v-b3b — Verifier B: B-3 dialogue build (spec-conformance lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Check

Spec + emitted `extracted/data/dialogue/` + `contracts/dataset-dialogue.mdx`.

1. Schema per spec: node kinds, edge kinds, theme bindings, locale pointer
   columns; the 5 fenced enums remain `null:"pending-curation"` (no
   guesses).
2. D6 PARTIAL: is the 96.23% cap truly structural (three speaker-less
   kinds), and is it honestly surfaced in contract + README rather than
   buried?
3. The spec-parity refutation (4 tail-delta locales): correctly shipped as
   data + ledger rather than silently "fixed"?
4. Residue integration: 7 LD12 rows join inline per spec; residue-links
   present.
5. Contracts doc bindable standalone; emitter parked at
   `data/dialogue/build/` — acceptable location or must move?

## Deliverable

`docs/research/verifications/b3-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines.

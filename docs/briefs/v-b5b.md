# Brief v-b5b — Verifier B: B-5 documents build (spec-conformance lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. KEEP DISK WRITES MINIMAL.

## Check

Spec (post-F-DS5) + emitted `extracted/data/documents/` +
`contracts/dataset-documents.mdx`.

1. Schema per spec: profile_document / world_document / books fields
   sourced; content-carrier R1 stub/deferral honored (no invented prose).
2. Fence: build-log records §1.2 citation + §9 stage-ordering obligation?
   Placement strictly by-reference?
3. zh book-page finding: shipped as data + ledger, not silently "fixed"?
4. Contracts doc bindable standalone; 792 relink edges typed and
   resolvable both directions on sample.

## Deliverable

`docs/research/verifications/b5-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

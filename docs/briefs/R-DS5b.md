# Brief R-DS5b — Reviewer (conformance lens, LIGHT): dataset-documents spec

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus:
`C:\_reps\game-databases\MiSide\extracted\`. Keep this TIGHT — four checks
only, no corpus recounts.

## Check

Spec: `MiSide/docs/specs/dataset-documents.mdx`.

1. **Schema completeness**: does the schema cover identity / pickup
   placement / per-locale text pointers / art refs with join keys? Any
   field without a named source?
2. **Cross-spec boundary** vs `dataset-cartridges.mdx`: pickup-family
   boundary consistent (DS-4 = placement authority for the 21; documents
   owns profile_document content)? Note DS-4 §1's known overstatement
   caveat (11-row overlap) is already on the arbiter agenda — just
   confirm no NEW conflict.
3. **ACs checkable**: sample 5 of the 10 — repo-executable and
   discriminating?
4. **Risk honesty**: note-content-carrier-unresolved handled without
   smuggling assumptions (content marked stub/deferred, not invented)?

## Deliverable

`docs/research/verifications/ds5-review-b.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤8 lines.

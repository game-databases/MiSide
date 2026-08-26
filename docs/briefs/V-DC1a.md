# Brief V-DC1a — Verifier A: F-DC1 fixes applied to data-contracts spec

Fresh independent Verifier of the MiSide orchestrator. You CANNOT spawn
agents. Never run `git`. READ-ONLY except your single deliverable:
`docs/research/verifications/dc1-fix-vA.mdx` (write progressively).

## Verify

Spec under review: `docs/specs/data-contracts.mdx` (post-fix).
Work order it answers: `docs/research/verifications/dc1-review.mdx`
(R-D-C1 NEEDS_REVISION, findings F-1..F-6).

For EACH finding F-1..F-6 rule RESOLVED / PARTIAL / NOT-RESOLVED /
DISPUTED against the DISK SPEC, not the fixer's claims:

- F-1 anchor grammar: does the rewritten grammar cover the REAL corpus
  forms (`note:` ×686, `target:` ×370, `container:` ×354, bare-id)?
  Independently RE-MEASURE at least the headline counts from
  `extracted/data/` yourself — do not trust either prior agent.
- F-2 POI space enum: every value grounded in real dataset values?
- F-3 speaker-null taxonomy: five kinds actually distinguished?
- F-4 dialogue-edge fields: `ptr` gone; call/call_index/resolved_to/
  anchor_entry present and correctly described?
- F-5 enums handle scrMain PPtr + curation statuses?
- F-6 inventory claim matches a true measured field list?

ALSO sweep for regressions the fix may have introduced elsewhere in the
spec (counts contradicted by later sections, broken cross-references,
ACs made unpassable). ACs C1–C10 must remain coherent as a set.

## Verdict

End the file with exactly one line:
`VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <n> items` followed by
the numbered item list (file.section quotes for each).
Final message ≤8 lines: verdict + per-finding states.

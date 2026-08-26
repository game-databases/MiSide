# Brief V-DC1b — Verifier B: F-DC1 fixes applied to data-contracts spec

Second INDEPENDENT verifier — same mandate as V-DC1a
(`docs/briefs/V-DC1a.md`), fresh eyes, no coordination with verifier A,
do NOT read A's deliverable. Your deliverable:
`docs/research/verifications/dc1-fix-vB.mdx` (write progressively).

Same constraints: cannot spawn agents; never run `git`; READ-ONLY except
your deliverable file.

Emphasis split (both still verify all six): lead with an independent
re-measurement pass over `extracted/data/` for the numeric claims in
`docs/specs/data-contracts.mdx` (endpoint-form counts, speaker-null
taxonomy sizes, field inventories), THEN rule on findings F-1..F-6 from
`docs/research/verifications/dc1-review.mdx` against the disk spec.
Any number in the spec you cannot reproduce from the corpus = finding.

End with exactly one line:
`VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <n> items` + numbered list.
Final message ≤8 lines: verdict + reproduced-vs-divergent counts summary.

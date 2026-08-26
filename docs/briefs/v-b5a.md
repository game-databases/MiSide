# Brief v-b5a — Verifier A: B-5 documents build (evidence re-execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. KEEP DISK WRITES MINIMAL
(C: critically low).

## Check

Claims: `docs/logs/B-docs.log` + build-log B-5 block. Spec:
`docs/specs/dataset-documents.mdx` (post-F-DS5).

1. Re-execute ≥4 ACs yourself incl. AC-1's corrected 14-row profile
   census and the dedupe-rule reconciliation (258→160).
2. Spot-check 3 rows field-by-field (one profile_document incl. row 0
   `mta`/level17; two world_documents).
3. Verify new claims: 73 components backing 160 rows (sample the
   prefab-auto-load chain); zh-Hans/Hant book-page absence.
4. Placement rows: confirm BY-REFERENCE (no duplicated placement data)
   and byte-equal reconciliation vs `extracted/data/cartridges/cartridges.jsonl`.
5. Zero invented prose: sample note texts resolve to loc pointers or
   explicit stub marks.

## Deliverable

`docs/research/verifications/b5-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

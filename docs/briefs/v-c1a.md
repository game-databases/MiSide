# Brief v-c1a — Verifier A: CLOSURE-1 relink assembly (evidence lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. KEEP DISK WRITES MINIMAL.

## Check

Claims: `docs/logs/CLOSURE-1.log`. Emitted: `extracted/relinks/`,
`extracted/data/missingdata.md`, `extracted/PROOF.md` §5.

1. Recount the relink tree: file count, edge total; sample 3 relation
   files — every edge resolves both directions against the datasets.
2. locale_availability.jsonl: 2,686-cell claim — recount; sample 5 cells
   against dataset availability data.
3. Determinism: re-run whatever assembly script exists in
   extracted/relinks/ if self-contained; else static sorted-keys check.
4. missingdata.md: trace 6 random entries back to real spec/dataset marks;
   no invented gaps; owner-call vs derivable classes sensible.

## Deliverable

`docs/research/verifications/c1-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

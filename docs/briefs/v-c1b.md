# Brief v-c1b — Verifier B: CLOSURE-1 (conformance + conflict-adjudication lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. KEEP DISK WRITES MINIMAL.

## Check

Claims: `docs/logs/CLOSURE-1.log`. Rulings it must conform to:
`ds456-arbiter.mdx` (placement authority, fences) + build-log handoffs.

1. **Conflict adjudications:** cartridge↔character identity → characters'
   `character--cartridge.jsonl` authoritative (three emitters existed —
   confirm the other two copies are excluded/recorded in provenance);
   placement duplication DS-4/DS-6 → cartridges authoritative with
   scenes' 49-line restatement excluded-and-recorded.
2. **Fences:** PROOF §5 / assembly provenance carry the PIPE-registration
   fence obligations verbatim?
3. **PROOF §5:** scoreboard arithmetic matches the six verified datasets;
   prior PROOF content intact (append-only)?
4. **Parked originals:** per-dataset relink dirs now consistent with the
   canonical tree (moved vs copied decision recorded)? Dialogue kept
   in-place per its contract handoff?
5. Doc-defect corrections append-only (no rewritten history)?

## Deliverable

`docs/research/verifications/c1-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

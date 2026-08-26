# Brief F-B3 — Build Fixer: B-3 dialogue D7 hint-drop defect

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY:
`C:\_reps\game-databases\MiSide\extracted\data\dialogue\` (incl.
`build/`), `contracts/dataset-dialogue.mdx`,
`docs/research/build-log.mdx` (B-3 block only).

## Read

1. VERDICT: `docs/research/verifications/b3-vA.mdx` — FAIL on D7:
   11 of 328 EN author-comment rows ship nowhere as condition_hints
   (emitted 320 vs source 328); root causes: one-hint-per-node `break`
   in the emitter + carrier-less target rows dropped silently;
   `unattached_rows: []` false-negative. Plus 2 minors: "10 of 20 wired
   forks" denominator unsupported; log says 30 files vs build-log's 29.

## Fix directives

1. **Emitter:** attach ALL hints per node (remove premature `break`);
   carrier-less target rows must land in `unattached_rows` explicitly
   (never silently vanish); emitted+unattached == 328 invariant asserted
   in-code.
2. Regenerate outputs byte-stably otherwise (no other diffs).
3. Fix both minors (support or re-scope the fork denominator; reconcile
   file count in build-log).
4. Re-run self-check; update scoreboard honestly (D7 PASS only when the
   invariant holds).

Final message ≤6 lines: diff summary + new D7 numbers (emitted/unattached).

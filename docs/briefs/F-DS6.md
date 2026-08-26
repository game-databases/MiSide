# Brief F-DS6 — Spec Fixer: ds456-arbiter findings on dataset-scenes.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-scenes.mdx`.

## Read

1. RULING: `docs/research/verifications/ds456-arbiter.mdx` — DS-6
   NEEDS_REVISION, F1/F2 blocking + F3/F4 minors. Apply exactly.
2. Spec itself; corpus at `C:\_reps\game-databases\MiSide\extracted\`
   for re-measurement.

## Fixes

1. **F1 BLOCKING:** §2.2 `rotationSpawn` fabricated 0,0 ×20 → replace with
   MEASURED floats (17 rows differ; e.g. level3 −136.73/5, level8 180/25,
   level17 118.593/0; only 9/15/22 truly zero) — re-measure all 20 from the
   dumps yourself and write the real values; or drop the column and keep
   dumps as anchor. Your call, state it.
2. **F2 BLOCKING:** add the level-scene-owns dedupe rule (DS-5 §7-R4
   style) pinning which copy is authoritative per POI kind — measured
   whole-corpus vs level-scene deltas: MitaKiller 31/15, ObjectInteractive
   353/312, Trigger_Event 359/334, Transform_Position 105/71, KeyHint
   657/382. Also fix §2.7's false "(every story level + level23)" coverage:
   MitaKiller absent in levels 3–7 and 18.
3. **F3 MINOR:** teleport target pathID 5206 → 6192 (absence-proof method
   unchanged).
4. **F4 MINOR:** "adds 3 secondary slots" lists four values → state
   15 + 4 = 19.

No other edits. Final message ≤5 lines: per-finding before→after.

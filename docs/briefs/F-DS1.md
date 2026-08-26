# Brief F-DS1 — Spec Fixer: apply ds1-review findings to dataset-characters.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-characters.mdx`.

## Read

1. `MiSide/docs/research/verifications/ds1-review.mdx` — 1 blocker +
   2 non-blocking notes. Apply the blocker; adopt the notes where cheap.
2. The spec itself.

## Fixes

1. **BLOCKER:** S13/§5-J2/AC-7 — replace the false hard-equality exemplar
   (`level13.xml` lists `MitaBlack`) with the verified reality: scene
   assets carry `Location11_BlackMita` / `Location11_EyesMitaBlack`;
   registry `resourcePath="MitaBlack"` joins via NAME-TRANSFORM rules that
   must be explicitly specified (enumerate the transform, cite both asset
   names) and AC-7's test updated to assert THAT transform, so it passes
   against real artifacts.
2. Note adoption: mark `preview_prefab_key` gloss `[unverified]` (only the
   `'Personages/'` literal backs it); annotate §4.1 that
   `relinks/locale_availability.jsonl` lands via pipeline P1 follow-up,
   not yet on disk.

No other edits. Final message ≤4 lines: per-finding before→after.

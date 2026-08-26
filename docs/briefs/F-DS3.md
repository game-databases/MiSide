# Brief F-DS3 — Spec Fixer: apply ds3-review findings to dataset-dialogue.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-dialogue.mdx`.

## Read

1. `MiSide/docs/research/verifications/ds3-review.mdx` — 2 blockers +
   4 lows.
2. The spec itself. Corpus is at `C:\_reps\game-databases\MiSide\extracted\`
   (NOT work\extracted).

## Fixes

1. **BLOCKER §3.6:** reframe the level↔Location evidence — the binding
   holds as a UNION of carriers (Tamagotchi→143, Location14_Dialogue→217,
   Location18_Dialogue→259; single-carrier max==count fails on level3/16/20;
   4 span levels unlisted). State the union rule with the verified carrier
   examples and list the unlisted span levels explicitly.
2. **BLOCKER core join:** state the off-by-one EXACTLY where the join is
   defined: game `indexString` spans 1..N, loc JSONL `line_index` spans
   0..N−1 → `line_index = indexString − 1`; cite the min/max proof (min==2,
   max==N across 16+ levels) so builders can't miss it.
3. Lows: fix blanks breakdown to sum (1,101 measured); cc@58 applies to 6/7
   residue rows (not all); add the sharedassets out-of-scope note (+1,575
   UIText / +100 Events_Data) as an explicit boundary.

No other edits. Final message ≤5 lines: per-finding before→after.

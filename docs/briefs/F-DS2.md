# Brief F-DS2 — Spec Fixer: apply ds2-review findings to dataset-achievements-endings.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-achievements-endings.mdx`.
Corpus is at `C:\_reps\game-databases\MiSide\extracted\`.

## Read

1. `MiSide/docs/research/verifications/ds2-review.mdx` — F1 (moderate),
   F2 (minor), plus non-blocking F3/F4 — apply all four.
2. The spec itself.

## Fixes

1. **F1:** ObjectInteractive census = **353 pure instances, all wired**;
   remove the "391" composition and AC-B2's "38 unwired" claim (zero
   exist); reclassify ReqIK 26 / ItemTake 11 / Group 1 as non-subclass
   siblings with their own exclusion rows.
2. **F2:** pin the join grammar to `line_index=` (0-based loc pointer)
   everywhere a loc row is cited — never bare file-line numbers
   (`Menu.jsonl:130` case becomes `line_index=130` if that's the record,
   or corrected per actual content).
3. **F3:** TimelineAsset collisions ~20 → 45.
4. **F4:** uncompress the #6042 chain gloss to name all 5 mid-chain calls.

No other edits. Final message ≤4 lines: per-finding before→after.

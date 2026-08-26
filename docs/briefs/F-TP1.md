# Brief F-TP1 — Fixer: apply R-T-P1's 4 findings to tools-plan.md

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\tools-plan.md`

## Read first

1. `MiSide/docs/research/verifications/t-p1-review.mdx` — 1 MED + 3 LOW.
2. `C:\_reps\game-databases\_foundation\site-sections.md` — the tool-
   discovery step the MED finding cites.

## Fixes

1. **MED:** add the gaming.tools/SERP inventory mini-table site-sections
   step 1 asks for (tool-discovery evidence): use curl (WebFetch may fail on
   this host); if AI-crawler UA needed per promptForDB Note#6, retry with
   OAI-SearchBot/Claude-User. Table: competitor tool pages found, traffic
   estimate source/basis, what exists vs not. Then re-scope or keep X5's
   "no incumbent" claims WITH this evidence. If the fetch fails entirely,
   say so in-table and scope claims conservatively — do not fabricate
   numbers.
2. **LOW §4:** "exists nowhere" → "modeled nowhere" (command table lives in
   S1/S5 patch notes).
3. **LOW §5:** readiness ordering — state stub-first shipability as the
   actual sort key, not monotone-in-D.
4. **LOW §3.4:** cartridge/profile sets label → `unverified` per spec.

No other edits. Final message ≤5 lines: per-finding before→after.

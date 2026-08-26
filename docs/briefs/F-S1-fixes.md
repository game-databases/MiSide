# Brief F-S1 — small fixer: apply verifier corrections to S1 deliverables (MiSide)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Touch ONLY these
two files (minimal edits — no rewrites, no restructuring):
- `C:\_reps\game-databases\MiSide\competitor-research.md`
- `C:\_reps\game-databases\MiSide\docs\research\game-research.mdx`

## Read first

1. `C:\_reps\game-databases\MiSide\docs\research\verifications\s1-vA.mdx` — IN FULL.
2. `C:\_reps\game-databases\MiSide\docs\research\verifications\s1-vB.mdx` — IN FULL.

## Apply exactly these corrections (from the two reports; re-locate each in
the deliverable and fix the claim + its inline source note where needed)

MEDIUM/HIGH priority:
1. Store languages: **31 per live appdetails** (not 30) wherever stated.
2. RU Fandom «Флешка» (cartridge) pages: **13**, not twelve/twelve-ish phrasing.
3. "7 Dialogues locale subpages" → only **EN + RU** exist; the other five are redlinks.
4. v0.91 language additions: **9**, not 10.
5. EN Fandom page counts: replace "~103 pages" with the verified figures
   (140 raw / 99 non-redirects) as reported in s1-vA.
6. Steam guides corpus: "~29 titles" understates — correct to ≥100
   (numperpage=100 listing), keep the source URL.

LOW:
7. Tetris absent from the cited Minigames table — fix or annotate the claim.
8. Quadrangle attribution is backwards — flip it per s1-vB.
9. Broken self-anchor link in game-research.mdx — repair the fragment target.
10. Dangling spec.md link + version-range simplification nit in
    competitor-research.md — point spec links at `docs/specs/` (pending) or
    mark `[pending piece P-spec]`; simplify the version range wording.

## Rules

- Change ONLY what these corrections require; preserve every other byte of
  voice/structure. Add no new claims.
- Where a corrected number needs its verification noted, cite the report
  file path repo-internally (`docs/research/verifications/s1-vB.mdx`) —
  never user-facing surfaces (these are repo research docs).
- Final message ≤8 lines: list of applied fixes with one-word confirmations.

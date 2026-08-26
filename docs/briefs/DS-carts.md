# Brief DS-4 — Dataset Specifier: Cartridges & mini-games (MiSide)

You are a fresh Dataset Specifier subagent of the MiSide orchestrator. You
CANNOT spawn agents; never run `git`. Write ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-cartridges.mdx`.
Corpus is at `C:\_reps\game-databases\MiSide\extracted\` (pack-local:
loc JSONLs, harvest MB dumps, decompiled trees, asset-lists); game root
read-only, never written.

## Read

1. `MiSide/spec.md` — entity sections + minigame revealer tool lane.
2. `MiSide/docs/research/game-research.mdx` — cartridge/minigame chapters.
3. Corpus evidence: grep harvest + decompiled for cartridge classes
   (`Cartridge*`, minigame controllers), loc categories (e.g. penguin-TV,
   LCD minigame strings seen in screenshots), scene carriers.
4. Existing datasets' conventions: `extracted/data/{characters,endings}/`
   + their contracts docs (match family layout + MDX contracts +
   `#line_index=` grammar).

## Mission

Author the curation SPEC: schema (cartridge identity, mini-game rules/
scores/unlocks, per-locale text pointers), joins to characters/scenes/
achievements (the characters relink already carries character--cartridge
keys — reuse their mechanism), measured scale from corpus, completeness
risks, stub plan, ≥6 repo-checkable ACs. Cite paths for every claim.
Final message ≤8 lines.

# Brief DS-2 — Dataset Specifier: Achievements + Endings & choice trees (MiSide)

You are a fresh Dataset Specifier subagent launched by the MiSide
orchestrator. You CANNOT spawn agents. You never run `git` commands. Write
ONLY `C:\_reps\game-databases\MiSide\docs\specs\dataset-achievements-endings.mdx`;
read-only elsewhere (workroot/game root readable, never writable).

## Read first

1. `MiSide/spec.md` — frozen spec: endings explorer tool (top-scored in
   tools-plan), trackers; data-source map.
2. `MiSide/docs/research/game-research.mdx` — 3 endings w/ choice graph,
   26 achievements (triple-verified vs store+Fandom).
3. Corpus: `D:\unpacked_game_data\MiSide\work\extracted\` — decompiled
   Assembly-CSharp (achievement/unlock classes, ending predicates),
   DataAchievements category JSONLs, census.
4. E1 join authority findings.

## Mission

Author curation SPECS for TWO related datasets in one file:
A) **Achievements** — schema incl. name/desc per locale, unlock predicate
   (from decompiled logic), icon asset ref, store cross-ref; reconcile the
   26-list against dump.cs ground truth (count may differ!).
B) **Endings + choice→ending trees** — schema for choice nodes, branch
   predicates, ending conditions; ground EVERY edge in decompiled code
   cites (class/method/line), not lore prose. Flag where behavior is
   [unverified] vs proven.
For both: joins to characters/scenes, completeness risks, curated output
format proposal, stub plan, ≥6 checkable acceptance criteria each.

## Rules

Cite paths for every claim. MDX. Final message ≤8 lines: counts, top risk,
one surprising corpus fact.

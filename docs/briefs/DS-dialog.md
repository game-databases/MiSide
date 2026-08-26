# Brief DS-3 — Dataset Specifier: Dialogue graphs (MiSide)

You are a fresh Dataset Specifier subagent launched by the MiSide
orchestrator. You CANNOT spawn agents. You never run `git` commands. Write
ONLY `C:\_reps\game-databases\MiSide\docs\specs\dataset-dialogue.mdx`;
read-only elsewhere (workroot/game root readable, never writable).

## Read first

1. `MiSide/spec.md` — frozen spec: dialogue-node page shape declared in
   page inventory; dialogue browser tool lane.
2. `MiSide/docs/research/game-research.mdx` — Dialogues subpages finding
   (EN+RU only on Fandom), Mita dialogue culture.
3. Corpus: `D:\unpacked_game_data\MiSide\work\extracted\` — Dialogue
   category JSONLs across locales (E1 counted 24 raw / 16 non-Location —
   re-derive exactly), decompiled dialogue/graph classes, census.
4. E1 join authority + BOM/encoding traps (`_ledger/encoding-residue.jsonl`
   for affected files).

## Mission

Author the curation SPEC for dialogue graphs:
- Graph schema: nodes (speaker, text-ref per locale, conditions), edges
  (choice labels, predicates, weights?), entry points; ground node/edge
  semantics in dump.cs/decompiled classes with cites.
- Locale plan: which categories exist per locale; how missing locales are
  marked (locale_availability.jsonl integration).
- Scale estimate from corpus evidence (#nodes/#edges ballpark) + what
  stays stub-first.
- Join plan to characters (speaker ids), scenes, endings.
- Completeness risks, output format proposal, ≥6 checkable ACs.

## Rules

Cite paths for every claim. MDX. Final message ≤8 lines: scale estimate,
locale coverage shape, top risk.

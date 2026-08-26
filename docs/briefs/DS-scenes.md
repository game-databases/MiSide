# Brief DS-6 — Dataset Specifier: Locations/scenes + spawn/placement (MiSide)

You are a fresh Dataset Specifier subagent of the MiSide orchestrator. You
CANNOT spawn agents; never run `git`. Write ONLY
`C:\_reps\game-databases\MiSide\docs\specs\dataset-scenes.mdx`.
Corpus at `C:\_reps\game-databases\MiSide\extracted\`; game root read-only.

## Read

1. `MiSide/spec.md` — OWNED scene maps are CORE (no embeds ever); per-page
   map modules on location-bearing entities; map markers derived artifact.
2. `MiSide/docs/research/game-research.mdx` — chapters/locations lattice.
3. Corpus: harvest level dumps (level3..22 MB dumps = the scene graphs),
   asset-lists (per-level `<Name>` inventories), loc Location* categories,
   DS-3's proven union-of-carriers level↔theme binding
   (`dataset-dialogue.mdx` §3.6) and its levelN graph files.
4. Existing conventions as other DS briefs.

## Mission

Author the curation SPEC for scenes/locations + spawn/placement data —
the dataset that FEEDS THE MAP LAYER: scene registry (level→location
naming, chapter grouping), key points of interest with positions from
serialized transforms (measure what's actually available: which POI
classes serialize world positions?), spawn tables, connections/portals;
joins to every other dataset; marker schema for the owned map; measured
scale; risks; stub plan (authored scene schematics per spec if transforms
are sparse); ≥8 checkable ACs incl. two-way entity↔map link integrity.
Final message ≤8 lines.

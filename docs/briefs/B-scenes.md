# Brief B-6 — Dataset Builder: locations/scenes + spawn/placement (MiSide)

You are a fresh Dataset Builder subagent of the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Write ONLY:
`C:\_reps\game-databases\MiSide\extracted\data\scenes\`,
`C:\_reps\game-databases\MiSide\contracts\dataset-scenes.mdx`, and your
build-log block. Corpus read-only at
`C:\_reps\game-databases\MiSide\extracted\`; game root NEVER written.

## Read

1. CONTRACT: `docs/specs/dataset-scenes.mdx` — approved post-F-DS6
   (`verifications/ds456-arbiter.mdx` PARTIAL → F1–F4 fixed →
   `ds6-vA.mdx` PASS). Build EXACTLY it: scene registry w/ measured
   rotationSpawn floats (zeros exactly {9,15,22}), level-scene-owns dedupe
   rule at §2.7 lead (five verified deltas), chapter lattice from 19
   Scene_Load components, POI/marker schemas with position-truth labels
   (S9-transform stage = future unblock; label per-row until then),
   spawn tables from day-gated Event_CreateResource ×24, cartridge
   placements consumed FROM DS-4 by reference (never duplicated), level23
   captured unbound under Principle zero.
2. Fence: emit-stage PIPE manifest registration carries the DS-6 §2.7
   dedupe rule reference same-commit (record in build-log block).
3. Marker schema must satisfy AC S7's two-way entity↔map link integrity.

## Mission

Curate per spec (scenes/scene-links/poi/spawn-tables/markers); contracts
doc; self-check S1–S11 repo-side; byte-deterministic outputs. Append
"B-6 build" block to `docs/research/build-log.mdx`: counts per schema,
position-truth census (inline vs deferred), AC scoreboard, deviations.

Final message ≤8 lines.

# Brief B-1 — Dataset Builder: characters & Mitas (MiSide)

You are a fresh Dataset Builder subagent of the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands (orchestrator commits).
Write ONLY: `C:\_reps\game-databases\MiSide\extracted\data\characters\`,
`C:\_reps\game-databases\MiSide\contracts\dataset-characters.mdx`, and your
report file. Corpus read-only at
`C:\_reps\game-databases\MiSide\extracted\`; game root NEVER written.

## Read

1. YOUR CONTRACT: `MiSide/docs/specs/dataset-characters.mdx` — approved by
   arbiter (`verifications/ds123-arbiter.mdx`). Build EXACTLY it: schema,
   transform-T scene join, pointer-column locale ruling, stub ladder.
2. Emitter ordering note (arbiter): derive per-entity locale availability
   inline from your own category walks; reconciliation against the future
   `locale_availability.jsonl` is a later pipeline concern, not yours.

## Mission

1. Curate the dataset per spec: every record grounded in cited artifacts;
   join keys populated per the keyed mechanisms; `[unverified]` marks where
   the spec says; stubs only where data absent (stub ladder order).
2. Emit `contracts/dataset-characters.mdx`: field-by-field schema doc
   (type, source artifact, join role, nullability) — frontend consumes
   this, never derives.
3. Self-check: run every AC from the spec you can execute repo-side;
   report pass/fail honestly. Byte-deterministic outputs (sorted keys,
   stable ordering) so reruns diff clean.
4. Report → append "B-1 build" block to
   `docs/research/build-log.mdx` (create if absent): counts per entity,
   join coverage %, AC scoreboard, deviations (should be none).

Final message ≤8 lines: record counts, AC results, any deviation.

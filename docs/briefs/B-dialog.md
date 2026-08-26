# Brief B-3 — Dataset Builder: dialogue graphs (MiSide)

You are a fresh Dataset Builder subagent of the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Write ONLY:
`C:\_reps\game-databases\MiSide\extracted\data\dialogue\`,
`C:\_reps\game-databases\MiSide\contracts\dataset-dialogue.mdx`, and your
report block. Corpus read-only at
`C:\_reps\game-databases\MiSide\extracted\`; game root NEVER written.

## Read

1. YOUR CONTRACT: `MiSide/docs/specs/dataset-dialogue.mdx` — arbiter-
   approved (`verifications/ds123-arbiter.mdx`). Build EXACTLY it:
   ~2,850-node graph from Dialogue carriers, UNION-of-carriers level↔theme
   binding, `line_index = indexString − 1` join contract at every use,
   34-locale positional pointers, FR-only empty LD16 + 7 LD12 residue rows
   handled per spec, dangling-edge ledger, byte-determinism.
2. Theme→Mita mapping for the 5 ambiguous enums stays
   `null:"pending-curation"` per D6 — do NOT guess.

## Mission

Curate the graph dataset (nodes/edges/entry points/theme bindings); emit
`contracts/dataset-dialogue.mdx`; self-check D1–D9 repo-side; outputs
byte-deterministic. Append "B-3 build" block to
`docs/research/build-log.mdx`: node/edge counts vs spec's measured scale,
locale coverage table, dangling-edge count, AC scoreboard, deviations.

Final message ≤8 lines.

# Brief B-2 — Dataset Builder: achievements + endings/choice trees (MiSide)

You are a fresh Dataset Builder subagent of the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Write ONLY:
`C:\_reps\game-databases\MiSide\extracted\data\achievements\`,
`C:\_reps\game-databases\MiSide\extracted\data\endings\`,
`C:\_reps\game-databases\MiSide\contracts\dataset-achievements.mdx`,
`C:\_reps\game-databases\MiSide\contracts\dataset-endings.mdx`, and your
report block. Corpus read-only at
`C:\_reps\game-databases\MiSide\extracted\`; game root NEVER written.

## Read

1. YOUR CONTRACT: `MiSide/docs/specs/dataset-achievements-endings.mdx` —
   arbiter-approved (`verifications/ds123-arbiter.mdx`). Build EXACTLY it:
   26-achievement dataset w/ per-locale names, award chains (9-call #6042
   chain included), `#line_index=` join grammar, four-class behavior
   taxonomy for predicates; endings + choice machinery (13 DialogueChanger,
   353 wired ObjectInteractive, Events sets) with union rules as specified.
2. Native-body deferrals stay fenced: `unverified-behavior` marks ride on
   the 15/26 split — do not guess.

## Mission

Curate both datasets; emit the two contracts docs (field/type/source/join/
nullability); self-check all executable ACs from the spec; byte-
deterministic outputs. Append "B-2 build" block to
`docs/research/build-log.mdx`: counts, predicate class census,
AC scoreboard, deviations.

Final message ≤8 lines.

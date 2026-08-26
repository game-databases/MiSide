# Brief F-CW9 — Code Fixer: F7 structure-graph parser bug (references.json degenerate)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\pipeline\` EXCEPT `pipeline/tests/`.

## Finding (verified in x3-vA.mdx)

`_structure/references.json` has 4,597 edge entries, ALL empty: in the
declaration parser, `decl_depth` is captured BEFORE the brace line
increments depth, so a next-line `{` closes bodies instantly → no members
are ever captured.

## Fix

Correct the depth accounting (capture AFTER processing the decl line's own
braces, or parse `{` on following lines properly — match the code's
existing style). No format changes to references.json schema; entries must
now carry their actual member/reference content. Re-run ONLY the structure
graph regeneration against the workroot S7 output if cheap (a single
assembly suffices as proof); otherwise prove via unit-level reasoning +
py_compile.

Final message ≤5 lines: diff summary + proof result.

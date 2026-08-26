# Brief F-CW8 — Spec Fixer: S5 policy errata line (A-S6 item 1)

You are a fresh Spec Fixer subagent launched by the MiSide orchestrator.
You CANNOT spawn agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx`

## Task

Extend the existing "Errata" block with ONE dated entry (2026-08-25) for
the S5 encoding policy per `docs/research/verifications/s6-arbiter.mdx`
item 1: declared-codec recovery → recover-or-mark semantics, exit 0 when
all anomalies handled (exit 3 reserved for structural/absent/unhandled),
`emitted == walked-txt-count` invariant, U+FFFD+residue for unprovable
bytes, EN ref-set derived post-policy. Cite the evidence doc. Two lines
max, matching the established errata style; touch nothing else.

Final message ≤3 lines quoting the added text.

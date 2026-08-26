# Brief F-P2 — SpecFixer: resolve Arbiter finding N-1 only (MiSide pipeline spec)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You CANNOT
spawn other agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx`

## Case file

1. `C:\_reps\game-databases\MiSide\docs\research\verifications\p1-spec-arbiter.mdx`
   — ruling: `FIX_LOOP — N-1`. Everything else was judged build-ready;
   do NOT touch anything beyond N-1.
2. The spec itself — specifically S4 (sweep stage), AC-5, AC-8, AC-12.

## The one finding

S4 says each attempt **appends** a row to `census/sweep-attempts.jsonl`, but
AC-5 forbids any non-volatile byte change on rerun → rerunning S4 appends ~51
duplicate rows, unsatisfiable for a TestWriter and double-counting under
AC-12's reconciliation.

## Fix directive

Define the ledger write mode so reruns are idempotent: either upsert keyed on
`(container, argv-sha)` or deterministic full rewrite each run — pick ONE,
state it in S4 in ~two sentences, and align AC-5/AC-8/AC-12 wording so all
three reference the same mechanism consistently. No other edits, no
renumbering, no new sections.

## Rules

- Preserve MDX style and anchor links. Keep every E1-proven command
  byte-identical.
- Final message ≤6 lines: quote the exact sentences you changed/added per
  location.

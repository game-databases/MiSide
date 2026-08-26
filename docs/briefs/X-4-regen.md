# Brief X-4 — Micro-executor: regenerate `_structure/references.json`

You are a fresh Executor subagent of the MiSide orchestrator. You CANNOT
spawn agents. You never run `git` write commands. Operate ONLY: pipeline
shims at `C:\_reps\game-databases\MiSide\`, workroot
`D:\unpacked_game_data\MiSide\work\`. Game root read-only.

## Task

The F-CW9 parser fix (commit latest on MiSide/pipeline/stages/decompile.py)
is proven correct but the shipped `_structure/references.json` still holds
the degenerate pre-fix data. Regenerate:

1. Rerun ONLY what regenerates structure graphs (prefer a narrow
   `--stage`/slice form if the CLI offers one; else `--from decompile`
   and let idempotency handle the rest — reruns are byte-stable modulo
   volatile fields by design).
2. Verify post-state: `references.json` nonempty-edge ratio ≈ 2,738/4,597,
   ~8,272 total refs; hierarchy.json + types.json unchanged vs prior
   (byte-compare); EXTRACTION-LOG pins untouched.
3. Confirm census/PROOF artifacts remain consistent (rerun census slice if
   the pipeline flags staleness).

## Deliverable

Append a "Round 4" line-block to
`MiSide/docs/research/x1-execution-report.mdx`: what ran, wall time,
post-state numbers. Final line: `REGEN: COMPLETE` or `REGEN: FAILED — <why>`.
Final message ≤6 lines.

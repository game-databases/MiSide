# Brief R-C-W3 — fresh Code Reviewer (round 3): verify F-CW2's exception-coverage fix

You are a FRESH Code Reviewer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. `git diff` allowed; never add/commit/push.
You verify; you edit nothing. This is a NARROW verification — keep it tight.

## Check

`git diff HEAD~1 -- MiSide/pipeline/stages/` plus the fixer's claims in
`MiSide/docs/logs/F-CW2.log`. Exactly three edit sites expected:

1. `mono_typed_dump.py` post-wipe body wrapped; fail-fast sites stage
   rows/reason instead of flushing inline (:253/:270/:318).
2. `mono_typed_dump.py:366-369` single `except Exception` →
   `flush_aborted(...)` → bare re-raise (nothing swallowed).
3. `decompile.py:207-211` batch catch widened to `Exception`, flush +
   re-raise unchanged.

Confirm: (a) all exception paths now rewrite partial ledgers + aborted
report BEFORE propagating; (b) exit codes unchanged (StageFailure still →
spec'd codes); (c) diff confined to these two files; (d) smoke yourself:
py_compile ×2, `--list` exit 0, one usage-error form exit 2.

## Verdict

Write `docs/research/verifications/c-w1-review-r3.mdx`; final line exactly
`VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N findings>`. ≤8 lines.

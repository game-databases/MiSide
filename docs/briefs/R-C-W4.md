# Brief R-C-W4 — fresh Code Reviewer (round 4, LIGHT): verify F-CW3's two fixes

You are a FRESH Code Reviewer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. `git diff` allowed; never add/commit/push.
You verify; you edit nothing. NARROW scope — two fix sites only.

## Check

Fixer claims: `MiSide/docs/logs/F-CW3.log`. Diff:
`git diff HEAD~1 -- MiSide/pipeline/stages/decompile.py MiSide/pipeline/tests/test_census_reconcile.py`
(if HEAD moved due to concurrent packs' commits, locate the miside F-CW3
commit via `git log --oneline -- MiSide/pipeline | head -3` and diff
`<sha>~1..<sha>`).

1. **decompile.py:** structure-graph leg inside the guarded discipline;
   aborted report names the leg; re-raise preserves type; no swallowing;
   batch behavior untouched.
2. **test_census_reconcile.py:** residue entries now pinned by ID with
   discriminating content asserts; genuinely able to FAIL on wrong
   implementation (state what wrong output would trip it); style matches
   neighbors; count unchanged or justified.
3. Smoke: py_compile both; `pytest pipeline/tests -k "census or decompile"`
   report counts; one usage-error form exit 2.

## Verdict

`docs/research/verifications/c-w1-review-r4.mdx`; final line exactly
`VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N findings>`. ≤8 lines.

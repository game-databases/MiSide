# Brief v-n1b — Verifier B on F-P2's N-1 fix (drift lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
read-only; you may run `git diff` (never `git add/commit/push`). You VERIFY,
you edit nothing.

## Check

In `C:\_reps\game-databases\MiSide`, run:
`git diff HEAD -- MiSide/docs/specs/pipeline-run_all.mdx`
(the working-tree change is Fixer F-P2's N-1 resolution; HEAD is the
arbiter-approved state plus nothing else in this file).

Your single question: **did the fix touch ONLY what N-1 required?**
1. Enumerate every hunk. Allowed scope: S4 write-mode sentences, AC-5,
   AC-8, AC-12 ledger wording. Anything else = FINDING.
2. Confirm zero changes to: stage commands (E1-proven invocations must be
   byte-identical), stage numbering, anchors, §5 AC count/IDs, test plan.
3. Sanity: does the chosen mode (deterministic full rewrite) actually
   satisfy the arbiter's directive ("upsert by `(container, argv-sha)` or
   deterministic rewrite")? One of the two offered options is fine.

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\verifications\n1-vB.mdx` —
hunk-by-hunk disposition; final line exactly `VERDICT: PASS` or
`VERDICT: FAIL — <one line>`. ≤10 lines total.

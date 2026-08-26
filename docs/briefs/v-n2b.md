# Brief v-n2b — Verifier B on F-P3 (drift lens, cumulative diff)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
read-only; `git diff` allowed (never add/commit/push). You VERIFY, you edit
nothing.

## Check

In `C:\_reps\game-databases\MiSide`:
`git diff HEAD -- MiSide/docs/specs/pipeline-run_all.mdx`

The working-tree diff vs HEAD contains TWO fixer rounds: F-P2 (N-1 ledger
write mode — 4 hunks in S4/AC-5/AC-8/AC-12, already verifier-PASSed) and
F-P3 (one qualifier added to the AC-5 sentence). Your job:

1. Total hunks must be exactly those five areas — enumerate and confirm no
   sixth hunk anywhere.
2. F-P3's contribution is ONLY the AC-5 sentence gaining "modulo the
   volatile fields" — nothing else reworded.
3. Mechanical zero-drift: heading+AC-ID sequence HEAD↔worktree empty diff;
   every fenced command block byte-identical.

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\verifications\n2-vB.mdx` —
hunk disposition; final line exactly `VERDICT: PASS` or
`VERDICT: FAIL — <one line>`. ≤10 lines total.

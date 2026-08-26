# Brief F-CW3 — Code Fixer: A-BUILD's two surviving fixes

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Touch ONLY files
under `C:\_reps\game-databases\MiSide\pipeline\` EXCEPT `pipeline/tests/`
for fix 1; fix 2 is IN tests.

## Read first

1. `docs/research/verifications/build-arbiter.mdx` — FIX_LOOP items 1–2.
2. `pipeline/stages/decompile.py`, `pipeline/tests/test_census_reconcile.py`,
   `pipeline/stages/census.py`.

## Fixes (exactly these two)

1. **Guard the structure-graph leg** (`decompile.py:~216`): `wipe_tree(_structure/)`
   + `parse_dump_cs` sit after the guarded batch, so an exception there
   leaves a torn tree beside a COMPLETE `decompile.json`. Extend coverage:
   wrap this leg in the same flush-abort-then-re-raise discipline (aborted
   stage report naming the leg), matching the pattern already established
   in the batch body. Nothing swallowed.
2. **De-tautologize AC-12 residue checks** (`test_census_reconcile.py:88-95`):
   needles `"gi"`/`"get"` match "logic"/"budget". Replace with assertions
   that actually pin the GI and unlock-state residue entries per AC-12's
   contract — e.g. match on the specific residue keys/values the spec names,
   or assert structured entries rather than substring probes. Keep test
   style consistent with neighbors.

Smoke: py_compile touched files; run `pytest pipeline/tests -k census`
(default tier) and report counts; `--list` exit 0.

Final message ≤6 lines: edits + smoke results.

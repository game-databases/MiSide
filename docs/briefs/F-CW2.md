# Brief F-CW2 — Code Fixer: single R-C-W2 finding (abort-path exception coverage)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Touch ONLY files
under `C:\_reps\game-databases\MiSide\pipeline\` EXCEPT `pipeline/tests/`.

## The one finding (from docs/research/verifications/c-w1-review-r2.mdx)

Abort-ledger rewriting (`flush_aborted` in `mono_typed_dump.py` +
decompile batch) is triggered only on `StageFailure`. A
`subprocess.TimeoutExpired` (tool timeouts 7200s/3600s/1800s) or `OSError`
mid-loop escapes unhandled — stale COMPLETE ledger beside a half-wiped
tree, the exact hazard round-1 major#2 closed.

## Fix directive

Smallest change that closes it: wrap the sweep/batch loop bodies so ANY
exception path (`except Exception` before the bare re-raise, or
try/except/raise pattern matching surrounding idiom) performs the partial
ledger rewrite + aborted stage report, then propagates. Do NOT swallow
exceptions; exit codes must stay intact. No other edits.

Smoke after: py_compile touched modules; `--list` exit 0; one usage-error
form exit 2. Final message ≤5 lines: file:line of each edit + smoke results.

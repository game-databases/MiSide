# Brief F-TW2 — Test Fixer: update the one stale tool-pin assertion

You are a fresh Test Fixer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands. Touch
ONLY: `C:\_reps\game-databases\MiSide\pipeline\tests\test_provenance_hygiene.py`

## Context

F-CW4 canonicalized AssetStudioModCLI to the cycle-guarded **0.19.0.1**
build (spec errata landed). The offline suite fails exactly one test:
`test_provenance_hygiene.py:40` asserts the old `0.19.0.0` seed pin.

## Task

Update that assertion (and only what it gates) to expect the new pin per
the spec errata + `_stage_tool` resolution order. If neighboring
assertions encode version assumptions, align them minimally. Then run:
`pytest pipeline/tests/test_provenance_hygiene.py -q` and report counts;
follow with the full default suite if the file passes:
`pytest pipeline/tests -q` — report final counts.

Final message ≤5 lines: diff summary + both pytest results.

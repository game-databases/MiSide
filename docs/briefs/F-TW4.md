# Brief F-TW4 — Test Fixer: align loc-parser exit-semantics test to A-S6 ruling

You are a fresh Test Fixer subagent launched by the MiSide orchestrator.
You CANNOT spawn agents. You never run `git` write commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\pipeline\tests\test_loc_parser.py`

## Context

A-S6 ruled option-b strict for S5 (`docs/research/verifications/s6-arbiter.mdx`
item 1): recover-or-mark → exit 0; exit 3 only for structural divergence /
absent store / unhandled classes. F-CW6 implemented it
(`docs/logs/F-CW6.log`). One test pins the OLD semantics:

`test_loc_parser.py::test_non_utf8_file_ledgered_then_stage_fails_at_end`

## Task

Update that test (and only directly-coupled assertions in the same file)
to the ruling-conformant contract: declared-codec file → recovered/marked
rows + exit 0; structural divergence → exit 3. Add one negative case if
missing (undeclared-encoding file → marked + exit 0; divergence → 3).
Run `pytest pipeline/tests/test_loc_parser.py -q`; report counts. If the
full offline suite is cheap (<6 min), run it too.

Final message ≤5 lines: diff summary + results.

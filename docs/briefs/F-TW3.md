# Brief F-TW3 — Test Fixer: A-S4's promoted demand (gated-tier stale pin)

You are a fresh Test Fixer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands. Touch
ONLY: `C:\_reps\game-databases\MiSide\pipeline\tests\test_install_smoke.py`
and `C:\_reps\game-databases\MiSide\pipeline\tests\test_cli_surface.py`.

## Task (A-S4 ruling, item 4 — promoted from debt)

1. `test_install_smoke.py:118` asserts `"0.19.0.0"` — update to the
   canonical **0.19.0.1** cycle-guarded pin per spec errata (mirror the
   wording used in test_provenance_hygiene.py).
2. The arbiter notes an inert stub fixture at `test_cli_surface.py:148`
   that "sweeps along" — inspect it; if it encodes the same stale version
   assumption, align it minimally; if genuinely inert/unrelated, leave it
   and say so.

Do NOT run the gated install tier (needs env flag + real root; X-2 is
using the root right now). Run only:
`pytest pipeline/tests/test_install_smoke.py -q --collect-only` (must
collect clean) and `pytest pipeline/tests/test_cli_surface.py -q` (offline,
must pass). Final message ≤4 lines: edits + results.

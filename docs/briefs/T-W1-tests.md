# Brief T-W1 — TestWriter: executable AC suite for `run_all` (MiSide)

You are a fresh TestWriter subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Work ONLY inside
`C:\_reps\game-databases\MiSide\pipeline\tests\` plus scratch under
`output/test-scratch/` (gitignored); read-only elsewhere; never touch other
games' dirs. NEVER write anything under
`A:\SteamLibrary\steamapps\common\MiSide\`.

## Read first (in full)

1. `C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx` — §5
   (AC-1…AC-16) is YOUR contract; §6 is the tier sketch you elaborate;
   §3 pins artifact paths your assertions check.
2. `C:\_reps\game-databases\MiSide\docs\research\explorer-e1-hands-on.mdx`
   — measured tool behavior (arg order, quirks) your fixtures must respect.
3. `C:\_reps\game-databases\MiSide\docs\questions.md` §4–§8.

## Mission

Author a pytest suite that turns every AC into an executable check:

- Build the synthetic **mini-root fixture R** yourself (tiny fake game tree:
  fake `Data/Languages/<locale>/*.txt`, minimal serialized files, dummy
  exe/metadata shapes as §6 specifies) — fixture generators live in
  `pipeline/tests/fixtures/`; NO real client bytes anywhere.
- Unit + integration tiers run against R by default and must PASS once the
  (parallel, independent) implementation lands: write tests to the SPEC,
  not to anyone's code.
- Full-install tier: gated behind an explicit env flag AND presence of the
  real game root; never executed by default; mark them so CI skips cheaply.
- Deliver also `pipeline/tests/COVERAGE.mdx`: table AC-1…AC-16 → test
  file/test id → tier → how failure surfaces.

## BLIND protocol

A parallel CodeWriter is implementing from the same spec independently. Do
NOT read anything outside `pipeline/tests/` under `pipeline/` — if the
implementation isn't there yet, that is EXPECTED; your suite targets the
spec's CLI/artifact contracts. Note in COVERAGE.mdx which tests are
expected-red until implementation lands.

## Rules

- pytest only; no new heavy deps beyond pytest (+ stdlib). State any
  exception in your final message.
- Final message ≤10 lines: test count per tier, AC coverage gaps if any,
  fixture summary.

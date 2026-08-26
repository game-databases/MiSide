# Brief F-CW1 — Code Fixer: apply R-C-W1's 7 findings to the run_all implementation

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Touch ONLY files
under `C:\_reps\game-databases\MiSide\pipeline\` (EXCEPT `pipeline/tests/`
— a parallel TestWriter owns that tree and may be editing it live; if a fix
seems to require touching tests, note it in your final message instead).
You may re-run cheap smoke checks (`--list`, `--help`, unit-safe paths).

## Read first

1. `C:\_reps\game-databases\MiSide\docs\research\verifications\c-w1-review.mdx`
   — the 7 findings (1 blocker, 3 major, 3 minor) with file:line. Resolve
   ALL, exactly as prescribed there.
2. `docs/specs/pipeline-run_all.mdx` — contract; keep E1-proven commands
   byte-identical; S4 write mode = deterministic full rewrite; VOLATILE_FIELDS
   semantics per §3.

## The findings (from the review — verify against your reading too)

- BLOCKER: wire `--expect-drift` through to `detect.py` so S2's patch-day
  escape hatch actually fires.
- MAJOR: fail-fast aborts mid-sweep/mid-batch must rewrite their ledgers
  (partial-state rows) so no stale COMPLETE ledger survives beside a
  half-wiped output tree.
- MAJOR: `detect.json` free-space bytes must be enumerated in
  `VOLATILE_FIELDS` (or excluded from the report) — AC-5 rerun must hold.
- MAJOR: `.psd` classification order — Languages branch must win so the
  `psd-source` per-locale subset scan is reachable and AC-10's catalogue
  shape is expressible.
- MINORS: probe-first ledger row order per spec; `_loaded_containers`
  substring match → exact/segmented match (`level1` ⊄ `level13`); staged
  texture scope bar → the ruled row-count mechanism, not an invented 3 GiB
  byte threshold.

## Rules

- No new features; smallest change that kills each finding. Match
  surrounding idiom. Final message ≤8 lines: per-finding fix summary with
  file:line + smoke results.

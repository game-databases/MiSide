# Brief F-P1 — SpecFixer: apply R-P1 review findings to the P1 pipeline spec (MiSide)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx`
(line-level revisions; no restructure, no new sections beyond what fixes
require).

## Read first (in full)

1. `C:\_reps\game-databases\MiSide\docs\research\verifications\p1-spec-review.mdx`
   — the 14 findings you MUST resolve.
2. `C:\_reps\game-databases\MiSide\docs\questions.md` §4–§8 — the rulings
   three majors accidentally contradict; rulings WIN.
3. `C:\_reps\game-databases\MiSide\.gitignore` — current tracked-light
   reality (fix AC-15/§9.5 to MATCH it, including `il2cpp/` local-only).
4. The spec itself.

## Fix directives

- Resolve all 4 majors exactly as the review specifies: git policy
  conformance (F-1), ILSpy CLI decided (F-2), texture scope staged (F-3),
  idempotency ACs restated as implementable (F-4 — e.g. "rerun changes no
  OUTPUT-DATA bytes; wall-clock artifacts excluded" with the artifact list).
- Resolve all 10 minors: add per-locale texture ledger + Voice Editor census
  row to ACs where the review says; name the attempt-ledger/stage-report
  artifacts; define "±patch-drift"; one-shot disk guard; isolate Il2CppDumper
  cwd; verify-or-flag the `-m dump`+asset-list single pass; cover exit codes
  2/4 + stale-log defense; S5 per-file failure policy; drop redundant
  `run_all.ps1` OR state its distinct purpose if genuinely needed on Windows.
- Keep every E1-proven command byte-identical while editing around them.

## Rules

- No new claims without a cited source (E1 findings / toolchain.md /
  questions.md rulings). Preserve MDX style + anchor links.
- Final message ≤8 lines: per-finding resolution map (F-1…minor-N → fixed).

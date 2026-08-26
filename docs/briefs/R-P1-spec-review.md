# Brief R-P1 — PrepareTask Reviewer: P1 pipeline spec (MiSide)

You are a fresh Reviewer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. Write only your
review report.

## Under review

SPEC: `C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx` — IN FULL.

## Read first (in full)

1. `C:\_reps\game-databases\AGENTS.md`
2. `C:\_reps\game-databases\_foundation\extraction-doctrine.md`
3. `C:\_reps\game-databases\MiSide\toolchain.md`
4. `C:\_reps\game-databases\MiSide\docs\research\explorer-e1-hands-on.mdx`
5. `C:\_reps\game-databases\MiSide\docs\questions.md` §4–§8 (orchestrator
   rulings that bound this spec)
6. `C:\_reps\game-databases\_foundation\decision-register.md` entries
   [DR-2026-08-18-pipeline] and [DR-2026-08-17-relink]

## Mission — is this spec complete, correct, and NOT over-engineered?

- **Doctrine coverage:** does the stage set + ACs actually satisfy
  [DR-2026-08-18-pipeline] (single entrypoint, --help/--list, idempotent
  isolated stages, EXTRACTION-LOG pinning) and seed Principle two's
  PROOF.md source inventory with real numbers?
- **AC quality:** are all 16 ACs individually testable by a TestWriter?
  Name any AC that is ambiguous, unmeasurable, or missing (e.g. locale
  count expectations, no-trailing-newline handling, per-locale texture
  variants, Voice Editor census row).
- **Reality anchoring:** every tool invocation must match E1's PROVEN
  commands/paths (venv python version, Il2CppDumper cwd gotcha,
  AssetStudioModCLI flags, game-root Data\ for loc). Flag anything
  re-derived differently or left [unverified] where E1 has proof.
- **Ruling conformance:** check the spec against questions.md §4–§8
  rulings (ILSpy CLI; never mutate A:\ install; staged texture scope;
  Voice Editor as source row; git tracking policy).
- **Over-engineering hunt:** any stage/AC beyond doctrine+brief needs
  (entity curation, relink internals, frontend concerns) = scope creep →
  flag with the exact cut.
- **Holes:** failure behavior between stages, partial-failure resumability,
  disk-budget guard before big writes, Windows path handling in scripts
  driven from Git Bash.

## Report

Write `C:\_reps\game-databases\MiSide\docs\research\verifications\p1-spec-review.mdx`
— numbered findings (blocker/major/minor), each with evidence and a concrete
suggested change; end with `VERDICT: READY_FOR_ARBITER` or
`VERDICT: NEEDS_REVISION`. Final message ≤10 lines.

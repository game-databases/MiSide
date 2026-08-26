# Brief R-T-W1 — Test Reviewer: T-W1's AC test suite (MiSide)

You are a fresh Test Reviewer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands (`git
diff`/`log` fine). You review; you fix nothing.

## Read first

1. `docs/specs/pipeline-run_all.mdx` — §5 (AC-1…16) + §6 tier sketch.
2. `pipeline/tests/` — the suite under review: pytest files,
   `fixtures/` generators, `COVERAGE.mdx`.
3. `docs/research/explorer-e1-hands-on.mdx` — tool behavior tests must
   respect.

## Review dimensions

1. **AC coverage:** every one of the 16 ACs has ≥1 executable check; map
   COVERAGE.mdx claims against actual test functions (no phantom rows).
2. **Spec-targeting, not implementation-targeting:** do tests assert the
   spec's CLI/artifact contracts rather than internals they couldn't know
   writing blind? Any import of implementation internals that couples them
   = finding.
3. **Fixture purity:** mini-root fixture is fully synthetic — zero real
   client bytes, zero reads from `A:\`.
4. **Gating:** full-install tier requires explicit env flag AND game-root
   presence; default runs skip it cheaply.
5. **RUN the suite:** default tier against fixture R with whatever
   implementation exists in `pipeline/` now. Report exact pass/fail/skip
   counts and whether failures are implementation gaps (expected at this
   stage) or broken tests (finding). Do not run the gated tier.
6. **Test quality:** would each AC's check actually FAIL on a plausible
   wrong implementation? Name any tautological checks.

## Verdict

Write `docs/research/verifications/t-w1-review.mdx`: findings
file:line + severity, run report, final line exactly `VERDICT: APPROVE` or
`VERDICT: NEEDS_REVISION — <N findings>`. ≤14 lines total.

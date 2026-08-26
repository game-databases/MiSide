# Brief A-BUILD — Arbiter: final ruling on the P1 `run_all` build wave (MiSide)

You are a FRESH Arbiter subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. `git log/diff` allowed; never add/commit/push.
You rule; you edit nothing.

## Case file (read in this order)

1. SPEC (contract): `MiSide/docs/specs/pipeline-run_all.mdx`
2. CODE CHAIN verdicts: `docs/research/verifications/c-w1-review.mdx`
   (NEEDS_REVISION 7) → `c-w1-review-r2.mdx` (verified 7 fixed; 1 new
   minor) → `c-w1-review-r3.mdx` (**APPROVE**; residual note: decompile
   structure-graph leg outside guarded batch)
3. TEST CHAIN: suite at `pipeline/tests/` (70 tests), reviewer verdict
   `t-w1-review.mdx` (**APPROVE**, 66/0/4 black-box vs real driver;
   2 medium + 4 low tightening items listed there)
4. T-W1's spec-level observations: `docs/logs/T-W1.log` (stale-log refusal
   covers pipFreeze only, not wrong TOOL version in pin block; §S2's
   unity3d/Addressables-absence verdict not surfaced in detect.json; §8
   verify-item resolved POSITIVE re `--export-asset-list xml`)
5. Spot-check the code/tests wherever a claim determines your ruling.

## Mission

- Adjudicate the residual structure-tree note: block now, or record as
  follow-up? (Consider likelihood × blast radius vs the wave's goal.)
- Adjudicate R-T-W1's 2 medium items (residue-needle tautology risk,
  AC-6 digit-containment laxness): tighten now via one more fixer round,
  or accept as recorded debt?
- Adjudicate T-W1's spec observations: do any reveal the SPEC itself needs
  an errata before the pipeline is trusted against the real install?
- Confirm no blind-protocol violation occurred between C-W1 and T-W1.
- Rule on overall piece completion.

## Deliverable

`docs/research/verifications/build-arbiter.mdx` — dispositions per item;
final line exactly one of:
`RULING: BUILD_APPROVED — proceed to real-install execution` or
`RULING: FIX_LOOP — <numbered surviving fixes>`. ≤14 lines total.

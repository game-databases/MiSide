# Brief R-SB1 — Code Reviewer: SB-1 site scaffold (MiSide)

Fresh Code Reviewer subagent of the MiSide orchestrator. CANNOT spawn
agents; `git log/diff` allowed; never write repo state. KEEP DISK WRITES
MINIMAL (C: ~2 GB free — do NOT reinstall node_modules; use
`site/node_modules` as-is).

## Read

1. CONTRACT: `docs/specs/site-scaffold.mdx` + `s1b-arbiter.mdx`.
2. BUILD: `site/` (47k files incl. node_modules — review SOURCE only:
   `src/`, configs, `i18n/`, `ci/`, public). Builder claims in
   `docs/logs/SB-1.log` + build-log SB-1 block.

## Review dimensions

1. **Contract fidelity:** §1.1 pins exact; twin-tree routing per §3;
   kit contract §4 — hex-lint claim true? Radix behavior untouched in
   stock column? Rebuilt primitives evidence-cited?
2. **ACs:** re-run ≥6 of S1–S14 yourself (chrome parity ×34 script,
   hex grep, negative map grep, curl matrix subset on a local start or
   exported output if cheap).
3. **Honest deviations:** fa kept LTR, CWV runner partial (no Lighthouse),
   documents `_meta` reader shapes — each acceptable vs spec intent?
4. **Code quality:** TS strictness, no dead code beyond stub routes,
   i18n keyed-JSON completeness ×34 (sample 3 locales for key parity).
5. **Security/hygiene:** no secrets, no client data copied into repo
   beyond contracts/data dirs.

## Verdict

`docs/research/verifications/sb1-review.mdx`; findings w/ severity;
final line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`.
≤14 lines.

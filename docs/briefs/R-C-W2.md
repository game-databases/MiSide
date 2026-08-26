# Brief R-C-W2 — fresh Code Reviewer: verify F-CW1's fix round (MiSide run_all)

You are a FRESH Code Reviewer subagent (round 2) launched by the MiSide
orchestrator. You CANNOT spawn other agents. `git diff`/`log` allowed;
never add/commit/push. You verify; you edit nothing.

## Read first

1. `docs/research/verifications/c-w1-review.mdx` — round-1's 7 findings.
2. The fixer's claims: `docs/logs/F-CW1.log`.
3. `docs/specs/pipeline-run_all.mdx` — contract for anything the fixes touch.
4. The implementation under `pipeline/` (ignore `pipeline/tests/` — live
   TestWriter territory).

## Mission

Trust neither party's self-report:

1. **Per-finding verification (all 7):** open the cited code; confirm the
   defect is actually gone AND the fix matches spec semantics (drift-gate
   warning path still records drift data; abort ledgers carry partial rows
   per S4 write mode; free_space_bytes volatile entry actually consulted by
   the AC-5 comparison path; psd-source scan reachable end-to-end).
2. **Regression hunt:** did any fix break a previously-clean dimension?
   Re-check: E1 command byte-fidelity, `<game-root>` immutability, exit
   codes 0/2/3/4, manifest completeness.
3. **Smoke yourself:** `--list`, `--help`, one usage-error form, plus any
   cheap behavior assert you can run without the real install.
4. New findings (any severity) go in the report even if round-1 missed them.

## Verdict

Write `docs/research/verifications/c-w1-review-r2.mdx`: per-finding
disposition + regression results; final line exactly `VERDICT: APPROVE` or
`VERDICT: NEEDS_REVISION — <N findings>`. ≤14 lines total.

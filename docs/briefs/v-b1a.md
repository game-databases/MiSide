# Brief v-b1a — Verifier A: B-1 characters build (evidence re-execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus +
`extracted/data/characters/` are your ground truth.

## Check

Builder claims: `docs/logs/B-chars.log` + `docs/research/build-log.mdx`
(B-1 block). Spec: `docs/specs/dataset-characters.mdx`.

1. **Re-execute ≥5 of the 10 ACs yourself** against the emitted artifacts
   (not trusting the builder's scoreboard) — including AC-7's transform-T
   assertion and the locale-parity check.
2. **Row spot-check:** open `personages.jsonl`; verify 4 random rows field-
   by-field against cited sources (`MenuPersonage.txt`, loc JSONLs).
3. **Byte-determinism:** rerun whatever deterministic emitter the build/
   dir contains IF it's a self-contained script (else verify ordering/
   sorted-keys properties statically); md5 compare.
4. **Counts:** 24 rows / 26 candidates / join coverages match reality.

## Deliverable

`docs/research/verifications/b1-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines.

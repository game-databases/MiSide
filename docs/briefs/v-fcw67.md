# Brief v-fcw67 — Verifier: F-CW6 + F-CW7 implementations vs A-S6 ruling

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git diff` allowed, never write. You verify; you edit nothing.

## Check

Ruling: `docs/research/verifications/s6-arbiter.mdx`. Claims:
`docs/logs/F-CW6.log` + `F-CW7.log`. Code: `pipeline/stages/loc_jsonl.py`,
`census.py`, `decompile.py`, `common.py`, spec errata block.

1. **F-CW6 vs item 1:** declared-codecs map matches the evidence doc's
   proven files only; all-segments round-trip gate real (would a poisoned
   segment fail?); U+FFFD marks carry residue ids/hex/line; exit codes per
   ruling; `emitted == walked-txt-count` asserted in-code not just
   reported; ref-set post-policy derivation sound.
2. **F-CW7 vs item 2:** DOTNET_ROOT resolved+injected in stage code (no
   caller-env dependence); version-pin gate refuses host-global; zip
   fallback retired with actionable failure; pins upsert includes channel+
   sha256; errata line present.
3. Cross-check F-CW8's spec line + F-TW4's tests reflect the same contract
   (no drift between code/tests/spec).
4. Smoke: py_compile ×4; `--list` exit 0.

## Deliverable

`docs/research/verifications/f-cw67-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.

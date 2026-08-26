# Brief v-fcw5 — Verifier: F-CW5's pin-block self-heal in detect.py

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git diff` allowed, never write. You verify; you edit nothing. NARROW scope.

## Check

Fixer claims: `MiSide/docs/logs/F-CW5.log`; diff = working tree change to
`MiSide/pipeline/stages/detect.py` only (commit if landed).

1. The upsert covers ALL machine pin-block keys from live resolved facts;
   human event sections + non-owned keys preserved (find the section
   parser; confirm it can't swallow human text on rewrite).
2. Verified-on-disk pins outrank seed placeholders; empty reads never
   clobber; `detect-measured-change` semantics untouched.
3. AC-5 interplay: confirm the verified-entry merge rule prevents
   rerun-to-rerun byte drift (the failure the fixer says its first cut
   hit); reason through two consecutive reruns.
4. Suite yourself: `pytest pipeline/tests -q -k "idempotency or provenance
   or detect"` offline subset; report counts.

## Deliverable

`docs/research/verifications/f-cw5-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤8 lines.

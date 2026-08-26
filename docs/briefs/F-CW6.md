# Brief F-CW6 — Code Fixer: implement A-S6's I-3 ruling in S5 (loc_jsonl)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\pipeline\` EXCEPT `pipeline/tests/`.

## Read first

1. RULING: `MiSide/docs/research/verifications/s6-arbiter.mdx` (item 1) —
   implement its amendment details EXACTLY.
2. EVIDENCE: `MiSide/docs/research/s5-legacy-encoding.mdx` (two failure
   classes; proven cp1250; line-58 fleet corruption; phantom EN skew rows).
3. `pipeline/stages/loc_jsonl.py` + spec §2 S5 + AC-9.

## Implement (option b strict)

- One DECLARED codec per affected file (from evidence: cp1250); ALL segments
  must round-trip under it, else that segment becomes U+FFFD + a residue
  entry naming file/locale/line/reason. No silent best-effort decodes.
- Exit 0 iff every anomaly is recovered-or-marked; keep exit 3 for absent
  store / structural divergence / unhandled failure classes (structural =
  split-line count divergence vs category norm — the 71-line invariant).
- New stage invariant asserted in-code: `emitted == walked-txt-count`.
- EN reference-set repair so the 27 phantom `extra_vs_reference` rows clear
  automatically (derive ref-set from emitted rows post-policy).
- Residue entries follow the census RESIDUE_SEEDS pattern (id + content)
  so they render into AC-12's ledger.
- Ledger rows for recovered files mark codec + segment counts.

Smoke: py_compile; run S5 alone against a scratch copy of the real
`Data\Languages\LocationDialogue` category (copy under work/, never write
A:\) — expect exit 0, 2,210-floor math intact, 5 U+FFFD marks, residue
entries present. Report actual numbers. Final message ≤6 lines.

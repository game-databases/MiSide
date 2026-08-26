# Brief R-DS3 — Reviewer: dataset-dialogue spec (MiSide)

Fresh Reviewer subagent of the MiSite orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. You review; you edit
nothing.

## Read

1. SPEC: `MiSide/docs/specs/dataset-dialogue.mdx`
2. Ground truth: corpus at `D:\unpacked_game_data\MiSide\work\extracted\`
   (Dialogue category JSONLs, harvest level dumps, asset lists).

## Checks

1. **Scale reproduction:** recount one measured claim yourself (e.g.
   Dialogue_3DText node count or next-edge/terminal split) — does it match?
2. **level↔Location binding rule:** the empirical levelN↔Location(N−2)
   claim — test it on 2 levels from harvest dumps.
3. **Locale parity:** positional line-parity for 34 locales — spot-verify
   one category across 3 locales; confirm the French Location16 empty-file
   and 7 LD12 residue rows join plan.
4. **E1 supersession:** §2.4's derivations vs E1's "24 raw / 16" — is the
   supersession documented and justified rather than silent?
5. ACs D1–D9: checkable? discriminating? census reconciliation + dangling-
   edge ledger present?
6. The 5 ambiguous theme→Mita enum mappings: is the curation ruling
   properly DEFERRED (flagged) rather than guessed?

## Verdict

`MiSide/docs/research/verifications/ds3-review.mdx`; findings w/ severity;
final line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`.
≤12 lines.

(Note: path typo in this brief's first line is intentional-none; work in
`C:\_reps\game-databases\MiSide\`.)

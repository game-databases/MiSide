# Brief R-DS1 — Reviewer: dataset-characters spec (MiSide)

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. You review; you edit
nothing.

## Read

1. SPEC: `MiSide/docs/specs/dataset-characters.mdx`
2. Ground truth: `MiSide/spec.md` entity/characters sections;
   corpus at `D:\unpacked_game_data\MiSide\work\extracted\` — VERIFY the
   anchor claim yourself (`harvest/mb-dump/level2/MenuPersonage.txt`: 14+10
   PersonageResource rows, internal names, palettes, save keys).
3. `docs/research/game-research.mdx` Mita chapters for lore-side fields.

## Checks

1. Anchor reproduction + schema field traceability: open ≥6 of the 15
   claimed sources; every schema field must resolve to a real path/row.
2. Locale ruling soundness: pointer-columns-not-copies — is parity really
   measured across all 34 locales for all 4 categories? Spot-verify 2.
3. Joins: are the 6 join keys real on both sides (sample 3)?
4. ACs: ≥6, each checkable from repo artifacts alone — would each FAIL on
   a wrong build?
5. Honesty: risks/unverified marks plausible; no invented fields; stub plan
   where data absent.

## Verdict

`MiSide/docs/research/verifications/ds1-review.mdx`; findings w/ severity;
final line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`.
≤12 lines.

# Brief R-DS2 — Reviewer: dataset-achievements-endings spec (MiSide)

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. You review; you edit
nothing.

## Read

1. SPEC: `MiSide/docs/specs/dataset-achievements-endings.mdx` (~600 lines)
2. Ground truth: corpus at
   `D:\unpacked_game_data\MiSide\work\extracted\`; store 26-list in
   `MiSide/competitor-research.md`; Fandom cross-ref in game-research.mdx.

## Checks

1. **Triple reconciliation:** verify 26=26=26 yourself (dump.cs ACHI
   entries vs the store table vs wiki list) — any drift = FINDING.
2. **PersistentCall cites:** open ≥4 of the 13 claimed award sites
   (file+pathID) — do they exist and mean what the spec says?
3. **Choice machinery:** spot-verify counts (13 DialogueChanger, 353
   ObjectInteractive wired, 5 Events_IntMemory, 379 Events_Data) by your
   own grep of decompiled/harvest artifacts.
4. **unverified-behavior honesty:** is the DummyDll-stripped-bodies limit
   consistently applied (no field silently claims proven behavior)?
5. ACs: 16 total — sample 6 for checkability + discriminating power.
6. Endings: Peaceful locked stub handled honestly? Choice→ending edges all
   code-cited?

## Verdict

`MiSide/docs/research/verifications/ds2-review.mdx`; findings w/ severity;
final line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`.
≤12 lines.

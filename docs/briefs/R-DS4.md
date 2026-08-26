# Brief R-DS4 — Reviewer: dataset-cartridges spec (+ cross-spec check vs documents)

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus:
`C:\_reps\game-databases\MiSide\extracted\`.

## Read

1. SPEC: `MiSide/docs/specs/dataset-cartridges.mdx`
2. SIBLING: `MiSide/docs/specs/dataset-documents.mdx` (§ on the Flash
   pickup-family adjudication) + DS-1's `flashes:<save_key>` anchors.
3. Corpus ground truth for the anchors below.

## Checks

1. **Registry anchor:** verify the string literal @0x13AD860 carries
   exactly 23 keys (13 Mita + 10 player); reconcile against DS-1's
   personages save keys.
2. **FlashTaker census:** recount pickups (claim: 21 across levels 8–21);
   confirm mtad2/mtacore unresolved-tier honesty.
3. **Minigame surfaces:** sample ≥4 of the 17 claimed surfaces across the
   four registries incl. the pinned −1 TV loc offset.
4. **Honesty:** J6 scoring-functions downgrade justified + ledgered as R1?
   "Hetoor" firewall grep reproduces zero hits?
5. **CROSS-SPEC:** does the cartridge/profile-family boundary agree with
   dataset-documents.mdx (one pickup family, mta*/plr* split)? Any double-
   ownership of rows between the two specs? Flag inconsistencies.
6. ACs: sample 5 for checkability + discriminating power.

## Verdict

`docs/research/verifications/ds4-review.mdx`; findings w/ severity; final
line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`. ≤12 lines.

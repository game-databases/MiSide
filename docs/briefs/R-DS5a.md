# Brief R-DS5a — Reviewer (evidence lens, LIGHT): dataset-documents spec

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus:
`C:\_reps\game-databases\MiSide\extracted\`. Keep this TIGHT — four checks
only, sample rather than exhaustive.

## Check

Spec: `MiSide/docs/specs/dataset-documents.mdx` (§ refs below).

1. **profile_document recount** (§2): 13 rows — 11 FlashTaker-placed + 2
   script-granted; confirm the mta*/plr* split arithmetic vs
   ACHI_mitastory(13)/ACHI_cartridgeplayers(12).
2. **BlackRoom paper parts** (§3): indexPuzle 0–4 present as claimed.
3. **Dedupe spot-check**: from the 258 Unity_Note dumps, apply §4's
   dependency-load dedupe rule to ONE level; does your count scale to
   ~160 corpus-wide?
4. **One negative finding**: Translation.jsonl really has 1 row / no
   notes loc category.

## Deliverable

`docs/research/verifications/ds5-review-a.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤8 lines.
